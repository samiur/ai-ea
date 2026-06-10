# PRD — “Samiur’s AI Executive Assistant (Calendar & Coordination)”

## 1) Problem & Goals

You have a high-volume, mixed-audience calendar (directs, peers/executives, customers, candidates). The assistant should:

1. Own scheduling/rescheduling so you don’t have to.
2. Automatically reschedule 1-1s with directs when conflicts arise.
3. Find time for inbound meeting requests.
4. Proactively coordinate over Gmail and Slack with human-caliber drafts and etiquette.
5. Respect your policies (priority, focus time, meeting length, buffers, time zones, travel).

**Primary KPI (MVP):**

* ≥70% of reschedule events auto-resolved without your intervention within 2 business hours.
* ≥60% of inbound scheduling requests auto-booked in ≤24h.
* ≤2% “bad outcomes” (double-book, wrong people/time zone) per month.

## 2) In-Scope (MVP)

* Google Calendar (primary), Gmail, Slack DMs/threads.
* 1-1 auto-rescheduler with policy engine (e.g., “1-1s may move ±14 days, preserve cadence, keep within work hours, preserve buffers”).
* Smart “find time” for new/internal meetings (policy-driven lengths, attendees, rooms/links).
* Draft-and-send flows:

  * **Approval mode** (default MVP): bot drafts email/Slack; nothing sends without an explicit approval. Approvals arrive as Slack DM cards with Approve / Reject / Edit buttons. (Grace-window auto-proceed is cut from approval mode; timed autonomy returns only as part of the opt-in auto mode — see R6.)
* Preference memory (Zep): durable counterpart/time/channel preferences, written back from accepted and declined options (see TRD §5).
* Daily agenda + conflicts digest (AM) and rolling conflict alerts, delivered in the same Slack DM as approvals.

**Post-MVP (near-term):**

* Candidate interview templates (panel assembly, backfills).
* Customer call presets (priority windows, exec sponsor alignment).
* Travel-aware constraints, cross-TZ heuristics, and “hard blocks.”
* Learning loop v2: mining historical accept/decline/edit patterns to seed and refine memory (MVP memory learns only from live interactions).

**Out-of-Scope (MVP):**

* Full task/project management, docs drafting, expense approvals, etc.

## 3) Users & Personas

* **Primary:** You (Samiur), Head of AI Product; wants zero-friction calendar.
* **Secondary:** Direct reports (1-1 partners), peers/executives, recruiters/people ops, customers, candidates — as coordination counterparts.
* **Admin/Failsafe:** Optional EA/Chief of Staff who can override.

## 4) Key Requirements

**R1. Unified Availability Graph**

* Merge GCal primary + focus blocks + buffer rules; detect “schedulable” vs “sacred” time.

**R2. Policy & Priority Engine**

* Encodes your rules: 1-1 reschedule window; priority tiers using the canonical enum shared with the TRD — VIP (Board/CEO) > Customer > Hiring > Internal > 1-1; default durations; buffers; no-meeting days; hard blocks; soft blocks.

**R3. 1-1 Auto-Rescheduler**

* Triggers: conflicts (exec/customer), travel, overlapping holds.
* Constraints: keep cadence, same weekday bias, preserve time-of-day when possible, notify counterpart with two time options + link.

**R4. Inbound Meeting Intake**

* Parse requests (email/Slack) → identify attendees, purpose, urgency → propose slots (≥2 options) → place soft holds + finalize.
* Soft holds live on **your** calendar only, with a TTL and auto-expiry (TRD §2.3); counterparts receive invites only on finalization.

**R5. Coordinator (Gmail & Slack)**

* Drafts polite, terse messages aligned with template library; supports DM, thread reply, small channel posts; handles follow-ups/escalations if no reply.

**R6. Approvals & Autonomy Controls**

* Modes: Approval-first (MVP), Auto with guardrails (opt-in, Phase 2+ of §12), Manual fallback.
* MVP is strictly approval-first: no message send and no calendar commit without an explicit approval tap. There is no timeout or grace-window auto-proceed in approval mode.
* The confidence scorer (TRD §6) runs in **shadow** during MVP: it logs a would-have-decided verdict on every action so thresholds are calibrated on real data before auto-send is enabled for 1-1s (Phase 2 of §12).
* Approval surface: Slack DM cards (Approve / Reject / Edit) are the primary surface; the web console is audit/history-only for MVP.
* Audit trail for every action (what/why/who/how decided).

