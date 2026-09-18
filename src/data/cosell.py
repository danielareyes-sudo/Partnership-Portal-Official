"""Stablecoin Provider Sprint — the execution plan, as data.

Source: Yuno_Stablecoin_Provider_Sprint.docx (Internal · Owner: Daniela · Draft v1),
covering September to November 2026. Text is the plan's own wherever it is shown
on screen; nothing here is a restatement in different words.

Salesforce remains the system of record for stage. `stage` below is a starting
position derived from each provider's "Where it stands" line so the sprint view
opens on something sensible — the portal does not write it back.
"""

# ── The desk ──────────────────────────────────────────────────────────────────
# The partnerships roster and the region each manager covers. The sprint plan
# names owners informally ("Melissa", "Ale", "Daniela / Melissa"); MANAGERS is
# the canonical list the board filters on, and each provider carries both — the
# roster key it is assigned to, and the plan's own wording as written.
#
# NOTE "Ale" in the plan is read here as Alessandra, on the basis that BVNK is
# London-based and Triple-A is Singapore, both inside her Europe/APAC coverage
# rather than a LATAM desk. If the plan meant Alejo, change `owner` on those two.

MANAGERS = [
    {"key": "Alessandra", "name": "Alessandra", "region": "Europe",       "accent": "#8B9BFF"},
    {"key": "Talita",     "name": "Talita",     "region": "LATAM",        "accent": "#E0ED80"},
    {"key": "Alejo",      "name": "Alejo",      "region": "LATAM",        "accent": "#FFD400"},
    {"key": "Mel",        "name": "Mel",        "region": "US & Global",  "accent": "#5FD4E8"},
    {"key": "Dani",       "name": "Dani",       "region": "Global",       "accent": "#E68ABE"},
]

UNASSIGNED = {"key": "Unassigned", "name": "Unassigned", "region": "owner to be named",
              "accent": "#676E8A"}


def manager(key):
    for m in MANAGERS:
        if m["key"] == key:
            return m
    return UNASSIGNED


SPRINT = {
    "title": "Stablecoin Provider Sprint",
    "subtitle": "Execution plan for the Partnerships team · September to November 2026",
    "meta": "Internal · Owner: Daniela · Draft v1",
    "window": "10 weeks",
    "launch": "Yuno Alliance launches externally on 23 September",
}

# The six Salesforce stages, in order. "Not started" is the implicit zero.
# The sales cycle a provider moves through. "Not started" is the holding pen for
# accounts still being screened — everything from Meeting Booked onward is the
# cycle proper, six stages ending at live traffic.
STAGES = ["Not started", "Meeting Booked", "Demo", "Product Workshop",
          "Pricing", "Contract", "Deal Closed", "Live"]

CYCLE_START = 1  # index of the first real stage; 0 is pre-cycle

PLAYS = {
    "full": "Full playbook",
    "stage5": "Go straight to Stage 5",
    "upsell": "Upsell version",
    "carved": "Carved out",
}

PROVIDERS = [
    {"name": "Zerohash", "owner": "Mel", "owner_plan": "Melissa", "support": None, "stage": 1,
     "standing": "NDA in progress (via Piotr)",
     "play": "full", "play_note": "Full playbook",
     "platform_fee": True},
    {"name": "Cyclops", "owner": "Dani", "owner_plan": "Daniela / Melissa", "support": "Mel", "stage": 5,
     "standing": "Contract stage, 10 bps proposal out",
     "play": "stage5",
     "play_note": "Go straight to Stage 5. Do not reopen pricing with the per-transaction model",
     "platform_fee": True},
    {"name": "BVNK", "owner": "Alessandra", "owner_plan": "Ale", "support": None, "stage": 0,
     "standing": "Screening",
     "play": "full",
     "play_note": "Full playbook. Mastercard acquisition is pending, so expect slower "
                  "decisions and confirm who signs",
     "platform_fee": True},
    {"name": "Triple-A", "owner": "Alessandra", "owner_plan": "Ale", "support": None, "stage": 0,
     "standing": "New in pipeline",
     "play": "full", "play_note": "Full playbook",
     "platform_fee": True},
    {"name": "Noah", "owner": "Unassigned", "owner_plan": "TBC", "support": None, "stage": 0,
     "standing": "Screening",
     "play": "full", "play_note": "Full playbook once an owner is named",
     "platform_fee": True},
    {"name": "crypto.com", "owner": "Unassigned", "owner_plan": "TBC", "support": None, "stage": 0,
     "standing": "Existing partner and lead",
     "play": "upsell",
     "play_note": "Upsell version: present Alliance as an upgrade to the current relationship",
     "platform_fee": True},
    {"name": "Coinflow", "owner": "Mel", "owner_plan": "Melissa", "support": None, "stage": 0,
     "standing": "Existing US partner",
     "play": "upsell", "play_note": "Upsell version, as above",
     "platform_fee": True},
    {"name": "Coinbase", "owner": "Mel", "owner_plan": "Melissa", "support": None, "stage": 5,
     "standing": "MSA and Order Form pending",
     "play": "carved",
     "play_note": "Carved out. Structure is a referral revshare paid to Yuno, so no "
                  "platform fee. Use Stages 2 and 3 only",
     "platform_fee": False},
    {"name": "Tempo", "owner": "Mel", "owner_plan": "Melissa", "support": None, "stage": 0,
     "standing": "Relationship",
     "play": "carved",
     "play_note": "Carved out. Align with the CEO-office stablecoin strategy before any "
                  "commercial conversation",
     "platform_fee": False},
]

