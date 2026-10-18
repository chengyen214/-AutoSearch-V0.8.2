"""
Clear OCR results for one paper.
"""

from database.mongo_connection import get_mongo_database

DOCUMENT_ID = "openalex:W7221570648"


def main():
    database = get_mongo_database()
    collection = database["paper_ocr_results"]

    document = collection.find_one(
        {"document_id": DOCUMENT_ID},
        {
            "_id": 1,
            "status": 1,
            "processed_pages": 1,
            "total_pages": 1,
        },
    )

    if document is None:
        print(f"No OCR result found: {DOCUMENT_ID}")
        return

    print("OCR result to delete:")
    print(document)

    confirmation = input(
        f"Type DELETE to remove OCR result for {DOCUMENT_ID}: "
    )

    if confirmation != "DELETE":
        print("Cancelled.")
        return

    result = collection.delete_one(
        {"_id": document["_id"]}
    )

    print(f"Deleted OCR documents: {result.deleted_count}")
    print("GridFS PDF was not deleted.")


if __name__ == "__main__":
    main()