**R7. Safety & Compliance**

* No sending without authenticated identity; human-like clarity; never shares confidential details; logs + rollback for calendar changes.
* **Untrusted-input hardening:** inbound email/Slack content is data, not instructions. Counterpart messages can never change policies, escalate autonomy, alter recipients, or trigger actions outside the current scheduling intent; parsed requests are validated against the policy engine before any action. First-time or unrecognized senders get the lowest-autonomy treatment.
* **AI disclosure:** messages to external parties (customers, candidates, recruiters outside the org) are identified as coming from your scheduling assistant (e.g., signed "Cal — Samiur's scheduling assistant"). Internal messages to directs/peers send as you, without disclosure.

**R8. Insights & Digests**

* Morning brief (top 5 risks, conflicts to fix, holds to confirm); weekly 1-1 stability report; SLA metrics.

## 5) Success Metrics

All metrics are computed from Decision Logger events (`decision_taken`, `message_sent`, `event_moved`). "Business hours" means your working hours in America/Los_Angeles. The §1 targets are provisional until validated against the Phase 0 shadow-mode baseline (§12).

* **Automation Rate:** % reschedules auto-handled.
* **Time-to-Book:** P50/P90 for inbound requests.
* **Error Rate:** conflicts created, wrong-TZ, wrong attendees.
* **User Effort:** approvals per week (downward trend).
* **Counterparty Satisfaction:** Slack-only for MVP — 👍/👎 emoji reactions on assistant DMs. Email counterparts are measured by proxy (reply rate, option-acceptance rate, opt-outs); no survey footers in professional email.

## 6) Experience Requirements (UX writing & tone)

* Crisp, respectful, low-ego tone; short first message, options clearly bullet-listed, one ask per message.
* Email: subject lines that encode purpose + action (“Rescheduling our 1-1 — two options”).
* Slack: uses threads; never spams channels; keeps emojis to a minimum for exec contexts.
* External messages carry the assistant signature (see R7 disclosure); internal messages read as if you wrote them.

## 7) System & Integration Requirements

**Architecture (decided 2026-06-10): hybrid agent + deterministic core.** An LLM agent (Claude Agent SDK) handles parsing, drafting, and coordination conversations through MCP tools; all calendar **writes** go through a thin deterministic Scheduler service that owns two-phase commit, idempotency, and policy checks (TRD §2.3). Where mature MCP servers exist (Calendar, Gmail, Slack), we use them instead of hand-building API clients.

* **Google Calendar**: read/write primary + free/busy, create/modify events; Meet links. Reads via MCP; writes only via the Scheduler service.
* **Gmail**: read relevant threads, draft/send as you; label “AI-assistant”. Via MCP.
* **Slack**: bot user with DM + thread reply; limited channel posting; hosts approval cards and the daily digest.
* **Memory (Zep)**: durable preferences, org facts, meeting series (TRD §5) — MVP infrastructure.
* **Policy Store**: per-rule key-value and feature flags.
* **Decision Logger**: every decision with rationale, inputs, recipients; the data source for §5 metrics.
* **Secrets & Auth**: OAuth scopes least-privilege; per-tenant (your workspace) isolation.

## 8) Constraints & Assumptions

* Workspace is Google-based; Slack Enterprise.
* Time zone: America/Los_Angeles, frequent cross-TZ.
* High signal meetings (CEO/CHRO/customers) trump most internal blocks.
* Cultural norms: default human-review before send (MVP).

## 9) User Stories (MVP slice)

**Epic A — Calendar Core**

* A1. As Samiur, when a Board/CEO hold conflicts with a 1-1, the 1-1 is auto-moved within ±14 days, offering 2 options to my report, preserving buffers.

  * **Acceptance:** event moved, counterpart notified, my agenda updated, Slack DM summary sent to me for visibility.
* A2. As Samiur, I get a 9:00 AM daily brief with top conflicts + one-tap approvals.

**Epic B — Coordinator**

* B1. As a counterpart, I receive a short, polite email with 2 time options + a calendar link; replying with “Option 1” books it.

  * **Acceptance:** replies parsed; event finalized; confirmation sent.