PLAYBOOK = [
    {"n": 1, "title": "Reach out", "when": "sent by Friday 18 September",
     "body": ["Each owner sends a personal note, not a template blast. Before writing it, "
              "spend twenty minutes on a short account brief in Salesforce covering what the "
              "provider does, who its customers are, which markets it serves and any existing "
              "Yuno touchpoint. The note should hang on the Alliance launch and one specific "
              "reason the fit is real for that provider. Ask for 45 minutes in the window of "
              "21 September to 2 October. A sample note is in Appendix A."],
     "done": "the note is sent, the Salesforce stage is updated and a follow-up is diarised "
             "three working days out."},
    {"n": 2, "title": "Present the partner program", "when": "21 September to 2 October",
     "body": ["Use the Alliance external deck. For stablecoin providers the pitch lands on "
              "reach: Yuno gets them connected to acquirers and PSPs faster than they can "
              "manage alone, and puts them in front of merchants through our network. Explain "
              "the commercial model in outline, as a platform fee plus transaction pricing, "
              "but hold back numbers. Numbers come after the workshop, once we have their data.",
              "Close the call by booking the workshop and sending the data request in "
              "Appendix B, so the provider arrives at the workshop with volumes and an "
              "acquirer and PSP wish list."],
     "done": "the workshop is booked, the data request is sent and the NDA is signed if it "
             "wasn't already."},
    {"n": 3, "title": "Product workshop", "when": "28 September to 16 October",
     "body": ["Run a 60-minute session. The provider presents their API for 30 minutes, then "
              "we spend 30 minutes on how they connect into Yuno. Bring someone from product "
              "or solutions engineering; this is a technical session, not a second sales call. "
              "The most useful thing to come out of the room is the list of acquirers and PSPs "
              "they want us to introduce or connect them to, because that list drives both the "
              "pricing and the integration plan.",
              "Before proposing any go-live date, confirm Yuno-side engineering capacity with "
              "product. We have seen integrations start without Partnerships and product "
              "aligned, and then stall at go-live. Dates we can't staff will cost us the "
              "leverage we need later.",
              "Within three working days, send a written technical scope covering the "
              "integration direction on each side, target acquirers and PSPs, markets, effort "
              "estimates for both teams and a proposed go-live."],
     "done": "the technical scope is agreed in writing and the provider's volume data is in hand."},
    {"n": 4, "title": "Pricing negotiation",
     "when": "proposal within five working days of the workshop, agreed by 30 October",
     "body": ["Follow the pricing playbook below. Send the proposal in writing, walk the "
              "provider through it live, and keep every concession traded against something "
              "rather than given away."],
     "done": "pricing is agreed in writing and approved at the right level."},
    {"n": 5, "title": "Contract and close", "when": "both contracts signed by 20 November",
     "body": ["There are two agreements for every provider, and the integration dates must be "
              "the same in both. The contracts section below covers what each needs to include."],
     "done": "both contracts are signed, the integration plan annex is attached to each and "
             "the technical kickoff is booked."},
]

# ── Pricing playbook ──────────────────────────────────────────────────────────
PLATFORM_FEE = {
    "list": 15000, "floor": 10000, "owner_limit": 12500,
    "bands": [(15000, 12500, "Deal owner, at their discretion"),
              (12500, 10000, "Daniela's approval required"),
              (10000, 0, "Not available. Trade elsewhere or walk away")],
    "start_trigger": "The platform fee should start at the earlier of go-live or 90 days "
                     "after signature. Otherwise a slow integration on the partner's side "
                     "quietly becomes a free period.",
}

