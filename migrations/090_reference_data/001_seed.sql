-- Reference data.
--
-- Adopted from the `ajo` database by
-- scripts/seed_reference_data.py. Do not hand-edit.
--
-- These rows are decisions, not data. They are emitted with explicit ids
-- so a fixture does not depend on a sequence's current value, and
-- `ON CONFLICT DO NOTHING` so the migration is safe to re-run against a
-- database that was seeded by hand during development.

-- contribution_frequencies: 4 row(s)
-- How often contributions fall due. Rounds always equal members, so a frequency sets the gap between rounds rather than the number of them.
INSERT INTO public.contribution_frequencies (id, code, label, interval_count, interval_unit, is_active, sort_order)
  VALUES
  ('01a0ede8-733b-7358-a8f8-1515d0bba644', 'weekly', 'Weekly', '1', 'week', 't', '10'),
  ('01a0ede8-7345-7bad-9a19-4227072dddb0', 'quarterly', 'Quarterly', '3', 'month', 't', '40'),
  ('01a0ede8-7345-7d31-80ea-606e3dd57b2b', 'fortnightly', 'Fortnightly', '2', 'week', 't', '20'),
  ('01a0ede8-7345-7d7c-a699-d71867ec73aa', 'monthly', 'Monthly', '1', 'month', 't', '30')
ON CONFLICT DO NOTHING;

-- roles: 6 row(s)
-- Role codes. Roles are reference data added by migration rather than a hard-coded enum, so a new role is a row and not an ALTER TYPE.
INSERT INTO public.roles (code, scope, name, description, is_active)
  VALUES
  ('ajo_member', 'ajo', 'Ajo member', 'One Ajo. Pay contributions, see own commitment, raise a dispute, request replacement exit. Cannot change payout order post-activation or unilaterally exit after activation.', 't'),
  ('ajo_organizer', 'ajo', 'Ajo organiser', 'One Ajo. Invite and remove pre-activation members, send reminders, propose position order, request payout release. Cannot withdraw member funds, control payouts, change settled records, guarantee another member''s debt, or act after the Ajo completes.', 't'),
  ('risk_officer', 'platform', 'Risk officer', 'View risk events, place accounts or Ajos under review, freeze, approve or reject overrides, manage limits. Cannot delete records, edit the ledger, or change fee configuration.', 't'),
  ('super_admin', 'platform', 'Super admin', 'Manage roles, configure platform settings, emergency freeze. Cannot bypass the append-only ledger or delete financial history.', 't'),
  ('support', 'platform', 'Support', 'Platform-wide read, contact members, assist disputes. Cannot move money or alter financial records. Cannot initiate or moderate payouts, change balances, or override risk decisions.', 't'),
  ('user', 'platform', 'User', 'Own account only. Create and join Ajos, pay, view own records.', 't')
ON CONFLICT DO NOTHING;

-- payment_channels: 3 row(s)
-- Card, bank transfer and the rest, with what each requires of a member.
INSERT INTO public.payment_channels (id, code, label, provider, provider_channel_code, min_amount_kobo, max_amount_kobo, requires_reference, is_active)
  VALUES
  ('01a0ede8-738d-7d8e-84e2-7392ffebf873', 'bank_transfer', 'Bank transfer', 'providusunity', 'bank_transfer', '0', NULL, 'f', 't'),
  ('01a0ede8-7390-7875-89f6-055d27307362', 'card', 'Debit card', 'providusunity', 'card', '0', NULL, 'f', 't'),
  ('01a0ede8-7390-7ba5-8893-5276f114ad01', 'ussd', 'USSD', 'providusunity', 'ussd', '0', NULL, 'f', 't')
ON CONFLICT DO NOTHING;

-- document_types: 10 row(s)
-- The document vocabulary: what a member can be asked to upload, and what it is used for.
INSERT INTO public.document_types (id, code, label, requires_expiry, retention_class, is_special_category, is_active, sort_order)
  VALUES
  ('01a0ede8-7490-7175-912f-cd9efc088bc6', 'avatar', 'Profile photo', 'f', 'ephemeral', 'f', 't', '10'),
  ('01a0ede8-7493-7148-b955-b2835b1e1f9f', 'selfie', 'Liveness selfie', 'f', 'kyc', 't', 't', '30'),
  ('01a0ede8-7493-71c8-984a-f07fd6686a89', 'support_evidence', 'Support evidence', 'f', 'support', 'f', 't', '90'),
  ('01a0ede8-7493-73e3-bc57-38b104b889e2', 'other', 'Other', 'f', 'operational', 'f', 't', '100'),
  ('01a0ede8-7493-74a0-a3f1-1d353ead2fe0', 'cac_certificate', 'CAC certificate', 't', 'kyc', 'f', 't', '50'),
  ('01a0ede8-7493-79ed-a015-df84d060c694', 'proof_of_address', 'Proof of address', 't', 'kyc', 'f', 't', '40'),
  ('01a0ede8-7493-7c58-a4bb-48566a7aeb51', 'bank_account', 'Bank account evidence', 'f', 'kyc', 'f', 't', '70'),
  ('01a0ede8-7493-7d31-825c-ae21ed0091c1', 'dispute_evidence', 'Dispute evidence', 'f', 'dispute', 'f', 't', '80'),
  ('01a0ede8-7493-7e44-8382-ff3e116816b3', 'national_id', 'National identity', 't', 'kyc', 't', 't', '20'),
  ('01a0ede8-7493-7fad-a8fe-41c75544bc0b', 'bank_statement', 'Bank statement', 't', 'kyc', 'f', 't', '60')
