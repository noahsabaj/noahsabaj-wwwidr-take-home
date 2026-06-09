# Contact Finder — AgentCollect Challenge (Stage B slice)

Takes a CSV of `company_name, mailing_address` and, for each company, finds the
right payment decision-maker by combining three independent (and individually
fallible) data sources — returning a contact only when it can be verified, and
flagging everything else for human review.

Design rationale is in [`PLAN.md`](PLAN.md), written and committed *before* the
clarifications (per the gated process). Reflection is in [`ABOUT.md`](ABOUT.md).

## Run it

```bash
python contact_finder.py
```

No dependencies (Python standard library only). It reads `data/companies.csv` and
`mocks/enrichment_responses.json`, prints a summary table, and writes
`output/contacts.csv`.

## Output

One row per company:

| field | meaning |
|-------|---------|
| `contact_name` | resolved decision-maker (kept as a lead even on review rows) |
| `contact_role` | role if known (Owner, President, …) |
| `contact_email_or_phone` | the reachable channel — **empty** when below threshold or unverifiable |
| `confidence_score` | explainable 0–100 (decomposed in the `reasons` column) |
| `source` | which providers contributed, e.g. `registry+listing+enrichment` |
| `needs_human_review` | `true` when confidence < 70 or there is no verifiable contact |
| `provenance` | the `mock://` source_url behind every value |
| `reasons` | full, human-readable trail of *why* the row scored what it did |

## How it works

- **Three fallible sources, one resolver.** `registry` (name + role), `listing`
  (web/maps; name + phone), `enrichment` (email/phone + self-reported confidence).
  Any source can be absent or return null fields.
- **Source authority for the name:** `registry > listing`. A registry
  **Registered Agent** is *not* the decision-maker — its name is discarded.
- **Agreement raises confidence; conflict lowers it.** When the registry and
  listing names match — fuzzily ("Robert" ≈ "Bob Kowalski", "Sean" ≈ "S. Murphy")
  — the score jumps; when they disagree (e.g. Tina Alvarez vs Marcus Webb) the row
  is sent to review rather than guessed.
- **Role priority** (per clarifications): AP/AR → owner/founder → CFO/finance →
  office manager.
- **Explainable confidence, threshold 70.** Below 70 → empty contact +
  `needs_human_review = true`. `enrichment.provider_confidence` is blended in, not
  taken as the final score.
- **Never fabricates.** No verifiable contact → flagged, never guessed. Every
  emitted value is attributable to a `source_url`.
- **Suppression / opt-out hook** is enforced before any lookup.

## Result on the sample data

8 of 30 companies returned a confident, traceable contact (≥ 70); 22 went to human
review. That high review rate is intentional — the brief optimises for **precision
over recall**: a correct, attributable contact is worth more than three guesses.

## Adaptation (plan → clarifications)

My three clarifying questions lined up with what the clarifications answered, and my
defaults matched on all three. The clarifications validated the plan and refined
three knobs:

1. **Persona** — I assumed AP/billing first, falling back to owner. Confirmed and
   sharpened to the exact ladder (AP → owner/founder → CFO/finance → office
   manager), which is now the role-fit weighting in the score.
2. **Threshold** — I assumed a conservative, review-biased cutoff. Confirmed
   (precision over recall) and set to a hard **70**, with an empty contact below it.
3. **Sources & compliance** — my registry → listing → enrichment design maps 1:1
   onto the three mock providers. Compliance tightened to US-B2B / business-only,
   and added an **opt-out / suppression** requirement, implemented as a suppression
   hook.