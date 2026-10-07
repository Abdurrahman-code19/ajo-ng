/**
 * Reading Ajos: `GET /api/v1/ajos` and `GET /api/v1/ajos/:id`, spec 11.
 *
 * Separate from `ajos.ts` (which is creation) because the read path has the
 * opposite shape to the write path: one round trip, no domain rules, and the
 * authorisation already done by the database.
 *
 * That last point is the one worth stating. There is no membership check in this
 * file. `ajos_select` is
 *
 *     USING (organizer_user_id = app.request_user_id()
 *            OR app.is_ajo_member(id) OR app.is_platform_staff())
 *
 * so the query returns rows only where the caller is a member, and it returns
 * *nothing* otherwise. The service therefore answers "not a member" by reading
 * zero rows, which the route reports as 404 -- and 404 rather than 403 is the
 * honest code, because an Ajo that is invisible to you is, for your purposes,
 * one that does not exist. Answering 403 would confirm the id.
 *
 * A second reason for keeping the rule in the schema: a membership check in
 * TypeScript would have to be re-derived from `ajo_members` by hand, and would
 * drift from the policy the moment somebody adds an `is_platform_staff` branch
 * in one place and not the other.
 */
import type pg from 'pg';

import { frequencyFromCode, collectionDayFromCode, type AjoFrequency, type CollectionDay } from '@ajo/domain';

import { withIdentity, type Identity } from './db.js';

export class AjoNotFoundError extends Error {
  constructor() {
    super('that Ajo does not exist');
    this.name = 'AjoNotFoundError';
  }
}

/** One row of `GET /api/v1/ajos`. */
export interface AjoSummary {
  readonly id: string;
  readonly reference: string;
  readonly organizerUserId: string;
  readonly name: string;
  readonly status: string;
  readonly contributionKobo: number;
  readonly currency: string;
  readonly frequency: AjoFrequency | null;
  readonly collectionDay: CollectionDay | null;
  readonly totalRounds: number;
  readonly positionsTotal: number;
  readonly positionsFilled: number;
  readonly membersCount: number;
  readonly yourPosition: number | null;
  readonly yourRole: string | null;
  readonly enrollmentOpensAt: string | null;
  readonly enrollmentClosesAt: string | null;
  readonly currentRound: number;
}

export interface AjoListResponse {
  readonly data: readonly AjoSummary[];
  readonly page: { readonly nextCursor: null; readonly limit: number };
}

interface SummaryRow {
  id: string;
  reference: string;
  organizer_user_id: string;
  name: string;
  status: string;
  contribution_amount_kobo: string;
  currency: string;
  frequency_code: string | null;
  collection_day: string | null;
  total_rounds: number;
  position_count: number;
  positions_filled: number;
  members_count: number;
  your_position: number | null;
  your_role: string | null;
  enrollment_opens_at: Date | null;
  enrollment_closes_at: Date | null;
  current_round: number;
}

/**
 * The projection both endpoints share.
 *
 * `positions_filled` counts claimed *and* locked seats, because a locked seat is
 * still a filled one -- a ten-seat Ajo that activated has ten filled seats and
 * reporting nine would make the dashboard disagree with the lifecycle rail
 * sitting next to it.
 *
 * The organizer's own seat is included in that count: per CANONICAL §3 the
 * creator occupies one of the `position_count` positions, so a five-member Ajo
 * with four invitees is full.
 */
