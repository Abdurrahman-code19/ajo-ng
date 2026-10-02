/**
 * Where the verification token goes.
 *
 * An interface, not a provider, because the token's whole security value is in
 * not being in the HTTP response and in not being in a log line -- and that is a
 * property of *every* call site, not one. With a provider named here, a future
 * Postmark implementation is a new file plus a line in `index.ts`, and there is
 * exactly one place in the codebase that is allowed to hold a plaintext token
 * for longer than the request that minted it.
 *
 * Two implementations exist, and only one of them is allowed near production:
 *
 *   * `createLoggingSender` writes the token to the log. Development only.
 *   * `createHttpRelaySender` posts it to an HTTP relay over a bearer token.
 *
 * The relay is deliberately not a named vendor. Every hosted mail provider has a
 * different payload, an SDK, and a rate-limit policy, and picking one here would
 * put that choice in a file that has no business making it. What is fixed is the
 * part that matters and does not vary: one authenticated HTTP POST carrying the
 * recipient and the token, with a timeout, and an error that never quotes the
 * token. A provider adapter is a thin function over that.
 */
export interface VerificationSender {
  sendVerificationToken(message: {
    readonly to: string;
    readonly userId: string;
    readonly token: string;
  }): Promise<void>;
}

export interface MailLog {
  info(fields: object, message: string): void;
}

/** Development only. The token lands in the log so a test or a human can use it. */
export function createLoggingSender(log: MailLog): VerificationSender {
  return {
    async sendVerificationToken(message): Promise<void> {
      log.info(
        {
          to: message.to,
          userId: message.userId,
          verificationToken: message.token,
        },
        'DEVELOPMENT: verification token; never log this outside local development',
      );
    },
  };
}

/** How to reach the relay. From the environment; never defaulted. */
export interface MailRelayConfig {
  readonly url: string;
  readonly token: string;
  readonly from: string;
}

const SUBJECT = 'Confirm your email address for Ajo';

function verificationBody(token: string, userId: string): string {
  // The token is in the body, not the subject and not a URL query string, so it
  // does not end up in a provider's logs, a mailbox list view, or a referrer.
  return [
    'Confirm your email address',
    '',
    `Account: ${userId}`,
    `Token: ${token}`,
    '',
    'To activate your account, send this token to the endpoint below:',
    '',
    '  POST /api/v1/auth/verify-email',
    '  { "token": "<the token above>" }',
    '',
    'The token can be used once and expires in 24 hours.',
    '',
    'If you did not create this account, ignore this message.',
  ].join('\n');
}

/**
 * The production transport.
 *
 * Failures throw. The caller is the registration route, which turns an exception
 * into a 500 and a log line, and the message here is the HTTP status only -- the
 * token must not reach an error string, because error strings end up in logs and
 * in some error trackers.
 */
export function createHttpRelaySender(relay: MailRelayConfig): VerificationSender {
  return {
    async sendVerificationToken(message): Promise<void> {
      const response = await fetch(relay.url, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          authorization: `Bearer ${relay.token}`,
        },
        body: JSON.stringify({
          from: relay.from,
          to: message.to,
          subject: SUBJECT,
          text: verificationBody(message.token, message.userId),
        }),
        // Without a timeout a stalled relay holds the registration request open
        // until the client gives up, which turns one slow dependency into an
        // exhausted connection pool.
        signal: AbortSignal.timeout(10_000),
      });

      if (!response.ok) {
        throw new Error(
          `the mail relay rejected the verification message (HTTP ${response.status})`,
        );
      }
    },
  };
}

/**
 * A raw transactional message, with no verification token in it.
 *
 * Separate from `VerificationSender` rather than a parameter on it because the two
 * have opposite safety properties. A verification message carries a secret, so it
 * is written to put the token in the body and never in a URL, never in a subject
 * line, and never in an error. A security notification carries no secret and is
 * the opposite: it is a warning about a compromised account, and it should be as
 * loud and as clear as the format allows. One interface cannot be right for both,
 * and folding them together would either weaken the token handling or water down
 * the alarm.
 */
