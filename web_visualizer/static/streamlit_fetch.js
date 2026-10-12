(() => {
  const pending = new Map();
  const nativeFetch = window.fetch.bind(window);
  const paths = new Set(["/api/summarize", "/api/pipeline"]);
  window.addEventListener("message", event => {
    if (event.source !== parent || event.data?.kind !== "visualizer-response") return;
    const entry = pending.get(event.data.id);
    if (!entry) return;
    pending.delete(event.data.id);
    clearTimeout(entry.timer);
    entry.resolve(new Response(JSON.stringify(event.data.body), {
      status: event.data.status, headers: { "Content-Type": "application/json" }
    }));
  });
  window.fetch = async (url, options = {}) => {
    if (!paths.has(String(url))) return nativeFetch(url, options);
    const id = crypto.randomUUID();
    const fields = [], files = [];
    let byteCount = 0;
    for (const [key, value] of options.body.entries()) {
      if (value instanceof File) {
        byteCount += value.size;
        if (byteCount > 10 * 1024 * 1024) throw new Error("Tổng dung lượng file tối đa 10 MB.");
        const base64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = () => reject(new Error("Không đọc được file."));
          reader.readAsDataURL(value);
        });
        files.push({name: value.name, base64});
      } else {
        fields.push([key, value]);
      }
    }
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error("Xử lý quá lâu. Hãy giảm số tài liệu rồi chạy lại."));
      }, 180_000);
      pending.set(id, {resolve, timer});
      parent.postMessage({kind: "visualizer-request", payload: {id, path: String(url), fields, files}}, "*");
    });
  };
  parent.postMessage({kind: "visualizer-ready"}, "*");
})();
