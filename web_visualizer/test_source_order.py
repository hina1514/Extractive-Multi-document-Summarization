import unittest

from web_visualizer.app import app
from web_visualizer.source_order import sort_by_input
from web_visualizer.test_pipeline_demo import TEXT


class SourceOrderTests(unittest.TestCase):
    def test_sort_preserves_selection_and_duplicate_text(self):
        selected = [
            {"id": "d2s1", "sourceIndex": 8, "docIndex": 1, "sourcePosition": 1, "text": "Cùng nội dung"},
            {"id": "d1s4", "sourceIndex": 3, "docIndex": 0, "sourcePosition": 4, "text": "Cùng nội dung"},
            {"id": "d1s2", "sourceIndex": 1, "docIndex": 0, "sourcePosition": 2, "text": "Câu khác"},
        ]
        result, trace = sort_by_input(selected)
        self.assertEqual([sentence["id"] for sentence in result], ["d1s2", "d1s4", "d2s1"])
        self.assertEqual([sentence["order"] for sentence in result], [1, 2, 3])
        self.assertEqual({sentence["id"] for sentence in result}, {sentence["id"] for sentence in selected})
        self.assertEqual(trace["before"][0]["afterOrder"], 3)
        self.assertTrue(trace["changed"])
        self.assertNotIn("order", selected[0])

    def test_already_sorted_input_has_no_move(self):
        selected = [{"id": "first", "sourceIndex": 1}, {"id": "last", "sourceIndex": 15}]
        _, trace = sort_by_input(selected)
        self.assertFalse(trace["changed"])

    def test_both_web_modes_sort_across_documents(self):
        client = app.test_client()
        for endpoint, output, trace_key in [("/api/summarize", "summary", "steps"), ("/api/pipeline", "final", None)]:
            with self.subTest(endpoint=endpoint):
                response = client.post(endpoint, data={"texts": [TEXT, TEXT.replace("rác", "vật liệu")], "clusters": "6", "cosineThreshold": "0"})
                self.assertEqual(response.status_code, 200, response.get_json())
                data = response.get_json()
                indexes = [sentence["sourceIndex"] for sentence in data[output]]
                self.assertEqual(indexes, sorted(indexes))
                trace = data[trace_key]["sorting"] if trace_key else data["sorting"]
                self.assertEqual({sentence["id"] for sentence in trace["before"]}, {sentence["id"] for sentence in data[output]})
                self.assertEqual([sentence["id"] for sentence in trace["after"]], [sentence["id"] for sentence in data[output]])


if __name__ == "__main__":
    unittest.main()
