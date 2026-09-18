"""Lead generation desk — Merchants and FinX.

Weekly operating rhythm for keeping new lead flow moving. Owners map to the
partnerships roster in cosell.py; regions come from the same desk so a manager
sees only what is theirs.

Priorities are P1/P2/P3: P1 is this week or it slips, P2 is this week if the
week allows, P3 is standing work that must not go quiet.
"""

TRACKS = {
    "Merchants": {
        "blurb": "Direct merchant demand — enterprise and mid-market processing volume.",
        "accent": "#3E4FE0",
        "sources": [
            ("Partner referrals", "Warmest route. A PSP or acquirer introducing their own "
                                  "merchant converts far above cold outbound."),
            ("Expansion triggers", "A merchant entering a new market needs local methods — "
                                   "the moment the news breaks is the moment to call."),
            ("Payments-pain inbound", "Approval-rate complaints and chargeback spikes surface "
                                      "in public forums and support channels."),
            ("Event and conference lists", "Attendee lists are a named universe, not a cold one."),
            ("Existing-merchant referrals", "The best-performing accounts know their peers."),
        ],
    },
    "FinX": {
        "blurb": "Financial-institution demand — banks, acquirers, PSPs, fintechs and "
                 "stablecoin providers connecting into Yuno.",
        "accent": "#0086A8",
        "sources": [
            ("Coverage gaps", "Where Yuno has merchant demand but no local rail, the provider "
                              "that fills it has a reason to talk today."),
            ("Alliance inbound", "The Alliance launch gives every provider a named programme "
                                 "to ask about."),
            ("Provider ecosystems", "A provider already integrated brings the rest of its "
                                    "corridor with it."),
            ("Regulatory shifts", "New licensing or scheme rules create a window where "
                                  "providers are actively re-platforming."),
            ("Competitor churn", "Providers leaving another orchestrator are in market now."),
        ],
    },
}

PRIORITIES = {
    "P1": ("#C4384A", "This week, or it slips"),
    "P2": ("#B36200", "This week if the week allows"),
    "P3": ("#3E4FE0", "Standing work — must not go quiet"),
}

# ── The weekly board ──────────────────────────────────────────────────────────
# owner is a roster key from cosell.MANAGERS, or "Desk" for whole-team work.
PLAYS = [
    # ---- Merchants ----------------------------------------------------------
    {"track": "Merchants", "p": "P1", "owner": "Talita",
     "title": "Mine the partner base for referrals",
     "task": "Pick five live partners and ask each for one merchant introduction. Name the "
             "merchant you want rather than asking open-endedly — a specific ask converts.",
     "tip": "Lead with what the partner gets: their merchant on better approval rates makes "
            "them look good, and the rev share follows.",
     "cadence": "Monday", "target": "5 asks · 2 intros"},
    {"track": "Merchants", "p": "P1", "owner": "Alejo",
     "title": "Work this week's expansion signals",
     "task": "Scan funding and expansion news for merchants entering a new market, and reach "
             "the payments owner inside 48 hours of the announcement.",
     "tip": "The window is days, not weeks. After the launch decision the rails are already "
            "chosen and you are pitching a migration instead of a build.",
     "cadence": "Tue / Thu", "target": "8 signals · 3 contacts"},
    {"track": "Merchants", "p": "P2", "owner": "Alessandra",
     "title": "Turn approval-rate pain into a conversation",
     "task": "Collect public complaints about declines, 3DS friction or chargebacks in your "
             "region and open with a specific observation, not a deck.",
     "tip": "Quote their own number back to them. A merchant who has said 'our approval rate "
            "in Brazil is terrible' has already done your qualifying.",
     "cadence": "Wednesday", "target": "6 opens"},
    {"track": "Merchants", "p": "P2", "owner": "Mel",
     "title": "Referral loop on the best accounts",
     "task": "Take the three healthiest merchant accounts and ask each for one peer "
             "introduction while the performance data is in front of them.",
     "tip": "Ask right after a good number lands — a merchant who just saw approval lift is "
            "the easiest referral you will ever get.",
     "cadence": "Thursday", "target": "3 asks"},
    {"track": "Merchants", "p": "P3", "owner": "Desk",
     "title": "Keep the event list warm",
     "task": "Work the attendee list from the last event: one touch per name, then retire the "
             "ones with no response after three.",
     "tip": "Three touches then stop. A list worked forever is a list nobody trusts.",
     "cadence": "Friday", "target": "20 touches"},

    # ---- FinX ---------------------------------------------------------------
    {"track": "FinX", "p": "P1", "owner": "Dani",
     "title": "Close the coverage gaps merchants are asking for",
     "task": "Take the top three markets where merchant demand exists but Yuno has no local "
             "rail, and name the providers who could fill each.",
     "tip": "This is the strongest opening in the business: you are not asking for a meeting, "
            "you are bringing them demand that already exists.",
     "cadence": "Monday", "target": "3 markets · 6 providers"},
    {"track": "FinX", "p": "P1", "owner": "Mel",
     "title": "Convert Alliance inbound inside 48 hours",
     "task": "Every inbound enquiry from the Alliance launch gets a personal reply and a "
             "45-minute slot offered within two working days.",
     "tip": "Inbound decays fast. A provider who wrote in on Monday and hears back on Friday "
            "has already had two other conversations.",
     "cadence": "Daily", "target": "100% inside 48h"},
    {"track": "FinX", "p": "P2", "owner": "Alessandra",
     "title": "Walk the corridor from a live provider",
     "task": "For each newly integrated provider, map the acquirers and PSPs they already work "
             "with and ask for a warm introduction to two.",
     "tip": "Ask during integration, not after go-live. Goodwill is highest while your "
            "engineers are in their Slack.",
     "cadence": "Tuesday", "target": "2 intros per provider"},
    {"track": "FinX", "p": "P2", "owner": "Alejo",
     "title": "Track the regulatory calendar",
     "task": "Watch licensing and scheme-rule changes in your markets and list the providers "
             "who have to re-platform because of them.",
     "tip": "A mandated deadline does the persuading for you — you are offering a way to meet "
            "a date they cannot move.",
     "cadence": "Wednesday", "target": "2 shortlists"},
    {"track": "FinX", "p": "P3", "owner": "Talita",
     "title": "Keep a live view of competitor churn",
     "task": "Note providers publicly leaving or reducing another orchestrator and log them "
             "with the reason given.",
     "tip": "Log the reason, not just the name. The reason is the opening line when you call.",
     "cadence": "Friday", "target": "running list"},
]

