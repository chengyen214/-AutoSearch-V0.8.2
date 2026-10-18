"""
tests/V9_1/test_digitimes_archive_robot.py

AutoSearch V9.1

DIGITIMES Archive Robot Real Request Test
"""

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


class TestDigitimesArchiveRobot:
    """
    使用實際 Archive Snapshot 驗證 DIGITIMES Robot。
    """

    URL = "https://www.digitimes.com.tw/tech/"

    VERSION = "2026-09-28T14:19:29"

    def test_digitimes_2026_09_28_robot_request(self):
        """
        詢問 DIGITIMES 2026-09-28 Archive Snapshot。
        """

        response = client.post(
            "/archive/chat",
            json={
                "url": self.URL,
                "query": "2026年9月28日這篇 DIGITIMES 內容有哪些重點？",
                "version": self.VERSION,
            },
        )

        print()
        print("Status Code:", response.status_code)
        print("Response:")
        print(response.json())

        assert response.status_code == 200

        data = response.json()

        assert data is not None