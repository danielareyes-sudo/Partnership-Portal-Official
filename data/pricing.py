"""Financial-services pricing model.

Source: Pricing_Calculator_Financial_Services.xlsx — the Calculator, Assumptions
and Tiering tabs. Fee levels, floors, caps and the bps benchmark are the
workbook's own; nothing here is a rounded-off retelling.

The workbook is explicit that it is a guide rather than a rulebook: two things
never bend — never price a transaction below the $0.01 cost floor, and keep the
control blend in a healthy market range. Everything else is a lever.
"""

PHILOSOPHY = (
    "This model is a GUIDE, not a rulebook. Every deal is different and has its own "
    "nuances. The goal is to give you a solid base to price from, quickly and "
    "consistently, without having to ask case by case. Use it as your starting point, "
    "then apply judgment.")

NEVER_BEND = (
    "Two things never bend: never price a transaction below the $0.01 cost floor, and "
    "keep an eye on the control blend in bps so the all-in price stays in a healthy "
    "market range.")

# ── Fixed fees by complexity ──────────────────────────────────────────────────
COMPLEXITY = ["Simple", "Medium", "Complex"]

IMPLEMENTATION_FEE = {"Simple": 15_000, "Medium": 30_000, "Complex": 45_000}
PLATFORM_FEE_MONTHLY = {"Simple": 10_000, "Medium": 25_000, "Complex": 45_000}

PLATFORM_FEE_NOTE = {
    "Simple": "Value fee. Includes support + maintenance",
    "Medium": "Value fee, not an FTE calc",
    "Complex": "Complex deals: up to ~$40-50k (Mau)",
}

# ── Costs, floors and benchmarks ──────────────────────────────────────────────
COST_FLOOR_PER_TX = 0.01          # 1 cent. Never below this.
PLATFORM_FEE_CAP = 0.3333         # Platform fee at most 1/3 of total deal revenue.
SUPPORT_COST_MONTHLY = 6_000      # Context only — never used as a formula.
BLEND_TARGET_BPS = 5              # ~5 bps. Market centre for pure orchestration.
BLEND_CEILING_BPS = 10            # ~10 bps once value add-ons are in.
FINANCE_REVIEW_THRESHOLD = 1_000_000   # Deals above this go to Finance + Product.

# ── Volume tiering ────────────────────────────────────────────────────────────
# Calculator's Tiered mode is MARGINAL: each band bills its own slice.
TIER_BANDS = [
    (0,          15_000_000,  0.02,   "Base band"),
    (15_000_000, 40_000_000,  0.0175, "Rewards higher volume"),
    (40_000_000, 80_000_000,  0.015,  "High volume"),
    (80_000_000, None,        0.0125, "Very high / strategic volume"),
]

# The Tiering tab's separate "where you land" benchmark — whole monthly volume
# charged at the band it falls in. Reference only; it does not feed the model.
LANDING_BENCHMARK_NOTE = (
    "Benchmark (Prosa model): total monthly volume falls in one band and ALL of it is "
    "charged at that price. The calculator's Tiered mode is marginal instead — each "
    "band bills its own slice.")

# ── Add-ons ───────────────────────────────────────────────────────────────────
# "free" means no third-party cost to Yuno, so it is a negotiation lever.
ADDONS = [
    ("Click to Pay (C2P)",           "Free (they pay us to offer it) → lever",        True),
    ("Anti-fraud",                   "Free for Yuno → can be bundled",                True),
    ("Risk conditions",              "Free for Yuno → can be bundled",                True),
    ("Tokenization / network tokens", "Free today; in banking it can be charged",     True),
    ("External 3DS",                 "HAS third-party cost → charge separately",      False),
    ("Tap to Pay",                   "HAS third-party cost → charge separately",      False),
    ("MC chargeback alerts",         "HAS third-party cost → charge separately",      False),
]

# ── Complexity guide ──────────────────────────────────────────────────────────
COMPLEXITY_GUIDE = [
    ("DEAL SIZE by client TPV", "primary",
     "<$500M = simple · $500M–$2B = medium · >$2B = complex"),
    ("# of integrations / PSPs to connect", "",
     "1–2 = simple · 3–5 = medium · 6+ = complex"),
    ("Markets / countries", "",
     "1 country = simple · 2–3 = medium · multi-region = complex"),
    ("Customization / bespoke development", "",
     "None = simple · Some config = medium · High = complex"),
]

COMPLEXITY_RULE = (
    "DEAL SIZE by client TPV is the primary criterion (bigger banks and players = more "
    "complex). The other dimensions fine-tune and can bump it up a level if several "
    "point to more complexity. When in doubt, go up a level.")

# TPV thresholds behind the primary criterion, so the tool can suggest a level.
TPV_SIMPLE_MAX = 500_000_000
TPV_MEDIUM_MAX = 2_000_000_000

STEPS = [
    "Ask the client for their annual TPV and transaction volume.",
    "Classify the deal's complexity (Simple / Medium / Complex).",
    "Choose the per-Tx mode: Fixed (one flat price) or Tiered (bands by monthly volume).",
    "Decide which add-ons to charge and which to bundle free as a lever.",
    "Check the result: effective price per Tx and control blend.",
]

REVIEW_NOTE = ("Deals over $1M in annual revenue go to Finance + Product for sign-off. "
               "When in doubt on any deal, bring it to the team.")