* B2. As Samiur, when a counterpart hasn’t replied to a scheduling message within 1 business day, the assistant follows up once on the same channel, then escalates to the other channel (Slack→email or email→Slack); after a second business day with no reply it surfaces the thread in my daily brief instead of pinging again.

  * **Acceptance:** at most one follow-up per channel; escalation logged; brief shows the stalled thread with one-tap “nudge again” / “I’ll handle it”.
* B3. As a counterpart, if I decline both offered options (or reply ambiguously), the assistant proposes two fresh slots at most once more; if those fail or my reply can’t be parsed confidently, it hands the thread to Samiur rather than looping.

  * **Acceptance:** max two proposal rounds per intent; ambiguous replies (parser confidence below threshold) always route to approval; no message loops.

**Epic C — Policy & Safety**

* C1. As Samiur, I can toggle “auto-send below risk threshold” (e.g., 1-1s yes, exec/customer no).

  * **Acceptance:** runs in approval mode by default; logs all actions.

## 10) Non-Functional

* **Reliability:** idempotent reschedules; conflict checks pre- and post-commit.
* **Latency:** propose times within 60s of trigger; send drafts ≤90s.
* **Security/Privacy:** least-priv OAuth; redact content in logs; SOC-friendly audit artifacts.
* **Observability:** structured events (decision_taken, message_sent, event_moved) with correlation IDs.

## 11) Risks & Mitigations

* **Mis-scheduling:** dry-run checks + confirmations; conservative defaults.
* **Social friction:** human-approval mode + empathetic templates; small N pilot with directs.
* **API rate limits:** exponential backoff + queues; fallbacks to “single summary DM.”

## 12) Rollout Plan

1. **Phase 0 — Shadow (2 weeks, you only):** no sends, no calendar writes. The assistant drafts, proposes, and the confidence scorer logs would-have-decided verdicts on real triggers. Output: KPI baseline; §1 targets confirmed or revised.
2. **Phase 1 (You only):** approval-first live; daily brief; 1-1 rescheduler; scorer still shadow-logging.
3. **Phase 2 (Directs):** extend to your reports; enable auto-send for 1-1s only, with thresholds calibrated in Phases 0–1.
4. **Phase 3 (Peers/Execs/Recruiting):** candidate/customer presets; broaden autonomy.

## 13) Example Message Templates (MVP)

**Email (Reschedule a 1-1):**
*Subject:* Rescheduling our 1-1 — two options
*Body:*
Hi {Name} — a priority conflict popped up on {old_date}. Could you do either of these?
• **Option 1:** {slot1_local}
• **Option 2:** {slot2_local}
If neither works, hit “Propose another time” and I’ll find alternatives. Thanks!

**Email (External — customer/candidate; carries disclosure per R7):**
*Subject:* Finding time with Samiur — two options
*Body:*
Hi {Name} — I help Samiur with scheduling. He’d love to find {duration} to {purpose}. Would either of these work?
• **Option 1:** {slot1_local}
• **Option 2:** {slot2_local}
If neither works, reply with a few windows that suit you and I’ll lock one in.
— Cal, Samiur’s scheduling assistant

**Slack DM (Internal “find time”):**
Hey {Name}! Can we grab **{duration}** this **{window}** for **{purpose}**?
• {slot1}
• {slot2}
Reply “1” or “2” to auto-book. If neither, say “more” and I’ll propose new slots.

---

**Last updated:** 2026-06-10

## 14) Changelog

* **2026-06-10** — PRD review: adopted hybrid agent+MCP architecture (§7); cut grace-window auto-proceed from approval mode and specified the Slack-first approval surface (§2, R6); confidence scorer runs in shadow during MVP (R6); added untrusted-input hardening and external AI-disclosure requirements (R7, §6); Zep memory promoted to MVP scope (§2, §7); added Phase 0 shadow-mode baseline and renumbered rollout (§12); KPI definitions + data source (§5); satisfaction metric scoped to Slack reactions (§5); failure-path stories B2/B3 (§9); soft-hold semantics (R4); tier names aligned with TRD (R2). Follow-up completed same day: plan.md renumbered to the reorganized step scheme and Steps 21–35 rewritten for the MCP architecture and Zep-in-MVP.
* **2025-10** — Initial PRD.
