# Operations, finance, sales, and support

*Last updated: 2026-10-13 | Version-sensitive: tax, legal, and payment rules by country; tool pricing | Re-check current docs before pinning versions, prices, or API names.*

Run the business side with clarity. Not legal, tax, or financial advice: confirm rules for your country and situation with qualified professionals. Calculator: `scripts/biz_calc.py` (`unit`, `pricing`, `forecast`, `breakeven`, `runway`, `risk`).

## Contents
1. Finance basics
2. Budgeting and forecasting
3. Pricing for margin and invoicing
4. Sales
5. Customer success and support
6. Operations and systems
7. People: hiring and contractors
8. Legal and compliance basics
9. Fundraising and funding options
10. KPI dashboards by model
11. Reporting cadence
12. Risk and continuity
13. Checklist

## 1. Finance basics

- **P&L (income statement):** revenue − cost of goods/services (COGS) = gross profit; − operating expenses = operating profit; − taxes/interest = net profit.
- **Cash flow:** cash in minus cash out. Profit is not cash: invoices unpaid, annual prepayments, inventory, and taxes shift timing. Watch cash weekly.
- **Balance sheet:** assets, liabilities, equity; useful for loans/investors.
- **Key ratios:** gross margin, net margin, burn (monthly net cash outflow), runway (cash / burn), customer acquisition cost (CAC), lifetime value (LTV), payback period, revenue per employee.
- **Cash vs accrual:** small businesses often use cash accounting; know which your jurisdiction allows.
- Separate business and personal money; track every transaction; reconcile monthly; keep receipts; set aside a tax percentage of each payment.

## 2. Budgeting and forecasting

Build a 12-month model with: starting cash, customers or sales per month, price, churn, COGS or gross margin, acquisition spend, fixed costs, taxes. Run it: `python scripts/biz_calc.py forecast --months 12 --new-per-month 20 --growth 0.05 --churn 0.05 --arpu 12 --gross-margin 0.85 --fixed 800 --cac 25 --cash 3000`. Read: the month cash is lowest (the funding you need), the break-even month, and what happens at worse churn/CAC. Make three scenarios (base, pessimistic, optimistic) and decide triggers ("if cash < 3 months of burn, cut X"). Keep a reserve of 3-6 months of fixed costs where possible. Compare actuals to forecast monthly and update assumptions.

## 3. Pricing for margin and invoicing

- Price from value and costs: cost floor (COGS + support + payment fees + platform fees + tax), competitor range, customer value; target gross margin (software 70-85%+, services 40-60%, physical products 30-60%; rough ranges, verify for your sector).
- Include payment fees (typically a few percent plus a fixed fee), refunds/chargebacks, and platform commissions in unit economics.
- Services: price by project or value, not hours when possible; scope with deliverables, exclusions, revision limits, timeline, acceptance criteria; 30-50% deposit; milestones; late fees; written change orders.
- Invoices: number, date, parties, scope, amount, tax, due date, payment methods; send promptly; follow up on a schedule (day 1 after due, day 7, day 14); keep a receivables list.
- Subscriptions: clear billing dates, dunning emails for failed cards, easy cancellation, prorations rules, annual discounts that improve cash.

## 4. Sales

- **Funnel:** lead → qualified → discovery call → proposal → close → onboarding. Track conversion per stage and cycle time.
- **Qualification (BANT/MEDDIC-lite):** budget, authority, need, timeline; also "what happens if they do nothing?"
- **Discovery call (30 min):** 5 min context; 15 min questions (current process, pain, cost of pain, previous attempts, decision process, success definition); 5 min summary; 5 min next step. Listen more than talk; quote their words in the proposal.
- **Outreach (ethical, relevant):** short message that references their situation, one clear value, one low-friction ask. Follow up 2-3 times over two weeks; stop when asked; follow anti-spam and privacy rules (consent, opt-out).
```
Subject: Question about <specific thing you noticed>
Hi <Name>, I saw <specific observation>. Teams like yours often struggle with <problem> and lose <cost>.
I help with <outcome> in <timeframe>. Worth a 15-minute call this week?
```
- **Demos:** start from their problem, show the shortest path to value, end with the next step.
- **Objections:** price (re-anchor to value and cost of inaction; offer tiers, not discounts), timing (what changes by waiting?), trust (references, pilot, guarantee), competitor (clarify the job to be done).
- **Proposals:** one page of outcome, scope, timeline, price options (good/better/best), terms, next step; send within 24 hours; follow up.
- **CRM hygiene:** every lead has a next action and date; update after every touch; review pipeline weekly; weigh pipeline by stage probability.
- Sales ethics: no false claims, no pressure tactics, honest limitations.

## 5. Customer success and support

- **Onboarding:** reach first value quickly: welcome message with one clear step, checklists, templates, short videos, a check-in at day 3 and day 14.
- **Support system:** shared inbox or helpdesk; response-time targets (for example under 24 h, faster for paid/urgent); macros for common answers; tag issues to find product problems; escalate bugs with repro steps.
- **Self-service:** searchable docs, FAQ, in-app tips; every repeated question becomes an article or product fix.
- **Retention:** monitor usage drops, send helpful nudges, exit surveys for cancellations, win-back flows; fix the top churn reasons.
- **Feedback loop:** NPS/CSAT sparingly, interviews with power users and churned users, a public roadmap or changelog.
- **Tone:** clear, human, accountable; own mistakes; do not blame users; refund fairly per policy.

