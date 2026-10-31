/**
 * AI Vehicle Service, Repair & Insurance Intelligence System
 * Frontend Controller: Dynamic Dropdowns, Multi-Model AJAX Inferences, 360 Turntable
 */

let vehicleMetadata = {};

document.addEventListener("DOMContentLoaded", async () => {
  await loadVehicleMetadata();
  setupDynamicDropdowns();
  setupPredictForm();
  setupDiagnoseForm();
  setupFraudForm();
  setupCarTurntableControls();
});

// 1. Fetch Vehicle Metadata for Dynamic Dropdowns
async function loadVehicleMetadata() {
  try {
    const res = await fetch("/api/vehicle-metadata");
    if (res.ok) {
      vehicleMetadata = await res.json();
    }
  } catch (err) {
    console.warn("Could not fetch dynamic vehicle metadata:", err);
  }
}

// 2. Setup Cascading Brand -> Model Dropdowns
function setupDynamicDropdowns() {
  const brandSelect = document.getElementById("brandSelect");
  const modelSelect = document.getElementById("modelSelect");

  if (!brandSelect || !modelSelect) return;

  brandSelect.addEventListener("change", () => {
    const selectedBrand = brandSelect.value;
    modelSelect.innerHTML = '<option value="">-- Select Model --</option>';

    if (selectedBrand && vehicleMetadata.brand_models && vehicleMetadata.brand_models[selectedBrand]) {
      const models = vehicleMetadata.brand_models[selectedBrand];
      models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        modelSelect.appendChild(opt);
      });
      if (models.length > 0) modelSelect.value = models[0];
    } else {
      const fallbackModels = ["Standard Model", "Base Edition", "Sport Edition", "Luxury Trim"];
      fallbackModels.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        modelSelect.appendChild(opt);
      });
    }
  });

  if (brandSelect.value) {
    brandSelect.dispatchEvent(new Event("change"));
  }
}

// 3. Multi-Model Predict Form Submission
function setupPredictForm() {
  const form = document.getElementById("predictForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitPredict");
    const originalText = btn ? btn.innerHTML : "Predict";
    if (btn) btn.innerHTML = "<span>⏳ Computing Pure ML Inferences...</span>";

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const json = await res.json();

      if (json.status === "success") {
        const data = json.data;
        const resultBox = document.getElementById("predictionResultBox");
        if (resultBox) {
          resultBox.style.display = "block";
          resultBox.scrollIntoView({ behavior: "smooth" });
        }

        const resCost = document.getElementById("resCost");
        const resTime = document.getElementById("resTime");
        const resVariance = document.getElementById("resVariance");
        const resInsBadge = document.getElementById("resInsuranceBadge");
        const resProb = document.getElementById("resProbability");
        const resProbBar = document.getElementById("resProbBar");

        if (resCost) resCost.textContent = `$${data.predicted_cost.toFixed(2)}`;
        if (resTime) resTime.textContent = `${data.predicted_time_hours.toFixed(1)} hrs`;
        if (resVariance) {
          const varSign = data.estimated_vs_actual_variance >= 0 ? "+$" : "-$";
          resVariance.textContent = `${varSign}${Math.abs(data.estimated_vs_actual_variance).toFixed(2)}`;
        }

        if (resInsBadge) {
          if (data.predicted_insurance_claim === 1) {
            resInsBadge.className = "badge badge-success";
            resInsBadge.textContent = "Likely Approved / Covered";
          } else {
            resInsBadge.className = "badge badge-warning";
            resInsBadge.textContent = "Direct Out-of-Pocket / Claim Unlikely";
          }
        }

        if (resProb) resProb.textContent = `${data.insurance_probability_pct}%`;
        if (resProbBar) resProbBar.style.width = `${data.insurance_probability_pct}%`;
      } else {
        alert("Prediction error: " + json.message);
      }
    } catch (err) {
      alert("Network or inference error: " + err.message);
    } finally {
      if (btn) btn.innerHTML = originalText;
    }
  });
}

// 4. Dedicated Insurance Fraud Form Submission
function setupFraudForm() {
  const form = document.getElementById("fraudForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitFraud");
    const originalText = btn ? btn.innerHTML : "Audit Fraud";
    if (btn) btn.innerHTML = "<span>⏳ Scanning Claim Telemetry...</span>";

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch("/api/predict/fraud", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const json = await res.json();

      if (json.status === "success") {
        const data = json.data;
        const resBox = document.getElementById("fraudResultBox");
        if (resBox) {
          resBox.style.display = "block";
          resBox.scrollIntoView({ behavior: "smooth" });
        }

        const resFraudBadge = document.getElementById("resFraudBadge");
        const resFraudProb = document.getElementById("resFraudProb");
        const resFraudBar = document.getElementById("resFraudBar");
        const resModelName = document.getElementById("resModelName");

        if (resFraudBadge) {
          resFraudBadge.className = `badge ${data.risk_badge}`;
          resFraudBadge.textContent = data.risk_level;
        }

        if (resFraudProb) resFraudProb.textContent = `${data.fraud_probability_pct}%`;
        if (resFraudBar) resFraudBar.style.width = `${data.fraud_probability_pct}%`;
        if (resModelName) resModelName.textContent = data.model_name;
      } else {
        alert("Fraud audit error: " + json.message);
      }
    } catch (err) {
      alert("Network or audit error: " + err.message);
    } finally {
      if (btn) btn.innerHTML = originalText;
    }
  });
}

