"""Section 14 — Security, Privacy and Compliance."""

BLOCKS = [
    {"t": "h1", "text": "14. Security, Privacy and Compliance"},

    {"t": "lead", "text": "AJO.ng handles Nigerian citizens' identity documents, bank "
     "details, and their savings. That combination makes it a target of both ordinary "
     "fraudsters and sophisticated criminals, and it places a real obligation on the "
     "platform to protect the data properly. This section states the controls. Whether "
     "those controls satisfy Nigerian law requires confirmation by qualified legal and "
     "compliance professionals before production launch."},

    {"t": "h2", "text": "14.1 Threat model"},
    {"t": "p", "text": "A threat model is only useful if it names the people who are "
     "trying to do what. The following are the realistic adversaries for a savings "
     "platform operating in Nigeria."},
    {"t": "table", "head": ["Adversary", "Capability", "Primary goal", "Defence in depth"], "widths": [1.5, 1.8, 1.6, 1.6], "size": 7.8, "rows": [
        ["Opportunistic fraudster", "Social engineering, fake support", "Convince a member to move money", "Never release money to a changed destination without cooling-off and multi-channel notification"],
        ["Account-takeover attacker", "Credential stuffing, SIM swap, malware", "Redirect the next payout", "Refresh rotation, device alerts, step-up auth, payout cooling-off"],
        ["Insider threat", "Legitimate database or console access", "Extract PII or divert funds", "Least privilege, segregation of duties, immutable ledger, four-eyes on bank details"],
        ["Payment fraudster", "Test cards, fake screenshots, first-party chargeback abuse", "Free contributions or reverse a payout", "Webhook-only confirmation, 3-D Secure, velocity limits, behaviour checks"],
        ["Organizer acting in bad faith", "Real access, real authority over their Ajo", "Mislead members, exclude people, extort", "Scoped permissions, no custody, no unilateral removal, audit, member complaints"],
        ["External attacker", "Vulnerability scanning, dependency exploits, credential stuffing", "Access, exfiltrate, deface", "Hardening, patching cadence, WAF, secret management, monitoring"],
        ["Third-party breach", "Compromise of a provider or vendor", "Cascade into AJO.ng's data", "Data minimisation, per-vendor scoping, encryption, vendor review"],
    ]},
    {"t": "p", "text": "AJO.ng's own staff are treated as a threat, not as a control. "
     "The permission matrix in section 12 deliberately contains no role that can edit or "
     "delete a ledger entry, and no role that can see both a member's identity documents "
     "and their bank details together."},

    {"t": "h2", "text": "14.2 Encryption and key management"},
    {"t": "table", "head": ["Layer", "Control"], "widths": [1.9, 4.6], "size": 8.4, "rows": [
        ["In transit", "TLS 1.3 preferred, TLS 1.2 minimum. HSTS on all web surfaces. Certificate pinning on the mobile app"],
        ["At rest — database", "AES-256 managed by the hosting provider, with per-environment keys"],
        ["At rest — sensitive columns", "Application-level envelope encryption for BVN, phone number, and bank account details"],
        ["At rest — secrets", "Managed secret store (e.g. a cloud KMS or secrets manager). No secrets in source, in images, or in environment files under version control"],
        ["Key rotation", "Data keys rotated at least annually and on any suspected exposure. Rotation is re-wrapped, not re-encrypted from scratch, so downtime is not required"],
        ["Separation of duties for keys", "No single engineer can decrypt production data. Break-glass access is logged, time-boxed, and reviewed"],
        ["Backups", "Encrypted with a key held separately from the backup itself, so a storage compromise does not expose the backups"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Why BVN deserves special handling.",
     "text": "A BVN is a national identity number, not a convenience field. It should be "
     "collected only where a legal or provider requirement genuinely demands it, stored "
     "encrypted, never logged in plaintext, never exposed in an API response, and "
     "displayed masked outside the verification flow. If a feature does not need BVN, it "
     "does not get it."},

    {"t": "h2", "text": "14.3 Application hardening"},
    {"t": "bullets", "items": [
        "**Input validation at the boundary** — every request validated against a schema before it reaches business logic. Types, ranges, formats, and lengths are all enforced, not merely checked.",
        "**Parameterised queries only** — no string-concatenated SQL anywhere in the codebase, including in migrations and admin tooling.",
        "**Output encoding** — context-aware encoding on every rendered surface, so member-supplied text cannot become script.",
        "**CSRF protection** on all cookie-authenticated state-changing routes. Bearer-token routes are not CSRF-vulnerable, but the cookie must not be used where a token is expected.",
        "**Content Security Policy** with no `unsafe-inline` in production, plus `frame-ancestors 'none'` to prevent clickjacking on the payment screens.",
        "**Rate limiting** per IP, per account, per device and per endpoint, with tighter limits on login, OTP, and payout operations than on ordinary reads.",
        "**File upload scanning** where a member may upload evidence in a dispute — size and type limits, content-type verification, and malware scanning before storage.",
        "**Dependency hygiene** — automated scanning for known vulnerabilities, with a defined SLA for remediation by severity.",
        "**Security headers** — a strict set including `X-Content-Type-Options`, `Referrer-Policy`, and `Permissions-Policy`.",
    ]},

    {"t": "h2", "text": "14.4 Row Level Security"},
    {"t": "p", "text": "PostgreSQL Row Level Security is the second authorization layer. It "
     "means that even a compromised application component using a valid connection cannot "
     "read across members."},
    {"t": "code", "size": 7.6, "text": """
  ALTER TABLE contributions ENABLE ROW LEVEL SECURITY;
  ALTER TABLE contributions FORCE ROW LEVEL SECURITY;   -- applies to the table owner too

  CREATE POLICY contributions_member_scope ON contributions
    FOR SELECT
    USING (
      member_id = current_setting('app.current_member_id', true)::uuid
      OR EXISTS (
        SELECT 1 FROM ajos a
        WHERE a.id = contributions.ajo_id
          AND a.organizer_id = current_setting('app.current_member_id', true)::uuid
      )
      OR current_setting('app.is_staff', true) = 'true'
    );
"""},
    {"t": "p", "text": "`FORCE ROW LEVEL SECURITY` matters. Without it, a table owner "
     "silently bypasses every policy, which would quietly undo the whole design. The "
     "requesting identity is set per-transaction at the start of the request and cleared "
     "at the end, so a pooled connection can never inherit a previous member's context."},
    {"t": "callout", "kind": "WARNING", "title": "RLS is not a substitute for application checks.",
     "text": "Both layers are required. RLS is a backstop against a bug in a query; the "
     "application layer is where business rules such as 'an organizer may see only their "
     "own Ajo' actually belong. A product that relies on RLS alone will eventually ship a "
     "service-role connection that quietly reads everything."},

    {"t": "h2", "text": "14.5 Data classification and minimisation"},
    {"t": "table", "head": ["Class", "Examples", "Handling"], "widths": [1.2, 2.2, 3.1], "size": 8.2, "rows": [
        ["Public", "Ajo name, contribution schedule, member first name + avatar", "May be shown to members of that Ajo"],
        ["Internal", "Contribution status, round history, notification records", "Members see their own; staff see as needed"],
        ["Confidential", "Full name, phone number, email, transaction history", "Encrypted at rest; access logged; never shared with other members"],
        ["Restricted", "BVN, NIN, bank account numbers, document images, device fingerprints", "Envelope-encrypted; access requires a named business reason and is logged; masked in all UI and APIs by default"],
    ]},
    {"t": "p", "text": "**Data minimisation is a design constraint, not a later cleanup.** If "
     "a field is not required by a confirmed regulatory or provider requirement, it is not "
     "collected. Every new data point in a financial product creates a permanent "
     "obligation to protect, retain, and eventually delete it."},

    {"t": "h2", "text": "14.6 PII handling rules"},
    {"t": "bullets", "items": [
        "**Log redaction** — no plaintext BVN, bank account number, national ID, or full phone number ever reaches a log. Structured logs carry an ID, and the ID resolves to a value only in a controlled path.",
        "**No PII in URLs or query strings** — they end up in browser history, proxy logs, and analytics. Identifiers go in the path or the body.",
        "**No PII in error messages** shown to members, and no stack trace ever reaches a client.",
        "**No PII in third-party analytics** — events carry opaque IDs, never names, numbers, or emails.",
        "**Masking in the UI** — bank account shown as `•••• •••• 1234`, BVN as `•••••••01`, phone as `080•••••123` outside the verification flow.",
        "**Screenshots and screen recording** — disabled on payment and identity screens in the app where the platform can control it; and treated as a member-education point where it cannot.",
    ]},

    {"t": "h2", "text": "14.7 Consent, cookies and tracking"},
    {"t": "p", "text": "AJO.ng is a savings app, not a tracking business. The default is "
     "no tracking, and every exception is justified."},
    {"t": "table", "head": ["Purpose", "Legal basis", "Mechanism"], "widths": [1.9, 1.7, 2.9], "size": 8.4, "rows": [
        ["Essential operation — sessions, security, payment processing", "Contract necessity", "Strictly necessary cookies only. Cannot be switched off, and the app still works"],
        ["Security and fraud prevention", "Legitimate interests", "Device fingerprint, IP, behavioural signals. Retained short-term, disclosed in the privacy notice"],
        ["Product analytics", "Consent, or legitimate interests where genuinely essential", "Pseudonymous identifiers only. No cross-site advertising trackers"],
        ["Marketing", "Consent, opt-in only", "Never loaded before consent. Withdrawable at any time"],
        ["Personalised notifications", "Consent per channel", "Push and email preferences, per category, per channel"],
    ]},
    {"t": "p", "text": "A consent banner that buries the reject button, or that treats "
     "refusing analytics as a wall, is a dark pattern. Reject must be as easy to use as "
     "accept, and refusing must not break the app."},

    {"t": "h2", "text": "14.8 Data retention and deletion"},
    {"t": "p", "text": "Retention periods for financial and identity records are governed "
     "by Nigerian law and by the requirements of the payment provider and banking "
     "partners. **The specific durations in this table must be confirmed by counsel "
     "before launch**; they are presented as the structure to be agreed, not as settled "
     "obligations."},
    {"t": "table", "head": ["Record", "Proposed retention", "On expiry"], "widths": [2.0, 1.5, 3.0], "size": 8.4, "rows": [
        ["Member account profile", "Life of account + 3 years", "Anonymise; retain nothing linkable"],
        ["Identity documents (BVN, NIN, ID images)", "Life of account + statutory period", "Crypto-shred: destroy the data key so the ciphertext is unrecoverable"],
        ["Transaction and ledger records", "Statutory period (7–10 years to be confirmed)", "Retain per statute. **Never** deleted simply because a member closes their account"],
        ["Payment provider references and settlement reports", "Statutory period", "Retained per statute"],
        ["Audit logs", "Statutory period", "Retained per statute"],
        ["Security and fraud logs", "12 months minimum", "Delete or anonymise"],
        ["Notification delivery records", "24 months", "Delete"],
        ["Support conversations", "24 months", "Delete or anonymise, except content referenced in a dispute"],
        ["Analytics events", "14 months", "Delete or aggregate irreversibly"],
        ["Application and infrastructure logs", "30–90 days", "Delete"],
        ["Backups", "Rolling 35 days", "Expire naturally; no selective deletion from backups"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Account closure is not deletion.",
     "text": "A member closing their account ends their access, not the platform's record "
     "of what happened. Financial and identity records survive per statute. Being honest "
     "about this — in the UI, at the point of closure — is both the right thing and the "
     "legal one, and it prevents a class of complaint and dispute that would otherwise be "
     "expensive to resolve."},

    {"t": "h2", "text": "14.9 Member rights"},
    {"t": "p", "text": "The following rights are described in plain language in the app, "
     "in both English and the languages the team can genuinely support, and are honoured "
     "through a single request path."},
    {"t": "table", "head": ["Right", "How it is honoured", "Target"], "widths": [1.9, 3.4, 1.2], "size": 8.4, "rows": [
        ["Access", "A member can request a copy of their personal data. Delivered in a machine-readable format within 30 days", "30 days"],
        ["Correction", "Self-service for profile fields; a request for identity-document correction, with a verification check so nobody else's document is changed", "30 days"],
        ["Withdrawal of consent", "Self-service, per purpose. Withdrawal stops the processing and does not affect processing already lawfully carried out", "Immediate"],
        ["Account closure", "Self-service, blocked only where an unsettled financial obligation exists, and the blockage is explained precisely", "Immediate once clear"],
        ["Complaint escalation", "Published internal path, then an external escalation route. Every complaint receives a reference number and a response", "Acknowledged in 2 business days"],
    ]},
    {"t": "p", "text": "Where a request is refused, the reason is given in writing. "
     "Transferring a data subject to another controller — a prospective investor or "
     "acquirer — is a separate disclosure that needs its own lawful basis and its own "
     "notice, and must not happen as a side effect of a data export request."},

    {"t": "h2", "text": "14.10 Cross-border data"},
    {"t": "p", "text": "AJO.ng is Nigerian. Members are Nigerian. The default assumption "
     "is that personal data stays in Nigeria, and any transfer of member data outside the "
     "country is an exception that requires both a legal basis under Nigerian data "
     "protection law and a documented decision — including which jurisdiction's law the "
     "processing is subject to. Support, analytics, email, and push infrastructure are all "
     "candidates for cross-border processing, and each must be assessed on its own merits."},

    {"t": "h2", "text": "14.11 Security testing"},
    {"t": "table", "head": ["Activity", "Frequency", "Owner", "Gate"], "widths": [1.9, 1.2, 1.5, 1.9], "size": 8.4, "rows": [
        ["Unit and integration tests (including the adversarial ledger suite)", "Every commit", "Engineering", "Blocks merge"],
        ["Static analysis and secret scanning", "Every commit", "CI", "Blocks merge"],
        ["Dependency vulnerability review", "Weekly", "Engineering", "High/critical must be resolved or risk-accepted in writing"],
        ["Authorised penetration test", "Before launch, then at least annually", "External specialist", "Blocks launch; all critical and high findings must be fixed"],
        ["Access review of all staff permissions", "Quarterly, and on any personnel change", "Security + super admin", "Removes stale access"],
        ["Disaster recovery rehearsal", "Every six months", "Engineering + ops", "Documented recovery time"],
        ["Incident response tabletop", "Every six months", "Whole team", "Documented action list"],
    ]},
    {"t": "p", "text": "The penetration test must be performed by a firm independent of "
     "the implementation team, must be scoped to cover authentication, authorisation, "
     "payout initiation, and webhook handling, and must be permitted to test the "
     "production-adjacent environment."},

    {"t": "h2", "text": "14.12 Secrets and access management"},
    {"t": "bullets", "items": [
        "Every secret lives in a managed secret store. Nothing sensitive in source control, container images, CI logs, or chat.",
        "Production access is just-in-time, time-boxed, and logged. Standing production access for engineers is not granted.",
        "Multi-factor authentication is mandatory for every staff account with any production access, and required for admin roles generally.",
        "Access is granted on a need-to-know basis, reviewed quarterly, and revoked the same day a person leaves or changes role.",
        "Every production action by a staff member is attributable to an individual. Shared accounts are prohibited for anything money-related, and a shared break-glass account has its every use reviewed.",
    ]},

    {"t": "h2", "text": "14.13 Monitoring and detection"},
    {"t": "table", "head": ["Signal", "Alert", "Severity", "Response"], "widths": [1.9, 1.7, 1.0, 1.9], "size": 8.2, "rows": [
        ["Ledger invariant broken", "Ledger sum ≠ sum of balances ≠ escrow", "P1", "Halt new payouts immediately. Page finance and engineering"],
        ["Unauthorised access attempt on financial data", "Any RLS or authorisation denial spike", "P1", "Investigate within the hour. Consider credential rotation"],
        ["Bulk PII export", "Any export above a normal volume", "P1", "Block pending investigation"],
        ["Webhook signature failures", "Sustained rise", "P2", "Check for a key rotation mismatch or an attack"],
        ["Provider balance divergence", "Settlement report ≠ ledger", "P1", "Halt payouts; reconcile before proceeding"],
        ["Payout destination changed then paid", "Within the cooling-off window", "P1", "Block the payout; manual verification required"],
        ["Unusual login pattern", "Impossible travel, new device plus new bank", "P2", "Step-up auth; notify member"],
        ["Error rate or latency breach", "SLO burn exceeded", "P2", "Standard incident process"],
    ]},

    {"t": "h2", "text": "14.14 Incident response"},
    {"t": "h3", "text": "14.14.1 Severity levels"},
    {"t": "table", "head": ["Level", "Definition", "Example"], "widths": [0.8, 2.4, 3.3], "size": 8.4, "rows": [
        ["P1", "Members affected, money at risk, or the books do not balance", "Payout rail down; suspected data breach; ledger invariant broken"],
        ["P2", "Significant degradation, no confirmed money loss", "Contribution success rate below target; webhook delays"],
        ["P3", "Limited impact, workaround available", "Single notification template failing"],
        ["P4", "Minor, cosmetic", "Copy error"],
    ]},
    {"t": "h3", "text": "14.14.2 Response process"},
    {"t": "numbers", "items": [
        "**Detect** — automated alerting, member report, or internal observation.",
        "**Triage** — the on-call engineer classifies the severity within 15 minutes for a P1 and starts the incident channel. No single person investigates a P1 alone.",
        "**Contain** — stop the bleeding first: halt payouts, disable a rail, revoke credentials, or block an endpoint. Root-cause analysis waits until the money is safe.",
        " **Communicate** — members are told what is affected, what is not, and what happens next. Security or privacy incidents are escalated to the data protection officer immediately, and any regulatory notification is made within whatever deadline law requires.",
        "**Recover** — restore service, verify the ledger invariant, and confirm reconciliation before declaring the incident closed.",
        "**Learn** — a blameless post-mortem within five business days, with owned and dated actions. A post-mortem without owned actions is not a post-mortem.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Communication is part of containment.",
     "text": "In a savings product, a well-handled outage that is communicated honestly "
     "produces loyal members. A well-handled outage that is hidden produces a public "
     "thread, and a public thread ends the business. Pre-agreed templates for the three "
     "most likely scenarios — payout delay, contribution verification delay, and a "
     "suspected security incident — should be written and approved before launch, so "
     "that nobody is drafting under pressure."},

    {"t": "h2", "text": "14.15 Security and privacy controls — summary checklist"},
    {"t": "table", "head": ["Control", "Status at MVP", "Note"], "widths": [2.3, 1.2, 3.0], "size": 8.4, "rows": [
        ["TLS everywhere, HSTS, certificate pinning", "Required", "Blocking for launch"],
        ["Envelope encryption of restricted columns", "Required", "Blocking for launch"],
        ["Managed secret store, no secrets in source", "Required", "Blocking for launch"],
        ["RLS enabled and forced on all financial tables", "Required", "Blocking for launch"],
        ["Log redaction of all PII", "Required", "Blocking for launch"],
        ["Refresh token rotation with reuse detection", "Required", "Blocking for launch"],
        ["Step-up auth on bank change and payout release", "Required", "Blocking for launch"],
        ["MFA for all staff with production access", "Required", "Blocking for launch"],
        ["Cooling-off on payout destination change", "Required", "Blocking for launch"],
        ["Independent penetration test", "Required", "Blocking for launch"],
        ["Documented breach response and notification path", "Required", "Blocking for launch"],
        ["Public privacy notice and cookie notice", "Required", "Blocking for launch"],
        ["Data subject request process", "Required", "Blocking for launch"],
        ["Data Processing Agreement with every processor", "Required", "Legal sign-off"],
        ["Formal retention schedule approved by counsel", "Required", "Legal sign-off"],
        ["Privacy policy and terms drafted by counsel", "Required", "Legal sign-off"],
        ["Security awareness training for staff", "Required", "Before launch"],
        ["Insurance (cyber, professional indemnity)", "Required", "Business decision"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "Legal review is a launch gate.",
     "text": "Nothing in this document constitutes legal advice, and no item here should "
     "be treated as a compliance determination. Before any real money moves, AJO.ng must "
     "obtain advice from **qualified Nigerian legal and compliance professionals** on "
     "licensing and registration obligations, the treatment of member funds under the "
     "chosen payment arrangement, data protection compliance, consumer protection "
     "requirements, and the terms of the payment provider contract."},
]
