# Krè mo — Submission Package

Everything needed to record, submit, and describe Krè mo for the CALL-E
"Your Code Is Calling" hackathon. Nothing in this document changes application
code; it documents the frozen DEMO build.

---

## 1. Video script (target 2:15–2:40)

Tone: plain, confident, technical-but-human. No hype words, no claim that
simulated calls were real.

**0:00–0:15 — HOOK**
> Right now, somewhere, someone needs one simple fact — is this crossing open, is this service running, is this actually true — and there's no website that knows. That information only exists behind a phone number.

**0:15–0:35 — WHY KRÈ MO EXISTS**
> This started from a real problem in French Guiana — river crossings, long distances, borders, conditions that change hour to hour, and no feed anywhere that tracks it. But this isn't a French Guiana problem. It's universal. Anywhere critical, current information only lives with a person who picks up a phone.

**0:35–1:20 — PRODUCT DEMO**
> This is Krè mo. The question: is the river crossing operating this afternoon. I press Verify Field Status. Krè mo reaches Source A — one independent observation. Then Source B — a second, independent observation. Watch the convergence: each signal resolves toward the center. When both agree, that becomes a verified fact, not a guess.
> Verified, demo. Two out of two sources agree. Crossing operating until 17:30, checked seconds ago.
> This recording uses simulated sources because our available +594 and +33 test numbers hit a CALL-E coverage mismatch. The live provider is already implemented, and we reported the issue to CALL-E support.

**1:20–1:50 — TECHNICAL IDEA**
> Under the hood, each phone call becomes a structured observation — a status, a detail, a confidence value. Krè mo compares independent observations with a deterministic consensus engine. No opaque AI confidence score. If sources contradict each other, that's conflicting. One source alone is never enough — that's insufficient. Only two independent sources agreeing becomes verified.

**1:50–2:15 — WHY THIS MATTERS**
> River crossings. Transport operations. Local service availability. Infrastructure status. Suppliers. Field operations. Anywhere the real, current answer isn't reliably online, and the only way to know is to ask someone directly.

**2:15–2:35 — CLOSE**
> This isn't a transport app. It's a verification layer for facts that still live offline. Krè mo turns a phone call into a corroborated, timestamped, verifiable fact.
> Krè mo. Field verification network.

**Runtime estimate:** the timestamp structure above totals 2:35 (155s); at a
natural delivery pace the script comfortably fills it with room for silent
visual beats, landing around **2:20–2:35** overall — inside the 2:15–2:40
target. The CALL-E disclosure sentence itself is ~32 words, roughly **8–10
seconds** spoken at a brisk, unhurried pace — keep it tight, it should not
become the focus of the section.

---

## 2. Shot list (1440×900, DEMO mode)

| Time | Narration cue | Screen / action | Click? | Pause? | Zoom |
|---|---|---|---|---|---|
| 0:00–0:15 | HOOK | Idle screen, full page visible: brand, question, both source panels on standby | none | hold static | none — wide shot |
| 0:15–0:35 | Origin story | Same idle screen, voiceover only | none | hold static | optional: very slow, subtle zoom toward the question text |
| 0:35–0:38 | "I press Verify Field Status" | Cursor visibly moves to and clicks the button | **click VERIFY FIELD STATUS** | none | none |
| 0:38–0:40 | "Krè mo reaches Source A" | Left trace lights amber, Source A card border amber, `ACQUIRING…` | — | real time (~1.4s) | none |
| 0:40–0:42 | "Then Source B" | Right trace lights amber, Source B card border amber | — | real time (~1.8s) | none |
| 0:42–0:44 | "Watch the convergence" | Both traces solid, center node pulses amber (`EVALUATING`) | — | real time, brief | slight zoom on the convergence node — signature shot |
| 0:44–0:46 | "When both agree, verified fact" | Node + traces resolve to solid green, `VERIFIED DEMO` banner appears | — | **hold 2–3s** | none — let the reveal animation play uncut |
| 0:46–1:05 | "Two out of two sources agree… checked seconds ago" | Full result block: banner, `2/2 SOURCES AGREE`, hero fact, freshness | — | hold | slow, subtle zoom on the result block — second signature shot |
| 1:05–1:15 | Shortened CALL-E disclosure sentence | Same screen, no cut away | optional: click EVIDENCE LOG open | hold | none — say it plainly, don't linger |
| 1:15–1:20 | (buffer) | Same screen | none | hold | none |
| 1:20–1:50 | Technical explanation | Stay on the verified result screen (evidence log open, `[SIMULATED]` visible) | none | hold static | continue the same gentle zoom, no new graphics |
| 1:50–2:15 | "Why this matters" examples | Cut to a clean, reset idle screen (reload off-camera beforehand) | none | hold static | none |
| 2:15–2:35 | Close | Idle or verified screen, whichever reads better | none | hold static | none — end on a still frame |

**Notes:**
- The acquire→verify sequence is genuinely fast (~3.2s). Record it once, in real time — don't slow it down artificially.
- Do not re-click "Verify Field Status" while a result is showing (resets the panel, looks like a glitch on camera).
- The fixture data always resolves to `VERIFIED`; the script never claims otherwise, and no `CONFLICTING`/`INSUFFICIENT` screen needs to be shown.
- Clean screenshots to export separately (already captured and confirmed to fit 1440×900 with no scrolling): idle, mid-acquisition (Source A active), verified result with evidence log expanded.

---

## 3. Devpost copy

**A. Project title**
> Krè mo

