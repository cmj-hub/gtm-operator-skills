#!/usr/bin/env python3
"""Read public pages for a domain and print three GTM gaps.

Stdlib only. No paid APIs. Core run needs no account.

  python3 scripts/check.py --domain example.com
  python3 scripts/check.py --html-file examples/thin-home.html --page-url https://thin.example/
  python3 scripts/check.py --html-file examples/thin-home.html --page-url https://thin.example/ --json

Exit codes: 0 printed, 2 bad input or fetch failed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


MAX_BYTES = 400_000
TIMEOUT_S = 12
USER_AGENT = "jmc-gtm-leak-check/0.2 (+https://github.com/cmj-hub/claude-gtm-leak-check)"

STACK_NEEDLES = (
    ("Google Tag Manager", "googletagmanager.com/gtm.js"),
    ("Google Analytics", "google-analytics.com"),
    ("HubSpot", "js.hs-scripts.com"),
    ("HubSpot", "js.hs-analytics.net"),
    ("Segment", "cdn.segment.com"),
    ("Intercom", "widget.intercom.io"),
    ("Plausible", "plausible.io/js"),
    ("Fathom", "cdn.usefathom.com"),
    ("Hotjar", "static.hotjar.com"),
    ("Marketo", "munchkin.marketo.net"),
    ("Pardot", "pardot.com"),
    ("Drift", "js.driftt.com"),
    ("Clay", "clay.com"),
)

AI_BOTS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended")
CTA_WORDS = ("demo", "book", "contact", "start", "get started", "talk", "trial")
WHO_NEEDLES = (
    "for teams",
    "for companies",
    "for founders",
    "for operators",
    "b2b",
    "who we help",
    "customers",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self._in_title = False
        self._in_script = False
        self.meta: dict[str, str] = {}
        self.scripts: list[str] = []
        self.json_ld: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.text_parts: list[str] = []
        self._current_href = ""
        self._in_json_ld = False
        self._json_ld_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (ad.get("name") or ad.get("property") or "").lower()
            if name and ad.get("content"):
                self.meta[name] = ad["content"]
        elif tag == "script":
            src = ad.get("src") or ""
            if src:
                self.scripts.append(src)
            if (ad.get("type") or "").lower() == "application/ld+json":
                self._in_json_ld = True
                self._json_ld_buf = []
            else:
                self._in_script = True
        elif tag == "a":
            self._current_href = ad.get("href") or ""
        elif tag in {"style", "noscript"}:
            self._in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._in_json_ld:
                self.json_ld.append("".join(self._json_ld_buf))
                self._in_json_ld = False
                self._json_ld_buf = []
            self._in_script = False
        elif tag in {"style", "noscript"}:
            self._in_script = False
        elif tag == "a":
            self._current_href = ""

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_buf.append(data)
            return
        if self._in_script:
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        text = " ".join(data.split())
        if text:
            self.text_parts.append(text)
            if self._current_href:
                self.links.append((text, self._current_href))


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_bytes(path: str) -> str:
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        fail_input(f"file not found: {path}")
    raw = p.read_bytes()
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
    return raw.decode("utf-8", errors="replace")


def fetch(url: str, *, required: bool = True) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=TIMEOUT_S) as resp:
            status = getattr(resp, "status", 200) or 200
            raw = resp.read(MAX_BYTES + 1)
    except HTTPError as err:
        body = err.read(MAX_BYTES) if err.fp else b""
        return err.code, body.decode("utf-8", errors="replace")
    except (URLError, TimeoutError, ValueError, OSError) as err:
        if required:
            fail_input(f"fetch failed: {url} ({err})")
        return 0, ""
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
    return status, raw.decode("utf-8", errors="replace")


def parse_html(html: str) -> PageParser:
    parser = PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    return parser


def robots_blocks_bot(robots: str, bot: str) -> bool:
    current: list[str] = []
    blocked = False
    for line in robots.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        if stripped.lower().startswith("user-agent:"):
            current = [u.strip() for u in stripped.split(":", 1)[1].split(",")]
            continue
        if stripped.lower().startswith("disallow:"):
            path = stripped.split(":", 1)[1].strip()
            if path == "/" and any(u == "*" or u.lower() == bot.lower() for u in current):
                blocked = True
    return blocked


def detect_stack(html: str, scripts: Iterable[str]) -> list[str]:
    blob = html.lower() + " " + " ".join(s.lower() for s in scripts)
    found: list[str] = []
    for name, needle in STACK_NEEDLES:
        if needle.lower() in blob and name not in found:
            found.append(name)
    return found


def analyze(
    *,
    page_url: str,
    html: str,
    robots_text: str | None,
    robots_url: str | None,
    llms_status: int | None,
    llms_url: str | None,
    pricing_html: str | None = None,
    pricing_url: str | None = None,
    pricing_status: int | None = None,
    careers_html: str | None = None,
    careers_url: str | None = None,
) -> dict:
    parsed = parse_html(html)
    title = " ".join(" ".join(parsed.title_parts).split())
    description = parsed.meta.get("description") or parsed.meta.get("og:description") or ""
    robots_meta = (parsed.meta.get("robots") or "").lower()
    text = " ".join(parsed.text_parts)
    sources = [page_url]
    if robots_url:
        sources.append(robots_url)
    if llms_url:
        sources.append(llms_url)
    if pricing_url:
        sources.append(pricing_url)
    if careers_url:
        sources.append(careers_url)

    findings: list[dict] = []

    def add(area: str, name: str, saw: str, source: str, why: str, severity: int) -> None:
        findings.append(
            {
                "area": area,
                "name": name,
                "what_we_saw": saw,
                "source": source,
                "why": why,
                "severity": severity,
            }
        )

    if not title:
        add(
            "site",
            "Missing title",
            "The homepage has no title tag.",
            page_url,
            "Search and answer engines have nothing to cite.",
            90,
        )
    elif len(title) < 12:
        add(
            "site",
            "Thin title",
            f"Title is {len(title)} characters: {title!r}.",
            page_url,
            "A stranger cannot tell what you sell from the tab.",
            70,
        )

    if not description.strip():
        add(
            "site",
            "Missing description",
            "No meta description on the homepage.",
            page_url,
            "Snippets and answer engines fall back to a random sentence.",
            60,
        )

    if len(text) < 200:
        add(
            "site",
            "Thin homepage",
            f"Visible text is {len(text)} characters.",
            page_url,
            "There is not enough public copy for a buyer or an agent to know the offer.",
            85,
        )

    cta = False
    blob = (text + " " + " ".join(h for _, h in parsed.links)).lower()
    for word in CTA_WORDS:
        if word in blob:
            cta = True
            break
    if not cta:
        add(
            "site",
            "No public next step",
            "No demo, contact, or start link in the visible copy.",
            page_url,
            "A stranger who believes you still cannot act.",
            75,
        )

    if "noindex" in robots_meta:
        add(
            "search",
            "Homepage is noindex",
            f"robots meta is {parsed.meta.get('robots')!r}.",
            page_url,
            "Search and answer engines are told not to cite this page.",
            95,
        )

    if not parsed.json_ld:
        add(
            "search",
            "No JSON-LD",
            "No application/ld+json script on the homepage.",
            page_url,
            "Answer engines prefer a typed Organization or SoftwareApplication block.",
            45,
        )

    if llms_status is not None and llms_status >= 400:
        add(
            "search",
            "No llms.txt",
            f"{llms_url or '/llms.txt'} returned {llms_status}.",
            llms_url or page_url,
            "Answer engines have no machine-readable brief for this domain.",
            50,
        )

    if robots_text:
        blocked = [bot for bot in AI_BOTS if robots_blocks_bot(robots_text, bot)]
        if blocked:
            add(
                "search",
                "AI crawlers blocked",
                "robots.txt disallows: " + ", ".join(blocked) + ".",
                robots_url or page_url,
                "Answer engines that honour robots.txt will never read the site.",
                80,
            )

    home_lower = text.lower()
    names_buyer = any(n in home_lower for n in WHO_NEEDLES)
    if careers_html:
        careers_text = " ".join(parse_html(careers_html).text_parts)
        if len(careers_text) >= 80 and not names_buyer:
            add(
                "site",
                "Homepage never names who they sell to",
                "A careers page exists, but the homepage never says who the product is for.",
                careers_url or page_url,
                "A stranger cannot tell if they are the buyer.",
                72,
            )

    if pricing_url is not None:
        pricing_text = " ".join(parse_html(pricing_html or "").text_parts)
        missing = pricing_status is not None and pricing_status >= 400
        thin = len(pricing_text) < 80
        if missing or thin:
            add(
                "site",
                "Thin or missing pricing",
                (
                    f"{pricing_url} returned {pricing_status}."
                    if missing
                    else f"Pricing page text is {len(pricing_text)} characters."
                ),
                pricing_url,
                "A buyer who is ready still cannot see what it costs.",
                65,
            )

    stack = detect_stack(html, parsed.scripts)
    if not stack:
        add(
            "stack",
            "No public analytics or CRM scripts",
            "No GTM, HubSpot, Segment, Intercom, or similar script on the homepage.",
            page_url,
            "Either the stack is server-side, or there is no measurement. Confirm with The GTM Directory MCP if it is already connected.",
            40,
        )

    findings.sort(key=lambda f: -f["severity"])
    gaps = findings[:3]

    return {
        "domain": urlparse(page_url).hostname or page_url,
        "gaps": [
            {
                "name": g["name"],
                "area": g["area"],
                "what_we_saw": g["what_we_saw"],
                "source": g["source"],
                "why": g["why"],
            }
            for g in gaps[:3]
        ],
        "stack": stack,
        "sources": sources,
        "title": title,
    }


def render_text(report: dict) -> str:
    lines = [
        f"GTM leak check: {report['domain']}",
        "",
    ]
    gaps = report["gaps"]
    if not gaps:
        lines.append("No public-signal leaks on the pages we read.")
        lines.append("")
    else:
        total = len(gaps)
        for i, gap in enumerate(gaps, 1):
            lines.append(f"Gap {i} of {total}: {gap['name']}")
            lines.append(f"  What we saw: {gap['what_we_saw']}")
            lines.append(f"  Source: {gap['source']}")
            lines.append(f"  Why it matters: {gap['why']}")
            lines.append("")
    stack = report.get("stack") or []
    if stack:
        lines.append("Tools seen: " + ", ".join(stack))
        lines.append("")
    lines.append("Sources read: " + ", ".join(report["sources"]))
    lines.append("")
    lines.append(
        "The Friday Signal: free emails on building GTM systems that compound. No pitch in it. One click unsubscribes. "
        "https://jaymountconsulting.com/newsletter/signal"
    )
    lines.append(
        "Want a written audit of the system you run, not just public signals? "
        "https://jaymountconsulting.com/growth-audit"
    )
    return "\n".join(lines) + "\n"


def origin_from(page_url: str) -> str:
    parts = urlparse(page_url)
    if not parts.scheme or not parts.netloc:
        fail_input("page URL must include a scheme and host")
    return f"{parts.scheme}://{parts.netloc}"


def pick_linked_url(origin: str, html: str, words: tuple[str, ...]) -> str | None:
    parsed = parse_html(html)
    for _label, href in parsed.links:
        low = href.lower()
        if any(w in low for w in words):
            return urljoin(origin + "/", href)
    return None


def fetch_domain(domain: str) -> dict:
    host = domain.strip().lower()
    host = re.sub(r"^https?://", "", host)
    host = host.split("/")[0]
    if not host or "." not in host:
        fail_input("need a domain like example.com")
    page_url = f"https://{host}/"
    status, html = fetch(page_url)
    if status >= 400:
        alt = f"https://www.{host}/" if not host.startswith("www.") else f"https://{host[4:]}/"
        status, html = fetch(alt)
        page_url = alt
    if status >= 400:
        fail_input(f"homepage returned {status} for {page_url}")
    origin = origin_from(page_url)
    robots_url = urljoin(origin, "/robots.txt")
    llms_url = urljoin(origin, "/llms.txt")
    robots_status, robots_text = fetch(robots_url, required=False)
    llms_status, _llms = fetch(llms_url, required=False)

    pricing_url = pick_linked_url(origin, html, ("pricing", "plans")) or urljoin(
        origin, "/pricing"
    )
    careers_url = pick_linked_url(origin, html, ("career", "jobs", "hiring")) or urljoin(
        origin, "/careers"
    )
    pricing_status, pricing_html = fetch(pricing_url, required=False)
    careers_status, careers_html = fetch(careers_url, required=False)
    if careers_status >= 400 or not careers_html:
        jobs_url = urljoin(origin, "/jobs")
        jobs_status, jobs_html = fetch(jobs_url, required=False)
        if jobs_status < 400 and jobs_html:
            careers_url, careers_status, careers_html = jobs_url, jobs_status, jobs_html

    return {
        "page_url": page_url,
        "html": html,
        "robots_text": robots_text if robots_status and robots_status < 400 else None,
        "robots_url": robots_url,
        "llms_status": llms_status,
        "llms_url": llms_url,
        "pricing_html": pricing_html if pricing_status and pricing_status < 400 else None,
        "pricing_url": pricing_url,
        "pricing_status": pricing_status,
        "careers_html": careers_html if careers_status and careers_status < 400 else None,
        "careers_url": careers_url if careers_status and careers_status < 400 else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print three GTM gaps from public pages.")
    parser.add_argument("--domain", help="example.com")
    parser.add_argument("--html-file", help="offline homepage HTML")
    parser.add_argument("--page-url", help="URL to cite as the homepage source")
    parser.add_argument("--robots-file", help="offline robots.txt")
    parser.add_argument("--llms-status", type=int, help="offline /llms.txt HTTP status")
    parser.add_argument("--pricing-file", help="offline pricing HTML")
    parser.add_argument("--pricing-url", help="URL to cite as the pricing page")
    parser.add_argument("--pricing-status", type=int, help="offline pricing HTTP status")
    parser.add_argument("--careers-file", help="offline careers HTML")
    parser.add_argument("--careers-url", help="URL to cite as the careers page")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    extra = {}
    if args.html_file:
        page_url = args.page_url or "https://example.com/"
        html = read_bytes(args.html_file)
        robots_text = read_bytes(args.robots_file) if args.robots_file else None
        origin = origin_from(page_url)
        robots_url = urljoin(origin, "/robots.txt") if args.robots_file else None
        llms_url = urljoin(origin, "/llms.txt") if args.llms_status is not None else None
        if args.pricing_file or args.pricing_status is not None:
            extra["pricing_html"] = read_bytes(args.pricing_file) if args.pricing_file else ""
            extra["pricing_url"] = args.pricing_url or urljoin(origin, "/pricing")
            extra["pricing_status"] = args.pricing_status
        if args.careers_file:
            extra["careers_html"] = read_bytes(args.careers_file)
            extra["careers_url"] = args.careers_url or urljoin(origin, "/careers")
        report = analyze(
            page_url=page_url,
            html=html,
            robots_text=robots_text,
            robots_url=robots_url,
            llms_status=args.llms_status,
            llms_url=llms_url,
            **extra,
        )
    elif args.domain:
        fetched = fetch_domain(args.domain)
        report = analyze(
            page_url=fetched["page_url"],
            html=fetched["html"],
            robots_text=fetched["robots_text"],
            robots_url=fetched["robots_url"],
            llms_status=fetched["llms_status"],
            llms_url=fetched["llms_url"],
            pricing_html=fetched.get("pricing_html"),
            pricing_url=fetched.get("pricing_url"),
            pricing_status=fetched.get("pricing_status"),
            careers_html=fetched.get("careers_html"),
            careers_url=fetched.get("careers_url"),
        )
    else:
        fail_input("pass --domain example.com or --html-file")

    if args.as_json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
