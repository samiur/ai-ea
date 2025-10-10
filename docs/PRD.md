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

  * **Approval mode** (default MVP): bot drafts email/Slack; you tap approve or the assistant autoproceeds after a grace window with safe defaults.
* Daily agenda + conflicts digest (AM) and rolling conflict alerts.

**Post-MVP (near-term):**

* Candidate interview templates (panel assembly, backfills).
* Customer call presets (priority windows, exec sponsor alignment).
* Travel-aware constraints, cross-TZ heuristics, and “hard blocks.”
* Learning loop: personal preferences learned from your historical accept/decline/edits.

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

* Encodes your rules: 1-1 reschedule window; priority tiers (Board/CEO > Customer > Hiring > Internal x-func > 1-1); default durations; buffers; no-meeting days; hard blocks; soft blocks.

**R3. 1-1 Auto-Rescheduler**

* Triggers: conflicts (exec/customer), travel, overlapping holds.
* Constraints: keep cadence, same weekday bias, preserve time-of-day when possible, notify counterpart with two time options + link.

**R4. Inbound Meeting Intake**

* Parse requests (email/Slack) → identify attendees, purpose, urgency → propose slots (≥2 options) → send holds + finalize.

**R5. Coordinator (Gmail & Slack)**

* Drafts polite, terse messages aligned with template library; supports DM, thread reply, small channel posts; handles follow-ups/escalations if no reply.

**R6. Approvals & Autonomy Controls**

* Modes: Approval-first (MVP), Auto with guardrails (opt-in), Manual fallback.
* Audit trail for every action (what/why/who/how decided).

**R7. Safety & Compliance**

* No sending without authenticated identity; human-like clarity; never shares confidential details; logs + rollback for calendar changes.

**R8. Insights & Digests**

* Morning brief (top 5 risks, conflicts to fix, holds to confirm); weekly 1-1 stability report; SLA metrics.

## 5) Success Metrics

* **Automation Rate:** % reschedules auto-handled.
* **Time-to-Book:** P50/P90 for inbound requests.
* **Error Rate:** conflicts created, wrong-TZ, wrong attendees.
* **User Effort:** approvals per week (downward trend).
* **Counterparty Satisfaction:** lightweight 👍/👎 on messages.

## 6) Experience Requirements (UX writing & tone)

* Crisp, respectful, low-ego tone; short first message, options clearly bullet-listed, one ask per message.
* Email: subject lines that encode purpose + action (“Rescheduling our 1-1 — two options”).
* Slack: uses threads; never spams channels; keeps emojis to a minimum for exec contexts.

## 7) System & Integration Requirements

* **Google Calendar**: read/write primary + free/busy, create/modify events; Meet links.
* **Gmail**: read relevant threads, draft/send as you; label “AI-assistant”.
* **Slack**: bot user with DM + thread reply; limited channel posting.
* **Policy Store**: per-rule key-value and feature flags.
* **Decision Logger**: every decision with rationale, inputs, recipients.
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

1. **Phase 0 (You only):** approval-first; daily brief; 1-1 rescheduler.
2. **Phase 1 (Directs):** extend to your reports; enable auto-send for 1-1s only.
3. **Phase 2 (Peers/Execs/Recruiting):** candidate/customer presets; broaden autonomy.

## 13) Example Message Templates (MVP)

**Email (Reschedule a 1-1):**
*Subject:* Rescheduling our 1-1 — two options
*Body:*
Hi {Name} — a priority conflict popped up on {old_date}. Could you do either of these?
• **Option 1:** {slot1_local}
• **Option 2:** {slot2_local}
If neither works, hit “Propose another time” and I’ll find alternatives. Thanks!

**Slack DM (Internal “find time”):**
Hey {Name}! Can we grab **{duration}** this **{window}** for **{purpose}**?
• {slot1}
• {slot2}
Reply “1” or “2” to auto-book. If neither, say “more” and I’ll propose new slots.