## 6. Operations and systems

- Document repeatable processes as short SOPs/checklists (onboarding a customer, publishing a release, month-end close).
- Tool stack by function: accounting (QuickBooks/Xero/open source), payments (Stripe/PayPal/local processors), CRM (HubSpot free/Notion/Airtable), support (shared inbox/helpdesk), project management (Linear/Trello/Notion), communication, password manager, backups.
- Automate the repetitive (invoices, onboarding emails, reports) with scripts and no-code tools (`tools/automation.md`); keep a manual fallback.
- Security hygiene: MFA everywhere, least-privilege access, offboarding checklist, device encryption, regular backups.
- Vendor management: list contracts, renewal dates, and alternatives; avoid single points of failure.

## 7. People: hiring and contractors

Hire when a bottleneck is clear and recurring; start with part-time or contract for spiky work. Write a one-page role: outcomes in 90 days, skills, pay range, process. Work-sample tests over puzzle interviews. Clear contracts: scope, payment, IP assignment, confidentiality, termination. Onboard with a first-week plan and a buddy. Classify workers correctly under local law (employee vs contractor). Pay on time. Document decisions and give regular feedback.

## 8. Legal and compliance basics

- **Entity:** sole proprietor/freelancer, LLC/company types vary by country; liability, taxes, and credibility differ. Consult a local professional.
- **Contracts:** client agreements (scope, payment, IP, liability limits, confidentiality), terms of service, privacy policy, refund policy, NDA only when needed, contractor agreements.
- **IP:** who owns what; license third-party assets and code properly (keep a license list); trademark checks before branding; open-source license obligations.
- **Privacy/data:** collect minimum data, lawful basis/consent, retention and deletion, breach response plan; GDPR/CCPA-style rules where applicable.
- **Taxes:** register where required, collect and remit sales tax/VAT where applicable (digital goods rules differ by country), keep records; get an accountant early.
- **Advertising/consumer law:** truthful claims, disclosures for affiliates/sponsorships, clear pricing, cancellation rights.
- **Security-related work:** written authorization and scope for any testing, data handling terms, incident reporting duties.

## 9. Fundraising and funding options

Options: savings and revenue, pre-sales, customer-funded projects, grants, loans, revenue-based financing, angels, venture capital, crowdfunding. Choose by growth ambition and risk: do not raise venture capital for a small niche business. Prepare: a clear problem and market, traction metrics, unit economics, use of funds with milestones, a realistic plan. Investors look at team, market size, growth, retention, margins, and defensibility. Understand the terms (equity percentage, valuation, SAFE/convertible notes, pro-rata, liquidation preference, vesting) and get legal advice. Keep 12-18 months of runway after raising. Pitch outline in `marketing-products.md`.

## 10. KPI dashboards by model

| Model | Core KPIs |
|---|---|
| SaaS | MRR/ARR, new MRR, churn (logo and revenue), net revenue retention, CAC, LTV:CAC, payback, activation rate, support tickets per customer |
| E-commerce | Conversion rate, AOV, repeat purchase rate, CAC/ROAS, gross margin, return rate, inventory turns |
| Games | D1/D7/D30 retention, session length, ARPDAU, conversion to payer, crash-free rate, level funnel |
| Services/agency | Utilization, pipeline coverage (3x target), average project value, margin per project, DSO (days sales outstanding), client concentration |
| Content/newsletter | Subscribers, open/click rates, growth rate, revenue per subscriber, churn |
| Marketplace | GMV, take rate, liquidity (match rate), repeat rate, supply/demand balance |
Pick 5-7 KPIs, define each precisely (formula, source), show trend and target, and review weekly. Distinguish leading (activation, pipeline) from lagging (revenue, churn) indicators.

## 11. Reporting cadence

Weekly: cash, pipeline, top KPIs, blockers, top 3 priorities. Monthly: P&L vs budget, forecast update, channel performance, churn reasons, decisions needed. Quarterly: OKR review, strategy check (`models-strategy.md`), pricing and cost review, risk register update (`biz_calc.py risk`). Keep a decision log.

## 12. Risk and continuity

Concentration (one client, one channel, one platform) · key-person dependency (document processes, share access safely) · cash shocks (reserve, invoice terms) · security incidents (backups, MFA, incident plan) · supplier failure · legal/compliance lapses · burnout (sustainable pace, vacations planned). Maintain business continuity: password manager with emergency access, documented runbooks, offsite backups, insurance where appropriate.

## 13. Checklist

- [ ] Separate accounts; monthly reconciliation; tax set-aside; accountant identified
- [ ] 12-month forecast with scenarios; runway and low-cash month known
- [ ] Pricing covers all costs and margin target; payment and refund terms clear
- [ ] Sales process with stages, next actions, and weekly pipeline review
- [ ] Onboarding to first value; support SLAs; docs for top questions
- [ ] SOPs for the 5 most repeated processes; tool stack and access documented
- [ ] Contracts, policies, and license list in place; privacy handled
- [ ] KPI dashboard with definitions; weekly/monthly/quarterly cadence
- [ ] Concentration and key-person risks mitigated
