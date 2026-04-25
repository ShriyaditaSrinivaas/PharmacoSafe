"""
FastAPI application for PharmacoSafe.
Serves the ML API and the animated frontend.
"""

import sys
import json
import numpy as np
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pharmacosafe.config import (
    DRUG_DATABASE, PHARMACOGENES, POPULATIONS,
    POPULATION_NAMES, DATA_DIR, MODELS_DIR, REPORTS_DIR,
)
from pharmacosafe.pharmaco.gene_drug_mapper import GeneDrugMapper
from pharmacosafe.pharmaco.variant_parser import VariantParser
from pharmacosafe.pharmaco.drug_database import DrugDatabase
from pharmacosafe.models.dosing_recommender import DosingRecommender

# ── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PharmacoSafe API",
    description="Pharmacogenomics-Driven ADR Prediction with Fairness Auditing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Services ───────────────────────────────────────────────────────────────
mapper = GeneDrugMapper()
parser = VariantParser()
drug_db = DrugDatabase()
recommender = DosingRecommender()

# Lazy-loaded models
_models = {}
_preprocessor = None


def _get_preprocessor():
    global _preprocessor
    if _preprocessor is None:
        import pandas as pd
        from pharmacosafe.data.preprocessor import DataPreprocessor
        _preprocessor = DataPreprocessor()
        # Fit on training data if available
        data_path = DATA_DIR / "pharmacogenomic_data.csv"
        if data_path.exists():
            df = pd.read_csv(data_path)
            # Fit encoders on first available drug
            for drug_id in DRUG_DATABASE:
                try:
                    _preprocessor.prepare_features(df, drug_id)
                    break
                except Exception:
                    continue
    return _preprocessor


def _get_model(drug_id: str):
    if drug_id not in _models:
        model_path = MODELS_DIR / f"adr_predictor_{drug_id}.joblib"
        if not model_path.exists():
            return None
        from pharmacosafe.models.adr_predictor import ADRPredictor
        _models[drug_id] = ADRPredictor.load(drug_id)
    return _models[drug_id]


# ── Pydantic Models ────────────────────────────────────────────────────────
class PatientInput(BaseModel):
    age: int = 50
    sex: str = "Male"
    weight_kg: float = 70.0
    bmi: float = 24.0
    egfr: float = 90.0
    alt_u_l: float = 25.0
    n_comedications: int = 2
    smoking_status: str = "Never"
    diabetes: int = 0
    population: str = "EUR"
    CYP2D6_phenotype: str = "Normal"
    CYP2C19_phenotype: str = "Normal"
    CYP2C9_phenotype: str = "Normal"
    CYP3A4_phenotype: str = "Normal"
    DPYD_phenotype: str = "Normal"
    TPMT_phenotype: str = "Normal"
    UGT1A1_phenotype: str = "Normal"
    VKORC1_phenotype: str = "Normal Sensitivity"


class PredictionRequest(BaseModel):
    patient: PatientInput
    drug_id: str


# ── API Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/drugs")
async def list_drugs(query: str = ""):
    """List all drugs or search by query."""
    if query:
        results = drug_db.search(query)
    else:
        results = drug_db.get_all_drugs()
    return {"drugs": results, "count": len(results)}


@app.get("/api/drugs/{drug_id}")
async def get_drug(drug_id: str):
    """Get detailed drug information."""
    drug = drug_db.get_drug(drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail=f"Drug '{drug_id}' not found")
    return drug


@app.get("/api/genes")
async def list_genes():
    """List all pharmacogenes."""
    return {"genes": drug_db.get_all_genes()}


@app.get("/api/populations")
async def list_populations():
    """List available populations."""
    return {
        "populations": [
            {"code": p, "name": POPULATION_NAMES[p]}
            for p in POPULATIONS
        ]
    }


@app.get("/api/database-stats")
async def database_stats():
    """Get database statistics."""
    return drug_db.get_statistics()


@app.post("/api/predict")
async def predict_adr(request: PredictionRequest):
    """Predict ADR risk for a patient-drug pair."""
    patient_dict = request.patient.model_dump()
    drug_id = request.drug_id

    if drug_id not in DRUG_DATABASE:
        raise HTTPException(status_code=404, detail=f"Drug '{drug_id}' not found")

    model = _get_model(drug_id)
    preprocessor = _get_preprocessor()

    # Get gene-based profile
    profile = mapper.get_patient_profile(patient_dict)
    drug_recs = mapper.get_drug_recommendations(patient_dict, drug_id)

    result = {
        "drug_id": drug_id,
        "drug_name": DRUG_DATABASE[drug_id]["name"],
        "gene_interactions": drug_recs.get("gene_interactions", []),
        "overall_gene_risk": drug_recs.get("overall_risk", "unknown"),
        "warnings": drug_recs.get("warnings", []),
    }

    # ML prediction if model available
    if model is not None:
        try:
            X = preprocessor.prepare_single_patient(patient_dict, drug_id)
            prediction = model.predict_single(X)
            result["ml_prediction"] = prediction

            # SHAP explanation
            try:
                from pharmacosafe.interpretability.shap_explainer import SHAPExplainer
                explainer = SHAPExplainer(model)
                explanation = explainer.explain_patient(X)
                result["shap_explanation"] = explanation
            except Exception:
                result["shap_explanation"] = None

            # Dosing recommendation
            dosing = recommender.recommend(patient_dict, drug_id, prediction["probability"])
            result["dosing_recommendation"] = dosing

        except Exception as e:
            result["ml_prediction"] = None
            result["error"] = str(e)
    else:
        # Rule-based fallback
        risk_map = {"high": 0.7, "moderate": 0.4, "low": 0.1}
        fallback_risk = risk_map.get(drug_recs.get("overall_risk", "low"), 0.2)
        result["ml_prediction"] = {
            "probability": fallback_risk,
            "risk_percent": round(fallback_risk * 100, 1),
            "risk_level": drug_recs.get("overall_risk", "Unknown").capitalize(),
            "note": "Rule-based estimate (ML model not trained for this drug)",
        }
        dosing = recommender.recommend(patient_dict, drug_id, fallback_risk)
        result["dosing_recommendation"] = dosing

    return result


