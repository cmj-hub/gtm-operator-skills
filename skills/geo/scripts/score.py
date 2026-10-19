#!/usr/bin/env python3
"""Score a findability draft.

Prints a channel decision, a buyer question, a citation record, an indexability
pass, one brief, and one kill date. Refuses a health-score dump, an llms.txt
project, or a 40-article calendar.

Each of the six axes is checked, not just filled in. The citation record, the
indexability pass, and the brief are structured records: the scorer checks the
runs, the evidence files, the crawler results, and the claim, not the wording
of a sentence. A failing draft prints one line per problem, named by axis, and
exits 1.

A pass means the record is complete and consistent. It does not mean the page
is indexed, cited, or effective; the review on the kill date measures that.

Stdlib only. No network. Evidence paths are checked for existence (never read)
relative to the draft's folder, or the working directory with --stdin.

  python3 scripts/score.py --file gtm/findability.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/findability.json --json

Every failing line reads `- <what is wrong> -> <what to change>`, and the last
line names the next step.

Exit codes: 0 passes, 1 refused or failing, 2 bad input.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


MAX_INPUT_BYTES = 2_000_000

FIELDS = (
    ("channel_decision", "channel decision"),
    ("buyer_question", "buyer question"),
    ("citation_record", "citation record"),
    ("indexability_pass", "indexability pass"),
    ("brief", "brief"),
    ("kill_date", "kill date"),
)
LABELS = {**dict(FIELDS), "review": "review"}

# Fields written as text; the rest are JSON objects.
TEXT_FIELDS = ("channel_decision", "buyer_question", "kill_date")

# The /geo:geo mode that writes each field.
MODES = {
    "channel_decision": "channel-decision",
    "buyer_question": "buyer-question",
    "citation_record": "citation-record",
    "indexability_pass": "indexability",
    "brief": "brief",
    "kill_date": "brief",
    "review": "review",
}

NEXT_PASS = "/landing-page:page"
NEXT_FAIL = "fix the lines above and run this again."
NEXT_REVIEW = {
    "expand": "/geo:geo buyer-question (the next question, in a new experiment file)",
    "revise": "/geo:geo brief (rewrite the first paragraph and the claim), then a new kill date",
    "stop": "/geo:geo buyer-question (a different question, in a new experiment file)",
}
EXAMPLE = "example:\n  python3 scripts/score.py --file examples/findability-good.json"

REFUSAL_FIXES = {
    "a health-score dump": "pick one buyer question and score one page for it",
    "an llms.txt project": "check fetchability with /geo:geo indexability instead",
    "a 40-article calendar": "write one brief per buyer question; run other questions as separate experiments",
}

# Refusals are read from the plan fields only. The citation record and the
# indexability pass are observations, and may name llms.txt or a score they saw.
HEALTH_RE = re.compile(r"health[-\s]?score", re.IGNORECASE)
LLMS_RE = re.compile(r"llms(?:-full)?\.txt", re.IGNORECASE)
CALENDAR_RE = re.compile(
    r"\b\d{2,}[-\s]?(?:article|post|page|blog|piece)s?\b"
    r"|content[-\s]calendar|editorial[-\s]calendar",
    re.IGNORECASE,
)
# A refusal term inside a clause that rejects it ("no content calendar", "one
# page, not a 40-article calendar") is not a plan to build it.
CLAUSE_SPLIT_RE = re.compile(r"[.:](?=\s|$)|[;!?,\n]|\bbut\b", re.IGNORECASE)
NEGATION_RE = re.compile(
    r"\b(?:no|not|never|without|instead of|rather than|skip|skipping|avoid|avoids|avoiding"
    r"|refuse|refuses|refused|reject|rejects|rejected|don't|do not|won't|will not|isn't|is not)\b",
    re.IGNORECASE,
)

PLACEHOLDER_RE = re.compile(
    r"^(?:tbd|tbc|todo|n/?a|none|none observed|unknown|unchecked|pending|-+|\?+|\.+)\.?$",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[T ][\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?$")
LIST_SEPARATORS_RE = re.compile(r"[|;]|,.*,.*,")
# A specific: a number, a quoted name, or a capitalized name after the first word.
SPECIFIC_RE = re.compile(r"\d|[\"“][^\"”]+[\"”]|(?<=\s)[A-Z]\w*")

METHODS = ("pasted answer", "manual run", "api run", "tool export")
CLEAN_SESSION_METHODS = ("pasted answer", "manual run")
BRAND_STATUSES = ("named", "cited", "both", "neither")
RUNS_PER_ENGINE = 3
BASELINE_WINDOW_DAYS = 7

# Crawlers whose block removes the page from search or AI answers. Training
# crawlers (GPTBot, ClaudeBot, Google-Extended, ...) may be blocked by policy.
REQUIRED_CRAWLERS = ("Googlebot", "Bingbot")
ANSWER_CRAWLERS = (
    "Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User",
    "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
)
ROBOTS_VALUES = ("allowed", "blocked")

REVIEW_DECISIONS = ("expand", "revise", "stop")
REVIEW_METRICS = ("indexed", "impressions", "qualified_visits", "conversions")

QUESTION_MIN_WORDS = 5
QUESTION_MAX_WORDS = 30
DECISION_MIN_WORDS = 8
BRIEF_MIN_WORDS = 8
BRIEF_MAX_WORDS = 150
CLAIM_MIN_WORDS = 5
REASON_MIN_WORDS = 8
MAX_REDIRECTS = 1
KILL_MIN_DAYS = 14
KILL_MAX_DAYS = 180


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_text(path: Path) -> str:
    try:
        if not path.exists():
            fail_input("file not found")
        if not path.is_file():
            fail_input("not a file")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input("file is too large")
        raw = path.read_bytes()
    except SystemExit:
        raise
    except OSError:
        fail_input("cannot read file")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input("file is not UTF-8 text")


def load_payload(args: argparse.Namespace) -> object:
    if args.file and args.stdin:
        fail_input("pass --file or --stdin, not both")
    if args.stdin:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            fail_input("input is too large")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            fail_input("input is not UTF-8 text")
    elif args.file:
        text = read_text(Path(args.file))
    else:
        fail_input("pass --file or --stdin")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail_input("invalid JSON")


def nonempty_text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def is_blank(value: object) -> bool:
    """True for an unfilled template: only empty strings, nulls, false, and empty containers."""
    if isinstance(value, dict):
        return all(is_blank(item) for item in value.values())
    if isinstance(value, list):
        return all(is_blank(item) for item in value)
    if isinstance(value, str):
        return not value.strip()
    return value is None or value is False


def normalize(value: object) -> object:
    """Strip text fields; keep filled objects; anything blank becomes ''."""
    if is_blank(value):
        return ""
    if isinstance(value, str):
        return value.strip()
    return value


def word_count(text: str) -> int:
    return len(text.split())


def same_words(a: str, b: str) -> bool:
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def parse_date(text: object) -> dt.date | None:
    if not isinstance(text, str):
        return None
    match = DATE_RE.match(text.strip())
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def is_url(text: object) -> bool:
    if not isinstance(text, str):
        return False
    parsed = urlparse(text.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def text_list(value: object) -> list | None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.strip() for item in value if item.strip()]
    return None


def host_matches(url: str, domain: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    domain = domain.lower().strip().lstrip(".")
    return host == domain or host.endswith("." + domain)


# --- Refusals ---------------------------------------------------------------

def affirmed(pattern: re.Pattern, text: str) -> bool:
    """True when the pattern appears in a clause that does not reject it."""
    for clause in CLAUSE_SPLIT_RE.split(text):
        for match in pattern.finditer(clause):
            if not NEGATION_RE.search(clause[: match.start()]):
                return True
    return False


def plan_text(values: dict) -> str:
    parts = [values["channel_decision"], values["buyer_question"]]
    brief = values["brief"]
    if isinstance(brief, dict):
        for key in ("page", "summary", "unique_claim"):
            if isinstance(brief.get(key), str):
                parts.append(brief[key])
        parts.extend(text_list(brief.get("follow_up_questions")) or [])
    elif isinstance(brief, str):
        parts.append(brief)
    return "\n".join(part for part in parts if isinstance(part, str))


def refusal_for(values: dict) -> str:
    blob = plan_text(values)
    if affirmed(HEALTH_RE, blob):
        return "a health-score dump"
    if affirmed(LLMS_RE, blob):
        return "an llms.txt project"
    if affirmed(CALENDAR_RE, blob):
        return "a 40-article calendar"
    return ""


# --- Text axes --------------------------------------------------------------

def check_channel_decision(text: str) -> list:
    if word_count(text) < DECISION_MIN_WORDS:
        return [("too short to be a decision", "say why search is or is not a channel for this offer, and what comes first")]
    return []


def check_buyer_question(text: str) -> list:
    problems = []
    if not text.endswith("?"):
        problems.append(("not written as a question", "write it as a buyer would type it, ending in ?"))
    if text.count("?") > 1:
        problems.append(("more than one question", "keep one question; give the other its own experiment"))
    if LIST_SEPARATORS_RE.search(text):
        problems.append(("reads like a keyword list", "write the sentence a buyer would type"))
    words = word_count(text)
    if words < QUESTION_MIN_WORDS:
        problems.append(("too short to be the buyer's own words", "quote the buyer's full question"))
    if words > QUESTION_MAX_WORDS:
        problems.append(("too long for one question", f"cut it to {QUESTION_MAX_WORDS} words or fewer"))
    if re.match(r"^what should we (?:publish|write|post)\b", text, re.IGNORECASE):
        problems.append(("that is our question, not the buyer's", "use a question a buyer asked on a call, a ticket, or a thread"))
    return problems


# --- Citation record --------------------------------------------------------

def check_evidence(evidence: object, base: Path) -> str:
    """Return a problem, or '' when the evidence is a URL or an existing path."""
    text = nonempty_text(evidence)
    if not text or PLACEHOLDER_RE.match(text):
        return "no evidence"
    if is_url(text):
        return ""
    path = Path(text)
    if not path.is_absolute():
        path = base / path
    try:
        if path.exists():
            return ""
    except OSError:
        pass
    return "evidence file not found"


def check_observations(observations: object, question: str, brand: str, brand_domain: str,
                       base: Path, today: dt.date, prefix: str = "") -> tuple:
    """Validate a list of runs. Return (problems, dates, groups)."""
    if not isinstance(observations, list) or not observations:
        return [(f"{prefix}no observations", "record each run as one entry in observations[]")], [], {}
    problems = []
    dates = []
    groups: dict = {}
    seen = set()

    def add(index: int, problem: str, fix: str) -> None:
        key = (problem, fix)
        if key not in seen:
            seen.add(key)
            problems.append((f"{prefix}run {index}: {problem}", fix))

    for index, obs in enumerate(observations, 1):
        if not isinstance(obs, dict):
            add(index, "not an object", "write each run as an object with engine, method, query, observed_at, run, brands_named, cited_urls, brand_status, evidence")
            continue
        engine = nonempty_text(obs.get("engine"))
        if not engine:
            add(index, "no engine", "name the engine, as 'ChatGPT' or 'Perplexity'")
        method = nonempty_text(obs.get("method")).lower()
        if method not in METHODS:
            add(index, "unknown method", "use one of: " + ", ".join(METHODS))
        query = nonempty_text(obs.get("query"))
        if not query:
            add(index, "no query", "record the exact text that was typed")
        elif question and not same_words(query, question):
            add(index, "query is not the buyer question word for word", "paste the buyer question verbatim; add no brand, place, or 'best'")
        if brand and query and re.search(r"\b" + re.escape(brand) + r"\b", query, re.IGNORECASE):
            add(index, "query names the brand", "run the question without the brand name")
        observed = parse_date(obs.get("observed_at"))
        if observed is None:
            add(index, "no observed_at date", "add when it ran, as YYYY-MM-DD or an ISO timestamp")
        elif observed > today:
            add(index, "observed_at is in the future", "record the date the run happened")
        else:
            dates.append(observed)
        run = obs.get("run")
        if not is_int(run) or run < 1:
            add(index, "no run number", "number the runs per engine: 1, 2, 3")
        if method in CLEAN_SESSION_METHODS and obs.get("clean_session") is not True:
            add(index, "not a clean session", "run it logged out or in a fresh profile, then set clean_session: true")
        named = text_list(obs.get("brands_named"))
        if named is None:
            add(index, "brands_named is not a list", "list the brands named in the answer text ([] if none)")
        cited = text_list(obs.get("cited_urls"))
        if cited is None:
            add(index, "cited_urls is not a list", "list the URLs the answer linked or cited ([] if none)")
        elif any(not is_url(url) for url in cited):
            add(index, "a cited URL is not a full URL", "record cited sources as https:// URLs")
        status = nonempty_text(obs.get("brand_status")).lower()
        if status not in BRAND_STATUSES:
            add(index, "no brand_status", "set brand_status to one of: " + ", ".join(BRAND_STATUSES))
        else:
            if brand and named is not None:
                in_text = any(same_words(name, brand) for name in named)
                if in_text != (status in ("named", "both")):
                    add(index, "brand_status disagrees with brands_named", "set brand_status from what the answer shows")
            if brand_domain and cited is not None:
                linked = any(host_matches(url, brand_domain) for url in cited)
                if linked != (status in ("cited", "both")):
                    add(index, "brand_status disagrees with cited_urls", "set brand_status from what the answer cites")
        evidence_problem = check_evidence(obs.get("evidence"), base)
        if evidence_problem:
            add(index, evidence_problem, "save the raw answer or a screenshot and put its path or URL in evidence")
        if engine and method in METHODS and is_int(run):
            groups.setdefault((engine, method), set()).add(run)

    for (engine, method), runs in sorted(groups.items()):
        needed = 1 if method == "tool export" else RUNS_PER_ENGINE
        if len(runs) < needed:
            problems.append((
                f"{prefix}{engine} ({method}) has {len(runs)} run{'s' if len(runs) != 1 else ''}",
                f"run it {RUNS_PER_ENGINE} times in clean sessions; answers vary between runs",
            ))
    if dates and (max(dates) - min(dates)).days > BASELINE_WINDOW_DAYS:
        problems.append((
            f"{prefix}runs span more than {BASELINE_WINDOW_DAYS} days",
            "a record is one sitting; run the set again within one week",
        ))
    return problems, dates, groups


def check_citation_record(record: object, question: str, base: Path, today: dt.date) -> list:
    if not isinstance(record, dict):
        return [("free text is not a record", "run /geo:geo citation-record; it writes observations[] (see examples/findability-good.json)")]
    brand = nonempty_text(record.get("brand"))
    brand_domain = nonempty_text(record.get("brand_domain"))
    problems = []
    if not brand:
        problems.append(("no brand", "name the brand being looked for, so each run can say whether it was named"))
    problems.extend(check_observations(record.get("observations"), question, brand, brand_domain, base, today)[0])
    return problems


def baseline_date(record: object) -> dt.date | None:
    if not isinstance(record, dict) or not isinstance(record.get("observations"), list):
        return None
    dates = [parse_date(obs.get("observed_at")) for obs in record["observations"] if isinstance(obs, dict)]
    dates = [d for d in dates if d]
    return min(dates) if dates else None


# --- Indexability pass ------------------------------------------------------

def check_indexability_pass(record: object, today: dt.date) -> list:
    if not isinstance(record, dict):
        return [("free text is not a record", "run /geo:geo indexability; it writes url, status, redirects, robots, noindex, in_sitemap, raw_html_has_answer")]
    problems = []
    if not is_url(record.get("url")):
        problems.append(("no URL", "name the one https:// URL that answers the buyer question"))
    checked = parse_date(record.get("checked_at"))
    if checked is None:
        problems.append(("no checked_at date", "add the date the checks ran (YYYY-MM-DD)"))
    elif checked > today:
        problems.append(("checked_at is in the future", "record the date the checks ran"))
    status = record.get("status")
    if not is_int(status):
        problems.append(("no HTTP status", "record the final status as a number, as 200"))
    elif status != 200:
        problems.append((f"the URL returns {status}, not 200", "fix the URL until it returns 200"))
    redirects = record.get("redirects")
    if not is_int(redirects) or redirects < 0:
        problems.append(("redirects not recorded", "record the redirect count from curl's %{num_redirects}"))
    elif redirects > MAX_REDIRECTS:
        problems.append((f"{redirects} redirects", "link to the final URL; one hop at most"))
    robots = record.get("robots")
    if not isinstance(robots, dict) or not robots:
        problems.append(("robots not recorded", "record allowed or blocked for each crawler in robots.txt"))
    else:
        bad = [token for token, value in robots.items() if value not in ROBOTS_VALUES]
        if bad:
            problems.append((f"robots value for {', '.join(bad)} is not allowed or blocked", "write allowed or blocked"))
        missing = [token for token in REQUIRED_CRAWLERS if token not in robots]
        if missing:
            problems.append((f"robots not recorded for {', '.join(missing)}", "check robots.txt for each search crawler"))
        blocked = [token for token in ANSWER_CRAWLERS if robots.get(token) == "blocked"]
        if blocked:
            problems.append((f"the page is blocked for {', '.join(blocked)}", "unblock the crawler in robots.txt or the CDN, then run the pass again"))
    noindex = record.get("noindex")
    if not isinstance(noindex, bool):
        problems.append(("noindex not recorded", "record true or false from meta robots and X-Robots-Tag"))
    elif noindex:
        problems.append(("the page is noindex, none, or nosnippet", "drop the directive, then run the pass again"))
    sitemap = record.get("in_sitemap")
    if not isinstance(sitemap, bool):
        problems.append(("sitemap not recorded", "record true or false for the exact URL"))
    elif not sitemap:
        problems.append(("the URL is not in the sitemap", "add the exact URL to a sitemap robots.txt points to"))
    raw = record.get("raw_html_has_answer")
    if not isinstance(raw, bool):
        problems.append(("raw HTML not checked", "fetch the page without JavaScript and record whether the answer is there"))
    elif not raw:
        problems.append(("the answer is not in the raw HTML", "render the first paragraph on the server; most AI crawlers do not run JavaScript"))
    return problems


# --- Brief ------------------------------------------------------------------

def check_brief(record: object) -> list:
    if not isinstance(record, dict):
        return [("free text is not a brief", "run /geo:geo brief; it writes page, summary, unique_claim, follow_up_questions")]
    problems = []
    if not nonempty_text(record.get("page")):
        problems.append(("no page", "name the one URL or path this brief is for"))
    summary = nonempty_text(record.get("summary"))
    words = word_count(summary)
    if words < BRIEF_MIN_WORDS:
        problems.append(("summary too short to be a brief", "say what the page says first and in what order"))
    elif words > BRIEF_MAX_WORDS:
        problems.append(("more than one page", "cut it to one page; give the rest their own experiments"))
    claim = nonempty_text(record.get("unique_claim"))
    if word_count(claim) < CLAIM_MIN_WORDS:
        problems.append(("no unique claim", "write the one claim only this brand can say, in a sentence"))
    elif not SPECIFIC_RE.search(claim):
        problems.append(("the claim names nothing specific", "add a number, a date, a price, or a named method"))
    questions = text_list(record.get("follow_up_questions"))
    if not questions:
        problems.append(("no follow-up questions", "list the questions the page's headings answer"))
    elif any(not q.endswith("?") for q in questions):
        problems.append(("a follow-up is not a question", "write each heading as the question it answers, ending in ?"))
    return problems


def check_kill_date(text: str, baseline: dt.date | None) -> list:
    kill = parse_date(text)
    if kill is None or len(text) != 10:
        return [("not a date", "write the kill date as YYYY-MM-DD")]
    if baseline is None:
        return []
    days = (kill - baseline).days
    if days < KILL_MIN_DAYS:
        return [(f"under {KILL_MIN_DAYS} days after the citation record", "set it 6 to 12 weeks after the page ships")]
    if days > KILL_MAX_DAYS:
        return [(f"over {KILL_MAX_DAYS} days after the citation record", f"set it within {KILL_MAX_DAYS} days of the citation record")]
    return []


# --- Review -----------------------------------------------------------------

def check_review(record: object, values: dict, base: Path, today: dt.date) -> list:
    """The kill-date review: same citation method, plus search and business evidence."""
    if not isinstance(record, dict):
        return [("free text is not a review", "run /geo:geo review; it writes observations, metrics, decision, reason")]
    problems = []
    baseline = baseline_date(values["citation_record"])
    reviewed = parse_date(record.get("date"))
    if reviewed is None:
        problems.append(("no date", "add the review date (YYYY-MM-DD)"))
    elif reviewed > today:
        problems.append(("date is in the future", "record the date the review ran"))
    elif baseline and (reviewed - baseline).days < KILL_MIN_DAYS:
        problems.append((f"under {KILL_MIN_DAYS} days after the citation record", "wait for recrawl; review on the kill date"))

    citation = values["citation_record"] if isinstance(values["citation_record"], dict) else {}
    brand = nonempty_text(citation.get("brand"))
    brand_domain = nonempty_text(citation.get("brand_domain"))
    found, _dates, groups = check_observations(
        record.get("observations"), values["buyer_question"], brand, brand_domain, base, today, prefix="rerun ")
    problems.extend(found)
    if groups and isinstance(citation.get("observations"), list):
        before = {
            (nonempty_text(obs.get("engine")), nonempty_text(obs.get("method")).lower())
            for obs in citation["observations"] if isinstance(obs, dict)
        }
        missing = sorted(before - set(groups))
        if missing:
            problems.append((
                "rerun skips " + ", ".join(f"{e} ({m})" for e, m in missing),
                "rerun every engine with the same method as the baseline",
            ))

    metrics = record.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
        problems.append(("no metrics", "record " + ", ".join(REVIEW_METRICS) + " (null when not tracked)"))
    else:
        absent = [key for key in REVIEW_METRICS if key not in metrics]
        if absent:
            problems.append((f"metrics missing {', '.join(absent)}", "record each one; use null when it is not tracked"))
        if not isinstance(metrics.get("indexed"), (bool, type(None))):
            problems.append(("indexed is not true, false, or null", "record whether the URL is indexed (Search Console URL inspection)"))
        for key in REVIEW_METRICS[1:]:
            value = metrics.get(key)
            if value is not None and (not is_int(value) or value < 0):
                problems.append((f"{key} is not a count", "record a whole number, or null when it is not tracked"))
        if all(metrics.get(key) is None for key in REVIEW_METRICS):
            problems.append(("citations are the only evidence", "add indexation, impressions, qualified visits, or conversions before deciding"))

    decision = nonempty_text(record.get("decision")).lower()
    if decision not in REVIEW_DECISIONS:
        problems.append(("no decision", "decide one of: " + ", ".join(REVIEW_DECISIONS)))
    if word_count(nonempty_text(record.get("reason"))) < REASON_MIN_WORDS:
        problems.append(("no reason", "say which evidence drove the decision"))
    if decision == "stop":
        if metrics.get("indexed") is False:
            problems.append(("stopping a page that is not indexed", "fix indexation and revise; citations cannot be judged yet"))
        earning = [key for key in ("qualified_visits", "conversions") if is_int(metrics.get(key)) and metrics[key] > 0]
        if earning:
            problems.append((
                f"stopping a page with {' and '.join(k.replace('_', ' ') for k in earning)}",
                "revise or expand; missing citations alone do not justify removing a page that earns",
            ))
    return problems


# --- Summaries for the passing printout --------------------------------------

def summarize(key: str, value: object) -> str:
    if key == "citation_record":
        obs = [o for o in value["observations"] if isinstance(o, dict)]
        groups: dict = {}
        for o in obs:
            groups.setdefault(f"{o['engine']} ({o['method']})", 0)
            groups[f"{o['engine']} ({o['method']})"] += 1
        runs = ", ".join(f"{name} ×{count}" for name, count in groups.items())
        hits = sum(1 for o in obs if o["brand_status"].lower() != "neither")
        named = sorted({n for o in obs for n in o["brands_named"] if not same_words(n, value["brand"])})
        line = f"{baseline_date(value)} · {runs} · {value['brand']} named or cited in {hits}/{len(obs)} runs"
        return line + (f" · others named: {', '.join(named)}" if named else "")
    if key == "indexability_pass":
        allowed = sum(1 for v in value["robots"].values() if v == "allowed")
        return (f"{value['url']} · {value['status']}, {value['redirects']} redirects · "
                f"robots allows {allowed} of {len(value['robots'])} crawlers · in sitemap · "
                f"answer in raw HTML · checked {value['checked_at']}")
    if key == "brief":
        return f"{value['page']} · {value['summary']} Claim: {value['unique_claim']}"
    if key == "review":
        return f"{value['date']} · {value['decision']} · {value['reason']}"
    return str(value)


def score(values: dict, base: Path, today: dt.date) -> list:
    """Return (key, problem, fix) triples. Empty means the draft passes."""
    problems = []
    for key, _label in FIELDS:
        value = values[key]
        if not value:
            problems.append((key, "missing", f"run /geo:geo {MODES[key]}"))
        elif isinstance(value, str) and PLACEHOLDER_RE.match(value):
            problems.append((key, "a placeholder is not a record", f"run /geo:geo {MODES[key]} and write what you observed"))
        elif key in TEXT_FIELDS and not isinstance(value, str):
            problems.append((key, "not text", "write this field as a string"))
    if problems:
        return problems
    checks = (
        ("channel_decision", check_channel_decision(values["channel_decision"])),
        ("buyer_question", check_buyer_question(values["buyer_question"])),
        ("citation_record", check_citation_record(values["citation_record"], values["buyer_question"], base, today)),
        ("indexability_pass", check_indexability_pass(values["indexability_pass"], today)),
        ("brief", check_brief(values["brief"])),
        ("kill_date", check_kill_date(values["kill_date"], baseline_date(values["citation_record"]))),
    )
    for key, found in checks:
        problems.extend((key, problem, fix) for problem, fix in found)
    if values.get("review"):
        problems.extend(("review", problem, fix) for problem, fix in check_review(values["review"], values, base, today))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a findability draft",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to a JSON object (gtm/findability.json)")
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read a JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    base = Path(args.file).resolve().parent if args.file else Path.cwd()
    today = dt.date.today()
    keys = [key for key, _label in FIELDS] + ["review"]
    values = {key: normalize(data.get(key)) for key in keys}
    named = refusal_for(values)
    problems = [] if named else score(values, base, today)
    passed = not named and not problems
    review = values["review"] if isinstance(values["review"], dict) else None
    next_step = NEXT_FAIL
    if passed:
        next_step = NEXT_REVIEW[review["decision"].lower()] if review else NEXT_PASS

    if args.json:
        result = {"pass": passed, "refused": named or None}
        if named:
            result["fix"] = REFUSAL_FIXES[named]
        result["problems"] = [
            {"field": key, "problem": text, "fix": fix} for key, text, fix in problems
        ]
        if passed:
            result["artifact"] = {key: values[key] for key in keys if values[key]}
        result["next"] = next_step
        print(json.dumps(result, indent=2))
    elif named:
        print(f"refused: {named}")
        print(f"- {named} → {REFUSAL_FIXES[named]}")
        print(f"Next: {next_step}")
    elif problems:
        print("draft is incomplete")
        for key, text, fix in problems:
            print(f"- {LABELS[key]}: {text} → {fix}")
        print(f"Next: {next_step}")
    else:
        for key in keys:
            if values[key]:
                print(f"{LABELS[key]}: {summarize(key, values[key])}")
        print(f"Next: {next_step}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
