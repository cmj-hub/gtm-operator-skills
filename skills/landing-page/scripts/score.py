#!/usr/bin/env python3
"""Score a page: one URL, one offer, and one action. Refuse a sitemap.

Optional: a one-sentence headline that names the offer and holds no URL,
and a one-line proof.

Stdlib only. No network. Does not publish.

  python3 scripts/score.py --file gtm/page.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/page.json --json

Each failing line reads `- <what is wrong> -> <what to change>`; the last line
names the next step.

Exit codes: 0 the page passes, 1 the page fails, 2 the input is unusable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


MAX_INPUT_BYTES = 2_000_000
MAX_OFFER_CHARS = 200
MAX_ACTION_CHARS = 160
MAX_PROOF_CHARS = 200

# Keys that mean the draft carries more than one of something.
SITEMAP_KEYS = ("urls", "pages", "sitemap")
EXTRA_OFFER_KEYS = ("offers", "offer_2", "second_offer")
EXTRA_ACTION_KEYS = ("actions", "ctas", "action_2", "second_action")

# A URL inside a headline: a scheme or a bare www. host.
URL_IN_TEXT = re.compile(r"\bhttps?://|\bwww\.", re.IGNORECASE)

# Short or generic words that do not show the headline names the offer.
STOP = {
    "that", "with", "this", "your", "from", "into", "over", "than", "then",
    "them", "they", "have", "what", "when", "where", "will", "just", "only",
    "read", "reply", "want", "next", "page", "names", "name",
}

# A sentence end followed by more text. "e.g." and decimals do not split.
SENTENCE_BREAK = re.compile(r"(?<!\be\.g)(?<!\bi\.e)[.!?]+[\"')\]]*\s+(?=\S)")


NEXT_PASS = "/email-sequence:lifecycle-email"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = "example:\n  python3 scripts/score.py --file examples/page-good.json"


def fix_for(problem: str) -> str:
    """What to change for one problem line. Plain words, no input echoed."""
    if problem == "a sitemap":
        return "keep one https address; each other page gets its own draft"
    if problem == "url is missing":
        return "write the page's address as https://host/path"
    if problem == "url holds more than one address":
        return "keep one address"
    if problem in ("url is not https", "url has no host"):
        return "write it as https://host/path"
    if problem == "headline holds a URL":
        return "move the address to url"
    if problem == "headline does not name the offer":
        return "put the offer's noun or result in the headline"
    if problem == "proof is empty":
        return "write one real result, or drop proof"
    if problem == "proof is more than one line":
        return "cut it to one line"
    match = re.match(r"more than one (\w+)$", problem)
    if match:
        return f"keep one {match.group(1)}; move the other to its own page"
    match = re.match(r"(\w+) is missing$", problem)
    if match:
        return f"write one {match.group(1)} sentence"
    if problem.endswith("is more than one sentence"):
        return "cut it to one sentence"
    match = re.search(r"longer than (\d+) characters$", problem)
    if match:
        return f"cut it to {match.group(1)} characters or fewer"
    return "fix this field"


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
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
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
    except (json.JSONDecodeError, RecursionError):
        fail_input("invalid JSON")


def nonempty_text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return " ".join(value.split())
    return ""


def is_sitemap(data: dict) -> bool:
    kind = nonempty_text(data.get("kind")).lower()
    if kind == "sitemap":
        return True
    if any(isinstance(data.get(key), (list, dict)) for key in SITEMAP_KEYS):
        return True
    if isinstance(data.get("url"), list):
        return True
    url = nonempty_text(data.get("url")).lower()
    path = urlsplit(url).path if url else ""
    if "sitemap" in url or path.endswith(".xml"):
        return True
    return False


def has_any(data: dict, keys: tuple[str, ...]) -> bool:
    return any(data.get(key) not in (None, "", [], {}) for key in keys)


def sentence_count(text: str) -> int:
    return len(SENTENCE_BREAK.split(text.strip()))


def check_url(raw: object) -> list[str]:
    url = nonempty_text(raw)
    if not url:
        return ["url is missing"]
    if any(ch.isspace() for ch in url) or url.count("://") > 1:
        return ["url holds more than one address"]
    parts = urlsplit(url)
    if parts.scheme != "https":
        return ["url is not https"]
    if not parts.hostname or "." not in parts.hostname:
        return ["url has no host"]
    return []


def check_line(name: str, raw: object, extra: bool, limit: int) -> list[str]:
    if isinstance(raw, (list, dict)) or extra:
        return [f"more than one {name}"]
    text = nonempty_text(raw)
    if not text:
        return [f"{name} is missing"]
    problems = []
    if sentence_count(text) > 1:
        problems.append(f"{name} is more than one sentence")
    if len(text) > limit:
        problems.append(f"{name} is longer than {limit} characters")
    return problems


def content_words(text: str) -> set[str]:
    """Words longer than three letters that are not in STOP."""
    words = re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("\u2019", ""))
    return {word for word in words if len(word) > 3 and word not in STOP}


def check_headline(raw: object, offer: object) -> list[str]:
    """Optional. One sentence, no URL, and it shares a content word with the offer."""
    problems = check_line("headline", raw, False, MAX_OFFER_CHARS)
    text = nonempty_text(raw) if isinstance(raw, str) else ""
    if not text:
        return problems
    if URL_IN_TEXT.search(text):
        problems.append("headline holds a URL")
    offer_words = content_words(nonempty_text(offer)) if isinstance(offer, str) else set()
    if offer_words and not offer_words & content_words(text):
        problems.append("headline does not name the offer")
    return problems


def check_proof(raw: object) -> list[str]:
    """Optional. One non-empty line."""
    if isinstance(raw, (list, dict)):
        return ["proof is more than one line"]
    if not isinstance(raw, str) or not raw.strip():
        return ["proof is empty"]
    if "\n" in raw.strip() or "\r" in raw.strip():
        return ["proof is more than one line"]
    if len(nonempty_text(raw)) > MAX_PROOF_CHARS:
        return [f"proof is longer than {MAX_PROOF_CHARS} characters"]
    return []


def score(data: dict) -> dict:
    if is_sitemap(data):
        return {"pass": False, "sitemap": True, "problems": ["a sitemap"]}
    has_headline = data.get("headline") is not None
    has_proof = data.get("proof") is not None
    problems = check_url(data.get("url"))
    if has_headline:
        problems += check_headline(data.get("headline"), data.get("offer"))
    if has_proof:
        problems += check_proof(data.get("proof"))
    problems += (
        check_line("offer", data.get("offer"), has_any(data, EXTRA_OFFER_KEYS), MAX_OFFER_CHARS)
        + check_line("action", data.get("action"), has_any(data, EXTRA_ACTION_KEYS), MAX_ACTION_CHARS)
    )
    result = {"pass": not problems, "sitemap": False, "problems": problems}
    if not problems:
        result["url"] = nonempty_text(data["url"])
        if has_headline:
            result["headline"] = nonempty_text(data["headline"])
        if has_proof:
            result["proof"] = nonempty_text(data["proof"])
        result["offer"] = nonempty_text(data["offer"])
        result["action"] = nonempty_text(data["action"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a page draft: one https URL, one offer, one action. Refuses a sitemap.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to a JSON object (gtm/page.json)")
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read a JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    result = score(data)
    result["fixes"] = [fix_for(problem) for problem in result["problems"]]
    result["next"] = NEXT_PASS if result["pass"] else NEXT_FAIL

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif not result["pass"]:
        print("a sitemap" if result["sitemap"] else "draft fails")
        for problem, fix in zip(result["problems"], result["fixes"]):
            print(f"- {problem} → {fix}")
        print(f"Next: {NEXT_FAIL}")
    else:
        for key in ("url", "headline", "proof", "offer"):
            if key in result:
                print(f"{key}: {result[key]}")
        print(f"action: {result['action']}")
        print(f"Next: {NEXT_PASS}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
