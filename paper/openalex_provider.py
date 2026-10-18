"""
paper/openalex_provider.py

AutoSearch V5

OpenAlex Paper Provider

功能：

1. OpenAlex Keyword Search
2. Publication Date Filter
3. Stored Paper Exclusion
4. Candidate Pool Selection
5. Paper Landing Page URL
6. Paper PDF URL
7. Landing Page URL Resolution
8. Landing Page Location Fallback
9. Random Fallback

DEFAULT_PER_PAGE = 候選數目
DEFAULT_RESULT_COUNT = 實際目標數目
"""

import random
from datetime import date, timedelta
from urllib.parse import urlparse

import requests

from database.paper_repository import (
    PaperRepository
)


OPENALEX_API_URL = "https://api.openalex.org/works"
DEFAULT_KEYWORD = "IC semiconductor"
DEFAULT_PER_PAGE = 15
DEFAULT_TIMEOUT = 10

DEFAULT_RESULT_COUNT = 10
DEFAULT_RECENT_MONTHS = 1
DEFAULT_EXPANDED_MONTHS = 6
DEFAULT_SORT = "publication_date:desc"


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
}


class OpenAlexProvider:
    """OpenAlex Paper Search Provider."""

    def __init__(
        self,
        api_url=OPENALEX_API_URL,
        timeout=DEFAULT_TIMEOUT,
        result_count=DEFAULT_RESULT_COUNT,
        paper_repository=None,
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.result_count = result_count
        self.paper_repository = (
            paper_repository
            or PaperRepository()
        )

    def search(
        self,
        keyword=None,
        per_page=DEFAULT_PER_PAGE,
    ):
        """Search papers with date priority and stored-paper fallback."""

        keyword = keyword or DEFAULT_KEYWORD

        today = date.today()

        recent_from = (
            today - timedelta(
                days=30 * DEFAULT_RECENT_MONTHS
            )
        ).isoformat()

        expanded_from = (
            today - timedelta(
                days=30 * DEFAULT_EXPANDED_MONTHS
            )
        ).isoformat()

        today_str = today.isoformat()

        recent_results = self._search_openalex(
            keyword=keyword,
            per_page=per_page,
            from_date=recent_from,
            to_date=today_str,
        )

        recent_candidates = self._deduplicate_results(
            recent_results
        )

        if len(recent_candidates) >= self.result_count:
            results = self._select_results(
                recent_candidates
            )
            self._print_results(results)
            return results

        expanded_results = self._search_openalex(
            keyword=keyword,
            per_page=per_page,
            from_date=expanded_from,
            to_date=today_str,
        )

        expanded_candidates = self._deduplicate_results(
            expanded_results
        )

        recent_urls = {
            result.get("url")
            for result in recent_candidates
            if result.get("url")
        }

        expanded_candidates = [
            result
            for result in expanded_candidates
            if result.get("url") not in recent_urls
        ]

        candidates = (
            recent_candidates
            + expanded_candidates
        )

        results = self._select_results(
            candidates
        )

        self._print_results(results)

        return results

    def _search_openalex(
        self,
        keyword,
        per_page,
        from_date=None,
        to_date=None,
        sort=DEFAULT_SORT,
    ):
        """Search OpenAlex works."""

        params = {
            "search": keyword,
            "per-page": per_page,
            "sort": sort,
        }

        filters = []

        if from_date:
            filters.append(
                f"from_publication_date:{from_date}"
            )

        if to_date:
            filters.append(
                f"to_publication_date:{to_date}"
            )

        if filters:
            params["filter"] = ",".join(filters)

        response = requests.get(
            self.api_url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        return [
            self._build_result(
                work,
                keyword,
            )
            for work in data.get("results", [])
        ]

    @staticmethod
    def _deduplicate_results(results):
        """Remove invalid and duplicate URLs."""

        candidates = []
        seen_urls = set()

        for result in results:
            url = result.get("url")

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            candidates.append(result)

        return candidates

    def _select_results(
        self,
        candidates,
    ):
        """Select new papers first and randomly fill from stored papers."""

        existing_urls = {
            str(url).strip()
            for url in self.paper_repository.get_existing_urls()
            if url
        }

        new_candidates = [
            result
            for result in candidates
            if result.get("url") not in existing_urls
        ]

        selected = new_candidates[:self.result_count]

        if len(selected) >= self.result_count:
            return selected

        selected_urls = {
            result.get("url")
            for result in selected
            if result.get("url")
        }

        stored_candidates = [
            result
            for result in candidates
            if result.get("url") in existing_urls
            and result.get("url") not in selected_urls
        ]

        random.shuffle(stored_candidates)

        remaining = self.result_count - len(selected)

        selected.extend(
            stored_candidates[:remaining]
        )

        return selected

    @staticmethod
    def _print_results(results):
        """Print final selected Paper URLs."""

        print()
        print("=" * 60)
        print("OpenAlex Final Paper URLs")
        print("=" * 60)
        print(f"Results: {len(results)}")

        for index, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"{index}. {result.get('url')}"
            )

        print("=" * 60)

    def _resolve_landing_page_url(
        self,
        url,
    ):
        """Resolve URL to the actual Landing Page URL."""

        if not url:
            return None

        try:
            response = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
            )

            resolved_url = (
                response.url
                or url
            )

            if self._is_challenge_url(
                resolved_url
            ):
                return None

            return resolved_url

        except requests.RequestException:
            return None

    @staticmethod
    def _is_challenge_url(
        url,
    ):
        """Check whether URL is a bot-protection challenge URL."""

        try:
            hostname = (
                urlparse(url).hostname
                or ""
            ).lower()

            return (
                hostname == "validate.perfdrive.com"
                or hostname.endswith(
                    ".validate.perfdrive.com"
                )
            )

        except Exception:
            return False

    def _get_landing_page_url(
        self,
        work,
    ):
        """Find and resolve the actual Paper Landing Page URL."""

        primary_location = (
            work.get("primary_location")
            or {}
        )

        primary_url = (
            primary_location.get(
                "landing_page_url"
            )
            or work.get("doi")
        )

        if primary_url:
            resolved_url = (
                self._resolve_landing_page_url(
                    primary_url
                )
            )

            if resolved_url:
                return resolved_url

        locations = (
            work.get("locations")
            or []
        )

        for location in locations:
            if not isinstance(
                location,
                dict,
            ):
                continue

            landing_page_url = (
                location.get(
                    "landing_page_url"
                )
            )

            if not landing_page_url:
                continue

            resolved_url = (
                self._resolve_landing_page_url(
                    landing_page_url
                )
            )

            if resolved_url:
                return resolved_url

        return primary_url

    def _build_result(
        self,
        work,
        keyword,
    ):
        """Build a simplified Paper Search Result."""

        landing_page_url = (
            self._get_landing_page_url(
                work
            )
        )

        best_oa_location = (
            work.get("best_oa_location")
            or {}
        )

        pdf_url = best_oa_location.get(
            "pdf_url"
        )

        openalex_id = work.get(
            "id"
        )

        document_id = None

        if openalex_id:
            document_id = (
                "openalex:"
                + openalex_id.rstrip("/").split("/")[-1]
            )

        return {
            "document_id": document_id,
            "keyword": keyword,
            "title": work.get("title"),
            "url": landing_page_url,
            "pdf_url": pdf_url,
        }


__all__ = [
    "OpenAlexProvider",
]