const SUMMARY_SELECT = `
  SELECT a.id,
         a.reference,
         a.organizer_user_id,
         a.name,
         a.status::text AS status,
         a.contribution_amount_kobo,
         a.currency::text AS currency,
         cf.code AS frequency_code,
         a.collection_day::text AS collection_day,
         a.total_rounds,
         a.position_count,
         (SELECT count(*)::int
            FROM public.ajo_positions p
           WHERE p.ajo_id = a.id
             AND p.status IN ('claimed', 'locked')
             AND p.deleted_at IS NULL) AS positions_filled,
         (SELECT count(*)::int
            FROM public.ajo_members m
           WHERE m.ajo_id = a.id
             AND m.deleted_at IS NULL) AS members_count,
         (SELECT p.position_number
            FROM public.ajo_members m
            JOIN public.ajo_positions p ON p.id = m.position_id
           WHERE m.ajo_id = a.id
             AND m.user_id = app.request_user_id()
             AND m.deleted_at IS NULL
             AND p.deleted_at IS NULL) AS your_position,
         -- Membership holds no role column: authority is a row in
         -- role_assignments (CANONICAL section 3: organizer authority is a
         -- role layered on top of membership). The organizer is still reported
         -- from organizer_user_id rather than from the grant, because that
         -- column is the one the activation audit trigger and the RLS policy
         -- both use; a missing ajo_organizer grant must not make the UI show
         -- the creator as a plain member of their own Ajo.
         (CASE WHEN a.organizer_user_id = app.request_user_id() THEN 'organizer'
               WHEN app.is_ajo_member(a.id) THEN 'member'
               ELSE NULL END)::text AS your_role,
         a.enrollment_opens_at,
         a.enrollment_closes_at,
         -- current_round is a state machine notion, not a column: the rounds
         -- themselves are created when the Ajo activates (E5-08), so anything
         -- not yet rotating reports 0 rather than inventing round 1.
         CASE
           WHEN a.status::text = 'round_in_progress' THEN a.rounds_completed + 1
           WHEN a.status::text IN ('active', 'completed') THEN GREATEST(a.rounds_completed, 1)
           ELSE 0
         END::int AS current_round
    FROM public.ajos a
    LEFT JOIN public.contribution_frequencies cf ON cf.id = a.frequency_id
   WHERE a.deleted_at IS NULL
     AND (a.organizer_user_id = app.request_user_id()
          OR app.is_ajo_member(a.id)
          OR app.is_platform_staff())`;

function toSummary(row: SummaryRow): AjoSummary {
  // Both vocabularies are read back rather than echoed, because a frequency code
  // the domain does not recognise is a data bug and a default here would hide it
  // behind a plausible-looking label.
  const frequency = row.frequency_code === null ? null : frequencyFromCode(row.frequency_code);
  if (row.frequency_code !== null && frequency === undefined) {
    throw new Error(`Ajo ${row.id} has an unrecognised frequency code: ${row.frequency_code}`);
  }
  const collectionDay =
    row.collection_day === null ? null : collectionDayFromCode(row.collection_day);
  if (row.collection_day !== null && collectionDay === undefined) {
    throw new Error(`Ajo ${row.id} has an unrecognised collection day: ${row.collection_day}`);
  }

  return {
    id: row.id,
    reference: row.reference,
    organizerUserId: row.organizer_user_id,
    name: row.name,
    status: row.status,
    contributionKobo: Number(row.contribution_amount_kobo),
    currency: row.currency.trim(),
    frequency: frequency ?? null,
    collectionDay: collectionDay ?? null,
    totalRounds: row.total_rounds,
    positionsTotal: row.position_count,
    positionsFilled: row.positions_filled,
    membersCount: row.members_count,
    yourPosition: row.your_position,
    yourRole: row.your_role,
    enrollmentOpensAt: row.enrollment_opens_at?.toISOString() ?? null,
    enrollmentClosesAt: row.enrollment_closes_at?.toISOString() ?? null,
    currentRound: row.current_round,
  };
}

/**
 * Ajos the caller belongs to.
 *
 * `status` is an optional filter on `ajos.status`; an unknown value filters to
 * nothing rather than being rejected, because the caller is choosing among
 * states that exist -- they simply chose a wrong one. The route refuses unknown
 * query keys regardless.
 *
 * Ordered by the lifecycle rather than by recency: an Ajo in `enrollment` with
 * a clock running is the one that needs a decision, so it sorts above a draft
 * that is doing nothing, which sorts above a completed rotation nobody has to
 * look at again. `cancelled` is last so a finished Ajo never displaces a live
 * one from the first screen.
 */
