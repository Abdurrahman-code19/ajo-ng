-- Actually telling the member that their tokens were copied.
--
-- Migration 103 detects the two security events in section 12.4 and writes an
-- audit row for each. It stops there, and that is the right place for a
-- migration to stop: an audit row is a record that something happened, and
-- 12.4.2 does not say the member is told. It says `security.suspicious_token_reuse`
-- "is sent to every registered contact", and nothing in the repository did
-- that. A member whose sessions were all revoked at three in the morning had
-- no way to find out, and would have worked it out from a login screen that
-- had suddenly forgotten them.
--
-- So this migration supplies the missing half, and it is structured around one
-- property that decides everything else: **the enqueue has to be in the same
-- transaction as the revocation.** Not "shortly after", not "on the next
-- request" -- the same transaction. A worker that polls an audit table after
-- the fact has a window in which a crash, a deploy or a backlog turns a
-- compromise alarm into silence, and for this one event the entire value is
-- that it cannot be lost. It is the same reason the revocation itself is a
-- single statement rather than a delete followed by an audit write.
--
-- Which is why the enqueue is a trigger on `audit_logs` and not a call in the
-- login handler. The reuse detection happens inside `app.claim_refresh_token`,
-- a SECURITY DEFINER function that 103 shipped and that this migration cannot
-- edit. A trigger on the audit row it already writes gets the enqueue into that
-- function's transaction without rewriting the function, so the event and its
-- notification commit or vanish together, which is the only pairing that
-- actually means anything.
--
-- The catalogue gap, and the schema that had already closed it
-- -----------------------------------------------------------
-- `security.suspicious_token_reuse` is required by 12.4.2 and is *not* in
-- CANONICAL.md section 8's notification catalogue. The catalogue has
-- `security.login_new_device` and `account.frozen` and no reuse row, so the spec
-- names an event in one place and does not list it in the table that is
-- declared canonical.
--
-- The obvious resolution is to follow the catalogue and deliver push and email
-- only. That resolution is already forbidden, and finding that out is the reason
-- this section is worth reading: `app.assert_money_critical_has_sms` is a
-- DEFERRABLE INITIALLY DEFERRED constraint trigger on `notification_templates`
-- that refuses any row with `is_security` unless that event has an active SMS
-- template. Seeding the two channels above fails at COMMIT with exactly that
-- error. The schema encodes a stronger reading of section 8 than the catalogue
-- prints -- SMS is not merely *permitted* for a security event, it is
-- *required* -- and it is the better reading. "SMS reserved for money-critical
-- and security events" is about who pays for a text message, and the answer for
-- an account takeover is that the platform does.
--
-- So both events get all three channels, and two consequences are recorded here
-- rather than discovered in production:
--
--   * CANONICAL.md section 8 shows "—" for `security.login_new_device` SMS. The
--     schema has been requiring SMS for it since migration 000, so that cell is
--     a documentation bug and the trigger is right. TODO.md records the fix.
--   * Both events need a phone number to be useful on SMS. `users.phone_e164` is
--     nullable, so `app.member_phone` returns NULL for a member who registered
--     without one and the worker skips that row. That is the right answer --
--     inventing a placeholder address would produce a send that fails forever
--     and bury the events that can be delivered -- but it does mean SMS coverage
--     for these events is "every member who gave us a number", not "every
--     member".
--
-- No preference is consulted, ever
-- -------------------------------
-- `notification_preferences` has `push_enabled`, `email_enabled`,
-- `sms_enabled`, `money_sms_opt_in` and a quiet-hours pair, and this migration
-- does not read any of them. That is the whole point, and it is worth being
-- explicit about because the naive version of this feature reads them and is
-- wrong in a way that is very hard to notice.
--
-- A member can switch off marketing-adjacent categories. Section 6's preference
-- screen says money-critical and security events "cannot be switched off,
-- because a savings product that lets you stop telling you it cannot pay you
-- has a different product than the one described in CANONICAL.md". The reuse
-- alarm is that case exactly, and in the worst instance: a preference that
-- silences it means an attacker holds live sessions against an account that
-- has explicitly asked not to be disturbed. Quiet hours have the same problem in
-- a milder form -- a breach detected at 3am is exactly when the member wants to
-- know, and deferring it to 7am is how the attacker finishes.
--
-- The rule is therefore enforced by the absence of code: no SELECT against
-- `notification_preferences` appears in this file. Both events are marked
-- `is_security`, so if a general-purpose dispatcher is written later, the
-- suppression path has something unambiguous to key off, and this file's
-- behaviour is the documented default rather than a special case someone has to
-- rediscover.
--
-- Delivery is at-least-once, and that is deliberate
-- --------------------------------------------------
-- `notifications_dedupe_unique` is UNIQUE on (dedupe_key, channel), so a given
-- event produces at most one message per channel. Materialisation is therefore
-- exactly-once.
--
-- Delivery after that is at-least-once, because `app.claim_queued_notifications`
-- leases a row by pushing `scheduled_for` forward rather than by marking it in
-- flight -- `notification_status` has no 'sending' value, and adding one to an
-- adopted enum is not this migration's business. If the worker dies between the
-- lease and the send, the lease expires and the row is offered again.
--
-- For this event that is the correct trade and not merely the usual one. A
-- member who receives "we signed you out, was this you?" twice has been
-- frightened twice and loses nothing. A member who receives it zero times has
-- been robbed. Two failures are not equivalent here, and a queue that quietly
-- drops on crash is the second one.