// 5. Diagnostic Agent Form Submission
function setupDiagnoseForm() {
  const form = document.getElementById("diagnoseForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitDiag");
    const originalText = btn ? btn.innerHTML : "Diagnose";
    if (btn) btn.innerHTML = "<span>🔍 Running NLP Diagnostic Agent...</span>";

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const json = await res.json();

      if (json.status === "success") {
        const data = json.data;
        const resBox = document.getElementById("diagResultBox");
        if (resBox) {
          resBox.style.display = "block";
          resBox.scrollIntoView({ behavior: "smooth" });
        }

        const diagCat = document.getElementById("diagCategory");
        const diagSeverity = document.getElementById("diagSeverity");
        const diagName = document.getElementById("diagName");
        const diagFix = document.getElementById("diagFix");
        const diagReplace = document.getElementById("diagReplaceParts");
        const diagRepair = document.getElementById("diagRepairActions");

        if (diagCat) diagCat.textContent = data.problem_classification;
        if (diagSeverity) {
          diagSeverity.className = `badge ${data.severity_badge}`;
          diagSeverity.textContent = `${data.severity} Severity`;
        }
        if (diagName) diagName.textContent = data.diagnosis;
        if (diagFix) diagFix.textContent = data.how_to_fix;

        if (diagReplace) {
          diagReplace.innerHTML = data.recommended_replace_parts.map(p => `<li>🔴 <strong>Replace:</strong> ${p}</li>`).join("");
        }
        if (diagRepair) {
          diagRepair.innerHTML = data.recommended_repair_actions.map(a => `<li>🟢 <strong>Action:</strong> ${a}</li>`).join("");
        }
      } else {
        alert("Diagnostic error: " + json.message);
      }
    } catch (err) {
      alert("Network or diagnostic error: " + err.message);
    } finally {
      if (btn) btn.innerHTML = originalText;
    }
  });
}

// 6. 360-Degree Rotating Car Turntable Controls
function setupCarTurntableControls() {
  const stage = document.getElementById("carStage");
  if (!stage) return;

  const btnPause = document.getElementById("btnTurntablePause");
  const btnSpeed1 = document.getElementById("btnTurntable1x");
  const btnSpeed2 = document.getElementById("btnTurntable2x");

  if (btnPause) {
    btnPause.addEventListener("click", () => {
      stage.classList.toggle("paused");
      btnPause.textContent = stage.classList.contains("paused") ? "▶ Play" : "⏸ Pause";
    });
  }

  if (btnSpeed1) {
    btnSpeed1.addEventListener("click", () => {
      stage.style.animationDuration = "16s";
      btnSpeed1.classList.add("active");
      if (btnSpeed2) btnSpeed2.classList.remove("active");
    });
  }

  if (btnSpeed2) {
    btnSpeed2.addEventListener("click", () => {
      stage.style.animationDuration = "8s";
      btnSpeed2.classList.add("active");
      if (btnSpeed1) btnSpeed1.classList.remove("active");
    });
  }
}

// 7. Quick Demo Scenarios
function fillDemoData(type) {
  const brandSelect = document.getElementById("brandSelect");
  const modelSelect = document.getElementById("modelSelect");
  const estCost = document.getElementById("estimatedCost");
  const partsUsed = document.getElementById("partsUsed");
  const serviceDesc = document.getElementById("serviceDescription");
  const serviceType = document.getElementById("serviceType");

  if (type === "brake") {
    if (brandSelect) brandSelect.value = "Toyota";
    if (brandSelect) brandSelect.dispatchEvent(new Event("change"));
    setTimeout(() => { if (modelSelect) modelSelect.value = "Camry"; }, 100);
    if (serviceType) serviceType.value = "Brake System Service";
    if (estCost) estCost.value = "240.00";
    if (partsUsed) partsUsed.value = "brake pads, brake rotor, brake fluid";
    if (serviceDesc) serviceDesc.value = "Squealing noise upon brake application at low speeds.";
  } else if (type === "engine") {
    if (brandSelect) brandSelect.value = "BMW";
    if (brandSelect) brandSelect.dispatchEvent(new Event("change"));
    setTimeout(() => { if (modelSelect) modelSelect.value = "3 Series"; }, 100);
    if (serviceType) serviceType.value = "Engine Diagnostics & Tune-up";
    if (estCost) estCost.value = "650.00";
    if (partsUsed) partsUsed.value = "spark plugs, oxygen sensor, oil filter";
    if (serviceDesc) serviceDesc.value = "Check engine light illuminated with rough idling on cold start.";
  }
}
