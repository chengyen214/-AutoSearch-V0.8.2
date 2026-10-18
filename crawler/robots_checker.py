"""
crawler/robots_checker.py

AutoSearch V6

Robots.txt Checker

用途：
    提供 robots.txt 檢查單一入口。

負責：
    - 建立 robots.txt URL
    - 下載 robots.txt
    - 呼叫 RobotsCacheRepository 查詢快取
    - 快取不存在時下載並保存
    - 辨識適用的 User-Agent Group
    - 判斷指定 URL 是否允許爬取

不負責：
    - SQL 實作
    - 實際網頁下載
    - CrawlService
"""

from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
)

ROBOTS_PATH = "/robots.txt"
TIMEOUT = 10


def get_base_url(url):
    """
    取得 URL 所屬的 Origin Base URL。

    保留 scheme、hostname 與明確指定的 port，
    不包含路徑、查詢參數、片段或帳號資訊。
    """

    parsed = urlsplit(url)

    if (
        parsed.scheme.lower() not in ("http", "https")
        or not parsed.hostname
    ):
        raise ValueError("Invalid URL")

    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid URL") from exc

    if ":" in hostname:
        hostname = f"[{hostname}]"

    authority = hostname

    if port is not None:
        authority = f"{authority}:{port}"

    return f"{parsed.scheme.lower()}://{authority}"


def get_robots_url(url):
    """建立 URL 所屬 Origin 的 robots.txt URL。"""

    return f"{get_base_url(url)}{ROBOTS_PATH}"


def get_robots_content(
    url,
    user_agent=DEFAULT_USER_AGENT,
    timeout=TIMEOUT,
):
    """
    下載 URL 所屬 Origin 的 robots.txt。

    urllib 會自動處理一般 HTTP 重新導向。
    HTTP 狀態錯誤由呼叫端處理。
    """

    robots_url = get_robots_url(url)

    request = Request(
        robots_url,
        headers={
            "User-Agent": user_agent,
        },
    )

    with urlopen(request, timeout=timeout) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def get_matching_rule_group(
    robots_content,
    user_agent=DEFAULT_USER_AGENT,
):
    """
    找出適用的 User-Agent Group。

    若多個 Group 具有相同的最高匹配程度，
    合併這些 Group 的 User-Agent tokens。

    沒有專用 Group 時使用 *。
    """

    groups = []
    current_agents = []
    current_has_rules = False

    for raw_line in robots_content.splitlines():
        line = raw_line.split("#", 1)[0].strip()

        if not line or ":" not in line:
            continue

        field, value = line.split(":", 1)
        field = field.strip().lower()
        value = value.strip()

        if field == "user-agent":
            if current_agents and current_has_rules:
                groups.append(current_agents)
                current_agents = []
                current_has_rules = False

            if value:
                current_agents.append(value)

        elif field in ("allow", "disallow"):
            if current_agents:
                current_has_rules = True

    if current_agents:
        groups.append(current_agents)

    parsed_agent = urlsplit(
        "https://example.invalid/"
    )

    del parsed_agent

    agent = user_agent.lower()
    best_length = 0
    matched_groups = []
    wildcard_groups = []

    for group in groups:
        group_match_length = 0
        has_wildcard = False

        for token in group:
            token_lower = token.lower()

            if token_lower == "*":
                has_wildcard = True
            elif token_lower and token_lower in agent:
                group_match_length = max(
                    group_match_length,
                    len(token_lower),
                )

        if group_match_length > best_length:
            best_length = group_match_length
            matched_groups = [group]
        elif (
            group_match_length > 0
            and group_match_length == best_length
        ):
            matched_groups.append(group)

        if has_wildcard:
            wildcard_groups.append(group)

    if matched_groups:
        selected_groups = matched_groups
    else:
        selected_groups = wildcard_groups

    if not selected_groups:
        return None

    tokens = []

    for group in selected_groups:
        for token in group:
            if token not in tokens:
                tokens.append(token)

    return ", ".join(tokens)


def check_robots(
    url,
    user_agent=DEFAULT_USER_AGENT,
    timeout=TIMEOUT,
):
    """
    robots.txt 單一入口。

    Pipeline：
        URL
         ↓
        Base URL
         ↓
        SQL Cache Lookup
         ├── Hit  → 讀取 robots_content
         └── Miss → 下載 robots.txt → 儲存 SQL
         ↓
        Parse robots.txt
         ↓
        判斷目前 URL
         ↓
        回傳 bool

    注意：
        回傳值只代表目前 URL 的判斷結果。
    """

    from database.robots_cache_repository import (
        RobotsCacheRepository,
    )

    try:
        base_url = get_base_url(url)
        robots_url = get_robots_url(url)
    except (TypeError, ValueError):
        return False

    repository = RobotsCacheRepository()

    try:
        cached = repository.get_by_base_url(base_url)
    except Exception:
        return False

    if cached is not None:
        robots_content = cached.get("robots_content")

        if robots_content is None:
            return False

        robots_url = cached.get("robots_url") or robots_url

    else:
        try:
            robots_content = get_robots_content(
                url,
                user_agent=user_agent,
                timeout=timeout,
            )

        except HTTPError as exc:
            if 400 <= exc.code < 500:
                # RFC 9309：4xx 表示 robots.txt 不可用。
                # RFC 允許爬蟲存取資源。
                robots_content = ""
            else:
                # 5xx：採取保守策略，不允許爬取。
                return False

        except Exception:
            # 網路錯誤：採取保守策略。
            return False

        try:
            rule_group = (
                get_matching_rule_group(
                    robots_content,
                    user_agent,
                )
                or "*"
            )

            repository.insert(
                base_url=base_url,
                robots_url=robots_url,
                robots_content=robots_content,
                rule_group=rule_group,
                checked_at=datetime.now(),
            )

        except Exception:
            return False

    try:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots_content.splitlines())

        return bool(
            parser.can_fetch(
                user_agent,
                url,
            )
        )

    except Exception:
        return False


__all__ = [
    "DEFAULT_USER_AGENT",
    "ROBOTS_PATH",
    "TIMEOUT",
    "get_base_url",
    "get_robots_url",
    "get_robots_content",
    "get_matching_rule_group",
    "check_robots",
]