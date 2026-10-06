"""
search/google_news_provider.py

AutoSearch V5

V5.2 P2.3

Google News Search Provider

用途：

    將 V4 既有 Google News RSS Search
    包裝成 V5 SearchProvider。

本模組負責：

    - Google News Provider
    - Provider Identity
    - Keyword Validation
    - Result Limit
    - 取得全部 Target crawler_url
    - 呼叫 V4 Google News Search
    - Google News 時間範圍搜尋
    - Google Search 時間範圍搜尋
    - IC semiconductor 多階段時間補充搜尋
    - Target Source Exclusion
    - Google News URL Exclusion
    - SearchResult Validation
    - SearchResult Normalization
    - 7 天結果優先
    - 延伸候選隨機補足
    - Google News URL Decode
    - Final Result URL Output

本模組不負責：

    - ProviderSearchAdapter 建立
    - SearchAdapter
    - SearchAdapterManager
    - SearchExecutionBridge
    - Crawler
    - Parser
    - Article
    - Archive
    - AI
    - Target INSERT / UPDATE
"""

import random

from search.search_engine import (
    search as google_news_search,
)

from search.search_engine import (
    resolve_google_news_urls,
)

from search.google_search_provider import (
    GoogleSearchProvider,
)

from search.search_provider import (
    SearchProvider,
)

from models.search_result import (
    SearchResult,
)

from services.url_source_grouping_service import (
    URLSourceGroupingService,
)

from database.connection import (
    get_connection,
)

from utils.logger import (
    logger,
)


