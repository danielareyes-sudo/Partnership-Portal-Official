"""Lead alerting and BDM assignment.

Who gets told when a lead arrives, and who picks it up. The GM roster is the
notification list; the BDM roster is the assignment pool. Regions use the
account book's own vocabulary so a lead's Region field routes without mapping.

Slack handles are filled in by the team — a handle left blank posts the GM's
name as plain text rather than a broken mention.
"""

# The channel every lead alert lands in.
LEADS_CHANNEL = "#partnership-leads"

# ── GMs · the notification list ───────────────────────────────────────────────
# Every GM is alerted on every lead; `regions` only controls who is called out
# as the regional owner in the message body.
GMS = [
    {"name": "GM · LATAM",         "handle": "", "regions": ["LATAM", "Brasil"]},
    {"name": "GM · North America", "handle": "", "regions": ["North America"]},
    {"name": "GM · EMEA",          "handle": "", "regions": ["EMEA", "Africa", "MENAT"]},
    {"name": "GM · APAC",          "handle": "", "regions": ["APAC"]},
    {"name": "GM · Global",        "handle": "", "regions": ["Global"]},
]

# ── BDMs · the assignment pool ────────────────────────────────────────────────
BDMS = [
    {"key": "Alessandra", "name": "Alessandra", "handle": "",
     "regions": ["EMEA", "Europe", "APAC", "Africa", "MENAT"]},
    {"key": "Talita",     "name": "Talita",     "handle": "",
     "regions": ["LATAM", "Brasil"]},
    {"key": "Alejo",      "name": "Alejo",      "handle": "",
     "regions": ["LATAM"]},
    {"key": "Mel",        "name": "Mel",        "handle": "",
     "regions": ["North America", "Global"]},
    {"key": "Dani",       "name": "Dani",       "handle": "",
     "regions": ["Global"]},
]

# Preference order per region. First with capacity takes it; ties round-robin.
REGION_ROUTING = {
    "LATAM":         ["Talita", "Alejo"],
    "Brasil":        ["Talita", "Alejo"],
    "EMEA":          ["Alessandra"],
    "Europe":        ["Alessandra"],
    "Africa":        ["Alessandra"],
    "MENAT":         ["Alessandra"],
    "APAC":          ["Alessandra"],
    "North America": ["Mel"],
    "Global":        ["Mel", "Dani"],
}

FALLBACK_BDM = "Dani"

TRACKS = ["FinX", "Merchants"]

SOURCES = ["Inbound", "Event", "Webinar", "Roundtable", "Partner referral",
           "Merchant referral", "Outbound", "Content", "Alliance launch", "Other"]

# ── The alert itself ──────────────────────────────────────────────────────────
SLA_HOURS = 48   # first contact, per the sprint plan's inbound rule.

ALERT_RULES = [
    ("Every lead", "Posts to the leads channel the moment it is logged, with the "
                   "assigned BDM named in the message."),
    ("Regional GM", "The GM whose region the lead sits in is called out by name; the "
                    "rest of the GM group is on the channel and sees it."),
    ("Assignment", "Routed by region from the account book's own Region field, "
                   "round-robin where two BDMs cover the same region."),
    ("Unrouted", f"A region with no BDM falls to {FALLBACK_BDM} and the message says so, "
                 f"rather than sitting unassigned."),
    ("Response", f"First contact inside {SLA_HOURS} hours. The alert carries the clock so "
                 f"nobody has to work out when it landed."),
]
