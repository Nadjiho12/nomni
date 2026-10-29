# Writing: styles, voices, and templates

*Last updated: 2026-10-13 | Version-sensitive: none significant (craft) | Re-check current docs before pinning versions, prices, or API names.*

Use for any prose task. Every style below has: what it is, how to do it, a before/after or template, and pitfalls. For fiction and books read `writing/fiction-books.md` as well.

## Contents
1. Process
2. Human-sounding prose (with edit techniques)
3. Professional writing (templates)
4. Teaching and explaining (templates)
5. Persuasive and marketing
6. Technical writing and documentation
7. Stylish / literary nonfiction
8. Bot, robot, and persona voices
9. Social posts, bios, and short copy
10. Editing passes
11. Rules and limits
12. Verification

## 1. Process

1. **Brief**: audience, purpose, voice, length, format, must-include points, what the reader should do next.
2. **Voice match**: if "like me" or "like this sample", read the sample and note sentence length, vocabulary, punctuation habits, humor, and stance; state your read in one line, then write.
3. **Outline** anything over a page.
4. **Draft** fast.
5. **Edit** with the passes in section 10.
6. **Deliver** with the piece first, and offer one or two variants (shorter, warmer, more formal).

## 2. Human-sounding prose

Goal: natural, specific writing that reads like a person with a point of view. Not disguise; quality.

Techniques:
- **Start concrete.** A moment, a number, a name, a small scene.
- **Vary rhythm.** Long sentence, then a short one. Fragments are allowed.
- **Plain words.** "Use", not "utilize"; "help", not "facilitate".
- **Commit.** State the claim; hedge only where uncertainty is real.
- **Break symmetry.** Not every list has three items; not every paragraph ends on a moral; not every sentence has the same shape.
- **Add lived texture.** A specific detail only someone who was there would know.
- **Cut tells.** "In today's fast-paced world", "delve", "tapestry", "it's important to note", "game-changer", "not just X but Y" on repeat, reflexive triplets, tidy closing summaries, heavy em-dashes, stacked adjectives, mirrored sentence openings.

Before:
> In today's fast-paced digital landscape, it's important to note that effective time management is not just a skill but a game-changer for productivity, focus, and well-being.

After:
> I lost most of last year to a calendar I never looked at. The fix was boring: one list, checked every morning, and three things allowed on it.

Before (email):
> I hope this message finds you well. I wanted to reach out to touch base regarding the aforementioned project timeline.

After:
> Quick check on the timeline: are we still aiming for the 14th? If not, tell me what moved.

Pitfalls: over-correcting into forced quirkiness; inventing personal anecdotes for the user (use placeholders like `[your example here]` when a real detail is needed).

## 3. Professional writing

Principles: bottom line up front, one idea per paragraph, active verbs, numbers over adjectives, named owner and date for every action, no buzzwords.

**Email:** subject states the action or decision. Body: ask/decision → context in 2-4 lines → what you need and by when.
```
Subject: Decision needed by Fri: vendor for Q4 rollout
Hi Sam,
I recommend Vendor B. It costs 12% more but ships two weeks sooner and includes support.
Need your OK by Friday so we can sign Monday. Options and numbers are below.
- A: $40k, ships Nov 20
- B: $45k, ships Nov 6 (recommended)
Thanks, Alex
```
**Status update:** Done / Next / Blockers / Asks (one line each, dates and owners).
**Memo:** Purpose → Recommendation → Rationale (3 bullets) → Risks → Next steps with owners.
**Proposal:** Problem → Proposed solution → Scope and deliverables → Timeline → Cost → Risks → Call to action.
**Meeting recap:** Decisions · Action items (owner, due) · Open questions.
**Difficult message (decline, bad news, pushback):** state the decision first, one sentence of reason, what you can offer, keep warmth without hedging.
**Resume/CV bullets:** verb + what + measurable result (`Cut deploy time 40% by parallelizing CI`).
**Cover letter:** why this role/company (specific) → strongest relevant proof → ask.

## 4. Teaching and explaining

Structure: objective → prerequisite check → intuition/analogy → worked example → guided practice → common mistakes → recap → self-check.

Explain-at-level ladder: state the level (age 10 / beginner / practitioner / expert) and keep vocabulary matched. Analogy rules: map one thing to one thing, say where the analogy breaks.

Lesson plan template:
```
Topic / Level / Time
Objective (learner can ...)
Warm-up (2 min question)
Explain (3 chunks, each with an example)
Practice (3 tasks, easy → hard, with answers)
Check for understanding (3 questions)
Common mistakes
Homework / next step
```
Study aids: flashcards (one fact per card, question on front), quizzes (mix recall and application, include answer key with explanations), cheat sheets (one page: definitions, formulas, examples), step-by-step tutorials (numbered, each step verifiable: "you should see ...").

