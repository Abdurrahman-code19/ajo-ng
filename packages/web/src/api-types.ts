/** API response types, mirrored from the canvas service responses. */

export type AjoStatus =
  | 'draft'
  | 'enrollment'
  | 'active'
  | 'round_in_progress'
  | 'completed'
  | 'cancelled'
  | 'cancelling'
  | 'frozen';

export type AjoFrequency = 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY';
export type CollectionDay =
  | 'MONDAY'
  | 'TUESDAY'
  | 'WEDNESDAY'
  | 'THURSDAY'
  | 'FRIDAY'
  | 'SATURDAY'
  | 'SUNDAY';

export interface AjoSummary {
  id: string;
  reference: string;
  organizerUserId: string;
  name: string;
  status: AjoStatus;
  contributionKobo: number;
  currency: string;
  frequency: AjoFrequency | null;
  collectionDay: CollectionDay | null;
  totalRounds: number;
  positionsTotal: number;
  positionsFilled: number;
  membersCount: number;
  yourPosition: number | null;
  yourRole: 'organizer' | 'member' | null;
  enrollmentOpensAt: string | null;
  enrollmentClosesAt: string | null;
  currentRound: number;
}

export interface AjoSeat {
  positionNumber: number;
  status: 'open' | 'claimed' | 'locked' | 'released';
  locked: boolean;
}

export interface AjoMember {
  userId: string;
  positionNumber: number | null;
  status: string;
  fullName: string;
  joinedAt: string | null;
}

export interface AjoDetail {
  ajo: AjoSummary;
  positions: AjoSeat[];
  members: AjoMember[];
}

export interface InvitationSummary {
  id: string;
  status: string;
  email: string;
  expiresAt: string;
  createdAt: string;
}

export interface EnrollmentOpenResult {
  ajoId: string;
  status: 'enrollment';
  enrollment: { opensAt: string; closesAt: string };
}

export interface PosetRow {
  id: string;
  positionNumber: number;
  status: string;
}

export interface CreateAjoResult {
  ajo: {
    id: string;
    reference: string;
    name: string;
    status: string;
    contributionKobo: number;
    currency: string;
    frequency: AjoFrequency;
    collectionDay: CollectionDay;
    durationRounds: number;
    maxMembers: number;
    startDate: string;
    organizerUserId: string;
  };
  positions: PosetRow[];
}

export interface MeResponse {
  userId: string;
  email: string;
  phoneE164: string | null;
  status: string;
  isEmailVerified: boolean;
  isPhoneVerified: boolean;
  displayName: string | null;
  preferredLocale: string | null;
  createdAt: string;
  lastLoginAt: string | null;
}

export interface AjoPreview {
  id: string;
  name: string;
  status: string;
  contributionKobo: number;
  currency: string;
  frequencyCode: string;
  collectionDay: string | null;
  durationRounds: number;
  maxMembers: number;
  membersCount: number;
  endsAt: string | null;
}

export interface FeeDisclosure {
  contributionKobo: number;
  feeKobo: number;
  totalChargeKobo: number;
}

export interface AjoRule {
  code: string;
  text: string;
}

export interface AjoRules {
  version: number;
  clauses: readonly AjoRule[];
}

export interface InvitationPreview {
  ajo: AjoPreview;
  organizer: { name: string };
  positionOptions: readonly number[];
  feeDisclosure: FeeDisclosure;
  rules: AjoRules;
}

export interface AcceptInvitationResult {
  accepted: true;
  ajoId: string;
  positionNumber: number;
  rulesVersion: number;
}