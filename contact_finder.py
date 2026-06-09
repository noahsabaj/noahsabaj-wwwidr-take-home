#!/usr/bin/env python3
"""
contact_finder.py - Stage B slice for the AgentCollect contact-finder challenge.

Implements the design in PLAN.md against the mocked providers in mocks/.

Reads:
    data/companies.csv               (company_name, mailing_address)
    mocks/enrichment_responses.json  (canned responses for 3 fallible "providers")
Writes:
    output/contacts.csv              (required output schema + provenance + reasons)
and prints a readable summary to stdout.

Design decisions (mirror PLAN.md + CLARIFICATIONS.md):
  - Three independent, individually-fallible sources: registry, listing, enrichment.
  - Source authority for the NAME: registry > listing (enrichment carries no name).
  - A registry "Registered Agent" is NOT the decision-maker -> its name is discarded.
  - Role priority (CLARIFICATIONS): AP/AR > owner/founder > CFO/finance > office manager.
  - Agreement across independent sources RAISES confidence; conflict LOWERS it.
  - confidence_score is an explainable 0-100 number with a per-row reasons trail.
  - Threshold = 70 (CLARIFICATIONS): below it -> empty contact + needs_human_review.
  - Provenance: every emitted value carries its mock:// source_url(s).
  - Suppression/opt-out hook (CLARIFICATIONS requirement) is enforced first.
  - Never fabricate: no verifiable contact -> needs_human_review, not a guess.
"""

import csv
import json
import os
from difflib import SequenceMatcher

# --- config ----------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "data", "companies.csv")
MOCK_PATH = os.path.join(HERE, "mocks", "enrichment_responses.json")
OUT_DIR = os.path.join(HERE, "output")
OUT_PATH = os.path.join(OUT_DIR, "contacts.csv")

CONFIDENCE_THRESHOLD = 70  # from CLARIFICATIONS.md

# Opt-out / suppression list (CLARIFICATIONS: "must support opt-out / suppression").
# Any company in here is never contacted, regardless of what the providers return.
SUPPRESSION_LIST = set()  # e.g. {"Cedar Ridge Plumbing LLC"}

# Roles that can authorize payment, best -> worst (CLARIFICATIONS priority order).
ROLE_PRIORITY = {
    "ap manager": 5, "accounts payable": 5, "ar manager": 5,
    "owner": 4, "founder": 4, "president": 4, "ceo": 4, "partner": 4, "member": 4,
    "cfo": 3, "finance lead": 3, "controller": 3, "finance": 3,
    "office manager": 2, "general manager": 2, "manager": 2,
}
NON_DECISION_ROLES = {"registered agent"}   # explicitly not our person
NAME_MATCH_RATIO = 0.6                       # "bounds of entropy" = fuzzy-match tolerance


# --- name matching ----------------------------------------------------------
def norm_name(name):
    """Lowercase, drop common titles and any '(parenthetical)' for matching."""
    if not name:
        return ""
    n = name.lower()
    for p in ("dr. ", "dr ", "mr. ", "mr ", "ms. ", "ms ", "mrs. ", "mrs "):
        if n.startswith(p):
            n = n[len(p):]
    if "(" in n:
        n = n.split("(")[0]
    return n.strip()


def same_person(a, b):
    """Fuzzy match two names: handles Robert/Bob, Sean/S. Murphy, spelling drift."""
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    pa, pb = na.split(), nb.split()
    # same last name + same first initial (e.g. "S. Murphy" ~ "Sean Murphy")
    if pa and pb and pa[-1] == pb[-1] and pa[0][0] == pb[0][0]:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= NAME_MATCH_RATIO


def email_matches_name(email, name):
    """Does the email's local-part corroborate the resolved name? (karen@ ~ Karen Liu)"""
    if not email or not name:
        return False
    local = email.split("@")[0].lower()
    tokens = [t for t in norm_name(name).split() if len(t) >= 3]
    return any(t in local for t in tokens)


def role_rank(role):
    if not role:
        return 0
    r = role.lower().strip()
    if r in NON_DECISION_ROLES:
        return -1
    return ROLE_PRIORITY.get(r, 0)


