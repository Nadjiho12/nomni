# Marketing and digital products

*Last updated: 2026-10-13 | Version-sensitive: benchmarks, platform fees, ad costs, legal/advertising rules | Re-check current docs before pinning versions, prices, or API names.*

Covers strategy, ideas, analysis, structure plans, management, and risk for digital products (software, apps, games, courses, ebooks, templates, plugins, communities, marketplaces, APIs, content businesses) and for marketing any product. Helper: `scripts/biz_calc.py` (RICE scoring, risk register, unit economics, break-even, runway, decision matrix).

Evidence rule: market sizes, benchmarks, competitor facts, and prices change and are easy to get wrong. Use web search when available and cite; otherwise label numbers **assumption** or **rule of thumb (verify)**. Never invent statistics, quotes, or case studies.

## Contents
1. Workflow
2. Customer and problem validation
3. Positioning and value proposition
4. Market and competitor analysis
5. Digital product structure
6. Pricing and monetization
7. Unit economics
8. Go-to-market plan
9. Channels and funnel
10. Management system
11. Risk management
12. Analytics and experiments
13. Structure plans and templates
14. Ethics and compliance
15. Verification

## 1. Workflow

Customer → problem → solution → positioning → pricing → channel → launch → measure → iterate. Strategy before tactics: do not write ads or build features before the buyer, problem, and promise are clear. When the user gives few details, deliver the full plan with stated assumptions (see `thinking/ideas-critical.md`, default-to-architecture rule).

## 2. Customer and problem validation

- **Segment**: who exactly (role, context, trigger event), not "everyone".
- **Jobs to be done**: `When [situation], I want to [motivation], so I can [outcome]`.
- **Problem test**: is it frequent, painful, and already costing money or time? Do people use workarounds or pay for substitutes? Workarounds are the strongest signal.
- **Interviews** (talk about their past behavior, not your idea): "Tell me about the last time you [did X]." "What did you try?" "What did it cost?" "What happened next?" Avoid "Would you use...?" and pitching. 8-15 interviews per segment reveal patterns.
- **Cheap tests before building**: landing page with email capture or waitlist, fake-door button, concierge/manual delivery, pre-sales, prototype or clickable mock, small paid ad test for demand.
- **Validation ladder (weak → strong)**: opinions < email signups < deposits/pre-orders < paid usage < repeat usage/referrals.

## 3. Positioning and value proposition

Positioning statement: `For [target] who [need], [product] is a [category] that [key benefit]. Unlike [alternative], it [differentiator], proven by [evidence].`
Build it from: competitive alternatives (including "do nothing" and spreadsheets) → unique attributes → value those attributes create → who cares most → category frame.
Value proposition test: specific, outcome-first, believable, different. Headline formula: outcome + for whom + how/time (`Ship a playable game in 7 days, no coding`).
Messaging hierarchy: one promise → three proof points → objections answered → one call to action. Use the customer's words from interviews and reviews.

## 4. Market and competitor analysis

- **Market size**: bottom-up beats top-down. `SAM = reachable customers × price × purchase frequency`; `SOM = realistic share in 12-24 months` from channel capacity. Show formulas and assumptions; do not quote a giant "TAM" without a basis.
- **Competitor matrix**: rows = competitors (direct, indirect, substitutes); columns = target, core promise, price, strengths, weaknesses, channels, reviews' common complaints. Find the gap customers complain about.
- **SWOT** (internal strengths/weaknesses, external opportunities/threats), **PESTEL** (political, economic, social, technological, environmental, legal), **Porter's five forces** (rivalry, new entrants, substitutes, buyer power, supplier power). Use them to produce decisions, not lists.
- **Positioning map**: two axes customers care about (for example price vs depth); look for empty, valuable space.
- **Review mining**: read 1-3 star reviews of competitors and forum threads; cluster complaints; count frequency.
- **Trend check**: search interest, community activity, platform policy changes; flag fads vs durable demand.

## 5. Digital product structure

| Type | Typical MVP | Watch for |
|---|---|---|
| SaaS / web app | One core workflow, auth, billing, onboarding | Churn, support load, security |
| Mobile app | Single job done well, offline behavior | Store rules, retention, permissions |
| Game | Core loop vertical slice, one monetization hook | Retention curve, content cost, platform fees |
| Course / ebook | Outline + 1-2 modules/chapters + sample, pre-sold | Completion rate, outdated content |
| Template / asset pack / plugin | 5-10 high-quality items, clear license | Piracy, support, marketplace fees |
| Community / membership | Seed with 20-50 engaged members, weekly ritual | Moderator burnout, engagement decay |
| Marketplace | Solve supply or demand first (cold start) | Disintermediation, trust and safety |
| API / dev tool | Docs, SDK, quickstart under 10 minutes | Reliability, versioning, pricing by usage |
| Content / newsletter | Consistent niche, repeatable format | Audience ownership, monetization lag |

