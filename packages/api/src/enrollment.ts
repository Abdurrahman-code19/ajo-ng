/**
 * Opening enrollment -- `POST /api/v1/ajos/:id/activate`, spec section 11.
 *
 * The endpoint name and the transition it performs do not match, and that is not
 * an oversight to be tidied away here. Per user-flows section 2.0.2 this endpoint
 * is `OPEN_ENROLLMENT`: DRAFT to ENROLLMENT. The ENROLLMENT to ACTIVE transition
 * is system-driven, fires on the fill event, and has no endpoint -- an endpoint
 * called "activate" that activated would let an organizer start a half-filled
 * rotation, which is the specific harm 2.0.2 was written to prevent. The name is
 * kept because the path is canonical; the function is named `openEnrollment`
 * because that is what it does.
 *
 * The rules live in `app.open_enrollment` (migration 113), not here. This file
 * only translates its refusals into the status codes section 11.5 names, in the
 * same shape `invitations.ts` uses, and reads the window back so the caller
 * learns the deadline they have just started rather than having to derive it.
 *
 * One divergence from the literal section 11 response, recorded deliberately:
 * 11.1 documents `{ confirm: true }` in and `{ ajo, positionsLocked, schedule }`
 * out, which describes the activation-to-ACTIVE reading. Under 2.0.2's reading
 * there is no schedule to return and no positions to lock -- they lock on the
 * fill -- so the response is the Ajo plus the window. Returning
 * `positionsLocked: true` here would be a lie about a roster that is still open.
 *
 * Also deliberate: no `reason` field, though 2.0.2 says this transition "requires
 * a recorded reason" and section 11.1's body is `{ confirm: true }` with no room
 * for one. The two spec sections disagree. `confirm: true` is honoured as the
 * spec's own body shape requires it, and the audit trigger already records who
 * opened enrollment and exactly when, so a free-text reason would collect strings
 * nobody reads on a transition that is not discretionary -- its guards decide it.
 */
import type pg from 'pg';

import { withIdentity, type Identity } from './db.js';
import { ValidationError } from './identity.js';

/** The raw JSON body. `unknown` on purpose: nothing here is trusted. */
export interface OpenEnrollmentInput {
  readonly confirm?: unknown;
}

/** 404: no such Ajo. 403: not the organizer. 409: it is not a draft. */
export class EnrollmentNotFoundError extends Error {
  constructor() {
    super('that Ajo does not exist');
    this.name = 'EnrollmentNotFoundError';
  }
}

export class EnrollmentNotAllowedError extends Error {
  constructor() {
    super('only the organizer of this Ajo may open enrollment');
    this.name = 'EnrollmentNotAllowedError';
  }
}

export class EnrollmentConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EnrollmentConflictError';
  }
}

export interface EnrollmentWindowResponse {
  readonly opensAt: string;
  readonly closesAt: string;
}

export interface OpenEnrollmentResult {
  readonly ajoId: string;
  readonly status: string;
  readonly enrollment: EnrollmentWindowResponse;
}

/**
 * `confirm` must be exactly `true`.
 *
 * Refusing a missing or false `confirm` rather than defaulting it is the point of
 * the field: it makes the caller state that opening enrollment starts a five-day
 * clock they cannot extend. Accepting a missing one would make the confirmation
 * decorative and the 409 that follows surprising -- the caller would be told the
 * Ajo was already enrolling in an enrollment they never asked for.
 *
 * The route schema already enforces this (`required: ['confirm']` plus
 * `const: true`), so through HTTP it is a 400 before any of this runs. This is
 * the same check one layer down, for a caller that is not the route -- and it
 * raises `ValidationError`, which is 422, because that is what an invalid value
 * already means everywhere else in this package. Were it a 409 instead, the same
 * body would be two different codes depending on who sent it.
 */
function assertConfirmed(input: OpenEnrollmentInput): void {
  if (input.confirm !== true) {
    throw new ValidationError('confirm', 'opening enrollment requires { "confirm": true }');
  }
}

export async function openEnrollment(
  pool: pg.Pool,
  identity: Identity,
  ajoId: string,
  input: OpenEnrollmentInput,
): Promise<OpenEnrollmentResult> {
  assertConfirmed(input);

  return withIdentity(pool, identity, async (client) => {
    try {
      // Two round trips, and the split is not a style choice. Reading the row in
      // the same statement as the call returns the pre-update status: one
      // command sees one snapshot, so the CTE's INSERT is invisible to the scan
      // of `ajos` beside it. `MATERIALIZED` is still required so the VOLATILE
      // function is not evaluated once per expanded column, and the second
      // query is what makes the response describe the state the database is
      // actually in rather than the state the caller's statement began with.
      const opened = await client.query<{ enrollment_opens_at: Date; enrollment_closes_at: Date }>(
        `WITH opened AS MATERIALIZED (
           SELECT * FROM app.open_enrollment($1::uuid) AS w
         )
         SELECT w.enrollment_opens_at, w.enrollment_closes_at
           FROM opened w`,
        [ajoId],
      );

      const window = opened.rows[0];
      if (window === undefined) {
        throw new Error('open_enrollment returned no row');
      }

      const stored = await client.query<{ id: string; status: string }>(
        `SELECT a.id, a.status::text AS status
           FROM public.ajos a
          WHERE a.id = $1::uuid`,
        [ajoId],
      );
      const row = stored.rows[0];
      if (row === undefined) {
        throw new Error(`Ajo ${ajoId} vanished after enrollment opened`);
      }

      return {
        ajoId: row.id,
        status: row.status,
        enrollment: {
          opensAt: window.enrollment_opens_at.toISOString(),
          closesAt: window.enrollment_closes_at.toISOString(),
        },
      };
    } catch (error) {
      translate(error);
    }
  });
}

function sqlState(error: unknown): string | undefined {
  if (error !== null && typeof error === 'object' && 'code' in error) {
    const { code } = error as { code?: unknown };
    if (typeof code === 'string') return code;
  }
  return undefined;
}

function messageOf(error: unknown): string {
  if (error !== null && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message);
  }
  return '';
}

/**
 * Map the function's refusals onto 404, 403 and 409.
 *
 * Matched on message as well as SQLSTATE, because `23514` carries four different
 * refusals from `app.open_enrollment` and "409" alone would tell an organizer
 * nothing about which rule stopped them. Anything unrecognised is rethrown rather
 * than given a guess: a refusal this function has never seen should be a 500 we
 * notice, not a 409 that quietly misdescribes the problem.
 */
function translate(error: unknown): never {
  switch (sqlState(error)) {
    case 'P0002':
      throw new EnrollmentNotFoundError();
    case '42501':
    case '28000':
      throw new EnrollmentNotAllowedError();
    case '23514': {
      const message = messageOf(error);
      if (message.includes('already open')) {
        throw new EnrollmentConflictError('enrollment is already open for this Ajo');
      }
      if (message.includes('window is closed')) {
        throw new EnrollmentConflictError(
          'this Ajo is no longer opening enrollment; its window is fixed',
        );
      }
      if (message.includes('not fully configured')) {
        throw new EnrollmentConflictError(
          'this Ajo is not fully configured yet; finish its rules before opening enrollment',
        );
      }
      throw new EnrollmentConflictError('this Ajo cannot open enrollment');
    }
    default:
      throw error;
  }
}