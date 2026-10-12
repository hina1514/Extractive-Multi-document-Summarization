// Preserve every source scene; append only the final source-order step.
const originalFlowBuild = flowBuild;
flowBuild = function () {
  originalFlowBuild();
  flowAdd(5, 'source-sort', 'Sort theo thứ tự câu trong input', 'Sắp tăng dần theo tài liệu và vị trí câu gốc, giữ nguyên tập câu đã chọn.');
};
const originalFlowContent = flowRenderContent;
flowRenderContent = function (item) {
  if (item.type === 'source-sort') {
    return window.SourceSortView.render(DATA.sorting) + '<h3 class="sorted-title">Bản tóm tắt sau Sort</h3><ol class="final-list sorted-final">' + DATA.sorting.after.map(sentence => '<li><small>' + esc(sentence.doc_label) + ' · câu ' + sentence.sourcePosition + ' · ' + esc(sentence.id) + '</small>' + esc(sentence.text) + '</li>').join('') + '</ol>';
  }
  return originalFlowContent(item);
};