ON CONFLICT DO NOTHING;

-- verification_check_types: 7 row(s)
-- Which kinds of identity check exist, and whether a check must pass before an Ajo can activate.
INSERT INTO public.verification_check_types (id, code, label, is_mandatory, document_type_id, provider, is_active, sort_order)
  VALUES
  ('01a0ede8-74d9-71f9-b873-35cdf3cb9352', 'phone', 'Phone number', 't', NULL, 'providusunity', 't', '10'),
  ('01a0ede8-74db-70a8-aac8-31aa0ad6172c', 'bvn', 'BVN', 'f', NULL, 'providusunity', 't', '30'),
  ('01a0ede8-74db-7300-854f-61c9b3eb5656', 'selfie', 'Liveness', 'f', '01a0ede8-7493-7148-b955-b2835b1e1f9f', 'providusunity', 't', '60'),
  ('01a0ede8-74db-76aa-aff2-39b74d41d824', 'nin', 'NIN', 'f', NULL, 'providusunity', 't', '40'),
  ('01a0ede8-74db-784a-a7f1-013c8111a184', 'cac', 'CAC', 'f', '01a0ede8-7493-74a0-a3f1-1d353ead2fe0', 'providusunity', 't', '50'),
  ('01a0ede8-74db-7b05-af12-3f072d8485fc', 'email', 'Email address', 't', NULL, 'internal', 't', '20'),
  ('01a0ede8-74dc-79e0-8648-27e721799b1c', 'bank_account', 'Bank account', 'f', '01a0ede8-7493-7c58-a4bb-48566a7aeb51', 'providusunity', 't', '70')
ON CONFLICT DO NOTHING;

-- dispute_reasons: 8 row(s)
-- The vocabulary support scripts off. A free-text dispute reason produces a report nobody can group by.
INSERT INTO public.dispute_reasons (id, code, label, is_active)
  VALUES
  ('01a0ede8-7443-78d7-ab22-453812563e21', 'contribution_wrong_amount', 'I was charged the wrong amount', 't'),
  ('01a0ede8-7445-7015-b40b-447bcf13687e', 'other', 'Something else', 't'),
  ('01a0ede8-7445-7568-b85b-41070a3dd369', 'unfair_removal', 'I was removed unfairly', 't'),
  ('01a0ede8-7445-75e3-a693-94ffdb48a65b', 'payout_wrong_amount', 'I received the wrong amount', 't'),
  ('01a0ede8-7445-7ad5-8f7c-033e7943b298', 'payout_not_received', 'My payout has not arrived', 't'),
  ('01a0ede8-7445-7d20-8c71-430917a924e7', 'position_dispute', 'I disagree with the position order', 't'),
  ('01a0ede8-7445-7f06-871d-77d038e28718', 'contribution_not_recorded', 'My payment is not showing', 't'),
  ('01a0ede8-7445-7f13-b10a-bb83322c5477', 'duplicate_charge', 'I was charged twice', 't')
ON CONFLICT DO NOTHING;

-- platform_settings: 7 row(s)
-- Platform-wide configuration. Readable by members, writable only by migration.
INSERT INTO public.platform_settings (key, value, value_type, description, is_sensitive, updated_by)
  VALUES
  ('default_contribution_kobo', '1000000', 'integer', 'Assumption pending founders: NGN 10,000.00 default contribution. Overridden per Ajo in ajos.contribution_amount_kobo.', 'f', NULL),
  ('enrollment_window_days', '5', 'integer', 'CANONICAL.md section 3: the enrollment window is exactly five days.', 'f', NULL),
  ('fee_bps', '200', 'integer', 'Platform fee in basis points. CANONICAL.md section 1 fixes this at 200 (2%). Stored for auditability; the arithmetic is compiled into the generated columns on payments, contributions and fees and cannot diverge from this value.', 'f', NULL),
  ('fee_label', '"2%"', 'string', 'The fee label shown on every disclosure.', 'f', NULL),
  ('grace_period_hours', '"48"', 'integer', 'CANONICAL.md section 4: 48-hour grace before a default is recorded.', 'f', NULL),
  ('platform_currency', '"NGN"', 'string', 'Single currency at v1. See money.ts.', 'f', NULL),
  ('sms_reserved_for', '["money_critical", "security_critical"]', 'json', 'CANONICAL.md section 8: SMS is reserved for money-critical and security events.', 'f', NULL)
ON CONFLICT DO NOTHING;

