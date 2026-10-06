"""
search/google_search_provider.py

AutoSearch V5

V5.6.3

Google Search Provider
SerpApi Implementation

用途：

    使用 SerpApi Google Search API
    執行 Google Web Search。

支援：

    1. Keyword Search

    2. URL + Keyword Search

    3. Exclude URL

    4. Time Range Search

本模組負責：

    - SerpApi Request
    - Google Search Request
    - API Response Parsing
    - SearchResult 建立
    - Result Limit
    - URL / Site Search
    - Exclude URL
    - Time Range
    - API Configuration

不負責：

    - SearchAdapter
    - SearchAdapterManager
    - Provider Resolution
    - SearchExecutionBridge
    - URL Deduplication
    - Crawler
    - Parser
    - Archive
    - AI
"""


import os
import re

from urllib.parse import (
    urlparse,
)

import requests

from dotenv import (
    load_dotenv,
)

from models.search_result import (
    SearchResult,
)

from search.search_provider import (
    SearchProvider,
)


load_dotenv()


class GoogleSearchProvider(
    SearchProvider
):
    """
    Google Search Provider。

    Backend:

        SerpApi

    支援：

        keyword

        keyword + optional url

        exclude_urls

        when:7d

        when:1m

        when:6m
    """

    provider_name = (
        "google_search"
    )

    max_results = 20

    API_URL = (
        "https://serpapi.com/search"
    )

    def __init__(
        self,
        api_key=None,
        timeout=7,
    ):
        """
        建立 Google Search Provider。

        Parameters
        ----------

        api_key:

            SerpApi API Key。

            如果沒有直接傳入，
            則從：

                SERPAPI_API_KEY

            讀取。

        timeout:

            HTTP Request Timeout。
        """

        self.api_key = (
            api_key
            or os.getenv(
                "SERPAPI_API_KEY"
            )
        )

        self.timeout = timeout

    def is_configured(
        self,
    ):
        """
        判斷 SerpApi 是否已設定 API Key。
        """

        return bool(
            self.api_key
        )

    @staticmethod
    def _normalize_url(
        url,
    ):
        """
        將 URL 正規化成 hostname。
        """

        if url is None:

            return None

        url = str(
            url
        ).strip()

        if not url:

            return None

        parse_target = url

        if not (
            parse_target.startswith(
                "http://"
            )
            or
            parse_target.startswith(
                "https://"
            )
        ):

            parse_target = (
                "https://"
                + parse_target
            )

        parsed = urlparse(
            parse_target
        )

        hostname = (
            parsed.hostname
        )

        if not hostname:

            return None

        hostname = (
            hostname.strip()
        )

        if not hostname:

            return None

        return hostname

    @classmethod
    def _build_query(
        cls,
        keyword,
        url=None,
    ):
        """
        建立 SerpApi Google Search Query。
        """

        keyword = str(
            keyword
        ).strip()

        site = cls._normalize_url(
            url
        )

        if site:

            return (
                f"site:{site} {keyword}"
            )

        return keyword

    @staticmethod
    def _build_time_filter(
        keyword,
    ):
        """
        將 when:7d、when:1m、when:6m 轉換成 SerpApi tbs。
        """

        match = re.search(
            r"\bwhen:(\d+)([dwm])\b",
            keyword,
            re.IGNORECASE,
        )

        if not match:

            return (
                keyword,
                None,
            )

        value = int(
            match.group(1)
        )

        unit = (
            match.group(2).lower()
        )

        if value <= 0:

            return (
                keyword,
                None,
            )

        if unit == "d":

            if value == 1:

                tbs = "qdr:d"

            else:

                tbs = (
                    f"qdr:d{value}"
                )

        elif unit == "w":

            if value == 1:

                tbs = "qdr:w"

            else:

                tbs = (
                    f"qdr:w{value}"
                )

        elif unit == "m":

            if value == 1:

                tbs = "qdr:m"

            else:

                tbs = (
                    f"qdr:m{value}"
                )

        else:

            return (
                keyword,
                None,
            )

        query = re.sub(
            r"\s+when:\d+[dwm]\b",
            "",
            keyword,
            flags=re.IGNORECASE,
        ).strip()

        return (
            query,
            tbs,
        )

    @staticmethod
    def _normalize_exclude_urls(
        exclude_urls,
    ):
        """
        正規化需要排除的 URL。
        """

        if not exclude_urls:

            return set()

        if isinstance(
            exclude_urls,
            str,
        ):

            exclude_urls = [
                exclude_urls
            ]

        try:

            items = list(
                exclude_urls
            )

        except TypeError:

            return set()

        results = set()

        for url in items:

            if url is None:

                continue

            url = str(
                url
            ).strip()

            if not url:

                continue

            results.add(
                url
            )

        return results

    def search(
        self,
        keyword,
        max_results=None,
        url=None,
        exclude_urls=None,
    ):
        """
        執行 SerpApi Google Search。

        Parameters
        ----------

        keyword:

            Search keyword。

            支援：

                when:7d

                when:1m

                when:6m

        max_results:

            最大搜尋結果數量。

        url:

            Optional website URL。

        exclude_urls:

            不希望出現在結果中的 URL。

        Returns
        -------

        list[SearchResult]
        """

        if keyword is None:

            return []

        keyword = str(
            keyword
        ).strip()

        if not keyword:

            return []

        if max_results is None:

            max_results = (
                self.max_results
            )

        try:

            max_results = int(
                max_results
            )

        except (
            TypeError,
            ValueError,
        ):

            max_results = (
                self.max_results
            )

        if max_results <= 0:

            return []

        exclude_urls = (
            self._normalize_exclude_urls(
                exclude_urls
            )
        )

        if not self.is_configured():

            raise ValueError(
                "SerpApi API key "
                "is not configured. "
                "Please set SERPAPI_API_KEY "
                "in .env."
            )

        search_keyword, time_filter = (
            self._build_time_filter(
                keyword
            )
        )

        query = (
            self._build_query(
                search_keyword,
                url=url,
            )
        )

        request_limit = min(
            max_results + len(exclude_urls),
            100,
        )

        params = {

            "engine":
                "google",

            "q":
                query,

            "api_key":
                self.api_key,

            "num":
                request_limit,

            "output":
                "json",

        }

        if time_filter:

            params["tbs"] = (
                time_filter
            )

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(
            data,
            dict,
        ):

            return []

        error = data.get(
            "error"
        )

        if error:

            raise ValueError(
                "SerpApi Google Search "
                f"error: {error}"
            )

        organic_results = data.get(
            "organic_results",
            [],
        )

        if not isinstance(
            organic_results,
            list,
        ):

            return []

        results = []

        for item in organic_results:

            if not isinstance(
                item,
                dict,
            ):

                continue

            result_url = item.get(
                "link",
                "",
            )

            if not result_url:

                continue

            result_url = str(
                result_url
            ).strip()

            if not result_url:

                continue

            if result_url in exclude_urls:

                continue

            title = item.get(
                "title",
                "",
            )

            snippet = item.get(
                "snippet",
                "",
            )

            source = ""

            displayed_link = item.get(
                "displayed_link",
                "",
            )

            if displayed_link:

                source = displayed_link

            else:

                parsed_url = urlparse(
                    result_url
                )

                source = (
                    parsed_url.netloc
                    or ""
                )

            result = SearchResult(
                keyword=keyword,
                title=title,
                url=result_url,
                source=source,
                published=None,
                search_source=self.provider_name,
                rank=len(results) + 1,
            )

            results.append(
                result
            )

            if (
                len(results)
                >= max_results
            ):

                break

        return results


__all__ = [
    "GoogleSearchProvider",
]