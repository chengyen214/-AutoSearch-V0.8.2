import unittest

from rag.paper_query_filter import PaperQueryFilter


class TestPaperQueryFilter(unittest.TestCase):

    def test_no_filter(self):
        self.assertIsNone(
            PaperQueryFilter.build()
        )

    def test_single_document_id(self):
        self.assertEqual(
            PaperQueryFilter.build(
                document_id="openalex:W123"
            ),
            {
                "document_id": "openalex:W123",
            },
        )

    def test_multiple_document_ids(self):
        self.assertEqual(
            PaperQueryFilter.build(
                document_ids=[
                    "openalex:W123",
                    "openalex:W456",
                ]
            ),
            {
                "document_id": {
                    "$in": [
                        "openalex:W123",
                        "openalex:W456",
                    ],
                },
            },
        )

    def test_duplicate_document_ids(self):
        self.assertEqual(
            PaperQueryFilter.build(
                document_ids=[
                    "openalex:W123",
                    "openalex:W123",
                    "openalex:W456",
                ]
            ),
            {
                "document_id": {
                    "$in": [
                        "openalex:W123",
                        "openalex:W456",
                    ],
                },
            },
        )

    def test_source_type(self):
        self.assertEqual(
            PaperQueryFilter.build(
                source_type="paper_pdf"
            ),
            {
                "source_type": "paper_pdf",
            },
        )

    def test_page_number(self):
        self.assertEqual(
            PaperQueryFilter.build(
                page_number=3
            ),
            {
                "page_number": 3,
            },
        )

    def test_combined_filters(self):
        self.assertEqual(
            PaperQueryFilter.build(
                document_id="openalex:W123",
                source_type="paper_pdf",
                page_number=3,
            ),
            {
                "$and": [
                    {
                        "document_id": "openalex:W123",
                    },
                    {
                        "source_type": "paper_pdf",
                    },
                    {
                        "page_number": 3,
                    },
                ],
            },
        )

    def test_document_id_and_document_ids_conflict(self):
        with self.assertRaises(ValueError):
            PaperQueryFilter.build(
                document_id="openalex:W123",
                document_ids=["openalex:W456"],
            )

    def test_invalid_page_number(self):
        for value in (0, -1, 1.5, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    PaperQueryFilter.build(
                        page_number=value
                    )

    def test_empty_document_ids(self):
        with self.assertRaises(ValueError):
            PaperQueryFilter.build(
                document_ids=[]
            )

    def test_invalid_document_id(self):
        with self.assertRaises(ValueError):
            PaperQueryFilter.build(
                document_id=" "
            )

    def test_invalid_source_type(self):
        with self.assertRaises(ValueError):
            PaperQueryFilter.build(
                source_type=""
            )


if __name__ == "__main__":
    unittest.main()