# ── Weekly rhythm ─────────────────────────────────────────────────────────────
RHYTHM = [
    ("Monday", "Set the week", "Pick the P1s, confirm owners, and put the number you are "
                               "chasing on the board."),
    ("Wednesday", "Mid-week check", "What has not moved since Monday, and what does it need?"),
    ("Friday", "Log and hand over", "Every new lead in Salesforce with a source and an owner "
                                    "before the week closes."),
]

DISCIPLINE = [
    "A lead with no owner is not a lead. Name someone before it goes on the board.",
    "Log the source every time — it is the only way to learn which route actually works.",
    "Three touches, then retire it. Lists that never close stop being believed.",
    "Specific asks beat open ones: name the merchant or provider you want introduced.",
    "Speed beats polish on inbound. A same-day reply outperforms a better email on Friday.",
]

QUALIFY = [
    ("Merchants", ["Annual processing volume and the markets it runs in",
                   "Current PSPs and the approval rate they live with",
                   "What is driving the change now — expansion, cost, or a failure",
                   "Who owns the payments decision, and who signs"]),
    ("FinX", ["Coverage: markets, methods and the rails they own",
              "Volume and average ticket, which set the pricing tier",
              "Which acquirers and PSPs they want reaching",
              "Integration appetite and whose engineers do the work"]),
]


