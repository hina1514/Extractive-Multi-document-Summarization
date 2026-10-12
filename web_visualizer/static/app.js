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

function formatScore(value) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : "—";
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("is-error", isError);
}

function activateStep(step) {
  tabs.forEach((tab) => {
    const isActive = tab.dataset.step === step;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-current", isActive ? "step" : "false");
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
            <details class="tokens"><summary>Xem ${sentence.tokenCount} token sau xử lý</summary><div class="term-cloud">${sentence.tokens.map(token => `<span class="term-chip">${escapeHtml(token)}</span>`).join("")}</div></details>
          </div>
          <div class="score">${sentence.tokenCount} token</div>
        </article>
      `,
    )
    .join("");

  container.className = "";
  container.innerHTML = `
    ${explain("Tách câu → Chuẩn hóa → Tách từ → Lọc", `${data.stats.documentCount} tài liệu tạo ra ${data.stats.sentenceCount} câu hợp lệ. Câu có tối đa 4 token bị loại; mã d1s2 là câu thứ 2 trong tài liệu 1.`)}<details><summary>Từ khóa nổi bật (TF-IDF)</summary><div class="term-cloud">${terms}</div></details>
    <div class="sentence-list">${sentences}</div>
  `;
}

function explain(title, text) {
  return `<div class="explanation"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p></div>`;
}

function renderClusters(data) {
  const sentences = data.steps.preprocess.sentences;
  const container = document.querySelector("#clusterView");
  container.className = "cluster-grid";
  container.innerHTML = explain("Word2Vec (256 chiều) → KMeans → Câu đại diện", `${sentences.length} câu được gom thành ${data.stats.clusterCount} cụm. Vector câu là tổng vector từ; mỗi cụm lấy câu gần tâm nhất. Mở cụm để so sánh các thành viên.`) + data.steps.clusters.map(cluster => {
    const sentence = sentences[cluster.sentenceIndex];
    const members = cluster.members.map(id => sentences.find(s => s.id === id));
    return `<article class="cluster-card" style="--cluster-color:${clusterColor(cluster.cluster)}">
      <div class="section-heading"><span class="cluster-pill">Cụm ${cluster.cluster}</span><span class="meta">${cluster.size} câu → 1 đại diện</span></div>
      <div class="cluster-dots" aria-label="${cluster.size} câu trong cụm">${members.map(member => `<span title="${escapeHtml(member.id)}" class="dot ${member.id === sentence.id ? "representative" : ""}"></span>`).join("")}</div>
      <div class="doc-name">Đại diện · ${escapeHtml(sentence.id)} · ${escapeHtml(sentence.docName)}</div><p class="sentence-text">${escapeHtml(sentence.text)}</p>
      <details><summary>Xem ${cluster.size} câu trong cụm</summary>${members.map(member => `<div class="member-row"><span class="meta">${escapeHtml(member.id)}${member.id === sentence.id ? " · đại diện" : ""}</span><p>${escapeHtml(member.text)}</p></div>`).join("")}</details>
    </article>`;
  }).join("");
}

function clusterColor(cluster) {
  return ["#0f766e", "#4669bd", "#aa641b", "#924f9a", "#b74d60"][ (cluster - 1) % 5 ];
}

function renderCentroid(data) {
  const container = document.querySelector("#centroidView");
  container.className = "sentence-list";
  container.innerHTML = explain("TF-IDF → Vector chủ đề → Chấm điểm → Lọc trùng", `${data.stats.candidateCount} câu đại diện được so với vector chủ đề chung. Giữ ${data.stats.centroidCount} câu; loại câu quá giống câu đã giữ (độ tương đồng > 0,95). Điểm hiển thị dùng đúng văn bản đầu vào của Centroid.`) + [...data.steps.clusters].sort((a,b) => b.score - a.score).map((cluster, rank) => {
    const sentence = data.steps.preprocess.sentences[cluster.sentenceIndex];
    return `<article class="ranking-row ${cluster.centroidSelected ? "is-selected" : ""}"><div class="meta">Hạng ${rank + 1}<br>${escapeHtml(sentence.id)}</div><div><p class="sentence-text">${escapeHtml(sentence.text)}</p><div class="score-meter"><i style="width:${Math.max(0, Math.min(100, cluster.score * 100))}%"></i></div><span class="score">Điểm chủ đề ${formatScore(cluster.score)}</span></div><span class="decision">${cluster.centroidSelected ? "Giữ cho MMR" : "Lọc trùng"}</span></article>`;
  }).join("");
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
            Liên quan ${formatScore(step.relevance)}<br>
            Trùng lặp ${formatScore(step.redundancy)}<br>
            ${index === 0 ? "Câu mốc" : "MMR " + formatScore(step.mmrScore)}
          </div>
        </article>
      `;
    })
    .join("");

  container.className = "mmr-list";
  container.innerHTML = explain("MMR = 0,6 × liên quan − 0,4 × trùng lặp", `Chọn câu đầu trong danh sách Centroid làm câu mốc. Mỗi lượt tiếp theo ưu tiên liên quan với câu mốc và phạt độ giống với câu đã chọn. Chế độ train của file gốc giữ tối thiểu câu mốc, với mục tiêu bằng số ứng viên Centroid trừ 4. Đang giữ ${data.stats.mmrCount} câu.`) + rows;
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
            <div class="doc-name">${escapeHtml(sentence.docName)} · ${escapeHtml(sentence.id)} · ${sentence.reason === "mmr" ? "Chọn bởi MMR" : "Bổ sung theo vị trí"}</div>
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
  summaryContainer.innerHTML = explain("Giữ câu MMR → Bổ sung theo vị trí → Sắp thứ tự", `${data.stats.summaryMode === "auto" ? "Tự động" : "Theo yêu cầu"}: ${data.stats.summaryLength} câu từ ${data.stats.sentenceCount} câu hợp lệ. ${data.stats.requestedSummaryLength > data.stats.clusterCount ? "Yêu cầu vượt số đại diện; đầu ra được giới hạn theo số cụm. " : ""}Thứ tự kết quả theo danh sách đại diện đã xếp theo vị trí trong tài liệu, đúng file gốc. Phần tô vàng bên dưới chỉ câu được chọn.`) + summaryRows;
  sourceContainer.innerHTML = documents;
}