**B. Tagline**
> Turn offline human knowledge into verified, timestamped facts.
*(62 characters — well within Devpost's limit.)*

**C. Short description**
> Krè mo turns phone calls into structured observations, then corroborates independent sources to produce timestamped real-world facts. One source is an observation. Agreement makes it verified.
*(192 characters — within a 300-character limit.)*

**D. Full project description**

**Inspiration**
The internet can't answer live, offline questions — is a river crossing running, is a service actually open right now. That information only exists behind a phone number. We started from a concrete case in French Guiana (river crossings, distance, fragmented live information) and generalized it: anywhere a critical fact only lives with a person who picks up a phone, this problem exists.

**What it does**
Krè mo takes one question, sends it to two independent field sources via CALL-E, and compares their structured, schema-validated observations with a deterministic consensus engine. The result is never a fabricated confidence score — it's `VERIFIED`, `CONFLICTING`, or `INSUFFICIENT`, with a timestamp, a freshness reading, and the raw evidence behind the call.

**How we built it**
TypeScript, zero extra frontend framework, a stateless `node:http` backend, and the official `@call-e/calle` SDK. A single provider interface backs both a real `LiveCalleProvider` (places actual CALL-E calls) and a `DemoProvider` (deterministic fixtures, clearly labeled `[SIMULATED]`) — switching between them is one environment variable, no code changes. The consensus engine is pure, dependency-free, and covered by 11 unit tests.

**Challenges we ran into**
CALL-E's live API rejected our only two available authorized test numbers — a French Guiana (+594) and a France (+33) number, in both French and English — even though France is listed as a supported region in CALL-E's own docs. After validating our request construction, E.164 formatting, locales and SDK types, we found a mismatch between the published coverage table and the live API behavior. We reported this to CALL-E support and built the demo to be transparent about running in DEMO mode as a result.

**Accomplishments we're proud of**
A consensus engine with an explainable, one-sentence rule for every outcome — including making `confidence: null` (not `0`) mean something specific and honest. A DEMO mode that is structurally incapable of pretending to be a real call. A field-instrument UI that communicates "verification," not "AI chatbot," in the first three seconds.

**What we learned**
That the hardest part of a corroboration product isn't the AI — it's resisting the urge to fabricate confidence, and being honest on-screen the moment something (like live coverage) doesn't work as expected.

**What's next**
A confirmed-supported test number to validate `LiveCalleProvider` end-to-end, more than one scenario/question type, and n-source corroboration beyond the fixed 2-source demo.

**E. Technologies used**
TypeScript, Node.js (`node:http`, `node:test`), `@call-e/calle` (CALL-E TypeScript SDK), `dotenv`, `tsx`, `tsc` — no frontend framework, no database, no extra runtime dependencies.

**F. Suggested project tags**
`typescript` · `nodejs` · `calle` · `phone-calls` · `fact-verification` · `consensus` · `field-instrument` · `hackathon2026`

**G. 5 strongest judge-facing bullet points**
1. Phone calls become data sources — CALL-E turns offline human knowledge into structured observations.
2. Corroboration instead of trust — one source is only an observation; agreement creates a verified fact.
3. Deterministic verification — VERIFIED / CONFLICTING / INSUFFICIENT follow auditable rules, not an opaque model score.
4. Universal offline-data layer — crossings are the demo; the same system applies to infrastructure, suppliers, transport and field operations.
5. Live-ready architecture — the real CALL-E provider and the demo provider share exactly the same observation/consensus pipeline.

---

## 4. Submission checklist

**Repository**
- [ ] Git repo initialized and all files committed (`git init` already run; needs a first commit)
- [ ] `.env.local` confirmed **not** committed (re-verify with `git check-ignore -v .env.local` after committing)
- [ ] `.gitignore` covers `node_modules/`, `dist/`, `.env*`
- [ ] Repo pushed to GitHub (public or judge-accessible), link ready

**README**
- [ ] Final `README.md` in place (this session's rewrite)
- [ ] CALL-E `+594`/`+33` rejection disclosed, support-contact fact included, no blame on CALL-E
- [ ] Demo-vs-Live mode explained clearly
- [ ] Environment variables table present and accurate

**Screenshots**
- [ ] Idle state, 1440×900
- [ ] Mid-acquisition state (Source A active), 1440×900
- [ ] Verified result state with evidence log expanded, 1440×900
- [ ] All three confirmed to render without scrolling (verified in-session)

**Demo video**
- [ ] Recorded per script + shot list above, 1440×900
- [ ] Runtime within ~2:15–2:40
- [ ] Shortened CALL-E disclosure present, ≤ ~10s, not dwelt on
- [ ] No claim, spoken or on-screen, that simulated calls were real
- [ ] Uploaded (YouTube/unlisted or Devpost's own uploader), link ready

**CALL-E integration**
- [ ] `LiveCalleProvider` code present and typechecked (already true)
- [ ] Phase 1 (`npm run test:call`) still intact and functional
- [ ] README states LIVE has not been exercised end-to-end, and that support was contacted (done)

**Devpost fields**
- [ ] Title: Krè mo
- [ ] Tagline (section 3B)
- [ ] Short description (section 3C)
- [ ] Full description (section 3D)
- [ ] Technologies used (section 3E)
- [ ] Tags (section 3F)
- [ ] Repo link, video link, live/demo link (if hosted) attached
- [ ] Team members added

**Disclosure**
- [ ] Explicit statement in README **and** Devpost description that the submitted demo runs in DEMO mode with simulated source responses, and why
- [ ] No wording anywhere implies the recorded demo placed real phone calls
- [ ] CALL-E support contact (support@heycall-e.com) documented as already done, not pending

**Final confirmation**
- [ ] All above boxes checked
- [ ] Submission preview reviewed once fully filled in on Devpost
- [ ] Submitted before the **September 14, 2026, 11:45pm SGT** deadline
