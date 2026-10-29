# Business models and strategy

*Last updated: 2026-10-13 | Version-sensitive: market data and platform policies | Re-check current docs before pinning versions, prices, or API names.*

How to choose, test, and defend a business model for digital products and services. Pair with `marketing-products.md` (customer, positioning, pricing, GTM, risk) and `operations-finance.md` (money, sales, support, operations). Numbers: `scripts/biz_calc.py`.

## Contents
1. Business model types
2. Choosing a model
3. Business model canvas and one-page strategy
4. Moats and defensibility
5. Strategy frameworks that earn their keep
6. Validation stages
7. Growth paths: bootstrap, funded, studio, agency
8. Platform and dependency strategy
9. Digital products specifics (games, apps, content, AI)
10. Pivot, persevere, or stop
11. Partnerships and channels
12. Strategy review checklist

## 1. Business model types

| Model | How it earns | Strengths | Watch for |
|---|---|---|---|
| SaaS subscription | Recurring fee per seat/usage | Predictable revenue, compounding | Churn, CAC payback, support load |
| Usage-based / API | Pay per call or unit | Aligns price with value | Revenue volatility, cost spikes |
| Marketplace | Commission on transactions | Network effects | Cold start, disintermediation, trust and safety |
| E-commerce / DTC | Margin on goods | Clear unit economics | Inventory, ads costs, returns, shipping |
| Digital products (templates, courses, ebooks, assets) | One-time sales | Low cost, high margin | Traffic dependence, piracy, refunds |
| Games | Premium, ads, IAP, subscriptions | Large audiences | Retention, hit-driven, platform fees |
| Content / media / newsletter | Ads, sponsorship, memberships | Owned audience compounds | Slow start, platform algorithms |
| Services / agency / freelance | Time or project fees | Cash flow fast, low capital | Doesn't scale, feast/famine, client concentration |
| Productized service | Fixed-scope service at fixed price | Repeatable, higher margins | Scope creep, delivery capacity |
| Consulting / expert advisory | Rates/retainers | High margin, credibility | Time-bound, reputation-dependent |
| Licensing / white label | Fees for using your IP | Leverage | Few big customers, enforcement |
| Hardware / physical + software | Device margin + recurring | Defensible bundle | Capital, supply chain, support |
| Open core / open source + services | Support, hosting, enterprise features | Distribution | Monetization friction, forks |
| Affiliate / lead-gen | Referral fees | Low cost | Dependence on partners and search |
| Local / operations business | Service to a geography | Proven demand | Hiring, operations, margins |

## 2. Choosing a model

Score candidate models (`scripts/biz_calc.py matrix`) on: time to first revenue, capital needed, skills fit, margin, scalability, defensibility, market access, risk. Useful defaults:
- Little money, need cash soon: productized service or freelance → fund a product.
- Strong skills, repeatable pain, time to build: SaaS or tool with a narrow niche.
- Audience first: content/newsletter → products and sponsorships.
- Highly creative, hit-driven: games with small scope and a marketing plan from day one.
- Technical depth in security/AI: productized audits, tools with usage-based or subscription pricing, training content.
Combine: services fund the product; the product reduces service load; content feeds both.

## 3. Business model canvas and one-page strategy

Canvas blocks: customer segments · value propositions · channels · customer relationships · revenue streams · key resources · key activities · key partners · cost structure.
One-page strategy: **Where to play** (segment, geography, product scope) · **How to win** (unique value, moat) · **What must be true** (3-5 assumptions with tests) · **Capabilities needed** · **Metrics and targets** · **Risks and kill criteria** · **Next 90 days**. Review quarterly.

## 4. Moats and defensibility

Network effects (value grows with users) · switching costs (data, workflows, integrations, habits) · proprietary data or feedback loops · brand and trust · scale economies · distribution advantage (audience, partnerships) · regulatory/licensing · speed and execution · specialized expertise. Early on, the realistic moat is **focus and speed in a niche**; record which moat you are building and how you will know it is working. In AI products, model access alone is not a moat (everyone has it): defensibility comes from workflow integration, proprietary data and evaluations, distribution, and trust.

## 5. Strategy frameworks that earn their keep

- **Jobs to be done:** what progress is the customer trying to make, and what do they currently hire instead?
- **Value proposition fit:** pains → pain relievers; gains → gain creators; test with real customers.
- **Blue Ocean ERRC grid:** Eliminate, Reduce, Raise, Create factors versus competitors to find uncontested space.
- **Porter's five forces / SWOT / PESTEL:** use to produce decisions, not lists (`marketing-products.md`).
- **Wardley-style evolution:** is the component genesis, custom, product, or commodity? Build what differentiates; buy commodities.
- **Unit economics first:** if a unit loses money and cannot improve, scale amplifies losses.
- **Second-order thinking and pre-mortems** (`thinking/ideas-critical.md`).
- **OODA loops/fast learning cycles:** the team that tests more cheap hypotheses wins early.
- **Rule of one:** one segment, one channel, one core promise until it works.

