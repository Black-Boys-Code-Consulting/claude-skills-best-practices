let caseCounter = 0;
let examplesCache = null;

const el = (id) => document.getElementById(id);

const ICON_PASS = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8.5L6.5 12L13 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_FAIL = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function statusBadge(status) {
  return `<span class="status-badge ${status}">${status === "pass" ? ICON_PASS : ICON_FAIL}${status}</span>`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Renders an empty score tile + one bar segment per step, all "pending" —
// steps fill in one at a time via setStepSegment()/updateScoreValue() as
// each check/test case completes, instead of the whole result appearing at once.
function scoreSkeletonHtml(idPrefix, total, unit) {
  let segs = "";
  for (let i = 0; i < total; i++) {
    segs += `<div class="seg pending" data-index="${i}"></div>`;
  }
  return `
    <div class="score-summary-block">
      <div class="score-tile">
        <span class="value" id="${idPrefix}-value">0/${total}</span>
        <span class="label" id="${idPrefix}-label">${unit}</span>
      </div>
      <div class="step-bar" id="${idPrefix}-bar" role="img" aria-label="0 of ${total} ${unit} checked">${segs}</div>
      <div class="score-legend">
        <span class="item"><span class="swatch pending"></span>Pending</span>
        <span class="item"><span class="swatch pass"></span>Passed</span>
        <span class="item"><span class="swatch fail"></span>Failed</span>
      </div>
    </div>
  `;
}

function setStepSegment(idPrefix, index, status) {
  const bar = el(`${idPrefix}-bar`);
  const seg = bar && bar.querySelector(`[data-index="${index}"]`);
  if (seg) seg.className = `seg ${status}`;
}

function updateScoreValue(idPrefix, passedSoFar, doneSoFar, total) {
  const value = el(`${idPrefix}-value`);
  const label = el(`${idPrefix}-label`);
  if (!value) return;
  value.textContent = `${passedSoFar}/${doneSoFar}`;
  value.className = "value" + (doneSoFar === 0 ? "" : passedSoFar === doneSoFar ? " pass" : " fail");
  label.textContent = doneSoFar < total ? `checked ${doneSoFar} of ${total}…` : "passed";
}

function newCaseId() {
  caseCounter += 1;
  return `case_${caseCounter}`;
}

function splitList(value) {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function addCaseRow(data = {}) {
  const id = data.id || newCaseId();
  const wrapper = document.createElement("div");
  wrapper.className = "case-card";
  wrapper.dataset.caseId = id;
  wrapper.innerHTML = `
    <div class="case-head">
      <strong>${id}</strong>
      <button class="small ghost remove-case">Remove</button>
    </div>
    <label>Prompt</label>
    <input type="text" class="case-prompt" value="${escapeAttr(data.prompt || "")}" placeholder="What would a user actually ask?" />
    <div class="row">
      <div>
        <label>Must include (comma-separated)</label>
        <input type="text" class="case-must-include" value="${escapeAttr((data.must_include || []).join(", "))}" placeholder="read-only, owner" />
      </div>
      <div>
        <label>Must NOT include (comma-separated)</label>
        <input type="text" class="case-must-not-include" value="${escapeAttr((data.must_not_include || []).join(", "))}" placeholder="DELETE FROM, DROP TABLE" />
      </div>
    </div>
    <label>Notes (optional)</label>
    <input type="text" class="case-notes" value="${escapeAttr(data.notes || "")}" placeholder="Why this check matters" />
  `;
  wrapper.querySelector(".remove-case").addEventListener("click", () => wrapper.remove());
  el("case-list").appendChild(wrapper);
}

function escapeAttr(str) {
  return String(str).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

function clearCases() {
  el("case-list").innerHTML = "";
}

function collectCases() {
  return Array.from(document.querySelectorAll("#case-list .case-card")).map((card) => ({
    id: card.dataset.caseId,
    prompt: card.querySelector(".case-prompt").value.trim(),
    must_include: splitList(card.querySelector(".case-must-include").value),
    must_not_include: splitList(card.querySelector(".case-must-not-include").value),
    notes: card.querySelector(".case-notes").value.trim(),
  })).filter((c) => c.prompt);
}

function loadBundle(bundle) {
  el("skill-description").value = bundle.description || "";
  el("skill-instructions").value = bundle.instructions || "";
  el("compare-description").value = bundle.compare_description || "";
  clearCases();
  (bundle.test_cases || []).forEach(addCaseRow);
  if (!bundle.test_cases || bundle.test_cases.length === 0) {
    addCaseRow();
  }
  el("error-banner").innerHTML = "";
  el("lint-results").innerHTML = "";
  el("live-results").innerHTML = "";
  window.scrollTo({ top: el("skill-section").offsetTop - 20, behavior: "smooth" });
}

async function loadExamples() {
  const container = el("example-buttons");
  try {
    const resp = await fetch("/api/examples");
    const data = await resp.json();
    examplesCache = data;
    container.innerHTML = "";

    (data.good || []).forEach((bundle) => {
      const btn = document.createElement("button");
      btn.textContent = `Good: ${bundle.name}`;
      btn.addEventListener("click", () => loadBundle(bundle));
      container.appendChild(btn);
    });

    (data.bad || []).forEach((bundle) => {
      const btn = document.createElement("button");
      btn.textContent = `Bad: ${bundle.name}`;
      btn.addEventListener("click", () => loadBundle(bundle));
      container.appendChild(btn);
    });

    if (data.overlap) {
      const btn = document.createElement("button");
      btn.textContent = `Bad: ${data.overlap.name} (lint only)`;
      btn.addEventListener("click", () => loadBundle(data.overlap));
      container.appendChild(btn);
    }
  } catch (e) {
    container.innerHTML = '<span class="hint">Couldn\'t load examples from the server.</span>';
  }
}

async function renderLint(checks) {
  const container = el("lint-results");
  const total = checks.length;
  container.innerHTML = `<h3>Static lint</h3>${scoreSkeletonHtml("lint-score", total, "checks")}<div id="lint-steps"></div>`;
  const stepsEl = el("lint-steps");

  let passed = 0;
  for (let i = 0; i < checks.length; i++) {
    const c = checks[i];
    await sleep(220);

    if (c.status === "pass") passed += 1;
    setStepSegment("lint-score", i, c.status);
    updateScoreValue("lint-score", passed, i + 1, total);

    const div = document.createElement("div");
    div.className = `check-item step-card ${c.status}`;
    div.innerHTML = `
      <div class="step-label">Step ${i + 1} of ${total}</div>
      ${statusBadge(c.status)}<strong>${c.check}</strong>
      <div class="reco">${c.message}${c.anti_pattern ? ` <strong>(see ${c.anti_pattern})</strong>` : ""}</div>
    `;
    stepsEl.appendChild(div);
  }
}

async function runLint() {
  el("error-banner").innerHTML = "";
  const body = {
    description: el("skill-description").value,
    instructions: el("skill-instructions").value,
    compare_description: el("compare-description").value,
  };
  try {
    const resp = await fetch("/api/lint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "Lint failed.");
    await renderLint(data.checks);
  } catch (e) {
    showError(e.message);
  }
}

function renderRunningStep(evt) {
  const div = document.createElement("div");
  div.className = "result-item step-card running";
  div.dataset.stepIndex = evt.index;
  div.innerHTML = `
    <div class="step-label">Step ${evt.index} of ${evt.total}</div>
    <span class="status-badge running"><span class="spinner"></span>running</span>
    <strong>${evt.id}</strong> &mdash; ${escapeAttr(evt.prompt)}
  `;
  return div;
}

function fillInStep(div, r) {
  const recos = (r.recommendations || [])
    .map((rec) => `<div class="reco">&rarr; ${rec}</div>`)
    .join("");
  const failuresList = (r.failures || []).map((f) => `<div class="reco">- ${f}</div>`).join("");
  div.className = `result-item step-card ${r.passed ? "pass" : "fail"}`;
  div.innerHTML = `
    <div class="step-label">Step ${r.index} of ${r.total}</div>
    ${statusBadge(r.passed ? "pass" : "fail")}<strong>${r.id}</strong> &mdash; ${escapeAttr(r.prompt)}
    ${failuresList}
    ${recos}
    ${r.notes ? `<div class="reco"><strong>Note:</strong> ${escapeAttr(r.notes)}</div>` : ""}
    ${r.response ? `<details><summary>Show raw response</summary><pre>${escapeAttr(r.response)}</pre></details>` : ""}
  `;
}

async function runLive() {
  el("error-banner").innerHTML = "";
  const apiKey = el("api-key").value.trim();
  const cases = collectCases();

  if (!el("skill-description").value.trim() && !el("skill-instructions").value.trim()) {
    showError("Add a skill description and/or instructions first.");
    return;
  }
  if (cases.length === 0) {
    showError("Add at least one test case with a prompt.");
    return;
  }

  const runButton = el("run-live");
  runButton.disabled = true;
  runButton.textContent = "Running against Claude…";

  const total = cases.length;
  const container = el("live-results");
  container.innerHTML = `<h3>Live test results</h3>${scoreSkeletonHtml("live-score", total, "test cases")}<div id="live-steps"></div>`;
  const stepsEl = el("live-steps");
  const stepCards = {};

  const body = {
    description: el("skill-description").value,
    instructions: el("skill-instructions").value,
    test_cases: cases,
    api_key: apiKey,
    model: el("model-select").value,
  };

  try {
    const resp = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new Error(data.detail || "Evaluation failed.");
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        const evt = JSON.parse(line);

        if (evt.type === "start") {
          const div = renderRunningStep(evt);
          stepsEl.appendChild(div);
          stepCards[evt.index] = div;
        } else if (evt.type === "result") {
          setStepSegment("live-score", evt.index - 1, evt.passed ? "pass" : "fail");
          updateScoreValue("live-score", evt.passed_so_far, evt.index, evt.total);
          const div = stepCards[evt.index];
          if (div) fillInStep(div, evt);
        }
      }
    }
  } catch (e) {
    showError(e.message);
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run live test against Claude";
  }
}

function showError(message) {
  el("error-banner").innerHTML = `<div class="error-banner">${escapeAttr(message)}</div>`;
}

document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
  addCaseRow();
  el("add-case").addEventListener("click", () => addCaseRow());
  el("run-lint").addEventListener("click", runLint);
  el("run-live").addEventListener("click", runLive);
});
