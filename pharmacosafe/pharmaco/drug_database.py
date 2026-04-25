"""
Drug Database for PharmacoSafe.
Provides structured access to the drug-gene interaction database.
"""

from typing import List, Optional, Dict
from pharmacosafe.config import DRUG_DATABASE, PHARMACOGENES


class DrugDatabase:
    """Structured interface to the drug-gene interaction database."""

    def __init__(self):
        self.drugs = DRUG_DATABASE
        self.genes = PHARMACOGENES

    def get_all_drugs(self) -> List[dict]:
        """Get summary list of all drugs in the database."""
        return [
            {
                "drug_id": drug_id,
                "name": info["name"],
                "class": info["class"],
                "indication": info["indication"],
                "key_genes": info["key_genes"],
                "severe_adr_rate": info["severe_adr_rate"],
            }
            for drug_id, info in self.drugs.items()
        ]

    def get_drug(self, drug_id: str) -> Optional[dict]:
        """Get detailed information about a specific drug."""
        if drug_id not in self.drugs:
            return None
        info = self.drugs[drug_id]
        return {"drug_id": drug_id, **info}

    def get_drugs_for_gene(self, gene_name: str) -> List[dict]:
        """Find all drugs affected by a specific gene."""
        results = []
        for drug_id, info in self.drugs.items():
            if gene_name in info["key_genes"]:
                results.append({"drug_id": drug_id, **info})
        return results

    def search(self, query: str) -> List[dict]:
        """Search drugs by name, class, indication, or gene."""
        query_lower = query.lower().strip()
        if not query_lower:
            return self.get_all_drugs()

        results = []
        for drug_id, info in self.drugs.items():
            searchable = " ".join([
                drug_id, info["name"], info["class"],
                info["indication"], " ".join(info["key_genes"]),
                " ".join(info["common_adrs"]),
            ]).lower()

            if query_lower in searchable:
                results.append({"drug_id": drug_id, **info})

        return results

    def get_all_genes(self) -> List[dict]:
        """Get summary of all pharmacogenes."""
        return [
            {
                "gene": gene_name,
                "description": info["description"],
                "phenotypes": info["phenotypes"],
                "n_affected_drugs": len(self.get_drugs_for_gene(gene_name)),
            }
            for gene_name, info in self.genes.items()
        ]

    def get_statistics(self) -> dict:
        """Get database statistics."""
        drug_classes = set(info["class"] for info in self.drugs.values())
        return {
            "n_drugs": len(self.drugs),
            "n_genes": len(self.genes),
            "n_drug_classes": len(drug_classes),
            "drug_classes": sorted(drug_classes),
            "avg_severe_adr_rate": sum(
                info["severe_adr_rate"] for info in self.drugs.values()
            ) / len(self.drugs),
        }