@app.post("/api/upload")
async def upload_patient_file(file: UploadFile = File(...)):
    """Upload a patient data file (CSV or JSON)."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    try:
        parsed = parser.parse_auto(text, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return parsed


@app.get("/api/demo-patients")
async def get_demo_patients():
    """Get pre-loaded demo patient profiles."""
    demos = [
        {
            "id": "demo_1",
            "name": "Maria Santos",
            "description": "72-year-old Admixed American female on warfarin with CYP2C9 Poor metabolizer",
            "data": {
                "age": 72, "sex": "Female", "weight_kg": 62, "bmi": 26.1,
                "egfr": 48, "alt_u_l": 35, "n_comedications": 6,
                "smoking_status": "Former", "diabetes": 1, "population": "AMR",
                "CYP2C9_phenotype": "Poor", "VKORC1_phenotype": "High Sensitivity",
                "CYP2D6_phenotype": "Normal", "CYP2C19_phenotype": "Intermediate",
                "CYP3A4_phenotype": "Normal", "DPYD_phenotype": "Normal",
                "TPMT_phenotype": "Normal", "UGT1A1_phenotype": "Normal",
            },
            "suggested_drug": "warfarin",
        },
        {
            "id": "demo_2",
            "name": "James Okafor",
            "description": "45-year-old African male on clopidogrel with CYP2C19 Poor metabolizer",
            "data": {
                "age": 45, "sex": "Male", "weight_kg": 88, "bmi": 28.5,
                "egfr": 95, "alt_u_l": 28, "n_comedications": 3,
                "smoking_status": "Current", "diabetes": 0, "population": "AFR",
                "CYP2C19_phenotype": "Poor", "CYP2D6_phenotype": "Ultra-rapid",
                "CYP2C9_phenotype": "Normal", "CYP3A4_phenotype": "Intermediate",
                "DPYD_phenotype": "Normal", "TPMT_phenotype": "Normal",
                "UGT1A1_phenotype": "Intermediate", "VKORC1_phenotype": "Normal Sensitivity",
            },
            "suggested_drug": "clopidogrel",
        },
        {
            "id": "demo_3",
            "name": "Yuki Tanaka",
            "description": "34-year-old East Asian female prescribed codeine with CYP2D6 Ultra-rapid metabolizer",
            "data": {
                "age": 34, "sex": "Female", "weight_kg": 55, "bmi": 21.5,
                "egfr": 110, "alt_u_l": 18, "n_comedications": 1,
                "smoking_status": "Never", "diabetes": 0, "population": "EAS",
                "CYP2D6_phenotype": "Ultra-rapid", "CYP2C19_phenotype": "Poor",
                "CYP2C9_phenotype": "Normal", "CYP3A4_phenotype": "Normal",
                "DPYD_phenotype": "Normal", "TPMT_phenotype": "Normal",
                "UGT1A1_phenotype": "Normal", "VKORC1_phenotype": "High Sensitivity",
            },
            "suggested_drug": "codeine",
        },
        {
            "id": "demo_4",
            "name": "Raj Patel",
            "description": "58-year-old South Asian male on 5-FU with DPYD Intermediate metabolizer",
            "data": {
                "age": 58, "sex": "Male", "weight_kg": 72, "bmi": 25.8,
                "egfr": 75, "alt_u_l": 42, "n_comedications": 4,
                "smoking_status": "Former", "diabetes": 1, "population": "SAS",
                "DPYD_phenotype": "Intermediate", "CYP2D6_phenotype": "Normal",
                "CYP2C19_phenotype": "Intermediate", "CYP2C9_phenotype": "Intermediate",
                "CYP3A4_phenotype": "Normal", "TPMT_phenotype": "Normal",
                "UGT1A1_phenotype": "Normal", "VKORC1_phenotype": "Normal Sensitivity",
            },
            "suggested_drug": "fluorouracil",
        },
    ]
    return {"patients": demos}


@app.get("/api/fairness")
async def get_fairness_results():
    """Get cached fairness audit results."""
    report_path = REPORTS_DIR / "fairness_audit.json"
    if not report_path.exists():
        return {"message": "No fairness audit results. Run the pipeline first.", "results": {}}

    with open(report_path) as f:
        results = json.load(f)
    return {"results": results}


@app.get("/api/training-results")
async def get_training_results():
    """Get model training results."""
    results_path = MODELS_DIR / "training_results.json"
    if not results_path.exists():
        return {"message": "No training results. Run the pipeline first.", "results": {}}

    with open(results_path) as f:
        results = json.load(f)
    return {"results": results}


# ── Serve Frontend ─────────────────────────────────────────────────────────
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
