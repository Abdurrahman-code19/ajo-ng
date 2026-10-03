/**
 * Creating an Ajo -- `POST /api/v1/ajos`, spec section 11.
 *
 * The route is a thin adapter; the rules live in two places and this file is the
 * seam between them. Configuration rules (`contribution`, `frequency`,
 * `collectionDay`, size) live in `@ajo/domain`, because the frontend and any
 * future client must be able to state them without a database. The write itself
 * lives in `app.create_ajo`, because it is one transaction whose pieces the
 * schema will not let be separated -- see migration 110.
 *
 * What is deliberately *not* here: the `409 duplicate active Ajo`. The spec
 * lists it, but neither the schema nor the product has a rule that defines
 * "duplicate" -- the per-organizer cap is the still-open decision D-08, and
 * inventing a name-collision rule now would turn an unwritten product decision
 * into an API contract nobody agreed to. It is recorded rather than guessed.
 */
import type pg from 'pg';
import {
  AjoRuleError,
  assertValidContributionAmount,
  assertValidMemberCount,
  collectionDayCode,
  collectionDayFromCode,
  frequencyCode,
  frequencyFromCode,
  isAjoFrequency,
  isCollectionDay,
  kobo,
  type AjoFrequency,
  type CollectionDay,
} from '@ajo/domain';

import { withIdentity, type Identity } from './db.js';
import { ValidationError } from './identity.js';

/** The raw JSON body, before validation. Every field is unknown on purpose. */
export interface CreateAjoInput {
  readonly name?: unknown;
  readonly description?: unknown;
  readonly contributionKobo?: unknown;
  readonly currency?: unknown;
  readonly frequency?: unknown;
  readonly collectionDay?: unknown;
  readonly durationRounds?: unknown;
  readonly maxMembers?: unknown;
  readonly startDate?: unknown;
}

/** The validated configuration `app.create_ajo` is called with. */
interface ValidatedAjo {
  readonly name: string;
  readonly description: string | null;
  readonly contributionKobo: number;
  readonly frequency: AjoFrequency;
  readonly collectionDay: CollectionDay;
  readonly members: number;
  readonly startDate: string;
}

/**
 * The caller authenticated but is not allowed to create an Ajo.
 *
 * The spec's precondition is "Member, email-verified"; a member who has not
 * verified their email is a real account that simply may not do this yet, which
 * is 403 and not 401 -- they are authenticated, just not permitted.
 */
export class AjoNotAllowedError extends Error {
  constructor() {
    super('your email address must be verified before you can create an Ajo');
    this.name = 'AjoNotAllowedError';
  }
}

export interface AjoResponse {
  readonly id: string;
  readonly reference: string;
  readonly name: string;
  readonly description: string | null;
  readonly status: string;
  readonly currency: string;
  readonly contributionKobo: number;
  readonly frequency: AjoFrequency;
  readonly collectionDay: CollectionDay | null;
  readonly durationRounds: number;
  readonly maxMembers: number;
  readonly startDate: string | null;
  readonly organizerUserId: string;
  readonly createdAt: string;
}

export interface PositionResponse {
  readonly positionNumber: number;
  readonly status: string;
}