function renderAll(data) {
  updateStats(data.stats);
  renderPreprocess(data);
  renderClusters(data);
  renderCentroid(data);
  renderMmr(data);
  renderSummary(data);
  unlockSteps();
  activateStep("preprocess");
}

async function runSummarizer() {
  if (!summaryLength.checkValidity()) { summaryLength.reportValidity(); return; }
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
    setStatus(`Đã tạo ${payload.stats.summaryLength} câu · ${payload.stats.summaryMode === "auto" ? "chế độ tự động" : "theo số câu yêu cầu"}.`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    runBtn.disabled = false;
  }
}

async function copySummary() {
  if (!resultData) {
    return;
  }
  const text = resultData.summary.map((sentence) => sentence.text).join("\n");
  try { await navigator.clipboard.writeText(text); setStatus("Đã sao chép bản tóm tắt."); }
  catch { setStatus("Không thể sao chép. Hãy chọn văn bản và sao chép thủ công.", true); }
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
// The divider supports mouse, touch, keyboard and keeps the preferred width.
const workspace = document.querySelector("#workspace");
const splitter = document.querySelector("#splitter");
let panePercent = 32;
try { panePercent = Number(localStorage.getItem("inputPanePercent")) || 32; } catch {}
function resizePane(percent) {
  panePercent = Math.max(24, Math.min(60, percent));
  workspace.style.setProperty("--input-width", `${panePercent}%`);
  splitter.setAttribute("aria-valuenow", Math.round(panePercent));
  try { localStorage.setItem("inputPanePercent", panePercent); } catch {}
}
resizePane(panePercent);
splitter.addEventListener("pointerdown", event => {
  if (event.button !== 0) return;
  splitter.setPointerCapture(event.pointerId);
  document.body.classList.add("is-resizing");
});
splitter.addEventListener("pointermove", event => {
  if (!splitter.hasPointerCapture(event.pointerId)) return;
  const rect = workspace.getBoundingClientRect();
  resizePane(100 * (event.clientX - rect.left) / rect.width);
});
function stopResizing(event) {
  if (splitter.hasPointerCapture(event.pointerId)) splitter.releasePointerCapture(event.pointerId);
  document.body.classList.remove("is-resizing");
}
splitter.addEventListener("pointerup", stopResizing);
splitter.addEventListener("pointercancel", stopResizing);
splitter.addEventListener("lostpointercapture", () => document.body.classList.remove("is-resizing"));
splitter.addEventListener("dblclick", () => resizePane(32));
splitter.addEventListener("keydown", event => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  resizePane(event.key === "Home" ? 24 : event.key === "End" ? 60 : panePercent + (event.key === "ArrowLeft" ? -2 : 2));
});
