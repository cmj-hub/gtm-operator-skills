# Indexability

Mode `indexability`: whether one URL can be fetched and listed by search and AI crawlers. Writes `indexability_pass`.

An indexability pass says whether one URL can be fetched and listed. It is not a site grade.

Answer engines can only quote what their crawler fetched or what a search index holds. Fetchability comes before content.

## Contents

- Checklist
- The six checks
- Crawlers to check in robots.txt
- Not part of this pass
- Output
- Score

## Checklist

Copy this list and tick it in order.

- [ ] 1. Name the one URL. The page that will answer the buyer question, or the page that answers it now.
- [ ] 2. Run the six checks below. Write each result.
- [ ] 3. Write each result into the `indexability_pass` object (Output, below).
- [ ] 4. Run the scorer.

Check again until the scorer exits 0.

Go back to step 2 if step 4 fails.

## The six checks

Set `URL` and the site root first. Every command is read-only.

```bash
URL="https://example.com/page"
SITE="https://example.com"
```

1. **Status.** One hop to 200. No redirect chain, no soft 404.
   ```bash
   curl -sIL -o /dev/null -w '%{http_code} %{num_redirects} %{url_effective}\n' "$URL"
   ```
   Record the final code as `status` (a number) and the count as `redirects`. Only 200 passes; at most one redirect.
2. **robots.txt.** The path is allowed for the crawlers below. A `Disallow` under `User-agent: *` blocks them all.
   ```bash
   curl -s "$SITE/robots.txt"
   ```
   Record `allowed` or `blocked` per crawler token in `robots`. `Googlebot` and `Bingbot` are required; add every AI crawler you checked.
3. **Meta robots and headers.** No `noindex`, `none`, or `nosnippet` on the page or in `X-Robots-Tag`. `nosnippet` keeps the page out of AI Overviews.
   ```bash
   curl -sI "$URL" | grep -i x-robots-tag
   curl -s "$URL" | grep -io '<meta[^>]*robots[^>]*>'
   ```
   Record `noindex: true` if any of the three is present.
4. **Canonical.** The page names itself as canonical, or names the URL you meant.
   ```bash
   curl -s "$URL" | grep -io '<link[^>]*canonical[^>]*>'
   ```
5. **Sitemap.** The exact URL is listed in a sitemap that robots.txt points to.
   ```bash
   curl -s "$SITE/robots.txt" | grep -i sitemap
   ```
   Record `in_sitemap` as true or false for the exact URL.
6. **Raw HTML.** The first paragraph of the answer appears in the HTML before JavaScript runs. Most AI crawlers do not render JavaScript.
   ```bash
   curl -s -A "Mozilla/5.0 (compatible; GPTBot/1.0)" "$URL" | grep -c "a phrase from the first paragraph"
   ```
   Record `raw_html_has_answer`. A count of 0 means the crawler sees an empty page. Repeat with the other user agents below and check the status: a CDN or bot wall that returns 403 to AI crawlers blocks the page even when robots allows it. Some CDNs block AI crawlers by default.

## Crawlers to check in robots.txt

Search indexes that answer engines draw from:

| Token | Feeds |
|---|---|
| `Googlebot` | Google Search, AI Overviews, AI Mode |
| `Bingbot` | Bing, Copilot, and engines that use the Bing index |

AI search and user-triggered fetchers. Blocking these removes the page from that engine's answers:

| Token | Feeds |
|---|---|
| `OAI-SearchBot`, `ChatGPT-User` | ChatGPT search and browsing |
| `Claude-SearchBot`, `Claude-User` | Claude search and browsing |
| `PerplexityBot`, `Perplexity-User` | Perplexity |

Training crawlers. Blocking these is a policy choice, not a findability fix:

| Token | Feeds |
|---|---|
| `GPTBot` | OpenAI model training |
| `ClaudeBot` | Anthropic model training |
| `Google-Extended` | Gemini training and grounding. Does not affect AI Overviews. |
| `Applebot-Extended` | Apple model training |
| `CCBot` | Common Crawl |

Vendors rename and add crawlers. Check the vendor's crawler page before you edit robots.txt.

## Not part of this pass

- An llms.txt file. It is not a fetchability control. No major answer engine has committed to read it.
- A site-wide crawl score. One URL, one pass.
- Page speed scores, unless the page times out.

## Output

The `indexability_pass` object. Example:

```json
{
  "url": "https://example.com/guides/which-buyer-question",
  "checked_at": "2026-10-01",
  "status": 200,
  "redirects": 0,
  "robots": {"Googlebot": "allowed", "Bingbot": "allowed", "OAI-SearchBot": "allowed",
             "Claude-SearchBot": "allowed", "PerplexityBot": "allowed", "GPTBot": "blocked"},
  "noindex": false,
  "in_sitemap": true,
  "raw_html_has_answer": true,
  "notes": "Optional. Anything else you saw, such as a CDN rule."
}
```

The scorer fails the pass on any status but 200, more than one redirect, a search or AI-search crawler marked `blocked` (training crawlers may be blocked), `noindex: true`, `in_sitemap: false`, or `raw_html_has_answer: false`. A pass records that the URL can be fetched on `checked_at`; it does not show the URL is indexed. The review checks indexation.

## Score

Write the field into `gtm/findability.json` (create `gtm/` if missing; start from `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json`), then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the six lines. Exit 1 prints `- field: what is wrong → what to change` per problem; fix that field first. Fields other skills own may read `missing` until those skills run.
