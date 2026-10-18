"""
tests/V9_0/test_articles_structure.py

AutoSearch V5

Articles Table Structure Real Test

測試：

1. MySQL Connection
2. articles Table Exists
3. Articles Table Columns
4. Articles Table Row Count
"""

from database.connection import (
    get_connection,
)


TABLE_NAME = "articles"


def main():
    """執行 Articles Table Structure Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Articles Table Structure Real Test"
    )

    print(
        "=" * 60
    )

    connection = None
    cursor = None

    try:
        print(
            "\n[1] Connecting MySQL..."
        )

        connection = get_connection()

        assert connection is not None

        print(
            "[PASS] MySQL connection successful"
        )

        cursor = connection.cursor()

        print(
            "\n[2] Checking articles table..."
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = %s
            """,
            (
                TABLE_NAME,
            ),
        )

        table_count = cursor.fetchone()[0]

        assert table_count == 1

        print(
            "[PASS] articles table exists"
        )

        print(
            "\n[3] Reading articles columns..."
        )

        cursor.execute(
            f"SHOW COLUMNS FROM `{TABLE_NAME}`"
        )

        columns = cursor.fetchall()

        assert columns

        print()

        for index, column in enumerate(
            columns,
            start=1,
        ):
            field = column[0]
            column_type = column[1]
            nullable = column[2]
            key = column[3]
            default = column[4]
            extra = column[5]

            print(
                f"{index}. {field}"
            )

            print(
                f"   Type       : {column_type}"
            )

            print(
                f"   Null       : {nullable}"
            )

            print(
                f"   Key        : {key}"
            )

            print(
                f"   Default    : {default}"
            )

            print(
                f"   Extra      : {extra}"
            )

        print(
            f"\nTotal Columns: {len(columns)}"
        )

        print(
            "\n[PASS] Articles table structure loaded"
        )

        print(
            "\n[4] Reading articles row count..."
        )

        cursor.execute(
            f"SELECT COUNT(*) FROM `{TABLE_NAME}`"
        )

        row_count = cursor.fetchone()[0]

        print(
            f"Articles Rows: {row_count}"
        )

        print(
            "\n[PASS] Articles table row count loaded"
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Articles Table Structure Real Test: PASS"
        )

        print(
            "=" * 60
        )

    except Exception as e:
        print(
            "\n"
            + "=" * 60
        )

        print(
            "Articles Table Structure Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()