export async function listAjos(
  pool: pg.Pool,
  identity: Identity,
  status?: string,
): Promise<AjoListResponse> {
  return withIdentity(pool, identity, async (client) => {
    const rows = await client.query<SummaryRow>(
      `${SUMMARY_SELECT}
       ${status === undefined ? '' : 'AND a.status::text = $1'}
       ORDER BY (CASE a.status::text
                   WHEN 'enrollment' THEN 0
                   WHEN 'active' THEN 1
                   WHEN 'round_in_progress' THEN 2
                   WHEN 'draft' THEN 3
                   WHEN 'frozen' THEN 4
                   WHEN 'cancelling' THEN 5
                   WHEN 'cancelled' THEN 6
                   WHEN 'completed' THEN 7
                   ELSE 8
                 END),
                a.updated_at DESC`,
      status === undefined ? [] : [status],
    );
    return { data: rows.rows.map(toSummary), page: { nextCursor: null, limit: 50 } };
  });
}

/** Roster and seat board for one Ajo. */
export interface AjoSeat {
  readonly positionNumber: number;
  readonly status: string;
  readonly locked: boolean;
}

export interface AjoMember {
  readonly userId: string;
  readonly positionNumber: number | null;
  readonly status: string;
  readonly fullName: string;
  readonly joinedAt: string | null;
}

export interface AjoDetail {
  readonly ajo: AjoSummary;
  readonly positions: readonly AjoSeat[];
  readonly members: readonly AjoMember[];
}

/**
 * One Ajo, with its seat board and roster.
 *
 * Three statements rather than one join-out-to-everything query: positions and
 * members are both keyed on `ajo_id` and are small (5–20 rows), and the
 * independent counts they carry are read inside `SUMMARY_SELECT` anyway. A
 * lateral-everything query would be one round trip and considerably harder to
 * read, for a table that can never be wider than twenty rows.
 */
export async function getAjo(pool: pg.Pool, identity: Identity, ajoId: string): Promise<AjoDetail> {
  return withIdentity(pool, identity, async (client) => {
    const summary = await client.query<SummaryRow>(
      `${SUMMARY_SELECT} AND a.id = $1::uuid`,
      [ajoId],
    );
    const row = summary.rows[0];
    if (row === undefined) {
      throw new AjoNotFoundError();
    }

    const positions = await client.query<{
      position_number: number;
      status: string;
      locked_at: Date | null;
    }>(
      `SELECT position_number, status::text AS status, locked_at
         FROM public.ajo_positions
        WHERE ajo_id = $1::uuid
          AND deleted_at IS NULL
        ORDER BY position_number`,
      [ajoId],
    );

    const members = await client.query<{
      user_id: string;
      position_number: number | null;
      status: string;
      display_name: string;
      joined_at: Date | null;
    }>(
      `SELECT m.user_id,
              p.position_number,
              m.status::text AS status,
              COALESCE(pr.display_name, u.email::text) AS display_name,
              m.joined_at
         FROM public.ajo_members m
         LEFT JOIN public.ajo_positions p ON p.id = m.position_id AND p.deleted_at IS NULL
         LEFT JOIN public.users u ON u.id = m.user_id
         LEFT JOIN public.profiles pr ON pr.user_id = m.user_id
        WHERE m.ajo_id = $1::uuid
          AND m.deleted_at IS NULL
          AND m.status IN ('invited', 'active', 'defaulted')
        ORDER BY COALESCE(p.position_number, 9999), m.joined_at`,
      [ajoId],
    );

    return {
      ajo: toSummary(row),
      positions: positions.rows.map((position) => ({
        positionNumber: position.position_number,
        status: position.status,
        locked: position.locked_at !== null,
      })),
      members: members.rows.map((member) => ({
        userId: member.user_id,
        positionNumber: member.position_number,
        status: member.status,
        fullName: member.display_name,
        joinedAt: member.joined_at?.toISOString() ?? null,
      })),
    };
  });
}
