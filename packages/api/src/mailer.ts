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
