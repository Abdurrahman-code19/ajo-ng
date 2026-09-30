"""
Section 8 — Entity Relationship Diagram (ERD).

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Companion section: section 9 (PostgreSQL schema) implements every entity,
constraint and cascade rule named here. Where the two could disagree, the rule
stated in this section is the intent and the rule in section 9 is the
mechanism; a divergence between them is a defect, not a choice.

CANONICAL.md section 5 names twenty-seven core entities. Thirteen further tables
are required to make that set work and to make the section 6 API surface
implementable; each is marked S (supporting) in 8.1.2 and each is justified
where it first appears.

Money is bigint kobo everywhere and is never float or numeric. The 2% fee is
applied exactly as CANONICAL.md section 1 states: a member owing
NGN 1,000.00 is charged NGN 1,020.00, of which NGN 1,000.00 is the round pool
and NGN 20.00 is fees_income; the recipient of a ten-member round receives the
base pool NGN 10,000.00 and never NGN 10,200.00. The fee never reduces a
payout, and the schema in section 9.5 enforces that as a CHECK constraint
rather than a convention. The tagline is "Your Ajo. Your Story."
"""

BLOCKS = [

    {"t": "h1", "text": "8. Entity Relationship Diagram (ERD)"},

    {
        "t": "lead",
        "text": (
            "This section is the structural contract for the AJO.ng data model. It names "
            "every persistent entity, the cardinality of every relationship between them, "
            "the rule that governs each relationship, and the exact behaviour of each "
            "foreign key when a row is deleted. It is written to be read against section "
            "9, which turns every relationship below into a real foreign key, and against "
            "section 6, which turns every entity below into an endpoint. The three sections "
            "are one design expressed three ways: an entity with no endpoint is dead code, "
            "an endpoint with no entity is unimplementable, and a relationship stated here "
            "with no constraint in section 9 is a relationship that will be violated in "
            "production by someone under time pressure who did not read this file."
        ),
    },

    # =====================================================================
    # 8.1
    # =====================================================================
    {"t": "h2", "text": "8.1 ERD scope and notation"},

    {
        "t": "p",
        "text": (
            "The scope is deliberately narrow in one direction and wide in the other. It is "
            "narrow in that it models *what is stored*, not *how it is used*: no derived "
            "columns that exist only to make a chart fast, no denormalised aggregates that "
            "could be computed, and no entity that has no reason to exist. It is wide in "
            "that it includes every operational and audit table the platform needs to be "
            "defensible, because a savings product that cannot show a regulator what happened "
            "to a member's money is not a product, it is an incident waiting for a customer."
        ),
    },

    {"t": "h3", "text": "8.1.1 Notation"},

    {
        "t": "p",
        "text": (
            "The diagrams use SQLAlchemy-style crow's foot, chosen because it is the one "
            "notation an engineer reading a migration can recognise without a legend they "
            "have to look up. It is drawn in 8.2 and repeated in a looser, grouped form in "
            "8.3 so that the cardinality rules and the narrative rationale sit next to each "
            "other rather than in a diagram on one page and a table on another."
        ),
    },

    {
        "t": "code",
        "text": """
  SYMBOL          MEANING
  --------------------------------------------------------------------
   ||             exactly one, and only one (NOT NULL, no default)
   |{             one or more (at least one, enforced by business rule)
   o{             zero or more
   o|             zero or one
   }o--           many-to-many, resolved through the table named in the
                  middle. The join table always carries a scope column
                  when the relationship is itself scoped (an Ajo role,
                  for example, is a role within one Ajo, not globally).

  NOTATION CONVENTIONS USED THROUGHOUT
  --------------------------------------------------------------------
   *  = entity named in CANONICAL.md section 5 (27 entities)
   S  = supporting table required to make the canonical set work
         or the section 6 API implementable (10 tables, see 8.1.2)
   _kobo suffix on every monetary column; bigint; never float, never
         numeric, never a text representation of a number.
   FK   = the child table, naming the column that holds the parent key
   ON DELETE = the referential action actually declared in section 9
""",
    },

    {"t": "h3", "text": "8.1.2 Scope boundary: canonical entities and supporting tables"},

    {
        "t": "p",
        "text": (
            "CANONICAL.md section 5 names twenty-seven core entities. Thirteen further tables "
            "are specified here and marked supporting. They are listed separately, with the "
            "reason each one exists, because the boundary between *the product's data* and "
            "*the platform's plumbing* is exactly the kind of line that erodes silently. Every "
            "supporting table below was added to satisfy a specific requirement in "
            "CANONICAL.md sections 2, 4, 6 or 8; none was added for symmetry or for a "
            "future feature that has not been asked for."
        ),
    },

    {
        "t": "table",
        "head": ["#", "Entity", "Class", "Why it exists"],
        "widths": [0.35, 1.5, 0.55, 4.1],
        "size": 8.0,
        "rows": [
            ["1", "`users`", "*", "The account. Supabase Auth owns the credential; this table owns everything the product needs to know about the person."],
            ["2", "`profiles`", "*", "Presentation data separated from identity so that a profile edit never touches the authentication record."],
            ["3", "`verification_checks`", "*", "BVN / NIN / CAC / selfie outcomes. Separated from `users` so that a re-verification is a new row, not a history-erasing update."],
            ["4", "`ajos`", "*", "The savings group. Root of the lifecycle state machine in CANONICAL.md section 3."],
            ["5", "`ajo_positions`", "*", "The turn order. One row per position; locks on activation."],
            ["6", "`ajo_members`", "*", "The join between a `user` and an `ajo`, carrying member status, replacement history and the claim on a position."],
            ["7", "`invitations`", "*", "Pre-activation join flow, with a hashed single-use token and its own lifecycle."],
            ["8", "`rounds`", "*", "One rotation step of one Ajo. The unit that a payout is funded against."],
            ["9", "`contribution_schedules`", "*", "The payment plan for a round: who is expected to pay, by when, and how much."],
            ["10", "`contributions`", "*", "One member's obligation for one round, and the record of whether it was met."],
            ["11", "`payments`", "*", "One collection attempt against the payment provider, carrying the 2% fee split."],
            ["12", "`payouts`", "*", "One disbursement to one position at the end of one round."],
            ["13", "`ledger_transactions`", "*", "Header of an append-only double-entry transaction. Four mandatory kinds, see 8.3.4."],
            ["14", "`ledger_postings`", "*", "The legs. Every transaction's postings sum to exactly zero."],
            ["15", "`fees`", "*", "The platform's own record of the 2% charge, separate from the member's payment and separable for reporting."],
            ["16", "`notifications`", "*", "Delivery queue and inbox for the canonical catalogue in CANONICAL.md section 8."],
            ["17", "`notification_preferences`", "*", "Per-user channel opt-in, so that SMS really is reserved for money-critical events."],
            ["18", "`disputes`", "*", "A member challenge, with its own lifecycle and evidence chain."],
            ["19", "`documents`", "*", "Binary artefacts: identity documents, selfies, CAC certificates, dispute evidence."],
            ["20", "`risk_events`", "*", "Signals and decisions from the risk function. Polymorphic by subject."],
            ["21", "`audit_logs`", "*", "Who did what, to which row, when, from where. Append-only, and the answer to most support questions."],
            ["22", "`admins`", "*", "The platform-operator flag on a `user`, carrying operator status and last activity."],
            ["23", "`roles`", "*", "The six canonical roles as data, so that role assignment is a row and not a code branch."],
            ["24", "`role_assignments`", "*", "Scoped grants. Resolves users-to-roles and users-to-roles-within-one-Ajo."],
            ["25", "`idempotency_keys`", "*", "Request-hash plus stored response. The mechanism that makes a retried payment safe."],
            ["26", "`webhook_events`", "*", "Inbound provider callbacks, deduplicated on the provider's own event id."],
            ["27", "`reconciliation_runs`", "*", "Daily and on-demand proofs that the ledger, the provider and the round expectations agree."],
            ["28", "`sessions`", "S", "Required by `GET /auth/sessions` and `DELETE /auth/sessions/:id`. Device and revocation state, including the `security.login_new_device` notification in CANONICAL.md section 8."],
            ["29", "`device_tokens`", "S", "Push delivery targets. A notification row that has nowhere to go is not a notification."],
            ["30", "`platform_settings`", "S", "The fee rate and other configuration. A separate table so that configuration is versioned, audited and reviewable, never a constant in code."],
            ["31", "`contribution_frequencies`", "S", "Frequency is business-configurable (weekly, fortnightly, monthly, custom), so it is a lookup row and not a native enum."],
            ["32", "`payment_channels`", "S", "Provider channel codes and limits. ProvidusUnity's capabilities are not yet known in writing, so the mapping is data."],
            ["33", "`notification_templates`", "S", "The catalogue in CANONICAL.md section 8 as data, so that copy can be corrected without a deployment and so that the money-critical channel rule is enforceable."],
            ["34", "`dispute_messages`", "S", "Required by `POST /disputes/:id/messages`. A dispute without a conversation is a ticket, not a resolution."],
            ["35", "`dispute_evidence`", "S", "Required by `POST /disputes/:id/evidence`. Kept separate from `documents` so that dispute evidence has its own retention and disclosure rules."],
            ["36", "`support_tickets`", "S", "The Support screen in CANONICAL.md section 7. Separate from `disputes` because support must not be able to move money (CANONICAL.md section 2)."],
            ["37", "`outbox_events`", "S", "Writes the ledger and the notification in one transaction and publishes after commit, so a payment that posts money cannot fail to send the receipt."],
            ["38", "`document_types`", "S", "The document vocabulary as data. A `doc_type_id` foreign key is enumerable by support and addable by migration; a free-text column is neither, and the 9.3 DDL adds it for that reason."],
            ["39", "`verification_check_types`", "S", "Which kinds of check exist, which are mandatory before activation, and which document each one requires. Keeps `verification_checks` a record of outcomes rather than a catalogue."],
            ["40", "`dispute_reasons`", "S", "The reason vocabulary. Five columns and no trigger, because a free-text dispute reason produces a report nobody can group by."],
        ],
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Twenty-seven plus thirteen",
        "text": (
            "The twenty-seven marked `*` are the entities CANONICAL.md section 5 commits to "
            "and they are not negotiable in name or in count. The thirteen marked `S` are the "
            "minimum set needed to satisfy CANONICAL.md sections 2, 4, 6 and 8 without "
            "overloading an existing table. A reviewer who believes a supporting table is "
            "unnecessary should be able to point at the endpoint or the rule it serves; if "
            "they can, the table stays. The last three were added late, and the reason is "
            "worth recording because it is the same argument three times: a column that holds "
            "one of a small fixed set of values is a table, because a table can be enumerated, "
            "extended by migration and constrained, and a text column can be misspelled."
        ),
    },

    {"t": "h3", "text": "8.1.3 What this section does not model"},

    {
        "t": "bullets",
        "items": [
            "**The payment provider's own ledger.** ProvidusUnity holds and moves the money under a commercial and regulatory arrangement that is still an open decision (CANONICAL.md D-02). AJO.ng's `payments` and `payouts` tables record what we were told and what we sent; they are reconciled against the provider, not derived from it. The reconciliation proof is `reconciliation_runs`.",
            "**Authentication credentials.** Supabase Auth owns passwords, MFA enrolment and tokens. `users.auth_subject_id` records the link. This is a documented one-to-one with a table AJO.ng does not own, treated in 8.4.",
            "**Files.** `documents` stores a path, a hash, a size and a MIME type. The bytes live in object storage. A row is retained when the object is gone, because the record that a document existed is itself the audit evidence.",
            "**Time.** There is no `time` entity. Time is a column, always `timestamptz`, always UTC, and rendered in the member's local zone at the edge (CANONICAL.md section 9.1 conventions, section 9.6 in this document's companion).",
            "**Search indexes and read models.** The dashboard in CANONICAL.md section 7 is served by indexed queries over these tables in v1. A materialised read model is a performance decision for a specific measured problem, not something to model before the problem exists.",
        ],
    },

    # =====================================================================
    # 8.2
    # =====================================================================
    {"t": "pagebreak"},
    {"t": "h2", "text": "8.2 Full text-based ERD"},

    {
        "t": "p",
        "text": (
            "The complete diagram. All forty entities appear exactly once as a primary "
            "box. Relationships are grouped into six bands matching the domains in 8.3, and "
            "cross-band relationships are listed in the final block so that no edge is hidden "
            "by the banding. Every line is under 78 characters so the diagram survives A4 "
            "without horizontal scaling."
        ),
    },

    {
        "t": "code",
        "text": """
============================================================================
 AJO.ng  -  ENTITY RELATIONSHIP DIAGRAM
 * = CANONICAL.md section 5     S = supporting table (see 8.1.2)
 || exactly one   |{ one or more   o{ zero or more   o| zero or one
   }o-  many-to-many, resolved by the table named between the braces
============================================================================

--- BAND 1   IDENTITY & ACCESS  (8.3.1) --------------------------------------
   roles ||--o{ role_assignments }o--|| users        (scope = platform)
   users ||--|| profiles
   users ||--|| admins
   users ||--o{ sessions
   users ||--o{ device_tokens
   users ||--o{ verification_checks
   verification_check_types ||--o{ verification_checks
   document_types ||--o{ documents
   document_types ||--o{ verification_check_types  (required document)
   verification_checks ||--o{ documents
   users ||--o{ documents                     (owner; also attaches to a
                                                verification check)
   profiles ||--o| documents                   (avatar only)
   users ||--|| notification_preferences
   users ||--o{ notifications
   notification_templates ||--o{ notifications  (event_key + channel)
   users ||--o{ support_tickets
   users ||--o{ audit_logs
   users ||--o{ risk_events
   users ||--o{ disputes                       (raised_by, against)

--- BAND 2   AJO LIFECYCLE  (8.3.2) ------------------------------------------
   users ||--o{ ajos                           (organizer)
   ajos ||--o{ ajo_positions
   ajos ||--o{ ajo_members
   users ||--o{ ajo_members
   ajo_positions |{--o{ ajo_members            (only pre-activation)
   ajos ||--o{ invitations
   ajo_positions ||--o{ invitations            (position offered)
   invitations ||--o| ajo_members              (row created on accept)
   role_assignments }o--|| ajos                (scope = ajo, organizer)

--- BAND 3   SCHEDULING  (8.3.3) ---------------------------------------------
   ajos ||--o{ rounds
   rounds ||--o{ contribution_schedules
   ajos ||--|| contribution_schedules          (denormalised, for RLS + read)
   contribution_frequencies ||--o{ ajos

--- BAND 4   MONEY  (8.3.4) --------------------------------------------------
   contribution_schedules ||--o{ contributions
   ajo_members ||--o{ contributions
   ajo_positions ||--o{ contributions           (via the member's claim)
   rounds ||--o{ contributions
   contributions ||--o{ payments               (retries are rows, not edits)
   payments ||--|| fees                       (one fee per settled payment)
   payment_channels ||--o{ payments
   rounds ||--o{ payouts
   ajo_positions ||--o| payouts                (1:1, enforced in 8.8)
   contributions ||--o{ disputes
   payouts ||--o{ disputes
   ledger_transactions ||--o{ ledger_postings  (>= 2, must sum to zero)
   ledger_transactions ||--o| ledger_transactions  (reversal, depth 1)
   users ||--o{ idempotency_keys
   idempotency_keys ||--o| ledger_transactions
   webhook_events ||--o| payments              (dedupe on provider event)

--- BAND 5   TRUST & RISK  (8.3.5) -------------------------------------------
   ajos ||--o{ disputes
   disputes ||--o{ dispute_messages
   disputes ||--o{ dispute_evidence
   dispute_reasons ||--o{ disputes
   documents ||--o| dispute_evidence
   users ||--o{ risk_events
   ajos ||--o{ risk_events
   payments ||--o{ risk_events
   payouts ||--o{ risk_events

--- BAND 6   ENGAGEMENT  (8.3.6) ---------------------------------------------
   users ||--o{ notifications
   users ||--|| notification_preferences
   users ||--o{ support_tickets
   ajos ||--o{ support_tickets
   users ||--o{ outbox_events
   ajos, rounds, payments, payouts -> outbox_events   (polymorphic)

--- CROSS-BAND EDGES NOT DRAWN ABOVE -----------------------------------------
   users -> ajos.organizer_user_id                       (1:N, restrict)
   users -> ajo_members.user_id                          (1:N, restrict)
   users -> ajos.organizer_user_id is the only person who may
     cancel, freeze or request payout release.
   audit_logs is polymorphic: every mutating table in every band writes
     one row. audit_logs has no foreign key back to its subject on purpose,
     because a polymorphic audit trail must not be cascade-deleted by the
     thing it is auditing.
   risk_events is polymorphic over user, ajo, payment and payout for the
     same reason.
   reconciliation_runs references a time window, not an entity. It is
     provable evidence and must survive every table it is used to check.
============================================================================
""",
    },

    {
        "t": "p",
        "text": (
            "One deliberate feature of the diagram is worth calling out, because it is the "
            "decision that shapes the rest of the money model. Position occupancy is held by "
            "`ajo_members.position_id`, not by `ajo_positions.member_id`. A membership claims "
            "a position; a position does not know its holder. This costs a join when you want "
            "to list a position's occupant, and it buys the elimination of a circular foreign "
            "key between two tables that both have independent lifecycles and both are "
            "soft-deleted. It also means a position can be released (the holder leaves) "
            "without touching the position row, which is the only way a position can be "
            "released before activation without deleting history."
        ),
    },

    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Why the diagram carries 40 boxes and not 27",
        "text": (
            "CANONICAL.md section 5 lists the core entities. Thirteen supporting tables are added "
            "because CANONICAL.md sections 2, 4, 6 and 8 require behaviour that those 27 "
            "cannot hold: session revocation (`GET /auth/sessions`), push delivery targets, "
            "dispute conversations and evidence, the notification catalogue as data, the fee "
            "rate as reviewable configuration, and a transactional outbox so that money and "
            "message cannot diverge. Each is a live requirement in a section that is already "
            "committed, not a speculative addition. If CANONICAL.md section 5 is later "
            "amended, this section is amended with it, in the same commit."
        ),
    },

    # =====================================================================
    # 8.3
    # =====================================================================
    {"t": "pagebreak"},
    {"t": "h2", "text": "8.3 Domain breakdown"},

    {
        "t": "p",
        "text": (
            "Six domains, each with an entity detail table and a relationship table. The "
            "detail table answers *what is this row and why does it exist*. The relationship "
            "table answers *what constrains it and what happens when it is deleted*. Both are "
            "required: a model that names entities without naming their delete semantics is a "
            "model that loses a member's receipt history the first time somebody runs a "
            "cascade by accident."
        ),
    },

    # ---------------------------------------------------------------- 8.3.1
    {"t": "h3", "text": "8.3.1 Identity and access"},

    {
        "t": "p",
        "text": (
            "The identity domain answers three questions: who is this person, are we allowed "
            "to let them move money, and what may they see. It deliberately contains no money "
            "and no Ajo membership, so that a question about access control never requires "
            "joining across a financial boundary. `role_assignments` is the only place in the "
            "whole model where the six canonical roles from CANONICAL.md section 2 are "
            "granted, and it is scoped: the same role code means something different at "
            "platform scope than it does within one Ajo."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`users` *", "The person. Auth credential lives in the identity provider; this row is the product's own record.", "`auth_subject_id`, `status` (pending_verification, active, frozen, closed), `phone_e164`, `last_seen_at`", "1:1 profiles, 1:1 admins, 1:1 notification_preferences; 1:N to almost everything else"],
            ["`profiles` *", "Display data, kept off `users` so a bio edit never rewrites the account row.", "`user_id`, `display_name`, `avatar_document_id`, `preferred_locale`, `bvn_last4`", "1:1 users; 0:1 documents (avatar)"],
            ["`verification_checks` *", "One attempt at one check. A re-verification is a new row so the history of failures survives.", "`user_id`, `check_type`, `status`, `provider_reference`, `failure_reason`, `expires_at`", "N:1 users; 1:N documents; 1:N audit_logs"],
            ["`documents` *", "The record of a file, not the file. Bytes live in object storage.", "`owner_user_id`, `verification_check_id`, `doc_type_id`, `storage_bucket`, `storage_path`, `sha256`, `mime_type`, `byte_size`, `scan_status`", "N:1 users; N:1 verification_checks; N:1 document_types; N:1 disputes (via dispute_evidence)"],
            ["`admins` *", "The platform-operator flag. A person is a user who is an admin; `admins` holds operator state, not permissions.", "`user_id`, `operator_status`, `last_active_at`, `invited_by_user_id`", "1:1 users; 1:N role_assignments"],
            ["`roles` *", "The six canonical roles as data, seeded and immutable in code by role, not by row.", "`code` (user, ajo_organizer, ajo_member, support, risk_officer, super_admin), `scope`, `description`", "1:N role_assignments"],
            ["`role_assignments` *", "A scoped grant. Platform grants have no Ajo; Ajo grants name exactly one Ajo.", "`role_id`, `user_id`, `scope`, `ajo_id` (nullable), `granted_by_user_id`, `expires_at`", "N:1 roles; N:1 users; 0:1 ajos; N:1 ajo_members"],
            ["`sessions` S", "Device sessions and revocation, serving `GET /auth/sessions` and the `security.login_new_device` alert.", "`user_id`, `refresh_token_hash`, `device_label`, `ip_address`, `user_agent`, `last_active_at`, `revoked_at`", "N:1 users; 0:1 device_tokens"],
            ["`device_tokens` S", "Push targets. A token is superseded, not deleted, so a notification in flight still reports.", "`user_id`, `session_id`, `platform`, `push_token` (unique), `last_seen_at`, `revoked_at`", "N:1 users; 0:1 sessions"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["users -> profiles", "1:1", "1:1", "`profiles.user_id` UNIQUE", "Exactly one profile per user, created with the user in the same transaction. `UNIQUE (user_id)` and `NOT NULL`.", "CASCADE on delete. No money, no history, recreatable."],
            ["users -> admins", "1:1", "1:1", "`admins.user_id` UNIQUE", "Exactly one admin record per user who has one. Absence means not an admin; there is no default row.", "CASCADE. Revoking operator status is `status`, not deletion."],
            ["users -> verification_checks", "1:N", "1:N", "`verification_checks.user_id`", "At least one check before a user can hold an active `ajo_members` row. Checks are never edited after decision; a re-check is a new row.", "RESTRICT. Deleting a user must not erase the fact that they were or were not verified."],
            ["verification_checks -> documents", "1:N", "1:N", "`documents.verification_check_id`", "The document submitted as evidence for that check. `ON DELETE SET NULL` so the document's existence outlives the check reference.", "SET NULL. The document row survives and remains disclosable."],
            ["users -> documents", "1:N", "1:N", "`documents.owner_user_id`", "Every document has exactly one owner, even when it also belongs to a check or a dispute.", "RESTRICT. Ownership of evidence is not transferable by deletion."],
            ["profiles -> documents", "1:N", "0:1", "`profiles.avatar_document_id`", "An avatar is a document owned by the same user. Guarded by a trigger that rejects a cross-user avatar.", "SET NULL. A user can lose an avatar without losing the file record."],
            ["users -> sessions", "1:N", "1:N", "`sessions.user_id`", "Many concurrent devices. `refresh_token_hash` stores a hash, never the token. Revocation is `revoked_at`, not delete.", "CASCADE. A deleted user has no sessions; audit of the deletion is in audit_logs."],
            ["users -> device_tokens", "1:N", "1:N", "`device_tokens.user_id`", "A token belongs to one user and one session. `UNIQUE (push_token)` because a token is a device, not a person.", "CASCADE. Push targets are infrastructure, not records."],
            ["users <-> roles", "M:N", "M:N", "via `role_assignments`", "UNIQUE (`role_id`, `user_id`) WHERE `scope='platform'`. Exactly the six codes in CANONICAL.md section 2; anything else is rejected by a CHECK on `roles.code`.", "CASCADE on `role_assignments` rows. Deleting a role is RESTRICT and is not an operation the product performs."],
            ["role_assignments -> ajos", "1:N", "0:1", "`role_assignments.ajo_id`", "Ajo-scoped grant. `CHECK (num_nonnulls(ajo_id, ajo_member_id) <= 1)` and `CHECK ((scope='platform') = (ajo_id IS NULL))` so scope and target cannot disagree.", "CASCADE. The grant dies with the Ajo; the audit_log row does not."],
            ["users -> audit_logs", "1:N", "1:N", "`audit_logs.actor_user_id`", "Every privileged mutation writes one row with before and after images. Append-only.", "RESTRICT. See 8.7."],
            ["users -> risk_events", "1:N", "1:N", "polymorphic `subject_id`", "Freeze, review and override decisions attach to a user without a hard foreign key, so the event survives the subject.", "No cascade. A risk event is evidence."],
        ],
    },

    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "KYC retention and special-category data",
        "text": (
            "Identity documents, selfies and any biometric-adjacent artefact captured for "
            "liveness are special-category personal data under the Nigeria Data Protection "
            "Act 2023 and require a lawful basis, explicit notice to the data subject, and a "
            "defined retention period. BVN is treated here as follows: the full value is "
            "never stored; only `bvn_last4` and a keyed hash are, and the verification itself "
            "is performed by the provider. Retention periods for KYC records, and whether "
            "anti-money-laundering record-keeping obligations override a data subject's "
            "erasure request, are questions for qualified Nigerian counsel and the appointed "
            "compliance adviser. No period is asserted in this specification. The same caveat "
            "applies to `documents`, whose retention is discussed in 8.9."
        ),
    },

    # ---------------------------------------------------------------- 8.3.2
    {"t": "h3", "text": "8.3.2 Ajo lifecycle"},

    {
        "t": "p",
        "text": (
            "Four entities, and they carry the whole of CANONICAL.md section 3. The state "
            "machine lives on `ajos.status`; the position order lives on `ajo_positions`; "
            "membership lives on `ajo_members`; and the pre-activation join flow lives on "
            "`invitations`. The two rules that are structural rather than procedural are "
            "encoded here rather than in application code: the enrollment window is exactly "
            "five days, and positions lock on activation."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`ajos` *", "The savings group and the root of the lifecycle. Holds the amount and frequency every other table derives from.", "`organizer_user_id`, `status`, `contribution_amount_kobo`, `frequency_id`, `position_count`, `total_rounds`, `enrollment_opens_at`, `enrollment_closes_at`, `activated_at`", "1:N to positions, members, invitations, rounds, schedules, contributions, payouts, disputes"],
            ["`ajo_positions` *", "The turn order. Created in `DRAFT`, filled during the five-day window, locked on activation, never renumbered after.", "`ajo_id`, `position_number`, `status` (open, claimed, locked, released, replaced, forfeited), `locked_at`, `released_at`", "1:N from ajos; 1:N to members, invitations, contributions, payouts"],
            ["`ajo_members` *", "A person inside an Ajo. Carries member status and, once claimed, the position they hold. The join entity for users-to-ajos.", "`ajo_id`, `user_id`, `position_id`, `status` (invited, active, defaulted, replaced, exited, removed), `invited_at`, `joined_at`, `left_at`", "N:1 ajos, users; 0:1 ajo_positions; 1:N to contributions, role_assignments"],
            ["`invitations` *", "A single-use, expiring, hashed-token invitation to a specific Ajo and optionally a specific position.", "`ajo_id`, `position_id`, `email`, `token_hash` UNIQUE, `status` (pending, accepted, declined, expired, revoked), `expires_at`, `accepted_at`", "N:1 ajos, ajo_positions, users (invited_by); 0:1 ajo_members (created on accept)"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["users -> ajos", "1:N", "1:N", "`ajos.organizer_user_id`", "Exactly one organizer per Ajo, and the organizer is always also a member. **The creator occupies one of the `position_count` positions rather than sitting outside them**, so a ten-member Ajo is one organizer and nine invitees. Cancellation, freezing and payout-release requests are authorized on this column.", "RESTRICT. An Ajo is never deleted while it has positions; cancellation is a state, not a delete."],
            ["ajos -> ajo_positions", "1:N", "1:N", "`ajo_positions.ajo_id`", "`UNIQUE (ajo_id, position_number)`. `CHECK (position_number BETWEEN 1 AND position_count)`. Rows are materialised in `DRAFT` and never deleted afterwards.", "RESTRICT. Positions are the turn order; deleting one is reordering by deletion, which CANONICAL.md section 3 forbids."],
            ["ajos -> ajo_members", "1:N", "1:N", "`ajo_members.ajo_id`", "`UNIQUE (ajo_id, user_id)`. A user holds at most one membership per Ajo, and at most one position per Ajo: `UNIQUE (ajo_id, position_id) WHERE position_id IS NOT NULL AND released_at IS NULL`.", "RESTRICT. Removal is `status='removed'` plus `deleted_at`; the row stays so a receipt can always be tied to a member."],
            ["users -> ajo_members", "1:N", "1:N", "`ajo_members.user_id`", "A user may be in many Ajos. A membership requires an accepted invitation or an organizer-added row in `ENROLLMENT` only.", "RESTRICT. A user record is never deleted by a membership operation."],
            ["ajo_positions -> ajo_members", "1:1", "0..1", "`ajo_members.position_id`", "A position is occupied if and only if exactly one live membership points at it. Occupancy is derived, never stored twice. Claiming takes a row lock (section 9.8).", "SET NULL on release, and `released_at` is stamped. This is the only supported way a position becomes open after activation."],
            ["ajos -> invitations", "1:N", "1:N", "`invitations.ajo_id`", "`UNIQUE (ajo_id, email) WHERE status = 'pending'` so an organizer cannot send two live invitations to the same address. Token is stored as a hash; the plaintext exists only in the email.", "CASCADE. An invitation is a pre-activation artefact with no financial history. Once accepted, the `ajo_members` row is what matters and it does not cascade."],
            ["ajo_positions -> invitations", "1:N", "0:1", "`invitations.position_id`", "Optional. An invitation may name the position it offers, or may be a general invitation to any open position.", "SET NULL. Revoking an invitation must not delete a position."],
            ["invitations -> ajo_members", "1:1", "0:1", "`ajo_members.invitation_id`", "Created in the same transaction that flips the invitation to `accepted`. `UNIQUE (invitation_id)` so an invitation cannot mint two memberships.", "RESTRICT. Two paths to a membership (invitation and organizer add) are possible, so this FK is nullable by design."],
            ["ajos -> role_assignments", "1:N", "0:1", "`role_assignments.ajo_id`", "Only `ajo_organizer` is granted at Ajo scope in v1. Ajo-scoped grants cannot outlive the Ajo: `expires_at` is set to the Ajo's `completed_at` at creation.", "CASCADE. A grant to a cancelled Ajo is meaningless and is removed with it."],
            ["ajos -> payment_channels", "1:N", "0:1", "`ajos.preferred_channel_id`", "Optional. Where null, the member's default from `profiles` applies. Nullability rather than a default row, so that 'no preference' is representable.", "RESTRICT. Channels are configuration and are deactivated, never deleted."],
        ],
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Positions lock on activation, and the schema says so",
        "text": (
            "CANONICAL.md section 3 states that payout positions lock on activation and that "
            "reordering afterwards requires a formal replacement or transfer request. That is "
            "encoded twice: as a trigger `app.assert_positions_locked()` that rejects any "
            "UPDATE touching `position_number`, `ajo_id` or `status` on `ajo_positions` while "
            "`ajos.status IN ('ACTIVE','ROUND_IN_PROGRESS','COMPLETED')`, and as the absence of "
            "any endpoint in CANONICAL.md section 6 that can reorder. The trigger is the "
            "enforcement; the endpoint absence is the belt."
        ),
    },

    # ---------------------------------------------------------------- 8.3.3
    {"t": "h3", "text": "8.3.3 Scheduling"},

    {
        "t": "p",
        "text": (
            "Two entities, and the distinction between them is the single most common source "
            "of confusion in a rotating savings product. `rounds` is the rotation step: the "
            "thing that gets funded and paid out. `contribution_schedules` is the payment plan "
            "for that step: who is expected to pay, by when, and how much. A round is a fact "
            "about the Ajo; a schedule is an obligation to a person. The Ajo's organizer does "
            "not get a schedule for themselves; every other live member gets exactly one, and "
            "the constraint that enforces it is in 8.8."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`rounds` *", "One rotation step of one Ajo. Carries the funding state, the collected base pool and the fee total.", "`ajo_id`, `round_number`, `status`, `due_date`, `opens_at`, `closes_at`, `target_amount_kobo`, `base_pool_kobo`, `fee_collected_kobo`, `completed_at`", "1:N from ajos; 1:N to schedules, contributions, payouts, disputes"],
            ["`contribution_schedules` *", "The plan for one round: who owes what, by when, and the cutoff after which late is assumed.", "`round_id`, `ajo_id`, `due_date`, `expected_amount_kobo`, `expected_member_count`, `late_cutoff_at`, `status`", "1:N from rounds; 1:N to contributions"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["ajos -> rounds", "1:N", "1:N", "`rounds.ajo_id`", "`UNIQUE (ajo_id, round_number)` and `CHECK (round_number >= 1)`. A partial unique index permits at most one `IN_PROGRESS` round per Ajo, so two rounds can never be funding at once.", "RESTRICT. Rounds are the financial spine of an Ajo. A cancelled Ajo keeps its rounds."],
            ["rounds -> contribution_schedules", "1:1", "1:1", "`contribution_schedules.round_id` UNIQUE", "Exactly one schedule per round, created atomically when the round opens, so that a round can never be funding with no obligations attached.", "CASCADE. A schedule with no round is meaningless and is created in the same transaction as its round."],
            ["ajos -> contribution_schedules", "1:N", "1:1", "`contribution_schedules.ajo_id`", "Deliberate denormalisation of the Ajo onto the schedule. It exists so the row-level security policy in section 9.6 can filter on a single column and so the member's obligation screen needs one index, not a three-table join.", "CASCADE. A deleted Ajo takes its schedules; blocked in practice by the RESTRICT on rounds."],
            ["contribution_frequencies -> ajos", "1:N", "1:N", "`ajos.frequency_id`", "Frequency is a lookup row, not an enum, because it is business-configurable. Round due dates are materialised onto `rounds.due_date` at round creation so that changing the Ajo's frequency later never rewrites history.", "RESTRICT. A frequency in use is deactivated (`is_active=false`), never deleted."],
            ["rounds -> contribution_schedules (amount)", "1:1", "1:1", "`expected_amount_kobo`", "Every schedule row for a round carries the same amount, denormalised from `ajos.contribution_amount_kobo`, and a deferred trigger asserts equality. A member's obligation is readable without joining the Ajo, which is the difference between one query and a correlated subquery on the hottest read in the product.", "n/a. This is a value rule, not a referential action."],
        ],
    },

    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "One schedule per round",
        "text": (
            "CANONICAL.md does not state whether a round may have more than one schedule "
            "(for example a base schedule and a catch-up schedule after a frozen period). v1 "
            "assumes one schedule per round, with the `UNIQUE (round_id)` constraint enforcing "
            "it, because a second schedule introduces a question this specification cannot yet "
            "answer: whether a member's obligation is the sum of their schedule rows or the "
            "row for the current round. If AJO.ng later needs staggered or partial collection "
            "within a round, the constraint becomes `UNIQUE (round_id, instalment_number)` and "
            "`contributions` gains `schedule_id` to a non-unique parent, which already "
            "supports it. The decision owner is the founders, and it is recorded as open."
        ),
    },

    # ---------------------------------------------------------------- 8.3.4
    {"t": "pagebreak"},
    {"t": "h3", "text": "8.3.4 Money"},

    {
        "t": "p",
        "text": (
            "Nine entities, and the only domain in this specification where a mistake is "
            "unrecoverable. The structure has four layers and the layers do not overlap. The "
            "obligation layer (`contributions`) records who owes what. The provider layer "
            "(`payments`, `payouts`) records what we told the provider and what it told us. "
            "The recognition layer (`ledger_transactions`, `ledger_postings`) records the "
            "economic truth, and it is the only layer that is authoritative. The "
            "assurance layer (`reconciliation_runs`, `webhook_events`, `idempotency_keys`) "
            "proves the first three agree with each other and with the outside world."
        ),
    },

    {
        "t": "callout",
        "kind": "WARNING",
        "title": "The four-step sequence is not optional and not reorderable",
        "text": (
            "CANONICAL.md section 4 fixes the recognition order: `contribution.received`, then "
            "`fee.recognised`, then `payout.recognized`, then `payout.settled`. Skipping step 3 "
            "causes escrow to drain against a liability that was never raised, and the "
            "solvency assertion correctly halts disbursement. The schema enforces the order "
            "with a `ledger_txn_kind` enum whose first four values are the sequence, plus a "
            "deferred trigger `app.assert_ledger_sequence()` that rejects a `payout.settled` "
            "whose `payout.recognized` predecessor does not exist and already balance. The "
            "database will refuse an out-of-order disbursement even if application code is "
            "wrong."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`contributions` *", "One member's obligation for one round and whether it was met. The `PENDING -> PAID -> OVERDUE -> GRACE -> DEFAULTED -> RECOVERED | WRITTEN_OFF` machine from CANONICAL.md section 4.", "`schedule_id`, `member_id`, `position_id`, `amount_kobo`, `fee_kobo`, `status`, `due_date`, `paid_at`, `defaulted_at`, `superseded_at`", "N:1 to schedules, members, rounds; 1:N payments; 1:N disputes"],
            ["`payments` *", "One collection attempt. Carries the whole 2% split on the row: base, fee, and the amount actually charged.", "`contribution_id`, `channel_id`, `provider`, `provider_reference`, `contribution_amount_kobo`, `fee_kobo`, `charged_amount_kobo`, `status`, `provider_created_at`, `settled_at`", "N:1 contributions and payment_channels; 1:1 fees; 0:1 webhook_events; N:1 risk_events"],
            ["`payouts` *", "One disbursement for one position in one round. `SCHEDULED -> FUNDING -> RELEASED -> SUCCESS | FAILED | HELD` per CANONICAL.md section 4.", "`round_id`, `position_id`, `member_id`, `base_pool_kobo`, `amount_kobo`, `fee_kobo` (0 by construction), `status`, `provider`, `provider_reference`, `held_reason`", "N:1 rounds, positions, members; 1:1 per (round, position); 1:N disputes, risk_events"],
            ["`fees` *", "The platform's own record of the 2% charge. Separate from the member's payment so that revenue reporting never depends on joining the payment table. The column is `fee_kobo`, matching `payments.fee_kobo`, and it is generated: a fee an application could write is a fee that can be wrong.", "`payment_id` UNIQUE, `contribution_id`, `contribution_amount_kobo`, `fee_kobo` (generated), `fee_rate_bps`, `status` (accrued, invoiced, refunded, written_off), `ledger_transaction_id`, `disclosed_at`", "1:1 payments; 0:1 ledger_transactions; 1:1 contributions"],
            ["`ledger_transactions` *", "Header of an append-only double-entry transaction. `kind` is the canonical sequence. Corrections are reversals, never updates.", "`kind`, `ajo_id`, `round_id`, `member_id`, `occurred_at`, `reverses_transaction_id`, `reversal_reason`, `request_id`, `idempotency_key`", "1:N ledger_postings; 0:1 reversal target; 0:1 fees; 0:1 idempotency_keys"],
            ["`ledger_postings` *", "The legs. Two or more per transaction, and the signed sum of one transaction is exactly zero. No `updated_at`, no `deleted_at`.", "`transaction_id`, `account_kind`, `side` (debit, credit), `amount_kobo`, `signed_kobo` (generated), `member_id`, `memo`", "N:1 ledger_transactions; 0:1 members, ajos, rounds (denormalised for reporting)"],
            ["`idempotency_keys` *", "The retried-request ledger. Stores the request hash and the response so a replay returns the original answer rather than a new one.", "`key` (PK), `user_id`, `route`, `request_hash`, `state` (in_progress, completed, failed), `response_status`, `response_body`, `resource_type`, `resource_id`, `expires_at`", "N:1 users; 0:1 ledger_transactions"],
            ["`webhook_events` *", "Inbound provider callbacks, deduplicated on the provider's own event id. Written before processing, so a crash between receive and process is recoverable.", "`provider`, `provider_event_id` (UNIQUE with provider), `event_type`, `signature_verified`, `raw_payload`, `status`, `attempts`, `next_retry_at`", "0:1 payments; N:1 ajos (for pinoout routing)"],
            ["`reconciliation_runs` *", "A proof, over a time window, that the internal ledger agrees with the provider and with round expectations. The artefact a regulator or an auditor asks for.", "`run_type`, `window_start`, `window_end`, `status`, `expected_kobo`, `actual_kobo`, `variance_kobo`, `findings` (jsonb), `started_at`, `finished_at`", "References a time window, not an entity, so it survives every table it checks"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["contribution_schedules -> contributions", "1:N", "1:N", "`contributions.schedule_id`", "`UNIQUE (schedule_id, member_id)`: exactly one obligation per member per schedule. Plus a partial unique on (`schedule_id`, `position_id`) WHERE `superseded_at IS NULL`, so exactly one *live* obligation per position slot survives a replacement.", "RESTRICT. A contribution is a debt record. Schedules are never deleted with contributions attached."],
            ["ajo_members -> contributions", "1:N", "1:N", "`contributions.member_id`", "A member owes in every round for as long as they are `active`. Removing a member sets `status='removed'` and stops future schedules; existing obligations remain and are still collectable.", "RESTRICT. A member who has ever owed money is never cascade-deleted from a contribution."],
            ["ajos -> contributions", "1:N", "1:N", "`contributions.ajo_id`", "Denormalised onto the contribution for the same reason as the schedule: the member's contribution list is the single hottest read in the product and it filters on one column.", "RESTRICT. Cancelled and completed Ajos keep their contributions forever, because a refund is a ledger event, not a deletion."],
            ["contributions -> payments", "1:N", "1:N", "`payments.contribution_id`", "Multiple attempts are rows, not edits. `UNIQUE (provider, provider_reference)` for provider dedupe, and a partial unique permitting at most one `SUCCESS` payment per contribution: `CREATE UNIQUE INDEX payments_one_success_per_contribution ON payments (contribution_id) WHERE status = 'success'`.", "RESTRICT. Never delete a payment to make room for a retry."],
            ["payments -> fees", "1:1", "1:1", "`fees.payment_id` UNIQUE", "Exactly one fee row per settled payment. A deferred trigger asserts `fees.fee_kobo = payments.fee_kobo` and that the fee is exactly `(contribution_amount_kobo * 200 + 5000) / 10000`, half-up, in integer kobo. Both sides are generated columns, so the trigger is a backstop rather than the primary mechanism.", "RESTRICT. Fee records are revenue records. A refunded fee is `status='refunded'`, never a delete."],
            ["payment_channels -> payments", "1:N", "1:N", "`payments.channel_id`", "The provider channel code lives on the lookup row so that a change of provider does not require rewriting history. `CHECK (amount_kobo BETWEEN min_amount_kobo AND max_amount_kobo)` is validated in application, the row is the source of the limits.", "RESTRICT. Channels are deactivated, not deleted."],
            ["rounds -> payouts", "1:N", "1:N", "`payouts.round_id`", "`UNIQUE (round_id, position_id)`: exactly one payout per position per round. A failed payout is retried by updating the same row's status, never by inserting a second one.", "RESTRICT. This is the table the funding principle in CANONICAL.md section 4 depends on."],
            ["ajo_positions -> payouts", "1:1", "0:1", "`payouts.position_id`", "A position receives at most one payout, and `CHECK (payouts.amount_kobo = payouts.base_pool_kobo)` is the schema's statement that the fee never reduces a payout. The base pool is the sum of that round's paid contributions and nothing else.", "RESTRICT. A position is never removed because a payout exists."],
            ["ledger_transactions -> ledger_postings", "1:N", "1:N", "`ledger_postings.transaction_id` DEFERRABLE INITIALLY DEFERRED", "At least two postings per transaction, and the signed sum is exactly zero, enforced by a deferred constraint trigger at commit. The deferrable foreign key is what allows the two legs to be inserted in either order inside one database transaction.", "CASCADE is *declared* RESTRICT in practice: the append-only trigger blocks DELETE on both tables, and the `REVOKE` removes DELETE from the client roles. The referential action is never reached."],
            ["ledger_transactions -> ledger_transactions", "1:1", "0:1", "`ledger_transactions.reverses_transaction_id`", "A reversal mirrors the original exactly. `CHECK ((kind = 'reversal') = (reverses_transaction_id IS NOT NULL))` and a deferred trigger rejects reversing a reversal, so reversals are one level deep.", "RESTRICT. Both rows are permanent."],
            ["users -> idempotency_keys", "1:N", "1:N", "`idempotency_keys.user_id`", "One row per key. The key is client-supplied and globally unique; the user and route are recorded so a replay by a different user is rejected rather than served.", "CASCADE. Keys expire (section 9.7) and are the one money-domain table that may be removed without loss."],
            ["idempotency_keys -> ledger_transactions", "1:1", "0:1", "`ledger_transactions.idempotency_key`", "The ledger records the key that produced it. A replay that reaches the ledger therefore cannot produce a second transaction, because the ledger's own lookup short-circuits first.", "RESTRICT. A transaction outlives its key's TTL."],
            ["webhook_events -> payments", "1:1", "0:1", "`payments.webhook_event_id`", "Set when the callback is the thing that finalised the payment. A `FAILED` signature is never linked. A payment may be created by a synchronous verify call instead, which is why this FK is nullable.", "RESTRICT. The event is the evidence; the payment is the record."],
        ],
    },

    {
        "t": "code",
        "text": """
THE FOUR CANONICAL POSTINGS, AS STORED
========================================================================
Worked example from CANONICAL.md section 1: ten members, NGN 1,000.00
each. All figures in kobo. The recipient receives the BASE pool.

 STEP  kind                  DEBIT                     CREDIT
 ----  --------------------  ------------------------  --------------------
  1    contribution.         escrow_cash   100,000    contributions_
       received              (x10 = 1,000,000)        receivable
                                                      1,000,000
  2    fee.recognised        escrow_cash      20,000  fees_income
                              (x10 =   200,000)            200,000
  3    payout.recognized     contributions_           payouts_payable
                             receivable     1,000,000       1,000,000
  4    payout.settled        payouts_payable 1,000,000  escrow_cash
                                                      1,000,000

 MEMBER-SIDE, for the one who pays
   contribution_amount_kobo = 100,000   (NGN 1,000.00  -> the round pool)
   fee_kobo                 =   2,000   (NGN    20.00  -> fees_income)
   charged_amount_kobo      = 102,000   (NGN 1,020.00  -> what is debited)

 ACROSS THE WHOLE AJO, TEN ROUNDS
   each member pays        NGN  10,200.00  in total (10 x NGN 1,020.00)
   the recipient receives   NGN  10,000.00  (the base pool, never
                                             NGN 10,200.00)
   AJO.ng retains          NGN   2,000.00
   total collected          NGN 102,000.00

 PER TRANSACTION INVARIANT
   SUM(signed_kobo) = 0, checked by a DEFERRABLE INITIALLY DEFERRED
   constraint trigger at COMMIT. 100,000 - 100,000 = 0. Always.
========================================================================
""",
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The fee is on the member's charge, never on the payout",
        "text": (
            "Steps 1 and 2 together lift NGN 1,020.00 of cash, but they lift it into two "
            "different destinations: the round pool and fees_income. Step 3 then moves exactly "
            "the base pool out of contributions_receivable. There is no arithmetic path by "
            "which the fee can reach the recipient, and section 9.5 adds a CHECK constraint so "
            "that even an application bug cannot construct one. This is the single most "
            "important structural statement in the specification and it is why `payouts` "
            "carries both `base_pool_kobo` and `amount_kobo` with a constraint that they are "
            "equal."
        ),
    },

    # ---------------------------------------------------------------- 8.3.5
    {"t": "h3", "text": "8.3.5 Trust and risk"},

    {
        "t": "p",
        "text": (
            "Three entities, and they exist because a rotating savings scheme runs on trust "
            "that is not contractual in the way a bank balance is. `disputes` is the member's "
            "route out. `risk_events` is the platform's route to noticing. `audit_logs` is the "
            "route to explaining afterwards. All three are append-only or near-append-only, "
            "and all three are polymorphic in subject where that avoids a foreign key into the "
            "thing they describe."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`disputes` *", "A member challenge against a contribution, a payout, or another member. Its own lifecycle, separate from the ledger correction that may follow it.", "`ajo_id`, `round_id`, `raised_by_user_id`, `against_user_id`, `contribution_id`, `payout_id`, `category`, `status`, `resolution`, `resolved_at`", "1:N from ajos, rounds, users, contributions, payouts; 1:N to messages and evidence"],
            ["`risk_events` *", "A signal and a decision. Records what was noticed about a user, Ajo, payment or payout and what was done about it.", "`subject_type`, `subject_id`, `event_type`, `severity`, `status`, `decision`, `score`, `signals` (jsonb), `decided_by_user_id`, `decided_at`", "Polymorphic over users, ajos, payments, payouts"],
            ["`audit_logs` *", "Immutable record of every privileged mutation, with before and after images, the actor, the request id and the originating address.", "`actor_user_id`, `actor_role_code`, `actor_type` (user, system, admin), `action`, `subject_type`, `subject_id`, `before_state` (jsonb), `after_state` (jsonb), `request_id`, `ip_address`, `user_agent`, `amount_kobo`, `occurred_at`", "N:1 users; polymorphic over every mutable table"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["users -> disputes", "1:N", "1:N", "`disputes.raised_by_user_id`, `against_user_id`", "A dispute is raised by a member about their own contribution or payout. `CHECK (raised_by_user_id <> against_user_id)` so nobody disputes themselves, which would otherwise be a route to a free support escalation.", "RESTRICT. A member who has disputed cannot be deleted."],
            ["ajos -> disputes", "1:N", "1:N", "`disputes.ajo_id`", "A dispute never leaves its Ajo. Cross-Ajo disputes are a different product and are not designed for here.", "RESTRICT."],
            ["contributions -> disputes", "1:N", "1:N", "`disputes.contribution_id`", "At most one of `contribution_id` and `payout_id` is set for a collection dispute; a payout dispute sets only `payout_id`. Checked in application, not by constraint, because a dispute may concern either.", "RESTRICT."],
            ["payouts -> disputes", "1:N", "1:N", "`disputes.payout_id`", "A disputed payout enters `HELD` (CANONICAL.md section 4) and does not settle until the dispute closes.", "RESTRICT."],
            ["disputes -> dispute_messages", "1:N", "1:N", "`dispute_messages.dispute_id`", "Append-only conversation. Messages are visible to the parties and to `support`; never to other members, which is the privacy rule in CANONICAL.md section 2.", "CASCADE. A dispute with no conversation is not a dispute."],
            ["disputes -> dispute_evidence", "1:N", "1:N", "`dispute_evidence.dispute_id`", "Each row references a `documents` row rather than storing a file itself, so that one upload can be referenced by a check and a dispute without duplication.", "CASCADE on the link. The underlying `documents` row is RESTRICT and is governed by its own retention."],
            ["users, ajos, payments, payouts -> risk_events", "polymorphic", "1:N", "`risk_events.subject_type` + `subject_id`", "No hard foreign key. This is deliberate: a risk decision must survive the deletion of its subject, and a foreign key would either block the deletion or cascade the evidence away. Integrity is maintained by a deferred trigger that checks the subject exists *at insert time* only.", "No cascade, ever. Risk evidence is not disposable."],
            ["every table -> audit_logs", "polymorphic", "1:N", "`audit_logs.subject_type` + `subject_id`", "One row per privileged mutation. Written by a trigger `app.audit_row()` on the tables listed in section 9.13, and by the service layer for business-level events. Includes `request_id` so a support ticket can be traced to an exact HTTP request.", "No cascade, ever. The audit trail must not be deleted by the thing it audits."],
        ],
    },

    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Dispute, default and record-keeping",
        "text": (
            "CANONICAL.md section 4 fixes that defaulting is private between the member, the "
            "organizer and platform risk, and that no member is publicly shamed or exposed. "
            "The data model supports that: `ajo_members.status = 'defaulted'` is visible only "
            "to the member, the organizer, `support` and `risk_officer`, enforced by the "
            "row-level security policies in section 9.6 and not by UI concealment. Whether any "
            "of these records must be produced to a regulator, a law-enforcement request or in "
            "civil recovery proceedings, on what timescale and under what authority, requires "
            "confirmation by qualified Nigerian counsel. A member's dispute file should be "
            "assumed discoverable; the schema is built on that assumption rather than against "
            "it."
        ),
    },

    # ---------------------------------------------------------------- 8.3.6
    {"t": "h3", "text": "8.3.6 Engagement"},

    {
        "t": "p",
        "text": (
            "Three entities for keeping people informed and helped. The rule from CANONICAL.md "
            "section 8 that SMS is reserved for money-critical and security events is not a "
            "UI convention here; it is a column on `notification_templates` and a constraint "
            "that rejects a template without an SMS row for any event flagged money-critical "
            "or security-critical. Support lives here rather than in Trust and Risk precisely "
            "because the `support` role cannot move money, and the schema keeps that "
            "separation visible: `support_tickets` has no foreign key to any money table."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Purpose", "Key fields", "Relationships"],
        "widths": [1.15, 1.95, 1.85, 1.55],
        "size": 7.6,
        "rows": [
            ["`notifications` *", "One notification instance to one user, on one channel. The queue and the inbox are the same row; `read_at` distinguishes them.", "`user_id`, `template_id`, `event_key`, `channel`, `status`, `subject`, `body`, `payload` (jsonb), `dedupe_key`, `scheduled_for`, `sent_at`, `read_at`", "N:1 users and notification_templates"],
            ["`notification_preferences` *", "Per-user channel opt-in. Defaults come from the catalogue, not from the user's history, so a new user is safe by default rather than noisy by default.", "`user_id` UNIQUE, `push_enabled`, `email_enabled`, `sms_enabled`, `quiet_hours_start`, `quiet_hours_end`, `money_sms_opt_in`", "1:1 users"],
            ["`support_tickets` S", "A support conversation that is not a dispute and has no access to money. `thread` is a jsonb array because a support thread is small, append-in-order, and never queried relationally.", "`user_id`, `ajo_id`, `category`, `subject`, `status`, `priority`, `assigned_to_user_id`, `thread` (jsonb), `resolved_at`", "N:1 users; 0:1 ajos; 0:1 users (assignee)"],
        ],
    },

    {
        "t": "table",
        "head": ["Relationship", "Type", "Card.", "FK", "Rule", "Cascade behaviour"],
        "widths": [1.15, 0.62, 0.5, 0.85, 1.7, 1.68],
        "size": 7.2,
        "rows": [
            ["users -> notification_preferences", "1:1", "1:1", "`notification_preferences.user_id` UNIQUE", "Created with the user. `CHECK (money_sms_opt_in = false OR sms_enabled = true)`: a member cannot opt into money SMS while SMS is off, which would otherwise silently suppress the payout alerts in CANONICAL.md section 8.", "CASCADE. Preferences are settings, not records."],
            ["users -> notifications", "1:N", "1:N", "`notifications.user_id`", "One row per recipient per channel per event. `UNIQUE (dedupe_key, channel)` is what stops a retried webhook sending the same receipt four times.", "CASCADE. Notifications are derived, and the source event is the record."],
            ["notification_templates -> notifications", "1:N", "1:N", "`notifications.template_id`", "`UNIQUE (event_key, channel)` on the template. A deferred trigger rejects a template set that omits SMS for any `event_key` flagged money-critical or security-critical.", "RESTRICT. A template in use is deactivated, not deleted; deleting it would orphan the reason a notification was sent."],
            ["users -> support_tickets", "1:N", "1:N", "`support_tickets.user_id`", "A member opens a ticket about their own account or Ajos. `support` may read and reply; `support` may not write to any table in the money domain, and no support table has an FK into one.", "CASCADE. Support conversations are not financial records."],
            ["ajos -> support_tickets", "1:N", "0:1", "`support_tickets.ajo_id`", "Optional context. A ticket about an Ajo can be read by that Ajo's members only if `visibility` permits; default is private to the requester and `support`.", "SET NULL. A deleted or anonymised Ajo does not take a support thread with it, and vice versa."],
        ],
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Why support is not in the money domain",
        "text": (
            "CANONICAL.md section 2 gives `support` the ability to read all records and assist "
            "with disputes, and the explicit inability to move money or alter financial "
            "records. The strongest way to enforce that is structural rather than procedural: "
            "no table reachable from `support_tickets` has a foreign key into `payments`, "
            "`payouts`, `fees` or the ledger, and the row-level security policies in section "
            "9.6 grant `support` SELECT only. A support agent who is tricked into editing a "
            "payout is refused by the database, not by a training module."
        ),
    },

    # =====================================================================
    # 8.4
    # =====================================================================
    {"t": "pagebreak"},
    {"t": "h2", "text": "8.4 One-to-one relationships"},

    {
        "t": "p",
        "text": (
            "Only five one-to-one relationships exist in the model, and that scarcity is "
            "deliberate. A one-to-one relationship in a database is a claim that a concept is "
            "genuinely different from its parent and yet always coexists with it. Most claims "
            "of that kind are wrong, and the usual result of a wrong claim is a table whose "
            "rows are fetched with a second query on every read. Where a one-to-one is used "
            "here, there is a reason, and the reason is stated."
        ),
    },

    {
        "t": "table",
        "head": ["Relationship", "Enforced by", "Card.", "FK", "Rationale, and why not a column"],
        "widths": [1.35, 1.15, 0.5, 1.0, 2.5],
        "size": 7.4,
        "rows": [
            ["`users` -> `profiles`", "`UNIQUE (user_id)`", "1:1", "`profiles.user_id` NOT NULL", "A profile is created and destroyed with the account, so the natural design is a nullable set of columns on `users`. It is a separate table because profile writes are frequent, the profile is the largest thing a member list returns, and keeping them apart means a profile write never takes a row lock on the account row that authentication and role checks also read. The `UNIQUE` is what makes it one-to-one rather than one-to-many."],
            ["`users` -> `admins`", "`UNIQUE (user_id)`", "1:1", "`admins.user_id` NOT NULL", "Administrator is a fact about a person, not about a role, because a person has at most one operator identity across the platform regardless of how many role grants they hold. The row is optional, so most users have none. Absent row means not an operator; a default row for every user would be 400,000 rows of nothing at the base case."],
            ["`users` -> `notification_preferences`", "`UNIQUE (user_id)`", "1:1", "`notification_preferences.user_id` NOT NULL", "Preferences are read on every single notification dispatch, which is the hottest read in the product after the dashboard. A separate one-row-per-user table means that read is an index lookup on a narrow table and never touches `users`, which is wide and contended. Defaults live in `notification_templates`, so a preference row only records the differences."],
            ["`users` -> `auth.users`", "documented, not a DDL FK", "1:1", "`users.auth_subject_id`", "The identity provider owns credentials, MFA and sessions. A hard cross-schema foreign key to a table this application does not own is brittle: an Auth schema migration can break a domain migration, and a domain migration run as a different role may not be permitted to reference it. The link is therefore a `citext` column with a `UNIQUE` constraint, validated by the service layer, and the comment on the column records that it is `auth.users(id)`."],
            ["`payments` -> `webhook_events` (optional)", "`UNIQUE (webhook_event_id)` on `payments`", "0..1", "`payments.webhook_event_id`", "A payment is normally finalised by a webhook, and a webhook is exactly what can be replayed, so the relationship is worth pinning. It is 0..1 rather than 1:1 because a synchronous `POST /payments/:id/verify` can finalise a payment first, in which case the webhook that arrives afterwards records `status='duplicate'` and links nothing. The `UNIQUE` on `webhook_event_id` guarantees one payment per event."],
        ],
    },

    {
        "t": "callout",
        "kind": "DECISION",
        "title": "The four real one-to-ones and the one that is documentation",
        "text": (
            "`users.auth_subject_id` is the only one-to-one in this model with no foreign key. "
            "The alternative, a real reference to the provider's own identity table, was "
            "rejected because it couples AJO.ng's migration graph to a table AJO.ng does not "
            "control, and a broken reference there is a production outage in a domain that "
            "was working. The trade-off is real and is accepted: the service layer must "
            "validate the link, and a bug there produces a profile with no login rather than "
            "a corrupted account. The reverse relationship, from the identity provider into "
            "AJO.ng, is handled by the provider's own user-provisioning hook, not by a "
            "foreign key."
        ),
    },

    # =====================================================================
    # 8.5
    # =====================================================================
    {"t": "h2", "text": "8.5 One-to-many relationships"},

    {
        "t": "p",
        "text": (
            "The bulk of the model. Each row names the parent, the child, the cardinality, "
            "the minimum, and the rule that decides when a child may not exist. The minimum "
            "column is the one that is usually omitted and is the one that catches the bugs: "
            "a one-to-many is not the same as a has-many, and the difference is whether the "
            "parent is allowed to exist with none of the child."
        ),
    },

    {
        "t": "table",
        "head": ["Parent", "Child", "Min", "FK", "The rule that decides it"],
        "widths": [1.2, 1.35, 0.5, 1.15, 2.3],
        "size": 7.4,
        "rows": [
            ["`users`", "`profiles`", "1", "`profiles.user_id`", "Every account has a profile, created in the same transaction as the user."],
            ["`users`", "`verification_checks`", "0", "`verification_checks.user_id`", "Required before a user can be an active `ajo_member`, not before they can register."],
            ["`users`", "`documents`", "0", "`documents.owner_user_id`", "Every document belongs to exactly one person. `NULL` is impossible; absence of documents is fine."],
            ["`users`", "`sessions`", "0", "`sessions.user_id`", "A user with no sessions is either not logged in or fully logged out. Both are valid."],
            ["`users`", "`device_tokens`", "0", "`device_tokens.user_id`", "Web-only members never register one and are still fully served."],
            ["`users`", "`admins`", "0", "`admins.user_id`", "Absence means not an operator. `support` and `risk_officer` grants are separate rows in `role_assignments`."],
            ["`users`", "`notification_preferences`", "1", "`notification_preferences.user_id`", "Created with the account, seeded from the catalogue defaults."],
            ["`users`", "`notifications`", "0", "`notifications.user_id`", "The inbox is empty on day one and that is a normal state."],
            ["`users`", "`support_tickets`", "0", "`support_tickets.user_id`", "A user who has never needed support has no ticket."],
            ["`users`", "`ajos`", "0", "`ajos.organizer_user_id`", "A member who has never organised anything has no Ajo rows."],
            ["`users`", "`ajo_members`", "0", "`ajo_members.user_id`", "Registration does not enrol anybody anywhere. Membership is a separate, consented act."],
            ["`users`", "`invitations`", "0", "`invitations.invited_by_user_id`", "Invitations are sent by organizers, or by the platform for a support-assisted join."],
            ["`users`", "`idempotency_keys`", "0", "`idempotency_keys.user_id`", "Present only for operations that required a key, which is every money-moving `POST`."],
            ["`users`", "`audit_logs`", "0", "`audit_logs.actor_user_id`", "Only privileged mutations and authentications are audited, so most users have few."],
            ["`users`", "`disputes`", "0", "`disputes.raised_by_user_id`", "Raising one is an explicit act by a member in good standing."],
            ["`users`", "`risk_events`", "0", "polymorphic", "Risk attaches to a user as a subject, not as an owner."],
            ["`roles`", "`role_assignments`", "0", "`role_assignments.role_id`", "A role that has never been granted to anyone is legal, and is how the six canonical roles are seeded."],
            ["`admins`", "`role_assignments`", "1", "`role_assignments.granted_by_user_id`", "Platform-scoped grants name the operator who made them, which is required for the audit trail to be meaningful."],
            ["`ajos`", "`ajo_positions`", "2", "`ajo_positions.ajo_id`", "CANONICAL.md section 3: an Ajo has between 5 and 20 positions and may not leave `DRAFT` outside that range. Enforced by a CHECK plus a trigger, not only by the state machine."],
            ["`ajos`", "`ajo_members`", "1", "`ajo_members.ajo_id`", "The organizer is always a member, so an Ajo never exists with zero members."],
            ["`ajos`", "`invitations`", "0", "`invitations.ajo_id`", "An Ajo that filled by organizer add has no invitations."],
            ["`ajos`", "`rounds`", "0", "`rounds.ajo_id`", "Zero rounds in `DRAFT` is correct. Zero rounds in `ACTIVE` is a bug and is caught by a trigger."],
            ["`ajos`", "`contribution_schedules`", "0", "`contribution_schedules.ajo_id`", "Created with the round, so the count equals the round count."],
            ["`ajos`", "`contributions`", "0", "`contributions.ajo_id`", "Zero in `DRAFT` is correct; zero in `ACTIVE` is a bug."],
            ["`ajos`", "`payouts`", "0", "`payouts.ajo_id`", "One per completed round, less any forfeited or replaced positions."],
            ["`ajos`", "`disputes`", "0", "`disputes.ajo_id`", "Most Ajos never have one."],
            ["`ajos`", "`outbox_events`", "0", "`outbox_events.ajo_id`", "Present once anything money-moving has happened."],
            ["`ajo_positions`", "`invitations`", "0", "`invitations.position_id`", "An unpositioned general invitation has none."],
            ["`ajo_positions`", "`contributions`", "1", "`contributions.position_id`", "Every round, every live position slot, exactly one obligation. This is the 1:1 in 8.8."],
            ["`ajo_positions`", "`payouts`", "0", "`payouts.position_id`", "One per round, for the position whose turn it is."],
            ["`rounds`", "`contribution_schedules`", "1", "`contribution_schedules.round_id`", "A round that opens always has exactly one schedule. Created atomically."],
            ["`rounds`", "`contributions`", "0", "`contributions.round_id`", "A round with no contributions is one that has just opened."],
            ["`rounds`", "`payouts`", "0", "`payouts.round_id`", "Zero until the round funds; one when it does."],
            ["`contribution_schedules`", "`contributions`", "0", "`contributions.schedule_id`", "Zero when every position is already filled and paid, which is the normal case in a one-member-per-round Ajo."],
            ["`contributions`", "`payments`", "0", "`payments.contribution_id`", "Zero for a contribution never yet attempted. Many for one that has failed and retried."],
            ["`payments`", "`fees`", "1", "`fees.payment_id`", "Every settled payment carries exactly one fee row, even when the fee rounds to zero kobo, in which case the row is `status='written_off'` and carries no ledger link."],
            ["`ledger_transactions`", "`ledger_postings`", "2", "`ledger_postings.transaction_id`", "At least two. A one-legged transaction is a rejected transaction, enforced by the deferred balance trigger."],
            ["`ledger_transactions`", "reversals", "0", "`ledger_transactions.reverses_transaction_id`", "Zero for the overwhelming majority. A partial unique index permits at most one reversal per original, so a mistake cannot be reversed twice."],
            ["`notifications`", "`notification_templates`", "1", "`notifications.template_id`", "Every notification is generated from a template, so that copy is reviewable in one place rather than scattered through code."],
            ["`disputes`", "`dispute_messages`", "1", "`dispute_messages.dispute_id`", "A dispute with no opening message is rejected at the API, and the message is written in the same transaction as the dispute."],
            ["`disputes`", "`dispute_evidence`", "0", "`dispute_evidence.dispute_id`", "A dispute may be raised before evidence exists."],
        ],
    },

    # =====================================================================
    # 8.6
    # =====================================================================
    {"t": "h2", "text": "8.6 Many-to-many relationships"},

    {
        "t": "p",
        "text": (
            "Every many-to-many in this model is resolved by a join entity that is named in the "
            "specification and designed in its own right. The reason is not elegance. It is "
            "that in a savings product the join is almost always where the business rule "
            "lives: what the pair *means* (an Ajo membership, a role grant, an obligation), "
            "when it started and ended, and what state it is in. A join table with only two "
            "foreign keys cannot hold any of that, and the usual workaround, an "
            "`AjoUsers`-style association with attributes smeared back onto both parents, is "
            "worse."
        ),
    },

    {
        "t": "table",
        "head": ["Left", "Right", "Join entity", "The attribute the join carries", "Why not two FKs on one side"],
        "widths": [0.95, 0.95, 1.25, 1.7, 1.65],
        "size": 7.2,
        "rows": [
            ["`users`", "`roles`", "`role_assignments`", "`scope` (platform or ajo), `ajo_id`, `ajo_member_id`, `granted_by_user_id`, `expires_at`, `revoked_at`", "A role grant is not a boolean. `ajo_organizer` granted inside one Ajo is a different grant from `ajo_organizer` granted platform-wide, and only the scoped form can be revoked without removing the role everywhere."],
            ["`users`", "`ajos`", "`ajo_members`", "`status` (invited, active, defaulted, replaced, exited, removed), `position_id`, `joined_at`, `left_at`, `replaced_by_membership_id`", "Membership is the single most stateful relationship in the product. It is where default, replacement, exit and removal live, and putting those columns on `users` would make every profile read a membership query."],
            ["`ajo_positions`", "`users`", "`ajo_members` (via `position_id`)", "The claim, its lock state and the release timestamp. `UNIQUE (ajo_id, position_id) WHERE position_id IS NOT NULL AND released_at IS NULL`", "Occupancy is the relationship. Modelling it as two independent foreign keys would require either a circular reference or a trigger keeping two sources of truth in step, and triggers that keep two copies in step are the ones that eventually fail silently at three in the morning."],
            ["`rounds`", "`users`", "`contributions` (via `schedule_id` and `member_id`)", "`amount_kobo`, `fee_kobo`, `status`, `due_date`, `paid_at`, `superseded_at`, `defaulted_at`", "The obligation is the money. It needs its own lifecycle, its own payments, its own dispute history and its own ledger postings. A bare pair of foreign keys on `rounds` would have nowhere to put any of that."],
            ["`notifications`", "`notification_templates`", "resolved inline by (`event_key`, `channel`)", "The `dedupe_key` on the notification and the `is_money_critical` flag on the template. Not a join table, and deliberately so", "The cardinality is fixed at one template per event and channel, which is a `UNIQUE` constraint on `notification_templates`, not a relationship that needs a table. Over-modelling this one would add a table to every notification insert for no gain."],
            ["`users`", "`documents`", "`documents` (owner plus optional `verification_check_id`)", "`doc_type`, `sha256`, `mime_type`, `byte_size`, `scan_status`, `expires_at`", "A document is already a relationship: it has a type, a hash, a lifecycle and a purpose. Making `documents` the join entity rather than the child of a separate join is the difference between a usable model and two extra tables."],
        ],
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Four of the six many-to-many relationships are the same two tables",
        "text": (
            "`users` and `ajos` are related three separate ways in this product: as organizer, "
            "as member, and as a scoped role holder. These are not three views of one "
            "relationship; they are three different relationships with different rules, and "
            "collapsing them into a single `AjoUsers` table is the standard mistake in this "
            "domain. The organizer is additionally a member, which is a `CHECK`-enforced "
            "invariant rather than a convention, and a member holding a position is a third "
            "fact about the same pair, held on the membership."
        ),
    },

    # =====================================================================
    # 8.7
    # =====================================================================
    {"t": "pagebreak"},
    {"t": "h2", "text": "8.7 Referential integrity rules"},

    {
        "t": "p",
        "text": (
            "The rule for the whole model is one sentence: **a delete may never destroy a "
            "financial record.** Everything below is that sentence made operational. There are "
            "four referential actions in this schema and only four, and three of them are "
            "conservative."
        ),
    },

    {
        "t": "table",
        "head": ["Action", "Where it is used", "Count", "Why"],
        "widths": [0.95, 2.0, 0.5, 3.05],
        "size": 7.6,
        "rows": [
            ["`ON DELETE CASCADE`", "Only between a table and its own satellite with no history: `users`->`profiles`, `users`->`admins`, `users`->`notification_preferences`, `users`->`sessions`, `users`->`device_tokens`, `users`->`role_assignments`, `users`->`notifications`, `users`->`support_tickets`, `users`->`idempotency_keys`, `users`->`documents` where the document is an avatar, `disputes`->`dispute_messages`, `disputes`->`dispute_evidence`, `rounds`->`contribution_schedules`, `ajos`->`invitations`.", "13", "Every one of these is a satellite whose deletion loses no independent history. A member losing their session list or their notification inbox is not an incident. A member losing their receipts is."],
            ["`ON DELETE SET NULL`", "Optional links where the link is metadata, not ownership: `documents.verification_check_id`, `invitations.position_id`, `profiles.avatar_document_id`, `support_tickets.ajo_id`, `webhook_events.payment_id` is not used (it is the other way round), `payouts.dispute_id` is not used (the dispute references the payout).", "4", "The record on the far side of the link stays and keeps its meaning. A document outlives the check it was submitted for, which is correct: the fact that a document existed is the evidence."],
            ["`ON DELETE RESTRICT`", "Everything touching money or history: `ajos`->`rounds`, `rounds`->`contributions`, `contributions`->`payments`, `payments`->`fees`, `rounds`->`payouts`, `contributions`->`disputes`, `users`->`verification_checks`, `users`->`ajo_members`, `users`->`disputes`, `users`->`audit_logs`, plus the entire ledger.", "30+", "This is the default and it is deliberate. `RESTRICT` fails immediately and loudly; a `NO ACTION` deferrable constraint would fail at commit, and a silently soft-deleted parent would leave an orphan that no query in the product is looking for."],
            ["No referential action at all", "`ledger_transactions`, `ledger_postings`, `audit_logs`, `risk_events`, `reconciliation_runs`, `webhook_events`, `roles`, `contribution_frequencies`, `payment_channels`, `platform_settings`.", "10", "These are never deleted by anything. Ledger and audit deletion is blocked by a trigger *and* by a `REVOKE`; configuration tables are deactivated, not removed. Declaring no action is the strongest statement available."],
        ],
    },

    {
        "t": "code",
        "text": """
THE DELETE LADDER, IN ORDER OF PREFERENCE
========================================================================
  1. Do nothing.                          the correct answer, most of the
                                          time. 89 of 101 relationships.

  2. Soft delete.  SET deleted_at =       business state ended, record
     now(), bump version.                 remains readable and auditable.
     Row invisible to ordinary reads
     via a partial index, visible to
     audit, statements and support.

  3. Anonymise.  Null or hash the         person asked to be forgotten;
     personal columns, keep the           the financial row must remain
     financial columns.                   provable. See the LEGAL
                                          callout in 8.9.

  4. Deactivate.  is_active = false.      configuration, not history.

  5. Post a reversing ledger entry.       a money mistake. Never an
                                          UPDATE, never a DELETE.

  6. Hard delete.  Only ever for a        session rows, expired
     satellite with no independent        idempotency keys, notification
     history (see action 1).              history, outbox rows already
                                          published past the retention
                                          window.
========================================================================
 Hard deletion of contributions, payments, payouts, fees,
 ledger_transactions, ledger_postings, audit_logs, risk_events or
 reconciliation_runs is not a supported operation at any privilege
 level, including the table owner. There is no admin endpoint for
 it and there is no stored procedure for it.
========================================================================
""",
    },

    {
        "t": "callout",
        "kind": "WARNING",
        "title": "The one place CASCADE appears in the money domain, and why it is safe",
        "text": (
            "`rounds -> contribution_schedules` is `ON DELETE CASCADE`, and it is the only "
            "cascade in the money domain. It is safe because a `rounds` row can never be "
            "deleted: `ajos -> rounds` is `RESTRICT`, `ajos` deletion is blocked by a trigger "
            "outside the retention window, and the application never issues a `DELETE` "
            "against `rounds` at all. The cascade exists to make the invariant `rounds` has "
            "exactly one schedule expressible, and it is unreachable in practice. If a "
            "reviewer finds a route by which a `rounds` row can be deleted, the cascade turns "
            "that bug into data loss, and the correct fix is to change the cascade to "
            "`RESTRICT` and delete the orphan schedule in application code."
        ),
    },

    # =====================================================================
    # 8.8
    # =====================================================================
    {"t": "h2", "text": "8.8 Cardinality constraints that encode business rules"},

    {
        "t": "p",
        "text": (
            "A business rule that lives in application code is a rule that will be true until "
            "the first time two requests arrive at once. Every rule in the table below is "
            "therefore expressed as a database constraint, and each has a named constraint or "
            "index so that a violation is a legible error message rather than a unique-index "
            "violation on an auto-generated name. The rules are the ones that would be "
            "catastrophic to get wrong, which is why they are here and not merely written in "
            "prose in section 1."
        ),
    },

    {
        "t": "table",
        "head": ["ID", "Business rule", "Enforced as", "Source"],
        "widths": [0.6, 2.3, 2.35, 1.25],
        "size": 7.4,
        "rows": [
            ["CR-01", "Exactly one contribution per (schedule, member). A member owes once per round, not twice because they pressed the button twice.", "`UNIQUE (schedule_id, member_id)` on `contributions`", "Product"],
            ["CR-02", "Exactly one *live* contribution per (schedule, position) slot, so that a replacement member does not produce two obligations on the same slot.", "`CREATE UNIQUE INDEX contributions_one_live_per_slot ON contributions (schedule_id, position_id) WHERE superseded_at IS NULL`", "Replacement flow"],
            ["CR-03", "Positions are unique per Ajo and numbered 1..position_count with no gaps and no duplicates.", "`UNIQUE (ajo_id, position_number)` and `CHECK (position_number BETWEEN 1 AND position_count)`", "CAN §3"],
            ["CR-04", "A position number never changes once the Ajo is ACTIVE. Reordering after activation is not permitted at all.", "`app.assert_positions_locked()` trigger rejecting `UPDATE` of `position_number` when `ajos.status IN ('ACTIVE','ROUND_IN_PROGRESS','COMPLETED')`", "CAN §3"],
            ["CR-05", "A member holds at most one position in an Ajo.", "`UNIQUE (ajo_id, position_id) WHERE position_id IS NOT NULL AND released_at IS NULL` on `ajo_members`", "Product"],
            ["CR-06", "One payout per (round, position). The recipient's turn happens once.", "`UNIQUE (round_id, position_id)` on `payouts`", "CAN §4"],
            ["CR-07", "At most one payout per position may be in flight at any time, so a double-clicked release cannot submit two disbursements.", "`CREATE UNIQUE INDEX payouts_one_live_per_slot ON payouts (round_id, position_id) WHERE status IN ('scheduled','funding','released','held')`", "CAN §4"],
            ["CR-08", "At most one successful payment per contribution. Retries create new rows; they never resurrect a settled one.", "`CREATE UNIQUE INDEX payments_one_success_per_contribution ON payments (contribution_id) WHERE status = 'success'`", "Product"],
            ["CR-09", "One provider reference per payment and one payment per webhook event.", "`UNIQUE (provider, provider_reference)` on `payments`; `UNIQUE (provider, provider_event_id)` on `webhook_events`; `UNIQUE (webhook_event_id)` on `payments`", "CAN §6"],
            ["CR-10", "One round in progress per Ajo. Two rounds funding at once would let two members be paid from the same pool.", "`CREATE UNIQUE INDEX rounds_one_in_progress_per_ajo ON rounds (ajo_id) WHERE status = 'in_progress'`", "CAN §3"],
            ["CR-11", "One live invitation per (Ajo, email address).", "`CREATE UNIQUE INDEX invitations_one_pending_per_ajo_email ON invitations (ajo_id, email) WHERE status = 'pending'`, using `citext`", "Product"],
            ["CR-12", "One fee per settled payment, and the fee is exactly 2% half-up of the base amount.", "`UNIQUE (payment_id)` on `fees`; `CHECK (fee_kobo = ((contribution_amount_kobo * 200) + 5000) / 10000)` on `payments`; deferred trigger `app.assert_fee_matches_payment()`", "CAN §1"],
            ["CR-13", "The amount charged equals the base amount plus the fee, to the kobo. A member owing NGN 1,000.00 is charged NGN 1,020.00 and no other figure.", "`CHECK (charged_amount_kobo = contribution_amount_kobo + fee_kobo)` on `payments`, and the same on `contributions`", "CAN §1"],
            ["CR-14", "A payout equals its base pool. The fee never reduces a payout: the recipient of a ten-member round receives NGN 10,000.00, not NGN 9,800.00 and not NGN 10,200.00.", "`CHECK (amount_kobo = base_pool_kobo)` and `CHECK (fee_kobo = 0)` on `payouts`", "CAN §1"],
            ["CR-15", "A round's base pool is exactly the sum of its paid, non-superseded contributions. No other number may be paid out.", "Deferred trigger `app.assert_round_pool()` comparing `rounds.base_pool_kobo` to the aggregate, run at commit", "CAN §4"],
            ["CR-16", "Every ledger transaction has at least two postings and the signed sum is exactly zero.", "Deferred constraint trigger `app.assert_transaction_balanced()`; `ledger_postings.signed_kobo` is a stored generated column", "CAN §4"],
            ["CR-17", "The four canonical kinds occur in order. `payout.settled` requires an earlier, complete `payout.recognized`.", "Deferred trigger `app.assert_ledger_sequence()` over `ledger_txn_kind` and `occurred_at`", "CAN §4"],
            ["CR-18", "The enrollment window is exactly five days, and an Ajo has between five and twenty members, the creator included.", "`CHECK (enrollment_closes_at <= enrollment_opens_at + interval '5 days')` on `ajos`; `CHECK (position_count BETWEEN 5 AND 20)`; trigger `app.assert_draft_exit()`", "CAN §3"],
            ["CR-19", "A terminal Ajo accepts no events. `COMPLETED` and `CANCELLED` are final.", "`app.assert_lifecycle_transition()` trigger over the transition table in CANONICAL.md section 3, and `CHECK` constraints coupling `completed_at`/`cancelled_at` to `status`", "CAN §3"],
            ["CR-20", "A user cannot dispute themselves, and an Ajo-scoped role grant cannot also be a platform grant.", "`CHECK (raised_by_user_id <> against_user_id)`; `CHECK ((scope='platform') = (ajo_id IS NULL AND ajo_member_id IS NULL))` on `role_assignments`", "Product"],
            ["CR-21", "Only one reversal per original transaction, and reversals are one level deep. A reversal is never itself reversed.", "Partial `UNIQUE (reverses_transaction_id)`; `CHECK ((kind='reversal') = (reverses_transaction_id IS NOT NULL))`; deferred trigger rejecting a reversal whose target is a reversal", "Product"],
            ["CR-22", "No amount is negative anywhere. Kobo are unsigned by construction and every money column carries a non-negative check.", "`CHECK (col >= 0)` on all 43 money columns; ledger postings use `> 0` because a zero-leg posting is meaningless", "Product"],
            ["CR-23", "A money-critical or security-critical event must have an SMS template, per CANONICAL.md section 8.", "Deferred trigger `app.assert_money_critical_has_sms()` over `notification_templates`", "CAN §8"],
            ["CR-24", "A user may hold at most one push token per device, and a revoked token is never reused.", "`UNIQUE (push_token)` on `device_tokens`", "Product"],
        ],
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Why CR-14 is a constraint and not a comment",
        "text": (
            "CANONICAL.md open decision D-01 records the question of whether the recipient "
            "receives the base pool or the full collected pool, with the base pool assumed in "
            "this specification. Assuming a number is not the same as protecting it, and a "
            "single `payouts.amount_kobo = base_pool_kobo * 1.02` in a payout service would "
            "put NGN 10,200.00 into a member's bank account and, in the base case, roughly "
            "NGN 3,000,000 of platform money into members' accounts across the year. That is "
            "not a bug that would be caught before a customer noticed. CR-14 makes the wrong "
            "figure a constraint violation, and CR-15 makes the base pool itself a computed "
            "fact rather than a typed-in number. D-01 is closed for the purposes of this "
            "specification; the founders confirm or amend it, and the amendment is a migration."
        ),
    },

    # =====================================================================
    # 8.9
    # =====================================================================
    {"t": "pagebreak"},
    {"t": "h2", "text": "8.9 Deletion and retention strategy per entity class"},

    {
        "t": "p",
        "text": (
            "Six entity classes, each with one deletion rule and one retention rule. The class "
            "is what matters, because retention is a policy about a kind of data rather than "
            "about a table, and a table that spans two classes (a contribution is a debt "
            "record *and* a personal record) takes the stricter of the two."
        ),
    },

    {
        "t": "table",
        "head": ["Class", "Tables", "Deletion", "Retention", "Rationale"],
        "widths": [0.95, 1.5, 1.25, 1.25, 1.55],
        "size": 7.2,
        "rows": [
            ["Ledger and audit", "`ledger_transactions`, `ledger_postings`, `audit_logs`, `reconciliation_runs`", "Never. Enforced by a trigger that raises on `UPDATE` or `DELETE` plus a `REVOKE` from all client roles. Corrections are reversing entries.", "Indefinite. No deletion at any point in the product's life.", "A savings record that can be edited is not a record. A member disputing a payout in three years' time must be shown the original entry and the reversal, not a row that was quietly corrected. Section 9.5 and 9.11 treat this as a hard requirement, subject to the LEGAL callout below."],
            ["Financial records", "`contributions`, `payments`, `payouts`, `fees`", "Never. Soft delete is not even offered, because there is no business event that means *a payment did not happen*. A mistaken payment is reversed in the ledger.", "Indefinite, at minimum for as long as the Ajo, the member's account and any dispute or legal process relating to them.", "These are the rows a regulator, a tax authority, a court or an auditor will ask for. The Nigerian position on the retention of banking and financial records, and the interaction with the Nigeria Data Protection Act 2023, requires confirmation by qualified Nigerian counsel and the appointed compliance adviser. No period is asserted here."],
            ["Operational records", "`ajos`, `rounds`, `contribution_schedules`, `ajo_positions`, `ajo_members`, `invitations`, `disputes`, `risk_events`", "Soft delete via `deleted_at`, always with an `audit_logs` row. A cancelled Ajo is never deleted; it is `status='cancelled'` with a reason and a `cancelled_at`.", "Retained for the life of the financial record they support, then anonymised. Risk events and disputes are retained independently of the Ajo, because they may be the subject of a separate process.", "A soft-deleted Ajo that still has a contribution is the normal state of every Ajo that fails, and the row is what proves the failure was handled correctly. `disputes` and `risk_events` have no cascade, so they outlive the Ajo by design."],
            ["Personal data", "`users`, `profiles`, `sessions`, `device_tokens`, `notifications`, `notification_preferences`, `support_tickets`, `documents`", "Account closure is an anonymisation, not a delete: personal columns are nulled or keyed-hashed, financial foreign keys are retained. The user row survives with `status='closed'`.", "Erasure on request where law permits, subject to the AML retention override below. Notifications and expired sessions are the only personal data with a short, hard TTL.", "The tension between a data subject's right to erasure and an anti-money-laundering obligation to retain records is real, is jurisdiction-specific, and is a question for counsel. The schema is built so that either answer can be implemented without a migration: personal columns are separable from financial ones, which is the whole reason `profiles` is a separate table."],
            ["Verification and documents", "`verification_checks`, `documents`", "Soft delete only. A verification failure is evidence of a decision and is never removed.", "Identity documents and biometrics are special-category data under the Nigeria Data Protection Act 2023 and carry a shorter default retention than the financial records they relate to. The period must be set by counsel.", "An identity document that has served its purpose should not sit in a storage bucket forever. Object-storage lifecycle rules and the database row's `expires_at` are the two halves of one policy, and both must be changed together."],
            ["Ephemeral and configuration", "`idempotency_keys`, `webhook_events`, `outbox_events`, `platform_settings`, `roles`, `role_assignments`, `contribution_frequencies`, `payment_channels`, `notification_templates`", "Hard delete permitted. TTL on idempotency keys (24 hours for money, 7 days otherwise), 90 days on published outbox rows, 180 days on `webhook_events` payloads once processed.", "Configuration retained indefinitely with a version history. Ephemeral data is deleted on a schedule, not on request.", "These carry no information that is not either in the ledger or reproducible. `webhook_events` is the exception worth naming: the raw payload is the proof that a provider told us something, so it is kept long enough to settle any dispute about that call, and the signature verification result is what makes it worth keeping."],
        ],
    },

    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Retention periods are not set in this document",
        "text": (
            "The table above gives a *shape* of retention policy and deliberately gives no "
            "numbers, because every number in it is a legal or regulatory position rather than "
            "an engineering one. Specifically: the retention period for KYC and transaction "
            "records under Nigerian anti-money-laundering and anti-terrorist-financing "
            "obligations; whether that period overrides a data subject's erasure request under "
            "the Nigeria Data Protection Act 2023; the treatment of biometric-adjacent data "
            "captured for liveness verification; cross-border transfer of identity data to a "
            "verification or payment provider; and the record-keeping obligations that attach "
            "to complaints and disputes. Each of these requires confirmation by qualified "
            "Nigerian legal counsel, the appointed compliance adviser, and the payment partner "
            "before launch. The schema is built to accommodate whatever those answers turn out "
            "to be, which is why personal data and financial data are separable and why "
            "`documents` has an `expires_at` independent of the Ajo."
        ),
    },

    {
        "t": "callout",
        "kind": "WARNING",
        "title": "A backup is not a retention policy",
        "text": (
            "Erasure from the primary database does not erase a member's identity document "
            "from last night's base backup, from a replica, or from an object-storage version. "
            "Any genuine erasure programme must include the retention and expiry schedule for "
            "backups themselves, and that schedule is itself subject to the same legal "
            "confirmation as the primary policy. Section 12 in the companion schema section "
            "covers point-in-time recovery and states the same caveat again, because this is "
            "the assumption that quietly fails in most data-protection programmes."
        ),
    },

    # =====================================================================
    # 8.10
    # =====================================================================
    {"t": "h2", "text": "8.10 Entity-to-API traceability"},

    {
        "t": "p",
        "text": (
            "Every endpoint in CANONICAL.md section 6 and every table in this section, mapped "
            "to each other. The purpose is bidirectional and the test is symmetric: an entity "
            "with no endpoint is dead weight, and an endpoint with no entity cannot be "
            "implemented. Four tables have no public endpoint by design and are listed as such "
            "at the foot of the table, because an internal table is a legitimate answer and an "
            "unexplained one is not."
        ),
    },

    {
        "t": "table",
        "head": ["Entity", "Endpoint group", "Endpoints (CAN §6)", "Notes"],
        "widths": [1.3, 0.85, 2.6, 1.75],
        "size": 7.0,
        "rows": [
            ["`users`", "Auth, Profile, Admin", "`POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/verify-email`, `/auth/otp/*`, `/auth/password/*`, `GET/PATCH /profile`, `GET /admin/users`, `POST /admin/users/:id/freeze`", "The auth endpoints write `users` and `sessions` in one transaction. The `admin/users/:id/freeze` endpoint sets `status='frozen'` and writes a `risk_events` row."],
            ["`profiles`", "Profile", "`GET/PATCH /profile`, `POST /profile/avatar`, `GET /profile/financial-summary`", "`financial-summary` is a read across `contributions`, `payouts` and the ledger; it is the one place where the product shows a member a number they did not ask for."],
            ["`sessions`, `device_tokens`", "Auth", "`GET /auth/sessions`, `DELETE /auth/sessions/:id`", "`DELETE` is a revocation (`revoked_at`), not a row delete, so that a stolen session's use is still visible in `audit_logs`."],
            ["`verification_checks`", "Verification", "`POST /verification/identity`, `GET /verification/:id`, `POST /verification/bvn`", "Each call creates a new check row. A rejection writes a new check, never an update of the previous one."],
            ["`documents`", "Verification, Disputes, Profile", "`POST /verification/identity`, `POST /disputes/:id/evidence`, `POST /profile/avatar`", "The avatar upload writes a `documents` row with `doc_type='avatar'` and returns a signed URL."],
            ["`admins`, `roles`, `role_assignments`", "Admin", "`GET /admin/overview`, `GET /admin/users`, `GET /admin/audit-logs`, `GET /admin/reports/*`", "There is deliberately no public endpoint that grants a role. Grants are made by the database owner role or by a signed administrative action in `audit_logs`, because a self-service role-grant endpoint is a privilege-escalation endpoint."],
            ["`platform_settings`", "Admin", "`GET /admin/reports/*` (settings view)", "Read-only over HTTP in v1. Changing the fee rate is a migration, not an API call, per 8.8 CR-12."],
            ["`ajos`", "Ajos", "`POST /ajos`, `GET /ajos`, `GET /ajos/:id`, `PATCH /ajos/:id`, `POST /ajos/:id/activate`, `/cancel`, `/freeze`, `/unfreeze`, `GET /ajos/:id/summary`", "The six state-changing endpoints are the only places `ajos.status` changes, and each one writes an `audit_logs` row with the before and after images."],
            ["`ajo_positions`", "Positions", "`GET /ajos/:id/positions`, `POST /ajos/:id/positions/claim`, `POST /ajos/:id/positions/reorder`, `POST /ajos/:id/positions/lock`", "`reorder` is authorized only while `status = 'DRAFT'`; after activation the endpoint returns 409 and CR-04 would reject the write regardless."],
            ["`ajo_members`", "Members", "`GET /ajos/:id/members`, `POST /ajos/:id/members`, `DELETE /ajos/:id/members/:memberId`, `PATCH /ajos/:id/members/:memberId`, `POST /ajos/:id/members/:memberId/replace`", "`DELETE` is a removal with a reason, not a row delete. `replace` is the endpoint behind CR-02's `superseded_at`."],
            ["`invitations`", "Invitations", "`POST /invitations`, `GET /invitations`, `GET /invitations/:token`, `POST /invitations/:token/accept`, `/decline`, `POST /invitations/resend`", "Accepting writes `ajo_members` in the same transaction that flips the invitation, satisfying the `UNIQUE (invitation_id)` rule."],
            ["`rounds`, `contribution_schedules`", "Contributions, Ajos", "`GET /ajos/:id/schedule`, `GET /contributions`, `GET /contributions/:id`", "There is no `POST` for either. Rounds and schedules are created by the system when a round opens, never by a client, which is why both tables have no writable API surface."],
            ["`contributions`", "Contributions", "`GET /contributions`, `GET /contributions/:id`, `GET /ajos/:id/contributions`, `POST /contributions/:id/pay`, `POST /contributions/:id/retry`", "`pay` creates a `payments` row and returns a provider authorisation URL. It never writes the ledger; the ledger is written when the payment succeeds."],
            ["`payments`", "Payments", "`POST /payments`, `POST /payments/:id/verify`, `GET /payments/:id`, `GET /payments/:id/receipt`", "`receipt` is the fee-disclosure surface required by CANONICAL.md section 1: base, fee and total as three separate lines, never one."],
            ["`fees`", "Payments, Admin", "`GET /payments/:id/receipt`, `GET /admin/reports/*`", "No write endpoint. Fees are created by the trigger on payment settlement, and any correction is a refund row."],
            ["`payouts`", "Payouts", "`GET /payouts`, `GET /payouts/:id`, `GET /ajos/:id/payouts`, `POST /payouts/:id/release`", "`release` is the organizer *request*; the actual disbursement runs the four-step sequence and is what `payouts.status` transitions to."],
            ["`ledger_transactions`, `ledger_postings`", "Transactions", "`GET /transactions`, `GET /transactions/:id`, `GET /statements`", "Read-only over HTTP, and there is no endpoint that can write either table. Section 9.6 grants no insert policy to any client role."],
            ["`idempotency_keys`", "All money-moving POSTs", "`POST /contributions/:id/pay`, `POST /contributions/:id/retry`, `POST /payouts/:id/release`, `POST /payments`", "The `Idempotency-Key` header is required on all four, per CANONICAL.md section 6 conventions."],
            ["`webhook_events`", "Webhooks", "`POST /webhooks/payments`", "The only unauthenticated endpoint. The row is written before any processing, and the unique constraint on (`provider`, `provider_event_id`) is the deduplication."],
            ["`reconciliation_runs`", "Admin", "`GET /admin/reports/*`", "Triggered by a scheduler, not by a request. A failed run pages the risk officer and blocks new disbursements."],
            ["`notifications`, `notification_preferences`", "Notifications", "`GET /notifications`, `POST /notifications/:id/read`, `POST /notifications/read-all`, `GET/PUT /notification-preferences`", "`PUT /notification-preferences` is the only way a member changes what they are told about their money."],
            ["`notification_templates`", "Admin", "`GET /admin/reports/*` (catalogue view)", "Read-only over HTTP. Copy changes go through review and a migration, because the money-critical channel rule is a constraint on this table."],
            ["`disputes`, `dispute_messages`, `dispute_evidence`", "Disputes", "`POST /disputes`, `GET /disputes`, `GET /disputes/:id`, `POST /disputes/:id/evidence`, `POST /disputes/:id/messages`", "`support` may read and may post messages; neither `support` nor any member can write `status` or `resolution`."],
            ["`risk_events`", "Admin", "`GET /admin/risk`, `POST /admin/risk/:id/decision`", "`POST /admin/risk/:id/decision` is authorized on `risk_officer` only, and `super_admin` can take the emergency freeze but cannot reverse a risk decision once made."],
            ["`audit_logs`", "Admin", "`GET /admin/audit-logs`", "Read-only, cursor-paginated, and the only table with a `GET` that is not scoped to the calling user's own records. `super_admin` cannot delete from it, because there is no endpoint that deletes from it."],
            ["`support_tickets`", "Admin, Support", "`GET /admin/overview` (support queue), `GET /admin/reports/*`", "No member-facing endpoint in v1. The Support screen in CAN §7 is served by an authenticated support console, not the member app."],
        ],
    },

    {
        "t": "p",
        "text": (
            "Four tables have no public endpoint and this is deliberate. `outbox_events` is "
            "written by triggers and read by a publisher process. `contribution_frequencies`, "
            "`payment_channels` and `platform_settings` are configuration, administered by "
            "migration and reviewed as code. Their absence from the API surface is a feature: "
            "a client that could change the contribution frequency or the payment channel at "
            "runtime is a client that can be induced to."
        ),
    },

    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Closing the loop with section 9",
        "text": (
            "Every table named in this section has a `CREATE TABLE` statement in section 9.3, "
            "every rule in 8.8 has a named constraint or index in 9.3 and 9.5, and every "
            "cascade decision in 8.7 has a matching `ON DELETE` clause in the DDL. The two "
            "sections are intended to be read side by side, and a change to either is a change "
            "to both. The traceability chain closes: CANONICAL.md section 5 names the "
            "entities, this section structures them, section 9 implements them, CANONICAL.md "
            "section 6 exposes them, and CANONICAL.md section 7 renders them. Nothing in the "
            "data model exists that no user ever sees and no operator ever needs. The tagline "
            "is *Your Ajo. Your Story.*"
        ),
    },

]
