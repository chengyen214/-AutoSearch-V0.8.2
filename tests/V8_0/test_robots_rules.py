"""
tests/V8_0/test_robots_rules.py

AutoSearch V6

Robots.txt Rules Test
"""

from urllib.robotparser import RobotFileParser


def create_parser(
    robots_content
):
    """
    建立 RobotFileParser。
    """

    parser = RobotFileParser()

    parser.parse(
        robots_content.splitlines()
    )

    return parser


def test_disallow_rule():

    robots_content = """
User-agent: *
Disallow: /private/
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/private/article"
    ) is False

    assert parser.can_fetch(
        "*",
        "https://example.com/news/article"
    ) is True


def test_allow_and_disallow_rule():

    robots_content = """
User-agent: *
Disallow: /private/
Allow: /private/public/
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/private/article"
    ) is False

    assert parser.can_fetch(
        "*",
        "https://example.com/private/public/article"
    ) is True


def test_user_agent_rule():

    robots_content = """
User-agent: Googlebot
Disallow: /google/

User-agent: *
Disallow: /private/
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "Googlebot",
        "https://example.com/google/article"
    ) is False

    assert parser.can_fetch(
        "Googlebot",
        "https://example.com/private/article"
    ) is True

    assert parser.can_fetch(
        "*",
        "https://example.com/google/article"
    ) is True

    assert parser.can_fetch(
        "*",
        "https://example.com/private/article"
    ) is False


def test_user_agent_case_insensitive():

    robots_content = """
User-agent: Googlebot
Disallow: /private/
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "googlebot",
        "https://example.com/private/article"
    ) is False


def test_longer_allow_rule():

    robots_content = """
User-agent: *
Disallow: /private/
Allow: /private/public/
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/private/public/article"
    ) is True

    assert parser.can_fetch(
        "*",
        "https://example.com/private/other/article"
    ) is False


def test_wildcard_rule():

    robots_content = """
User-agent: *
Disallow: /*.pdf
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/report.pdf"
    ) is False

    assert parser.can_fetch(
        "*",
        "https://example.com/report.html"
    ) is True


def test_end_anchor_rule():

    robots_content = """
User-agent: *
Disallow: /private$
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/private"
    ) is False

    assert parser.can_fetch(
        "*",
        "https://example.com/private/article"
    ) is True


def test_empty_disallow():

    robots_content = """
User-agent: *
Disallow:
"""

    parser = create_parser(
        robots_content
    )

    assert parser.can_fetch(
        "*",
        "https://example.com/private/article"
    ) is True

    assert parser.can_fetch(
        "*",
        "https://example.com/news/article"
    ) is True