"""Check the standalone demo's shared web input and output contract."""
import io
import re
import unittest
from unittest.mock import patch

from web_visualizer.app import app


TEXT = " ".join([
    "Thành phố triển khai chương trình phân loại rác tại nguồn ở ba quận.",
    "Hộ gia đình được hướng dẫn tách rác hữu cơ giấy và nhựa.",
    "Thùng màu riêng giúp người dân bỏ rác đúng quy định.",
    "Trường học hướng dẫn học sinh nhận biết vật liệu có thể tái chế.",
    "Các tổ dân phố tiếp nhận phản ánh về những điểm tập kết rác quá tải.",
    "Xe chuyên dụng thu gom riêng rác đã phân loại mỗi tuần.",
    "Xe chuyển giấy và nhựa đến nhà máy để xử lý.",
    "Nhà máy cân và phân loại vật liệu thu hồi trước khi tái chế.",
    "Rác hữu cơ sạch được đưa đến khu ủ compost để tạo phân bón.",
    "Lịch thu gom được thông báo trước nhằm hạn chế tình trạng rác bị trộn lẫn.",
])


class PipelineDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.tokenizers = patch.multiple(
            "underthesea",
            sent_tokenize=lambda text: [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()],
            word_tokenize=lambda text, **kwargs: " ".join(re.findall(r"\w+", text)),
        )
        self.tokenizers.start()
        self.addCleanup(self.tokenizers.stop)

    def test_demo_assets_and_shared_page(self):
        page = self.client.get("/")
        self.assertIn(b'id="interactiveDemo"', page.data)
        script = self.client.get("/demo/assets.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn(b"window.PipelineDemo", script.data)
        self.assertNotIn(b"$('run').onclick=async", script.data)
        self.assertIn(b"@scope (#interactiveDemo)", self.client.get("/demo/assets.css").data)

    def test_upload_trace_and_manual_summary_limit(self):
        response = self.client.post("/api/pipeline", data={
            "files": (io.BytesIO(TEXT.encode("utf-8")), "waste.txt"),
            "clusters": "8", "cosineThreshold": "0", "mode": "test", "summaryLength": "1",
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        self.assertEqual(len(data["final"]), 1)
        self.assertEqual(data["final"][0]["doc_label"], "waste.txt")
        self.assertEqual(data["summaryMode"], "manual")
        self.assertTrue(data["kmeans"]["history"])
        self.assertTrue(data["centroid"]["process"])
        self.assertTrue(data["mmr"]["rounds"])
        self.assertEqual(data["final"][0]["id"], data["mmr"]["selected"][0]["id"])

    def test_blank_or_missing_length_uses_automatic_count(self):
        for extra in ({}, {"summaryLength": ""}):
            with self.subTest(extra=extra):
                response = self.client.post("/api/pipeline", data={"texts": TEXT, "cosineThreshold": "0", **extra})
                self.assertEqual(response.status_code, 200, response.get_json())
                data = response.get_json()
                self.assertEqual(data["kmeans"]["k"], 3)
                self.assertEqual(len(data["final"]), 3)
                self.assertEqual(data["summaryMode"], "auto")

    def test_bad_parameters_and_short_documents_are_actionable(self):
        for field, value in [("clusters", "0"), ("clusters", "31"), ("clusters", "1.5"),
                             ("lambda", "nan"), ("lambda", "2"), ("cosineThreshold", "2"),
                             ("summaryLength", "0"), ("mode", "invalid")]:
            with self.subTest(field=field, value=value):
                response = self.client.post("/api/pipeline", data={"texts": TEXT, field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())
        response = self.client.post("/api/pipeline", data={"texts": "Chương trình phân loại rác được triển khai rộng rãi."})
        self.assertEqual(response.status_code, 400)
        self.assertIn("5", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
