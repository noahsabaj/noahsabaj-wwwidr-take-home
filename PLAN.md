# PLAN.md

> We need to collect payment from ~1,000 unpaid small-business accounts. We only have their company_name and mailing_address. That's it. What do we do?

Brief note, I first consulted Claude Opus 4.8 on Max thinking mode before going anywhere beyond this initial point. 
I want to make sure that I follow the requirements correctly and author exemplary work.
If I refer to Claude, assume Claude Opus 4.8 on Max thinking mode.

If you handed an address to a human and instructed them to find who to email about their unpaid bill, I'd expect the human to google the company, find their website, click their about/contact page, find a name/email on that page, boom, found. If the human can't find it in about/contact/footer, put it on a check later list for businesses that require deep investigation.

But a human isn't doing this, a machine is!

## Architecture
The confidence_score represents how confident the system is about whether or not we have found a valid
employee/officer/owner that can manipulate their firm's financials (pay).

Insert a column (each row will use) boolean field. This column is titled "Human-review" with all fields
defaulting to no. This can change whether or not we need human review, later on.

1. Read and clean the CSV (parse company_name + address, and then normalize)
2. All sources go through a common interface with configurable parameters to reuse code and reduce duplication.
3. Free ones run in parallel first. Government business registration records, direct internet query. 
If all three agree, that's about as high as the confidence_score can be, we can reasonably say we found our 
person/people. If any disagree (2/3, 1/3, 0/3), we first determine if the disagreement exceeds the bounds of
entropy (records found a name, website also has name but unlabeled, or spelled slightly differently). If the disagreement exceeds the bounds of entropy, we must move to step 4.
4. Run paid searches following UNIX philosophy of least privilege first as to be conservative with money.
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

As an interesting project, we can design & train a next-action prediction model that studies the 
actions the humans take to find a person. We study how thehumans find people and train a model to do just 
that, in an effort to automate the process and remove that manual human checker from the loop, freeing up 
costs and labor for other endeavors. We can also operate a parallel data broker business, considering we are actively collecting names of employees at a business. (Legality above all)

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
1. In this example, if we use both the government records and a paid data service and they both agree on
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
Deduplication involves collecting the names from multiple sources, accounting for entropy (Jeremiah, 
Jeremia. Noah, Noa. Karoline, Caroline), combine into one record (use the source of higher authority).

Source authority hierarchy (Lower number, higher authority. Higher number, lower authority):
1. Government business registration record (assuming name matches what the internet search returned, 
otherwise it's likely a lawyer/filing agency and therefore not usable).
2. Paid service (internet search must corroborate or else this cannot be used alone).
3. Direct internet query.

confidence_score, the engine of this software.
Increases confidence score:
1. Independent sources agree on name (same name for government records, internet, and/or paid service).
2. This name has "Owner/CFO/AP Manager, Office Manager" sitting contextually with the name (contextually
meaning that this role is associated with this name).
3. Evidence trail (Providence). We track all sources and at what time they were discovered at. Insert this
into a new column into the respective row (what time the information was collected at for this business and 
where we got the info from).
4. No result (cannot verify),

## Privacy / compliance
Cannot scrape LinkedIn, their privacy policy prevents that.

## Clarifying questions
<!-- For EACH question: (a) why it matters, (b) your default assumption if unanswered, (c) what changes in your design depending on the answer. 3 sharp > 15 shallow. -->

1. **Question:**
   - Why it matters:
   - Default assumption:
   - What changes if answered: