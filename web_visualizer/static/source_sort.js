(() => {
  const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[character]));
  window.SourceSortView = {
    render(trace) {
      const column = (sentences, sorted) => `<div class="sort-column"><div class="sort-column-heading"><span>${sorted ? "02" : "01"}</span><h3>${sorted ? "Sau Sort · đúng thứ tự input" : "Trước Sort · tập câu đã chọn"}</h3></div>${sentences.map(sentence => `<article class="sort-item ${sentence.beforeOrder !== sentence.afterOrder ? "sort-moved" : ""}"><div class="sort-item-top"><b>${sorted ? sentence.afterOrder : sentence.beforeOrder}</b><span>${esc(sentence.id)}</span><em>${sentence.beforeOrder === sentence.afterOrder ? "Giữ vị trí" : `${sentence.beforeOrder} → ${sentence.afterOrder}`}</em></div><div class="sort-source">Tài liệu ${sentence.docIndex + 1} · câu ${sentence.sourcePosition} · ${esc(sentence.docName || sentence.doc_label)}</div><p>${esc(sentence.text)}</p></article>`).join("")}</div>`;
      return `<div class="sort-verdict"><span>✓</span><div><strong>${trace.changed ? "Đã sắp xếp theo input" : "Các câu đã đúng thứ tự input"}</strong><p>${trace.after.length} câu được giữ nguyên · khóa Sort: vị trí xuất hiện trong input</p></div></div><div class="sort-comparison">${column(trace.before, false)}<div class="sort-arrow" aria-hidden="true">→</div>${column(trace.after, true)}</div>`;
    }
  };
})();
