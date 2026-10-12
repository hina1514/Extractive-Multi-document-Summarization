"""Bridge browser FormData to the existing Flask handlers without an HTTP server."""
import base64
import binascii
import io
import re
from pathlib import Path

from werkzeug.datastructures import MultiDict
from web_visualizer.app import app
from web_visualizer.pipeline_demo import demo_script, demo_styles


ROOT = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
API_PATHS = {"/api/summarize", "/api/pipeline"}


def render_document():
    """Inline trusted repository assets so no Flask URLs are needed on Cloud."""
    with app.test_client() as client:
        document = client.get("/").get_data(as_text=True)
    styles = {"/demo/assets.css": demo_styles(), "/static/styles.css": (ROOT / "static/styles.css").read_text(encoding="utf-8")}
    scripts = {
        "/demo/assets.js": demo_script(),
        "/static/source_sort.js": (ROOT / "static/source_sort.js").read_text(encoding="utf-8"),
        "/static/app.js": (ROOT / "static/app.js").read_text(encoding="utf-8"),
    }
    for path, css in styles.items():
        document = re.sub(r'<link\b[^>]*href="' + re.escape(path) + r'"[^>]*>', lambda _: f"<style>{css}</style>", document)
    for path, javascript in scripts.items():
        document = document.replace(f'<script src="{path}"></script>', "<script>" + javascript.replace("</script", "<\\/script") + "</script>")
    bridge = (ROOT / "static/streamlit_fetch.js").read_text(encoding="utf-8")
    # Install the fetch bridge before any UI event can submit a request.
    return document.replace("<head>", "<head><script>" + bridge + "</script>", 1)


def dispatch_request(payload):
    request_id = payload.get("id") if isinstance(payload, dict) else None
    try:
        if not isinstance(payload, dict) or payload.get("path") not in API_PATHS:
            raise ValueError("Yêu cầu không hợp lệ.")
        form = MultiDict()
        fields = payload.get("fields", [])
        if not isinstance(fields, list) or len(fields) > 100:
            raise ValueError("Quá nhiều trường dữ liệu.")
        text_size = 0
        for field in fields:
            if not isinstance(field, list) or len(field) != 2 or not all(isinstance(value, str) for value in field):
                raise ValueError("Dữ liệu đầu vào không hợp lệ.")
            text_size += len(field[1])
            form.add(*field)
        if text_size > 100_000:
            raise ValueError("Tổng văn bản tối đa 100.000 ký tự.")
        files = payload.get("files", [])
        if not isinstance(files, list) or len(files) > 30:
            raise ValueError("Tải lên tối đa 30 file.")
        byte_count = 0
        for uploaded in files:
            encoded = uploaded.get("base64", "")
            if not isinstance(encoded, str) or len(encoded) > (MAX_UPLOAD_BYTES * 4 // 3 + 4):
                raise ValueError("Tổng dung lượng file tối đa 10 MB.")
            raw = base64.b64decode(encoded, validate=True)
            byte_count += len(raw)
            if byte_count > MAX_UPLOAD_BYTES:
                raise ValueError("Tổng dung lượng file tối đa 10 MB.")
            form.add("files", (io.BytesIO(raw), uploaded.get("name", "uploaded.txt")))
        with app.test_client() as client:
            response = client.post(payload["path"], data=form)
        return {"id": request_id, "status": response.status_code, "body": response.get_json()}
    except (ValueError, TypeError, AttributeError, binascii.Error) as error:
        return {"id": request_id, "status": 400, "body": {"error": str(error)}}