## 6. Validation stages

| Stage | Question | Evidence | Typical cost |
|---|---|---|---|
| Problem | Does the pain exist and cost money/time? | 10-15 interviews, existing workarounds | Days |
| Demand | Will people pay or commit? | Waitlist conversion, pre-orders, paid pilot | 1-3 weeks |
| Solution | Does the MVP deliver the outcome? | Users reach value; qualitative feedback | 2-8 weeks |
| Retention | Do they come back / not churn? | Flat retention curve, repeat usage | 1-3 months |
| Acquisition | Can you get customers at a profitable cost? | CAC payback in range on one channel | 1-3 months |
| Scale | Can operations/support keep up? | Margins hold, SLAs met | Ongoing |
Move forward only when the current stage has real evidence; going back is cheaper than building on a false assumption.

## 7. Growth paths

- **Bootstrapped:** revenue funds growth; keep burn low; slower, more control; ideal for niche SaaS, tools, content, services.
- **Funded (VC):** needs a large market and very fast growth; trade ownership for speed; metrics investors expect (growth rate, retention, margins, market size). Do not raise to validate; raise to scale proven loops.
- **Studio/portfolio (games, apps):** many small bets with shared tooling; kill fast, double down on winners; track cost per prototype and hit rate.
- **Agency to product:** use client work to find repeated needs; productize the most repeated deliverable; protect capacity for product work.
- **Creator/community-led:** audience first, then products; own the email list.

## 8. Platform and dependency strategy

Platforms (app stores, ad networks, social algorithms, marketplaces, API providers, cloud hosts) can change terms or ban accounts. Mitigate: multi-channel acquisition, own your audience (email list, community), exportable data and portable code, contractual protections for key vendors, fallbacks for critical APIs, ads-off or alternate monetization paths, keeping platform fees in the unit economics. Track concentration: no single platform above about 40-50% of revenue or traffic without a plan.

## 9. Digital products specifics

- **Games:** expected value is hit-driven; fund through scope control (`games/production.md`), wishlists/community before launch, platform choice by audience, monetization that respects players (no manipulative mechanics aimed at children).
- **Apps:** retention is the business; build onboarding to first value, push notifications with consent, subscription management with clear cancellation.
- **Courses/ebooks/templates:** sell outcomes, not content; cohort or support tiers raise value; keep content current; license terms clear; expect piracy and focus on service and updates.
- **Content/newsletters:** consistency, niche authority, owned list; monetize with sponsorships (clear disclosure), memberships, products.
- **AI products:** unit economics include inference cost per use; set usage limits and tiers, cache and route to cheaper models, measure quality with evals, be transparent about limits, handle data privacy contractually, and plan for model/provider changes (`ai/architecture.md`).
- **Security/consulting products:** trust and proof matter: case studies (anonymized with permission), certifications, clear scopes, rules of engagement, insurance and contracts, authorized-only work.

## 10. Pivot, persevere, or stop

Decide on evidence at pre-agreed checkpoints. **Persevere** if leading metrics improve (activation, retention, referrals) and learning continues. **Pivot** (change segment, problem, channel, price, or model) when you have strong evidence the current path fails but you found a pull signal elsewhere. **Stop** when kill criteria hit and no pull signal exists. Write the criteria in advance (for example "fewer than 3% visitor-to-signup after 500 visitors and 3 offer changes") and the decision date; use `biz_calc.py runway` to bound the time you can afford.

## 11. Partnerships and channels

Look for partners that already own your audience and do not compete (tools, communities, creators, agencies, marketplaces). Offer clear mutual value (revenue share, co-marketing, integrations). Start with one pilot partner and a written one-page agreement (scope, split, exclusivity, term, exit). Measure partner-sourced CAC and retention separately.

## 12. Strategy review checklist

- [ ] Customer segment specific; problem validated with evidence
- [ ] Model chosen with a scored comparison; unit economics computed with labeled assumptions
- [ ] Moat identified and a way to tell if it is forming
- [ ] Three to five "must be true" assumptions with tests and dates
- [ ] Platform/customer concentration risks and mitigations listed
- [ ] Kill/pivot criteria and decision dates written
- [ ] 90-day plan with owners, metrics, and budget
