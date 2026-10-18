"""
rag/retriever/ranking.py

AutoSearch V7

RAG Retrieval Ranking

功能：

    Candidate Retrieval Results
        ↓
    Vector Similarity
        +
    matched_ai_keywords
        +
    crawl_time（時間型 Query）
        ↓
    Ranked Candidate Results

本階段不負責：

    - Query Embedding
    - ChromaDB Query
    - URL Scope
    - Candidate-K
    - Final Top-K
    - Context Builder
    - LLM
"""

import json
import re
from datetime import (
    datetime,
    timedelta,
    timezone,
)


VECTOR_WEIGHT = 0.60
KEYWORD_WEIGHT = 0.40

TIME_VECTOR_WEIGHT = 0.50
TIME_KEYWORD_WEIGHT = 0.30
TIME_WEIGHT = 0.20

LOCAL_TIMEZONE = timezone(
    timedelta(hours=8)
)

RECENT_DAYS = 30


class RetrievalRanking:
    """
    Candidate Retrieval Ranking。

    使用：

        Vector Similarity
        matched_ai_keywords
        crawl_time
    """

    @staticmethod
    def _validate_result(
        result
    ):
        """
        驗證 ChromaDB Candidate Result。
        """

        if result is None:
            raise ValueError(
                "Retrieval result cannot be None."
            )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "Retrieval result must be a dict."
            )

        required_fields = [
            "ids",
            "documents",
            "metadatas",
            "distances",
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    "Retrieval result is missing "
                    f"'{field}'."
                )

    @staticmethod
    def _get_first_group(
        result,
        field,
    ):
        """
        取得 ChromaDB single-query result。
        """

        values = result[field]

        if not isinstance(
            values,
            list,
        ):
            raise TypeError(
                f"Retrieval field '{field}' "
                "must be a list."
            )

        if not values:
            return []

        first_group = values[0]

        if first_group is None:
            return []

        if not isinstance(
            first_group,
            list,
        ):
            raise TypeError(
                f"Retrieval field '{field}' "
                "first group must be a list."
            )

        return first_group

    @staticmethod
    def _similarity_from_distance(
        distance
    ):
        """
        將 cosine distance 轉成 similarity。

        similarity = 1 - distance
        """

        if not isinstance(
            distance,
            (int, float),
        ):
            raise TypeError(
                "distance must be numeric."
            )

        similarity = (
            1.0 - float(distance)
        )

        return max(
            0.0,
            min(
                1.0,
                similarity,
            ),
        )

    @staticmethod
    def _load_keywords(
        value
    ):
        """
        將 matched_ai_keywords 轉成 list。
        """

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):
            value = value.strip()

            if not value:
                return []

            try:
                value = json.loads(
                    value
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                return []

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                str(keyword).strip()
                for keyword in value
                if keyword is not None
                and str(keyword).strip()
            ]

        return []

    @classmethod
    def _keyword_score(
        cls,
        metadata,
    ):
        """
        計算 matched_ai_keywords Score。

        目前採用：

            有 matched keyword → 1.0
            無 matched keyword → 0.0
        """

        if not isinstance(
            metadata,
            dict,
        ):
            return 0.0

        keywords = cls._load_keywords(
            metadata.get(
                "matched_ai_keywords"
            )
        )

        if not keywords:
            return 0.0

        return 1.0

    @staticmethod
    def _is_time_query(
        query
    ):
        """
        判斷 Query 是否具有時間需求。
        """

        if not query:
            return False

        patterns = [
            r"最近",
            r"最新",
            r"近期",
            r"這個月",
            r"本月",
            r"上個月",
            r"上月",
            r"這週",
            r"本週",
            r"上週",
            r"這星期",
            r"本星期",
            r"上星期",
            r"今天",
            r"昨天",
            r"前幾天",
            r"近\s*[一二三四五六七八九十0-9]+\s*天",
            r"近\s*[一二三四五六七八九十0-9]+\s*週",
            r"近\s*[一二三四五六七八九十0-9]+\s*星期",
            r"近\s*[一二三四五六七八九十0-9]+\s*個月",
            r"20\d{2}\s*年",
            r"20\d{2}\s*[-/]\s*\d{1,2}",
        ]

        return any(
            re.search(
                pattern,
                str(query),
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    @staticmethod
    def _is_exact_date_query(
        query
    ):
        """
        判斷 Query 是否指定明確日期。

        支援：

            2026年9月28日
            2026-09-28
            2026/09/28
        """

        if not query:
            return False

        patterns = [
            r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
            r"20\d{2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{1,2}",
        ]

        return any(
            re.search(
                pattern,
                str(query),
            )
            for pattern in patterns
        )

    @staticmethod
    def _parse_crawl_time(
        value
    ):
        """
        解析 crawl_time。
        """

        if not value:
            return None

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        try:
            crawl_time = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            return None

        if crawl_time.tzinfo is None:
            crawl_time = crawl_time.replace(
                tzinfo=timezone.utc
            )

        return crawl_time

    @staticmethod
    def _parse_number(
        value
    ):
        """
        將中文數字或阿拉伯數字轉成 int。
        """

        if value is None:
            return None

        value = str(
            value
        ).strip()

        if value.isdigit():
            return int(
                value
            )

        chinese_numbers = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }

        if value in chinese_numbers:
            return chinese_numbers[value]

        return None

    @staticmethod
    def _month_range(
        year,
        month,
        tz,
    ):
        """
        建立指定月份的時間範圍。

        回傳：

            start
            end
        """

        start = datetime(
            year,
            month,
            1,
            tzinfo=tz,
        )

        if month == 12:
            end = datetime(
                year + 1,
                1,
                1,
                tzinfo=tz,
            )
        else:
            end = datetime(
                year,
                month + 1,
                1,
                tzinfo=tz,
            )

        return start, end

    @staticmethod
    def _day_range(
        year,
        month,
        day,
        tz,
    ):
        """
        建立指定日期的時間範圍。

        回傳：

            start
            end
        """

        start = datetime(
            year,
            month,
            day,
            tzinfo=tz,
        )

        end = (
            start
            + timedelta(days=1)
        )

        return start, end

    @classmethod
    def _parse_time_range(
        cls,
        query,
        now=None,
    ):
        """
        將時間型 Query 解析成時間範圍。

        回傳：

            (start, end)

        無明確範圍時：

            (None, None)
        """

        if not query:
            return None, None

        if now is None:
            now = datetime.now(
                LOCAL_TIMEZONE
            )

        if now.tzinfo is None:
            now = now.replace(
                tzinfo=LOCAL_TIMEZONE
            )

        query = str(
            query
        ).strip()

        if not query:
            return None, None

        if re.search(
            r"今天",
            query,
        ):
            start = datetime(
                now.year,
                now.month,
                now.day,
                tzinfo=LOCAL_TIMEZONE,
            )

            end = (
                start
                + timedelta(days=1)
            )

            return start, end

        if re.search(
            r"昨天",
            query,
        ):
            end = datetime(
                now.year,
                now.month,
                now.day,
                tzinfo=LOCAL_TIMEZONE,
            )

            start = (
                end
                - timedelta(days=1)
            )

            return start, end

        match = re.search(
            r"近\s*([一二三四五六七八九十0-9]+)\s*天",
            query,
        )

        if match:
            days = cls._parse_number(
                match.group(1)
            )

            if days:
                return (
                    now - timedelta(days=days),
                    now,
                )

        match = re.search(
            r"近\s*([一二三四五六七八九十0-9]+)\s*週",
            query,
        )

        if match:
            weeks = cls._parse_number(
                match.group(1)
            )

            if weeks:
                return (
                    now - timedelta(
                        weeks=weeks
                    ),
                    now,
                )

        match = re.search(
            r"近\s*([一二三四五六七八九十0-9]+)\s*星期",
            query,
        )

        if match:
            weeks = cls._parse_number(
                match.group(1)
            )

            if weeks:
                return (
                    now - timedelta(
                        weeks=weeks
                    ),
                    now,
                )

        match = re.search(
            r"近\s*([一二三四五六七八九十0-9]+)\s*個月",
            query,
        )

        if match:
            months = cls._parse_number(
                match.group(1)
            )

            if months:
                return (
                    now - timedelta(
                        days=months * 30
                    ),
                    now,
                )

        if re.search(
            r"(這個月|本月)",
            query,
        ):
            start = datetime(
                now.year,
                now.month,
                1,
                tzinfo=LOCAL_TIMEZONE,
            )

            return start, now

        if re.search(
            r"(上個月|上月)",
            query,
        ):
            if now.month == 1:
                year = now.year - 1
                month = 12
            else:
                year = now.year
                month = now.month - 1

            return cls._month_range(
                year,
                month,
                LOCAL_TIMEZONE,
            )

        year_month_day_match = re.search(
            r"(20\d{2})\s*年\s*"
            r"(\d{1,2})\s*月\s*"
            r"(\d{1,2})\s*日",
            query,
        )

        if year_month_day_match:
            year = int(
                year_month_day_match.group(1)
            )

            month = int(
                year_month_day_match.group(2)
            )

            day = int(
                year_month_day_match.group(3)
            )

            try:
                return cls._day_range(
                    year,
                    month,
                    day,
                    LOCAL_TIMEZONE,
                )
            except ValueError:
                return None, None

        year_month_day_match = re.search(
            r"(20\d{2})\s*[-/]\s*"
            r"(\d{1,2})\s*[-/]\s*"
            r"(\d{1,2})",
            query,
        )

        if year_month_day_match:
            year = int(
                year_month_day_match.group(1)
            )

            month = int(
                year_month_day_match.group(2)
            )

            day = int(
                year_month_day_match.group(3)
            )

            try:
                return cls._day_range(
                    year,
                    month,
                    day,
                    LOCAL_TIMEZONE,
                )
            except ValueError:
                return None, None

        year_month_match = re.search(
            r"(20\d{2})\s*年\s*(\d{1,2})\s*月",
            query,
        )

        if year_month_match:
            year = int(
                year_month_match.group(1)
            )

            month = int(
                year_month_match.group(2)
            )

            if 1 <= month <= 12:
                return cls._month_range(
                    year,
                    month,
                    LOCAL_TIMEZONE,
                )

        year_month_match = re.search(
            r"(20\d{2})\s*[-/]\s*(\d{1,2})",
            query,
        )

        if year_month_match:
            year = int(
                year_month_match.group(1)
            )

            month = int(
                year_month_match.group(2)
            )

            if 1 <= month <= 12:
                return cls._month_range(
                    year,
                    month,
                    LOCAL_TIMEZONE,
                )

        year_match = re.search(
            r"(20\d{2})\s*年",
            query,
        )

        if year_match:
            year = int(
                year_match.group(1)
            )

            start = datetime(
                year,
                1,
                1,
                tzinfo=LOCAL_TIMEZONE,
            )

            end = datetime(
                year + 1,
                1,
                1,
                tzinfo=LOCAL_TIMEZONE,
            )

            return start, end

        if re.search(
            r"(最近|最新|近期)",
            query,
        ):
            return (
                now - timedelta(
                    days=RECENT_DAYS
                ),
                now,
            )

        return None, None

    @staticmethod
    def _is_freshness_query(
        query
    ):
        """
        判斷是否為模糊的新近時間 Query。

        最近、最新、近期使用 freshness ranking，
        而不是單純判斷是否落在固定時間範圍內。
        """

        if not query:
            return False

        return bool(
            re.search(
                r"(最近|最新|近期)",
                str(query),
            )
        )

    @staticmethod
    def _time_range_score(
        crawl_time,
        start,
        end,
        now=None,
    ):
        """
        計算 crawl_time 時間符合度。

        指定時間範圍：

            範圍內 → 1.0
            範圍外 → 0.0

        無指定時間範圍：

            使用 freshness score。
        """

        if crawl_time is None:
            return 0.0

        if now is None:
            now = datetime.now(
                LOCAL_TIMEZONE
            )

        if now.tzinfo is None:
            now = now.replace(
                tzinfo=LOCAL_TIMEZONE
            )

        if start is None or end is None:
            return RetrievalRanking._freshness_score(
                crawl_time,
                now=now,
            )

        if crawl_time < start:
            return 0.0

        if crawl_time >= end:
            return 0.0

        return 1.0

    @staticmethod
    def _freshness_score(
        crawl_time,
        now=None,
    ):
        """
        計算 crawl_time freshness score。

        越新分數越高。
        """

        if crawl_time is None:
            return 0.0

        if now is None:
            now = datetime.now(
                timezone.utc
            )

        if now.tzinfo is None:
            now = now.replace(
                tzinfo=timezone.utc
            )

        if crawl_time.tzinfo is None:
            crawl_time = crawl_time.replace(
                tzinfo=timezone.utc
            )

        age = (
            now - crawl_time
        ).total_seconds()

        if age <= 0:
            return 1.0

        days = (
            age / 86400.0
        )

        return max(
            0.0,
            1.0 - min(
                days / RECENT_DAYS,
                1.0,
            ),
        )

    def rank(
        self,
        result,
        query,
        now=None,
    ):
        """
        重新排序 Candidate Results。

        Exact Date Query：

            先進行時間硬過濾，
            只有指定日期的 Candidate
            才進入 Vector + Keyword Ranking。

        Month / Year Query：

            使用時間範圍 Score。

        最近 / 最新 / 近期：

            使用 Freshness Ranking。

        不修改原始 Result。

        now：

            測試時可指定固定時間。
            正式執行未指定時使用目前時間。
        """

        self._validate_result(
            result
        )

        ids = self._get_first_group(
            result,
            "ids",
        )

        documents = self._get_first_group(
            result,
            "documents",
        )

        metadatas = self._get_first_group(
            result,
            "metadatas",
        )

        distances = self._get_first_group(
            result,
            "distances",
        )

        lengths = {
            len(ids),
            len(documents),
            len(metadatas),
            len(distances),
        }

        if len(lengths) != 1:
            raise ValueError(
                "Retrieval result count mismatch."
            )

        if now is None:
            now = datetime.now(
                LOCAL_TIMEZONE
            )

        if now.tzinfo is None:
            now = now.replace(
                tzinfo=LOCAL_TIMEZONE
            )

        time_query = self._is_time_query(
            query
        )

        exact_date_query = (
            self._is_exact_date_query(
                query
            )
        )

        freshness_query = (
            self._is_freshness_query(
                query
            )
        )

        time_start = None
        time_end = None

        if time_query:
            time_start, time_end = (
                self._parse_time_range(
                    query,
                    now=now,
                )
            )

        ranked = []

        for index in range(
            len(ids)
        ):
            metadata = (
                metadatas[index]
                or {}
            )

            crawl_time = None

            if time_query:
                crawl_time = (
                    self._parse_crawl_time(
                        metadata.get(
                            "crawl_time"
                        )
                    )
                )

            if (
                exact_date_query
                and (
                    time_start is None
                    or time_end is None
                )
            ):
                continue

            if (
                exact_date_query
                and (
                    crawl_time is None
                    or crawl_time < time_start
                    or crawl_time >= time_end
                )
            ):
                continue

            similarity = (
                self._similarity_from_distance(
                    distances[index]
                )
            )

            keyword_score = (
                self._keyword_score(
                    metadata
                )
            )

            if time_query:
                if freshness_query:
                    time_score = (
                        self._freshness_score(
                            crawl_time,
                            now=now,
                        )
                    )
                else:
                    time_score = (
                        self._time_range_score(
                            crawl_time,
                            time_start,
                            time_end,
                            now=now,
                        )
                    )

                score = (
                    TIME_VECTOR_WEIGHT
                    * similarity
                    +
                    TIME_KEYWORD_WEIGHT
                    * keyword_score
                    +
                    TIME_WEIGHT
                    * time_score
                )

            else:
                score = (
                    VECTOR_WEIGHT
                    * similarity
                    +
                    KEYWORD_WEIGHT
                    * keyword_score
                )

            ranked.append(
                (
                    score,
                    index,
                )
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return {
            "ids": [
                ids[index]
                for _, index in ranked
            ],
            "documents": [
                documents[index]
                for _, index in ranked
            ],
            "metadatas": [
                metadatas[index]
                for _, index in ranked
            ],
            "distances": [
                distances[index]
                for _, index in ranked
            ],
        }


__all__ = [
    "RetrievalRanking",
]