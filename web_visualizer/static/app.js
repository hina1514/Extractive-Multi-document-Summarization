const textInputs = document.querySelector("#textInputs");
const addTextBtn = document.querySelector("#addTextBtn");
const fileInput = document.querySelector("#fileInput");
const fileList = document.querySelector("#fileList");
const runBtn = document.querySelector("#runBtn");
const statusEl = document.querySelector("#status");
const summaryLength = document.querySelector("#summaryLength");
const statsBar = document.querySelector("#statsBar");
const tabs = [...document.querySelectorAll(".step-tab")];
const nextButtons = [...document.querySelectorAll(".next-step")];
const copyBtn = document.querySelector("#copyBtn");

let resultData = null;
let inputCount = 1;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("is-error", isError);
}

function activateStep(step) {
  tabs.forEach((tab) => {
    const isActive = tab.dataset.step === step;
    tab.classList.toggle("is-active", isActive);
  });

  document.querySelectorAll(".step-panel").forEach((panel) => {
    panel.classList.toggle("is-active", panel.id === `${step}Panel`);
  });
}

function unlockSteps() {
  tabs.forEach((tab) => {
    tab.disabled = false;
  });
  nextButtons.forEach((button) => {
    button.disabled = false;
  });
  copyBtn.disabled = false;
}

function addTextBox(value = "") {
  inputCount += 1;
  const block = document.createElement("article");
  block.className = "text-box";
  block.innerHTML = `
    <div class="text-box-header">
      <span>Văn bản ${inputCount}</span>
      <button class="remove-text" type="button" title="Xóa văn bản">×</button>
    </div>
    <textarea name="texts">${escapeHtml(value)}</textarea>
  `;
  textInputs.appendChild(block);
}

function renderFiles() {
  const files = [...fileInput.files];
  fileList.innerHTML = files.map((file) => `<span class="file-chip">${escapeHtml(file.name)}</span>`).join("");
}

function updateStats(stats = {}) {
  const values = [
    [stats.documentCount || 0, "văn bản"],
    [stats.sentenceCount || 0, "câu"],
    [stats.clusterCount || 0, "cụm"],
    [stats.summaryLength || 0, "câu tóm tắt"],
  ];

  statsBar.innerHTML = values
    .map(([value, label]) => `<div><strong>${value}</strong><span>${label}</span></div>`)
    .join("");
}

function renderPreprocess(data) {
  const container = document.querySelector("#preprocessView");
  const terms = data.steps.preprocess.topTerms
    .map((item) => `<span class="term-chip">${escapeHtml(item.term)}</span>`)
    .join("");
  const sentences = data.steps.preprocess.sentences
    .map(
      (sentence) => `
        <article class="sentence-row ${sentence.selected ? "is-selected" : ""}">
          <div class="meta">${escapeHtml(sentence.id)}<br>${escapeHtml(sentence.docName)}</div>
          <div>
            <div class="sentence-text">${escapeHtml(sentence.text)}</div>
            ${sentence.selected ? '<span class="selected-badge">Được chọn</span>' : ""}
          </div>
          <div class="score">${sentence.tokenCount} token</div>
        </article>
      `,
    )
    .join("");

  container.className = "";
  container.innerHTML = `
    <div class="term-cloud">${terms}</div>
    <div class="sentence-list">${sentences}</div>
  `;
}

function renderClusters(data) {
  const container = document.querySelector("#clusterView");
  const rows = data.steps.clusters
    .map((cluster) => {
      const sentence = data.steps.preprocess.sentences.find((item) => item.id === cluster.sentenceId);
      return `
        <article class="cluster-row ${cluster.selected ? "is-selected" : ""}">
          <div><span class="cluster-pill">Cụm ${cluster.cluster}</span></div>
          <div>
            <div class="doc-name">${escapeHtml(sentence.docName)} · ${cluster.size} câu</div>
            <div class="sentence-text">${escapeHtml(sentence.text)}</div>
            ${cluster.selected ? '<span class="selected-badge">Qua MMR</span>' : ""}
          </div>
          <div class="score">centroid ${cluster.score.toFixed(3)}</div>
        </article>
      `;
    })
    .join("");

  container.className = "cluster-grid";
  container.innerHTML = rows;
}

