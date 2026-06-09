# PLAN.md

> We need to collect payment from ~1,000 unpaid small-business accounts. We only have their company_name and mailing_address. That's it. What do we do?

Brief note, I first consulted Claude Opus 4.8 on Max thinking mode before going anywhere beyond this initial point. 
I want to make sure that I follow the requirements correctly and author exemplary work.
If I refer to Claude, assume Claude Opus 4.8 on Max thinking mode.

If you handed an address to a human and instructed them to find who to email about their unpaid bill, I'd expect the human to google the company, find their website, click their about/contact page, find a name/email on that page, boom, found. If the human can't find it in about/contact/footer, put it on a check later list for businesses that require deep investigation.

But a human isn't doing this, a machine is!

Bounds of entropy = fuzzy-match tolerance

## Architecture
The confidence_score represents how confident the system is about whether or not we have found a valid
employee/officer/owner that can manipulate their firm's financials (pay).

Insert a column (each row will use) boolean field. This column is titled "Human-review" with all fields
defaulting to no. This can change whether or not we need human review, later on.

1. Read and clean the CSV (parse company_name + address, and then normalize)
2. All sources go through a common interface with configurable parameters to reuse code and reduce duplication.
3. Free ones run in parallel first. Government business registration records, direct internet query. 
If both agree, that's about as high as the confidence_score can be, we can reasonably say we found our 
person/people. If any disagree, we first determine if the disagreement exceeds the bounds of
entropy (records found a name, website also has name but unlabeled, or spelled slightly differently). If the disagreement exceeds the bounds of entropy, we must move to step 4.
4. Run paid searches following cheapest-first as to be conservative with money.
If nothing comes back for the least amount of spending, judge whether or not an increase in spending would
yield an increase in the confidence_score. If yes, run the additional searches until the confidence_score
indicates a valid person found. If this step fails, then mark this person as currently unreachable by the
system.
5. If multiple candidate names return, create a new column for each respective business (row) of name
candidates. (John Hamilton, Alexandra Clark, Mike Mills).
6. For each row in the csv, assign it the cumulative confidence score. If the score is above our acceptance
threshold, then add the valid name to that row in a new Name/Officer/etc. column. If the score is below our
acceptance threshold, then promote to the human-review queue.
7. Unreachable people are promoted to the human-review queue (bool value in column for that row flipped to 
true). Humans will manually sift the internet (and other sources) for a valid name that matches that business. This method will likely have a high success rate but low speed and high cost.

(Future extension, out of scope for this slice)
As an interesting project, we can design & train a next-action prediction model that studies the 
actions the humans take to find a person. We study how the humans find people and train a model to do just 
that, in an effort to automate the process and remove that manual human checker from the loop, freeing up 
costs and labor for other endeavors.

