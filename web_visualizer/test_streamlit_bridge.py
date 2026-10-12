import base64
import unittest
from unittest.mock import patch

from web_visualizer.streamlit_bridge import dispatch_request, render_document
from web_visualizer.test_pipeline_demo import TEXT


class StreamlitBridgeTests(unittest.TestCase):
    def test_document_uses_inline_assets_and_both_existing_modes(self):
        document = render_document()
        self.assertIn('id="interactiveDemo"', document)
        self.assertIn('id="overviewLambda"', document)
        self.assertIn('visualizer-request', document)
        self.assertNotIn('<script src=', document)
        self.assertNotIn('<link rel="stylesheet"', document)
        self.assertIn('source-sort', document)

    def test_manual_text_uses_same_summary_handler(self):
        result = dispatch_request({"id": "text-request", "path": "/api/summarize",
                                   "fields": [["texts", TEXT], ["lambda", "0.2"], ["summaryLength", "1"]]})
        self.assertEqual(result["status"], 200, result)
        self.assertEqual(result["id"], "text-request")
        self.assertEqual(result["body"]["stats"]["lambda"], 0.2)
        self.assertEqual(len(result["body"]["summary"]), 1)

    def test_multiple_uploaded_files_reach_the_demo(self):
        result = dispatch_request({
            "id": "upload-request", "path": "/api/pipeline",
            "fields": [["clusters", "6"], ["cosineThreshold", "0"], ["summaryLength", "2"]],
            "files": [{"name": name, "base64": base64.b64encode(TEXT.encode()).decode()}
                      for name in ["first.txt", "second.txt"]],
        })
        self.assertEqual(result["status"], 200, result)
        self.assertEqual(result["body"]["documents"], 2)
        self.assertEqual(len(result["body"]["final"]), 2)

    def test_invalid_inputs_are_returned_as_api_errors(self):
        for payload in [{"id": "wrong", "path": "/admin"},
                        {"id": "bad-file", "path": "/api/pipeline", "files": [{"base64": "!!!"}]},
                        {"id": "bad-fields", "path": "/api/summarize", "fields": [[1, "text"]]},
                        {"id": "huge", "path": "/api/summarize", "fields": [["texts", "a" * 100001]]}]:
            self.assertEqual(dispatch_request(payload)["status"], 400)
        with patch('web_visualizer.streamlit_bridge.MAX_UPLOAD_BYTES', 2):
            result = dispatch_request({"path": "/api/summarize", "files": [{"base64": base64.b64encode(b'abc').decode()}]})
            self.assertEqual(result["status"], 400)


if __name__ == '__main__':
    unittest.main()
