#!/usr/bin/env python3
"""score.py prints the findability artifact or refuses the named bad draft."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
CELL = "super-secret-cell"
GOOD = json.loads((EXAMPLES / "findability-good.json").read_text())
REVIEWED = json.loads((EXAMPLES / "findability-reviewed.json").read_text())


def run(args, stdin=None):
    # Evidence paths in the examples resolve against examples/ for --stdin too.
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=EXAMPLES,
    )


def score_draft(draft):
    return run(["--stdin"], stdin=json.dumps(draft))


def score(**changes):
    return score_draft({**copy.deepcopy(GOOD), **changes})


def with_obs(base=GOOD, **changes):
    """GOOD with every baseline observation changed."""
    draft = copy.deepcopy(base)
    for obs in draft["citation_record"]["observations"]:
        obs.update(changes)
    return draft


def with_index(**changes):
    draft = copy.deepcopy(GOOD)
    draft["indexability_pass"].update(changes)
    return draft


def with_brief(**changes):
    draft = copy.deepcopy(GOOD)
    draft["brief"].update(changes)
    return draft


def with_review(**changes):
    draft = copy.deepcopy(REVIEWED)
    draft["review"].update(changes)
    return draft


def with_metrics(**changes):
    draft = copy.deepcopy(REVIEWED)
    draft["review"]["metrics"].update(changes)
    return draft


class ScoreFindability(unittest.TestCase):
    def test_good_draft_prints_artifact(self):
        result = run(["--file", str(EXAMPLES / "findability-good.json")])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for label in ("channel decision:", "buyer question:", "citation record:",
                      "indexability pass:", "brief:", "kill date:"):
            self.assertIn(label, result.stdout)
        self.assertIn("named or cited in 0/3 runs", result.stdout)
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: /landing-page:page")

    def test_good_draft_from_another_folder(self):
        # --file resolves evidence against the draft's folder, not the cwd.
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "score.py"), "--file", str(EXAMPLES / "findability-good.json")],
            capture_output=True, text=True, cwd=ROOT / "tests",
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_calendar_exits_1(self):
        result = run(["--file", str(EXAMPLES / "findability-calendar.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a 40-article calendar", result.stdout)
        self.assertNotIn("channel decision:", result.stdout)

    def test_weak_draft_names_each_axis(self):
        result = run(["--file", str(EXAMPLES / "findability-weak.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("draft is incomplete", result.stdout)
        for label in ("channel decision", "buyer question", "citation record",
                      "indexability pass", "brief", "kill date"):
            self.assertIn("- " + label + ":", result.stdout)
        for line in result.stdout.splitlines()[1:-1]:
            self.assertIn(" → ", line)
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: fix the lines above and run this again.")

    def test_help_shows_example(self):
        result = run(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("examples/findability-good.json", result.stdout)

    def test_input_alias(self):
        result = run(["--input", str(EXAMPLES / "findability-good.json")])
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_template_is_missing_everywhere(self):
        result = run(["--file", str(EXAMPLES / "findability-template.json")])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count(": missing →"), 6, result.stdout)

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"brief": "' + CELL)
        self.assertNotEqual(bad.returncode, 0)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertNotEqual(array.returncode, 0)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)

    def test_json_output(self):
        result = run(["--file", str(EXAMPLES / "findability-good.json"), "--json"])
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["pass"])
        self.assertEqual(payload["artifact"]["kill_date"], "2026-12-15")
        self.assertEqual(payload["artifact"]["indexability_pass"]["status"], 200)
        self.assertEqual(payload["next"], "/landing-page:page")
        failing = json.loads(run(["--stdin", "--json"], stdin=json.dumps({**GOOD, "kill_date": "soon"})).stdout)
        self.assertFalse(failing["pass"])
        self.assertEqual(failing["problems"][0]["field"], "kill_date")
        self.assertTrue(failing["problems"][0]["fix"])
        self.assertIn("run this again", failing["next"])


class Refusals(unittest.TestCase):
    def test_refusals_in_plan_fields(self):
        cases = {
            "a health-score dump": with_brief(summary="Publish the site health score for every page we own, ranked."),
            "an llms.txt project": {**GOOD, "channel_decision": "Search is a channel, so we start an llms.txt project for the site."},
            "a 40-article calendar": with_brief(summary="Write 25 posts on answer engines and ship them all this quarter."),
        }
        for named, draft in cases.items():
            with self.subTest(named):
                result = score_draft(draft)
                self.assertEqual(result.returncode, 1)
                lines = result.stdout.strip().splitlines()
                self.assertEqual(lines[0], f"refused: {named}")
                self.assertTrue(lines[1].startswith(f"- {named} → "), lines[1])
                self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")

    def test_rejecting_a_calendar_is_not_a_calendar(self):
        for summary in (
            "One page, not a 40-article calendar. First paragraph answers the buyer question.",
            "No content calendar; the first paragraph answers the buyer question with the claim.",
            "Skip the health score. First paragraph answers the buyer question with one claim.",
            "We avoid an llms.txt file. First paragraph answers the buyer question with one claim.",
        ):
            with self.subTest(summary):
                result = score_draft(with_brief(summary=summary))
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_negation_does_not_leak_across_clauses(self):
        result = score_draft(with_brief(summary="No single page will do, write 25 posts on answer engines this quarter."))
        self.assertIn("refused: a 40-article calendar", result.stdout)

    def test_refusal_reads_follow_up_questions(self):
        result = score_draft(with_brief(follow_up_questions=["What goes in our 40-article content calendar?"]))
        self.assertIn("refused", result.stdout)

    def test_observations_may_name_llms_txt(self):
        result = score_draft(with_index(notes="An llms.txt file exists and changes nothing here."))
        self.assertEqual(result.returncode, 0, result.stdout)


class Axes(unittest.TestCase):
    def assertProblem(self, result, label, text=""):
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("- " + label + ":", result.stdout)
        if text:
            self.assertIn(text, result.stdout)

    def test_placeholders_fail(self):
        self.assertProblem(score(citation_record="None observed."), "citation record")
        self.assertProblem(score(indexability_pass="Unchecked."), "indexability pass")

    def test_free_text_records_fail(self):
        self.assertProblem(score(citation_record="On 2026-10-01 a pasted answer named a rival. Method: pasted answer."),
                           "citation record", "free text is not a record")
        self.assertProblem(score(indexability_pass="The URL returns 200, is allowed in robots, and is in the sitemap."),
                           "indexability pass", "free text is not a record")
        self.assertProblem(score(brief="One page. First paragraph answers the buyer question with one claim."),
                           "brief", "free text is not a brief")

    def test_buyer_question(self):
        self.assertProblem(score(buyer_question="answer engine optimization agency pricing"), "buyer question")
        self.assertProblem(score(buyer_question="What should we publish next?"), "buyer question")
        self.assertProblem(score(buyer_question="What is GEO? How is it priced?"), "buyer question")
        self.assertProblem(score(buyer_question="GEO?"), "buyer question")
        self.assertProblem(score(buyer_question="geo agency | aeo agency | ai seo tool?"), "buyer question")


class CitationRecord(unittest.TestCase):
    def assertProblem(self, draft, text):
        result = score_draft(draft)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("- citation record:", result.stdout)
        self.assertIn(text, result.stdout)

    def test_three_runs_per_engine(self):
        draft = copy.deepcopy(GOOD)
        draft["citation_record"]["observations"] = draft["citation_record"]["observations"][:2]
        self.assertProblem(draft, "ChatGPT (pasted answer) has 2 runs")

    def test_duplicate_run_numbers_count_once(self):
        self.assertProblem(with_obs(run=1), "has 1 run")

    def test_tool_export_needs_one_row(self):
        draft = copy.deepcopy(GOOD)
        obs = copy.deepcopy(draft["citation_record"]["observations"][0])
        obs.update(method="tool export", engine="Perplexity")
        draft["citation_record"]["observations"].append(obs)
        self.assertEqual(score_draft(draft).returncode, 0, score_draft(draft).stdout)

    def test_query_is_the_buyer_question(self):
        self.assertProblem(with_obs(query="best way to pick a buyer question for one page?"), "not the buyer question")
        ok = with_obs(query="  how do I know which buyer question  is worth one page? ")
        self.assertEqual(score_draft(ok).returncode, 0)

    def test_query_without_brand(self):
        draft = with_obs(query="How do I know which buyer question is worth one page? Example Co")
        draft["buyer_question"] = draft["citation_record"]["observations"][0]["query"]
        self.assertProblem(draft, "query names the brand")

    def test_needs_brand(self):
        draft = copy.deepcopy(GOOD)
        del draft["citation_record"]["brand"]
        self.assertProblem(draft, "no brand")

    def test_evidence_saved(self):
        self.assertProblem(with_obs(evidence=""), "no evidence")
        self.assertProblem(with_obs(evidence="evidence/not-there.png"), "evidence file not found")
        ok = with_obs(evidence="https://example.com/evidence/run.png")
        self.assertEqual(score_draft(ok).returncode, 0)

    def test_clean_session(self):
        self.assertProblem(with_obs(clean_session=False), "not a clean session")
        ok = with_obs(method="api run", clean_session=False)
        self.assertEqual(score_draft(ok).returncode, 0, score_draft(ok).stdout)

    def test_dates(self):
        self.assertProblem(with_obs(observed_at="yesterday"), "no observed_at date")
        self.assertProblem(with_obs(observed_at="2999-01-01"), "in the future")
        draft = copy.deepcopy(GOOD)
        draft["citation_record"]["observations"][2]["observed_at"] = "2026-09-01"
        self.assertProblem(draft, "runs span more than 7 days")
        ok = with_obs(observed_at="2026-10-01T14:02:00Z")
        self.assertEqual(score_draft(ok).returncode, 0)

    def test_fields_typed(self):
        self.assertProblem(with_obs(method="remembered"), "unknown method")
        self.assertProblem(with_obs(brands_named="Rival Co"), "brands_named is not a list")
        self.assertProblem(with_obs(cited_urls=["rival.example"]), "not a full URL")
        self.assertProblem(with_obs(brand_status="maybe"), "no brand_status")
        self.assertProblem(with_obs(engine=""), "no engine")

    def test_brand_status_matches_answer(self):
        self.assertProblem(with_obs(brand_status="named"), "disagrees with brands_named")
        self.assertProblem(with_obs(cited_urls=["https://www.example.com/x"]), "disagrees with cited_urls")
        ok = with_obs(cited_urls=["https://www.example.com/x"], brand_status="cited")
        self.assertEqual(score_draft(ok).returncode, 0, score_draft(ok).stdout)


class Indexability(unittest.TestCase):
    def assertProblem(self, draft, text):
        result = score_draft(draft)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("- indexability pass:", result.stdout)
        self.assertIn(text, result.stdout)

    def test_exactly_200(self):
        self.assertProblem(with_index(status=204), "returns 204, not 200")
        self.assertProblem(with_index(status=301), "returns 301")
        self.assertProblem(with_index(status="200"), "no HTTP status")
        self.assertProblem(with_index(status=True), "no HTTP status")

    def test_redirects(self):
        self.assertEqual(score_draft(with_index(redirects=1)).returncode, 0)
        self.assertProblem(with_index(redirects=2), "2 redirects")

    def test_robots(self):
        self.assertProblem(with_index(robots={}), "robots not recorded")
        self.assertProblem(with_index(robots={"Googlebot": "allowed"}), "robots not recorded for Bingbot")
        self.assertProblem(with_index(robots={"Googlebot": "allowed", "Bingbot": "allowed", "PerplexityBot": "blocked"}),
                           "blocked for PerplexityBot")
        self.assertProblem(with_index(robots={"Googlebot": "yes", "Bingbot": "allowed"}), "is not allowed or blocked")
        training_blocked = with_index(robots={"Googlebot": "allowed", "Bingbot": "allowed", "ClaudeBot": "blocked", "CCBot": "blocked"})
        self.assertEqual(score_draft(training_blocked).returncode, 0)

    def test_page_flags(self):
        self.assertProblem(with_index(noindex=True), "noindex")
        self.assertProblem(with_index(noindex="no"), "noindex not recorded")
        self.assertProblem(with_index(in_sitemap=False), "not in the sitemap")
        self.assertProblem(with_index(raw_html_has_answer=False), "not in the raw HTML")
        self.assertProblem(with_index(url="example.com/page"), "no URL")
        self.assertProblem(with_index(checked_at="2999-01-01"), "in the future")


class Brief(unittest.TestCase):
    def assertProblem(self, draft, text):
        result = score_draft(draft)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("- brief:", result.stdout)
        self.assertIn(text, result.stdout)

    def test_one_page(self):
        self.assertProblem(with_brief(summary="One page."), "summary too short")
        self.assertProblem(with_brief(summary=" ".join(["word"] * 200)), "more than one page")
        self.assertProblem(with_brief(page=""), "no page")

    def test_unique_claim(self):
        self.assertProblem(with_brief(unique_claim=""), "no unique claim")
        self.assertProblem(with_brief(unique_claim="we are fast, friendly, and easy to work with."), "names nothing specific")
        for claim in ("Setup takes 4 days instead of three weeks for most teams.",
                      "Our Pain Signal Profile method maps buyer words to pages.",
                      'Our "first-answer test" decides which page ships next.'):
            with self.subTest(claim):
                self.assertEqual(score_draft(with_brief(unique_claim=claim)).returncode, 0)

    def test_follow_up_questions(self):
        self.assertProblem(with_brief(follow_up_questions=[]), "no follow-up questions")
        self.assertProblem(with_brief(follow_up_questions=["Where questions come from"]), "not a question")


class KillDate(unittest.TestCase):
    def test_kill_date_window(self):
        for value in ("next quarter", "2026-10-05", "2027-09-01", "2026-13-40", "2026-12-15T00:00:00Z"):
            with self.subTest(value):
                result = score(kill_date=value)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("- kill date:", result.stdout)


class Review(unittest.TestCase):
    def assertProblem(self, draft, text):
        result = score_draft(draft)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("- review:", result.stdout)
        self.assertIn(text, result.stdout)

    def test_reviewed_example_passes(self):
        result = run(["--file", str(EXAMPLES / "findability-reviewed.json")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("review: 2026-09-14 · expand", result.stdout)
        self.assertIn("Next: /geo:geo buyer-question", result.stdout)

    def test_next_step_follows_decision(self):
        result = score_draft(with_review(decision="revise"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Next: /geo:geo brief", result.stdout)

    def test_citations_alone_do_not_decide(self):
        draft = with_metrics(indexed=None, impressions=None, qualified_visits=None, conversions=None)
        self.assertProblem(draft, "citations are the only evidence")

    def test_metrics_recorded(self):
        draft = copy.deepcopy(REVIEWED)
        del draft["review"]["metrics"]["conversions"]
        self.assertProblem(draft, "metrics missing conversions")
        self.assertProblem(with_metrics(impressions=-1), "impressions is not a count")
        self.assertProblem(with_metrics(indexed="yes"), "indexed is not true, false, or null")

    def test_do_not_stop_a_page_that_earns(self):
        self.assertProblem(with_review(decision="stop"), "stopping a page with qualified visits and conversions")
        draft = with_review(decision="stop")
        draft["review"]["metrics"].update(qualified_visits=0, conversions=0)
        self.assertEqual(score_draft(draft).returncode, 0, score_draft(draft).stdout)

    def test_do_not_stop_an_unindexed_page(self):
        draft = with_review(decision="stop")
        draft["review"]["metrics"].update(indexed=False, qualified_visits=0, conversions=0)
        self.assertProblem(draft, "not indexed")

    def test_rerun_uses_the_same_method(self):
        draft = copy.deepcopy(REVIEWED)
        for obs in draft["review"]["observations"]:
            obs["method"] = "api run"
        self.assertProblem(draft, "rerun skips ChatGPT (pasted answer)")

    def test_rerun_is_validated(self):
        draft = copy.deepcopy(REVIEWED)
        draft["review"]["observations"] = draft["review"]["observations"][:1]
        self.assertProblem(draft, "rerun ChatGPT (pasted answer) has 1 run")

    def test_decision_and_reason(self):
        self.assertProblem(with_review(decision="keep"), "no decision")
        self.assertProblem(with_review(reason="good"), "no reason")
        self.assertProblem(with_review(date="2026-07-10"), "under 14 days")


if __name__ == "__main__":
    unittest.main()
