export default function ({ parentElement, data, setTriggerValue }) {
  const frame = parentElement.querySelector(".visualizer");
  let response = data?.response;
  const deliver = () => {
    if (response) frame.contentWindow.postMessage({ kind: "visualizer-response", ...response }, "*");
  };
  const listener = event => {
    if (event.source !== frame.contentWindow) return;
    if (event.data?.kind === "visualizer-ready") deliver();
    if (event.data?.kind === "visualizer-request") setTriggerValue("request", event.data.payload);
  };
  window.addEventListener("message", listener);
  // With a stable Streamlit key, the iframe survives reruns and keeps inputs,
  // uploaded File objects, animation position and pending fetch promises.
  if (!frame.dataset.initialized) {
    frame.dataset.initialized = "true";
    frame.srcdoc = data.document;
  } else {
    deliver();
  }
  return () => window.removeEventListener("message", listener);
}