class GoogleNewsProvider(SearchProvider):
    """
    V5 Google News Search Provider。
    """

    provider_name = "google_news"

    max_results = 10

    candidate_results = 45

    search_time_range = "when:7d"

    def __init__(
        self,
        timeout=7,
    ):
        """
        建立 GoogleNewsProvider。
        """

        self.timeout = timeout

        self.url_source_grouping_service = (
            URLSourceGroupingService()
        )

        self.google_search_provider = (
            GoogleSearchProvider(
                timeout=timeout,
            )
        )

    def search(
        self,
        keyword,
        max_results=None,
    ):
        """
        執行 Google News + Google Search。
        """

        keyword = self._normalize_keyword(
            keyword
        )

        if not keyword:
            return []

        max_results = (
            self._normalize_max_results(
                max_results
            )
        )

        if max_results <= 0:
            return []

        crawler_urls = (
            self.url_source_grouping_service
            .fetch_crawler_urls()
        )

        search_keyword = (
            f"{keyword} "
            f"{self.search_time_range}"
        )

        primary_results = (
            google_news_search(
                search_keyword,
                max_results=self.candidate_results,
                resolve_urls=False,
            )
        )

        source_results = list(
            primary_results
        )

        if (
            keyword.lower()
            == "ic semiconductor"
            and len(source_results)
            < self.candidate_results
        ):
            remaining_candidates = (
                self.candidate_results
                - len(source_results)
            )

            additional_results = (
                google_news_search(
                    (
                        f"{keyword} "
                        f"when:1m"
                    ),
                    max_results=remaining_candidates,
                    resolve_urls=False,
                )
            )

            source_results.extend(
                additional_results
            )

            if (
                len(source_results)
                < self.candidate_results
            ):
                remaining_candidates = (
                    self.candidate_results
                    - len(source_results)
                )

                additional_results = (
                    google_news_search(
                        (
                            f"{keyword} "
                            f"when:6m"
                        ),
                        max_results=remaining_candidates,
                        resolve_urls=False,
                    )
                )

                source_results.extend(
                    additional_results
                )

        results = self._normalize_results(
            source_results=source_results,
            keyword=keyword,
            max_results=max_results,
            crawler_urls=crawler_urls,
            primary_results=primary_results,
        )

        results = self._decode_selected_news_results(
            results
        )

        google_news_urls = {
            str(
                getattr(
                    item,
                    "url",
                    "",
                )
            ).strip()
            for item in results
            if getattr(
                item,
                "url",
                None,
            )
        }

        google_search_results = (
            self._search_google_results(
                keyword=keyword,
                crawler_urls=crawler_urls,
                exclude_urls=google_news_urls,
                max_results=max_results,
            )
        )

        final_results = (
            results
            +
            google_search_results
        )

        self._print_final_results(
            final_results
        )

        return final_results

    @staticmethod
    def _decode_selected_news_results(
        results,
    ):
        """
        並行 Decode 最終選出的 Google News Results。
        """

        if not results:
            return []

        valid_results = []

        for item in results:

            if not isinstance(
                item,
                SearchResult,
            ):
                continue

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            valid_results.append(
                item
            )

        if not valid_results:
            return []

        urls = [
            str(
                getattr(
                    item,
                    "url",
                    "",
                )
            ).strip()
            for item in valid_results
        ]

        decoded_urls = (
            resolve_google_news_urls(
                urls
            )
        )

        decoded_results = []

        for item in valid_results:

            url = str(
                getattr(
                    item,
                    "url",
                    "",
                )
            ).strip()

            decoded_url = decoded_urls.get(
                url,
                url,
            )

            if not decoded_url:
                continue

            item.url = str(
                decoded_url
            ).strip()

            decoded_results.append(
                item
            )

        for index, item in enumerate(
            decoded_results,
            start=1,
        ):
            item.rank = index

        return decoded_results

    def _search_google_results(
        self,
        keyword,
        crawler_urls,
        exclude_urls=None,
        max_results=10,
    ):
        """
        執行 Google Search。
        """

        primary_results = (
            self.google_search_provider.search(
                (
                    f"{keyword} "
                    f"{self.search_time_range}"
                ),
                max_results=self.candidate_results,
                exclude_urls=exclude_urls,
            )
        )

        source_results = list(
            primary_results
        )

        if (
            keyword.lower()
            == "ic semiconductor"
            and len(source_results)
            < self.candidate_results
        ):
            remaining_candidates = (
                self.candidate_results
                - len(source_results)
            )

            additional_results = (
                self.google_search_provider.search(
                    (
                        f"{keyword} "
                        f"when:1m"
                    ),
                    max_results=remaining_candidates,
                    exclude_urls=exclude_urls,
                )
            )

            source_results.extend(
                additional_results
            )

            if (
                len(source_results)
                < self.candidate_results
            ):
                remaining_candidates = (
                    self.candidate_results
                    - len(source_results)
                )

                additional_results = (
                    self.google_search_provider.search(
                        (
                            f"{keyword} "
                            f"when:6m"
                        ),
                        max_results=remaining_candidates,
                        exclude_urls=exclude_urls,
                    )
                )

                source_results.extend(
                    additional_results
                )

        return self._normalize_google_search_results(
            source_results=source_results,
            primary_results=primary_results,
            keyword=keyword,
            max_results=max_results,
            crawler_urls=crawler_urls,
            exclude_urls=exclude_urls,
        )

    @classmethod
    def _normalize_google_search_results(
        cls,
        source_results,
        primary_results=None,
        keyword="",
        max_results=10,
        crawler_urls=None,
        exclude_urls=None,
    ):
        """
        Validate / Normalize Google Search Results。
        """

        if source_results is None:
            return []

        if not isinstance(
            source_results,
            list,
        ):
            raise TypeError(
                "Google Search "
                "must return a list"
            )

        if primary_results is None:
            primary_results = []

        if crawler_urls is None:
            crawler_urls = []

        if exclude_urls is None:
            exclude_urls = set()

        exclude_urls = {
            str(url).strip()
            for url in exclude_urls
            if url
        }

        primary_urls = set()

        for item in primary_results:

            if not isinstance(
                item,
                SearchResult,
            ):
                continue

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            url = str(
                url
            ).strip()

            if not url:
                continue

            primary_urls.add(
                url
            )

        primary_candidates = []

        extended_candidates = []

        seen_urls = set()

        for item in source_results:

            if not isinstance(
                item,
                SearchResult,
            ):
                continue

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            url = str(
                url
            ).strip()

            if not url:
                continue

            if url in exclude_urls:
                continue

            if url in seen_urls:
                continue

            excluded = False

            for crawler_url in crawler_urls:

                if (
                    URLSourceGroupingService
                    .is_excluded_by_crawler_url(
                        url,
                        crawler_url,
                    )
                ):
                    excluded = True
                    break

            if excluded:
                continue

            seen_urls.add(
                url
            )

            if url in primary_urls:
                primary_candidates.append(
                    item
                )

            else:
                extended_candidates.append(
                    item
                )

        if (
            not primary_candidates
            and not extended_candidates
        ):
            return []

        results = []

        for item in primary_candidates:

            results.append(
                item
            )

            if len(results) >= max_results:
                break

        if len(results) < max_results:

            remaining = (
                max_results
                - len(results)
            )

            if (
                len(extended_candidates)
                <= remaining
            ):
                results.extend(
                    extended_candidates
                )

            else:
                results.extend(
                    random.sample(
                        extended_candidates,
                        remaining,
                    )
                )

        normalized_results = []

        for item in results:

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            try:
                item.url = str(
                    url
                ).strip()

            except AttributeError:
                pass

            try:
                item.keyword = keyword

            except AttributeError:
                pass

            try:
                item.search_source = (
                    "google_search"
                )

            except AttributeError:
                pass

            try:
                item.rank = (
                    len(normalized_results)
                    + 1
                )

            except AttributeError:
                pass

            normalized_results.append(
                item
            )

        return normalized_results

    @staticmethod
    def _normalize_keyword(
        keyword,
    ):
        """
        Normalize Search Keyword。
        """

        if keyword is None:
            return ""

        keyword = str(
            keyword
        ).strip()

        return keyword

    @classmethod
    def _normalize_max_results(
        cls,
        max_results,
    ):
        """
        Normalize Result Limit。
        """

        if max_results is None:
            return cls.max_results

        try:
            value = int(
                max_results
            )

        except (
            TypeError,
            ValueError,
        ):
            return cls.max_results

        return min(
            value,
            cls.max_results,
        )

    @classmethod
    def _normalize_results(
        cls,
        source_results,
        keyword,
        max_results,
        crawler_urls=None,
        primary_results=None,
    ):
        """
        Validate / Normalize V4 Search Results。
        """

        if source_results is None:
            return []

        if not isinstance(
            source_results,
            list,
        ):
            raise TypeError(
                "Google News Search "
                "must return a list"
            )

        if crawler_urls is None:
            crawler_urls = []

        if primary_results is None:
            primary_results = []

        primary_urls = set()

        for item in primary_results:

            if not isinstance(
                item,
                SearchResult,
            ):
                continue

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            url = str(
                url
            ).strip()

            if not url:
                continue

            primary_urls.add(
                url
            )

        primary_candidates = []

        extended_candidates = []

        seen_urls = set()

        for item in source_results:

            if not isinstance(
                item,
                SearchResult,
            ):
                continue

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            url = str(
                url
            ).strip()

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(
                url
            )

            if url in primary_urls:
                primary_candidates.append(
                    item
                )

            else:
                extended_candidates.append(
                    item
                )

        if (
            not primary_candidates
            and not extended_candidates
        ):
            return []

        results = []

        for item in primary_candidates:

            results.append(
                item
            )

            if len(results) >= max_results:
                break

        if len(results) < max_results:

            remaining = (
                max_results
                - len(results)
            )

            if (
                len(extended_candidates)
                <= remaining
            ):
                results.extend(
                    extended_candidates
                )

            else:
                results.extend(
                    random.sample(
                        extended_candidates,
                        remaining,
                    )
                )

        normalized_results = []

        for item in results:

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            try:
                item.url = str(
                    url
                ).strip()

            except AttributeError:
                pass

            try:
                item.keyword = keyword

            except AttributeError:
                pass

            try:
                item.search_source = (
                    cls.provider_name
                )

            except AttributeError:
                pass

            try:
                item.rank = (
                    len(normalized_results)
                    + 1
                )

            except AttributeError:
                pass

            normalized_results.append(
                item
            )

        return normalized_results

    @staticmethod
    def _print_final_results(
        results,
    ):
        """
        只顯示 Provider 最終結果 URL。
        """

        print()

        print(
            "=" * 50
        )

        print(
            "Google News + Google Search Final Results"
        )

        print(
            "=" * 50
        )

        for index, item in enumerate(
            results,
            start=1,
        ):

            url = getattr(
                item,
                "url",
                None,
            )

            if not url:
                continue

            print(
                f"{index}. URL: {url}"
            )

        print(
            "=" * 50
        )

    @staticmethod
    def _get_existing_urls(
        urls,
    ):
        """
        查詢 MySQL articles.url。
        """

        if not urls:
            return set()

        conn = None
        cursor = None

        try:

            conn = get_connection()

            if conn is None:

                logger.warning(
                    "SQL connection unavailable "
                    "during Google News URL lookup."
                )

                return set()

            cursor = conn.cursor()

            placeholders = ", ".join(
                ["%s"] * len(urls)
            )

            query = f"""
                SELECT url
                FROM articles
                WHERE url IN ({placeholders})
            """

            cursor.execute(
                query,
                tuple(urls),
            )

            rows = cursor.fetchall()

            existing_urls = set()

            for row in rows:

                if not row:
                    continue

                url = row[0]

                if url is None:
                    continue

                existing_urls.add(
                    str(url).strip()
                )

            return existing_urls

        except Exception as exc:

            logger.exception(
                "Failed to query existing "
                "Google News Article URLs: "
                f"error={exc}"
            )

            return set()

        finally:

            if cursor is not None:

                try:
                    cursor.close()

                except Exception:
                    pass

            if conn is not None:

                try:
                    conn.close()

                except Exception:
                    pass


__all__ = [
    "GoogleNewsProvider",
]