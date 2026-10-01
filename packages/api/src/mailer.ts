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
 * `createLoggingSender` writes the token to the log, which is appropriate for
 * local development and for nothing else. It says so on the object, so the
 * mistake is visible at the point it is made rather than discovered later.
 */
export interface VerificationSender {
  sendVerificationToken(message: {
    readonly to: string;
    readonly userId: string;
    readonly token: string;
  }): Promise<void>;
}

/** Development only. The token lands in the log so a test or a human can use it. */
export function createLoggingSender(
  log: { info: (fields: object, message: string) => void },
): VerificationSender {
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

/**
 * The sender the composition root picks.
 *
 * There is no production transport yet, and this function is the guard that says
 * so rather than a stub that would pretend otherwise. In production it throws and
 * the process refuses to start: the logging sender writes the plaintext
 * verification token to stdout, and a working signup flow that also publishes
 * every token to the logs is worse than an API that will not boot, because it
 * fails silently in the direction that hands over accounts. Failing at startup is
 * the same choice `loadConfig` makes about a missing credential.
 *
 * A real implementation replaces the throw with a new `VerificationSender` (an
 * SMTP client, a provider SDK), and `createLoggingSender` stays for development.
 * The parameter is the environment string rather than a boolean so the caller
 * does not have to decide what counts as production; `NODE_ENV` is the single
 * source, read in `config.ts` like everything else.
 */
export function createVerificationSender(
  environment: string,
  log: { info: (fields: object, message: string) => void },
): VerificationSender {
  if (environment === 'production') {
    throw new Error(
      'No email transport is configured. The development sender writes the ' +
        'plaintext verification token to stdout, which must not happen in ' +
        'production. Implement VerificationSender against the chosen provider ' +
        'and wire it in createVerificationSender before deploying.',
    );
  }
  return createLoggingSender(log);
}
