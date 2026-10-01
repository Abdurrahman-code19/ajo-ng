/**
 * A UUIDv7, generated here rather than by the database.
 *
 * The reason is ordering, not variety. Every table's primary key defaults to
 * `app.uuidv7()` because a time-ordered key inserts near the end of the index
 * instead of scattering across it. Registration is the one write that cannot use
 * the default, because the row's id has to exist *before* the insert -- the
 * `users_insert_own` policy checks the new row's id against `app.user_id`, and
 * the transaction's identity is that same id. So the API has to be able to
 * produce one itself, and a v4 would work functionally while quietly undoing the
 * index behaviour for the largest table in the schema.
 *
 * Layout, per RFC 9562: 48 bits of Unix milliseconds, then 4 bits of version,
 * 12 bits of sub-millisecond counter to fill the remaining randomness, 2 bits
 * of variant, and 62 random bits.
 */
import { randomFillSync } from 'node:crypto';

export function uuidv7(now: number = Date.now()): string {
  const bytes = randomFillSync(new Uint8Array(16));

  // 48-bit timestamp. A number beyond 2^48 ms is the year 10889, so masking is
  // defensive rather than meaningful, and it keeps this a total function.
  const ms = BigInt(now) & 0xffff_ffff_ffffn;
  bytes[0] = Number((ms >> 40n) & 0xffn);
  bytes[1] = Number((ms >> 32n) & 0xffn);
  bytes[2] = Number((ms >> 24n) & 0xffn);
  bytes[3] = Number((ms >> 16n) & 0xffn);
  bytes[4] = Number((ms >> 8n) & 0xffn);
  bytes[5] = Number(ms & 0xffn);

  // Version 7, and the 12 bits after it stay random. RFC 9562 allows a
  // sub-millisecond counter there to keep keys minted inside the same
  // millisecond in creation order; it is deliberately not used, because
  // monotonic ordering across two processes sharing a database would need
  // shared state, and a UUID is not a sequence. Ordering is only claimed within
  // a millisecond, which is what an index benefits from.
  bytes[6] = 0x70 | ((bytes[6] ?? 0) & 0x0f);

  // Variant 1: the two high bits of byte 8 are fixed to `10`. `0xbf & 0x3f` is
  // the mask, not the value -- a mask is what *keeps* the two high bits of
  // `bytes[8]`, and those bits are exactly the variant. Masking to 0x3f, or
  // assigning 0xbf directly, sets both high bits to 1 and produces a v4-shaped
  // UUID, which still parses as a UUID and would have passed any test that only
  // checked the format.
  bytes[8] = 0xbf & ((bytes[8] ?? 0) | 0xc0);

  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    hex.slice(12, 16),
    hex.slice(16, 20),
    hex.slice(20, 32),
  ].join('-');
}
