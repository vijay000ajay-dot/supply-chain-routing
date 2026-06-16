/**
 * Frontend logic for the Supply Chain Routing dashboard.
 */

const form = document.getElementById("route-form");
const sourceSelect = document.getElementById("source");
const destinationSelect = document.getElementById("destination");
const metricSelect = document.getElementById("metric");
const metricDescription = document.getElementById("metric-description");
const findRouteBtn = document.getElementById("find-route-btn");
const btnLabel = findRouteBtn.querySelector(".btn-label");
const btnSpinner = findRouteBtn.querySelector(".btn-spinner");
const formError = document.getElementById("form-error");

const resultsSection = document.getElementById("results-section");
const resultSubtitle = document.getElementById("result-subtitle");
const pathDisplay = document.getElementById("path-display");
const statDistance = document.getElementById("stat-distance");
const statCost = document.getElementById("stat-cost");
const statTime = document.getElementById("stat-time");
const statRisk = document.getElementById("stat-risk");
const legsContainer = document.getElementById("legs-container");
const complexityContent = document.getElementById("complexity-content");

const metricDescriptions = Object.fromEntries(
  (window.METRIC_DESCRIPTIONS || []).map((item) => [item.value, item.description])
);

/**
 * Format INR currency for display.
 * @param {number} value
 * @returns {string}
 */
function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Show or hide the inline form error message.
 * @param {string} message
 */
function showError(message) {
  if (!message) {
    formError.hidden = true;
    formError.textContent = "";
    return;
  }
  formError.hidden = false;
  formError.textContent = message;
}

/**
 * Toggle loading state on the submit button.
 * @param {boolean} isLoading
 */
function setLoading(isLoading) {
  findRouteBtn.disabled = isLoading;
  btnLabel.textContent = isLoading ? "Computing..." : "Find Route";
  btnSpinner.hidden = !isLoading;
}

/**
 * Prevent selecting the same hub for source and destination.
 */
function syncDestinationOptions() {
  const sourceValue = sourceSelect.value;
  Array.from(destinationSelect.options).forEach((option) => {
    if (!option.value) {
      return;
    }
    option.disabled = option.value === sourceValue;
  });

  if (destinationSelect.value === sourceValue) {
    destinationSelect.value = "";
  }
}

/**
 * Update metric helper text when selection changes.
 */
function updateMetricDescription() {
  metricDescription.textContent =
    metricDescriptions[metricSelect.value] || "Select a routing strategy.";
}

/**
 * Render animated path nodes in the results banner.
 * @param {string[]} path
 */
function renderPath(path) {
  pathDisplay.innerHTML = "";

  path.forEach((node, index) => {
    const nodeEl = document.createElement("span");
    nodeEl.className = "path-node";
    nodeEl.textContent = node;
    pathDisplay.appendChild(nodeEl);

    if (index < path.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "path-arrow";
      arrow.textContent = "→";
      pathDisplay.appendChild(arrow);
    }
  });
}

/**
 * Render leg cards for the step-by-step trajectory.
 * @param {Array<object>} steps
 */
function renderLegs(steps) {
  legsContainer.innerHTML = "";

  steps.forEach((step) => {
    const card = document.createElement("article");
    card.className = "leg-card";
    card.innerHTML = `
      <div class="leg-index">${step.leg}</div>
      <div>
        <p class="leg-title">${step.from} → ${step.to}</p>
        <div class="leg-meta">
          <span><strong>Distance:</strong> ${step.distance_km} km</span>
          <span><strong>Fuel:</strong> ${formatCurrency(step.fuel_cost_inr)}</span>
          <span><strong>Time:</strong> ${step.transit_hours} hrs</span>
          <span><strong>Risk:</strong> ${step.risk_factor}</span>
          <span><strong>Types:</strong> ${step.from_type} → ${step.to_type}</span>
        </div>
      </div>
    `;
    legsContainer.appendChild(card);
  });
}

/**
 * Render complexity analysis grid.
 * @param {object} complexity
 */
function renderComplexity(complexity) {
  const rows = [
    ["Algorithm", complexity.algorithm],
    ["Time (Big-O)", complexity.time],
    ["Space (Big-O)", complexity.space],
    ["Heap Insert", complexity.heap_insert],
    ["Heap Extract", complexity.heap_extract_min],
    ["Path Rebuild", complexity.path_reconstruction],
    ["Relaxations", String(complexity.relaxations)],
    ["Heap Operations", String(complexity.heap_operations)],
  ];

  complexityContent.innerHTML = rows
    .map(
      ([label, value]) => `
        <div>
          <div>${label}</div>
          <span>${value}</span>
        </div>
      `
    )
    .join("");
}

/**
 * Populate the results panel from API response.
 * @param {object} data
 */
function renderResults(data) {
  resultsSection.hidden = false;
  resultSubtitle.textContent = `${data.metric_label} • ${data.summary.hops} hop(s)`;

  renderPath(data.path);

  statDistance.textContent = `${data.summary.total_distance_km} km`;
  statCost.textContent = formatCurrency(data.summary.total_fuel_cost_inr);
  statTime.textContent = `${data.summary.total_transit_hours} hrs`;
  statRisk.textContent = data.summary.max_risk_factor;

  renderLegs(data.steps);
  renderComplexity(data.complexity);

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Submit route request to Flask API.
 * @param {SubmitEvent} event
 */
async function handleSubmit(event) {
  event.preventDefault();
  showError("");

  const source = sourceSelect.value;
  const destination = destinationSelect.value;
  const metric = metricSelect.value;

  if (!source || !destination) {
    showError("Please select both a starting hub and a destination.");
    return;
  }

  if (source === destination) {
    showError("Source and destination must be different.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, destination, metric }),
    });

    const data = await response.json();

    if (!response.ok) {
      showError(data.error || "Unable to compute route.");
      return;
    }

    renderResults(data);
  } catch (error) {
    showError("Network error. Is the Flask server running?");
  } finally {
    setLoading(false);
  }
}

sourceSelect.addEventListener("change", syncDestinationOptions);
metricSelect.addEventListener("change", updateMetricDescription);
form.addEventListener("submit", handleSubmit);

syncDestinationOptions();
updateMetricDescription();