# ── Channels: how we go and find them ─────────────────────────────────────────
# Each channel is a way of generating named leads, with the weekly tip that
# makes it work and the number to chase.
CHANNELS = [
    {"name": "Events & conferences", "icon": "◈", "accent": "#E0ED80",
     "tracks": ["Merchants", "FinX"], "owner": "Desk", "cadence": "Per event",
     "target": "30 named · 10 meetings",
     "tip": "Book meetings before you fly, not on the floor. An agenda sent two weeks out "
            "converts several times better than a badge scan, and the ones who decline tell "
            "you who to chase next quarter.",
     "steps": ["Pull the attendee and sponsor list the moment it publishes",
               "Name the 30 you actually want and split them by owner",
               "Send personal invites two weeks out with a specific reason to meet",
               "Debrief inside 48 hours — after that the notes go cold"]},
    {"name": "Webinars", "icon": "▶", "accent": "#8B9BFF",
     "tracks": ["Merchants", "FinX"], "owner": "Mel", "cadence": "Monthly",
     "target": "120 registered · 25 qualified",
     "tip": "Co-host with a partner rather than presenting alone. Their list is the lead "
            "source, the shared audience halves the promotion work, and a partner on the "
            "panel is a reference the room can question live.",
     "steps": ["Pick a topic from a live merchant problem, not a product tour",
               "Co-host with one partner who brings their own list",
               "Ask one qualifying question on the registration form",
               "Follow up inside 24 hours while the session is still fresh"]},
    {"name": "Roundtables & dinners", "icon": "◇", "accent": "#FFA53D",
     "tracks": ["Merchants"], "owner": "Talita", "cadence": "Quarterly per market",
     "target": "12 seats · 6 opportunities",
     "tip": "Ten payments leads around a table beats a hundred in a hall. Let a merchant "
            "host the topic — peers speak more openly to peers than to a vendor.",
     "steps": ["One city, one vertical, twelve seats",
               "A merchant opens, not Yuno",
               "No deck in the room; the follow-up carries the detail",
               "Every attendee gets a named owner before the plates are cleared"]},
    {"name": "Content & benchmarks", "icon": "▤", "accent": "#5FD4E8",
     "tracks": ["Merchants", "FinX"], "owner": "Dani", "cadence": "Monthly",
     "target": "1 asset · 40 inbound",
     "tip": "Publish the number nobody else can. Yuno sees approval rates across providers "
            "and markets — a regional benchmark is the one thing a merchant cannot get from "
            "their own PSP, and it earns the meeting on its own.",
     "steps": ["Pick one market and one metric per asset",
               "Anonymise and check with data before publishing",
               "Gate nothing — the citation is worth more than the form fill",
               "Give every seller three lines they can send with it"]},
    {"name": "Partner co-marketing", "icon": "⧉", "accent": "#A9DE4E",
     "tracks": ["FinX"], "owner": "Alessandra", "cadence": "Per launch",
     "target": "2 launches · 15 intros",
     "tip": "Every new integration is a launch moment with two audiences. Agree the joint "
            "announcement and the intro list before go-live, while the partner still needs "
            "something from you.",
     "steps": ["Put co-marketing in the agreement, not in a later conversation",
               "Announce jointly on the day the connector goes live",
               "Trade intro lists — theirs for yours, named on both sides",
               "Run one joint webinar within a month of launch"]},
    {"name": "Outbound sequences", "icon": "→", "accent": "#B9C2FF",
     "tracks": ["Merchants", "FinX"], "owner": "Alejo", "cadence": "Weekly",
     "target": "40 sent · 8 replies",
     "tip": "Lead with their number, not ours. An opening line naming the market they just "
            "entered or the rail they are missing gets read; a capabilities paragraph does "
            "not. Three touches, then retire it.",
     "steps": ["Segment by trigger, never by industry alone",
               "One observation about them before any claim about Yuno",
               "Three touches across two weeks, then stop",
               "Log every reply, including the no — it is next quarter's list"]},
]

# ── Merchant referral base ────────────────────────────────────────────────────
# Yuno holds no merchant prospect list, so the merchant lane is seeded from the
# live base: named accounts to ask for named introductions.
MERCHANT_BASE = [
    ("Rappi",        "Colombia",  "LATAM",      "Delivery"),
    ("MercadoLibre", "Argentina", "LATAM",      "Marketplace"),
    ("Uber",         "Mexico",    "LATAM",      "Mobility"),
    ("Netflix",      "USA",       "N. America", "Subscription"),
    ("Spotify",      "Brazil",    "LATAM",      "Subscription"),
    ("Despegar",     "Argentina", "LATAM",      "Travel"),
    ("Falabella",    "Chile",     "LATAM",      "Retail"),
    ("iFood",        "Brazil",    "LATAM",      "Delivery"),
    ("Cinépolis",    "Mexico",    "LATAM",      "Entertainment"),
    ("PedidosYa",    "Argentina", "LATAM",      "Delivery"),
    ("Claro",        "Mexico",    "LATAM",      "Telco"),
    ("Linio",        "Colombia",  "LATAM",      "Marketplace"),
]

MERCHANT_SOURCE_NOTE = (
    "Yuno holds no merchant prospect list in this portal, so the merchant lane starts from "
    "the live base: each account below is a named referral source, not a lead. Ask for a "
    "specific peer by name — an open ask gets an open answer.")

FINX_SOURCE_NOTE = (
    "Pulled live from the partner account book: every partner sitting at Opportunity "
    "Identification or Initial Negotiation, with the owner on record.")
