// Runs in the standalone renderer's private scope through its web adapter.
const originalFlowBuild = flowBuild;
flowBuild = function () {
  originalFlowBuild();
  const final = flowSteps.find(step => step.type === 'final');
  if (final) {
    final.title = 'Tập câu được chọn trước Sort';
    final.description = 'Giữ câu MMR và bổ sung câu theo vị trí. Tập này được chuyển sang bước Sort cuối cùng.';
  }
  flowAdd(5, 'source-sort', 'Sort theo thứ tự câu trong input', 'Sắp tăng dần theo tài liệu và vị trí câu gốc, giữ nguyên tập câu đã chọn.');
};
FLOW_GROUPS[5] = 'Kết quả & Sort';
const originalFlowStrip = renderFlowStrip;
renderFlowStrip = function (...args) {
  originalFlowStrip(...args);
  $('flow-strip').querySelectorAll('.flow-tile').forEach(tile => {
    let color = tile.style.background;
    if (color === 'rgb(170, 179, 193)') color = '#123447';
    if (tile.classList.contains('selected')) color = '#0f766e';
    tile.style.setProperty('background', color, 'important');
  });
};
const originalFlowContent = flowRenderContent;
flowRenderContent = function (item) {
  if (item.type === 'final') {
    return '<div class="flow-result"><b>Đã chọn ' + DATA.sorting.before.length + ' câu</b><p>Bước tiếp theo chỉ đổi thứ tự hiển thị theo input.</p></div><ol class="final-list">' + DATA.sorting.before.map(sentence => '<li><small>' + esc(sentence.id) + ' · ' + esc(sentence.doc_label) + '</small>' + esc(sentence.text) + '</li>').join('') + '</ol>';
  }
  if (item.type === 'source-sort') {
    return window.SourceSortView.render(DATA.sorting) + '<h3 class="sorted-title">Bản tóm tắt sau Sort</h3><ol class="final-list sorted-final">' + DATA.final.map(sentence => '<li><small>' + esc(sentence.doc_label) + ' · câu ' + sentence.sourcePosition + ' · ' + esc(sentence.id) + '</small>' + esc(sentence.text) + '</li>').join('') + '</ol>';
  }
  return originalFlowContent(item);
};

function upgradeClusterChart(markup) {
  const holder = document.createElement('div');
  holder.innerHTML = markup;
  const svg = holder.querySelector('svg');
  if (!svg) return markup;
  svg.classList.add('cluster-chart');
  const namespace = 'http://www.w3.org/2000/svg';
  const bounds = svg.viewBox.baseVal;
  const width = bounds.width || 760, height = bounds.height || 420;
  const defs = document.createElementNS(namespace, 'defs');
  defs.innerHTML = '<linearGradient id="chart-paper" x2="0" y2="1"><stop stop-color="#f8fcff"/><stop offset="1" stop-color="#edf4f8"/></linearGradient><filter id="chart-point-shadow" x="-60%" y="-60%" width="220%" height="220%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#102a43" flood-opacity=".25"/></filter>';
  const background = document.createElementNS(namespace, 'rect');
  background.setAttribute('width', width); background.setAttribute('height', height);
  background.setAttribute('rx', '18'); background.setAttribute('fill', 'url(#chart-paper)');
  svg.prepend(background); svg.prepend(defs);
  svg.querySelectorAll('circle.km-dot').forEach(point => {
    point.classList.add('chart-sentence-point');
    point.setAttribute('r', point.classList.contains('km-point-current') ? '8' : '6');
    point.setAttribute('stroke', '#fff'); point.setAttribute('stroke-width', '2');
    point.setAttribute('tabindex', '0');
    const title = point.querySelector('title')?.textContent || 'Câu trong input';
    const sentence = DATA.sentences.find(sentence => title.startsWith(sentence.id + ' ·'));
    point.setAttribute('aria-label', title);
    point.setAttribute('data-chart-detail', title + (sentence ? ' — ' + sentence.text : ''));
  });
  svg.querySelectorAll('text.km-point-label').forEach(label => {
    label.setAttribute('font-weight', '700');
  });
  svg.querySelectorAll('text').forEach(label => {
    if (label.textContent.startsWith('μ')) {
      label.classList.add('chart-center-label');
      label.setAttribute('transform', 'translate(0,-6)');
    }
  });
  svg.querySelectorAll('path[class*="km-center"]').forEach(center => {
    center.classList.add('chart-centroid');
    center.setAttribute('stroke', '#fff'); center.setAttribute('stroke-width', '2');
  });
  const frame = document.createElement('section');
  frame.className = 'chart-frame';
  frame.innerHTML = '<header class="chart-header"><div><span class="chart-kicker">KHÔNG GIAN CÂU</span><h3>Bản đồ phân cụm</h3></div><span class="chart-dimension">PCA · 2D</span></header><div class="chart-detail" aria-live="polite">Di chuột hoặc chọn một điểm để xem câu và cụm.</div>';
  frame.insertBefore(svg, frame.lastChild);
  holder.prepend(frame);
  return holder.innerHTML;
}
const originalKmSvgBase = kmSvgBase;
kmSvgBase = (...args) => upgradeClusterChart(originalKmSvgBase(...args));
const originalPlot = plot;
plot = (...args) => upgradeClusterChart(originalPlot(...args));
root.addEventListener('pointerover', showChartDetail);
root.addEventListener('focusin', showChartDetail);
root.addEventListener('click', showChartDetail);
function showChartDetail(event) {
  const point = event.target.closest('[data-chart-detail]');
  if (!point) return;
  const detail = point.closest('.chart-frame')?.querySelector('.chart-detail');
  if (detail) detail.textContent = point.dataset.chartDetail;
}