export interface NotificationTransport {
  sendEmail(message: {
    readonly to: string;
    readonly subject: string;
    readonly body: string;
  }): Promise<void>;
}

/**
 * The production transport for notifications.
 *
 * The same relay, the same authentication, the same timeout -- only the payload
 * differs. Two send paths over one relay rather than one send path with a nullable
 * token field, because the failure mode of sharing it is a template that forgets
 * to interpolate something and sends a member a body with a raw `{{token}}` in
 * it, which is exactly the sort of message that makes people stop reading alerts.
 */
export function createHttpRelayTransport(relay: MailRelayConfig): NotificationTransport {
  return {
    async sendEmail(message): Promise<void> {
      const response = await fetch(relay.url, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          authorization: `Bearer ${relay.token}`,
        },
        body: JSON.stringify({
          from: relay.from,
          to: message.to,
          subject: message.subject,
          text: message.body,
        }),
        // Same reasoning as `createHttpRelaySender`: a stalled relay must not hold
        // a worker pass open until the process gives up. This is longer than the
        // verification send's 10s because a notification body is longer and the
        // relay may be doing provider work, but it is still bounded.
        signal: AbortSignal.timeout(15_000),
      });

      if (!response.ok) {
        // The status only, never the body. A relay's error response can echo the
        // recipient address back, and this string reaches `failure_detail`, which
        // is read by anyone debugging the queue.
        throw new Error(`the mail relay rejected the message (HTTP ${response.status})`);
      }
    },
  };
}

/** Development only. The message lands in the log so a test or a human can read it. */
export function createLoggingTransport(log: MailLog): NotificationTransport {
  return {
    async sendEmail(message): Promise<void> {
      log.info(
        { to: message.to, subject: message.subject, body: message.body },
        'DEVELOPMENT: security notification; never log this outside local development',
      );
    },
  };
}

/**
 * The notification transport the composition root picks.
 *
 * Same rule as `createVerificationSender`, and for the same reason: in production
 * with no relay, this throws rather than returning the logging transport. A process
 * that will not start is much better than one that starts and logs every
 * compromise alarm to stdout, where it lands in a log aggregator and is read by
 * nobody who was told to act on it.
 */
export function createNotificationTransport(
  environment: string,
  log: MailLog,
  relay?: MailRelayConfig,
): NotificationTransport {
  if (environment !== 'production') {
    return createLoggingTransport(log);
  }

  if (relay === undefined) {
    throw new Error(
      'No mail transport is configured. Set MAIL_RELAY_URL, MAIL_RELAY_TOKEN ' +
        'and MAIL_FROM. The development transport writes every security ' +
        'notification to stdout, so this process will not start without a relay.',
    );
  }

  return createHttpRelayTransport(relay);
}

/**
 * The sender the composition root picks.
 *
 * In production this returns the relay, and throws if no relay is configured.
 * Throwing is the point: the alternative is the logging sender, which publishes
 * every verification link to stdout. A process that will not start is a much
 * better outcome than one that starts and hands over accounts, and it is the
 * same choice `loadConfig` makes about a missing credential.
 *
 * `relay` is passed in rather than read from the environment so that "is this
 * production" and "is there a transport" are both decided in `config.ts` and
 * nowhere else.
 */
export function createVerificationSender(
  environment: string,
  log: MailLog,
  relay?: MailRelayConfig,
): VerificationSender {
  if (environment !== 'production') {
    return createLoggingSender(log);
  }

  if (relay === undefined) {
    throw new Error(
      'No mail transport is configured. Set MAIL_RELAY_URL, MAIL_RELAY_TOKEN ' +
        'and MAIL_FROM. The development sender writes the plaintext ' +
        'verification token to stdout, which must not happen in production, so ' +
        'this process will not start without a relay.',
    );
  }

  return createHttpRelaySender(relay);
}
