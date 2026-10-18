"""
tests/V9_0/test_raw_html_structure.py

AutoSearch V5

Raw HTML MongoDB Structure Test

用途：

    讀取 MongoDB raw_html Collection
    確認實際資料結構。

注意：

    本測試只讀取 MongoDB。
    不新增、修改或刪除資料。
"""

from collections import Counter

from database.mongo_connection import (
    get_mongo_collection,
)


COLLECTION_NAME = "raw_html"
SAMPLE_COUNT = 3


def print_value(
    value,
    indent=0,
):
    """印出 MongoDB 欄位內容。"""

    prefix = " " * indent

    if isinstance(
        value,
        dict,
    ):
        for key, item in value.items():
            print(
                f"{prefix}{key}: "
                f"{type(item).__name__}"
            )

            if isinstance(
                item,
                (dict, list),
            ):
                print_value(
                    item,
                    indent + 4,
                )

    elif isinstance(
        value,
        list,
    ):
        print(
            f"{prefix}length: "
            f"{len(value)}"
        )

        if value:
            print(
                f"{prefix}item type: "
                f"{type(value[0]).__name__}"
            )

            if isinstance(
                value[0],
                (dict, list),
            ):
                print_value(
                    value[0],
                    indent + 4,
                )


def inspect_indexes(
    collection,
):
    """檢查 raw_html Index。"""

    print()
    print("[1] Indexes")

    indexes = list(
        collection.list_indexes()
    )

    if not indexes:
        print("No indexes found.")
        return

    for index in indexes:
        print(
            f"- {index.get('name')}: "
            f"{index.get('key')}"
        )


def inspect_documents(
    collection,
):
    """檢查 raw_html 實際文件結構。"""

    print()
    print("[2] Documents")

    total = collection.count_documents({})

    print(
        f"Total Documents: {total}"
    )

    if total == 0:
        print("raw_html is empty.")
        return []

    documents = list(
        collection.find({})
        .sort(
            "created_at",
            -1,
        )
        .limit(
            SAMPLE_COUNT
        )
    )

    print(
        f"Sample Documents: "
        f"{len(documents)}"
    )

    for index, document in enumerate(
        documents,
        start=1,
    ):
        print()
        print(
            f"Document #{index}"
        )

        print(
            f"_id: "
            f"{document.get('_id')}"
        )

        print(
            f"Fields: "
            f"{list(document.keys())}"
        )

        print()

        for key, value in document.items():
            if key == "_id":
                continue

            print(
                f"{key}: "
                f"{type(value).__name__}"
            )

            if key == "resources":
                print_value(
                    value,
                    indent=4,
                )

    return documents


def inspect_field_statistics(
    documents,
):
    """統計 Sample Document 欄位。"""

    print()
    print("[3] Field Statistics")

    if not documents:
        print("No documents.")
        return

    field_counter = Counter()

    for document in documents:
        field_counter.update(
            document.keys()
        )

    for field, count in sorted(
        field_counter.items()
    ):
        print(
            f"- {field}: "
            f"{count}/{len(documents)}"
        )


def inspect_resource_structure(
    documents,
):
    """檢查 resources.css 與 resources.images。"""

    print()
    print("[4] Resource Structure")

    if not documents:
        print("No documents.")
        return

    for index, document in enumerate(
        documents,
        start=1,
    ):
        resources = document.get(
            "resources"
        )

        print()
        print(
            f"Document #{index}"
        )

        if resources is None:
            print(
                "resources: None"
            )
            continue

        if not isinstance(
            resources,
            dict,
        ):
            print(
                "resources type: "
                f"{type(resources).__name__}"
            )
            continue

        print(
            f"resources keys: "
            f"{list(resources.keys())}"
        )

        for resource_type in (
            "css",
            "images",
        ):
            values = resources.get(
                resource_type,
                [],
            )

            print(
                f"{resource_type}: "
                f"type={type(values).__name__}, "
                f"count="
                f"{len(values) if isinstance(values, list) else 'N/A'}"
            )

            if isinstance(
                values,
                list,
            ) and values:
                print(
                    f"{resource_type}[0]: "
                    f"{values[0]}"
                )


def main():
    print("=" * 60)
    print(
        "Raw HTML MongoDB Structure Test"
    )
    print("=" * 60)

    collection = get_mongo_collection(
        COLLECTION_NAME
    )

    print()
    print(
        f"Database: "
        f"{collection.database.name}"
    )

    print(
        f"Collection: "
        f"{collection.name}"
    )

    inspect_indexes(
        collection
    )

    documents = inspect_documents(
        collection
    )

    inspect_field_statistics(
        documents
    )

    inspect_resource_structure(
        documents
    )

    print()
    print("=" * 60)
    print(
        "Raw HTML Structure Test: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()