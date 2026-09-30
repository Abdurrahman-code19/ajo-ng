"""Section 24 — Legal, Regulatory and Compliance Considerations."""

BLOCKS = [
    {"t": "h1", "text": "24. Legal, Regulatory and Compliance Considerations"},

    {"t": "callout", "kind": "LEGAL", "title": "This section is not legal advice.",
     "text": "Nothing in this document constitutes legal advice, and no statement here "
     "should be relied upon as a compliance determination. It is a structured list of "
     "issues the platform must resolve. **Every item requires review by qualified "
     "Nigerian legal and compliance professionals before AJO.ng accepts any real money or "
     "launches to the public.** The purpose of writing them down is to ensure the "
     "questions are asked early, not to pre-empt the answers."},

    {"t": "lead", "text": "AJO.ng sits at an intersection that makes legal structure "
     "genuinely consequential: it collects money from individuals, holds that money in "
     "aggregate, pays it back on a schedule, operates a shared group with a human "
     "organizer at its centre, and handles identity documents. Each of those elements "
     "attracts regulatory attention in its own right."},

    {"t": "h2", "text": "24.1 Questions that must be answered before launch"},
    {"t": "table", "head": ["#", "Question", "Why it is decisive"], "widths": [0.5, 2.7, 3.3], "size": 8.0, "rows": [
        ["1", "Does AJO.ng require registration with a financial regulator, and with which one?", "Determines the licensing path, the capital and governance requirements, and the timeline. This is the first question, and everything else follows from it"],
        ["2", "Does holding member funds in a pooled account constitute custody of client money?", "If yes, the structure, the segregation, the reconciliation, and possibly the licensing all change materially"],
        ["3", "What does the payment provider agreement permit, and what does it prohibit?", "Defines the permitted model. Some providers permit an agency arrangement, some do not permit pooled accounts at all"],
        ["4", "What are the AML and KYC obligations, and who must discharge them?", "Customer due diligence, beneficial ownership, record-keeping, and suspicious activity reporting. A money laundering reporting officer may be legally required"],
        ["5", "What consumer protection rules apply to a savings product?", "Disclosure requirements, cooling-off rights, fair treatment, and complaint handling"],
        ["6", "What are the data protection obligations?", "Registration, lawful basis, retention, data subject rights, and any cross-border transfer restrictions"],
        ["7", "Is the 2% fee regulated, capped, or disclosed in a prescribed way?", "A fee on savings is exactly the kind of charge regulators examine"],
        ["8", "Are contributions refundable, and on what terms?", "Affects both the product and the accounting. Indefinite refund rights would undermine the entire model"],
        ["9", "Is a default a contractual breach, a debt, or a loss?", "Determines what happens to the Ajo when a member does not pay. This is a foundational design question, not an edge case"],
        ["10", "What is the tax treatment of contributions, the fee, and any default?", "Whether the fee is taxable income, whether contributions are deductible, and how defaults are treated"],
        ["11", "What consumer disclosures are mandatory?", "Terms, privacy notice, risk disclosures, and fee disclosure in clear language"],
        ["12", "What are the record-keeping requirements and retention periods?", "Defines the retention schedule in section 14.8, which is currently a proposal"],
    ]},

    {"t": "h2", "text": "24.2 Business structure"},
    {"t": "p", "text": "The structure determines almost everything else, and it is a legal "
     "decision before it is a business one."},
    {"t": "bullets", "items": [
        "**Company structure** — a private limited company is the likely vehicle, but the appropriate entity and its regulatory classification must be confirmed.",
        "**Where the contracting party sits** — the member's agreement is with AJO.ng, the payment provider, or both, and this must be unambiguous in the terms.",
        "**Segregation of funds** — a design decision with legal consequences. The product already requires separate collection, payout, and operating accounts, which is consistent with a strong position, but the adequacy of that separation must be assessed by counsel.",
        "**The platform is not the guarantor.** AJO.ng must never take on the credit risk of a member default, because doing so converts an operating business into a credit business with entirely different capital and regulatory consequences.",
        "**The organizer is not a party to the financial contract** between AJO.ng and its members. The organizer facilitates; the platform contracts. This distinction should be explicit in the terms, because ambiguity here is a significant legal exposure.",
    ]},

    {"t": "h2", "text": "24.3 Role obligations"},
    {"t": "h3", "text": "24.3.1 AJO.ng as platform operator"},
    {"t": "bullets", "items": [
        "Customer due diligence on every member before they can hold a payoutable position.",
        "Record-keeping of transactions, identity verification, and all privileged actions.",
        "Suspicious activity detection, investigation, and reporting where legally required.",
        "Sanctions and politically-exposed-person screening.",
        "Clear, truthful disclosure of the fee, the terms, the risks, and the default policy.",
        "A functioning complaint process with a published route and a response time.",
        "Data protection compliance in full.",
        "Business continuity and incident response, per section 20.6.",
    ]},
    {"t": "h3", "text": "24.3.2 The organizer"},
    {"t": "p", "text": "The organizer performs a genuinely ambiguous function: they bring "
     "people together, set the terms, and hold the group together. That is not a regulated "
     "activity, and AJO.ng should not present it as one — but the platform must define the "
     "role clearly."},
    {"t": "bullets", "items": [
        "The organizer is a **facilitator**, not a trustee, not a custodian, and not a guarantor of member funds.",
        "The organizer **never handles member money**. Contributions are made to AJO.ng; the organizer never collects, holds, forwards, or accounts for it.",
        "The organizer may **not charge any fee**, levy, or 'handling charge' beyond the AJO.ng fee.",
        "The organizer may **not request BVN, PIN, or bank credentials from members**, for any purpose.",
        "The organizer may **not remove a member after activation**, because that would affect committed funds.",
        "The organizer may **not communicate about money outside AJO.ng**, which is both a control and a legal boundary.",
        "The organizer is bound by the Ajo rules, the platform terms, and a specific role agreement.",
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The organizer is the platform's biggest unmanaged risk.",
     "text": "Every serious failure mode that does not involve a technical breach involves a "
     "human being inside an Ajo. A member who believes the organizer is acting for "
     "AJO.ng will do what the organizer asks. AJO.ng's defence is not technical — it is a "
     "clearly written role agreement, unambiguous in-product communication about what the "
     "organizer can and cannot do, a visible reporting channel, and a risk process that "
     "treats organizer behaviour as a first-class risk category rather than a support "
     "ticket."},

    {"t": "h2", "text": "24.4 Consumer protection"},
    {"t": "bullets", "items": [
        "**Transparent fees** — the 2% service fee must be disclosed before every payment, in plain language, and in the terms. It must never be presented as a percentage of what the member receives.",
        "**No hidden charges** — a member may never be charged anything beyond the stated fee. Any future change to the fee must be communicated in advance and never applied retrospectively to an active Ajo.",
        "**Fair treatment** — no discrimination on any basis, and no differential pricing. The fee is the same for every member regardless of amount, which is both simpler and fairer than a tiered structure.",
        "**Access to one's own money** — a member must be able to reach their funds without unreasonable friction. A payout delay beyond the stated window is a consumer harm even when the money is coming.",
        "**Complaint handling** — a published process, a reference number, a named owner, and a response time. A member who cannot find out what happened to a complaint will assume the worst and will be right often enough to be believed.",
        "**Default handling must be fair** — a default is a missed contribution, not a moral failing. The grace period, the recovery offer, and the rule against shaming other members (BR-018, BR-019) are consumer protections as much as product decisions.",
    ]},

    {"t": "h2", "text": "24.5 AML and KYC obligations"},
    {"t": "p", "text": "AJO.ng will be subject to anti-money-laundering obligations to "
     "some degree, and the extent of those obligations depends on the business "
     "characterisation determined in 24.1. The platform should be built to meet the higher "
     "standard, because retrofitting compliance under regulatory pressure is far harder "
     "and more expensive than building it in."},
    {"t": "table", "head": ["Obligation", "What it means here", "Status"], "widths": [1.5, 3.4, 1.6], "size": 8.2, "rows": [
        ["Customer due diligence", "Verify identity before a member can receive a payout. Risk-based, proportionate to the member's activity", "Design defined; provider-dependent"],
        ["Beneficial ownership", "Identify and verify who ultimately owns or controls a member account", "**Legal determination required**"],
        ["Enhanced due diligence", "Additional checks for higher-risk members: large contributors, politically exposed persons, complex structures", "**Legal determination required**"],
        ["Sanctions screening", "Check every member against applicable sanctions lists, at onboarding, on payout, and periodically", "**Requires a licensed screening provider**"],
        ["Transaction monitoring", "The risk engine, plus aggregation across accounts. Per-transaction thresholds alone are insufficient", "Designed in section 15"],
        ["Record keeping", "Identity records, transaction records, and monitoring records for the statutory period", "Periods to be confirmed"],
        ["Suspicious activity reporting", "Report to the FIU within the statutory deadline, with a complete internal case file", "**Deadline and format require counsel**"],
        ["Sanctions reporting", "Report breaches of sanctions immediately", "**Legal determination required**"],
        ["Training", "Staff training on AML obligations, and a named money laundering reporting officer if required", "**Role requirement to be confirmed**"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "AJO.ng does not move money on behalf of members.",
     "text": "A large part of the compliance burden in a payments business comes from "
     "moving money for customers. AJO.ng's design keeps that boundary clear: contributions "
     "buy a rotating savings position, and the payout returns the member's own money rather "
     "than sending funds to a third party on someone's instruction. Whether that framing "
     "holds legally, and what obligations follow from it, is a question for counsel — and "
     "it is one of the most important questions in this section."},

    {"t": "h2", "text": "24.6 Data protection"},
    {"t": "p", "text": "The technical controls are specified in section 14. The legal "
     "requirements are specified here, and the overlap between the two is where most "
     "compliance failures occur — a system can be technically secure and still unlawful "
     "because the lawful basis for processing was never established."},
    {"t": "table", "head": ["Requirement", "How AJO.ng addresses it", "Open item"], "widths": [1.5, 3.4, 1.6], "size": 8.0, "rows": [
        ["Lawful basis for each processing purpose", "Contract necessity for operation; consent for marketing; legitimate interests for fraud prevention, with a balancing assessment", "**Confirm each basis formally**"],
        ["Consent, freely given and informed", "Explicit opt-in with an unlinked accept and reject. No pre-ticked boxes. No service degradation on refusal", "Consent copy to be drafted"],
        ["Data minimisation", "Only fields with a confirmed requirement are collected, including BVN", "**Confirm the BVN requirement**"],
        ["Purpose limitation", "Data collected for verification is not reused for unrelated purposes without a new basis", "Policy to be written"],
        ["Data subject rights", "Access, correction, withdrawal, and deletion, with a single request path", "Process to be documented"],
        ["Retention", "The schedule in section 14.8, with statutory overrides for financial records", "**Periods to be confirmed**"],
        ["Security measures", "Encryption, access control, RLS, audit logging, testing", "Specified in section 14"],
        ["Breach notification", "Escalation to the data protection officer, and notification to the regulator and affected members within statutory deadlines", "**Deadlines to be confirmed**"],
        ["Data processing agreements", "A DPA with every processor, including the payment provider, notification services, and analytics", "**Required before launch**"],
        ["Cross-border transfers", "Data residency assessed per vendor; transfers only with a legal basis", "**Vendor assessment required**"],
        ["Registration with the data protection authority", "If required for the platform's activities", "**Confirm the requirement**"],
    ]},

    {"t": "h2", "text": "24.7 Required documents"},
    {"t": "p", "text": "The following must exist, be reviewed by counsel, and be published "
     "in accessible form before launch. None of them are optional, and shipping a product "
     "with placeholder legal text is a decision to expose every member and the company to "
     "unnecessary risk."},
    {"t": "table", "head": ["Document", "Purpose", "Priority"], "widths": [2.1, 3.2, 1.2], "size": 8.4, "rows": [
        ["Terms of service", "The member agreement with AJO.ng: the service, the fee, the Ajo mechanism, the default policy, liability, and dispute resolution", "P0"],
        ["Privacy notice", "What data is collected, why, the lawful basis, retention, sharing, and the rights available", "P0"],
        ["Cookie and tracking notice", "What is set on the web app, and how to control it", "P0"],
        ["Ajo rules", "The plain-language rules every member and organizer accepts: contribution schedule, position lock, default, recovery, and no off-platform payment", "P0"],
        ["Organizer role agreement", "The organizer's specific permissions and prohibitions", "P0"],
        ["Fee disclosure", "The 2% service fee, stated clearly, before every payment and in the terms", "P0"],
        ["Risk disclosure", "What can go wrong: default, payout delay, provider failure, and that AJO.ng is not a bank or an investment product", "P0"],
        ["Complaint procedure", "How to complain, to whom, and what response to expect", "P0"],
        ["Acceptable use policy", "Prohibitions: fraud, money mule activity, harassment, off-platform solicitation", "P1"],
        ["Data subject request procedure", "Internal procedure for access, correction, and deletion requests", "P0"],
        ["Business continuity and disaster recovery plan", "Required for operational resilience and likely for the payment provider", "P0"],
        ["AML/CTF programme documentation", "Policies, risk assessment, and the reporting process", "**If legally required**"],
    ]},

    {"t": "h2", "text": "24.8 Marketing and claims"},
    {"t": "p", "text": "The way AJO.ng describes itself is a legal matter as much as a "
     "branding one. The following constraints exist to keep the platform out of trouble "
     "with itself."},
    {"t": "bullets", "items": [
        "**AJO.ng is a rotating savings group, not an investment product, a bank, or a lender.** Never claim or imply otherwise. No 'returns', 'yields', 'interest', or 'profits' language.",
        "**The 2% is a service fee charged on contributions**, never described as a percentage of what a member receives. The two framings describe different economics, and only one is true.",
        "**No promise of guaranteed returns.** Members receive their own savings, which is the whole point, and saying so plainly is both honest and a good marketing line.",
        "**No urgency or scarcity pressure.** Savings products sold under time pressure produce defaults, and defaults are the business's main risk.",
        "**Testimonials require consent and must be real.** A fabricated review is a legal and reputational problem.",
        "**No targeting of vulnerable individuals.** Financial products must not be marketed in a way that exploits financial distress.",
        "**All advertising must carry the required disclosures and risk warnings**, and comply with advertising standards as well as financial promotion rules.",
    ]},

    {"t": "h2", "text": "24.9 Intellectual property"},
    {"t": "bullets", "items": [
        "The AJO.ng name and logo require protection. A trademark search should be conducted before launch, and the domain and handles secured across the major platforms.",
        "The codebase, documentation, and design system are the company's assets and belong in the repository with a clear contributor licence.",
        "Third-party open-source dependencies must be licence-compliant, and a dependency licence review should be part of the release process.",
        "Content contributed by members — profile photos, dispute evidence, messages — must have a clear licence for use, or be stored privately without reuse.",
        "Employee and contractor IP assignment agreements should be in place for everyone who writes code or designs product.",
    ]},

    {"t": "h2", "text": "24.10 Employment and staffing considerations"},
    {"t": "bullets", "items": [
        "Employment contracts compliant with Nigerian labour law, with the required statutory deductions and benefits.",
        "Data protection obligations for staff, and confidentiality obligations covering member financial data.",
        "AML training for any staff in a covered role, and documented training records.",
        "Disciplinary procedures that can be applied consistently, particularly for the handling of member data and money.",
        "A whistleblowing mechanism that is genuinely safe to use, given the small size of an early team.",
        "Contractor and agency arrangements for support and risk roles, with the appropriate agreements in place.",
    ]},

    {"t": "h2", "text": "24.11 Insurance"},
    {"t": "bullets", "items": [
        "**Professional indemnity insurance** — for errors and omissions in the service.",
        "**Cyber insurance** — for breach response, notification costs, and restoration. The cost of notifying affected members in Nigeria should be assumed to be significant.",
        "**Crime and fidelity insurance** — covering internal fraud by staff with access to money movement. A dedicated money-handling role is a strong reason to hold this.",
        "**Directors and officers insurance** — once the company has a board.",
        "**Business interruption cover** — reflecting the actual recovery objectives in section 20.6.",
    ]},
    {"t": "p", "text": "Insurance is a business decision and should be taken with an "
     "adviser once the business model and provider agreement are settled, because the "
     "coverage that matters depends on how the money flows."},

    {"t": "h2", "text": "24.12 Obligations by partner"},
    {"t": "table", "head": ["Partner", "Likely obligations", "Open items"], "widths": [1.3, 2.9, 2.3], "size": 8.2, "rows": [
        ["Payment provider (ProvidusUnity)", "KYC on merchants, transaction reporting, settlement reconciliation, adherence to provider policy, prompt incident reporting", "**Merchant onboarding requirements, fees, and permitted use cases to be confirmed**"],
        ["Bank or settlement partner", "Account due diligence, source of funds, ongoing monitoring", "**To be confirmed**"],
        ["Cloud and database providers", "Data processing agreements, security standards, breach notification, data residency", "**DPAs and residency to be confirmed**"],
        ["Notification providers", "Data processing agreements, content standards, delivery reporting", "**DPAs to be executed**"],
        ["App stores", "Privacy declarations, data deletion paths, compliance with store policies", "Standard requirements"],
    ]},

    {"t": "h2", "text": "24.13 Compliance monitoring"},
    {"t": "bullets", "items": [
        "A named compliance owner, with a direct line to the founders.",
        "A compliance register: every obligation, its owner, its evidence, and its review date. An obligation with no evidence is not being met.",
        "Quarterly review of policies against actual practice. Policy documents that describe a system nobody operates are worse than no policy at all, because they create a false record.",
        "Annual review by external advisers, and after any material change to the product or the business model.",
        "Regulatory change monitoring, with a defined process for assessing and implementing changes.",
        "A training register, so it is always possible to demonstrate that staff were trained.",
    ]},

    {"t": "h2", "text": "24.14 Pre-launch legal checklist"},
    {"t": "table", "head": ["#", "Item", "Status"], "widths": [0.5, 4.7, 1.3], "size": 8.4, "rows": [
        ["1", "Regulatory characterisation and licensing determination obtained in writing", "**Outstanding**"],
        ["2", "Payments partner agreement executed, with permitted use cases confirmed", "**Outstanding**"],
        ["3", "Custody position confirmed and the account structure approved", "**Outstanding**"],
        ["4", "Terms of service drafted by counsel and approved", "**Outstanding**"],
        ["5", "Privacy notice and cookie notice drafted by counsel and published", "**Outstanding**"],
        ["6", "Ajo rules and organizer role agreement drafted and approved", "**Outstanding**"],
        ["7", "AML/CTF risk assessment completed, if legally required", "**Outstanding**"],
        ["8", "Data protection registration or notification made, if required", "**Outstanding**"],
        ["9", "Data processing agreements executed with every processor", "**Outstanding**"],
        ["10", "Retention schedule approved and implemented in the system", "**Outstanding**"],
        ["11", "Complaint procedure published and staffed", "**Outstanding**"],
        ["12", "Trademark search completed; name and marks protected", "**Outstanding**"],
        ["13", "Insurance arranged", "**Outstanding**"],
        ["14", "Staff contracts, confidentiality, and IP assignment in place", "**Outstanding**"],
        ["15", "Advice obtained on tax treatment of the fee and of contributions", "**Outstanding**"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "This checklist is the reason the launch date is not a technical decision.",
     "text": "All fifteen items above are outstanding, and every one of them can "
     "take longer than the engineering work. The right response is to open the legal work "
     "now, in parallel with development, rather than to treat it as the final gate before "
     "launch. A fintech that builds for a year and then discovers its structure is wrong "
     "has wasted a year."},
]
