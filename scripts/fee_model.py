"""
AJO.ng revenue model — 2% platform fee charged on every contribution deposit.

Fee mechanic (per founder direction):
  - A member owing a ₦1,000 contribution deposits ₦1,020.
  - ₦1,000 is the member's contribution to the round pool.
  - ₦20 (2%) is AJO.ng's platform fee.
  - The member whose turn it is receives the BASE pool: 10 x ₦1,000 = ₦10,000.

All money below is integer kobo. No floats.

Run: python3 scripts/fee_model.py
"""

from __future__ import annotations

# ---------------------------------------------------------------- platform fee
FEE_BPS = 200  # 2.00% expressed in basis points (200 bps = 2%)
FEE_LABEL = "2%"


def kobo(naira_amount: int) -> int:
    return naira_amount * 100


def fee_on(amount_kobo: int) -> int:
    """Platform fee for one deposit. Rounds half-up, documented in the PRD."""
    return (amount_kobo * FEE_BPS + 5_000) // 10_000


def total_charge(contribution_kobo: int) -> int:
    """What the member is actually debited."""
    return contribution_kobo + fee_on(contribution_kobo)


# ------------------------------------------------------------------ scenarios
# Figures below mirror AJOng_Year_1_Financial_Model_UPDATED.xlsx exactly.
SCENARIOS = [
    {"name": "Conservative", "ajos": 150, "members": 8, "contribution": 7_500, "rounds": 10},
    {"name": "Base Case", "ajos": 300, "members": 10, "contribution": 10_000, "rounds": 10},
    {"name": "Growth Case", "ajos": 600, "members": 12, "contribution": 12_000, "rounds": 10},
]


def scenario_rows() -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for s in SCENARIOS:
        deposits = s["ajos"] * s["members"] * s["rounds"]
        volume = s["ajos"] * s["members"] * s["contribution"] * s["rounds"]
        fee = sum(fee_on(kobo(s["contribution"])) for _ in range(deposits))
        rows.append(
            {
                "scenario": s["name"],
                "ajos": s["ajos"],
                "members": s["members"],
                "contribution": s["contribution"],
                "rounds": s["rounds"],
                "deposits": deposits,
                "volume": volume,
                "fee_revenue": fee // 100,  # convert kobo -> naira
                "fee_per_ajo": fee // 100 // s["ajos"],
            }
        )
    return rows


def worked_example() -> list[tuple[str, str]]:
    contribution = kobo(1_000)
    fee = fee_on(contribution)
    members, rounds = 10, 10
    base_pool = contribution * members
    collected = total_charge(contribution) * members

    return [
        ("Members in the Ajo", str(members)),
        ("Contribution per member per round", f"NGN {contribution // 100:,}.00"),
        ("Platform fee (2%)", f"NGN {fee // 100}.00"),
        ("Total charged per member", f"NGN {total_charge(contribution) // 100:,}.00"),
        ("Base pool paid to recipient", f"NGN {base_pool // 100:,}.00"),
        ("Total actually collected in the round", f"NGN {collected // 100:,}.00"),
        ("Platform fee retained in the round", f"NGN {(collected - base_pool) // 100}.00"),
        ("Rounds in the Ajo", str(rounds)),
        ("Total contributed per member over the Ajo", f"NGN {total_charge(contribution) // 100 * rounds:,}.00"),
        ("Total received by recipient at their turn", f"NGN {base_pool // 100:,}.00"),
        ("Platform fee over the full Ajo", f"NGN {(collected - base_pool) * rounds // 100:,}.00"),
        ("Total collected across the Ajo", f"NGN {collected // 100 * rounds:,}.00"),
    ]


def fee_sensitivity() -> list[tuple[int, int, int, int]]:
    """(contribution naira, fee naira, total charged, % of total)."""
    out = []
    for amount in (300, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000):
        c = kobo(amount)
        f = fee_on(c)
        t = total_charge(c)
        pct = (f / t * 10000) / 100
        out.append((amount, f // 100, t // 100, pct))
    return out


if __name__ == "__main__":
    print("=" * 78)
    print("AJO.ng — PLATFORM FEE MODEL (2% on every contribution deposit)")
    print("=" * 78)

    print("\nWORKED EXAMPLE — the founder's case")
    print("-" * 78)
    for label, value in worked_example():
        print(f"  {label:<52} {value}")

    print("\nYEAR-1 SCENARIOS (aligned to existing financial model)")
    print("-" * 78)
    header = (
        f"  {'Scenario':<14}{'Ajos':>6}{'Deposits':>10}"
        f"{'Volume':>16}{'Fee Revenue':>15}{'Fee/Ajo':>12}"
    )
    print(header)
    for r in scenario_rows():
        print(
            f"  {str(r['scenario']):<14}{r['ajos']:>6,}{r['deposits']:>10,}"
            f"{r['volume']:>16,}{r['fee_revenue']:>15,}{r['fee_per_ajo']:>12,}"
        )

    print("\nFEE SENSITIVITY BY CONTRIBUTION SIZE")
    print("-" * 78)
    print(f"  {'Contribution':>14}{'Fee (2%)':>12}{'Total charged':>16}{'Fee share':>12}")
    for amount, fee, total, pct in fee_sensitivity():
        print(f"  {('NGN ' + format(amount, ',')):>14}{('NGN ' + format(fee, ',')):>12}"
              f"{('NGN ' + format(total, ',')):>16}{pct:>11.2f}%")
