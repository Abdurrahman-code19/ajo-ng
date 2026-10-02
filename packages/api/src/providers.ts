/**
 * Turning configured secrets into adapters.
 *
 * The one rule worth stating: an adapter exists if and only if its secret was
 * configured. There is no separate list of "enabled providers", because two
 * lists drift -- a provider added to one and not the other mounts an endpoint
 * that cannot verify anything, and a provider removed from one leaves an
 * adapter nobody uses.
 */
import {
  MockFinancialProvider,
  type FinancialProvider,
  type ProviderId,
} from '@ajo/domain';

export type ProviderResolver = (id: string) => FinancialProvider | undefined;

export interface ProviderRegistryOptions {
  /** Provider id to HMAC secret. Absent means the provider is not switched on. */
  readonly secrets: Readonly<Record<string, string>>;
}

/**
 * Builds the adapters this process will serve webhooks for.
 *
 * Only `mock` is constructed. `providus_unity` has an entry in the configuration
 * map so an operator who has a secret gets a clear "no adapter yet" at boot
 * rather than a silently missing endpoint -- but there is nothing honest to
 * build until `E3-01` lands the provider's signing format, so it throws.
 *
 * That throw is the point. The alternative is a ProvidusUnity adapter that
 * guesses at HMAC and would reject every real callback in production, which is a
 * failure nobody would find until a paying member's contribution silently never
 * settled.
 */
export function createProviderRegistry(
  options: ProviderRegistryOptions,
): {
  readonly providers: ReadonlyMap<ProviderId, FinancialProvider>;
  readonly resolve: ProviderResolver;
} {
  const providers = new Map<ProviderId, FinancialProvider>();

  for (const [id, secret] of Object.entries(options.secrets)) {
    switch (id) {
      case 'mock':
        providers.set('mock', new MockFinancialProvider({ secret }));
        break;
      case 'providus_unity':
        throw new Error(
          'PROVIDUSUNITY_WEBHOOK_SECRET is set but there is no ProvidusUnity adapter. ' +
            'The provider signing format is documented in E3-01; building one that ' +
            'guesses would reject every real callback.',
        );
      default:
        throw new Error(
          `webhook secret configured for unknown provider ${JSON.stringify(id)}`,
        );
    }
  }

  return {
    providers,
    resolve: (id: string) => providers.get(id as ProviderId),
  };
}