export interface CreateAjoResult {
  readonly ajo: AjoResponse;
  readonly positions: readonly PositionResponse[];
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Validate the create body, or throw the first `ValidationError`.
 *
 * Returned rather than mutating the input, so the route never sees a partially
 * normalised object: either every field is the shape the write needs, or the
 * call failed and nothing was sent.
 */
export function validateCreateAjo(input: CreateAjoInput): ValidatedAjo {
  const name = typeof input.name === 'string' ? input.name.trim() : '';
  if (name.length < 3 || name.length > 80) {
    throw new ValidationError('name', 'an Ajo name must be 3 to 80 characters');
  }

  if (input.currency !== 'NGN') {
    throw new ValidationError('currency', 'the only supported currency is NGN');
  }

  if (!isAjoFrequency(input.frequency)) {
    throw new ValidationError('frequency', 'frequency must be WEEKLY, BIWEEKLY or MONTHLY');
  }

  if (!isCollectionDay(input.collectionDay)) {
    throw new ValidationError(
      'collectionDay',
      'collectionDay must be a weekday name, e.g. FRIDAY',
    );
  }

  const maxMembers = input.maxMembers;
  const durationRounds = input.durationRounds;
  if (
    typeof maxMembers !== 'number' ||
    !Number.isSafeInteger(maxMembers) ||
    typeof durationRounds !== 'number' ||
    !Number.isSafeInteger(durationRounds)
  ) {
    throw new ValidationError('maxMembers', 'maxMembers and durationRounds must be whole numbers');
  }
  // Rounds equal members: one round pays exactly one member, so a group of ten
  // runs ten rounds. Two independent fields that must agree is a redundancy the
  // API inherits from the spec; the disagreement is rejected rather than
  // silently resolved in either direction.
  if (durationRounds !== maxMembers) {
    throw new ValidationError(
      'durationRounds',
      'durationRounds must equal maxMembers: each round pays one member',
    );
  }
  try {
    assertValidMemberCount(maxMembers);
  } catch (error) {
    throw new ValidationError('maxMembers', ruleMessage(error));
  }

  if (
    typeof input.contributionKobo !== 'number' ||
    !Number.isSafeInteger(input.contributionKobo) ||
    input.contributionKobo < 0
  ) {
    throw new ValidationError('contributionKobo', 'contributionKobo must be a whole number of kobo');
  }
  try {
    assertValidContributionAmount(kobo(input.contributionKobo), maxMembers);
  } catch (error) {
    throw new ValidationError('contributionKobo', ruleMessage(error));
  }

  const startDate = typeof input.startDate === 'string' ? input.startDate.trim() : '';
  if (!ISO_DATE.test(startDate) || Number.isNaN(Date.parse(`${startDate}T00:00:00Z`))) {
    throw new ValidationError('startDate', 'startDate must be an ISO date (YYYY-MM-DD)');
  }

  const description = input.description === undefined ? null : String(input.description).trim();
  if (description !== null && description.length > 2000) {
    throw new ValidationError('description', 'a description may not exceed 2000 characters');
  }

  return {
    name,
    description: description === '' ? null : description,
    contributionKobo: input.contributionKobo,
    frequency: input.frequency,
    collectionDay: input.collectionDay,
    members: maxMembers,
    startDate,
  };
}

function ruleMessage(error: unknown): string {
  if (error instanceof AjoRuleError) {
    return error.message;
  }
  throw error;
}

interface AjoRow {
  id: string;
  reference: string;
  name: string;
  description: string | null;
  status: string;
  organizer_user_id: string;
  currency: string;
  contribution_amount_kobo: string;
  position_count: number;
  total_rounds: number;
  collection_day: string | null;
  start_date: Date | null;
  created_at: Date;
  frequency_code: string;
}

interface PositionRow {
  position_number: number;
  status: string;
}

export async function createAjo(
  pool: pg.Pool,
  identity: Identity,
  input: CreateAjoInput,
): Promise<CreateAjoResult> {
  const config = validateCreateAjo(input);

  return withIdentity(pool, identity, async (client) => {
    // The precondition, read under the caller's own identity so the row policy
    // applies. Doing this here rather than catching the SQLSTATE the function
    // raises gives the caller a specific 403 instead of a generic failure, and
    // keeps "not verified" distinguishable from "database said no".
    const gate = await client.query<{ is_email_verified: boolean; status: string }>(
      `SELECT is_email_verified, status::text AS status
         FROM public.users
        WHERE id = $1::uuid
          AND deleted_at IS NULL`,
      [identity.userId],
    );
    const me = gate.rows[0];
    if (me === undefined || !me.is_email_verified || me.status !== 'active') {
      throw new AjoNotAllowedError();
    }

    const created = await client.query<AjoRow>(
      // `(function(...)).*` expands the returned composite into the columns of
      // the row, so the response is built from what was actually written rather
      // than from the input echoed back. The join pulls the cadence's own code
      // back for the response; `create_ajo` returns the Ajo row, not the code.
      `SELECT a.*, cf.code AS frequency_code
         FROM (SELECT (app.create_ajo($1, $2, $3, $4, $5, $6, $7, $8)).*) AS a
         JOIN public.contribution_frequencies cf ON cf.id = a.frequency_id`,
      [
        config.name,
        config.description,
        config.contributionKobo,
        'NGN',
        frequencyCode(config.frequency),
        config.members,
        collectionDayCode(config.collectionDay),
        config.startDate,
      ],
    );

    const row = created.rows[0];
    if (row === undefined) {
      // The function returns a row or raises; a nil row here would mean the
      // INSERT silently dropped, which nothing in the schema permits.
      throw new Error('create_ajo returned no row');
    }

    const positions = await client.query<PositionRow>(
      `SELECT position_number, status::text AS status
         FROM public.ajo_positions
        WHERE ajo_id = $1::uuid
          AND deleted_at IS NULL
        ORDER BY position_number`,
      [row.id],
    );

    return { ajo: toAjoResponse(row), positions: positions.rows.map(toPositionResponse) };
  });
}

function toAjoResponse(row: AjoRow): AjoResponse {
  // The cadence and the day are read back out of the row rather than echoed
  // from the request, so an unrecognised value is a bug and not a value the
  // response should paper over with a default.
  const frequency = frequencyFromCode(row.frequency_code);
  if (frequency === undefined) {
    throw new Error(`Ajo ${row.id} has an unrecognised frequency code: ${row.frequency_code}`);
  }
  const collectionDay = row.collection_day === null ? null : collectionDayFromCode(row.collection_day);
  if (row.collection_day !== null && collectionDay === undefined) {
    throw new Error(`Ajo ${row.id} has an unrecognised collection day: ${row.collection_day}`);
  }

  return {
    id: row.id,
    reference: row.reference,
    name: row.name,
    description: row.description,
    status: row.status,
    currency: row.currency.trim(),
    contributionKobo: Number(row.contribution_amount_kobo),
    frequency,
    collectionDay: collectionDay ?? null,
    durationRounds: row.total_rounds,
    maxMembers: row.position_count,
    startDate: row.start_date === null ? null : toIsoDate(row.start_date),
    organizerUserId: row.organizer_user_id,
    createdAt: row.created_at.toISOString(),
  };
}

/**
 * A `date` column is a calendar day with no time zone.
 *
 * `pg` parses it into a `Date` at local midnight, so `toISOString()` -- which
 * converts to UTC first -- can name the previous day in any zone west of UTC.
 * Reading the local components back returns the day the database actually
 * stored, wherever the process runs.
 */
function toIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function toPositionResponse(row: PositionRow): PositionResponse {
  return { positionNumber: row.position_number, status: row.status };
}