TRX_TIERS = [
    (0, 250_000, 0.08, "Up to 250k"),
    (250_000, 1_000_000, 0.065, "250k to 1M"),
    (1_000_000, None, 0.05, "Above 1M"),
]

BPS_FLOOR = 0.0010  # 10 bps
BREAKEVEN_ATV = 80.0

PRICING_RULE = ("Price at the greater of the per-transaction tier or 10 bps. This is standard "
                "in the market, protects us at both ends of the ATV range and saves us from "
                "having to guess each provider's mix upfront.")

TIER_CAVEAT = ("The tier thresholds are a proposal and need sign-off before the first pricing "
               "proposal goes out.")

CONCESSION_ORDER = [
    "The integration fee waiver",
    "Transaction tier thresholds",
    "A lower transaction tier in exchange for a volume commitment",
    "Priority on acquirer and PSP introductions",
    "Visibility in the Alliance founding cohort",
]

INTEGRATION_FEE = ("Both companies are doing integration work, so waiving the fee is "
                   "reasonable. Make the waiver conditional on the provider hitting the "
                   "milestones in the integration plan. If they slip beyond an agreed grace "
                   "period, the fee applies. This turns a giveaway into our best lever for "
                   "keeping integrations on schedule.")

ATV_TABLE = [("$25", "$0.080", "$0.025", "Per trx"),
             ("$50", "$0.080", "$0.050", "Per trx"),
             ("$80", "$0.080", "$0.080", "Break-even"),
             ("$150", "$0.080", "$0.150", "Bps"),
             ("$300", "$0.080", "$0.300", "Bps")]

CONTRACTS = [
    ("Agreement A", "The provider connecting into Yuno",
     "This is the commercial agreement. It carries the platform fee, transaction pricing, "
     "the conditional integration fee waiver, the fee start trigger, and the service levels "
     "we commit to."),
    ("Agreement B", "Yuno connecting into the provider",
     "This is the technical and processing agreement for their endpoint, including any "
     "referral or revenue share that flows to Yuno."),
    ("Annex", "A single integration plan, referenced by both",
     "The annex sets out technical kickoff, sandbox access, certification, production "
     "credentials and the first live merchant, with an owner on each side for every "
     "milestone. If a date moves, it moves in the annex and both agreements follow."),
]

LEGAL_DEPENDENCY = ("Legal templates are the dependency to watch. The agreements need to be "
                    "in English and reflect the upsell motion, and that has already slowed "
                    "the co-sell work. Templates for A and B need to be ready by 30 September "
                    "to leave room for 20 November signatures.")

RHYTHM = ("Salesforce is the only tracker. We'll run a 30-minute sprint review every Monday "
          "until 20 November, looking only at what moved, what is stuck and what needs an "
          "escalation. Anything below the $12.5k platform-fee line, any request to drop the "
          "bps floor and any integration date product hasn't confirmed comes to Daniela the "
          "same day.")

DECISIONS = [
    "Sign-off on the greater-of pricing rule and the tier thresholds, with finance involved.",
    "Owners for Noah and crypto.com.",
    "A date from legal for the two English templates.",
    "Alignment with the CEO office on Tempo.",
    "A named product or solutions contact for the workshops, so capacity is booked before "
    "the first date is promised.",
]

OUTREACH_NOTE = (
    "Hi [name], hope you're well. We're launching Yuno Alliance on 23 September. It's our "
    "partner program for providers who want faster reach into acquirers, PSPs and merchants "
    "across LatAm and beyond. Stablecoin providers are one of the groups we're building it "
    "around, and [company] came straight to mind because [specific reason]. Would you be open "
    "to 45 minutes in the next couple of weeks? I'd love to walk you through the program, show "
    "how other providers are connecting into Yuno, and hear where you're heading next. "
    "[Your name]")

DATA_REQUEST = [
    ("Total processing volume, monthly and annual",
     "Sets the transaction tier and tests the bps floor"),
    ("Transaction count", "Sets the transaction tier"),
    ("Average transaction value",
     "Decides whether per-trx or bps is the operative price"),
    ("Pay-in and payout split", "Both are priced, and the mix changes the economics"),
    ("Markets and currencies", "Scopes coverage and integration effort"),
    ("Acquirers and PSPs to introduce or connect",
     "Drives the integration plan and our value proposition"),
    ("Target go-live and existing integrations",
     "Anchors the dates in the integration plan annex"),
]