## Sources & strategy
I consulted Claude on sources & strategy. Apparently each US state keeps a searchable database of registered
businesses. These occasionally list owners or officers. There are also paid data services that sell
business contact info (ZoomInfo, Apollo, Clearbit, and they're highly saturated). Claude asked me which one
I'd rather use, and it reminds me of my human approach earlier.

1. Use the government business registration records first. If we successfully find the owner/officers, we
can then hone in on their emails/phone numbers by cross-searching their names with the internet and finding
either their company page or some portal at which we can get a contact (social media). If
we cannot successfully find the owner/officers, then put this business in a "needs further investigation"
category where we attempt the paid data service route.
2. Paid data service route is the promotion step if the governmenty business registration record comes back
unpopulated. This should contain the contact information for the owner/officers which we can access 
directly.
As this is a promotion step, we try to exhaust free methods first.

How does the above strategy fail at each step?
1. The government registry frequently lists a registered agent. Typically a lawyer or a filing service, not
the owner. If you get an owner/officer name, great, keep digging on that name. A lawyer or filing service
is information but adds more steps to the chain. We should attempt another route.
2. Social media is hit or miss. You can ping for John Smith on LinkedIn and you'll get at least 5,000. Plus,
LinkedIn's privacy policy does not allow scraping (Claude informed me of this).
3. Paid services work very well for big/tech companies. Small, local companies, not so much. If any exists,
it is very likely to be stale. It will be confidently wrong with its return, a large number of times.

A single source doesn't cut it though. It fails almost every time, and even if it didn't fail often, the
times that it does is enough to warrant multiple attack patterns. Before getting into the multiple parallel
attack patterns, we should discuss conflict resolution first.
In this example, if we use both the government records and a paid data service and they both agree on
the same name, the confidence_score will increase. If they disagree, that's a red flag warranting case 
promotion.

Another free route we can (and should, this one is very useful) take is a direct internet query.
Take the business name, query the internet, filter by the top 10 results and identify whether any of the
results point to a valid website with a semantically similar name. If yes, check about/contact/footer, if 
we get a name and email &/ phone number then we can raise the confidence_score quite high. If no about/
contact/footer, try to find any name anywhere in the website and judge whether or not that name is the 
owner/officers. If no names can be found anywhere on the website, then switch to querying just the address. 
Google usually gives back locational results that map to businesses. If you search 415 Mission St, San 
Francisco, CA 94105, Google gives you back the Salesforce Tower (and businesses inside it). If we get a
business mapped to the address, and they have a website, check the website, same name search (about/footer/
contact/website-wide search), if no name comes back, try searching the internet with both the company_name
AND mailing_address in the query. The specificity will greatly reduce the amount of results, and if it's
not one of the 10 that comes back, it's probably not it. Same name search pattern on the website.

Name judgement is a confidence input. A name next to the word "Owner" or "CFO" or any other valid
payment-capable employee/officer raises the confidence significantly that the name we found is the valid
name of the payment-capable person. A random name with no association (for example, perhaps a customer
testimony) carries no-to-low confidence.

## Quality

**Dedupe.** Collect candidate names from every source. Treat small spelling differences as the same person 
(Jeremiah/Jeremia, Karoline/Caroline) via fuzzy matching, and merge them into one record, keeping the value 
from the highest-authority source (below). Never merge two *different* people who happen to share a name, 
same name ≠ same person.

**Source-authority hierarchy.** These sources don't sit on one trust axis, they do different jobs, so I 
split them.

For the name itself (who is tied to this business), highest to lowest authority:
1. **Government registration record**, but only when it names an actual owner/officer. If it only lists a 
registered agent (a lawyer or filing service), that is not our person, discard the name and rely on other 
routes.
2. **Paid data service**, trusted for a name, but never used alone, it's often stale or confidently wrong 
on small businesses, so it needs corroboration.
3. **Direct web/website result**, lowest authority on its own, since anyone can put a name on a page.

The web also plays a second, different role: corroboration. An independent web hit confirming the same 
name (ideally with a role) is what turns a single-source guess into a high-confidence match. So the web 
isn't validating a higher authority, it's a separate, independent data point, and agreement across 
independent sources is what drives the score up. When sources conflict on the name and nothing breaks the 
tie, that's a low-confidence row → human review, not a coin-flip.

**confidence_score** — the engine. A 0–100 number, and explainable: for any row I can say exactly why it 
scored what it did.

*Raises the score:*
- Independent sources agree on the same name (registry + web + paid all pointing to one person is about as 
high as it gets).
- The name sits next to a payment-capable role ("Owner," "CFO," "AP Manager," "Office Manager") — role 
context tied to that specific name.
- The contact channel was verified, not guessed — e.g., the email was confirmed deliverable, not just 
inferred from a company pattern.

*Lowers the score:*
- Only one source found the name (no corroboration).
- The email/phone was guessed from a pattern and never verified.
- The data looks stale (old filing, no recent web presence).
- The name has no role attached, or came from somewhere irrelevant (e.g., a customer testimonial).

**Provenance.** Every value we output records where it came from and when. For each row we log the 
source(s) and the timestamp the info was collected, so a human can later audit exactly why we believe a 
given contact.

**Cannot-verify.** When nothing checks out — no name, a name we can't corroborate, or no reachable + 
verified contact — we do not invent one. The row gets no contact, its human-review flag flips to true, 
and we note how far we got. "We don't know" is a valid, honest output.

**False-positive risk.** A wrong contact is worse than no contact — emailing the wrong person about a debt 
is a real liability. The system is deliberately biased toward human review over a confident guess: when in 
doubt, flag it.

## Privacy / compliance
Three primary categories:

1. **Will use:** Public/official records, respect each source's terms & robots.txt, collect only what's needed 
to make contact (data minimization), don't retain anything longer than necessary.
2. **Won't use:** Scraping sources that forbid it (LinkedIn is a good example), fabricate contacts, use
illegally-sourced data.
3. **Where debt collectors must be careful:**
- These are *business* (commercial) accounts, so the FDCPA — which protects *consumers* on personal/
household debts mostly does not apply to us. We shouldn't assume consumer-debt rules by default.
- Exception: some "small businesses" are sole proprietors, or the debt was personally guaranteed by the 
owner. There the business/consumer line blurs and consumer protections can apply, so verify the account 
type before assuming.
- Regardless of FDCPA: revealing that a debt exists to the wrong person is a risk on its own (a privacy 
problem, and in consumer cases an illegal third-party disclosure). This is the strongest reason to verify a 
contact before reaching out, a wrong contact isn't just useless, it can be a liability.
- GDPR applies to any non-US account (data subjects in the EU/UK), which raises the bar on consent, data 
minimization, and deletion.

## Clarifying questions
1. **Who exactly is the target contact, and is there a priority order (owner > AP > manager > office** 
**manager?):**
   - Why it matters: it changes which sources I lean on and how I can weight role-fit.
   - Default assumption: target whoever has payment authority. Prefer AP/billing, fall back to owner.
   - What changes if answered: the role-judgement weight in my confidence score, and which routes I run 
   first.

2. **Which sources are we permitted to use, and do we already have internal/licensed data? (CRM, client onboarding records, paid subscriptions, etc.):**
   - Why it matters: it sets both my compliance boundary (what I'm allowed to touch) and my strategy — if 
   we already hold a subscription or internal records, those are cheaper and higher-trust, so they jump to 
   the top of the waterfall.
   - Default assumption: only public/official records + public web search, no internal or licensed data, 
   and stay conservative with anything that has restrictive terms.
   - What changes if answered: if internal/licensed data exists, it becomes the first route and reorders 
   the whole pipeline; if certain sources are off-limits, I drop them and lean harder on the rest.

3. **What confidence threshold gates human review, and how costly is a wrong contact vs no contact?:**
   - Why it matters: it sets the single most important knob — the accept/reject boundary — and the 
   precision/recall lean of the whole system.
   - Default assumption: a wrong contact is worse than no contact (debt sent to the wrong party is a legal/
   reputational risk), so set a conservative threshold and bias toward human review.
   - What changes if answered: the threshold value itself, whether I auto-accept single-source matches at 
   all, and how hard I push rows to humans vs ship automatically.