-- ---------------------------------------------------------------------------
-- 1. The templates.
--
-- Six rows: two events, three channels each -- push, email, sms. The sms row is
-- not optional. `app.assert_money_critical_has_sms` is a deferred constraint
-- trigger that refuses to commit any `is_security` template whose event has no
-- active sms template, and it fires at COMMIT rather than per row, so all three
-- channels for one event have to land in the same transaction. The hint in that
-- trigger says so.
--
-- The bodies are templates in the `{{key}}` sense and the substitution happens
-- in `app.render_notification_body`, which walks the payload rather than doing
-- anything clever. `is_security` is set on all six so the flag is queryable:
-- `app.drain_security_notifications` filters on it, which is what makes the
-- suppression decision sit next to the template rather than in a list of event
-- keys inside a worker.
--
-- The two sms bodies are short on purpose. A text message is read on a phone in
-- the street, usually by one hand, so they carry the decision and nothing else
-- -- where to look, what to do -- and put the detail in the email, which is
-- where a member goes when they want to read properly.
--
-- No attempt is made to make any of these bodies pretty. They are plain text
-- because the adopted channel enum is push/email/sms with no rendering layer,
-- and a template engine would be a dependency chosen by a migration.
-- ---------------------------------------------------------------------------
INSERT INTO public.notification_templates
  (event_key, channel, subject, body, is_security, is_money_critical, is_active)
VALUES
  (
    'security.login_new_device',
    'push',
    'New sign-in to your Ajo account',
    E'You signed in to Ajo from a device we have not seen before.\n\n'
    'Device: {{device_label}}\nPlatform: {{platform}}\nLocation: {{ip_address}}\nTime: {{occurred_at}}\n\n'
    'If this was you, no action is needed. If it was not, sign out and revoke your sessions now.',
    true,
    false,
    true
  ),
  (
    'security.login_new_device',
    'email',
    'New sign-in to your Ajo account',
    E'You signed in to Ajo from a device we have not seen before.\n\n'
    'Device: {{device_label}}\nPlatform: {{platform}}\nLocation: {{ip_address}}\nTime: {{occurred_at}}\n\n'
    'If this was you, no action is needed. If it was not, sign out and revoke your sessions now:\n\n'
    '  GET    /api/v1/auth/sessions\n'
    '  DELETE /api/v1/auth/sessions/:id\n\n'
    'Changing your password signs you out everywhere.',
    true,
    false,
    true
  ),
  (
    'security.login_new_device',
    'sms',
    NULL,
    'Ajo: new sign-in from ' || '{{platform}}{{device_label_clause}}'
      || ' at ' || '{{ip_address}}. If this was you, ignore this. If not, revoke your sessions now.',
    true,
    false,
    true
  ),
  (
    'security.suspicious_token_reuse',
    'push',
    'Your Ajo sessions were signed out',
    E'Someone presented a refresh token that had already been used. That usually '
    'means the token was copied, so we signed out every session on your account.\n\n'
    'Time: {{occurred_at}}\n\n'
    'If you do not recognise this, change your password immediately.',
    true,
    false,
    true
  ),
  (
    'security.suspicious_token_reuse',
    'email',
    'Your Ajo sessions were signed out',
    E'Someone presented a refresh token that had already been used. That usually '
    'means the token was copied, so we signed out every session on your account.\n\n'
    'Time: {{occurred_at}}\n\n'
    'If this was you, it may be a device that refreshed twice at once. If it was '
    'not, change your password immediately, then sign in again on the device you trust.\n\n'
    'What we know: one of your refresh tokens was presented a second time after it '
    'had already been replaced. A token cannot tell us whether that was an attacker '
    'or a slow client on your own machine, which is why we sign you out either way '
    'and let you decide.',
    true,
    false,
    true
  ),
