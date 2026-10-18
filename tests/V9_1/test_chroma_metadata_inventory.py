"""
tests/V9_1/test_chroma_metadata_inventory.py

AutoSearch V7

Chroma Metadata Inventory Real Test

目的：

    盤點目前 ChromaDB 實際儲存的 Metadata。

測試：

1. 找出 Chroma Persistence Directory
2. 列出 Chroma Collections
3. Collection-level Metadata
4. Document count
5. Document Metadata fields
6. Metadata field types
7. Metadata null / empty count
8. Metadata distinct count
9. Metadata sample
10. 不修改 ChromaDB
"""

import json
from collections import defaultdict
from pathlib import Path


PAGE_SIZE = 500

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "archive",
}


def find_chroma_directories(
    project_root,
):
    """找出包含 chroma.sqlite3 的 Chroma Persistence Directory。"""

    directories = []

    for path in project_root.rglob(
        "chroma.sqlite3"
    ):
        if not path.is_file():
            continue

        relative_parts = (
            path.parent.relative_to(
                project_root
            ).parts
        )

        if any(
            part in EXCLUDED_DIRECTORY_NAMES
            for part in relative_parts
        ):
            continue

        directories.append(
            path.parent
        )

    return sorted(
        set(directories)
    )


def get_collection(
    client,
    collection,
):
    """兼容不同 ChromaDB 版本的 Collection 取得方式。"""

    if hasattr(
        collection,
        "name",
    ):
        return client.get_collection(
            name=collection.name
        )

    return client.get_collection(
        name=str(
            collection
        )
    )


def get_collection_name(
    collection,
):
    """取得 Collection 名稱。"""

    if hasattr(
        collection,
        "name",
    ):
        return collection.name

    return str(
        collection
    )


def normalize_value(
    value,
):
    """將 Metadata value 轉為可統計形式。"""

    if value is None:
        return None

    if isinstance(
        value,
        str,
    ):
        return value.strip()

    return value


def value_type(
    value,
):
    """取得 Metadata value 型別。"""

    if value is None:
        return "NoneType"

    return type(
        value
    ).__name__


def is_empty_value(
    value,
):
    """判斷 Metadata value 是否為空。"""

    if value is None:
        return True

    if isinstance(
        value,
        str,
    ):
        return value.strip() == ""

    return False


def collect_metadata_statistics(
    collection,
):
    """盤點 Collection 所有 Document Metadata。"""

    total_count = collection.count()

    field_values = defaultdict(
        list
    )

    metadata_count = 0

    offset = 0

    while offset < total_count:
        result = collection.get(
            offset=offset,
            limit=PAGE_SIZE,
            include=[
                "metadatas",
            ],
        )

        metadatas = result.get(
            "metadatas",
            [],
        )

        if not metadatas:
            break

        for metadata in metadatas:
            metadata = (
                metadata
                or {}
            )

            if metadata:
                metadata_count += 1

            for key, value in metadata.items():
                field_values[key].append(
                    normalize_value(
                        value
                    )
                )

        offset += len(
            metadatas
        )

    statistics = {}

    for key in sorted(
        field_values
    ):
        values = field_values[
            key
        ]

        non_empty_values = [
            value
            for value in values
            if not is_empty_value(
                value
            )
        ]

        distinct_values = set()

        for value in non_empty_values:
            try:
                distinct_values.add(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        sort_keys=True,
                        default=str,
                    )
                )

            except Exception:
                distinct_values.add(
                    str(value)
                )

        types = sorted(
            {
                value_type(
                    value
                )
                for value in values
            }
        )

        statistics[key] = {
            "count": len(values),
            "non_empty": len(
                non_empty_values
            ),
            "empty": (
                len(values)
                - len(non_empty_values)
            ),
            "distinct": len(
                distinct_values
            ),
            "types": types,
            "samples": non_empty_values[
                :5
            ],
        }

    return {
        "total_count": total_count,
        "metadata_count": metadata_count,
        "metadata_fields": statistics,
    }


def print_collection_report(
    collection,
):
    """輸出 Collection Metadata Report。"""

    collection_name = (
        get_collection_name(
            collection
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Collection: {collection_name}"
    )

    print(
        "=" * 70
    )

    collection_metadata = (
        getattr(
            collection,
            "metadata",
            None,
        )
    )

    print(
        "\nCollection Metadata:"
    )

    if collection_metadata:
        print(
            json.dumps(
                collection_metadata,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
    else:
        print(
            "  [EMPTY]"
        )

    report = collect_metadata_statistics(
        collection
    )

    print(
        "\nDocument Count:"
    )

    print(
        f"  Total    : "
        f"{report['total_count']}"
    )

    print(
        f"  Has Meta : "
        f"{report['metadata_count']}"
    )

    print(
        "\nMetadata Fields:"
    )

    if not report[
        "metadata_fields"
    ]:
        print(
            "  [EMPTY]"
        )
        return

    for key, statistics in (
        report[
            "metadata_fields"
        ].items()
    ):
        print(
            f"\n  [{key}]"
        )

        print(
            f"    Types      : "
            f"{statistics['types']}"
        )

        print(
            f"    Count      : "
            f"{statistics['count']}"
        )

        print(
            f"    Non-empty  : "
            f"{statistics['non_empty']}"
        )

        print(
            f"    Empty      : "
            f"{statistics['empty']}"
        )

        print(
            f"    Distinct   : "
            f"{statistics['distinct']}"
        )

        print(
            "    Samples    :"
        )

        for sample in statistics[
            "samples"
        ]:
            print(
                "      "
                + json.dumps(
                    sample,
                    ensure_ascii=False,
                    default=str,
                )
            )


def main():
    """執行 Chroma Metadata Inventory Real Test。"""

    print(
        "=" * 70
    )

    print(
        "Chroma Metadata Inventory Real Test"
    )

    print(
        "=" * 70
    )

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    print(
        "\n[1] Project Root"
    )

    print(
        f"  {project_root}"
    )

    print(
        "\n[2] Finding Chroma Persistence Directories..."
    )

    chroma_directories = (
        find_chroma_directories(
            project_root
        )
    )

    assert chroma_directories, (
        "No Chroma persistence directory "
        "containing chroma.sqlite3 was found."
    )

    for directory in chroma_directories:
        print(
            f"  [FOUND] {directory}"
        )

    print(
        "\n[PASS] Chroma persistence directories found"
    )

    print(
        "\n[3] Loading ChromaDB..."
    )

    try:
        import chromadb

    except ImportError as error:
        raise RuntimeError(
            "chromadb is not installed."
        ) from error

    print(
        "[PASS] chromadb imported"
    )

    total_collections = 0

    for chroma_directory in (
        chroma_directories
    ):
        print(
            "\n[4] Opening Chroma:"
        )

        print(
            f"  Path: {chroma_directory}"
        )

        client = (
            chromadb.PersistentClient(
                path=str(
                    chroma_directory
                )
            )
        )

        collections = (
            client.list_collections()
        )

        print(
            f"  Collections: "
            f"{len(collections)}"
        )

        if not collections:
            print(
                "  [EMPTY]"
            )
            continue

        for collection_item in collections:
            collection = get_collection(
                client,
                collection_item,
            )

            total_collections += 1

            print_collection_report(
                collection
            )

    assert total_collections > 0

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Chroma Metadata Inventory Real Test: PASS"
    )

    print(
        "=" * 70
    )

    print(
        "\nNo ChromaDB data was modified."
    )


if __name__ == "__main__":
    main()