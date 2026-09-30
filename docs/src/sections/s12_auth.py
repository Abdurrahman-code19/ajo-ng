"""Section 12 — Authentication and Authorization."""

BLOCKS = [
    {"t": "h1", "text": "12. Authentication and Authorization"},

    {"t": "lead", "text": "Authentication establishes who a member is. Authorization "
     "decides what they may do — and, critically, what they may not do to money that is "
     "not theirs. In AJO.ng the second question matters more than the first."},

    {"t": "h2", "text": "12.1 Principles"},
    {"t": "numbers", "items": [
        "**Deny by default.** No endpoint is public unless explicitly listed. No role is implied by context.",
        "**Two independent layers.** Application authorization plus PostgreSQL Row Level Security. A leaked API key must not be sufficient to read another member's records.",
        "**Least privilege, and time-bounded.** Permissions are granted narrowly and revoked automatically (sessions, freezes, role changes).",
        "**Step-up for money.** Disbursing, changing bank details, and resolving disputes require a fresh authentication, not a long-lived session.",
        "**Authorization is checked server-side on every request.** Hiding a button in the UI is a design decision, never a security control.",
        "**Financial records are immutable for every role, including super admin.** Corrections happen by reversing entry, never by update.",
    ]},

    {"t": "h2", "text": "12.2 Account lifecycle"},
    {"t": "code", "size": 8.0, "text": """
  registered ──email verified──▶ PENDING_VERIFICATION
        │                                  │
        │                            KYC submitted
        ▼                                  ▼
     PENDING ──KYC approved──▶ ACTIVE ──▶ ACTIVE
                                    │  │
                                    │  └── default recorded ──▶ RESTRICTED
                                    │
                                    └── risk decision ──▶ FROZEN (money-out blocked)
                                    └── member request / breach ──▶ SUSPENDED
                                    └── long inactivity ──▶ DORMANT ──▶ CLOSED (data retained)
"""},
    {"t": "table", "head": ["State", "May contribute", "May receive payout", "May join/create Ajo", "May withdraw"], "widths": [1.2, 1.1, 1.3, 1.4, 1.1], "size": 8.4, "rows": [
        ["PENDING_VERIFICATION", "No", "n/a", "No", "No"],
        ["ACTIVE", "Yes", "Yes", "Yes", "Yes"],
        ["RESTRICTED (in default)", "Yes, to cure the default", "Yes", "No new Ajos", "Limited — subject to freeze"],
        ["FROZEN (risk)", "No", "Yes — always", "No", "No"],
        ["SUSPENDED (breach)", "No", "Yes — after review", "No", "No"],
        ["DORMANT", "No", "Yes — always", "No", "No"],
        ["CLOSED", "No", "Settled obligations only", "No", "No"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The rule that protects members:",
     "text": "No state ever prevents a member from **receiving** money already owed to "
     "them. A frozen, suspended or dormant member is always able to be paid out. A "
     "platform that can trap a member's own funds by freezing them has created a "
     "custody problem it does not have a licence to handle."},

    {"t": "h2", "text": "12.3 Registration"},
    {"t": "numbers", "items": [
        "Member submits email, password, full name, Nigerian phone number.",
        "Server normalises the phone to E.164 (+234…) and checks for an existing account with that phone or email.",
        "Password is hashed with **Argon2id** (see 14.1) before storage; the plaintext never touches a log.",
        "A `users` row is created `PENDING_VERIFICATION`. No Ajo may be created or joined in this state.",
        "A verification token is generated, stored hashed, and emailed. 24-hour expiry, single use.",
        "`acceptedTerms` and `acceptedPrivacy` must be explicitly true. Both the boolean and a timestamp are written to `audit_logs` as consent evidence, together with the document version.",
        "An optional referral or invitation code may be attached, allowing registration to be pre-filled from an invitation link.",
    ]},

    {"t": "h2", "text": "12.4 Login and session management"},
    {"t": "h3", "text": "12.4.1 Token architecture"},
    {"t": "table", "head": ["Token", "Format", "Lifetime", "Storage", "Renewal"], "widths": [1.2, 1.3, 0.9, 1.7, 1.4], "size": 8.4, "rows": [
        ["Access token", "JWT (EdDSA/Ed25519)", "15 min", "Memory only, never localStorage", "Refresh call"],
        ["Refresh token", "Opaque random 256-bit", "30 days", "httpOnly, Secure, SameSite=Strict cookie", "Rotated on every use"],
        ["Device token", "Opaque", "Until revoked", "Secure storage (Keychain / EncryptedSharedPreferences)", "Not renewable"],
    ]},
    {"t": "p", "text": "Ed25519 is preferred over RS256 for mobile because signature "
     "verification is fast on low-end Android hardware, which is a meaningful share of "
     "the target market."},

    {"t": "h3", "text": "12.4.2 Refresh rotation and theft detection"},
    {"t": "bullets", "items": [
        "Each refresh token belongs to a **family**. Using a token rotates it and issues a successor in the same family.",
        "Presenting an already-rotated token means the token was copied — a real device and an attacker now hold the same lineage. The entire family is revoked immediately, all sessions for that member are invalidated, and `security.suspicious_token_reuse` is sent to every registered contact.",
        "This is the standard, well-proven control against refresh-token theft and is preferred over a longer-lived non-rotating token, which is simpler but far more damaging to leak.",
    ]},

    {"t": "h3", "text": "12.4.3 Session controls"},
    {"t": "table", "head": ["Control", "Behaviour"], "widths": [1.7, 4.8], "size": 8.4, "rows": [
        ["Device management", "A member sees every active device and can revoke any of them. Revoking the current device logs it out"],
        ["Concurrent sessions", "Default cap of 5 active sessions; the oldest is evicted on exceeding it"],
        ["Idle timeout", "14 days without activity requires re-authentication"],
        ["Absolute timeout", "90 days maximum session age regardless of activity"],
        ["New device alert", "A login from an unrecognised device triggers `security.login_new_device` by push and email, showing device, location and time"],
        ["Server-side revocation", "Freeze, suspension, password change, and confirmed token theft all revoke server-side immediately — a stolen access token dies within its 15-minute life at the latest"],
    ]},

    {"t": "h2", "text": "12.5 Multi-factor authentication"},
    {"t": "table", "head": ["Factor", "When required", "Fallback"], "widths": [1.4, 2.6, 2.5], "size": 8.4, "rows": [
        ["Email OTP", "Registration, email change, password reset", "None — a verified email is the baseline"],
        ["SMS OTP", "Phone change, bank-account change, payout destination change, withdrawal beyond a threshold", "Email OTP, with a cooling-off period"],
        ["TOTP authenticator app", "Opt-in; **mandatory** for admin and risk roles; strongly encouraged after any payout-dispute resolution", "SMS OTP"],
        ["Biometric (device)", "Mobile local unlock — protects the app on a shared phone, not a substitute for server authentication", "Device PIN"],
        ["Step-up authentication", "Releasing a payout, resolving a dispute, changing a bank account, viewing full BVN", "Re-auth required within the last 5 minutes"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Step-up matters more than MFA here.",
     "text": "The highest-value attack on a savings platform is not password guessing — it "
     "is a member whose session is hijacked, or a fraudster who has convinced a member "
     "to change a bank account. Step-up authentication in front of exactly those actions "
     "is worth more than an MFA toggle."},

    {"t": "h2", "text": "12.6 Password policy and recovery"},
    {"t": "bullets", "items": [
        "Minimum 12 characters, with at least one uppercase, one lowercase and one digit. Length matters far more than composition rules; 12 characters is the floor, and a 16-character passphrase is recommended in the UI copy.",
        "Checked against a breached-password list (k-anonymity range query, so no plaintext is transmitted).",
        "No forced rotation on a schedule. Rotation is required only on a suspected compromise — scheduled rotation pushes people toward `Password123!` variants and is counterproductive.",
        "Reset link: single use, 1-hour expiry, hashed in storage, and **all existing sessions are revoked on use**.",
        "A password change notifies every registered email and device.",
    ]},

    {"t": "h2", "text": "12.7 Role-based access control"},
    {"t": "p", "text": "The six roles are defined in CANONICAL.md §2. A person may hold "
     "multiple roles, and a role is always scoped: `ajo_organizer` is scoped to one Ajo, "
     "while `risk_officer` is platform-wide."},

    {"t": "h3", "text": "12.7.1 Permission matrix"},
    {"t": "code", "size": 7.4, "text": """
Permission                       user  member  organizer  support  risk  super
───────────────────────────────  ────  ──────  ─────────  ──────  ────  ─────
view own profile                 Y      Y         Y          Y*      Y*      Y
edit own profile                 Y      Y         Y          -       -       Y
create an Ajo                    Y      Y         Y          -       -       Y
join an Ajo                      Y      Y         Y          -       -       Y
view own Ajos                    Y      Y         Y          Y       Y       Y
view any member's Ajo            -      -         -          Y       Y       Y
view another member's bank info   -      -         -          -       -       Y
invite members to own Ajo        -      -         Y          -       -       Y
remove member (pre-activation)   -      -         Y          -       -       Y
acknowledge Ajo rules             Y      Y         Y          -       -       Y
pay own contribution             Y      Y         Y          -       -       Y
request own payout               Y      Y         Y          -       -       Y
release an Ajo payout            -      -         Y**        -       -       Y
view own transactions            Y      Y         Y          Y       Y       Y
view all transactions            -      -         -          Y       Y       Y
raise a dispute                   Y      Y         Y          -       -       Y
respond to a dispute             -      -         Y**        Y       Y       Y
resolve a dispute                -      -         -          -       Y       Y
view risk queue                  -      -         -          -       Y       Y
record a risk decision           -      -         -          -       Y       Y
freeze a member                  -      -         -          -       Y       Y
freeze an Ajo                    -      -         -          -       Y       Y
view audit logs                  -      -         -          -       -       Y
assign roles                     -      -         -          -       -       Y
edit or delete a ledger entry    -      -         -          -       -       NEVER
""",
     },
    {"t": "p", "text": "`*` Redacted to essentials.  `**` Scoped strictly to the "
     "Ajos the organizer created. Note the final row: there is no permission, for any "
     "role, that allows editing or deleting a ledger entry."},

    {"t": "h3", "text": "12.7.2 Organizer scope in detail"},
    {"t": "p", "text": "The organizer is the highest-trust non-platform role and the "
     "easiest place for the product to create a liability. Their powers are deliberately "
     "narrow, and every one of them is auditable."},
    {"t": "table", "head": ["Organizer can", "Organizer cannot", "Why"], "widths": [2.1, 2.1, 2.3], "size": 8.4, "rows": [
        ["Create an Ajo and configure it", "Change contribution amount, frequency or duration after activation", "Members committed to those terms; changing them would alter a financial obligation"],
        ["Invite people to join", "Invite without the invitee's informed consent", "A phone number is personal data; disclosure is limited to the minimum"],
        ["Remove a member before activation", "Remove a member after activation", "Post-activation removal would break a live financial cycle"],
        ["Send contribution reminders", "Send messages that misrepresent AJO.ng", "Reminders are AJO.ng messages; impersonation destroys trust platform-wide"],
        ["See who has paid and who has not", "See another member's bank account or BVN", "Payment status is needed to run the group; identity documents are not"],
        ["Acknowledge that a member defaulted", "Publicly shame, disclose, or blacklist a defaulting member", "AJO.ng does not publicly expose defaulting members (BR-019)"],
        ["Request payout release", "Withdraw member funds, hold funds, or change a payout destination", "The organizer is a facilitator, not a custodian or guarantor"],
        ["Approve a replacement member", "Assume the defaulting member's debt", "AJO.ng does not automatically charge other members extra (BR-018)"],
    ]},

    {"t": "h2", "text": "12.8 Account takeover protection"},
    {"t": "table", "head": ["Signal", "Response"], "widths": [2.2, 4.3], "size": 8.4, "rows": [
        ["Failed logins from multiple IPs/ASNs", "Step up to OTP; notify the member; temporary rate limit"],
        ["Impossible travel — two logins far apart in a short time", "Force re-authentication; notify"],
        ["New device + new bank account within a short window", "**Block the bank-account change** pending a cooling-off period and manual review. This combination is the classic redirection-fraud pattern"],
        ["Phone number changed then payout requested", "Hold the payout for manual risk review"],
        ["Sudden change in contribution amount on a new Ajo", "Cap new-Ajo contribution amounts for accounts under 30 days old"],
        ["Many failed OTP attempts", "Cooldown and full session revocation"],
        ["Account recovery request from a new email and phone together", "Hold for 24 hours and require in-app confirmation from an existing session"],
        ["Any admin access from an unrecognised device", "Page the security owner; MFA is already mandatory for admin"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Payout redirection is the highest-value fraud.",
     "text": "In Nigerian fraud, account takeover is rarely aimed at stealing a balance — "
     "there is little to steal until a payout. It is aimed at redirecting the next "
     "payout to an attacker's account. The defence is a **delay between changing a bank "
     "account and receiving a payout**, plus notification of every change to every "
     "registered channel. This single control is worth more than any amount of fraud "
     "scoring."},

    {"t": "h2", "text": "12.9 Segregation of duties"},
    {"t": "bullets", "items": [
        "No person may both **initiate** and **approve** a manual intervention, a refund above a threshold, or a ledger correction.",
        "Risk decisions and dispute resolutions are logged with actor, timestamp, reason and the evidence considered.",
        "Every privileged action writes an `audit_logs` row that is append-only. A privileged action without an audit record is treated as a security incident in itself.",
        "Production database access is time-boxed, ticket-justified and logged. Direct production data edits are prohibited — corrections go through the application so they are validated and recorded.",
    ]},

    {"t": "h2", "text": "12.10 Session and access audit"},
    {"t": "p", "text": "The following are recorded and retained for the periods required "
     "by section 24, whose retention periods **require confirmation by Nigerian legal "
     "counsel**: successful and failed logins, token refreshes, token-reuse detections, "
     "password changes, email and phone changes, bank-account changes, MFA enrolment and "
     "removal, every role assignment, every session revocation, and every step-up "
     "challenge. This record is what allows AJO.ng to answer, months later, the question a "
     "member will inevitably ask: *who changed my bank details, and when?*"},
]
