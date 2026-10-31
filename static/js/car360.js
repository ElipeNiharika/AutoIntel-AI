/**
 * 🚗 AutoIntel AI - High-Definition 360° Interactive Canvas 3D Vehicle Turntable
 * Pure Frontend Vector Mathematics & Real-Time Canvas 3D Rendering (Zero DL / Computer Vision)
 */

class CarTurntable360 {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext("2d");
    this.angle = 0.55; // Initial rotation angle
    this.autoRotateSpeed = 0.008;
    this.isAutoRotating = true;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.dragSensitivity = 0.008;
    this.autoResumeTimer = null;

    this.initCanvasSize();
    this.setupEventListeners();
    this.startAnimationLoop();
  }

  initCanvasSize() {
    const parent = this.canvas.parentElement;
    const rect = parent ? parent.getBoundingClientRect() : { width: 500 };
    const dpr = window.devicePixelRatio || 1;
    this.width = Math.min(rect.width > 50 ? rect.width : 500, 520);
    this.height = 300;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(dpr, dpr);
  }

  setupEventListeners() {
    window.addEventListener("resize", () => this.initCanvasSize());

    // Mouse Drag Controls
    this.canvas.addEventListener("mousedown", (e) => {
      this.isDragging = true;
      this.isAutoRotating = false;
      this.lastMouseX = e.clientX;
      this.canvas.style.cursor = "grabbing";
      if (this.autoResumeTimer) clearTimeout(this.autoResumeTimer);
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      const deltaX = e.clientX - this.lastMouseX;
      this.angle += deltaX * this.dragSensitivity;
      this.lastMouseX = e.clientX;
    });

    window.addEventListener("mouseup", () => {
      if (this.isDragging) {
        this.isDragging = false;
        this.canvas.style.cursor = "grab";
        this.autoResumeTimer = setTimeout(() => { this.isAutoRotating = true; }, 2500);
      }
    });

    // Touch Drag Controls (Mobile & Tablet)
    this.canvas.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.isAutoRotating = false;
        this.lastMouseX = e.touches[0].clientX;
        if (this.autoResumeTimer) clearTimeout(this.autoResumeTimer);
      }
    }, { passive: true });

    window.addEventListener("touchmove", (e) => {
      if (!this.isDragging || e.touches.length !== 1) return;
      const deltaX = e.touches[0].clientX - this.lastMouseX;
      this.angle += deltaX * this.dragSensitivity;
      this.lastMouseX = e.touches[0].clientX;
    }, { passive: true });

    window.addEventListener("touchend", () => {
      if (this.isDragging) {
        this.isDragging = false;
        this.autoResumeTimer = setTimeout(() => { this.isAutoRotating = true; }, 2500);
      }
    });

    // Control Buttons
    const btnPause = document.getElementById("btn360Pause");
    const btn1x = document.getElementById("btn3601x");
    const btn2x = document.getElementById("btn3602x");

    if (btnPause) {
      btnPause.addEventListener("click", () => {
        this.isAutoRotating = !this.isAutoRotating;
        btnPause.textContent = this.isAutoRotating ? "⏸ Pause" : "▶ Rotate";
      });
    }

    if (btn1x) {
      btn1x.addEventListener("click", () => {
        this.autoRotateSpeed = 0.008;
        this.isAutoRotating = true;
        btn1x.classList.add("active");
        if (btn2x) btn2x.classList.remove("active");
      });
    }

    if (btn2x) {
      btn2x.addEventListener("click", () => {
        this.autoRotateSpeed = 0.016;
        this.isAutoRotating = true;
        btn2x.classList.add("active");
        if (btn1x) btn1x.classList.remove("active");
      });
    }
  }

  startAnimationLoop() {
    const loop = () => {
      if (this.isAutoRotating && !this.isDragging) {
        this.angle += this.autoRotateSpeed;
      }
      this.render();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  render() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h / 2 + 25;

    ctx.clearRect(0, 0, w, h);

    // 1. Draw 3D Ground Holographic Turntable
    ctx.save();
    ctx.translate(cx, cy + 32);
    ctx.scale(1, 0.32);

    // Ground Shadow & Radial Glow
    const gradRing = ctx.createRadialGradient(0, 0, 60, 0, 0, 210);
    gradRing.addColorStop(0, "rgba(221, 39, 245, 0.28)");
    gradRing.addColorStop(0.6, "rgba(56, 189, 248, 0.08)");
    gradRing.addColorStop(1, "transparent");
    ctx.fillStyle = gradRing;
    ctx.beginPath();
    ctx.arc(0, 0, 210, 0, Math.PI * 2);
    ctx.fill();

    // Turntable Edge Ring
    ctx.strokeStyle = "rgba(221, 39, 245, 0.35)";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(0, 0, 185, 0, Math.PI * 2);
    ctx.stroke();

    // Inner Telemetry Track
    ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
    ctx.lineWidth = 1.2;
    ctx.setLineDash([8, 12]);
    ctx.beginPath();
    ctx.arc(0, 0, 145, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 2. 3D Isometric Perspective Projection
    const cosA = Math.cos(this.angle);
    const sinA = Math.sin(this.angle);
    const tilt = 0.28;

    const project = (x, y, z) => {
      const rx = x * cosA - z * sinA;
      const rz = x * sinA + z * cosA;
      const scale = 1.05;
      const px = cx + rx * scale;
      const py = cy - y * scale + rz * tilt * scale;
      return { x: px, y: py, z: rz };
    };

    // 3. Define 3D Vehicle Geometry (Sleek Modern Electric Fastback)
    const wheels = [
      { x: 58, y: 15, z: 38 },   // Front Right
      { x: 58, y: 15, z: -38 },  // Front Left
      { x: -58, y: 15, z: 38 },  // Rear Right
      { x: -58, y: 15, z: -38 }, // Rear Left
    ];

    const pts = {
      noseL: project(85, 20, -32),
      noseR: project(85, 20, 32),
      hoodL: project(38, 38, -34),
      hoodR: project(38, 38, 34),
      windL: project(10, 58, -30),
      windR: project(10, 58, 30),
      roofL: project(-35, 60, -28),
      roofR: project(-35, 60, 28),
      rearGlassL: project(-68, 42, -32),
      rearGlassR: project(-68, 42, 32),
      tailL: project(-86, 30, -32),
      tailR: project(-86, 30, 32),
      skirtFL: project(80, 12, -34),
      skirtFR: project(80, 12, 34),
      skirtBL: project(-82, 12, -34),
      skirtBR: project(-82, 12, 34)
    };

    // Sort Wheels by Z-depth
    const projWheels = wheels.map((w, idx) => ({ ...project(w.x, w.y, w.z), idx }));
    projWheels.sort((a, b) => a.z - b.z);

    // Draw Back Wheels
    projWheels.filter(w => w.z < 0).forEach(w => this.drawWheel(ctx, w.x, w.y));

    // Underbody Shadow
    ctx.fillStyle = "rgba(6, 7, 12, 0.85)";
    ctx.beginPath();
    ctx.moveTo(pts.skirtFL.x, pts.skirtFL.y);
    ctx.lineTo(pts.skirtFR.x, pts.skirtFR.y);
    ctx.lineTo(pts.skirtBR.x, pts.skirtBR.y);
    ctx.lineTo(pts.skirtBL.x, pts.skirtBL.y);
    ctx.closePath();
    ctx.fill();

    // 4. Draw Panels with Metallic Shading
    const drawFace = (p1, p2, p3, p4, fillColor, strokeColor) => {
      ctx.fillStyle = fillColor;
      ctx.strokeStyle = strokeColor || "rgba(221, 39, 245, 0.35)";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.lineTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    };

    // Top Surfaces
    drawFace(pts.noseL, pts.noseR, pts.hoodR, pts.hoodL, "rgba(20, 24, 38, 0.96)", "#DD27F5"); // Hood
    drawFace(pts.hoodL, pts.hoodR, pts.windR, pts.windL, "rgba(56, 189, 248, 0.22)", "rgba(56, 189, 248, 0.7)"); // Windshield
    drawFace(pts.windL, pts.windR, pts.roofR, pts.roofL, "rgba(14, 17, 28, 0.98)", "#DD27F5"); // Roof
    drawFace(pts.roofL, pts.roofR, pts.rearGlassR, pts.rearGlassL, "rgba(56, 189, 248, 0.18)", "rgba(56, 189, 248, 0.6)"); // Rear Glass
    drawFace(pts.rearGlassL, pts.rearGlassR, pts.tailR, pts.tailL, "rgba(20, 24, 38, 0.96)", "#DD27F5"); // Trunk

    // Flanks
    drawFace(pts.noseL, pts.hoodL, pts.skirtFL, pts.skirtBL, "rgba(16, 19, 32, 0.92)", "rgba(221, 39, 245, 0.35)");
    drawFace(pts.noseR, pts.hoodR, pts.skirtFR, pts.skirtBR, "rgba(24, 28, 44, 0.92)", "rgba(221, 39, 245, 0.35)");

    // 5. LED Headlight & Tail Light Bars
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(pts.noseL.x, pts.noseL.y);
    ctx.lineTo(pts.noseR.x, pts.noseR.y);
    ctx.stroke();

    ctx.strokeStyle = "#f43f5e";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(pts.tailL.x, pts.tailL.y);
    ctx.lineTo(pts.tailR.x, pts.tailR.y);
    ctx.stroke();

    // 6. Draw Front Wheels (Overbody)
    projWheels.filter(w => w.z >= 0).forEach(w => this.drawWheel(ctx, w.x, w.y));
  }

  drawWheel(ctx, x, y) {
    ctx.save();
    ctx.translate(x, y);

    // Tire
    ctx.fillStyle = "#0c0d12";
    ctx.strokeStyle = "#DD27F5";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Alloy Rim
    ctx.fillStyle = "#27272a";
    ctx.beginPath();
    ctx.arc(0, 0, 10, 0, Math.PI * 2);
    ctx.fill();

    // Hub Cap
    ctx.fillStyle = "#38bdf8";
    ctx.beginPath();
    ctx.arc(0, 0, 3.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }
}

// Auto-initialize on load
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("carTurntableCanvas")) {
    window.turntableInstance = new CarTurntable360("carTurntableCanvas");
  }
});