function renderMmr(data) {
  const container = document.querySelector("#mmrView");
  const sentences = data.steps.preprocess.sentences;
  const rows = data.steps.mmr
    .map((step, index) => {
      const sentence = sentences[step.sentenceIndex];
      return `
        <article class="mmr-row is-selected">
          <div class="summary-number">${index + 1}</div>
          <div>
            <div class="doc-name">${escapeHtml(sentence.docName)} · ${escapeHtml(sentence.id)}</div>
            <div class="sentence-text">${escapeHtml(sentence.text)}</div>
          </div>
          <div class="score">
            relevance ${step.relevance.toFixed(3)}<br>
            redundancy ${step.redundancy.toFixed(3)}<br>
            mmr ${step.mmrScore.toFixed(3)}
          </div>
        </article>
      `;
    })
    .join("");

  container.className = "mmr-list";
  container.innerHTML = rows;
}

function renderSummary(data) {
  const summaryContainer = document.querySelector("#summaryView");
  const sourceContainer = document.querySelector("#sourceView");
  const summaryRows = data.summary
    .map(
      (sentence, index) => `
        <article class="summary-row">
          <div class="summary-number">${index + 1}</div>
          <div>
            <div class="doc-name">${escapeHtml(sentence.docName)}</div>
            <div class="summary-text">${escapeHtml(sentence.text)}</div>
          </div>
        </article>
      `,
    )
    .join("");

  const documents = data.documents
    .map((document) => {
      const sentences = document.sentences
        .map(
          (sentence) => `
            <span class="source-sentence ${sentence.selected ? "is-selected" : ""}" title="${escapeHtml(sentence.id)}">
              ${escapeHtml(sentence.text)}
            </span>
          `,
        )
        .join(" ");

      return `
        <article class="document-block">
          <h3>${escapeHtml(document.name)}</h3>
          <p>${sentences}</p>
        </article>
      `;
    })
    .join("");

  summaryContainer.className = "summary-list";
  summaryContainer.innerHTML = summaryRows;
  sourceContainer.innerHTML = documents;
}

function renderAll(data) {
  updateStats(data.stats);
  renderPreprocess(data);
  renderClusters(data);
  renderMmr(data);
  renderSummary(data);
  unlockSteps();
  activateStep("preprocess");
}

async function runSummarizer() {
  const formData = new FormData();
  document.querySelectorAll('textarea[name="texts"]').forEach((textarea) => {
    formData.append("texts", textarea.value);
  });
  [...fileInput.files].forEach((file) => {
    formData.append("files", file);
  });
  formData.append("summaryLength", summaryLength.value);

  runBtn.disabled = true;
  setStatus("Đang xử lý văn bản...");

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Không xử lý được dữ liệu.");
    }

    resultData = payload;
    renderAll(payload);
    setStatus("Đã tạo bản tóm tắt.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    runBtn.disabled = false;
  }
}

function copySummary() {
  if (!resultData) {
    return;
  }
  const text = resultData.summary.map((sentence) => sentence.text).join("\n");
  navigator.clipboard.writeText(text);
  setStatus("Đã copy bản tóm tắt.");
}

addTextBtn.addEventListener("click", () => addTextBox());
textInputs.addEventListener("click", (event) => {
  if (!event.target.classList.contains("remove-text")) {
    return;
  }
  event.target.closest(".text-box").remove();
});
fileInput.addEventListener("change", renderFiles);
runBtn.addEventListener("click", runSummarizer);
copyBtn.addEventListener("click", copySummary);

tabs.forEach((tab) => {
  tab.addEventListener("click", () => activateStep(tab.dataset.step));
});

nextButtons.forEach((button) => {
  button.addEventListener("click", () => activateStep(button.dataset.next));
});