**MVP definition**: smallest thing that tests the riskiest assumption with real users. List assumptions, rank by (impact if wrong × uncertainty), test the top one first.
**Roadmap**: Now / Next / Later (outcomes, not features), reviewed monthly. **Prioritization**: RICE (`Reach × Impact × Confidence / Effort`), ICE, MoSCoW (Must/Should/Could/Won't), Kano (basic/performance/delight), value-vs-effort grid. Compute with `biz_calc.py rice`.
**Build vs buy vs no-code**: buy or no-code for non-differentiating parts; build what makes the product different. Record the decision and the trigger to revisit.
**Product-market fit signals**: retention curve flattens, users would be very disappointed without it (survey ≥ 40% "very disappointed" is a common heuristic, verify), organic referrals, sales cycle shortens.

## 6. Pricing and monetization

Models: one-time purchase, subscription, freemium, free trial, usage-based, tiered (good/better/best), pay-what-you-want, marketplace fee/commission, ads, sponsorship, affiliate, licensing, services around the product, donations. Games: premium, ads, in-app purchases, battle pass (state ethical limits; no manipulative mechanics aimed at children).
Methods: **value-based** (price as a share of the value delivered), competitor-anchored, cost-plus (floor only), willingness-to-pay research (Van Westendorp questions: too cheap / bargain / getting expensive / too expensive).
Tactics: 3 tiers with the middle as the target; annual discount; anchor with a premium tier; limit by value metric (seats, projects, usage) that scales with customer value; grandfather early users; test price with new traffic, not by silently changing existing customers' prices.
Check: price covers costs plus margin and CAC (see unit economics); free tier must not cost more than it converts.
Compare price points with `python scripts/biz_calc.py pricing --prices 5,9,15,19 --base-price 9 --base-conv 0.01 --visitors 2000 --ad-spend 300 --cpc 0.8 --churn 0.08 --elasticity -1.0`. It models conversion as `(price/base)^elasticity`: at -1.0 revenue is neutral across prices, above that (for example -0.5) higher prices win, below that (-1.5) lower prices win. Elasticity is an assumption, so always rerun at -0.5 / -1.0 / -1.5, state that the answer depends on it, and recommend a real split test (new visitors see different prices; keep existing customers' prices stable). When search tools exist, look up 2-3 comparable products' public prices and cite them; otherwise mark competitor prices **open gap**.

## 7. Unit economics

```
ARPU = revenue / active customers (per month)
Gross margin = (revenue - COGS) / revenue
Churn = customers lost per month / customers at start
LTV = ARPU × gross margin / churn
CAC = total acquisition spend / new customers
Payback (months) = CAC / (ARPU × gross margin)
LTV:CAC rule of thumb ≥ 3, payback under 12 months (verify per business model)
Break-even units = fixed costs / (price - variable cost per unit)
Runway (months) = cash / monthly net burn
```
Run: `python scripts/biz_calc.py unit --arpu 12 --gross-margin 0.8 --churn 0.05 --cac 40`. Sanity-check: do churn and CAC assumptions come from data or guesses? Label them. Sensitivity: show the result at ±30% on the two most uncertain inputs.

## 8. Go-to-market plan

One-page GTM:
```
Target segment & trigger event:
Positioning statement:
Offer & price:
Primary channel (1) and secondary (1-2):
Launch sequence: T-4w seed audience → T-2w waitlist/teasers → T-0 launch → T+1w follow-ups → T+4w review
Assets: landing page, demo, onboarding emails (3-5), social posts, FAQ, press/community posts
Budget & time per channel:
Targets (leading + lagging): visitors → signups → activation → paid
Owner per task & dates:
Risks and contingency:
```
Launch ideas: build in public, waitlist with a referral reward, beta cohort with testimonials, Product Hunt/community launches (follow rules), partnerships/co-marketing, free tool as lead magnet, comparison and "alternative to X" pages, launch-day live demo. Focus on **one** primary channel until it works.

## 9. Channels and funnel

AARRR funnel: Acquisition → Activation (first value moment) → Retention → Revenue → Referral. Find the weakest step and fix it before pushing more traffic.

| Channel | Best for | Cost | Time to results |
|---|---|---|---|
| SEO / content | Search-intent problems | Time | Months |
| Social / short video | Visual, consumer, personality-led | Time | Weeks, volatile |
| Email | Owned audience, conversion | Low | Compounds |
| Communities (forums, Discord, subreddits) | Niche products | Time, trust | Weeks |
| Paid ads | Validated offer, fast tests | Money | Days |
| Partnerships / affiliates | Complementary audiences | Revenue share | Weeks |
| Marketplaces / app stores | Discovery inside a platform | Fees | Varies |
| Outbound sales | High-priced B2B | Time | Weeks |

Pick channels by audience presence, your strengths, and cost per learning cycle (ICE score). Landing page checklist: headline promise, subhead, one visual/demo, 3 benefits, proof, one CTA, FAQ, trust signals, fast and mobile-friendly. Email onboarding: welcome (value + first step) → quick win → social proof → objection handling → offer.

## 10. Management system

- **Goals**: OKRs (1-3 objectives, 2-4 measurable key results per quarter).
- **Cadence**: daily 10-minute focus list; weekly review (metrics, blockers, next week's top 3); monthly roadmap/strategy review; quarterly OKR reset and retrospective.
- **Work flow**: Kanban (Backlog → Doing (WIP limit 3) → Review → Done) or 1-2 week sprints.
- **Roles**: RACI per initiative (Responsible, Accountable, Consulted, Informed); one accountable owner per task.
- **Decision log**: date, decision, options, reason, owner, revisit trigger.
- **Budget**: monthly plan vs actual, 10-20% reserve, track cost per channel.
- **Team**: first hires by bottleneck (build, sell, support); document processes (checklists/runbooks) before delegating; contractors for spiky work.
- **Stakeholder map**: power vs interest grid, communication plan per group.
- **Weekly report template**: Wins · Metrics (this vs last week) · Problems · Decisions needed · Next week's top 3.

## 11. Risk management

Register fields: ID · risk · category · likelihood (1-5) · impact (1-5) · score (L×I) · mitigation · contingency · owner · early-warning trigger · status. Run: `python scripts/biz_calc.py risk --file risks.csv`.

Categories to scan: market (no demand, competitor response), product (core assumption false, quality), technical (scalability, security, vendor lock-in), platform/dependency (API/policy changes, app store rejection, ad account bans), financial (runway, price too low, payment disputes), legal/compliance (privacy, IP/licensing, advertising claims, taxes, consumer law), operational (single point of failure, burnout), reputation (reviews, security incident), people (key person loss).

Methods:
- **Pre-mortem**: assume it failed in 12 months; list why; convert causes into mitigations.
- **Scenarios**: best/base/worst with numeric assumptions and decision triggers.
- **Kill criteria**: write in advance (`If fewer than 3% of visitors sign up after 500 visitors, change the offer`; `if CAC payback stays above 18 months for 3 months, stop this channel`).
- **Reduce risk cheaply**: smaller experiments, pre-sell, stagger spending, diversify channels and platforms, keep backups and exportable data, contracts and licenses in writing.

## 12. Analytics and experiments

- **North star** (one metric tied to delivered value) + input metrics (a metric tree). Track leading indicators (activation, weekly active) before lagging (revenue).
- **Cohort retention**: share of each signup week still active at weeks 1, 4, 8; a flat tail means a core audience.
- **Funnel**: conversion at each step; measure by source.
- **A/B tests**: one change, pre-state the metric and minimum effect, decide sample size in advance (rough: small lifts need thousands of visitors per variant), do not stop at the first "win", beware multiple comparisons. For tiny traffic, use qualitative tests (5-8 user sessions) instead.
- **Surveys**: short, one question per metric, avoid leading wording.
- **Dashboards**: one page, weekly numbers, trend vs target.

## 13. Structure plans and templates

**Lean Canvas**: Problem · Customer segments · Unique value proposition · Solution · Channels · Revenue streams · Cost structure · Key metrics · Unfair advantage.
**One-page business plan**: Summary · Problem · Solution · Market · Competition & differentiation · Model & pricing · GTM · Operations & team · Financials (12-month, assumptions listed) · Risks · Milestones · Ask.
**30/60/90 plan**: 30 = validate (interviews, landing page, prototype); 60 = build/pilot (MVP, first users, first revenue); 90 = launch and learn (channel focus, pricing test, retention check).
**12-month roadmap**: quarter themes with measurable outcomes.
**Pitch outline (10 slides)**: problem · solution · demo · market · model · traction · GTM · competition · team · ask.
**Org structure (small team)**: product/engineering, growth/marketing, operations/support; document who owns what.
Copywriting for launch posts, emails, and landing pages: see `writing/styles.md`.

## 14. Ethics and compliance

No fake reviews or testimonials, no invented scarcity or fake countdowns, no hidden fees or dark patterns, no unsubstantiated health/financial/performance claims, clear ad and affiliate disclosures, honor opt-outs. Respect privacy law (consent, data minimization, deletion on request; GDPR/CCPA-style rules where they apply), platform rules, trademark and copyright/licensing. Verify tax, consumer-protection, and payment rules for the user's country and for buyers' countries with a qualified professional; this skill is not legal or financial advice.

## 15. Verification

Recompute every number with `biz_calc.py` or a script; mark each figure as data, assumption, or rule of thumb; check that the plan has one owner, one date, and one metric per action; confirm risks have triggers and mitigations; cite sources for market facts or label them without evidence; confirm the plan answers the user's goal, not just a generic template.

## 16. Related

Choose and defend the model: `business/models-strategy.md`. Money, sales, support, operations, legal basics, KPIs, fundraising: `business/operations-finance.md`. Numbers: `scripts/biz_calc.py` (`unit`, `pricing`, `forecast`, `risk`, `rice`, `matrix`). Ideas with evidence: `thinking/ideas-critical.md`.
