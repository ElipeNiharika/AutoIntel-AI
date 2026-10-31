/**
 * AI Vehicle Service, Repair & Insurance Intelligence System
 * Admin Analytics Dashboard with Chart.js
 * Strictly database-driven KPIs and charts from MySQL Prediction records
 */

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const res = await fetch("/api/stats");
    const json = await res.json();

    if (json.status === "success") {
      const kpis = json.kpis;
      const kpiTotal = document.getElementById("kpiTotal");
      const kpiAvgCost = document.getElementById("kpiAvgCost");
      const kpiAvgTime = document.getElementById("kpiAvgTime");
      const kpiInsPct = document.getElementById("kpiInsPct");

      if (kpiTotal) {
        kpiTotal.textContent = kpis.total_predictions.toString();
      }

      if (kpiAvgCost) {
        kpiAvgCost.textContent = kpis.total_predictions > 0 
          ? `$${kpis.avg_cost.toFixed(2)}` 
          : "$0.00";
      }

      if (kpiAvgTime) {
        kpiAvgTime.textContent = kpis.total_predictions > 0 && kpis.avg_time > 0
          ? `${kpis.avg_time.toFixed(1)} hrs` 
          : "N/A";
      }

      if (kpiInsPct) {
        kpiInsPct.textContent = kpis.total_predictions > 0 
          ? `${kpis.insurance_pct.toFixed(1)}%` 
          : "N/A";
      }

      renderCharts(json.charts);
    }
  } catch (err) {
    console.error("Failed to load database dashboard metrics:", err);
  }
}

function renderCharts(chartsData) {
  if (!chartsData) return;

  // 1. Diagnosis Categories Doughnut Chart
  const ctxCat = document.getElementById("chartCategories");
  if (ctxCat && chartsData.categories) {
    const hasData = chartsData.categories.labels && chartsData.categories.labels.length > 0;
    const labels = hasData ? chartsData.categories.labels : ["No Saved Records"];
    const values = hasData ? chartsData.categories.values : [1];
    const colors = hasData ? [
      "#DD27F5", "#9333ea", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e"
    ] : ["rgba(255, 255, 255, 0.08)"];

    new Chart(ctxCat, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: "#0a0a0d",
          borderWidth: 3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#a1a1aa", boxWidth: 12, padding: 15, font: { weight: '600', size: 11 } }
          }
        }
      }
    });
  }

  // 2. Service Types Distribution Bar Chart
  const ctxSvc = document.getElementById("chartServices");
  if (ctxSvc && chartsData.services) {
    const hasData = chartsData.services.labels && chartsData.services.labels.length > 0;
    const labels = hasData ? chartsData.services.labels : ["No Workorders"];
    const values = hasData ? chartsData.services.values : [0];

    new Chart(ctxSvc, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Workorders",
          data: values,
          backgroundColor: "rgba(221, 39, 245, 0.75)",
          borderColor: "#DD27F5",
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            ticks: { color: "#a1a1aa", maxRotation: 25, minRotation: 25, font: { size: 10 } },
            grid: { color: "rgba(255, 255, 255, 0.04)" }
          },
          y: {
            ticks: { color: "#a1a1aa", precision: 0 },
            grid: { color: "rgba(255, 255, 255, 0.04)" }
          }
        }
      }
    });
  }

  // 3. Top Replaced Parts Chart
  const ctxParts = document.getElementById("chartParts");
  if (ctxParts && chartsData.top_parts) {
    const hasData = chartsData.top_parts.labels && chartsData.top_parts.labels.length > 0;
    const labels = hasData ? chartsData.top_parts.labels : ["No Replaced Parts"];
    const values = hasData ? chartsData.top_parts.values : [0];

    new Chart(ctxParts, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Frequency",
          data: values,
          backgroundColor: "rgba(147, 51, 234, 0.75)",
          borderColor: "#9333ea",
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            ticks: { color: "#a1a1aa", precision: 0 },
            grid: { color: "rgba(255, 255, 255, 0.04)" }
          },
          y: {
            ticks: { color: "#a1a1aa", font: { size: 11 } },
            grid: { color: "rgba(255, 255, 255, 0.04)" }
          }
        }
      }
    });
  }
}