# --- core: resolve one company ---------------------------------------------
def resolve(company, providers):
    reasons, sources_used, provenance = [], [], []
    registry = providers.get("registry")
    listing = providers.get("listing")
    enrichment = providers.get("enrichment")

    # 1. resolve the decision-maker NAME (registry > listing) ----------------
    name, role, registry_name = None, None, None
    if registry and registry.get("name"):
        if role_rank(registry.get("role")) == -1:
            reasons.append("registry returned a registered agent, not a decision-maker (name discarded)")
        else:
            name, role, registry_name = registry["name"], registry.get("role"), registry["name"]
            sources_used.append("registry")
            provenance.append(registry.get("source_url"))
            reasons.append(f"registry name '{name}' (role: {role})")

    listing_name = listing.get("name") if listing else None
    if listing_name and name is None:
        name = listing_name
        sources_used.append("listing")
        provenance.append(listing.get("source_url"))
        reasons.append(f"listing name '{name}' (no role)")

    # 2. corroboration: do independent name sources agree / conflict? --------
    agreeing = False
    if registry_name and listing_name:
        if same_person(registry_name, listing_name):
            agreeing = True
            if "listing" not in sources_used:
                sources_used.append("listing")
                provenance.append(listing.get("source_url"))
            reasons.append(f"independent sources agree on the name ({registry_name} ~ {listing_name})")
        else:
            reasons.append(f"sources CONFLICT on the name ({registry_name} vs {listing_name}) -> not corroborated")

    # 3. resolve a reachable, attributable CONTACT (email preferred) ---------
    contact, prov_conf = "", 0
    if enrichment:
        prov_conf = enrichment.get("provider_confidence") or 0
        if enrichment.get("email"):
            contact = enrichment["email"]
            sources_used.append("enrichment")
            provenance.append(enrichment.get("source_url"))
            reasons.append(f"enrichment email (provider_confidence {prov_conf})")
        elif enrichment.get("phone"):
            contact = enrichment["phone"]
            sources_used.append("enrichment")
            provenance.append(enrichment.get("source_url"))
            reasons.append(f"enrichment phone (provider_confidence {prov_conf})")
    if not contact and listing and listing.get("phone"):
        contact = listing["phone"]
        if "listing" not in sources_used:
            sources_used.append("listing")
            provenance.append(listing.get("source_url"))
        reasons.append("listing phone")

    # 4. explainable confidence score ---------------------------------------
    score = 0
    if name:
        score += 20  # we have a candidate name
        if registry_name:
            score += 10  # ...from the authoritative source
        rr = role_rank(role)
        if rr >= 4:
            score += 25; reasons.append("name has a payment-capable role (owner/founder tier)")
        elif rr == 3:
            score += 20; reasons.append("name has a finance role")
        elif rr == 2:
            score += 8;  reasons.append("name has only a manager/fallback role")
        if agreeing:
            score += 25; reasons.append("+ corroborated by a second independent source")
        elif email_matches_name(contact, name):
            score += 12; reasons.append("+ enrichment email corroborates the name")
        elif registry_name and not listing_name:
            score -= 5;  reasons.append("single uncorroborated name source")
    if contact:
        score += 15
        score += min(prov_conf, 100) * 0.10  # blend (not equal to) provider's self-confidence
        reasons.append(f"reachable contact present (+enrichment self-confidence {prov_conf})")
    else:
        reasons.append("no reachable contact channel")
    if name is None and contact:
        score -= 10; reasons.append("contact found but no named decision-maker")
    if not providers:
        reasons.append("no provider returned anything (cannot verify)")

    score = max(0, min(100, round(score)))
    needs_review = (score < CONFIDENCE_THRESHOLD) or (not contact) or (name is None)

    return {
        "company_name": company,
        "contact_name": name or "",                       # kept as a lead even on review rows
        "contact_role": role or "",
        "contact_email_or_phone": "" if needs_review else contact,  # never emit below threshold
        "confidence_score": score,
        "source": "+".join(dict.fromkeys(sources_used)) or "none",
        "needs_human_review": needs_review,
        "provenance": " | ".join(p for p in dict.fromkeys(provenance) if p),
        "reasons": "; ".join(reasons),
    }


# --- run --------------------------------------------------------------------
def main():
    with open(MOCK_PATH, encoding="utf-8") as f:
        mock = json.load(f)

    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            company = r["company_name"]
            if company in SUPPRESSION_LIST:
                rows.append({
                    "company_name": company, "contact_name": "", "contact_role": "",
                    "contact_email_or_phone": "", "confidence_score": 0,
                    "source": "suppressed", "needs_human_review": True,
                    "provenance": "", "reasons": "company on opt-out/suppression list",
                })
                continue
            rows.append(resolve(company, mock.get(company, {})))

    os.makedirs(OUT_DIR, exist_ok=True)
    fields = ["company_name", "contact_name", "contact_role", "contact_email_or_phone",
              "confidence_score", "source", "needs_human_review", "provenance", "reasons"]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # readable summary
    emitted = [r for r in rows if not r["needs_human_review"]]
    review = [r for r in rows if r["needs_human_review"]]
    print(f"\nProcessed {len(rows)} companies -> wrote {OUT_PATH}")
    print(f"  contact found (>= {CONFIDENCE_THRESHOLD}): {len(emitted)}")
    print(f"  needs human review:        {len(review)}\n")
    print(f"{'COMPANY':<30} {'NAME':<18} {'CONTACT':<34} {'SCORE':>5} {'REVIEW':>7}")
    print("-" * 98)
    for r in rows:
        print(f"{r['company_name']:<30.29} {r['contact_name']:<18.17} "
              f"{(r['contact_email_or_phone'] or '-'):<34.33} "
              f"{r['confidence_score']:>5} {str(r['needs_human_review']):>7}")


if __name__ == "__main__":
    main()