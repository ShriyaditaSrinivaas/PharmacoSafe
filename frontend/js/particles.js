/**
 * PharmacoSafe — Animated Molecule Particle Background
 * Creates floating connected particles resembling molecular structures.
 */

class ParticleSystem {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: null, y: null };
        this.config = {
            count: 80,
            maxSpeed: 0.4,
            size: { min: 1.5, max: 3.5 },
            connectionDistance: 150,
            mouseRadius: 200,
            colors: ['#00f5d4', '#7b2ff7', '#00d4ff', '#9945ff', '#f72fa0'],
        };

        this.init();
        this.bindEvents();
        this.animate();
    }

    init() {
        this.resize();
        for (let i = 0; i < this.config.count; i++) {
            this.particles.push(this.createParticle());
        }
    }

    createParticle() {
        const color = this.config.colors[Math.floor(Math.random() * this.config.colors.length)];
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            vx: (Math.random() - 0.5) * this.config.maxSpeed,
            vy: (Math.random() - 0.5) * this.config.maxSpeed,
            size: this.config.size.min + Math.random() * (this.config.size.max - this.config.size.min),
            color: color,
            alpha: 0.3 + Math.random() * 0.5,
            pulse: Math.random() * Math.PI * 2,
            pulseSpeed: 0.01 + Math.random() * 0.02,
        };
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    bindEvents() {
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
        window.addEventListener('mouseout', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update and draw particles
        this.particles.forEach((p, i) => {
            // Update position
            p.x += p.vx;
            p.y += p.vy;
            p.pulse += p.pulseSpeed;

            // Bounce off edges
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;

            // Mouse repulsion
            if (this.mouse.x !== null) {
                const dx = p.x - this.mouse.x;
                const dy = p.y - this.mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < this.config.mouseRadius) {
                    const force = (this.config.mouseRadius - dist) / this.config.mouseRadius;
                    p.vx += (dx / dist) * force * 0.02;
                    p.vy += (dy / dist) * force * 0.02;
                }
            }

            // Speed limit
            const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
            if (speed > this.config.maxSpeed * 2) {
                p.vx *= 0.95;
                p.vy *= 0.95;
            }

            // Draw particle with pulse
            const pulseSize = p.size + Math.sin(p.pulse) * 0.5;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, pulseSize, 0, Math.PI * 2);
            this.ctx.fillStyle = p.color;
            this.ctx.globalAlpha = p.alpha * (0.7 + Math.sin(p.pulse) * 0.3);
            this.ctx.fill();

            // Outer glow
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, pulseSize * 2.5, 0, Math.PI * 2);
            this.ctx.fillStyle = p.color;
            this.ctx.globalAlpha = 0.05;
            this.ctx.fill();
        });

        // Draw connections
        this.ctx.globalAlpha = 1;
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const a = this.particles[i];
                const b = this.particles[j];
                const dx = a.x - b.x;
                const dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < this.config.connectionDistance) {
                    const alpha = (1 - dist / this.config.connectionDistance) * 0.15;
                    this.ctx.beginPath();
                    this.ctx.moveTo(a.x, a.y);
                    this.ctx.lineTo(b.x, b.y);
                    this.ctx.strokeStyle = a.color;
                    this.ctx.globalAlpha = alpha;
                    this.ctx.lineWidth = 0.8;
                    this.ctx.stroke();
                }
            }
        }

        this.ctx.globalAlpha = 1;
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize
const particleSystem = new ParticleSystem('particle-canvas');
