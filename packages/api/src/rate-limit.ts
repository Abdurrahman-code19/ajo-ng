/**
 * The rate limit in front of registration, and the interface the route depends
 * on rather than on ioredis.
 *
 * The interface exists so the route can be tested without a Redis server, and so
 * the limiter can be swapped for a different backing store without touching the
 * handler. The implementation is a fixed window, which is the weakest of the
 * three common designs: a client can send `limit` requests at the end of one
 * window and `limit` at the start of the next, so the effective ceiling is
 * double. That is acceptable here because what is being protected is a signup
 * endpoint with a known cost, and a sliding window or token bucket would be
 * strictly better at the cost of a Lua script and a sorted set.
 *
 * What it is *not* acceptable for is being the only thing between the endpoint
 * and an unbounded write path into `users` -- which is what it is, and which is
 * stated at the call site rather than left to be discovered.
 */
import { Redis } from 'ioredis';

export interface RateLimiter {
  /** Resolves false when the attempt is over the limit. */
  consume(key: string): Promise<boolean>;
  /**
   * Whether the backing store is reachable, without consuming an attempt.
   *
   * Readiness needs this, and it needs it to be honest: a limiter that has lost
   * Redis is not a limiter. The tempting implementation is to catch the error
   * and allow the request, but the route's limit is the only thing bounding the
   * signup write path, so "Redis is down" must mean "stop accepting
   * registrations", not "accept them all".
   */
  ping(): Promise<boolean>;
  close(): Promise<void>;
}

export interface FixedWindowOptions {
  readonly url: string;
  readonly limit: number;
  readonly windowMs: number;
  /** Injectable so a test can assert the key derivation without Redis. */
  readonly now?: () => number;
}

export function createFixedWindowLimiter(options: FixedWindowOptions): RateLimiter {
  const now = options.now ?? Date.now;
  const redis = new Redis(options.url, { maxRetriesPerRequest: 2 });

  return {
    async consume(key: string): Promise<boolean> {
      const window = Math.floor(now() / options.windowMs);
      // The window number is in the key, so counters expire on their own instead
      // of needing a sweep. The TTL is two windows so a counter cannot expire
      // between the INCR and the reply that decides whether the caller is let
      // through.
      const redisKey = `ajo:ratelimit:registration:${key}:${window}`;
      const count = await redis.incr(redisKey);
      if (count === 1) {
        await redis.expire(redisKey, Math.ceil(options.windowMs / 1000) * 2);
      }
      return count <= options.limit;
    },
    async ping(): Promise<boolean> {
      try {
        return (await redis.ping()) === 'PONG';
      } catch {
        return false;
      }
    },
    async close(): Promise<void> {
      await redis.quit();
    },
  };
}

/** A limiter that allows everything. For tests, and only for tests. */
export function allowAllLimiter(): RateLimiter {
  return {
    async consume(): Promise<boolean> {
      return true;
    },
    async ping(): Promise<boolean> {
      return true;
    },
    async close(): Promise<void> {
      /* nothing to close */
    },
  };
}