## 5. Persuasive and marketing

Frameworks: **PAS** (Problem, Agitate, Solve), **AIDA** (Attention, Interest, Desire, Action), **BAB** (Before, After, Bridge), **4Ps** (Promise, Picture, Proof, Push). Headline formula: outcome + timeframe or specificity (`Ship your first game in 7 days`). One promise, proof (numbers, quotes, demos), one call to action. Handle objections in an FAQ. Write in the customer's words, cut superlatives that lack evidence.

## 6. Technical writing and documentation

README skeleton: what it is (1 line) · demo/screenshot · install · quick start (copy-paste works) · usage · configuration · examples · troubleshooting · contributing · license. API doc per endpoint: purpose, request (curl), parameters table, response example, errors. Runbook: symptom → check → fix → escalate. Procedure writing: one action per step, imperative verbs, expected result after each step, warnings before the risky step, no ambiguous words ("should", "might").

## 7. Stylish / literary nonfiction

Choose precise nouns and strong verbs, cut decorative adjectives, control rhythm with sentence length and punctuation, use one fresh image per paragraph, let white space and restraint carry emotion, open on scene or paradox, end on an image or turn rather than a summary.

Flat: `The city was busy and loud in the morning.`
Styled: `By seven the street had learned its own noise: shutters, scooters, someone hammering a tin roof back into agreement.`

Genres: personal essay (specific scene → reflection → turn), profile (subject in motion, telling detail, contrasts), op-ed (thesis in the first 100 words, strongest counterargument answered), speech (spoken rhythm, repetition, short sentences, one memorable line), toast/eulogy (one story, warmth, a light touch of humor, brevity).

## 8. Bot, robot, and persona voices

Define the voice in five rules before writing: vocabulary, sentence shape, what it never says, its quirk, its emotional range. Give three sample lines, then stay inside the rules.

Robotic: literal, low-contraction, status phrasing, dry precision.
> `Query received. Processing. Result: three matches. Confidence: moderate. Awaiting instruction.`

Helpful assistant persona: warm, concise, offers next step. Gruff mentor: short sentences, blunt, cares underneath. Playful NPC: catchphrase, consistent slang. Keep the voice readable; the constraint is flavor, not friction. For game NPCs and UI bots, provide a line table by situation (greeting, success, failure, idle, farewell) with 3 variants each to avoid repetition.

## 9. Social posts, bios, and short copy

Post: hook line (specific claim or question) → 2-4 short lines of value → one call to action. Thread: numbered points, each standing alone, strong first and last. Bio: who you help + proof + a human detail. Product description: outcome, three features as benefits, one spec line. Names/slogans: generate 10, cut to 3, check pronunciation, meaning, and availability. Captions: one image, one idea. Keep each platform's length and norms.

## 10. Editing passes

1. **Structure**: does the opening earn attention, does each paragraph do one job, is the ending deliberate?
2. **Clarity**: one idea per sentence, define terms, cut throat-clearing.
3. **Concision**: delete filler words (very, really, just, actually, in order to, the fact that).
4. **Voice**: consistent tense, POV, tone; read aloud in your head.
5. **Accuracy**: every fact and number checked or marked; no invented quotes.
6. **Polish**: grammar, punctuation, formatting, consistent terminology.

Tighten by 10-20% without losing content; if the user asked for a specific length, hit it.

## 11. Rules and limits

- Match style through traits (diction, rhythm, structure), not by reproducing an author's text; do not reproduce copyrighted passages, lyrics, or poems.
- Do not invent quotes, statistics, or events attributed to real people; mark uncertain claims.
- Help with voice and clarity, but do not help misrepresent authorship where rules forbid AI assistance (for example graded work under a no-AI policy).
- Use placeholders for personal facts the user has not given.
- Dark or mature fiction themes follow normal safety judgment.

## 12. Verification

Check against the brief (audience, voice, length, format); confirm every required point is present; read the first and last paragraph twice; scan for stock phrases and repeated sentence openings; confirm facts and names; for long pieces confirm consistency of terms and tone from start to end.

## 13. Automated prose check

Run `python scripts/writing_lint.py draft.txt` after drafting. It reports sentence-length variety (flat rhythm), repeated sentence openers, stock phrases, filler words, adverb and passive density, very long sentences, and a readability score. Treat flags as places to look, not rules: fix what reads badly aloud, keep what is intentional. Re-run after the edit pass and compare. For voice matching, lint the user's own sample first and aim for similar sentence-length spread and phrasing habits.