(
    'security.suspicious_token_reuse',
    'sms',
    NULL,
    'Ajo: someone used a sign-in token twice, so we signed you out everywhere at '
      || '{{occurred_at}}. If this was you, ignore it. If not, change your password now.',
    true,
    false,
    true
  )
ON CONFLICT (event_key, channel) DO NOTHING;

COMMENT ON TABLE public.outbox_events IS
  'The transactional outbox. Rows are written in the same transaction as the change '
  'that caused them, so an event cannot be lost by a crash between the business '
  'logic committing and a worker noticing. Migration 104 first uses it: the '
  'session.refresh_token_reuse and session.login_new_device audit rows enqueue '
  'here from a trigger, and app.drain_security_notifications materialises them '
  'into `notifications`.';

-- ---------------------------------------------------------------------------
-- 2. Enqueue.
--
-- SECURITY DEFINER because `outbox_events` has RLS on and its only policy is
-- `outbox_events_select_staff`, which needs a platform-staff identity. A trigger
-- firing inside an audit insert has one: the audit row's own actor, which for
-- both events is 'system' and carries no user id. So this function is the thing
-- that makes the write possible, and it is written as a function rather than
-- inline in the trigger for that reason alone.
--
-- ON CONFLICT DO NOTHING against `outbox_events_dedupe_unique`, which is
-- UNIQUE (event_type, aggregate_id). One enqueue per event per session, which
-- is the right granularity: a session cannot legitimately produce two reuse
-- events, because the first one revokes it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.enqueue_security_notification(
  p_event_key    text,
  p_aggregate_id uuid,
  p_user_id      uuid,
  p_payload      jsonb
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, app
AS $$
BEGIN
  -- No `scheduled_for`: `outbox_events` has `next_retry_at` instead, and the
  -- column list is spelled out rather than relying on the default so that a later
  -- migration adding a NOT NULL column cannot turn this into a runtime error
  -- inside the reuse detection.
  INSERT INTO public.outbox_events
    (aggregate_type, aggregate_id, event_type, payload, status, next_retry_at)
  VALUES
    ('session', p_aggregate_id, p_event_key,
     coalesce(p_payload, '{}'::jsonb) || jsonb_build_object('user_id', p_user_id),
     'pending', now())
  ON CONFLICT (event_type, aggregate_id) DO NOTHING;
END;
$$;

COMMENT ON FUNCTION app.enqueue_security_notification(text, uuid, uuid, jsonb) IS
  'Writes one row to the outbox. Called by the audit_logs trigger, inside the '
  'transaction that produced the security event, so the alarm and the revocation '
  'are the same commit.';

-- ---------------------------------------------------------------------------
-- 3. The trigger.
--
-- Fires only for the two security actions, and only on INSERT. 103 writes its
-- audit row as part of the revocation statement, so this lands in the same
-- transaction as `UPDATE sessions SET revoked_at = ... WHERE user_id = ...`.
--
-- The filter is a WHEN clause rather than an IF inside the body so the trigger
-- does not become an entry point for every audit row in the system. Audit rows
-- are written on registration, verification, consent, contribution and payout,
-- and this trigger does not need to see any of them.
--
-- `after_state->>'user_id'` is where 103 puts the affected member: the audit row
-- deliberately has `actor_user_id = NULL`, because the actor of a reuse is not
-- the member -- it is whoever presented the copied token, who is not known and
-- may not be a user at all. So the notification recipient is read out of the
-- payload rather than the actor column, and the two being different is the
-- point: this is a notification *about* the member, not *from* them.
--
-- A NULL user_id means the row is not about a member -- a staff or service
-- audit row that happens to share the action name. Returning quietly is right
-- there; the alternative is an outbox event no worker can ever resolve.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.security_audit_to_outbox()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, app
AS $$
DECLARE
  v_user_id  uuid;
  v_event_key text;
BEGIN
  v_user_id := (NEW.after_state ->> 'user_id')::uuid;

  IF v_user_id IS NULL THEN
    RETURN NEW;
  END IF;

  v_event_key := CASE NEW.action
    WHEN 'session.refresh_token_reuse' THEN 'security.suspicious_token_reuse'
    WHEN 'session.login_new_device'    THEN 'security.login_new_device'
  END;

  IF v_event_key IS NULL THEN
    RETURN NEW;
  END IF;

  PERFORM app.enqueue_security_notification(
    v_event_key,
    NEW.subject_id,
    v_user_id,
    coalesce(NEW.after_state, '{}'::jsonb)
  );

  RETURN NEW;
END;
$$;

CREATE TRIGGER audit_logs_security_to_outbox
  AFTER INSERT ON public.audit_logs
  FOR EACH ROW
  WHEN (NEW.action IN ('session.refresh_token_reuse', 'session.login_new_device'))
  EXECUTE FUNCTION app.security_audit_to_outbox();

COMMENT ON TRIGGER audit_logs_security_to_outbox ON public.audit_logs IS
  'Turns the two session security audit rows into outbox events in the same '
  'transaction. A trigger rather than a call in the request handler because the '
  'reuse event is detected inside app.claim_refresh_token, a shipped function '
  'this migration must not edit, and the alarm has to commit with the revocation '
  'or it is worthless.';

-- ---------------------------------------------------------------------------
-- 4. Recognising a new device.
--
-- 12.4.3 and US-04: the alert is for "an unrecognised device or location", and
-- revoking a session must not raise it. US-04 is the constraint that shapes
-- this function, because a naive "is there a live session for this device?"
-- check gets it wrong in both directions.
--
-- It searches *every* session row the member has ever had, revoked ones
-- included, and not just the live ones. Two ordinary flows would otherwise
-- alert:
--
--   * Sign out, then sign back in on the same phone. The old session is revoked,
--     so a live-only check finds nothing and sends "we have not seen this
--     device before" to the member's own account. This is the common case --
--     people sign out constantly -- and it trains people to ignore the alert,
--     which is how the alert stops working at all.
--   * Revoke a session from the sessions list, then the client re-authenticates.
--     Same false alarm, and US-04 explicitly says revoking must not send one.
--
-- A revoked session is evidence, as 103's own comments say at length, and it is
-- also the record that this member has used this device before. Both facts come
-- from the same row, and searching history rather than live rows is what makes
-- "unrecognised" mean "never seen" instead of "not currently signed in".
--
-- The comparison is `IS NOT DISTINCT FROM` on both columns, which is the NULL
-- case rather than an oversight. A client that sends no `device_label` and no
-- `platform` produces a row of NULLs, and every such client collides with every
-- other NULL client under plain `=`, because NULL = NULL is unknown. The
-- members most likely to send nothing are browser clients on older builds, and
-- treating all of them as one device would mean the sixth silent login alerted
-- and the first five did not -- an ordering no user can explain and no support
-- answer can give.
--
-- This looks inconsistent with `REPLACE_SAME_DEVICE` in `login.ts`, which also
-- uses `IS NOT DISTINCT FROM`, and the two are not comparable: replacing is
-- about the live invariant `sessions_one_active_per_device` enforces, and
-- matching is about identity, and identity has to treat NULLs as equal or it has
-- no stable answer. It is recorded here because the next reader will wonder.
--
-- `p_session_id` is the session this call is *about*, and it is excluded from the
-- lookup rather than looked up. So the caller inserts the session first and then
-- calls this, which is the order the login handler already had, and the function
-- is not required to run before the INSERT. Getting that wrong in the other
-- direction -- excluding too much -- would make a device look new on every login,
-- so the exclusion is by exact id and not by anything coarser.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.record_login_new_device(
  p_user_id      uuid,
  p_session_id   uuid,
  p_platform     text,
  p_device_label text,
  p_ip_address   inet,
  p_user_agent   text
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, app
AS $$
DECLARE
  v_seen_before boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1
      FROM public.sessions
     WHERE user_id = p_user_id
       -- Excluding the session being described. This is what lets the caller run
       -- the function *after* the INSERT and pass the real id: without it the
       -- lookup finds the row the caller just wrote and reports every login as a
       -- familiar device, which is a function that never sends an alert. Passing
       -- the real id also means the audit row's `subject_id` and the outbox row's
       -- `aggregate_id` are the session that actually exists, rather than a
       -- generated uuid -- which matters because
       -- `outbox_events_dedupe_unique` is UNIQUE (event_type, aggregate_id), so an
       -- id that never matches a session cannot dedupe against anything.
       AND id IS DISTINCT FROM p_session_id
       AND platform IS NOT DISTINCT FROM p_platform
       AND device_label IS NOT DISTINCT FROM p_device_label
  )
  INTO v_seen_before;

  IF v_seen_before THEN
    RETURN false;
  END IF;

  INSERT INTO public.audit_logs
    (actor_user_id, actor_type, action, subject_type, subject_id,
     ip_address, user_agent, after_state)
  VALUES
    (NULL, 'system', 'session.login_new_device', 'session', p_session_id,
     p_ip_address, p_user_agent,
     jsonb_build_object(
       'user_id', p_user_id,
       'platform', p_platform,
       'device_label', p_device_label,
       -- A text message has room for the device name and the platform or for
       -- the platform alone, but not for "on iOS from " followed by nothing.
       -- The clause is composed here rather than in the template because the
       -- template language is placeholder substitution and cannot decide
       -- whether a fragment is needed at all.
       'device_label_clause',
         CASE WHEN p_device_label IS NULL OR p_device_label = '' THEN ''
              ELSE ' (' || left(p_device_label, 40) || ')' END,
       'ip_address', host(p_ip_address),
       'user_agent', p_user_agent,
       'occurred_at', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') || ' UTC'
     ));

  RETURN true;
END;
$$;

COMMENT ON FUNCTION app.record_login_new_device(uuid, uuid, text, text, inet, text) IS
  'Writes the session.login_new_device audit row when the member has never used '
  'this (platform, device_label) pair before, and returns whether it did. Called '
  'before the session INSERT, because afterwards the row being created is the '
  'evidence that the device exists.';

-- ---------------------------------------------------------------------------
-- 5. Rendering and contact resolution.
--
-- Defined before the drain functions that call them. plpgsql does not resolve
-- function references until the statement runs, so the order is not strictly
-- required -- but a migration that only works because of when it is read is a
-- migration that reads as broken, and the reader is the point of the comments.
-- ---------------------------------------------------------------------------

-- Substitution over the payload. `jsonb_each_text` is the whole mechanism: a
-- template may reference any key the caller supplied and gets '' for one it did
-- not, which is better than failing the delivery of a security alarm over a
-- missing optional field. A placeholder the payload does not supply is left
-- alone, for the caller to strip.
--
-- `replace` is case-sensitive and does not interpret backreferences, so `{{`
-- needs no escaping -- worth stating because a habit of doubling backslashes in
-- generated SQL gets cargo-culted into functions where it is wrong.
CREATE OR REPLACE FUNCTION app.render_notification_body(
  p_template text,
  p_payload  jsonb
)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_key   text;
  v_value text;
  v_out   text := p_template;
BEGIN
  IF p_template IS NULL OR p_payload IS NULL THEN
    RETURN p_template;
  END IF;

  FOR v_key, v_value IN
    SELECT key, value FROM jsonb_each_text(p_payload)
  LOOP
    v_out := replace(v_out, '{{' || v_key || '}}', coalesce(v_value, ''));
  END LOOP;

  RETURN v_out;
END;
$$;

COMMENT ON FUNCTION app.render_notification_body(text, jsonb) IS
  'Substitutes {{key}} placeholders from a JSON payload. Any placeholder the '
  'payload does not supply is left alone, for the caller to strip -- so a '
  'template with a typo produces a slightly odd message rather than a delivery '
  'failure.';

-- "Sent to every registered contact" -- 12.4.2. In this schema a member's
-- registered contacts are `users.email` (NOT NULL, citext) and
-- `users.phone_e164` (nullable). There is no contacts table, so "every
-- registered contact" is those two columns, and this function pair is the only
-- place that resolves them.
--
-- SECURITY DEFINER because `users` has FORCE ROW LEVEL SECURITY and
-- `users_select_self_or_staff` needs an identity. A worker holds none -- it is
-- sending *about* members, not as them.
--
-- Nullable, deliberately. A member with no phone on file gets NULL for sms and
-- the delivery worker skips the row. Inventing a placeholder address would
-- produce a send that fails loudly and repeatedly, and marking the row failed
-- forever would bury the events that can actually be delivered.
CREATE OR REPLACE FUNCTION app.member_email(p_user_id uuid)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT u.email::text FROM public.users u WHERE u.id = p_user_id;
$$;

CREATE OR REPLACE FUNCTION app.member_phone(p_user_id uuid)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT u.phone_e164::text FROM public.users u WHERE u.id = p_user_id;
$$;

COMMENT ON FUNCTION app.member_email(uuid) IS
  'The member''s registered email address, which is NOT NULL in the adopted '
  'schema. Resolved as SECURITY DEFINER because FORCE ROW LEVEL SECURITY on '
  'users means a worker with no identity cannot read the row.';

COMMENT ON FUNCTION app.member_phone(uuid) IS
  'The member''s registered phone in E.164, or NULL when they registered '
  'without one. NULL is the answer, not an error: it means there is nothing to '
  'send to on the sms channel for this member.';

-- ---------------------------------------------------------------------------
-- 6. Draining.
--
-- Outbox -> notifications, atomically. Both the FOR UPDATE and the status change
-- happen in one function, so an event cannot be marked published without its
-- notification rows existing, and cannot have its notification rows created
-- without being marked published. Splitting it into "claim, then write" would
-- put a crash between them and lose the alarm, which is the failure this whole
-- migration exists to prevent.
--
-- SKIP LOCKED so two API replicas polling at the same moment do not fight over
-- the same event and do not block each other.
--
-- The ORDER BY is on `next_retry_at`, which is the retry backoff, ahead of
-- `created_at` so a retried event is offered before a fresh one -- a member
-- should hear about a compromise before a routine new-device login.
--
-- RETURN QUERY, not a bare INSERT ... RETURNING. plpgsql raises "query has no
-- destination for result data" for a SQL statement carrying a RETURNING clause
-- with no INTO, so `RETURN QUERY <insert ... returning *>` is the shape that
-- both writes the rows and hands the caller exactly the rows this call inserted.
-- A re-drain that finds the event already published returns nothing, and a
-- duplicate event -- which `notifications_dedupe_unique` blocks -- returns
-- nothing too.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.drain_security_notifications(p_limit integer DEFAULT 20)
RETURNS SETOF public.notifications
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, app
AS $$
DECLARE
  v_event RECORD;
BEGIN
  IF p_limit IS NULL OR p_limit < 1 THEN
    RAISE EXCEPTION 'p_limit must be a positive integer, got %', p_limit;
  END IF;

  FOR v_event IN
    SELECT id, event_type, aggregate_id, payload
      FROM public.outbox_events
     WHERE status = 'pending'
       AND next_retry_at <= now()
     ORDER BY next_retry_at, created_at
     FOR UPDATE SKIP LOCKED
     LIMIT p_limit
  LOOP
    RETURN QUERY
      INSERT INTO public.notifications
        (user_id, template_id, event_key, channel, status, subject, body,
         payload, dedupe_key, scheduled_for)
      SELECT
        (v_event.payload ->> 'user_id')::uuid,
        t.id,
        t.event_key,
        t.channel,
        'queued',
        t.subject,
        -- Placeholder substitution, then strip anything the payload did not
        -- supply. A leftover {{token}} in a security email looks broken and
        -- erodes trust in the one message that must be believed.
        trim(both E'\n' FROM regexp_replace(
          app.render_notification_body(t.body, coalesce(v_event.payload, '{}'::jsonb)),
          '\{\{\s*[a-z_]+\s*\}\}', '', 'g'
        )),
        coalesce(v_event.payload, '{}'::jsonb),
        t.event_key || ':' || v_event.aggregate_id::text,
        now()
        FROM public.notification_templates t
       WHERE t.event_key = v_event.event_type
         AND t.is_active
         AND t.is_security
      ON CONFLICT (dedupe_key, channel) DO NOTHING
      RETURNING *;

    UPDATE public.outbox_events
       SET status = 'published',
           published_at = now()
     WHERE id = v_event.id;
  END LOOP;
END;
$$;

COMMENT ON FUNCTION app.drain_security_notifications(integer) IS
  'Materialises queued security notifications from the outbox and marks the '
  'events published, in one transaction. Returns only the rows this call '
  'inserted. A caller that gets an empty set has nothing to do.';

-- ---------------------------------------------------------------------------
-- 7. Leasing queued notifications for delivery.
--
-- SELECT ... FOR UPDATE SKIP LOCKED, then push scheduled_for forward by
-- p_lease_seconds. This is the lease discussed at the top: `notification_status`
-- has no in-flight value, so visibility is expressed in time instead. A worker
-- that crashes mid-send leaves the row 'queued' with a future scheduled_for, and
-- the next pass picks it up once the lease expires.
--
-- `notifications` has no attempt counter and this does not fabricate one.
-- `outbox_events.attempts` is real but counts enqueue retries, not delivery
-- attempts, and reporting one as the other would be a plausible-looking lie in
-- an ops dashboard.
--
-- The default lease is far longer than the mail relay's 10s timeout. Making it
-- *shorter* than the slowest plausible send would be the bug: two workers would
-- pick up the same row and every breach would alarm twice.
--
-- Push rows come back with a NULL recipient on purpose. Resolving a push target
-- means reading `device_tokens`, and delivering to APNs or FCM means a provider
-- that does not exist in this repository. Queuing the row records the intent and
-- gives the future provider somewhere to look; pretending to resolve a target
-- here would be a function that returns NULL for every real member.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.claim_queued_notifications(
  p_limit         integer DEFAULT 20,
  p_lease_seconds integer DEFAULT 300
)
RETURNS TABLE (
  id        uuid,
  user_id   uuid,
  event_key text,
  channel   public.notification_channel,
  subject   text,
  body      text,
  recipient text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, app
AS $$
BEGIN
  IF p_limit IS NULL OR p_limit < 1 THEN
    RAISE EXCEPTION 'p_limit must be a positive integer, got %', p_limit;
  END IF;

  RETURN QUERY
    WITH claimed AS (
      SELECT n.id, n.user_id, n.event_key, n.channel, n.subject, n.body
        FROM public.notifications n
       WHERE n.status = 'queued'
         AND n.scheduled_for <= now()
         AND n.deleted_at IS NULL
       ORDER BY n.scheduled_for, n.created_at
       FOR UPDATE SKIP LOCKED
       LIMIT p_limit
    ),
    leased AS (
      UPDATE public.notifications n
         SET scheduled_for = now() + make_interval(secs => greatest(p_lease_seconds, 1))
        FROM claimed c
       WHERE n.id = c.id
      RETURNING n.id, n.user_id, n.event_key, n.channel, n.subject, n.body
    )
    SELECT l.id, l.user_id, l.event_key, l.channel, l.subject, l.body,
           CASE l.channel
             WHEN 'email' THEN app.member_email(l.user_id)
             WHEN 'sms'   THEN app.member_phone(l.user_id)
             ELSE NULL
           END
      FROM leased l;
END;
$$;

COMMENT ON FUNCTION app.claim_queued_notifications(integer, integer) IS
  'Leases queued notifications for delivery by pushing scheduled_for into the '
  'future, and returns them with a resolved recipient where the channel has one. '
  'push returns NULL: there is no push provider to deliver to yet.';

-- ---------------------------------------------------------------------------
-- 8. Send and fail.
--
-- Both SECURITY DEFINER for the same reason as the claim: `notifications` has
-- `notifications_select_own` and `notifications_update_own`, and a worker is
-- not the member. Marking a row sent is the last thing that happens, so it needs
-- to be able to write a row the worker could not have selected.
--
-- `mark_notification_failed` does not schedule a retry. Delivery retries are a
-- provider concern; the mail relay rejects with an HTTP status and retrying a
-- message a provider will keep rejecting only buries the events that can be
-- delivered. `failed_at` plus a bounded `failure_detail` is what makes it
-- investigable instead. The 500-character cap is because `failure_detail` is
-- free text and a provider error body can be megabytes.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.mark_notification_sent(p_notification_id uuid)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  UPDATE public.notifications
     SET status = 'sent',
         sent_at = now()
   WHERE id = p_notification_id;
$$;

CREATE OR REPLACE FUNCTION app.mark_notification_failed(
  p_notification_id uuid,
  p_detail text
)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  UPDATE public.notifications
     SET status = 'failed',
         failed_at = now(),
         failure_detail = left(coalesce(p_detail, ''), 500)
   WHERE id = p_notification_id;
$$;

-- ---------------------------------------------------------------------------
-- 9. Who may call what.
--
-- `bootstrap_roles.sql` runs before any migration, so its
-- `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO ajo_app` covers the functions
-- that exist when it runs and nothing created afterwards. The functions in 103
-- are reachable because PostgreSQL's default is EXECUTE TO PUBLIC and the
-- REVOKE that would have withdrawn it had already happened by then.
--
-- That default is too loose for the delivery functions here, so it is closed
-- rather than inherited. `app.drain_security_notifications` and
-- `app.claim_queued_notifications` take a user id from their caller and write
-- real rows that a real relay sends mail from, so any role holding EXECUTE can
-- address an alarm to an arbitrary member -- and `PUBLIC` includes every role in
-- the cluster, including ones nobody has added yet.
--
-- The enqueue, render and contact functions stay reachable by `ajo_app`,
-- because the login path needs `app.record_login_new_device` and the trigger
-- needs the rest. The delivery functions do not, so they are REVOKEd from PUBLIC
-- and granted to `ajo_app` explicitly -- which is the role the worker connects
-- as, since `ajo_api` is a member of it.
-- ---------------------------------------------------------------------------
REVOKE EXECUTE ON FUNCTION
  app.drain_security_notifications(integer),
  app.claim_queued_notifications(integer, integer),
  app.mark_notification_sent(uuid),
  app.mark_notification_failed(uuid, text)
FROM PUBLIC;

GRANT EXECUTE ON FUNCTION
  app.drain_security_notifications(integer),
  app.claim_queued_notifications(integer, integer),
  app.mark_notification_sent(uuid),
  app.mark_notification_failed(uuid, text),
  app.record_login_new_device(uuid, uuid, text, text, inet, text),
  app.enqueue_security_notification(text, uuid, uuid, jsonb),
  app.render_notification_body(text, jsonb),
  app.member_email(uuid),
  app.member_phone(uuid)
TO ajo_app;