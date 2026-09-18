import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import base64 as _b64
import re as _re

try:
    import os as _os
    _BASE = _os.path.dirname(_os.path.abspath(__file__))
    _LOGO_B64 = _b64.b64encode(open(_os.path.join(_BASE, "Yuno logo.png"),"rb").read()).decode()
except:
    _LOGO_B64 = ""

try:
    _DANIELA_B64 = _b64.b64encode(open(_os.path.join(_BASE, "daniela.png"),"rb").read()).decode()
except:
    _DANIELA_B64 = ""

try:
    import sys as _sys
    _sys.path.insert(0, _os.path.join(_BASE, "data"))
    from partner_contacts import PARTNER_CONTACTS as _EXT_CONTACTS
except:
    _EXT_CONTACTS = {}

try:
    from integrations import INTEGRATIONS as _INTEGRATIONS
except:
    _INTEGRATIONS = {}

try:
    import pricing as _PR
except:
    _PR = None

try:
    import leadgen as _LG
except:
    _LG = None

try:
    import routing as _RT
except:
    _RT = None

try:
    import cosell as _CS
except:
    _CS = None

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PAPO · Yuno Partner Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ──────────────────────────────────────────────────────────────
for k, v in [("role", None), ("pending_role", None), ("sso_method", None), ("auth_email", ""), ("pw_error", False), ("page", "Home"), ("cat_filter", "all"), ("tier_mode", "idle"), ("tier_open", None), ("auth_email_used", ""), ("partner_identity", None), ("alliance_alerted", None), ("insight_tab", "market"), ("selected_partner", None), ("partner_tab", "Overview"), ("integration_open", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# Sync page from URL query params on first load
_qp = st.query_params
if "role" in _qp and st.session_state.role is None:
    if _qp["role"] in ("internal", "partner"):
        st.session_state.role = _qp["role"]
if "page" in _qp:
    valid_pages = {"Home","Pipeline","Partners","Merchants","Performance","Benchmarks","Insights","PayRec","MerchSim","MissionCtrl","Expansion","Cosell","LeadGen","Share","GTM"}
    if _qp["page"] in valid_pages:
        st.session_state.page = _qp["page"]

# ── Data (loaded from Excel) ──────────────────────────────────────────────────
_PARTNERS_EXCEL = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "strategic_accounts.xlsx")

_TYPE_COLOR = {"Acquirer": "#3E4FE0", "PSP/Aggregator": "#C24E00", "APM": "#0086A8",
               "BaaS": "#2F8A1F", "Fraud Provider": "#C4187F", "Plug-In": "#6B6F00",
               "Other": "#676E8A"}
_TYPE_SHORT = {"Acquirer": "Acquirer", "PSP/Aggregator": "PSP", "APM": "APM", "Fraud Provider": "Fraud", "BaaS": "BaaS", "Other": "Other", "Plug-In": "Plug-In"}
_STAGE_MAP  = {"Live Partner": "Live", "Agreement Signed": "Agreement Signed", "Agreement Review": "Agreement Review", "Initial Negotiation": "Negotiation", "Opportunity Identification": "Prospect", "Lost": "Lost", "Only to be integrated": "Integration Only", "Agreement Signed - Only referrals": "Referral Only", "Non-qualified Partner": "Non-Qualified"}

@st.cache_data
def load_partners_excel():
    try:
        df = pd.read_excel(_PARTNERS_EXCEL, sheet_name="All partners")
        seen, partners = set(), []
        for _, row in df.iterrows():
            name = str(row.get("Provider", "")).strip()
            if not name or name in seen or name == "nan":
                continue
            seen.add(name)
            offering = str(row.get("Partner offering (acquirer, APM, Fraud etc)", "Other")).strip()
            stage_raw = str(row.get("Deal Stage", "")).strip()
            region = str(row.get("Region", "")).strip()
            country = str(row.get("Country", "")).strip()
            tier = str(row.get("Type of Partner", "")).strip()
            manager = str(row.get("Partner Manager", "")).strip()
            strategic = bool(row.get("Strategic?", False))
            mgmt_type = str(row.get("Type of Management", "")).strip()
            initials = "".join(w[0] for w in name.replace("/", " ").replace("(", " ").split() if w)[:2].upper()
            partners.append({
                "name": name, "type": _TYPE_SHORT.get(offering, offering), "offering_raw": offering,
                "region": region if region != "nan" else "", "country": country if country != "nan" else "",
                "status": _STAGE_MAP.get(stage_raw, stage_raw), "stage_raw": stage_raw,
                "tier": tier if tier != "nan" else "", "manager": manager if manager != "nan" else "",
                "strategic": strategic, "mgmt_type": mgmt_type if mgmt_type != "nan" else "",
                "logo": initials, "color": _TYPE_COLOR.get(offering, "#676E8A"),
                "cat": _TYPE_SHORT.get(offering, offering),
                "nda": bool(row.get("NDA Signed and in drive", False)),
                "revshare": bool(row.get("Revshare Contract", False)),
                "revshare_active": bool(row.get("Revshare active", False)),
                "integration_ready": bool(row.get("Integration Ready by Yuno", False)),
                "integration_used": bool(row.get("Integration Used by Merchants", False)),
                "comments": str(row.get("Comments", "")).strip() if str(row.get("Comments", "")).strip() != "nan" else "",
            })
        return sorted(partners, key=lambda x: x["name"].lower())
    except Exception:
        return []

PARTNERS_DATA = load_partners_excel()

# Revenue share data from PPTX (Feb 2026)
_REVSHARE_BY_PARTNER = {"DLocal": 25338, "Stripe": 21705, "Cielo": 17635, "Bamboo": 9491, "Mercado Pago": 7365, "Unlimint": 5949, "PagBank": 4516, "Nuvei/Paymentez": 3772, "Pagar.me": 3441, "PicPay": 3180}
_REVSHARE_MONTHLY = [("Nov 24",61000),("Dec 24",61000),("Jan 25",122000),("Feb 25",122000),("Mar 25",183000),("Apr 25",183000),("May 25",144000),("Jun 25",145000),("Jul 25",166000),("Aug 25",219000),("Sep 25",245000),("Oct 25",245000),("Nov 25",178000),("Dec 25",161000),("Jan 26",123000),("Feb 26",123000)]
_REVSHARE_BY_REGION = {"LATAM": 42, "Brazil": 29, "Global": 25, "APAC": 3, "North America": 0}
_REGION_STATS = {
    "Brazil":        {"total":73,"live":32,"strategic":9,"tier1":4,"revshare":"$32.9K/mo"},
    "LATAM":         {"total":105,"live":15,"strategic":2,"tier1":31,"revshare":"$47.6K/mo"},
    "EMEA":          {"total":81,"live":2,"strategic":3,"tier1":21,"revshare":"-"},
    "Global":        {"total":107,"live":18,"strategic":13,"tier1":12,"revshare":"$28.3K/mo"},
    "APAC":          {"total":53,"live":6,"strategic":4,"tier1":10,"revshare":"$32.9K/mo"},
    "North America": {"total":37,"live":3,"strategic":5,"tier1":4,"revshare":"$0.4K/mo"},
    "Africa":        {"total":5,"live":0,"strategic":0,"tier1":2,"revshare":"-"},
}
_MANAGER_STATS = {
    "Alessandra Rospigliosi": {"regions":"EMEA, APAC, Africa, Global","strategic":8,"tier1":17,"tier2":44,"tier3":16},
    "Francisco Quintana":     {"regions":"MENAT, APAC, Global","strategic":1,"tier1":12,"tier2":25,"tier3":15},
    "Lily":                   {"regions":"APAC, Global","strategic":3,"tier1":9,"tier2":19,"tier3":1},
    "Johanderson Guevara":    {"regions":"Brazil, LATAM, Global","strategic":8,"tier1":13,"tier2":12,"tier3":22},
    "Talita Diaz Gama":       {"regions":"LATAM, Brazil, Global","strategic":3,"tier1":20,"tier2":16,"tier3":24},
    "Partha":                 {"regions":"APAC","strategic":1,"tier1":0,"tier2":1,"tier3":1},
}

CAT_CLASS   = {"PSP":"cat-psp","Acquirer":"cat-acquirer","APM":"cat-apm","Fraud":"cat-fraud","Fraud / KYC":"cat-fraud","BaaS":"cat-baas"}
STATUS_CLASS = {"Live":"p-green","Integration":"p-blue","Prospect":"p-amber","In Dev":"p-purple"}

# ── Source of Truth data for Payment Recommendations ─────────────────────────
_SOT_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "source_of_truth.xlsx")

_VERTICAL_COLS = {
    "High Risk":     "ACCEPTS_HIGH_RISK",
    "Gambling":      "ACCEPTS_GAMBLING",
    "Gaming":        "ACCEPTS_GAMING",
    "Forex":         "ACCEPTS_FOREX",
    "Crypto":        "ACCEPTS_CRYPTO",
    "Adult":         "ACCEPTS_ADULT",
    "MLM":           "ACCEPTS_MULTI_LEVEL_MARKETING",
    "Airlines":      "ACCEPTS_AIRLINES",
}

_ISO_TO_COUNTRY = {}
try:
    import pycountry as _pyc
    for c in _pyc.countries:
        _ISO_TO_COUNTRY[c.alpha_2] = c.name
except Exception:
    pass

@st.cache_data
def load_sot_data():
    try:
        df = pd.read_excel(_SOT_PATH, sheet_name="Partners")
        df = df[df["PROVIDER_CATEGORY"].isin(["ACQUIRER","GATEWAY","AGREGATOR","AGREGATOR / GATEWAY","PAYMENT_METHOD"])].copy()
        return df
    except Exception:
        return pd.DataFrame()

_SOT_DF = load_sot_data()
_SOT_COUNTRIES = sorted(set(_ISO_TO_COUNTRY.get(c, c) for c in _SOT_DF["COUNTRY_ISO"].dropna().unique() if _ISO_TO_COUNTRY.get(c, c) != c)) if len(_SOT_DF) > 0 else []
_SOT_PROVIDERS = sorted(_SOT_DF["PROVIDER_NAME"].dropna().unique().tolist()) if len(_SOT_DF) > 0 else []

def find_partners(country_iso=None, verticals=None, live_only=True, processing_type=None):
    """Find matching partners from Source of Truth."""
    df = _SOT_DF.copy()
    if len(df) == 0:
        return []
    if live_only:
        df = df[df["Live/NonLive Partner/Contract signed"] == "Live"]
    if country_iso:
        df = df[df["COUNTRY_ISO"] == country_iso]
    if processing_type:
        df = df[df["PROCESSING_TYPE"] == processing_type]
    if verticals:
        for v in verticals:
            col = _VERTICAL_COLS.get(v)
            if col and col in df.columns:
                df = df[(df[col] == True) | (df[col] == 1) | (df[col] == 1.0)]
    # Group by provider
    results = []
    for provider, grp in df.groupby("PROVIDER_NAME"):
        cats = grp["PROVIDER_CATEGORY"].unique().tolist()
        countries = sorted(grp["COUNTRY_ISO"].dropna().unique().tolist())
        pm_types = sorted(grp["PAYMENT_METHOD_TYPE"].dropna().unique().tolist())
        proc_types = grp["PROCESSING_TYPE"].dropna().unique().tolist()
        status = "Live" if "Live" in grp["Live/NonLive Partner/Contract signed"].values else "Non Live"
        supports = {}
        for feat in ["SUPPORTS_TOKENIZATION","SUPPORTS_RECURRING_PAYMENTS","SUPPORTS_PAYOUTS","SUPPORTS_INSTALLMENTS","SUPPORTS_PAYFAC","SUPPORTS_SPLIT_PAYMENTS","3DS"]:
            vals = grp[feat].dropna().unique()
            supports[feat] = any(v == True or v == 1 or v == 1.0 for v in vals)
        results.append({
            "name": provider,
            "categories": cats,
            "countries_iso": countries,
            "countries_count": len(countries),
            "payment_methods": pm_types[:8],
            "processing_types": proc_types,
            "status": status,
            "row_count": len(grp),
            "supports": supports,
        })
    results.sort(key=lambda x: (-x["countries_count"], x["name"]))
    return results

# ══ Partner tiering — the framework, executed ═══════════════════════════════════
# The framework workbook defines weights, thresholds and a 0–5 rubric. This runs
# it over every account rather than the 13 that were scored by hand. Each
# criterion derives from a named field, so a partner's score can always be
# explained by pointing at the row it came from.

def _find_book(*names):
    """Prefer a copy inside the repo; fall back to the user's Downloads."""
    import os
    for n in names:
        p = _os.path.join(_BASE, "data", n)
        if _os.path.exists(p):
            return p
    for n in names:
        p = _os.path.expanduser(_os.path.join("~", "Downloads", n))
        if _os.path.exists(p):
            return p
    return None

_ACCOUNTS_BOOK = _find_book("partnerships_accounts.xlsx", "Partnerships Accounts (14).xlsx")
_TIERING_BOOK  = _find_book("partner_tiering_model.xlsx", "partner_tiering_model (1).xlsx")

# The framework: Melissa's five-criterion rubric, re-weighted to run the partner
# network as a revenue engine and a lead machine. RevShare is dropped — it
# follows the relationship, it does not define it — and replaced by upsell
# potential: is this a FinX rail Yuno can sell more through. Volume is today's
# revenue, upsell is tomorrow's, co-sell and market weight are where the leads
# come from, and stage says whether any of it can happen now.
_TIER_WEIGHTS_DEFAULT = {"volume": 0.25, "market": 0.25, "cosell": 0.20, "stage": 0.15, "upsell": 0.15}
_TIER_CUTS_DEFAULT = {"Strategic": 0.75, "Tier 1": 0.55, "Tier 2": 0.30}

# The largest providers in the world. They score 5/5 on external market weight
# and nothing more — the tier is decided by the score, never by this list.
_MUST_HAVE = {
    "adyen", "stripe", "checkout", "worldpay", "fiserv", "global payments", "jp morgan",
    "nuvei", "dlocal", "ebanx", "payu", "rapyd", "airwallex", "worldline", "nexi",
    "network international", "elavon", "cybersource", "mercadopago", "pagseguro",
    "cielo", "rede", "getnet", "paypal / braintree", "klarna", "visa", "mastercard",
    "american express", "coinbase", "revolut", "tempo", "bridge", "circle",
    "riskified", "signifyd", "forter", "apple pay", "google pay", "alipay", "wechat pay",
    "ant intl antom", "unlimit", "xendit", "razorpay", "payoneer", "wise", "square",
    "shift4", "bamboo payments", "kushki", "prosa", "redeban colombia",
}

# The human-in-the-loop layer — Melissa's "Manual Override Tier" column. A
# placement beats the score, and the reason panel says so in as many words.
# Placements are made on screen and kept in data/tier_placements.json; the
# seed below only applies the first time, when the file does not exist yet.
_MANUAL_TIER_SEED = {
    "visa": "Strategic", "mastercard": "Strategic",
    "bbva": "Tier 1",
}
_PLACEMENTS_FILE = _os.path.join(_BASE, "data", "tier_placements.json")


def load_placements():
    """key → {"tier", "by", "when", "name"}; seeded once from the code table."""
    import json as _json, datetime as _dt
    try:
        with open(_PLACEMENTS_FILE) as f:
            return _json.load(f)
    except FileNotFoundError:
        seed = {k: {"tier": t, "by": "seed", "when": _dt.date.today().isoformat(), "name": k.title()}
                for k, t in _MANUAL_TIER_SEED.items()}
        try:
            _os.makedirs(_os.path.dirname(_PLACEMENTS_FILE), exist_ok=True)
            with open(_PLACEMENTS_FILE, "w") as f:
                _json.dump(seed, f, indent=2, sort_keys=True)
        except Exception:
            pass
        return seed
    except Exception:
        return {}


def save_placement(key, name, tier, by="Daniela Reyes"):
    """tier=None clears the placement and hands the partner back to the model."""
    import json as _json, datetime as _dt
    cur = load_placements()
    if tier:
        cur[key] = {"tier": tier, "by": by, "when": _dt.date.today().isoformat(), "name": name}
    else:
        cur.pop(key, None)
    _os.makedirs(_os.path.dirname(_PLACEMENTS_FILE), exist_ok=True)
    with open(_PLACEMENTS_FILE, "w") as f:
        _json.dump(cur, f, indent=2, sort_keys=True)

# The upsell motion is aimed at FinX partners — the rails a merchant needs, not
# the tooling around them: acquirers, PSPs, APMs (wallets live here in the book),
# fraud providers, crypto and stablecoin rails, account-to-account rails.
_FINX_TYPES = {"Acquirer", "PSP/Aggregator", "APM", "Fraud Provider", "Crypto", "A2A"}
_FINX_WORDS = ("wallet", "stablecoin", "crypto")   # catches a wallet filed under another type
_SIGNIFICANT_VOLUME = 1_000_000   # approved txns / month — the rubric's "meets minimum" band
# The two card schemes are a merchant lead source in their own right — they
# refer merchants to acquirers and orchestrators — so they carry the flag even
# though they never process volume on Yuno's rails.
_SCHEME_LEAD_SOURCES = {"visa", "mastercard"}
_CLOSED_STAGES = {"Lost", "Non-qualified Partner", "Stop at this Stage"}

# The traffic sheet names providers the way the gateway does, not the way the
# book does. Every row here was checked by hand against the account list.
_TRAFFIC_ALIASES = {
    "amex": "American Express", "antom": "Ant Intl (Antom)", "bac credomatic": "BAC International Bank",
    "bamboo": "Bamboo Payments", "bci mach": "Banco BCI", "bradesco": "Banco Bradesco",
    "cybersource gtw": "Cybersource", "diners": "Diners Club", "evo": "Evo Payments",
    "fac": "FAC / Powertranz", "inovio": "Inovio Gateway", "itau": "Itau Unibanco", "klap 2": "Klap",
    "monnet": "Monnet Payments", "ntt data": "NTTD", "okto": "OKTO Payments",
    "paymentez": "Nuvei", "prisma": "PayWay / Prisma", "prosa iso": "Prosa",
    "redeban direct": "Redeban Colombia", "refacil": "Refácil", "santander": "Banco Santander BR",
    "unlimint": "Unlimit", "vr": "VR Beneficios", "zaincash": "Zain Cash",
}


@st.cache_data(show_spinner=False)
def load_tiering_framework():
    """Weights are the portal's; the tier gates can still be edited on the
    Framework sheet and land here."""
    w, cuts = dict(_TIER_WEIGHTS_DEFAULT), dict(_TIER_CUTS_DEFAULT)
    if not _TIERING_BOOK:
        return w, cuts, False
    try:
        fr = pd.read_excel(_TIERING_BOOK, sheet_name="Framework", header=None)
        for _, row in fr.iterrows():
            label = str(row[0]).strip().lower()
            if label in ("strategic", "tier 1", "tier 2"):
                try: cuts[str(row[0]).strip()] = float(row[1])
                except Exception: pass
        return w, cuts, True
    except Exception:
        return w, cuts, False


@st.cache_data(show_spinner=False)
def load_live_traffic():
    """approved_transactions per provider — the volume criterion's evidence."""
    if not _ACCOUNTS_BOOK:
        return {}
    try:
        t = pd.read_excel(_ACCOUNTS_BOOK, sheet_name="Partners Live Traffic (July 202", header=1)
        t.columns = [str(c).strip() for c in t.columns]
        out = {}
        for _, r in t.iterrows():
            name = str(r.get("provider", "")).strip()
            if not name or name.lower() == "nan":
                continue
            key = _norm_partner(name)
            key = _norm_partner(_TRAFFIC_ALIASES.get(key, key))
            try: out[key] = out.get(key, 0.0) + float(r.get("approved_transactions") or 0)
            except Exception: pass
        return out
    except Exception:
        return {}


# The account book and the scoring book spell some partners differently.
_PARTNER_ALIASES = {
    "checkout.com": "checkout", "checkoutcom": "checkout",
    "paypal": "paypal / braintree", "braintree": "paypal / braintree",
    "elavon .": "elavon", "kount equifax": "kount",
    "mercado pago": "mercadopago", "nuvei/paymentez": "nuvei",
}


def _norm_partner(name):
    import re, unicodedata
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = s.strip().lower().replace("_", " ").replace("-", " ")
    s = re.sub(r"[^a-z0-9 /.]", "", s)
    s = re.sub(r"\b(inc|ltd|llc|s\.?a\.?|sas|gmbh|corp|co|the)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return _PARTNER_ALIASES.get(s, s)


def _b(v):
    return str(v).strip().lower() in ("true", "1", "1.0", "yes", "y")


def _score_volume(approved):
    """0–5 from the rubric's monthly bands, applied to approved transactions."""
    if approved <= 0:            return 0, "zero approved transactions"
    if approved < 100_000:       return 1, f"{approved:,.0f} approved — trace"
    if approved < 1_000_000:     return 2, f"{approved:,.0f} approved — small but recurring"
    if approved < 10_000_000:    return 3, f"{approved:,.0f} approved — meets minimum"
    if approved < 100_000_000:   return 4, f"{approved:,.0f} approved — large, growing"
    return 5, f"{approved:,.0f} approved — dominant on book"


def _is_finx(row, ptype):
    if ptype in _FINX_TYPES:
        return True
    blob = " ".join(str(row.get(c, "")) for c in ("Type", "Classification", "ICP", "Comments")).lower()
    return any(wd in blob for wd in _FINX_WORDS)


def _score_market(row, key):
    """External market weight — the rubric's 'dominant global' to 'niche'."""
    if key in _MUST_HAVE:  return 5, "named must-have · dominant global provider"
    cls = str(row.get("Classification", "")).strip().lower()
    tier = str(row.get("Tier", "")).strip()
    if "global" in cls:    return 4, "global provider"
    if "regional" in cls:  return 3, "regional leader"
    if tier in ("T1", "Strategic"): return 3, f"{tier} on file"
    if "country" in cls:   return 2, "notable in-country player"
    if "niche" in cls or "product" in cls: return 1, "niche / product partner"
    return 0, "minimal scale on record"


def _score_stage(stage, integ, approved):
    """Deal / integration stage — can Yuno sell through this rail today."""
    if stage in _CLOSED_STAGES:              return 0, f"{stage.lower()}"
    live = integ == "live"
    if live and stage == "Agreement Signed":
        if approved >= 10_000_000:           return 5, "live, signed, fully scaled"
        if approved >= _SIGNIFICANT_VOLUME:  return 4, "live, signed, deeply embedded"
        if approved > 0:                     return 3, "live, signed, operationally embedded"
        return 2, "live and signed, early activity"
    if live:                                 return 2, f"live · {stage.lower() or 'no agreement'}"
    if stage == "Agreement Signed":          return 1, "signed, not live"
    return 0, stage.lower() or "not signed"


def _score_cosell(row, lead_source, ptype, integ, approved):
    """Co-sell / referral — will this partner send merchants to Yuno."""
    upsell, crossbeam = _b(row.get("Upsell Y/N")), _b(row.get("Crossbeam?"))
    flags = int(upsell) + int(crossbeam)
    if flags == 2 and lead_source: return 5, "two-way, structural — lead source with Crossbeam and referral programme"
    if flags == 2:                 return 4, "two-way, regular — Crossbeam-backed referral programme"
    if flags and lead_source:      return 4, "lead source with a referral motion"
    if lead_source:                return 3, "lead source — merchants come through this rail"
    if flags:                      return 2, "one-way, structural" if upsell else "Crossbeam only"
    if ptype in ("Acquirer", "PSP/Aggregator") and integ == "live" and approved > 0:
        return 1, "live rail, referrals ad hoc at best"
    return 0, "no referral motion"


def _score_upsell(finx, integ, stage):
    """Upsell potential — a FinX rail with a contract and an integration to sell against."""
    if not finx:
        return 0, "not a FinX rail — nothing to upsell through"
    if stage in _CLOSED_STAGES:            return 1, f"FinX rail, but {stage.lower()}"
    if integ == "live" and stage == "Agreement Signed": return 5, "FinX rail, signed and live — sell now"
    if integ == "live":                    return 4, "FinX rail, live"
    if stage == "Agreement Signed":        return 3, "FinX rail, signed — live next"
    if stage in ("Agreement Review", "Initial Negotiation"): return 2, f"FinX rail, {stage.lower()}"
    return 1, "FinX rail, not yet engaged"


@st.cache_data(show_spinner=False)
def run_tiering():
    """Score every account, then consolidate to one row per partner. Regional
    accounts (Checkout, Checkout BR, Checkout MENA…) are scored individually and
    the partner takes its strongest account's score; owners and regions are
    pooled so nothing is lost, and the tier on file is the highest one recorded."""
    if not _ACCOUNTS_BOOK:
        return [], {}, {}
    _, cuts, from_book = load_tiering_framework()
    w = dict(_TIER_WEIGHTS_DEFAULT)   # weights live in code; the sheet only sets the gates
    traffic = load_live_traffic()
    df = pd.read_excel(_ACCOUNTS_BOOK, sheet_name="All Partners")
    df = df[df["Partner Name"].notna()]
    df["_acct"] = df["Account Name"].where(df["Account Name"].notna(), df["Partner Name"])
    df = df.drop_duplicates(subset=["_acct"])

    rows = []
    for _, r in df.iterrows():
        partner = str(r["Partner Name"]).strip()
        name = str(r["_acct"]).strip()
        key = _norm_partner(partner)
        approved = traffic.get(key, 0.0)
        ptype = str(r.get("Type", "") or "—").strip()
        integ = str(r.get("Integration Stage", "") or "—").strip()
        stage = str(r.get("Deal Stage", "") or "—").strip()
        scheme = key in _SCHEME_LEAD_SOURCES
        finx = _is_finx(r, ptype) or scheme
        lead_source = scheme or (ptype == "Acquirer" and integ.lower() == "live"
                                 and approved >= _SIGNIFICANT_VOLUME)

        sv, wv = _score_volume(approved)
        sm, wm = _score_market(r, key)
        sc, wc = _score_cosell(r, lead_source, ptype, integ.lower(), approved)
        ss, ws = _score_stage(stage, integ.lower(), approved)
        su, wu = _score_upsell(finx, integ.lower(), stage)
        score = (sv * w["volume"] + sm * w["market"] + sc * w["cosell"]
                 + ss * w["stage"] + su * w["upsell"]) / 5.0
        if score >= cuts["Strategic"]:   computed = "Strategic"
        elif score >= cuts["Tier 1"]:    computed = "Tier 1"
        elif score >= cuts["Tier 2"]:    computed = "Tier 2"
        else:                            computed = "Tier 3"
        # No lift for must-haves: the score decides the tier, the manual table is
        # the only override. Market weight still credits the named providers.
        override = False
        rows.append({
            "name": name, "partner": partner, "key": key,
            "region": str(r.get("Region", "") or "—"),
            "country": str(r.get("Country", "") or "—"),
            "type": ptype, "stage": stage, "integration": integ,
            "manager": str(r.get("Partner Manager", "") or "Unassigned"),
            "current_tier": str(r.get("Tier", "") or "—"),
            "approved": approved,
            "finx": finx, "lead_source": lead_source, "must_have": key in _MUST_HAVE,
            "focus": ("Merchant lead source · FinX upsell" if lead_source
                      else "FinX upsell" if finx else "—"),
            "criteria": [
                ("Yuno volume & growth",        sv, w["volume"], wv),
                ("External market weight",      sm, w["market"], wm),
                ("Co-sell / referral",          sc, w["cosell"], wc),
                ("Deal / integration stage",    ss, w["stage"], ws),
                ("Upsell potential (FinX)",     su, w["upsell"], wu),
            ],
            "score": score, "computed": computed, "scored_by": "derived", "note": "",
            "override": override, "final": "Strategic" if override else computed, "seat": None,
        })
    # ── One row per partner ──────────────────────────────────────────────────
    placements = load_placements()
    by_partner = {}
    for r in rows:
        by_partner.setdefault(r["key"], []).append(r)
    merged = []
    for key, group in by_partner.items():
        best = max(group, key=lambda r: (r["score"], r["integration"].lower() == "live",
                                         r["stage"] == "Agreement Signed"))
        owners, regions, accounts = [], [], []
        for g in group:
            for o in split_managers(g["manager"]):
                if o not in owners: owners.append(o)
            if g["region"] not in regions: regions.append(g["region"])
            accounts.append(g["name"])
        on_file = max((str(g["current_tier"]).strip() for g in group),
                      key=lambda t: _TIER_RANK.get(_TIER_NORM.get(t, t), -1))
        row = dict(best)
        row["name"] = best["partner"]
        row["accounts"] = accounts
        row["scored_account"] = best["name"]
        row["region"] = "Global" if "Global" in regions else " / ".join(regions)
        row["manager"] = ", ".join(owners) if owners else best["manager"]
        row["current_tier"] = on_file
        row["finx"] = any(g["finx"] for g in group)
        row["lead_source"] = any(g["lead_source"] for g in group)
        row["focus"] = ("Merchant lead source · FinX upsell" if row["lead_source"]
                        else "FinX upsell" if row["finx"] else "—")
        placed = placements.get(key)
        row["manual"] = placed["tier"] if placed else None
        row["placed_by"] = placed.get("by", "") if placed else ""
        row["placed_when"] = placed.get("when", "") if placed else ""
        if row["manual"]:
            row["final"] = row["manual"]
        merged.append(row)
    merged.sort(key=lambda x: -x["score"])
    return merged, w, cuts


def tier_split(rows):
    out = {t: [] for t in ("Strategic", "Tier 1", "Tier 2", "Tier 3")}
    for r in rows:
        out[r["final"]].append(r)
    return out


# ══ Partner Alliance — who is at the door ══════════════════════════════════════
# A partner signs in with a work address. The domain is matched against the
# partner book to answer one question: are they actually a partner? The answer
# decides what they see, and an unrecognised provider raises an alert rather than
# being quietly let in or quietly turned away.

# Deal stages, grouped by what they mean for access.
_STAGE_PARTNER = {"Agreement Signed", "Only Integrated", "Only to be Integrated"}
_STAGE_PROSPECT = {"Agreement Review", "Initial Negotiation", "Opportunity Identification"}
_STAGE_CLOSED = {"Lost", "Stop at this Stage", "Non-qualified Partner"}

# Domains that belong to no single partner, so they can never identify one.
_PUBLIC_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "icloud.com", "me.com", "proton.me", "protonmail.com", "aol.com",
    "qq.com", "163.com", "gmx.com", "mail.com", "zoho.com", "yandex.com",
}


@st.cache_data(show_spinner=False)
def load_partner_directory():
    """domain → partner, built from the AM emails in the accounts workbook."""
    if not _ACCOUNTS_BOOK:
        return {}, {}
    accounts = {}
    try:
        df = pd.read_excel(_ACCOUNTS_BOOK, sheet_name="All Partners")
        df = df[df["Partner Name"].notna()].drop_duplicates(subset=["Partner Name"])
        for _, r in df.iterrows():
            name = str(r["Partner Name"]).strip()
            accounts[_norm_partner(name)] = {
                "name": name,
                "account": str(r.get("Account Name", "") or name),
                "region": str(r.get("Region", "") or "—"),
                "country": str(r.get("Country", "") or "—"),
                "tier": str(r.get("Tier", "") or "—"),
                "type": str(r.get("Type", "") or "—"),
                "stage": str(r.get("Deal Stage", "") or "—"),
                "integration": str(r.get("Integration Stage", "") or "—"),
                "manager": str(r.get("Partner Manager", "") or "Unassigned"),
                "classification": str(r.get("Classification", "") or "—"),
            }
    except Exception:
        return {}, {}

    domains = {}
    try:
        c = pd.read_excel(_ACCOUNTS_BOOK, sheet_name="Partnerships Contacts")
        for _, r in c.iterrows():
            email = str(r.get("AM Email", "") or "").strip().lower()
            pname = str(r.get("Partner Name", "") or "").strip()
            if "@" not in email or not pname:
                continue
            dom = email.rsplit("@", 1)[-1].strip().strip(".")
            if not dom or dom in _PUBLIC_DOMAINS:
                continue
            key = _norm_partner(pname)
            if key in accounts:
                domains.setdefault(dom, key)
    except Exception:
        pass
    return domains, accounts


def resolve_partner(email):
    """Identify the company behind a work address, and say how confident we are.

    status is one of: partner · prospect · closed · unknown · public
    """
    domains, accounts = load_partner_directory()
    addr = (email or "").strip().lower()
    if "@" not in addr:
        return {"status": "unknown", "domain": "", "company": "", "account": None, "via": "no address"}
    dom = addr.rsplit("@", 1)[-1].strip().strip(".")

    if dom in _PUBLIC_DOMAINS:
        return {"status": "public", "domain": dom, "company": "", "account": None,
                "via": "public mailbox — cannot identify a company"}

    key = domains.get(dom)
    via = "AM email domain"
    if not key:
        # Fall back to the domain's own second-level label against partner names.
        label = _norm_partner(dom.rsplit(".", 2)[0] if dom.count(".") > 1 else dom.split(".")[0])
        if label in accounts:
            key, via = label, "domain name matches a partner account"
        else:
            for k in accounts:
                if k and (k == label or (len(label) > 4 and label in k.split())):
                    key, via = k, "domain name matches a partner account"
                    break

    if not key:
        guess = dom.split(".")[0].replace("-", " ").title()
        return {"status": "unknown", "domain": dom, "company": guess, "account": None,
                "via": "no account in the partner book"}

    acct = accounts[key]
    stage = acct["stage"]
    status = ("partner" if stage in _STAGE_PARTNER else
              "prospect" if stage in _STAGE_PROSPECT else
              "closed" if stage in _STAGE_CLOSED else "prospect")
    return {"status": status, "domain": dom, "company": acct["name"], "account": acct, "via": via}


# ── Alerting ──────────────────────────────────────────────────────────────────
_ALERT_LOG = _os.path.join(_BASE, "data", "unrecognised_providers.jsonl")


def _slack_config():
    """Webhook or bot token + channel, from .streamlit/secrets.toml."""
    try:
        sl = st.secrets["slack"]
        return (sl.get("webhook_url", ""), sl.get("bot_token", ""),
                sl.get("channel", "#partnerships-only-visibility-integrations"))
    except Exception:
        return "", "", "#partnerships"


def alert_unrecognised_provider(res, email):
    """Tell the partnerships channel that an unknown provider tried to sign in.

    Always writes the local log first, so the signal survives even when Slack is
    unconfigured or the call fails — an alert that vanishes silently is worse
    than no alert.
    """
    import json as _json, datetime as _dt
    record = {
        "ts": _dt.datetime.utcnow().isoformat() + "Z",
        "email_domain": res["domain"],
        "company_guess": res["company"],
        "status": res["status"],
        "reason": res["via"],
    }
    delivered, detail = False, ""
    try:
        with open(_ALERT_LOG, "a") as f:
            f.write(_json.dumps(record) + "\n")
    except Exception as e:
        detail = f"log write failed: {e}"

    webhook, token, channel = _slack_config()
    text = (f":warning: *Unrecognised provider at the Partner Portal door*\n"
            f"*Domain:* `{res['domain']}`   *Best guess:* {res['company'] or '—'}\n"
            f"*Why flagged:* {res['via']}\n"
            f"Not in `Partnerships Accounts` — worth a look before they are turned away.")
    if webhook:
        try:
            import urllib.request as _u
            req = _u.Request(webhook, data=_json.dumps({"text": text}).encode(),
                             headers={"Content-Type": "application/json"})
            _u.urlopen(req, timeout=5).read()
            delivered, detail = True, f"posted to {channel}"
        except Exception as e:
            detail = f"Slack webhook failed: {e}"
    elif token:
        try:
            import urllib.request as _u
            req = _u.Request("https://slack.com/api/chat.postMessage",
                             data=_json.dumps({"channel": channel, "text": text}).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {token}"})
            resp = _json.loads(_u.urlopen(req, timeout=5).read().decode())
            delivered = bool(resp.get("ok"))
            detail = f"posted to {channel}" if delivered else f"Slack API: {resp.get('error')}"
        except Exception as e:
            detail = f"Slack API failed: {e}"
    else:
        detail = "no Slack credentials configured — logged locally only"
    return delivered, detail, channel



# ── Lead routing and alerting ─────────────────────────────────────────────────
# Every lead that arrives is announced once, to one channel, with a named BDM
# already on it. The assignment is deterministic so two people never think the
# same lead is theirs — and so nobody has to chase who owns it.

_LEAD_LOG = _os.path.join(_BASE, "data", "lead_alerts.jsonl")


def leads_channel():
    """The channel lead alerts post to. Secrets win over the checked-in default."""
    try:
        return st.secrets["slack"].get("leads_channel", _RT.LEADS_CHANNEL)
    except Exception:
        return _RT.LEADS_CHANNEL


def _mention(person):
    """A Slack mention when we hold a handle, the plain name when we do not."""
    h = (person.get("handle") or "").strip()
    if not h:
        return person["name"]
    if h.startswith("U") or h.startswith("S"):
        return f"<@{h}>" if h.startswith("U") else f"<!subteam^{h}>"
    return h if h.startswith("@") else f"@{h}"


def gm_for_region(region):
    """The GM called out by name on this lead. Every GM sees the channel post."""
    r = (region or "").strip()
    for gm in _RT.GMS:
        if r in gm["regions"]:
            return gm
    return next((g for g in _RT.GMS if "Global" in g["regions"]), _RT.GMS[0])


def assign_bdm(region, _counter=None):
    """Route by region, round-robin where two BDMs share one.

    The counter lives in session state so repeated leads into the same region
    alternate rather than all landing on the first name in the list.
    """
    r = (region or "").strip()
    pool = _RT.REGION_ROUTING.get(r, [])
    by_key = {b["key"]: b for b in _RT.BDMS}
    if not pool:
        return by_key.get(_RT.FALLBACK_BDM, _RT.BDMS[0]), True
    if len(pool) == 1:
        return by_key[pool[0]], False
    n = st.session_state.get(f"_rr_{r}", 0)
    st.session_state[f"_rr_{r}"] = n + 1
    return by_key[pool[n % len(pool)]], False


def lead_alert_text(lead, bdm, gm, unrouted=False):
    """The message body. Plain text so it survives webhook and API alike."""
    note = f"\n> {lead['note']}" if lead.get("note") else ""
    routed = (f"  _no BDM covers {lead['region']} — routed to the fallback_"
              if unrouted else "")
    return (
        f":inbox_tray: *New {lead['track']} lead · {lead['name']}*\n"
        f"*Region:* {lead['region']}   *Source:* {lead['source']}\n"
        f"*Assigned BDM:* {_mention(bdm)}{routed}\n"
        f"*Regional GM:* {_mention(gm)}\n"
        f"*First contact due:* within {_RT.SLA_HOURS}h of now{note}")


def lead_alert_blocks(lead, bdm, gm, unrouted=False):
    """Block Kit version — the same message, laid out."""
    fields = [("Track", lead["track"]), ("Region", lead["region"]),
              ("Source", lead["source"]), ("Assigned BDM", _mention(bdm)),
              ("Regional GM", _mention(gm)),
              ("First contact", f"within {_RT.SLA_HOURS}h")]
    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": f"New {lead['track']} lead · {lead['name']}"}},
        {"type": "section",
         "fields": [{"type": "mrkdwn", "text": f"*{k}*\n{v}"} for k, v in fields]},
    ]
    if unrouted:
        blocks.append({"type": "context", "elements": [
            {"type": "mrkdwn",
             "text": f":warning: No BDM covers {lead['region']} — routed to the fallback."}]})
    if lead.get("note"):
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn", "text": f">{lead['note']}"}})
    return blocks


def post_lead_alert(lead, bdm, gm, unrouted=False, channel=None):
    """Log it, then post it. The log is written first so the signal survives a
    Slack outage or a portal running without credentials."""
    import json as _json, datetime as _dt
    channel = channel or leads_channel()
    record = {"ts": _dt.datetime.utcnow().isoformat() + "Z", "channel": channel,
              "assigned": bdm["name"], "gm": gm["name"], "unrouted": unrouted, **lead}
    try:
        with open(_LEAD_LOG, "a") as f:
            f.write(_json.dumps(record) + "\n")
    except Exception as e:
        return False, f"log write failed: {e}", channel

    text = lead_alert_text(lead, bdm, gm, unrouted)
    blocks = lead_alert_blocks(lead, bdm, gm, unrouted)
    webhook, token, _ = _slack_config()
    if webhook:
        try:
            import urllib.request as _u
            payload = {"text": text, "blocks": blocks}
            req = _u.Request(webhook, data=_json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"})
            _u.urlopen(req, timeout=5).read()
            return True, f"posted to {channel}", channel
        except Exception as e:
            return False, f"Slack webhook failed: {e}", channel
    if token:
        try:
            import urllib.request as _u
            payload = {"channel": channel, "text": text, "blocks": blocks}
            req = _u.Request("https://slack.com/api/chat.postMessage",
                             data=_json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {token}"})
            resp = _json.loads(_u.urlopen(req, timeout=5).read().decode())
            ok = bool(resp.get("ok"))
            return ok, (f"posted to {channel}" if ok else f"Slack API: {resp.get('error')}"), channel
        except Exception as e:
            return False, f"Slack API failed: {e}", channel
    return False, "no Slack credentials configured — logged locally only", channel


def recent_lead_alerts(n=12):
    import json as _json
    try:
        with open(_LEAD_LOG) as f:
            rows = [_json.loads(x) for x in f if x.strip()]
    except Exception:
        return []
    return list(reversed(rows))[:n]


# ── Market profiles ────────────────────────────────────────────────────────────
# Shared by Market Intel and the Market Expansion simulator — one source, so a
# figure quoted on one page cannot drift from the same figure on the other.
_MARKET_PROFILES = {
    "Brazil": {
        "flag":"🇧🇷","population":"216M","gdp":"$2.17T","ecom_size":"$62B (2025)",
        "payment_methods":[("PIX",40),("Credit Card",30),("Boleto Bancario",15),("Debit Card",10),("Other",5)],
        "top_acquirers":"Cielo, Rede (Itau), Getnet (Santander), Stone, PagSeguro, Adyen",
        "regulatory":"Central Bank regulates PIX. Open Finance mandate in effect. PIX credit launching Q2 2026. Data localization not required but LGPD (data privacy) applies to all payment data.",
        "settlement":"PIX: instant. Cards: D+1 to D+30 (negotiable). Boleto: D+1 after payment confirmation.",
        "fx":"BRL is not freely convertible. Central Bank controls FX. Merchants must use authorized dealers. IOF tax (up to 6.38%) applies to cross-border transactions.",
        "instore_online":"Online 48% / In-store 52%. PIX rapidly gaining in-store share via QR code.",
    },
    "Mexico": {
        "flag":"🇲🇽","population":"130M","gdp":"$1.79T","ecom_size":"$38B (2025)",
        "payment_methods":[("Credit Card",32),("Debit Card",28),("OXXO (cash voucher)",18),("SPEI/CoDi",12),("Digital Wallets",10)],
        "top_acquirers":"BBVA Mexico, Banorte, Conekta, Stripe, Mercado Pago, Kushki",
        "regulatory":"Banxico regulates payment systems. CoDi (instant payments) push. Fintech Law (Ley Fintech) governs digital payments. CNBV oversees PSPs.",
        "settlement":"Cards: D+1 to D+3. SPEI: instant (banking hours). OXXO: D+1 after cash payment.",
        "fx":"MXN is freely traded. No FX restrictions for merchants. Withholding tax on cross-border payments may apply (ISR).",
        "instore_online":"Online 38% / In-store 62%. Cash-based methods (OXXO) remain critical for unbanked population (~45%).",
    },
    "Colombia": {
        "flag":"🇨🇴","population":"52M","gdp":"$363B","ecom_size":"$12B (2025)",
        "payment_methods":[("Credit Card",30),("PSE (bank transfer)",28),("Debit Card",18),("Cash (Efecty/Baloto)",15),("Digital Wallets",9)],
        "top_acquirers":"Redeban, Credibanco, Kushki, Mercado Pago, PayU, Addi (BNPL)",
        "regulatory":"Superintendencia Financiera oversees payments. Transfiya 2.0 (instant payments) launched 2026. GMF tax (4x1000) on financial transactions.",
        "settlement":"Cards: D+1 to D+7. PSE: D+1. Cash vouchers: D+1 after confirmation.",
        "fx":"COP has managed float. Central bank approval needed for large FX transactions. Repatriation of funds possible but requires documentation.",
        "instore_online":"Online 32% / In-store 68%. Cash on delivery still significant in tier-2 cities.",
    },
    "Argentina": {
        "flag":"🇦🇷","population":"46M","gdp":"$641B","ecom_size":"$14B (2025)",
        "payment_methods":[("Credit Card (installments)",38),("Debit Card",25),("Bank Transfer",15),("Digital Wallets",14),("Cash (Rapipago/PagoFacil)",8)],
        "top_acquirers":"Prisma (Visa), First Data (MC), Mercado Pago, Ualá, Modo",
        "regulatory":"BCRA regulates payments. Installment plans (cuotas) are culturally essential. Capital controls (cepo) restrict FX. DEBIN for instant debits.",
        "settlement":"Cards: D+10 to D+18 standard (accelerated available at cost). Bank transfers: D+0 to D+1.",
        "fx":"Strict capital controls. Multiple exchange rates (official, MEP, CCL). Cross-border settlement is complex. Merchants must navigate BCRA restrictions.",
        "instore_online":"Online 40% / In-store 60%. Installment-based credit card payments dominate eCommerce.",
    },
    "Chile": {
        "flag":"🇨🇱","population":"19.5M","gdp":"$335B","ecom_size":"$12B (2025)",
        "payment_methods":[("Debit Card",35),("Credit Card",30),("Bank Transfer (Khipu)",18),("Prepaid Cards",10),("Cash",7)],
        "top_acquirers":"Transbank, Getnet, Kushki, Mercado Pago, Flow",
        "regulatory":"CMF oversees financial regulation. Transbank monopoly broken by four-party model reform. New PSP licensing framework in place since 2022.",
        "settlement":"Cards: D+1 to D+2. Khipu: instant/D+1. Transbank: D+2 standard.",
        "fx":"CLP is freely traded. No significant FX restrictions. Chile has bilateral trade agreements reducing friction for cross-border commerce.",
        "instore_online":"Online 42% / In-store 58%. Debit cards overtook credit cards as primary online method in 2024.",
    },
    "India": {
        "flag":"🇮🇳","population":"1.44B","gdp":"$3.94T","ecom_size":"$120B (2025)",
        "payment_methods":[("UPI",48),("Credit Card",15),("Debit Card",14),("Net Banking",10),("Wallets (Paytm, PhonePe)",8),("Cash on Delivery",5)],
        "top_acquirers":"Razorpay, Cashfree, PayU India, CCAvenue, Juspay, Pine Labs (in-store)",
        "regulatory":"RBI regulates all payments. Zero MDR on UPI (under review). Data localization mandate — all payment data must be stored in India. Recurring payment framework (e-mandate) in effect.",
        "settlement":"UPI: instant. Cards: T+1 to T+3. Net Banking: T+1 to T+2.",
        "fx":"INR is partially convertible. RBI controls capital account. FEMA regulations govern cross-border payments. LRS limit of $250K/year for individuals.",
        "instore_online":"Online 35% / In-store 65%. UPI QR codes dominate in-store. 15B+ monthly UPI transactions as of 2026.",
    },
    "Indonesia": {
        "flag":"🇮🇩","population":"278M","gdp":"$1.42T","ecom_size":"$62B (2025)",
        "payment_methods":[("Digital Wallets (GoPay, OVO, Dana)",35),("Bank Transfer (VA)",28),("Credit Card",12),("QRIS (QR standard)",15),("Convenience Store",10)],
        "top_acquirers":"Midtrans (GoTo), Xendit, DOKU, Nicepay, Ayoconnect",
        "regulatory":"Bank Indonesia oversees payments. QRIS is the national QR standard. PBI regulations on payment systems. Local processing requirement for domestic transactions.",
        "settlement":"Bank transfers: instant (BI-FAST). Cards: D+2 to D+7. E-wallets: D+1.",
        "fx":"IDR is managed float. BI approval needed for large transfers. Repatriation rules apply. Withholding tax on cross-border digital services.",
        "instore_online":"Online 40% / In-store 60%. QRIS unifying fragmented QR code market. E-wallet adoption among highest in Southeast Asia.",
    },
    "UAE": {
        "flag":"🇦🇪","population":"10M","gdp":"$509B","ecom_size":"$10B (2025)",
        "payment_methods":[("Credit Card",40),("Debit Card",22),("Apple Pay / Samsung Pay",18),("AANI (instant)",10),("Cash on Delivery",10)],
        "top_acquirers":"Network International, Checkout.com, Tap Payments, Amazon Payment Services, Telr",
        "regulatory":"CBUAE regulates payments. AANI instant payment system launched nationwide 2026. Strong AML/KYC requirements. UAE PASS digital identity integration for onboarding.",
        "settlement":"Cards: D+1 to D+3. AANI: instant. COD reconciliation: D+1 to D+5.",
        "fx":"AED is pegged to USD (3.6725). No FX restrictions. Free zones offer simplified cross-border payment structures. No income tax; 9% corporate tax introduced 2023.",
        "instore_online":"Online 45% / In-store 55%. Contactless penetration among highest globally (>80% of in-store card transactions).",
    },
    "Saudi Arabia": {
        "flag":"🇸🇦","population":"36M","gdp":"$1.07T","ecom_size":"$16B (2025)",
        "payment_methods":[("Mada (debit)",45),("Credit Card",25),("STC Pay",12),("Apple Pay",10),("SADAD / BNPL (Tamara, Tabby)",8)],
        "top_acquirers":"Neoleap, Geidea, HyperPay, Moyasar, Tap Payments, Checkout.com",
        "regulatory":"SAMA regulates payments. Mada scheme mandatory for all domestic debit. BNPL framework introduced 2023. Open Banking launched. Vision 2030 driving cashless push — targeting 70% non-cash by 2025.",
        "settlement":"Mada: D+1. Credit cards: D+2 to D+5. STC Pay: D+1.",
        "fx":"SAR pegged to USD (3.75). No FX restrictions. Straightforward repatriation. ZATCA manages VAT (15%) compliance.",
        "instore_online":"Online 38% / In-store 62%. Mada contactless payments growing rapidly. NFC penetration > 70%.",
    },
    "Nigeria": {
        "flag":"🇳🇬","population":"224M","gdp":"$477B","ecom_size":"$8B (2025)",
        "payment_methods":[("Bank Transfer",35),("Cards (Verve, Visa, MC)",25),("USSD",18),("Mobile Money",12),("eNaira / Cash",10)],
        "top_acquirers":"Paystack (Stripe), Flutterwave, Interswitch, Kuda, Moniepoint",
        "regulatory":"CBN regulates payments. eNaira (CBDC) in circulation. Cashless policy enforced. Verve is the dominant local card scheme. PSB (Payment Service Bank) licenses expanding mobile money.",
        "settlement":"Bank transfers: instant (NIP). Cards: D+1. USSD: D+1. Mobile money: instant.",
        "fx":"NGN has unified floating rate (post-2023 reform). FX liquidity challenges persist. Repatriation can be delayed. Parallel market premiums have narrowed post-reform.",
        "instore_online":"Online 30% / In-store 70%. USSD payments critical for feature-phone users. Bank transfers growing fastest.",
    },
    "South Africa": {
        "flag":"🇿🇦","population":"62M","gdp":"$399B","ecom_size":"$7.5B (2025)",
        "payment_methods":[("Credit Card",30),("Debit Card",25),("EFT (bank transfer)",22),("Instant EFT (Ozow, Stitch)",15),("Cash / Voucher",8)],
        "top_acquirers":"Nedbank, Standard Bank, Peach Payments, PayFast (Takealot), Ozow, Stitch",
        "regulatory":"SARB and PASA regulate payments. National Payment System Act. Strong consumer protection via NCA. PayShap instant payment system launched 2023.",
        "settlement":"Cards: D+1 to D+3. EFT: D+1 to D+2. Instant EFT: D+0. PayShap: instant.",
        "fx":"ZAR is freely traded. Excon rules apply to cross-border flows. Loop structures available for multinationals. Withholding tax on royalties/services.",
        "instore_online":"Online 32% / In-store 68%. Instant EFT growing rapidly as card alternative. Tap-to-phone pilots expanding.",
    },
    "UK": {
        "flag":"🇬🇧","population":"68M","gdp":"$3.34T","ecom_size":"$170B (2025)",
        "payment_methods":[("Debit Card",42),("Credit Card",25),("Open Banking / FPS",12),("Digital Wallets",15),("BNPL (Klarna, Clearpay)",6)],
        "top_acquirers":"Worldpay, Adyen, Stripe, Barclays Payments, Checkout.com, Trust Payments",
        "regulatory":"FCA and PSR regulate payments. Strong Consumer Duty (2023). Open Banking well-established (9M+ users). SCA enforced under UK-retained PSD2. BNPL regulation pending.",
        "settlement":"Faster Payments: instant. Cards: D+1 to D+3. BACS: D+3.",
        "fx":"GBP is freely traded. No restrictions. London is global FX hub. Cross-border payments straightforward. Interchange capped at 0.2% debit / 0.3% credit.",
        "instore_online":"Online 52% / In-store 48%. Contactless limit raised to £100. Open Banking payments accelerating for eCommerce.",
    },
    "Germany": {
        "flag":"🇩🇪","population":"84M","gdp":"$4.46T","ecom_size":"$130B (2025)",
        "payment_methods":[("PayPal",28),("Invoice/Kauf auf Rechnung",20),("Credit Card",18),("SEPA Direct Debit",15),("Debit (girocard)",12),("SOFORT/Klarna",7)],
        "top_acquirers":"Adyen, Unzer, Computop, Worldline, Stripe, Payone",
        "regulatory":"BaFin and Bundesbank oversee payments. PSD2/SCA enforced. Strong data privacy (GDPR strictest interpretation). E-invoicing mandate from 2025.",
        "settlement":"SEPA: D+1. Cards: D+1 to D+3. Invoice: varies (14-30 days).",
        "fx":"EUR — no FX needed within eurozone. No restrictions for cross-border EUR payments. SEPA zone covers 36 countries.",
        "instore_online":"Online 45% / In-store 55%. Germany historically cash-heavy but post-COVID card/digital adoption surged. girocard dominates in-store.",
    },
    "France": {
        "flag":"🇫🇷","population":"68M","gdp":"$3.05T","ecom_size":"$95B (2025)",
        "payment_methods":[("Credit/Debit Card (CB)",45),("PayPal",15),("Bank Transfer (SEPA)",12),("Digital Wallets",10),("Cartes Bancaires",10),("BNPL / Cheque",8)],
        "top_acquirers":"Worldline, Adyen, Stripe, PayPlug, Dalenys (Natixis), Lyra",
        "regulatory":"ACPR/Banque de France regulate. PSD2/SCA enforced. Cartes Bancaires (CB) is mandatory co-badging on all French cards. DGCCRF consumer protection applies.",
        "settlement":"Cards: D+1 to D+2. SEPA Credit Transfer: D+1. SEPA Instant: seconds.",
        "fx":"EUR — no FX within eurozone. Interchange capped per EU regulation.",
        "instore_online":"Online 42% / In-store 58%. Carte Bancaire network processes majority of domestic transactions. Contactless widely adopted.",
    },
    "USA": {
        "flag":"🇺🇸","population":"335M","gdp":"$28.78T","ecom_size":"$1.14T (2025)",
        "payment_methods":[("Credit Card",38),("Debit Card",28),("Digital Wallets (Apple Pay, Google Pay)",16),("ACH/Bank Transfer",10),("BNPL",5),("Cash/Other",3)],
        "top_acquirers":"Chase Paymentech, Fiserv (First Data), Worldpay, Adyen, Stripe, Square, Braintree",
        "regulatory":"Federal Reserve, OCC, CFPB, and state regulators. Durbin amendment caps debit interchange. No federal data privacy law (state-level patchwork — CCPA, etc.). FedNow instant payment system live since 2023.",
        "settlement":"ACH: D+1 to D+2. FedNow: instant. Cards: D+1 to D+2. Wire: same-day.",
        "fx":"USD is global reserve currency. No FX restrictions. Straightforward cross-border settlement.",
        "instore_online":"Online 42% / In-store 58%. Contactless adoption growing but still below EU levels. Tap-to-pay at ~35% of in-store card transactions.",
    },
    "Canada": {
        "flag":"🇨🇦","population":"40M","gdp":"$2.14T","ecom_size":"$58B (2025)",
        "payment_methods":[("Credit Card",38),("Debit (Interac)",30),("Digital Wallets",14),("Bank Transfer (EFT)",10),("BNPL",5),("Cash",3)],
        "top_acquirers":"Moneris, Global Payments, Chase (Canada), Adyen, Stripe, Nuvei",
        "regulatory":"Bank of Canada and OSFI oversee payments. Payments Canada modernizing with RTR (Real-Time Rail). Interchange regulated. PIPEDA (privacy). Retail Payment Activities Act (2024).",
        "settlement":"Interac e-Transfer: instant. Cards: D+1 to D+2. EFT: D+1 to D+3. RTR (upcoming): instant.",
        "fx":"CAD is freely traded. No FX restrictions. Close integration with US financial system.",
        "instore_online":"Online 40% / In-store 60%. Interac Flash (contactless debit) very popular in-store. Interac Online for eCommerce.",
    },
    "Japan": {
        "flag":"🇯🇵","population":"125M","gdp":"$4.23T","ecom_size":"$180B (2025)",
        "payment_methods":[("Credit Card",40),("Convenience Store Payment (Konbini)",15),("Digital Wallets (PayPay, LinePay)",18),("Bank Transfer (Furikomi)",12),("Carrier Billing",8),("Cash",7)],
        "top_acquirers":"GMO Payment Gateway, SB Payment Service, Adyen, Stripe Japan, Paygent, DG Financial Technology",
        "regulatory":"FSA and Bank of Japan regulate. Cashless Vision targeting 40%+ cashless ratio (achieved ~39% in 2024). JCB is major domestic card scheme alongside Visa/MC. Installments (bunkatsu) culturally important.",
        "settlement":"Cards: D+15 to D+30 (monthly cycle typical). Bank transfer: D+0 to D+1. E-wallets: D+1 to D+15.",
        "fx":"JPY is freely traded. No FX restrictions. Japan has unique long settlement cycles for card payments that require planning.",
        "instore_online":"Online 38% / In-store 62%. IC card payments (Suica, PASMO) dominate transit/convenience. QR code wallets (PayPay) growing rapidly.",
    },
    "Singapore": {
        "flag":"🇸🇬","population":"5.9M","gdp":"$497B","ecom_size":"$9B (2025)",
        "payment_methods":[("Credit Card",38),("Debit Card",20),("PayNow (instant)",18),("Digital Wallets (GrabPay, ShopeePay)",15),("BNPL (Atome, Pace)",5),("NETS",4)],
        "top_acquirers":"Adyen, Stripe, 2C2P, Worldline, Rapyd, Nium",
        "regulatory":"MAS regulates payments. Payment Services Act (PS Act) covers all payment service providers. PayNow corporate expanding. SGQR unified QR standard. Strong AML framework.",
        "settlement":"PayNow: instant. Cards: D+1 to D+3. NETS: D+1. FAST: instant.",
        "fx":"SGD is managed float (MAS band). No FX restrictions. Singapore is Asian payments hub. Cross-border QR payments linked with Thailand (PromptPay) and India (UPI).",
        "instore_online":"Online 48% / In-store 52%. SGQR standardizes QR payments. Contactless card penetration > 85%.",
    },
    "Turkey": {
        "flag":"🇹🇷","population":"85M","gdp":"$1.11T","ecom_size":"$25B (2025)",
        "payment_methods":[("Credit Card (installments)",45),("Debit Card / BKM Express",20),("Bank Transfer (FAST/EFT)",18),("Digital Wallets",10),("Cash on Delivery",7)],
        "top_acquirers":"Iyzico (PayU), PayTR, Param, Craftgate, Stripe Turkey, Garanti BBVA",
        "regulatory":"CBRT and BRSA regulate payments. Installment payments deeply embedded (up to 12 months interest-free). BKM operates domestic card scheme (Troy). FAST instant payment system live.",
        "settlement":"Cards: D+1 to D+30 (installment cycles). FAST: instant. Bank transfer: D+0 to D+1.",
        "fx":"TRY is volatile. Central bank interventions frequent. FX-denominated pricing restricted for domestic transactions. Cross-border settlements can face delays. Withholding taxes apply.",
        "instore_online":"Online 35% / In-store 65%. Installment-based card payments are the norm for eCommerce. Troy card scheme growing domestically.",
    },
    "Egypt": {
        "flag":"🇪🇬","population":"106M","gdp":"$398B","ecom_size":"$8B (2025)",
        "payment_methods":[("Cash on Delivery",35),("Credit/Debit Card",22),("Mobile Wallets (Fawry, Vodafone Cash)",20),("Bank Transfer (InstaPay)",13),("Meeza (local scheme)",10)],
        "top_acquirers":"Fawry, Paymob, Accept (by Paymob), Kashier, ValU (BNPL), Amazon Payment Services",
        "regulatory":"CBE regulates payments. National Payment Council driving cashless. InstaPay instant transfer system. Meeza is the national card scheme. Mobile money regulations enabling wallet interoperability.",
        "settlement":"Cards: D+2 to D+7. InstaPay: instant. Mobile wallets: D+1 to D+2. COD: varies.",
        "fx":"EGP floated in 2022-2024 reforms. FX availability has improved but repatriation can still face delays. Letters of credit requirements eased. Central bank unified the exchange rate.",
        "instore_online":"Online 22% / In-store 78%. Cash on delivery remains dominant for eCommerce. Mobile wallet adoption accelerating among younger demographics.",
    },
}

# The rest of the world lives in data/market_profiles_extra.py — one table on
# screen, two files on disk so the long tail does not bury the core markets.
try:
    from market_profiles_extra import (MARKET_PROFILES_EXTRA as _MP_EXTRA,
                                       MARKET_REGION as _MARKET_REGION,
                                       MARKET_ISO_EXTRA as _ISO_EXTRA)
    for _k, _v in _MP_EXTRA.items():
        _MARKET_PROFILES.setdefault(_k, _v)
except Exception:
    _MARKET_REGION, _ISO_EXTRA = {}, {}
_REGION_ORDER = ["LATAM", "North America", "Europe", "Nordics", "MENA", "Africa", "APAC"]


PIPELINE_STAGES = {
    "Prospect":    {"color":"#858CA6","count":3},
    "Qualified":   {"color":"#8B94BC","count":3},
    "Evaluation":  {"color":"#8B9BFF","count":4},
    "Negotiation": {"color":"#D08A1A","count":2},
    "Won":         {"color":"#8FA300","count":2},
}

CONTACTS = [
    {"init":"TK","bg":"rgba(84,104,245,.2)","color":"#8B94BC","name":"Tom Kuehn","role":"Head of LATAM Partnerships","company":"Adyen · PSP","badge":"Champion","badge_class":"p-green","last":"2d ago","rel":"★★★★★","deals":"3 active"},
    {"init":"RV","bg":"rgba(209,78,0,.2)","color":"#8B9BFF","name":"Ricardo Vega","role":"VP Business Development","company":"Nuvei · PSP","badge":"Warm","badge_class":"p-amber","last":"5h ago","rel":"★★★★☆","deals":"1 active"},
    {"init":"AP","bg":"rgba(0,134,168,.2)","color":"#3FA8C4","name":"Ana Pacheco","role":"Strategic Partnerships Director","company":"Kushki · Acquirer","badge":"Active","badge_class":"p-blue","last":"1w ago","rel":"★★★★☆","deals":"2 active"},
    {"init":"FM","bg":"rgba(47,138,31,.2)","color":"#D08A1A","name":"Felipe Morales","role":"Head of Digital Products","company":"Getnet · Acquirer (Santander)","badge":"Executive Sponsor","badge_class":"p-green","last":"Today","rel":"★★★★★","deals":"1 at Negotiation"},
    {"init":"DH","bg":"rgba(196,24,127,.2)","color":"#D9737F","name":"Diana Herrera","role":"Fraud Partnerships Lead","company":"SEON · Fraud & Risk","badge":"Live Partner","badge_class":"p-green","last":"3d ago","rel":"★★★★☆","deals":"Integration live"},
    {"init":"MC","bg":"rgba(47,138,31,.2)","color":"#E6CE7A","name":"Martín Castillo","role":"CEO & Co-Founder","company":"Pomelo · BaaS","badge":"New Vertical","badge_class":"p-amber","last":"Yesterday","rel":"★★★☆☆","deals":"1 at Evaluation"},
]

# ── CSS ─────────────────────────────────────────────────────────────────────────
_STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');
:root {
  /* Surfaces — the blue-tinted neutrals from Yuno Alliance Mission Control */
  --bg:#EEF0FA; --bg2:#ffffff; --bg3:#F1F3FB; --bg4:#E2E6F4; --bg5:#D2D7EA;
  --sunk:rgba(35,42,61,.09);
  --border:rgba(35,42,61,.10); --border2:rgba(35,42,61,.16);

  /* Dark chrome — void / panel, straight from the reference */
  --void:#080911; --panel:#10131C; --panel2:#141827; --panel3:#191E2F;
  --panel-border:#232A3D; --panel-border-bright:#38415C;

  /* Ink */
  --text:#10131C; --text2:#4A5170; --text3:#676E8A;
  --text-dark:#EEF0FA; --text-dark2:#8991AC; --text-dark3:#565D78;

  /* Accent — Yuno electric blue. #5468F5 on dark, #3E4FE0 on light for contrast. */
  --indigo:#3E4FE0; --indigo-hover:#2F3FC4; --blue-bright:#5468F5; --blue-ink:#8B9BFF;
  --indigo-light:rgba(84,104,245,0.10); --indigo-mid:rgba(84,104,245,0.18);
  --ring:rgba(84,104,245,0.35); --blue-glow:rgba(84,104,245,0.5);

  /* Status — the reference's lime / coral / amber, stepped for a light ground */
  --green:#5A7A00; --green-bright:#E0ED80; --green-soft:rgba(224,237,128,.34);
  --amber:#B36200; --amber-bright:#FFD400; --amber-soft:rgba(255,212,0,.20);
  --red:#C4384A;   --red-bright:#FF6B7D;   --red-soft:rgba(255,107,125,.16);
  --standby:#676E8A; --standby-soft:rgba(103,110,138,.14);
  --blue:#5A6486; --blue-soft:rgba(90,100,134,.13);
  --purple:#3E4FE0; --teal:#0086A8;

  /* Categorical — re-validated for CVD separation against this surface */
  --c1:#3E4FE0; --c2:#C24E00; --c3:#0086A8;
  --c4:#2F8A1F; --c5:#C4187F; --c6:#6B6F00; --c7:#676E8A;

  --shadow:0 1px 1px rgba(16,19,28,.04),0 3px 10px rgba(16,19,28,.06);
  --shadow-md:0 2px 6px rgba(16,19,28,.07),0 14px 36px rgba(16,19,28,.10);
  --r-card:18px; --r-ctl:10px; --r-pill:999px;
  --ease:cubic-bezier(.32,.72,0,1);

  --font:'Geist','GeistSans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  --mono:'Geist Mono','GeistMono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
html,body,[class*="css"] {
  font-family:var(--font) !important;
  background-color:var(--bg) !important;
  color:var(--text) !important;
}
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding-top:2.5rem !important; padding-bottom:2.5rem !important; padding-left:2.5rem !important; padding-right:2.5rem !important; max-width:100% !important; background:var(--bg) !important; }
[data-testid="stAppViewContainer"] { background:var(--bg) !important; }
[data-testid="stAppViewContainer"] > section:nth-child(2) { background:var(--bg) !important; }
[data-testid="stMain"] { background:var(--bg) !important; }
.main { background:var(--bg) !important; }
section[data-testid="stMain"] > div { background:var(--bg) !important; }
[data-testid="stSidebar"] { background:#080911 !important; border-right:0.5px solid rgba(255,255,255,0.05) !important; }
[data-testid="stSidebar"] > div:first-child { padding:0 !important; }
/* Role toggle buttons (inside columns in sidebar) */
[data-testid="stSidebar"] [data-testid="column"] [data-testid="stButton"] > button {
  border-radius:20px !important; border:none !important; font-size:11px !important; font-weight:600 !important; padding:7px 12px !important;
}
[data-testid="stSidebar"] [data-testid="column"] [data-testid="stButton"] > button[data-testid="baseButton-primary"] {
  background:var(--indigo) !important; color:#fff !important;
}
[data-testid="stSidebar"] [data-testid="column"] [data-testid="stButton"] > button[data-testid="baseButton-secondary"] {
  background:transparent !important; color:var(--text3) !important;
}
/* Nav buttons (sidebar buttons NOT in columns) */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div > [data-testid="stButton"] > button {
  background:transparent !important; border:none !important; color:var(--text2) !important;
  text-align:left !important; justify-content:flex-start !important; border-radius:8px !important;
  font-size:14px !important; font-weight:400 !important; padding:10px 14px !important;
  display:flex !important; align-items:center !important; width:100% !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div > [data-testid="stButton"] > button:hover {
  background:var(--bg3) !important; color:var(--text) !important;
}
[data-testid="stSidebar"] button[data-nav-active="true"] {
  background:var(--indigo-light) !important; border-left:3px solid var(--indigo) !important;
  border-radius:0 8px 8px 0 !important; color:var(--indigo) !important; font-weight:600 !important; padding-left:11px !important;
}
[data-testid="stSidebar"] button[data-badge]::after {
  content:attr(data-badge); margin-left:auto; font-size:10px; font-family:var(--font);font-variant-numeric:tabular-nums;
  background:var(--bg3); color:var(--text3); padding:2px 7px; border-radius:10px; flex-shrink:0;
}
[data-testid="stSidebar"] button[data-nav-active="true"][data-badge]::after {
  background:var(--indigo-mid); color:var(--indigo);
}
[data-testid="stTextInput"] input { background:#fff !important; border:1px solid var(--border2) !important; color:var(--text) !important; border-radius:8px !important; font-family:var(--font) !important; font-size:14px !important; }
[data-testid="stTextInput"] input[type="password"] { background:#fff !important; color:var(--text) !important; -webkit-text-fill-color:var(--text) !important; caret-color:var(--text) !important; }
[data-testid="stTextInput"] input::placeholder { color:var(--text3) !important; }
[data-testid="stTextInput"] input:focus { border-color:var(--indigo) !important; box-shadow:0 0 0 3px rgba(84,104,245,0.12) !important; }
.stButton > button { background:#fff !important; color:var(--text2) !important; border:1px solid var(--border2) !important; border-radius:8px !important; font-family:var(--font) !important; font-weight:600 !important; font-size:14px !important; }
.stButton > button:hover { border-color:var(--indigo) !important; color:var(--indigo) !important; }
.stButton > button[data-testid="baseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
  background:var(--indigo) !important; color:#fff !important; border:1px solid var(--indigo) !important; }
[data-testid="stFormSubmitButton"] > button[kind="secondaryFormSubmit"] {
  background:#fff !important; color:var(--text2) !important;
  border:1px solid var(--border2) !important; }
[data-testid="stFormSubmitButton"] > button {
  border-radius:var(--r-ctl) !important; font-family:var(--font) !important;
  font-weight:500 !important; font-size:14px !important; }
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover {
  background:var(--indigo-hover) !important; border-color:var(--indigo-hover) !important; }
.stButton > button[data-testid="baseButton-primary"]:hover { background:#2F3FC4 !important; }
/* Streamlit's multiselect tags default to red — an alarm colour for a neutral chip. */
[data-baseweb="tag"] { background:var(--indigo) !important; border-radius:6px !important;
  font-family:var(--font) !important; font-size:11px !important; font-weight:500 !important; }
[data-baseweb="tag"] span, [data-baseweb="tag"] svg { color:#fff !important; fill:#fff !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div { border-radius:var(--r-ctl) !important; }
/* Segmented view switch (Connectors / Partner tiers) */
[data-testid="stMain"] [role="radiogroup"] { gap:6px !important; }
[data-testid="stMain"] [role="radiogroup"] label { border:1px solid rgba(0,0,0,.10) !important;
  border-radius:999px !important; padding:6px 15px !important; background:#fff !important;
  font-size:13px !important; transition:all .16s var(--ease) !important; }
[data-testid="stMain"] [role="radiogroup"] label:has(input:checked) {
  background:var(--indigo-light) !important; border-color:var(--indigo) !important; }
/* BaseWeb paints the radio/checkbox mark red by default. */
[role="radiogroup"] [data-baseweb="radio"] div[class]:first-child { background-color:transparent !important; }
[role="radiogroup"] [data-baseweb="radio"] > div:first-of-type > div:first-child {
  background-color:transparent !important; border-color:rgba(35,42,61,.28) !important; }
[role="radiogroup"] label:has(input:checked) [data-baseweb="radio"] > div:first-of-type > div:first-child {
  background-color:var(--indigo) !important; border-color:var(--indigo) !important; }
[role="radiogroup"] [data-baseweb="radio"] div[data-testid] { background:transparent !important; }
[data-testid="stCheckbox"] input:checked + div,
[data-baseweb="checkbox"] input:checked + span { background-color:var(--indigo) !important;
  border-color:var(--indigo) !important; }
.pill{display:inline-flex;align-items:center;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:var(--font);font-variant-numeric:tabular-nums;letter-spacing:.2px;white-space:nowrap;}
.p-green{background:rgba(90,107,0,.1);color:#48610A;}
.p-blue{background:rgba(90,100,134,.1);color:#464F6E;}
.p-amber{background:rgba(138,106,0,.1);color:#8A4B00;}
.p-red{background:rgba(196,56,74,.1);color:#A32C3C;}
.p-purple{background:rgba(84,104,245,.1);color:#2F3FC4;}
.p-teal{background:rgba(13,148,136,.1);color:#00697F;}
.p-grey{background:rgba(107,114,128,.1);color:#4A5170;}
.cat-acquirer{background:rgba(0,0,0,.04);color:var(--text3);border:1px solid rgba(0,0,0,.07);}
.cat-psp{background:rgba(0,0,0,.04);color:var(--text3);border:1px solid rgba(0,0,0,.07);}
.cat-apm{background:rgba(0,0,0,.04);color:var(--text3);border:1px solid rgba(0,0,0,.07);}
.cat-fraud{background:rgba(0,0,0,.04);color:var(--text3);border:1px solid rgba(0,0,0,.07);}
.cat-baas{background:rgba(0,0,0,.04);color:var(--text3);border:1px solid rgba(0,0,0,.07);}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--bg4);border-radius:3px;}
.pipeline-wrap{overflow-x:auto;margin-bottom:20px;padding-bottom:8px;}
.pipeline-board{display:flex;gap:12px;min-width:1000px;align-items:flex-start;}
.stage-col{background:#fff;border:none;box-shadow:var(--shadow);border-radius:12px;width:200px;flex-shrink:0;overflow:hidden;}
.stage-head{padding:10px 14px;background:#F7F8FD;border-bottom:1px solid rgba(0,0,0,0.06);display:flex;align-items:center;justify-content:space-between;}
.stage-name{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;}
.stage-num{font-size:10px;font-family:var(--font);font-variant-numeric:tabular-nums;background:var(--bg3);color:var(--text3);padding:2px 7px;border-radius:10px;}
.pcard{margin:8px;padding:11px 12px;background:#fff;border:1px solid rgba(0,0,0,0.06);border-radius:10px;cursor:pointer;transition:box-shadow .12s,border-color .12s;}
.pcard:hover{box-shadow:var(--shadow-md);border-color:rgba(0,0,0,0.1);}
.pcard-name{font-size:12px;font-weight:600;margin-bottom:5px;color:var(--text);}
.pcard-meta{display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:5px;}
.pcard-val{font-family:var(--font);font-variant-numeric:tabular-nums;font-size:10px;color:var(--text2);}
.pcard-owner{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--text3);margin-top:7px;}
.mini-av{width:16px;height:16px;border-radius:50%;font-size:10px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;}
.ma-y{background:rgba(84,104,245,0.15);color:#3E4FE0;}
.ma-e{background:rgba(90,100,134,0.15);color:#5A6486;}
.pbar{height:3px;background:var(--bg3);border-radius:2px;margin-top:9px;overflow:hidden;}
.pfill{height:100%;border-radius:2px;}

/* ══ Co-sell mission control ══════════════════════════════════════════════════
   A console board rather than a document: dark ground, provider call-signs at
   a size you can read across a room, and status carried by a coloured rail
   instead of a sentence. Detail lives one click down, never on the tile. */
.st-key-mcboard{background:linear-gradient(168deg,#07080E 0%,#0E1119 55%,#121623 100%);
  border:1px solid #232A3D;border-radius:16px;padding:16px 16px 6px;margin-bottom:12px;
  position:relative;overflow:hidden;}
.st-key-mcboard::before{content:'';position:absolute;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(139,155,255,.05) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(139,155,255,.05) 1px,transparent 1px);
  background-size:34px 34px;}
.st-key-mcboard::after{content:'';position:absolute;top:-130px;right:-90px;width:430px;
  height:430px;border-radius:50%;pointer-events:none;z-index:0;
  background:radial-gradient(circle,rgba(84,104,245,.17),transparent 66%);}
.st-key-mcboard [data-testid="stHorizontalBlock"]{position:relative;z-index:1;}
.st-key-mcboard [data-testid="stButton"] > button{
  background:rgba(255,255,255,.04) !important;border:1px solid rgba(255,255,255,.09) !important;
  border-left:3px solid #5C6480 !important;border-radius:9px !important;
  color:#EEF0FA !important;font-family:var(--font) !important;font-size:12.5px !important;
  font-weight:600 !important;letter-spacing:-.012em !important;line-height:1.25 !important;
  padding:11px 10px !important;margin-bottom:4px !important;min-height:46px !important;
  justify-content:flex-start !important;text-align:left !important;
  transition:background .16s var(--ease),border-color .16s var(--ease) !important;}
.st-key-mcboard [data-testid="stButton"] > button:hover{
  background:rgba(255,255,255,.085) !important;border-color:rgba(139,155,255,.5) !important;}
.st-key-mcboard [data-testid="stButton"] > button p{
  font-size:12.5px !important;font-weight:600 !important;}
/* The two move arrows under each tile */
.st-key-mcboard [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button{
  border-left-width:1px !important;border-left-color:rgba(255,255,255,.09) !important;
  min-height:0 !important;padding:2px 0 !important;margin-bottom:11px !important;
  justify-content:center !important;text-align:center !important;
  background:rgba(255,255,255,.02) !important;color:#8991AC !important;
  font-size:10px !important;border-radius:6px !important;}
.st-key-mcboard [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button p{font-size:10px !important;}
.st-key-mcboard [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button:hover{color:#EEF0FA !important;
  background:rgba(139,155,255,.16) !important;}
.st-key-mcboard [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button:disabled{opacity:.28 !important;}
/* Lane headers */
.mc-lane{padding:7px 8px 8px;margin-bottom:8px;border-radius:0 0 8px 8px;
  background:rgba(255,255,255,.03);font-family:var(--font);}
.mc-lane-n{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  line-height:1.3;min-height:24px;}
.mc-lane-c{font-size:15px;font-weight:700;color:#EEF0FA;font-variant-numeric:tabular-nums;
  line-height:1;margin-top:3px;}
.mc-lane-empty{text-align:center;color:#3B4258;font-size:13px;padding:6px 0 12px;}
/* Status strip */
.mc-strip{display:flex;gap:7px;flex-wrap:wrap;margin:2px 0 11px;font-family:var(--font);}
.mc-cell{flex:1;min-width:96px;background:#10131C;border:1px solid #232A3D;
  border-radius:9px;padding:9px 12px;}
.mc-cell .v{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1;}
.mc-cell .k{font-size:8.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:#5C6480;margin-top:4px;}
.mc-empty{background:#10131C;border:1px solid #232A3D;border-radius:14px;padding:26px;
  text-align:center;font-size:12.5px;color:#8991AC;font-family:var(--font);}
/* Desk roster */
.mc-desk{display:flex;gap:7px;flex-wrap:wrap;margin:2px 0 11px;}
.mc-seat{flex:1;min-width:114px;background:#fff;border:1px solid rgba(35,42,61,.10);
  border-radius:10px;padding:10px 12px;font-family:var(--font);}
.mc-seat .n{font-size:12.5px;font-weight:600;color:#10131C;}
.mc-seat .r{font-size:9.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
  color:#858CA6;margin-top:2px;}
.mc-seat .c{font-size:18px;font-weight:700;font-variant-numeric:tabular-nums;
  letter-spacing:-.02em;margin-top:6px;}
/* ══ Nav rail ═════════════════════════════════════════════════════════════════
   One instrument, not five loose lozenges: a Yuno-blue rail carrying the views,
   with the live one lifted out of it as a white card. White-on-blue for the
   resting segments and blue-on-white for the live one keeps both legible —
   the earlier near-black rail left the inactive labels too dim to read. */
[class*="st-key-nav_"] [role="radiogroup"]{
  display:inline-flex !important;gap:3px !important;flex-wrap:wrap !important;
  background:linear-gradient(135deg,#3E4FE0 0%,#5468F5 100%) !important;
  border:1px solid rgba(47,63,196,.55) !important;
  border-radius:13px !important;padding:4px !important;
  box-shadow:0 2px 5px rgba(62,79,224,.20),0 10px 26px rgba(62,79,224,.20) !important;}
[class*="st-key-nav_"] [role="radiogroup"] label{
  background:transparent !important;border:1px solid transparent !important;
  border-radius:9px !important;padding:8px 18px !important;margin:0 !important;
  color:rgba(255,255,255,.82) !important;font-family:var(--font) !important;
  font-size:12.5px !important;font-weight:600 !important;letter-spacing:-.005em !important;
  transition:background .18s var(--ease),color .18s var(--ease),
             box-shadow .18s var(--ease) !important;}
[class*="st-key-nav_"] [role="radiogroup"] label p{
  font-size:12.5px !important;font-weight:600 !important;color:inherit !important;}
[class*="st-key-nav_"] [role="radiogroup"] label:hover{
  background:rgba(255,255,255,.16) !important;color:#fff !important;}
[class*="st-key-nav_"] [role="radiogroup"] label:has(input:checked){
  background:#fff !important;color:#2F3FC4 !important;
  box-shadow:0 1px 2px rgba(16,19,28,.12),0 4px 12px rgba(16,19,28,.16) !important;}
[class*="st-key-nav_"] [role="radiogroup"] label:has(input:checked) p{
  color:#2F3FC4 !important;}
/* The dot carries no meaning here — the lift is the affordance. */
[class*="st-key-nav_"] [role="radiogroup"] [data-baseweb="radio"] > div:first-of-type{
  display:none !important;}

/* ══ Segmented toggles ════════════════════════════════════════════════════════
   A control that reads as an instrument rather than a form field: the whole
   segment is the hit area, the live one lifts out of the rail and carries an
   accent bar, and the numbers under each label stay legible while unselected. */
.seg-rail{background:#0E1119;border:1px solid #232A3D;border-radius:13px;
  padding:7px;margin-bottom:10px;}
.seg-rail [data-testid="stButton"] > button{
  background:transparent !important;border:1px solid transparent !important;
  border-radius:9px !important;color:#8991AC !important;font-family:var(--font) !important;
  padding:13px 12px !important;min-height:0 !important;width:100% !important;
  display:flex !important;flex-direction:column !important;align-items:flex-start !important;
  gap:3px !important;text-align:left !important;
  transition:background .17s var(--ease),color .17s var(--ease),
             border-color .17s var(--ease),box-shadow .17s var(--ease) !important;}
.seg-rail [data-testid="stButton"] > button:hover{
  background:rgba(255,255,255,.05) !important;color:#EEF0FA !important;}
.seg-rail [data-testid="stButton"] > button p{margin:0 !important;line-height:1.35 !important;}
.seg-rail [data-testid="stButton"] > button p:first-child{
  font-size:13.5px !important;font-weight:600 !important;letter-spacing:-.012em !important;}
.seg-rail [data-testid="stButton"] > button p:last-child{
  font-size:10.5px !important;font-weight:500 !important;opacity:.8 !important;
  font-variant-numeric:tabular-nums !important;}
/* The live segment */
.seg-rail [data-testid="stButton"] > button[kind="primary"]{
  background:linear-gradient(160deg,#1B2135,#141A2B) !important;
  border-color:#3E4863 !important;color:#EEF0FA !important;
  box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 6px 18px rgba(0,0,0,.32) !important;
  position:relative !important;}
.seg-rail [data-testid="stButton"] > button[kind="primary"]::before{
  content:'';position:absolute;left:12px;right:12px;top:0;height:2px;border-radius:0 0 2px 2px;
  background:linear-gradient(90deg,#5468F5,#8B9BFF);}
.seg-rail [data-testid="stButton"] > button[kind="primary"] p:last-child{
  color:#8B9BFF !important;opacity:1 !important;}

/* Result read-outs — the two control outputs the model exists to produce */
.px-out{display:flex;gap:10px;flex-wrap:wrap;margin:4px 0 12px;}
.px-big{flex:1;min-width:210px;background:linear-gradient(160deg,#0E1119,#141827 60%,#191E2F);
  border:1px solid #232A3D;border-radius:14px;padding:18px 20px;position:relative;
  overflow:hidden;font-family:var(--font);}
.px-big::after{content:'';position:absolute;top:-70px;right:-50px;width:260px;height:260px;
  border-radius:50%;background:radial-gradient(circle,rgba(84,104,245,.18),transparent 66%);}
.px-k{font-size:9px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;
  color:#5C6480;position:relative;z-index:1;}
.px-v{font-size:34px;font-weight:700;letter-spacing:-.03em;line-height:1.05;margin-top:7px;
  font-variant-numeric:tabular-nums;position:relative;z-index:1;}
.px-s{font-size:11px;color:#8991AC;margin-top:5px;position:relative;z-index:1;}
.px-band{display:flex;align-items:center;gap:7px;margin-top:11px;position:relative;z-index:1;}
.px-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.px-flag{font-size:11px;font-weight:600;}

/* ══ Lead generation console ══════════════════════════════════════════════════
   The demand desk as a board: a status rail, then named leads as call-signs on
   a dark ground. Same grammar as the co-sell board so the two read as one room. */
.lg-rail{display:flex;gap:7px;flex-wrap:wrap;margin:2px 0 11px;font-family:var(--font);}
.lg-stat{flex:1;min-width:96px;background:#10131C;border:1px solid #232A3D;
  border-radius:9px;padding:10px 12px;}
.lg-stat .v{font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1;}
.lg-stat .k{font-size:8.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:#5C6480;margin-top:4px;}
.lg-board{background:linear-gradient(168deg,#07080E 0%,#0E1119 55%,#121623 100%);
  border:1px solid #232A3D;border-radius:16px;padding:16px;margin-bottom:10px;
  position:relative;overflow:hidden;}
.lg-board::before{content:'';position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(139,155,255,.05) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(139,155,255,.05) 1px,transparent 1px);
  background-size:34px 34px;}
.lg-board::after{content:'';position:absolute;top:-130px;right:-90px;width:430px;height:430px;
  border-radius:50%;pointer-events:none;
  background:radial-gradient(circle,rgba(84,104,245,.16),transparent 66%);}
.lg-grid{position:relative;z-index:1;display:grid;gap:7px;
  grid-template-columns:repeat(auto-fill,minmax(196px,1fr));max-height:560px;overflow-y:auto;}
.lg-tile{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);
  border-left:3px solid #5C6480;border-radius:9px;padding:11px 12px;
  font-family:var(--font);transition:background .15s var(--ease),border-color .15s var(--ease);}
.lg-tile:hover{background:rgba(255,255,255,.085);border-color:rgba(139,155,255,.5);}
.lg-n{font-size:12.5px;font-weight:600;color:#EEF0FA;letter-spacing:-.012em;line-height:1.3;
  word-break:break-word;}
.lg-m{display:flex;align-items:center;gap:7px;margin-top:7px;flex-wrap:wrap;}
.lg-tag{font-size:8px;font-weight:700;letter-spacing:.07em;padding:2px 6px;border-radius:4px;
  white-space:nowrap;}
.lg-r{font-size:10px;color:#5C6480;}
.lg-ask{font-size:10.5px;color:#8991AC;margin-top:7px;padding-top:6px;
  border-top:1px solid rgba(255,255,255,.07);line-height:1.4;}
.lg-count{font-size:10.5px;color:#858CA6;margin:2px 0 8px;font-family:var(--font);
  font-variant-numeric:tabular-nums;}
.lg-empty{background:#10131C;border:1px solid #232A3D;border-radius:14px;padding:24px;
  text-align:center;font-size:12.5px;color:#8991AC;font-family:var(--font);}
.lg-note{font-size:11px;color:#858CA6;line-height:1.6;font-family:var(--font);
  padding:2px 2px 0;}
/* Routing read-out */
.lg-route{background:#10131C;border:1px solid #232A3D;border-radius:12px;padding:6px 16px;
  margin-bottom:11px;font-family:var(--font);}
.lg-route-r{display:flex;align-items:center;gap:12px;padding:10px 0;flex-wrap:wrap;
  border-bottom:1px solid rgba(255,255,255,.07);}
.lg-route-r:last-child{border-bottom:0;}
.lg-route-k{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:#5C6480;width:106px;flex-shrink:0;}
.lg-route-v{font-size:14px;font-weight:600;letter-spacing:-.012em;}
.lg-route-n{margin-left:auto;font-size:10.5px;color:#8991AC;text-align:right;}
/* Rosters */
.lg-roster{background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;
  padding:14px 16px;height:100%;font-family:var(--font);}
.lg-roster-h{font-size:9.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:#858CA6;margin-bottom:8px;}
.lg-roster-r{display:flex;align-items:center;gap:10px;padding:7px 0;flex-wrap:wrap;
  border-bottom:1px solid rgba(35,42,61,.055);}
.lg-roster-n{font-size:12px;font-weight:600;color:#10131C;min-width:104px;}
.lg-roster-m{font-size:10.5px;color:#676E8A;flex:1;min-width:96px;}
.lg-roster-h2{font-size:10px;font-weight:600;}
/* Alert feed */
.lg-feed{display:flex;align-items:center;gap:11px;padding:8px 10px;flex-wrap:wrap;
  border-bottom:1px solid rgba(255,255,255,.06);font-family:var(--font);}
.lg-feed-t{font-size:10px;color:#5C6480;font-variant-numeric:tabular-nums;width:104px;
  flex-shrink:0;}
.lg-feed-n{font-size:12.5px;font-weight:600;color:#EEF0FA;min-width:118px;}
.lg-feed-r{font-size:10.5px;color:#8991AC;}
.lg-feed-a{margin-left:auto;font-size:11px;color:#E0ED80;font-weight:600;}

/* Channel panels */
.lg-ch{background:#10131C;border:1px solid #232A3D;border-radius:13px;padding:16px 18px;
  margin-bottom:9px;position:relative;overflow:hidden;font-family:var(--font);}
.lg-ch-h{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:10px;}
.lg-ch-i{display:grid;place-items:center;width:26px;height:26px;border-radius:7px;
  font-size:13px;flex-shrink:0;}
.lg-ch-n{font-size:14.5px;font-weight:600;color:#EEF0FA;letter-spacing:-.015em;}
.lg-ch-c{margin-left:auto;font-size:10px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:#5C6480;}
.lg-ch-tip{background:rgba(255,255,255,.04);border-radius:9px;padding:11px 13px;
  font-size:11.5px;color:#B7BEDA;line-height:1.65;margin-bottom:10px;}
.lg-ch-body{margin-bottom:11px;}
.lg-ch-f{display:flex;align-items:center;gap:8px;padding-top:9px;
  border-top:1px solid rgba(255,255,255,.07);}

/* ══ Tiering mission control ══════════════════════════════════════════════════
   The tiering run reads as an instrument panel: a status rail across the top,
   four gauges carrying the buckets, and the desk as a row of stations. Numbers
   are the loudest thing on screen; labels sit underneath them. */
@keyframes tcPulse{0%,100%{opacity:1}50%{opacity:.3}}
.tc-live{animation:tcPulse 2.2s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.tc-live{animation:none}}

.tc-shell{background:linear-gradient(168deg,#07080E 0%,#0E1119 55%,#121623 100%);
  border:1px solid #232A3D;border-radius:18px;padding:22px 24px 20px;margin-bottom:12px;
  position:relative;overflow:hidden;font-family:var(--font);}
.tc-shell::before{content:'';position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(139,155,255,.05) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(139,155,255,.05) 1px,transparent 1px);
  background-size:34px 34px}
.tc-shell::after{content:'';position:absolute;top:-140px;right:-100px;width:460px;height:460px;
  border-radius:50%;pointer-events:none;
  background:radial-gradient(circle,rgba(84,104,245,.18),transparent 66%)}
.tc-in{position:relative;z-index:1}
.tc-top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:9px}
.tc-eyebrow{font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:#E0ED80}
.tc-clock{margin-left:auto;font-size:10.5px;color:#5C6480;font-variant-numeric:tabular-nums}
.tc-h{font-size:22px;font-weight:600;color:#EEF0FA;letter-spacing:-.025em}
.tc-sub{font-size:12.5px;color:#8991AC;margin-top:5px;line-height:1.65;max-width:900px}
/* Status rail */
.tc-rail{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}
.tc-stat{flex:1;min-width:104px;background:rgba(255,255,255,.035);
  border:1px solid rgba(255,255,255,.08);border-radius:9px;padding:10px 12px}
.tc-stat .v{font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
.tc-stat .k{font-size:8.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:#5C6480;margin-top:4px}

/* Bucket gauges */
.tc-gauges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.tc-g{flex:1;min-width:172px;background:#10131C;border:1px solid #232A3D;border-radius:13px;
  padding:15px 16px 13px;position:relative;overflow:hidden;font-family:var(--font)}
.tc-g::before{content:'';position:absolute;left:0;right:0;top:0;height:2px}
.tc-g-h{display:flex;align-items:baseline;gap:6px;margin-bottom:9px}
.tc-g-n{font-size:9.5px;font-weight:700;letter-spacing:.11em;text-transform:uppercase}
.tc-g-mode{margin-left:auto;font-size:8.5px;font-weight:700;letter-spacing:.07em;
  padding:2px 6px;border-radius:4px}
.tc-g-v{font-size:30px;font-weight:700;line-height:1;letter-spacing:-.03em;
  font-variant-numeric:tabular-nums}
.tc-m{margin-top:10px}
.tc-m-r{display:flex;align-items:center;gap:7px;margin-bottom:5px}
.tc-m-k{font-size:8.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  color:#5C6480;width:52px;flex-shrink:0}
.tc-m-bar{flex:1;height:5px;background:rgba(255,255,255,.07);border-radius:3px;overflow:hidden}
.tc-m-fill{height:100%;border-radius:3px;transition:width .35s var(--ease)}
.tc-m-v{font-size:10px;color:#8991AC;font-variant-numeric:tabular-nums;width:42px;
  text-align:right;flex-shrink:0}
.tc-g-f{margin-top:11px;padding-top:9px;border-top:1px solid rgba(255,255,255,.07);
  font-size:10.5px;display:flex;align-items:center;gap:6px}

/* Tiering desk — same console tile, on the dark tiering ground */
.st-key-tierdesk{margin-bottom:6px;}
.st-key-tierdesk [data-testid="stButton"] > button{
  background:#10131C !important;border:1px solid #232A3D !important;
  border-left:3px solid #232A3D !important;border-radius:11px !important;
  color:#EEF0FA !important;font-family:var(--font) !important;font-size:13px !important;
  font-weight:600 !important;letter-spacing:-.01em !important;
  padding:13px 14px !important;margin-bottom:9px !important;min-height:52px !important;
  justify-content:flex-start !important;text-align:left !important;
  transition:background .16s var(--ease),border-color .16s var(--ease) !important;}
.st-key-tierdesk [data-testid="stButton"] > button:hover{
  background:#191E2F !important;border-color:#38415C !important;}
.st-key-tierdesk [data-testid="stButton"] > button p{
  font-size:13px !important;font-weight:600 !important;}
/* Tier browser — a light instrument on the light page */
.st-key-tierpick [data-testid="stButton"] > button{
  background:#fff !important;border:1px solid #E4E6F0 !important;border-radius:12px !important;
  color:#10131C !important;font-family:var(--font) !important;padding:12px 15px !important;
  min-height:0 !important;width:100% !important;display:flex !important;
  flex-direction:column !important;align-items:flex-start !important;gap:2px !important;
  text-align:left !important;box-shadow:0 1px 2px rgba(16,19,28,.04) !important;
  transition:border-color .16s var(--ease),background .16s var(--ease) !important;}
.st-key-tierpick [data-testid="stButton"] > button:hover{
  border-color:#B9C0FF !important;background:#FAFAFF !important;}
.st-key-tierpick [data-testid="stButton"] > button p{margin:0 !important;line-height:1.3 !important;}
.st-key-tierpick [data-testid="stButton"] > button p:first-child{
  font-size:13.5px !important;font-weight:600 !important;letter-spacing:-.01em !important;}
.st-key-tierpick [data-testid="stButton"] > button p:last-child{
  font-size:11px !important;font-weight:500 !important;color:#676E8A !important;
  font-variant-numeric:tabular-nums !important;}
.st-key-tierpick [data-testid="stButton"] > button[kind="primary"]{
  background:#3E4FE0 !important;border-color:#3E4FE0 !important;color:#fff !important;
  box-shadow:0 6px 18px rgba(62,79,224,.25) !important;}
.st-key-tierpick [data-testid="stButton"] > button[kind="primary"] p{color:#fff !important;}
.st-key-tierpick [data-testid="stButton"] > button[kind="primary"] p:last-child{
  color:rgba(255,255,255,.82) !important;}
.st-key-conn_examples{margin:-4px 0 10px;}
.st-key-conn_examples [data-testid="stButton"] > button{
  background:#fff !important;border:1px solid rgba(35,42,61,.12) !important;border-radius:999px !important;
  color:#4A5170 !important;font-family:var(--font) !important;font-size:11.5px !important;
  font-weight:500 !important;padding:4px 10px !important;min-height:0 !important;
  margin-bottom:6px !important;transition:border-color .14s var(--ease),color .14s var(--ease) !important;}
.st-key-conn_examples [data-testid="stButton"] > button:hover{
  border-color:#8B9BFF !important;color:#2F3FC4 !important;background:#F4F5FF !important;}
.st-key-conn_examples [data-testid="stButton"] > button p{font-size:11.5px !important;
  white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;}
.st-key-tierlist [data-testid="stButton"] > button{
  background:#fff !important;border:1px solid #E4E6F0 !important;border-radius:10px !important;
  color:#10131C !important;font-family:var(--font) !important;padding:9px 13px !important;
  min-height:0 !important;width:100% !important;display:flex !important;
  flex-direction:column !important;align-items:flex-start !important;gap:1px !important;
  text-align:left !important;margin-bottom:-6px !important;
  transition:border-color .14s var(--ease),background .14s var(--ease) !important;}
.st-key-tierlist [data-testid="stButton"] > button:hover{
  border-color:#B9C0FF !important;background:#FAFAFF !important;}
.st-key-tierlist [data-testid="stButton"] > button p{margin:0 !important;line-height:1.3 !important;
  white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;
  max-width:100% !important;}
.st-key-tierlist [data-testid="stButton"] > button p:first-child{
  font-size:13px !important;font-weight:600 !important;}
.st-key-tierlist [data-testid="stButton"] > button p:last-child{
  font-size:10.5px !important;font-weight:500 !important;color:#676E8A !important;
  font-variant-numeric:tabular-nums !important;}
.st-key-tierlist [data-testid="stButton"] > button[kind="primary"]{
  background:#EEF0FF !important;border-color:#3E4FE0 !important;color:#10131C !important;
  box-shadow:none !important;}
.st-key-tierlist [data-testid="stButton"] > button[kind="primary"] p:last-child{color:#3E4FE0 !important;}
.st-key-tierdl [data-testid="stDownloadButton"] > button{
  background:#3E4FE0 !important;border:1px solid #3E4FE0 !important;color:#fff !important;
  font-weight:600 !important;border-radius:11px !important;font-family:var(--font) !important;}
.st-key-tierdl [data-testid="stDownloadButton"] > button:hover{
  background:#5468F5 !important;border-color:#5468F5 !important;}
.st-key-tierdl [data-testid="stDownloadButton"] > button p{color:#fff !important;font-weight:600 !important;}
"""

_LANDING_CSS = """
/* ══ Sign-in ═════════════════════════════════════════════════════════════════
   The front door wears the product's own dark ground full-bleed — not a dark
   card floating on a light page. One measure, one accent, Geist throughout. */
[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display:none !important; }

.stApp {
  background-color:#080911 !important;
  background-image:
    radial-gradient(circle at 50% 40%, rgba(84,104,245,0.26) 0%, transparent 58%),
    radial-gradient(circle at 1px 1px, rgba(255,255,255,0.035) 1px, transparent 0) !important;
  background-size:100% 100%, 28px 28px !important;
  background-repeat:no-repeat, repeat !important;
  background-attachment:fixed !important;
}
[data-testid="stAppViewContainer"], section[data-testid="stMain"], .main,
section[data-testid="stMain"] > div, .block-container,
[data-testid="stVerticalBlock"], [data-testid="stMarkdownContainer"] { background:transparent !important; }

/* One centred 376px measure — every widget inherits it, so nothing is centred twice. */
.main .block-container, .block-container {
  max-width:100% !important; padding:44px 0 !important; box-sizing:border-box !important;
  min-height:100vh !important; display:flex !important;
  flex-direction:column !important; justify-content:center !important; }
.block-container > [data-testid="stVerticalBlock"] {
  flex:0 0 auto !important; width:100% !important; max-width:376px !important;
  margin:0 auto !important; gap:0 !important; }

.yl { font-family:var(--font) !important; }
/* the measure sets gap:0, so controls declare their own rhythm */
section[data-testid="stMain"] [data-testid="stTextInput"] { margin-bottom:10px !important; }
section[data-testid="stMain"] [data-testid="stHorizontalBlock"] { gap:10px !important; }
.yl-brand { display:flex; align-items:center; justify-content:center; gap:11px; margin-bottom:28px; }
.yl-mark { display:grid; grid-template-columns:repeat(4,7px); gap:2.5px; }
.yl-mark span { width:7px; height:7px; border-radius:1.5px; background:#8B9BFF; }
.yl-mark .m { opacity:.42 } .yl-mark .o { opacity:0 }
.yl-word { font-size:22px; font-weight:700; color:#EEF0FA; letter-spacing:-.035em; line-height:1; }

.yl .yl-title { text-align:center !important; font-size:22px !important; font-weight:600 !important;
  color:#EEF0FA !important; letter-spacing:-.024em !important; line-height:1.24 !important;
  margin:0 0 9px !important; padding:0 !important; font-family:var(--font) !important; }
.yl .yl-sub { text-align:center !important; font-size:14px !important; font-weight:400 !important;
  color:#8991AC !important; line-height:1.5 !important; margin:0 0 26px !important;
  padding:0 !important; font-family:var(--font) !important; }

/* ── Provider buttons (fallback chooser only) ────────────────────────────────
   Icons sit in a fixed 20px slot at a fixed inset, so the marks and the label
   baselines align down one axis rather than drifting with label length. */
a.yl-sso { display:flex; align-items:center; gap:13px;
  width:100%; min-height:52px; padding:0 18px; margin-bottom:10px;
  border-radius:12px; border:1px solid rgba(255,255,255,0.13);
  background:rgba(255,255,255,0.055); box-sizing:border-box;
  font-family:var(--font) !important; font-size:14px; font-weight:500; letter-spacing:-.005em;
  color:#EEF0FA !important; text-decoration:none !important;
  transition:background .16s var(--ease), border-color .16s var(--ease),
             transform .16s var(--ease), box-shadow .16s var(--ease); }
a.yl-sso::before { content:""; flex:0 0 20px; height:20px;
  background-repeat:no-repeat; background-position:center; background-size:contain; }
a.yl-sso:hover { background:rgba(255,255,255,0.10); border-color:rgba(122,140,255,0.55);
  transform:translateY(-1px); box-shadow:0 10px 28px rgba(0,0,0,.5); text-decoration:none !important; }
a.yl-sso:active { transform:translateY(0); box-shadow:none; }
a.yl-sso:focus-visible { outline:none; border-color:#8B9BFF; box-shadow:0 0 0 3px rgba(122,140,255,.55); }
a.yl-sso .yl-chip { margin-left:auto; font-family:var(--font);font-variant-numeric:tabular-nums; font-size:10px; font-weight:500;
  letter-spacing:.06em; text-transform:uppercase; color:#8991AC;
  border:1px solid rgba(255,255,255,.13); padding:3px 7px; border-radius:5px; }
a.yl-sso .yl-chip-live { color:#E0ED80; border-color:rgba(224,237,128,.30); background:rgba(224,237,128,.12); }

.yl-or { display:flex; align-items:center; gap:12px; margin:20px 0 4px; }
.yl-or::before, .yl-or::after { content:""; flex:1; height:1px; background:rgba(255,255,255,0.09); }
.yl-or span { font-size:12px; font-weight:400; color:#8991AC; }

a.yl-alt { display:block; text-align:center; font-family:var(--font) !important;
  font-size:13px; font-weight:500; color:#8991AC !important; text-decoration:none !important;
  padding:11px 8px; border-radius:9px; transition:color .16s var(--ease), background .16s var(--ease); }
a.yl-alt:hover { color:#EEF0FA !important; background:rgba(255,255,255,0.05); text-decoration:none !important; }
a.yl-alt:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(122,140,255,.55); }

.yl-foot { display:flex; align-items:center; justify-content:center; gap:7px;
  margin-top:22px; font-size:11px; font-weight:400; color:#8991AC; }
.yl-foot svg { flex:0 0 13px; }

.yl-step { text-align:center; padding:0 0 22px; }
.yl-step-badge { width:46px; height:46px; border-radius:13px; margin:0 auto 18px;
  display:flex; align-items:center; justify-content:center;
  background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.13); }
.yl-step .yl-h { font-size:18px !important; font-weight:600 !important; color:#EEF0FA !important;
  letter-spacing:-.02em !important; margin:0 0 8px !important; padding:0 !important;
  font-family:var(--font) !important; }
.yl-step .yl-p { font-size:13px !important; font-weight:400 !important; color:#8991AC !important;
  line-height:1.55 !important; margin:0 !important; padding:0 !important; font-family:var(--font) !important; }
.yl-hint { text-align:center; font-size:12px; color:#8991AC; line-height:1.8; margin-top:16px; }
.yl-hint b { color:#EEF0FA; font-weight:500; font-family:var(--font);font-variant-numeric:tabular-nums; font-size:11px; }
.yl-err { text-align:center; font-size:12px; font-weight:500; color:#FF7A72;
  margin:0 0 10px; padding:9px 12px; border-radius:9px;
  background:rgba(255,107,125,.10); border:1px solid rgba(255,107,125,.28); }
/* the measure sets gap:0, so a markdown block between controls must claim its own space */
section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.yl-err) { display:block !important; }
.yl-note { display:flex; gap:9px; align-items:flex-start; margin-top:18px; padding:11px 13px;
  border-radius:10px; background:rgba(84,104,245,0.14); border:1px solid rgba(122,140,255,0.30);
  font-size:11px; line-height:1.6; color:#B6BCD0; }
.yl-note b { color:#CBD3FA; font-weight:500; font-family:var(--font);font-variant-numeric:tabular-nums; }

/* ── Widgets on the dark ground ── */
[data-testid="stTextInputRootElement"] {
  background:rgba(255,255,255,0.055) !important; border:1px solid rgba(255,255,255,0.13) !important;
  border-radius:11px !important; min-height:52px !important; overflow:hidden !important;
  transition:border-color .16s var(--ease), box-shadow .16s var(--ease) !important; }
[data-testid="stTextInputRootElement"]:focus-within {
  border-color:#8B9BFF !important; box-shadow:0 0 0 3px rgba(122,140,255,.45) !important; }
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"] { background:transparent !important; }
[data-testid="stTextInput"] input {
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:#EEF0FA !important; -webkit-text-fill-color:#EEF0FA !important; caret-color:#8B9BFF !important;
  min-height:50px !important; padding:0 16px !important;
  font-family:var(--font) !important; font-size:14px !important; letter-spacing:-.005em !important; }
[data-testid="stTextInput"] input::placeholder { color:#858CA6 !important; -webkit-text-fill-color:#858CA6 !important; }
[data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stTextInput"] input:-webkit-autofill:hover,
[data-testid="stTextInput"] input:-webkit-autofill:focus,
[data-testid="stTextInput"] input:-webkit-autofill:active {
  -webkit-text-fill-color:#EEF0FA !important;
  caret-color:#8B9BFF !important;
  -webkit-box-shadow:0 0 0 1000px #171A28 inset !important;
          box-shadow:0 0 0 1000px #171A28 inset !important;
  background-color:transparent !important;
  background-clip:content-box !important;
  transition:background-color 600000s 0s, color 600000s 0s !important; }
[data-testid="stTextInput"] input:-internal-autofill-selected {
  -webkit-text-fill-color:#EEF0FA !important;
  background-color:transparent !important; }
[data-testid="stTextInput"] input[type="password"] {
  background:transparent !important; color:#EEF0FA !important;
  -webkit-text-fill-color:#EEF0FA !important; font-family:var(--font) !important; letter-spacing:.14em !important; }
[data-testid="stTextInputRootElement"] button {
  background:transparent !important; border:none !important; color:#858CA6 !important; }
[data-testid="stTextInputRootElement"] button:hover { color:#EEF0FA !important; }
[data-testid="stTextInputRootElement"] button svg { fill:currentColor !important; }

section[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button,
section[data-testid="stMain"] [data-testid="stButton"] > button {
  min-height:50px !important; border-radius:11px !important; font-family:var(--font) !important;
  font-size:14px !important; font-weight:500 !important; letter-spacing:-.005em !important;
  background:rgba(255,255,255,0.055) !important; color:#EEF0FA !important;
  border:1px solid rgba(255,255,255,0.13) !important; transition:all .16s var(--ease) !important; }
section[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover,
  section[data-testid="stMain"] [data-testid="stButton"] > button:hover {
  background:rgba(255,255,255,0.10) !important; border-color:rgba(122,140,255,0.55) !important; }
section[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"],
  section[data-testid="stMain"] [data-testid="stButton"] > button[kind="primary"] {
  background:#3E4FE0 !important; border-color:#3E4FE0 !important; color:#fff !important; font-weight:600 !important; }
section[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover,
  section[data-testid="stMain"] [data-testid="stButton"] > button[kind="primary"]:hover {
  background:#5468F5 !important; border-color:#5468F5 !important; }
section[data-testid="stMain"] [data-testid="stButton"] > button:focus-visible {
  outline:none !important; box-shadow:0 0 0 3px rgba(122,140,255,.55) !important; }

@media (prefers-reduced-motion: reduce) {
  a.yl-sso, a.yl-alt, section[data-testid="stMain"] [data-testid="stButton"] > button {
    transition:none !important; }
  a.yl-sso:hover { transform:none !important; }
}
"""

# ── One font, everywhere ───────────────────────────────────────────────────────
# The CSS variable --font governs every DOM node, but Plotly renders to SVG and
# never sees it: a chart with no explicit family falls back to the library
# default and the page ends up wearing two typefaces. So the same stack is
# declared once here and installed as the Plotly default template, which every
# figure inherits. Charts should not set `family` themselves.
_FONT_STACK = "Geist, GeistSans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"

# Type scale — the sizes the portal actually uses, named so a section cannot
# invent a sixth heading size.
_T_HERO_TITLE = 26      # hero headline
_T_PAGE_TITLE = 20      # section hero title
_T_EYEBROW    = 10      # uppercase kicker above a title
_T_LABEL      = 11      # uppercase section label in the body
_T_BODY       = 13       # standard body copy
_T_META       = 11      # secondary / caption

# Uniform uppercase tracking. Was drifting between .1em and .15em by section.
_TRACK = ".11em"


def _install_plotly_theme():
    """Make Geist and the portal's ink colours the chart default, once."""
    try:
        import plotly.io as _pio
        import plotly.graph_objects as _go
        base = _pio.templates["plotly_white"]
        t = _go.layout.Template(base)
        t.layout.font = dict(family=_FONT_STACK, color="#676E8A", size=11)
        t.layout.title = dict(font=dict(family=_FONT_STACK, color="#10131C", size=13), x=0)
        t.layout.hoverlabel = dict(font=dict(family=_FONT_STACK, size=11))
        t.layout.legend = dict(font=dict(family=_FONT_STACK, size=10))
        t.layout.paper_bgcolor = "rgba(0,0,0,0)"
        t.layout.plot_bgcolor = "rgba(0,0,0,0)"
        t.layout.colorway = ["#3E4FE0", "#C24E00", "#0086A8",
                             "#2F8A1F", "#C4187F", "#6B6F00", "#676E8A"]
        _pio.templates["yuno"] = t
        _pio.templates.default = "yuno"
    except Exception:
        pass


_install_plotly_theme()


def _eyebrow(text, tone="light"):
    """The uppercase kicker. One definition, so tracking cannot drift again."""
    col = "#8B9BFF" if tone == "dark" else "#858CA6"
    return (f'<div style="font-size:{_T_EYEBROW}px;font-weight:500;letter-spacing:{_TRACK};'
            f'text-transform:uppercase;color:{col};font-family:var(--mono);'
            f'font-variant-numeric:tabular-nums;margin-bottom:10px;">{text}</div>')


def _section_label(text, top=20, bottom=10):
    """Body-level section label — the '1 · Who is expanding' treatment."""
    return (f'<div style="font-size:{_T_LABEL}px;font-weight:500;letter-spacing:{_TRACK};'
            f'text-transform:uppercase;color:#858CA6;font-family:var(--mono);'
            f'margin:{top}px 0 {bottom}px;">{text}</div>')


def nav_radio(label, options, key, **kw):
    """The portal's one view switcher.

    Wrapped in a keyed container so the blue-rail styling can find it — every
    switcher in the portal goes through here rather than restyling per page.
    """
    with st.container(key=f"nav_{key}"):
        return st.radio(label, options, horizontal=True, key=key,
                        label_visibility="collapsed", **kw)


def hero(title, subtitle="", eyebrow="", tiles=None, lockup=None, badge=None):
    """The portal's one page header.

    Every external section used to roll its own: three corner radii, three
    padding pairs, two backgrounds and two title sizes between them. This is
    that treatment settled — dark ground, optional eyebrow, optional stat
    tiles, optional co-brand lockup.
    """
    head = lockup if lockup else (
        f'<div style="font-size:{_T_PAGE_TITLE}px;font-weight:700;color:#F1F3FB;'
        f'letter-spacing:-.02em;">{title}</div>')
    badge_html = ""
    if badge:
        badge_html = (
            f'<span style="font-size:10px;font-weight:600;letter-spacing:.12em;'
            f'text-transform:uppercase;background:rgba(224,237,128,.16);color:#E0ED80;'
            f'border:1px solid rgba(224,237,128,.34);padding:3px 9px;border-radius:5px;">'
            f'{badge}</span>')
    tile_html = ""
    if tiles:
        tile_html = ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;">' + "".join(
            f'<div style="background:rgba(255,255,255,0.04);border:.5px solid rgba(255,255,255,0.08);'
            f'border-radius:8px;padding:10px 14px;text-align:center;min-width:88px;">'
            f'<div style="font-size:16px;font-weight:700;color:{c};font-variant-numeric:tabular-nums;">{v}</div>'
            f'<div style="font-size:10px;color:#4A5170;text-transform:uppercase;letter-spacing:.06em;'
            f'margin-top:2px;">{k}</div></div>'
            for v, k, c in tiles) + '</div>')
    return f"""
<div style="background:linear-gradient(160deg,#080911 0%,#10131C 55%,#141827 100%);
            border:1px solid #232A3D;border-radius:16px;padding:24px 28px;margin-bottom:14px;
            position:relative;overflow:hidden;font-family:var(--font);">
  <div style="position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,
              rgba(255,255,255,0.03) 1px,transparent 0);background-size:22px 22px;pointer-events:none;"></div>
  <div style="position:absolute;top:-90px;right:-70px;width:420px;height:420px;border-radius:50%;
              background:radial-gradient(circle,rgba(84,104,245,0.18),transparent 65%);pointer-events:none;"></div>
  <div style="position:relative;z-index:1;">
    {eyebrow and _eyebrow(eyebrow, "dark") or ""}
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">{head}{badge_html}</div>
    {f'<div style="font-size:12.5px;color:#8991AC;line-height:1.6;margin-top:6px;max-width:660px;">{subtitle}</div>' if subtitle else ''}
    {tile_html}
  </div>
</div>"""


def inject_css(role):
    css = _STATIC_CSS + ("" if role else _LANDING_CSS)
    escaped = css.replace('\\', '\\\\').replace('`', '\\`')
    if not role:
        btn_js = """
setInterval(function(){
  var doc = window.parent.document;
  var allBtns = doc.querySelectorAll('button[data-testid="baseButton-secondary"]');
  // Check if password modal is open (pw_back button exists)
  var hasPwBack = Array.from(allBtns).some(function(b){ return b.innerText.trim().startsWith('←'); });
  if(hasPwBack){
    allBtns.forEach(function(b){
      var txt = b.innerText.trim();
      if(txt.startsWith('←')){
        b.style.setProperty('background','rgba(255,255,255,.08)','important');
        b.style.setProperty('color','#aaa','important');
        b.style.setProperty('border','1px solid rgba(255,255,255,.12)','important');
      }
    });
  } else {
    if(allBtns[0]){allBtns[0].style.setProperty('background','rgba(255,255,255,.2)','important');allBtns[0].style.setProperty('color','#fff','important');}
    if(allBtns[1]){
      allBtns[1].setAttribute('data-partner-btn','true');
      allBtns[1].style.setProperty('background','#ffffff','important');
      allBtns[1].style.setProperty('color','#3E4FE0','important');
      allBtns[1].style.setProperty('border','1.5px solid rgba(84,104,245,.3)','important');
    }
  }
},100);"""
    else:
        current_page = st.session_state.get('page', 'Pipeline')
        _page_to_nav = {"Pipeline":"Partner Leads","Partners":"Partner Portfolio","Merchants":"Merchants","MerchSim":"Merchant Sim","MissionCtrl":"Partners In Flight","Performance":"Partner Health","Benchmarks":"Rev Share","Insights":"Market Intel","Home":"Home"}
        active_nav = _page_to_nav.get(current_page, "Home")
        _badge_map = {"Partner Portfolio":"47","Partners In Flight":"3","Partner Leads":"24","Merchants":"12","Rev Share":"Apr 1"}
        btn_js = f"""
setTimeout(function(){{
  var activeNav='{active_nav}';
  var badges={str(_badge_map).replace("'",'"')};
  var sidebar=window.parent.document.querySelector('[data-testid="stSidebar"]');
  if(!sidebar)return;
  sidebar.querySelectorAll('button').forEach(function(btn){{
    var t=btn.textContent.trim();
    var isActive=(t===activeNav);
    var badge=badges[t]||'';
    // Style as dark sidebar nav item
    btn.style.cssText='display:flex !important;align-items:center !important;gap:9px !important;padding:8px 14px 8px 16px !important;cursor:pointer !important;border-radius:8px !important;margin:1px 8px !important;border:none !important;box-shadow:none !important;font-size:13px !important;font-weight:'+(isActive?'600':'400')+' !important;color:'+(isActive?'#8B9BFF':'#8991AC')+' !important;background:'+(isActive?'rgba(84,104,245,0.15)':'transparent')+' !important;border-left:2px solid '+(isActive?'#3E4FE0':'transparent')+' !important;text-align:left !important;width:calc(100% - 16px) !important;';
    // Add badge
    if(badge && !btn.querySelector('.nav-badge')){{
      var b=document.createElement('span');
      b.className='nav-badge';
      b.style.cssText='margin-left:auto;font-size:10px;font-weight:600;padding:1px 6px;border-radius:8px;font-family:var(--font);font-variant-numeric:tabular-nums;'+(badge==='3'?'background:rgba(196,56,74,0.22);color:#D9737F;':'background:rgba(255,255,255,0.08);color:#8991AC;');
      b.textContent=badge;
      btn.appendChild(b);
    }}
  }});
}},300);"""
    components.html(
        f"<script>var old=window.parent.document.getElementById('papo-css');if(old)old.remove();var s=window.parent.document.createElement('style');s.id='papo-css';s.textContent=`{escaped}`;window.parent.document.head.appendChild(s);{btn_js}</script>",
        height=0,
    )

# ══ Market Expansion — deterministic model ═════════════════════════════════════
# House rule from the build brief: nothing on screen is a number someone made up
# in prose. Every figure is either read out of a dataset (chip: the file name) or
# computed from a NAMED assumption the user can move on screen (chip: assumption).
# Keeping the model here — pure functions, no Streamlit — is what makes that
# checkable: these run in a test without a browser.

_MARKET_ISO = {
    "Brazil":"BR", "Mexico":"MX", "Colombia":"CO", "Argentina":"AR", "Chile":"CL",
    "India":"IN", "Indonesia":"ID", "UAE":"AE", "Saudi Arabia":"SA", "Nigeria":"NG",
    "South Africa":"ZA", "UK":"GB", "Germany":"DE", "France":"FR", "USA":"US",
    "Canada":"CA", "Japan":"JP", "Singapore":"SG", "Turkey":"TR", "Egypt":"EG",
}
_MARKET_ISO.update(_ISO_EXTRA)

# Defaults are the starting position of the on-screen sliders, not fixed truth.
_ASSUMPTIONS = {
    "local_acquiring_pp": (8.0,  "Local acquiring vs cross-border", 0.0, 15.0,
                           "Processing on a domestic licence instead of cross-border. "
                           "Issuers decline foreign-acquired attempts far more often."),
    "failover_pp":        (3.5,  "Retry / failover on a second provider", 0.0, 8.0,
                           "A declined attempt re-routed to a second acquirer. Only "
                           "applies when moving from one provider to two or more."),
    "method_pp_full":     (6.0,  "Full local method coverage", 0.0, 12.0,
                           "Earned in proportion to the market share of the local "
                           "methods you are missing, so partial coverage earns part."),
    "token_pp":           (1.5,  "Network tokenisation / account updater", 0.0, 4.0,
                           "Recovers expired-card declines. Subscription models feel "
                           "this most."),
    "ceiling_pct":        (97.0, "Practical approval ceiling", 90.0, 99.0,
                           "No routing change pushes approval past this. Uplift is "
                           "always capped by the headroom beneath it."),
    "cb_bps_base":        (65.0, "Baseline chargeback rate (bps)", 0.0, 300.0,
                           "Chargebacks per 10,000 transactions before a fraud layer."),
    "cb_reduction_pct":   (40.0, "Chargeback reduction with a fraud layer", 0.0, 80.0,
                           "Effect of adding 3DS plus a fraud provider."),
}


def _assumption_defaults():
    return {k: v[0] for k, v in _ASSUMPTIONS.items()}


def market_providers(iso, verticals=None):
    """Providers actually live in this market. Source: source_of_truth.xlsx."""
    return find_partners(country_iso=iso, verticals=verticals or None, live_only=True)


def market_method_gap(market, merchant_methods):
    """Which of the market's own payment methods the merchant does not yet accept.

    Returns (covered_share, gap_rows). Shares come from _MARKET_PROFILES, so the
    arithmetic is over a published mix rather than a guess.
    """
    prof = _MARKET_PROFILES.get(market, {})
    mix = prof.get("payment_methods", [])
    have = " ".join(merchant_methods).lower()
    covered, rows = 0, []
    for name, share in mix:
        key = name.split("(")[0].strip().lower()
        token = key.split("/")[0].strip()
        hit = any(w and w in have for w in (token, key)) or (
            "card" in key and "card" in have)
        if hit:
            covered += share
        rows.append({"method": name, "share": share, "covered": hit})
    return covered, rows


def simulate_expansion(*, merchant, market, added_providers, assumptions,
                       has_fraud_layer, provider_caps):
    """Model one expansion. Pure arithmetic over the inputs — no hidden state.

    merchant        dict: aov, txn_mo, ar, methods, providers, sector
    provider_caps   dict of capability booleans read from source_of_truth.xlsx
    Returns every intermediate step so the UI can show its working.
    """
    a = assumptions
    ceiling = a["ceiling_pct"]
    ar0 = float(merchant["ar"])
    in_market = market_iso(market) in merchant.get("countries", [])
    # Entering a market you do not process in yet starts below your global rate:
    # the cross-border penalty is the same lever as local acquiring, inverted.
    baseline = ar0 if in_market else max(0.0, ar0 - a["local_acquiring_pp"])

    # Levers are collected first and scaled together. Applying them one at a time
    # would let whichever ran first eat all the headroom, which made the ordering
    # of the code look like a finding about the business — the largest lever could
    # show as zero purely for being evaluated last.
    raw = []

    def add(label, pp, why, kind="assumption"):
        if pp > 0.001:
            raw.append({"label": label, "pp": pp, "why": why, "kind": kind})

    if added_providers and not in_market:
        add("Local acquiring", a["local_acquiring_pp"],
            f"{added_providers[0]} processes domestically in {market}")
    total_providers = len(set(merchant.get("providers", [])) | set(added_providers))
    if total_providers >= 2 and added_providers:
        add("Retry / failover", a["failover_pp"],
            f"{total_providers} providers — declines can be re-routed")

    covered, gap_rows = market_method_gap(market, merchant.get("methods", []))
    uncovered = max(0, 100 - covered)
    if uncovered > 0 and added_providers:
        add("Local payment methods", a["method_pp_full"] * uncovered / 100.0,
            f"{uncovered}% of {market} volume sits on methods you do not accept yet")

    if provider_caps.get("SUPPORTS_TOKENIZATION") and added_providers:
        add("Tokenisation", a["token_pp"],
            "Network tokens recover expired-card declines")

    headroom = max(0.0, ceiling - baseline)
    wanted = sum(r["pp"] for r in raw)
    scale = min(1.0, headroom / wanted) if wanted > 0 else 0.0
    steps = [dict(r, pp=r["pp"] * scale, uncapped=r["pp"]) for r in raw if r["pp"] * scale > 0.001]
    ar1 = min(baseline + wanted * scale, ceiling)
    capped = scale < 1.0
    txns = float(merchant["txn_mo"])
    aov = float(merchant["aov"])

    declines0 = txns * (100 - ar0) / 100.0
    declines1 = txns * (100 - ar1) / 100.0
    recovered = max(0.0, declines0 - declines1)

    cb0 = a["cb_bps_base"]
    cb1 = cb0 * (1 - a["cb_reduction_pct"] / 100.0) if has_fraud_layer else cb0
    cb_txn0 = txns * cb0 / 10000.0
    cb_txn1 = txns * cb1 / 10000.0

    return {
        "in_market": in_market,
        "ar0": ar0, "ar_entry": ar0 if in_market else max(0.0, ar0 - a["local_acquiring_pp"]),
        "ar1": ar1, "uplift_pp": ar1 - ar0,
        "steps": steps, "capped": capped, "headroom": headroom,
        "uplift_uncapped": wanted,
        "declines0": declines0, "declines1": declines1, "recovered_txn": recovered,
        "recovered_rev": recovered * aov,
        "annual_rev": recovered * aov * 12,
        "cb_bps0": cb0, "cb_bps1": cb1,
        "cb_txn0": cb_txn0, "cb_txn1": cb_txn1,
        "cb_avoided": max(0.0, cb_txn0 - cb_txn1),
        "cb_cost_avoided": max(0.0, cb_txn0 - cb_txn1) * (aov + 25.0),
        "method_covered": covered, "method_gap": gap_rows,
        "provider_count": total_providers,
    }


def market_iso(market):
    return _MARKET_ISO.get(market, market[:2].upper())


def competitor_benchmark(market, exclude=None):
    """Who else already processes here, from _MERCHANT_PROFILES. Real rows only."""
    iso = market_iso(market)
    rows = [dict(v, key=k) for k, v in _MERCHANT_PROFILES.items()
            if iso in v.get("countries", []) and k != exclude]
    rows.sort(key=lambda m: -m["ar"])
    return rows


def expansion_tips(sim, merchant, market, added_providers, provider_caps, has_fraud_layer):
    """Tips fire off computed gaps, so each one can name the number behind it."""
    tips = []
    gap = [g for g in sim["method_gap"] if not g["covered"]]
    if gap:
        top = max(gap, key=lambda g: g["share"])
        tips.append(("Add " + top["method"],
                     f"{top['method']} is {top['share']}% of {market} volume and you do not "
                     f"accept it. It is the single largest uncovered slice of this market.",
                     f"+{sim['ar1'] - sim['ar_entry']:.1f}pp modelled once local methods are on"))
    if sim["provider_count"] < 2:
        tips.append(("Run a second provider",
                     "One provider means a decline is a lost sale — there is nowhere to retry "
                     "it, and no leverage at renewal.",
                     "Retry / failover uplift is unavailable below two providers"))
    if not has_fraud_layer and float(merchant["aov"]) >= 50:
        tips.append(("Put a fraud layer in front",
                     f"At a ${float(merchant['aov']):.0f} average order, chargebacks cost the "
                     f"goods as well as the fee. 3DS plus a fraud provider is the standard pair.",
                     f"−{sim['cb_bps0'] - sim['cb_bps0'] * 0.6:.0f} bps modelled"))
    if not provider_caps.get("SUPPORTS_RECURRING_PAYMENTS") and "subscription" in \
            merchant.get("sector", "").lower():
        tips.append(("Check recurring support",
                     "This is a subscription book, but the provider you picked is not flagged "
                     "for recurring payments in the coverage data.",
                     "source_of_truth.xlsx"))
    prof = _MARKET_PROFILES.get(market, {})
    if prof.get("settlement"):
        tips.append(("Model the settlement lag", prof["settlement"],
                     "Market profile"))
    if prof.get("fx"):
        tips.append(("Check FX and repatriation", prof["fx"], "Market profile"))
    return tips


# ── Landing Page ───────────────────────────────────────────────────────────────
# Identity-first sign-in. One field decides everything: the work domain selects
# the identity provider (Home Realm Discovery), so the three provider buttons
# collapse into a single path. The chooser only appears when the domain is
# unknown *and* at least one real OIDC client is configured — in a demo
# deployment there is nothing to choose, so it never appears at all.
_SSO_PROVIDERS = [("google", "Google"), ("microsoft", "Microsoft"), ("okta", "Okta")]
_SSO_KEYS = [k for k, _ in _SSO_PROVIDERS]

_INTERNAL_DOMAINS = ("yuno.com", "yuno.co", "y.uno")

# Which provider owns which domain. Extend without touching code by adding
# [auth.domains] to .streamlit/secrets.toml.
_DOMAIN_ROUTES = {d: "google" for d in _INTERNAL_DOMAINS}

# The credential decides the role — nobody declares who they are up front.
_ACCESS_CODES = {"Yuno": "internal", "Partners": "partner"}

_EMAIL_RE = r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$"

_SSO_ICONS = {
    "google": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18">'
              '<path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>'
              '<path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"/>'
              '<path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/>'
              '<path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/></svg>',
    "microsoft": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 21">'
                 '<rect x="1" y="1" width="9" height="9" fill="#F25022"/><rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>'
                 '<rect x="1" y="11" width="9" height="9" fill="#00A4EF"/><rect x="11" y="11" width="9" height="9" fill="#FFB900"/></svg>',
    "okta": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
            '<circle cx="10" cy="10" r="9" fill="#007DC1"/><circle cx="10" cy="10" r="5.4" fill="#fff"/></svg>',
}


def _icon_uri(key):
    """Inline the provider mark as a background image — survives any HTML sanitiser."""
    return "data:image/svg+xml;base64," + _b64.b64encode(_SSO_ICONS[key].encode()).decode()


def _sso_configured(provider):
    """True only when a real OIDC client exists for this provider."""
    try:
        auth = st.secrets["auth"]
        if not (auth.get("redirect_uri") and auth.get("cookie_secret")):
            return False
        return bool(auth.get(provider, {}).get("client_id"))
    except Exception:
        return False


def _any_sso_live():
    return any(_sso_configured(p) for p in _SSO_KEYS)


def _domain_routes():
    routes = dict(_DOMAIN_ROUTES)
    try:
        routes.update({k.lower(): v for k, v in st.secrets["auth"]["domains"].items()})
    except Exception:
        pass
    return routes


def _role_for_email(email):
    return "internal" if (email or "").rsplit("@", 1)[-1].lower() in _INTERNAL_DOMAINS else "partner"


def _grant(role):
    st.session_state.role = role
    st.session_state.pending_role = None
    st.session_state.sso_method = None
    st.session_state.auth_email = ""
    st.session_state.pw_error = False
    st.session_state.page = "Home"
    st.query_params.clear()
    st.query_params["role"] = role
    st.query_params["page"] = "Home"
    st.rerun()


def _reset_auth():
    st.session_state.sso_method = None
    st.session_state.pending_role = None
    st.session_state.auth_email = ""
    st.session_state.pw_error = False
    st.query_params.clear()
    st.rerun()


def _enter_with(email, provider=None):
    """One decision point for every route into the portal."""
    st.session_state.auth_email_used = email
    st.session_state.partner_identity = resolve_partner(email)
    st.session_state.alliance_alerted = None
    provider = provider or _domain_routes().get(email.rsplit("@", 1)[-1].lower())
    if provider and _sso_configured(provider):
        st.login(provider)          # real redirect; the IdP returns the identity
        st.stop()
    _grant(_role_for_email(email))  # nothing configured — the typed address is the whole flow


_YUNO_MARK = ('<div class="yl-mark">'
              '<span></span><span class="m"></span><span class="m"></span><span class="o"></span>'
              '<span class="m"></span><span></span><span></span><span class="m"></span>'
              '<span class="m"></span><span></span><span></span><span class="m"></span>'
              '<span class="o"></span><span class="m"></span><span class="m"></span><span></span>'
              '</div>')

_SHIELD = ('<svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="#8991AC" '
           'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="M7 1.4L2.6 3.3v3.9c0 2.7 1.9 4.6 4.4 5.4 2.5-.8 4.4-2.7 4.4-5.4V3.3L7 1.4z"/></svg>')

_KEY = ('<svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="#CBD3FA" '
        'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" style="margin-top:2px;flex:0 0 13px">'
        '<rect x="2.6" y="6" width="8.8" height="6.4" rx="1.6"/><path d="M4.9 6V4.3a2.1 2.1 0 014.2 0V6"/></svg>')


def show_landing():
    # A real IdP round trip already happened — take the identity it returned.
    try:
        if st.user.is_logged_in:
            _grant(_role_for_email(getattr(st.user, "email", "")))
    except Exception:
        pass

    method = st.session_state.get("sso_method")
    intent = st.query_params.get("auth")
    if intent and not method:
        if intent in _SSO_KEYS:
            stored = st.session_state.get("auth_email", "")
            if stored:
                _enter_with(stored, provider=intent)
            if _sso_configured(intent):
                st.login(intent)
                st.stop()
        if intent in ("code", "providers"):
            st.session_state.sso_method = method = intent

    if method == "providers":
        return _show_provider_chooser()
    if method == "code":
        return _show_access_code()
    return _show_front_door()


# ── Front door: one field ─────────────────────────────────────────────────────
def _show_front_door():
    live = _any_sso_live()
    st.markdown(f"""
<div class="yl">
  <div class="yl-brand">{_YUNO_MARK}<span class="yl-word">yuno</span></div>
  <div class="yl-title">Yuno Alliance</div>
  <div class="yl-sub">Sign in with your work account.</div>
</div>""", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False, border=False):
        email = st.text_input("Work email", placeholder="name@company.com",
                              key="login_email", label_visibility="collapsed")
        if st.session_state.get("pw_error"):
            st.markdown('<p class="yl-err" role="alert">Enter a valid work email address.</p>',
                        unsafe_allow_html=True)
        submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

    if submitted:
        addr = (email or "").strip()
        if not _re.match(_EMAIL_RE, addr):
            st.session_state.pw_error = True
            st.rerun()
        st.session_state.pw_error = False
        if live and addr.rsplit("@", 1)[-1].lower() not in _domain_routes():
            st.session_state.auth_email = addr        # domain unknown — ask once
            st.session_state.sso_method = "providers"
            st.rerun()
        _enter_with(addr)

    chip = ("SOC 2 Type II · 256-bit TLS · SSO enforced" if live
            else "SOC 2 Type II · 256-bit TLS · demo mode")
    st.markdown(f"""
<div class="yl">
  <div class="yl-or"><span>or</span></div>
  <a class="yl-alt" href="?auth=code">Use an access code</a>
  <div class="yl-foot">{_SHIELD}<span>{chip}</span></div>
</div>""", unsafe_allow_html=True)


# ── Fallback: unknown domain, and real providers exist to choose between ──────
def _show_provider_chooser():
    email = st.session_state.get("auth_email", "")
    domain = email.rsplit("@", 1)[-1] if "@" in email else "that domain"
    icon_css = "".join(
        f'a.yl-sso[href="?auth={k}"]::before{{background-image:url({_icon_uri(k)});}}'
        for k, _ in _SSO_PROVIDERS)
    buttons = "".join(
        f'<a class="yl-sso" href="?auth={k}" aria-label="Continue with {n}">Continue with {n}'
        + ('<span class="yl-chip yl-chip-live">SSO</span>' if _sso_configured(k)
           else '<span class="yl-chip">Demo</span>') + '</a>'
        for k, n in _SSO_PROVIDERS)

    st.markdown(f"""
<style>{icon_css}</style>
<div class="yl">
  <div class="yl-step">
    <div class="yl-step-badge">{_KEY}</div>
    <div class="yl-h">Choose your provider</div>
    <div class="yl-p">We don't have a sign-in route for <b>{domain}</b> yet.<br>Pick the one your organisation uses.</div>
  </div>
  {buttons}
</div>""", unsafe_allow_html=True)

    if st.button("Back", key="prov_back", use_container_width=True):
        _reset_auth()


# ── Access code ───────────────────────────────────────────────────────────────
def _show_access_code():
    st.markdown(f"""
<div class="yl"><div class="yl-step">
  <div class="yl-step-badge">
    <svg width="21" height="21" viewBox="0 0 22 22" fill="none" stroke="#8B9BFF" stroke-width="1.6"
         stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="9.5" width="14" height="10" rx="2.5"/><path d="M7.5 9.5V6.8a3.5 3.5 0 017 0v2.7"/>
    </svg>
  </div>
  <div class="yl-h">Access code</div>
  <div class="yl-p">Enter the code from your Yuno Partner Manager.<br>Your code decides what you can see.</div>
</div></div>""", unsafe_allow_html=True)

    with st.form("code_form", clear_on_submit=False, border=False):
        code = st.text_input("Access code", type="password", placeholder="Access code",
                             key="pw_input", label_visibility="collapsed")
        if st.session_state.get("pw_error"):
            st.markdown('<p class="yl-err" role="alert">That code was not recognised — '
                        'contact your Yuno Partner Manager.</p>', unsafe_allow_html=True)
        f1, f2 = st.columns([1, 1.4])
        back = f1.form_submit_button("Back", use_container_width=True)
        go = f2.form_submit_button("Enter portal", use_container_width=True, type="primary")

    if back:
        _reset_auth()
    if go:
            role = _ACCESS_CODES.get((code or "").strip())
            if role:
                _grant(role)
            st.session_state.pw_error = True
            st.rerun()

    st.markdown('<div class="yl"><div class="yl-foot">' + _SHIELD +
                '<span>Codes are issued per partner and rotate quarterly</span></div></div>',
                unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
def show_sidebar():
    is_internal = st.session_state.role == "internal"
    role_label = "INTERNAL" if is_internal else "PARTNER"
    # An external partner sees the co-brand, so it is always obvious whose data
    # this is and that they are not looking at the whole programme.
    _pname = external_partner_name()
    _side_lockup = (f'yuno <span style="font-weight:400;color:#8991AC;">&times;</span> {_pname}'
                    if _pname else "yuno")

    with st.sidebar:
        # Logo + role badge header
        st.markdown(f"""
<div style="padding:18px 16px 14px;border-bottom:0.5px solid rgba(255,255,255,0.05);display:flex;align-items:center;gap:9px;">
  <div style="display:grid;grid-template-columns:repeat(4,5px);gap:1.5px;">
    <span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:transparent;"></span>
    <span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span>
    <span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span>
    <span style="width:5px;height:5px;border-radius:1px;background:transparent;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;opacity:0.4;"></span><span style="width:5px;height:5px;border-radius:1px;background:#3E4FE0;"></span>
  </div>
  <span style="font-size:16px;font-weight:600;color:#EEF0FA;letter-spacing:-0.02em;">{_side_lockup}</span>
  <span style="margin-left:auto;font-size:10px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;background:rgba(84,104,245,0.2);color:#8B9BFF;padding:2px 7px;border-radius:4px;border:0.5px solid rgba(84,104,245,0.3);">{role_label}</span>
</div>""", unsafe_allow_html=True)

        # Nav sections
        if is_internal:
            NAV_SECTIONS = [
                ("OVERVIEW", [
                    ("Home",        "Home"),
                    ("Partners",    "Partner Portfolio"),
                ]),
                ("PIPELINE & FLOW", [
                    ("MissionCtrl", "Partners In Flight"),
                    ("Pipeline",    "Partner Leads"),
                    ("LeadGen",     "Lead Generation"),
                    ("Cosell",      "Co-sell Sprint"),
                ]),
                ("PERFORMANCE", [
                    ("Performance", "Partner Health"),
                    ("Benchmarks",  "Rev Share"),
                ]),
                ("INTELLIGENCE", [
                    ("Insights",    "Market Intel"),
                ]),
                ("TOOLS", [
                    ("Expansion",   "Market Expansion"),
                    ("MerchSim",    "Merchant Sim"),
                ]),
            ]
        else:
            NAV_SECTIONS = [
                ("OVERVIEW", [
                    ("Home",        "Home"),
                    ("Partners",    "Partner Portfolio"),
                ]),
                ("PERFORMANCE", [
                    ("Performance", "Partner Health"),
                    ("Benchmarks",  "Benchmarks"),
                ]),
                ("INTELLIGENCE", [
                    ("Insights",    "Market Intel"),
                ]),
                ("COLLABORATE", [
                    ("GTM",         "Joint GTM"),
                    ("Share",       "Send to Yuno"),
                ]),
            ]

        _NAV_BADGES = {"Partner Portfolio":"47","Partners In Flight":"3","Partner Leads":"24","Merchants":"12","Rev Share":"Apr 1","Recommendations":"12"}

        for section_label, items in NAV_SECTIONS:
            st.markdown(f'<div style="padding:14px 16px 4px;font-size:10px;font-weight:500;letter-spacing:0.12em;text-transform:uppercase;color:#858CA6;">{section_label}</div>', unsafe_allow_html=True)
            for page_key, label in items:
                if st.button(label, key=f"nav_{page_key}", use_container_width=True, type="secondary"):
                    st.session_state.page = page_key
                    st.session_state.integration_open = False
                    st.query_params["page"] = page_key
                    st.query_params["role"] = st.session_state.role
                    st.rerun()

        # User footer
        _who = signed_in_name()
        _initials = "".join(w[0] for w in _who.split()[:2]).upper() or "•"
        _org = "Yuno" if is_internal else (_pname or company_from_domain(signed_in_email()) or "Partner")
        _line = "Yuno · Partnerships" if is_internal else f"{_org} · Partner Alliance"
        st.markdown(f"""
<div style="margin-top:auto;padding:12px 14px;border-top:0.5px solid rgba(255,255,255,0.05);display:flex;align-items:center;gap:9px;">
  <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,{'#3E4FE0,#6B7BFF' if is_internal else '#5A6486,#8B94BC'});display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:white;flex-shrink:0;">{_initials}</div>
  <div><div style="font-size:12px;font-weight:600;color:#D2D7EA;">{_who}</div><div style="font-size:10px;color:#4A5170;">{_line}</div></div>
</div>""", unsafe_allow_html=True)


# ── Stat Row ───────────────────────────────────────────────────────────────────
def stat_row(stats):
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        val_color = f"color:{s.get('val_color','#3E4FE0')};"
        delta_color = {"up":"#5A7A00","down":"#C4384A","flat":"#858CA6"}.get(s.get("delta_type","flat"), "#858CA6")
        col.markdown(f"""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:12px;padding:18px 20px;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:12px 12px 0 0;"></div>
  <div style="font-size:10px;color:#858CA6;letter-spacing:0.5px;text-transform:uppercase;font-weight:600;margin-bottom:8px;">{s['label']}</div>
  <div style="font-size:20px;font-weight:700;font-family:var(--font);font-variant-numeric:tabular-nums;letter-spacing:-1px;line-height:1;{val_color}">{s['value']}</div>
  <div style="font-size:11px;margin-top:6px;color:{delta_color};">{s['delta']}</div>
</div>""", unsafe_allow_html=True)

# ── Pipeline View ──────────────────────────────────────────────────────────────
def show_pipeline():
    is_internal = st.session_state.role == "internal"

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:#080911;border-radius:16px;padding:24px 28px;margin-bottom:14px;position:relative;overflow:hidden;">
  <div style="position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,0.03) 1px,transparent 0);background-size:22px 22px;pointer-events:none;"></div>
  <div style="position:relative;z-index:1;">
    <div style="font-size:20px;font-weight:700;color:#F1F3FB;letter-spacing:-0.02em;margin-bottom:4px;">Partner Leads</div>
    <div style="font-size:12px;color:#676E8A;margin-bottom:14px;">Track merchant opportunities from prospect to won. Filter by region to see deal flow.</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#8B9BFF;">$4.2M</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Pipeline Value</div></div>
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#B9C2FF;">24</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Active Deals</div></div>
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#D08A1A;">$175K</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Avg Deal Size</div></div>
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#E0ED80;">38%</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Win Rate</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Region toggles ────────────────────────────────────────────────────────
    _pipe_regions = {
        "All":      {"deals":24,"value":"$4.2M","prospect":6,"qualified":5,"eval":7,"nego":4,"won":2},
        "LATAM":    {"deals":10,"value":"$1.8M","prospect":3,"qualified":2,"eval":3,"nego":1,"won":1},
        "Brasil":   {"deals":5,"value":"$0.9M","prospect":1,"qualified":1,"eval":2,"nego":1,"won":0},
        "N. America":{"deals":4,"value":"$0.8M","prospect":1,"qualified":1,"eval":1,"nego":1,"won":0},
        "EMEA":     {"deals":3,"value":"$0.5M","prospect":1,"qualified":1,"eval":0,"nego":0,"won":1},
        "APAC":     {"deals":2,"value":"$0.2M","prospect":0,"qualified":0,"eval":1,"nego":1,"won":0},
    }
    sel_pipe_region = st.session_state.get("pipe_region", "All")
    pr_cols = st.columns(len(_pipe_regions))
    for ri, (rname, rdata) in enumerate(_pipe_regions.items()):
        if pr_cols[ri].button(f"{rname} ({rdata['deals']})", key=f"pipe_reg_{ri}", use_container_width=True):
            st.session_state["pipe_region"] = rname
            st.rerun()

    # Style region buttons
    components.html(f"""<script>
setTimeout(function(){{
  var doc = window.parent.document;
  var active = '{sel_pipe_region}';
  doc.querySelectorAll('button').forEach(function(btn){{
    var t = btn.textContent.trim();
    if(t.match(/^(All|LATAM|Brasil|N\\. America|EMEA|APAC)\s*\(/)){{
      var isOn = t.startsWith(active+' (') || (active==='All' && t.startsWith('All ('));
      btn.style.cssText='background:'+(isOn?'#080911':'#fff')+' !important;border:1px solid '+(isOn?'#3E4FE0':'#E2E6F4')+' !important;border-radius:8px !important;padding:8px 8px !important;font-size:11px !important;color:'+(isOn?'#8B9BFF':'#676E8A')+' !important;font-weight:'+(isOn?'700':'500')+' !important;cursor:pointer !important;box-shadow:none !important;';
    }}
  }});
}},200);
</script>""", height=0)

    # ── Region overview table ─────────────────────────────────────────────────
    rd = _pipe_regions.get(sel_pipe_region, _pipe_regions["All"])
    stages = [("Prospect", rd["prospect"], "#858CA6"), ("Qualified", rd["qualified"], "#5A6486"), ("Evaluation", rd["eval"], "#3E4FE0"), ("Negotiation", rd["nego"], "#B36200"), ("Won", rd["won"], "#5A7A00")]
    total_d = rd["deals"] or 1
    bar_html = '<div style="display:flex;gap:2px;height:8px;margin:10px 0;border-radius:4px;overflow:hidden;">'
    for label, count, color in stages:
        w = max(int(count / total_d * 100), 2) if count > 0 else 0
        if w > 0:
            bar_html += f'<div style="width:{w}%;background:{color};" title="{label}: {count}"></div>'
    bar_html += '</div>'

    stage_pills = "".join(f'<div style="text-align:center;flex:1;padding:8px;background:#fff;border:0.5px solid #E2E6F4;border-radius:8px;"><div style="font-size:15px;font-weight:700;color:{color};">{count}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;margin-top:2px;">{label}</div></div>' for label, count, color in stages)

    st.markdown(f'<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:12px;padding:16px 20px;margin-bottom:14px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                f'<span style="font-size:14px;font-weight:700;color:#10131C;">{sel_pipe_region}</span>'
                f'<span style="font-size:13px;font-weight:700;color:#3E4FE0;">{rd["value"]}</span></div>'
                f'{bar_html}'
                f'<div style="display:flex;gap:6px;margin-top:8px;">{stage_pills}</div>'
                f'</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Deal Board</div>', unsafe_allow_html=True)

    st.markdown("""
<div style="margin-top:20px;margin-bottom:10px;">
  <span style="font-size:15px;font-weight:700;color:#10131C;letter-spacing:-0.3px;">Deal Board</span>
  <span style="font-size:11px;color:#858CA6;margin-left:10px;">Drag to move · Click to open · Internal notes visible to Yuno BD only</span>
</div>
""", unsafe_allow_html=True)

    # Kanban board as HTML (no <style> tag — styles injected via JS already)
    kanban_html = """
<div class="pipeline-wrap">
<div class="pipeline-board">

<!-- Prospect -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#676E8A;">Prospect</span><span class="stage-num">6</span></div>
  <div class="pcard"><div class="pcard-name">Qatar Airways</div><div class="pcard-meta"><span class="pill cat-psp">Travel</span><span class="pill p-amber">Warm</span></div><div class="pcard-val">$80K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R. · via Adyen ref</div><div class="pbar"><div class="pfill" style="width:15%;background:#858CA6;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Bancolombia</div><div class="pcard-meta"><span class="pill cat-acquirer">Banking</span><span class="pill p-blue">Inbound</span></div><div class="pcard-val">$120K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">JL</span>Jorge L. · Direct</div><div class="pbar"><div class="pfill" style="width:10%;background:#5A6486;"></div></div></div>
  <div class="pcard"><div class="pcard-name">iFood</div><div class="pcard-meta"><span class="pill cat-baas">Food</span><span class="pill p-amber">Pilot</span></div><div class="pcard-val">$200K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">MC</span>Maria C. · Direct</div><div class="pbar"><div class="pfill" style="width:12%;background:#B36200;"></div></div></div>
</div>

<!-- Qualified -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#8B94BC;">Qualified</span><span class="stage-num">5</span></div>
  <div class="pcard"><div class="pcard-name">Rappi</div><div class="pcard-meta"><span class="pill cat-apm">Super App</span><span class="pill p-green">Hot</span></div><div class="pcard-val">$350K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:30%;background:#5A7A00;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Falabella</div><div class="pcard-meta"><span class="pill cat-acquirer">Retail</span><span class="pill p-blue">Active</span></div><div class="pcard-val">$180K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">AP</span>Ana P. · Partner ref</div><div class="pbar"><div class="pfill" style="width:28%;background:#5A6486;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Despegar</div><div class="pcard-meta"><span class="pill cat-fraud">Travel</span><span class="pill p-purple">Trial</span></div><div class="pcard-val">$95K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DG</span>Diego G.</div><div class="pbar"><div class="pfill" style="width:25%;background:#5468F5;"></div></div></div>
</div>

<!-- Evaluation -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#8B9BFF;">Evaluation</span><span class="stage-num">7</span></div>
  <div class="pcard"><div class="pcard-name">Spotify</div><div class="pcard-meta"><span class="pill cat-psp">Streaming</span><span class="pill p-green">Hot</span></div><div class="pcard-val">$620K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">RV</span>Ricardo V. · Direct</div><div class="pbar"><div class="pfill" style="width:55%;background:#5468F5;"></div></div></div>
  <div class="pcard"><div class="pcard-name">PedidosYa</div><div class="pcard-meta"><span class="pill cat-apm">Food</span><span class="pill p-teal">Active</span></div><div class="pcard-val">$240K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:50%;background:#0086A8;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Claro</div><div class="pcard-meta"><span class="pill cat-acquirer">Telco</span><span class="pill p-amber">Stalled</span></div><div class="pcard-val">$310K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">LM</span>Luisa M. · Partner</div><div class="pbar"><div class="pfill" style="width:48%;background:#B36200;"></div></div></div>
  <div class="pcard"><div class="pcard-name">MercadoLibre</div><div class="pcard-meta"><span class="pill cat-baas">E-commerce</span><span class="pill p-amber">New</span></div><div class="pcard-val">$440K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">MC</span>Maria C.</div><div class="pbar"><div class="pfill" style="width:42%;background:#B36200;"></div></div></div>
</div>

<!-- Negotiation -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#D08A1A;">Negotiation</span><span class="stage-num">2</span></div>
  <div class="pcard"><div class="pcard-name">Uber</div><div class="pcard-meta"><span class="pill cat-acquirer">Mobility</span><span class="pill p-green">High Priority</span></div><div class="pcard-val">$850K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">FM</span>Felipe M. · Direct</div><div class="pbar"><div class="pfill" style="width:75%;background:#3E4FE0;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Cinépolis</div><div class="pcard-meta"><span class="pill cat-apm">Entertainment</span><span class="pill p-blue">Regional</span></div><div class="pcard-val">$110K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DG</span>Diego G.</div><div class="pbar"><div class="pfill" style="width:70%;background:#0086A8;"></div></div></div>
</div>

<!-- Won -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#8FA300;">Won</span><span class="stage-num">2</span></div>
  <div class="pcard" style="border-color:rgba(90,107,0,.25);"><div class="pcard-name">Netflix</div><div class="pcard-meta"><span class="pill cat-psp">Streaming</span><span class="pill p-green">Live</span></div><div class="pcard-val">$1.2M ARR signed</div><div class="pcard-owner"><span class="mini-av ma-e">TK</span>Tom K. · Direct</div><div class="pbar"><div class="pfill" style="width:100%;background:#5A7A00;"></div></div></div>
  <div class="pcard" style="border-color:rgba(90,107,0,.25);"><div class="pcard-name">Linio</div><div class="pcard-meta"><span class="pill cat-fraud">E-commerce</span><span class="pill p-green">Live</span></div><div class="pcard-val">$290K ARR signed</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:100%;background:#5A7A00;"></div></div></div>
</div>

</div></div>"""
    st.markdown(kanban_html, unsafe_allow_html=True)

    # Bottom row: funnel + activity
    col_funnel, col_activity = st.columns([3, 2])

    with col_funnel:
        st.markdown('<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:18px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;font-weight:700;color:#10131C;margin-bottom:2px;">Pipeline Funnel</div><div style="font-size:11px;color:#858CA6;margin-bottom:14px;">Current quarter · all categories</div>', unsafe_allow_html=True)
        funnel_data = [("Prospect",6,100,"#858CA6"),("Qualified",5,83,"#676E8A"),("Evaluation",7,100,"#5468F5"),("Negotiation",4,50,"#B36200"),("Won",2,33,"#5A7A00")]
        funnel_html = ""
        for label, count, pct, color in funnel_data:
            funnel_html += f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
  <span style="font-size:11px;color:#676E8A;width:90px;text-align:right;flex-shrink:0;">{label}</span>
  <div style="flex:1;height:24px;background:#F7F8FD;border-radius:4px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:{color};display:flex;align-items:center;padding-left:10px;font-size:10px;font-family:var(--font);font-variant-numeric:tabular-nums;font-weight:600;color:rgba(0,0,0,0.7);">{count} deals</div>
  </div>
  <span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#676E8A;width:20px;">{count}</span>
</div>"""
        st.markdown(funnel_html, unsafe_allow_html=True)

        if is_internal:
            st.markdown("""
<div style="border:1px solid rgba(47,138,31,.22);background:rgba(47,138,31,.04);border-radius:10px;padding:13px 16px;margin-top:16px;">
  <div style="font-size:10px;font-weight:700;color:#B36200;letter-spacing:.9px;text-transform:uppercase;margin-bottom:10px;">🔒 Internal Yuno Only</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#676E8A;">Blended margin (est.)</span><span style="font-family:var(--font);font-variant-numeric:tabular-nums;color:#B36200;">61%</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#676E8A;">Committed quota coverage</span><span style="font-family:var(--font);font-variant-numeric:tabular-nums;color:#B36200;">2.4×</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;"><span style="color:#676E8A;">At-risk deals (&gt;90d stalled)</span><span style="font-family:var(--font);font-variant-numeric:tabular-nums;color:#B36200;">3</span></div>
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_activity:
        st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:18px;">
  <div style="font-size:13px;font-weight:700;color:#10131C;margin-bottom:2px;">Recent Activity</div>
  <div style="font-size:11px;color:#858CA6;margin-bottom:14px;">Last 48 hours</div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#5A7A00;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#676E8A;line-height:1.55;"><strong style="color:#10131C;">Uber</strong> moved to Negotiation. MSA draft sent.</div><div style="font-size:10px;color:#858CA6;font-family:var(--font);font-variant-numeric:tabular-nums;margin-top:2px;">2h ago · Daniela R.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#5A6486;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#676E8A;line-height:1.55;"><strong style="color:#10131C;">Spotify</strong> technical review call scheduled for Dec 18.</div><div style="font-size:10px;color:#858CA6;font-family:var(--font);font-variant-numeric:tabular-nums;margin-top:2px;">5h ago · Ricardo V.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#B36200;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#676E8A;line-height:1.55;"><strong style="color:#10131C;">MercadoLibre</strong> added as new e-commerce opportunity.</div><div style="font-size:10px;color:#858CA6;font-family:var(--font);font-variant-numeric:tabular-nums;margin-top:2px;">Yesterday · Maria C.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#3E4FE0;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#676E8A;line-height:1.55;"><strong style="color:#10131C;">Netflix</strong> integration live. First transaction processed.</div><div style="font-size:10px;color:#858CA6;font-family:var(--font);font-variant-numeric:tabular-nums;margin-top:2px;">Yesterday · Tom K.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;">
    <div style="width:7px;height:7px;border-radius:50%;background:#5468F5;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#676E8A;line-height:1.55;"><strong style="color:#10131C;">Despegar</strong> trial extended to Jan 15. Positive signal.</div><div style="font-size:10px;color:#858CA6;font-family:var(--font);font-variant-numeric:tabular-nums;margin-top:2px;">2d ago · Diego G.</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Partners View ──────────────────────────────────────────────────────────────
def _partner_detail(p):
    """Render partner detail page with tabs (Salesforce-style)."""
    if st.button("← Back to Directory", key="back_to_dir"):
        st.session_state.selected_partner = None
        st.session_state.partner_tab = "Overview"
        st.rerun()

    STATUS_BADGE = {"Live": ("background:#3F5208;color:#fff;", "ACTIVE"), "Agreement Signed": ("background:#464F6E;color:#fff;", "AGREEMENT SIGNED"), "Agreement Review": ("background:#2F3FC4;color:#fff;", "IN REVIEW"), "Negotiation": ("background:#B36200;color:#fff;", "NEGOTIATION"), "Prospect": ("background:#6E3C00;color:#fff;", "PROSPECT"), "Lost": ("background:#C4384A;color:#fff;", "LOST")}
    badge_style, badge_label = STATUS_BADGE.get(p["status"], ("background:#676E8A;color:#fff;", p["status"].upper()))
    scope = "Global" if p.get("region","") in ("Global","APAC/EMEA") or p.get("country","") == "Global" else "Regional"
    strategic_tag = '<span style="background:#FAF0D0;color:#6E3C00;font-size:10px;font-weight:700;padding:3px 10px;border-radius:4px;margin-left:10px;letter-spacing:0.5px;">STRATEGIC</span>' if p.get("strategic") else ""

    st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
  <div>
    <div style="display:flex;align-items:center;gap:0;"><span style="font-size:22px;font-weight:700;color:#10131C;letter-spacing:-0.5px;">{p['name']}</span>{strategic_tag}</div>
    <div style="font-size:13px;color:#858CA6;margin-top:4px;">{p['type']} &middot; {p.get('country','')} &middot; {p.get('region','')} &middot; {p.get('manager','Unassigned')}</div>
  </div>
  <span style="{badge_style}font-size:11px;font-weight:700;padding:6px 18px;border-radius:20px;letter-spacing:0.5px;">{badge_label}</span>
</div>""", unsafe_allow_html=True)

    # Completeness
    checks = [p.get("nda"), p.get("revshare"), p.get("integration_ready"), p.get("integration_used"), bool(p.get("comments"))]
    check_labels = ["NDA Signed", "Rev Share Contract", "Integration Ready", "Merchant Using", "Notes Added"]
    done = sum(1 for c in checks if c)
    pct = int(done / len(checks) * 100)
    bar_color = "#5A7A00" if pct >= 70 else "#B36200" if pct >= 40 else "#C4384A"
    tags_html = "".join(f'<span style="font-size:10px;color:{"#3F5208" if checks[i] else "#858CA6"};padding:3px 8px;border-radius:4px;background:{"#F4F8E4" if checks[i] else "#F7F8FD"};border:1px solid {"#E7F0C4" if checks[i] else "#E2E6F4"};">{check_labels[i]}</span>' for i in range(len(checks)))
    st.markdown(f"""
<div style="margin:12px 0 16px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
    <div style="flex:1;height:5px;background:#E2E6F4;border-radius:3px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:{bar_color};border-radius:3px;transition:width 0.3s;"></div></div>
    <span style="font-size:12px;font-weight:700;color:{bar_color};">{pct}%</span>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:5px;">{tags_html}</div>
</div>""", unsafe_allow_html=True)

    TABS = ["Overview", "Contacts", "Contracts", "SLA", "Revenue", "Questionnaires", "Audit Log"]
    tab_cols = st.columns(len(TABS))
    for i, (col, tab) in enumerate(zip(tab_cols, TABS)):
        if col.button(tab, key=f"ptab_{i}", use_container_width=True):
            st.session_state.partner_tab = tab
            st.rerun()

    active_tab = st.session_state.partner_tab

    # ── Overview ──────────────────────────────────────────────────────────────
    if active_tab == "Overview":
        st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:28px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:24px;">Basic Information</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 48px;">
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Provider Name</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p['name']}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Type</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p['type']}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Scope</div><div style="font-size:14px;font-weight:600;color:#10131C;">{scope}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Deal Stage</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p['status']}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Country</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p.get('country','-')}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Region</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p.get('region','-')}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Partner Tier</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p.get('tier','-')}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Management</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p.get('mgmt_type','-')}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Partner Manager</div><div style="font-size:14px;font-weight:600;color:#10131C;">{p.get('manager','-')}</div></div>
    <div style="padding:14px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Strategic Partner</div><div style="font-size:14px;font-weight:600;color:#10131C;">{'Yes' if p.get('strategic') else 'No'}</div></div>
    <div style="padding:14px 0;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Notes</div><div style="font-size:14px;color:#676E8A;">{p.get('comments') or '-'}</div></div>
    <div style="padding:14px 0;"><div style="font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">NDA Signed</div><div style="font-size:14px;font-weight:600;color:#10131C;">{'Yes' if p.get('nda') else 'No'}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

        # Region context card
        r_stats = _REGION_STATS.get(p.get("region",""), None)
        if r_stats:
            st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:12px;background:#fff;">
  <div style="font-size:15px;font-weight:700;color:#10131C;margin-bottom:16px;">Region Context — {p.get('region','')}</div>
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#10131C;">{r_stats['total']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Total</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#3F5208;">{r_stats['live']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Live</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#2F3FC4;">{r_stats['strategic']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Strategic</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#464F6E;">{r_stats['tier1']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Tier 1</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#3F5208;">{r_stats['revshare']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Rev Share</div></div>
  </div>
</div>""", unsafe_allow_html=True)

        # Manager stats card
        m_stats = _MANAGER_STATS.get(p.get("manager",""), None)
        if m_stats:
            st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:12px;background:#fff;">
  <div style="font-size:15px;font-weight:700;color:#10131C;margin-bottom:4px;">Account Manager — {p.get('manager','')}</div>
  <div style="font-size:12px;color:#858CA6;margin-bottom:16px;">{m_stats['regions']}</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#2F3FC4;">{m_stats['strategic']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Strategic</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#464F6E;">{m_stats['tier1']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Tier 1</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#10131C;">{m_stats['tier2']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Tier 2</div></div>
    <div style="text-align:center;padding:12px;border:1px solid #F1F3FB;border-radius:8px;"><div style="font-size:20px;font-weight:700;color:#676E8A;">{m_stats['tier3']}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">Tier 3</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Contacts ──────────────────────────────────────────────────────────────
    elif active_tab == "Contacts":
        partner_contacts = [c for c in CONTACTS if p["name"].split("/")[0].split("(")[0].strip().lower() in c["company"].lower()] or CONTACTS[:2]
        rows_html = ""
        for c in partner_contacts:
            rows_html += f"""<tr style="border-bottom:1px solid #F1F3FB;">
  <td style="padding:14px 16px;font-size:13px;font-weight:600;color:#10131C;">{c['name']}</td>
  <td style="padding:14px 16px;font-size:13px;color:#676E8A;">{c['role']}</td>
  <td style="padding:14px 16px;font-size:13px;color:#676E8A;">{c.get('company','')}</td>
  <td style="padding:14px 16px;font-size:13px;color:#676E8A;">{c['last']}</td>
  <td style="padding:14px 16px;font-size:13px;color:#676E8A;">{c['rel']}</td>
</tr>"""
        st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;overflow:hidden;margin-top:16px;background:#fff;">
  <div style="padding:20px 20px 12px;font-size:16px;font-weight:700;color:#10131C;">Partner Contacts</div>
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr><th style="padding:10px 16px;font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">Name</th><th style="padding:10px 16px;font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">Role</th><th style="padding:10px 16px;font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">Company</th><th style="padding:10px 16px;font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">Last Contact</th><th style="padding:10px 16px;font-size:11px;font-weight:600;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">Relationship</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

    # ── Contracts ─────────────────────────────────────────────────────────────
    elif active_tab == "Contracts":
        has_contract = p.get("revshare") or p["status"] == "Live"
        if has_contract:
            rev_status = "ACTIVE" if p.get("revshare_active") else "SIGNED"
            rev_bg = "#F0F5DC" if p.get("revshare_active") else "#DFE3F2"
            rev_color = "#3F5208" if p.get("revshare_active") else "#464F6E"
            st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:20px;">Contracts</div>
  <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="font-size:14px;font-weight:700;color:#10131C;">Revenue Share Agreement</div>
      <span style="background:{rev_bg};color:{rev_color};font-size:11px;font-weight:600;padding:3px 12px;border-radius:20px;">{rev_status}</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
      <div><div style="font-size:11px;color:#858CA6;">NDA</div><div style="font-size:13px;font-weight:600;color:#10131C;">{'Signed' if p.get('nda') else 'Pending'}</div></div>
      <div><div style="font-size:11px;color:#858CA6;">Rev Share Active</div><div style="font-size:13px;font-weight:600;color:#10131C;">{'Yes' if p.get('revshare_active') else 'No'}</div></div>
      <div><div style="font-size:11px;color:#858CA6;">Management Type</div><div style="font-size:13px;font-weight:600;color:#10131C;">{p.get('mgmt_type','-')}</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="border:1px solid #E2E6F4;border-radius:10px;padding:48px;margin-top:16px;background:#fff;text-align:center;"><div style="font-size:14px;color:#858CA6;">No contracts on file</div><div style="font-size:12px;color:#D2D7EA;margin-top:4px;">Contracts will appear here once the partnership is formalized.</div></div>', unsafe_allow_html=True)

    # ── SLA ───────────────────────────────────────────────────────────────────
    elif active_tab == "SLA":
        if p["status"] == "Live":
            st.markdown("""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:20px;">Service Level Agreements</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;">
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Uptime SLA</div><div style="font-size:22px;font-weight:700;color:#3F5208;">99.95%</div><div style="font-size:11px;color:#858CA6;margin-top:6px;">Target: 99.9%</div></div>
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Response Time</div><div style="font-size:22px;font-weight:700;color:#10131C;">240ms</div><div style="font-size:11px;color:#858CA6;margin-top:6px;">Target: &lt;500ms</div></div>
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Support Response</div><div style="font-size:22px;font-weight:700;color:#10131C;">2h</div><div style="font-size:11px;color:#858CA6;margin-top:6px;">Target: &lt;4h (P1)</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="border:1px solid #E2E6F4;border-radius:10px;padding:48px;margin-top:16px;background:#fff;text-align:center;"><div style="font-size:14px;color:#858CA6;">No SLA defined yet</div><div style="font-size:12px;color:#D2D7EA;margin-top:4px;">SLAs will be configured once the integration goes live.</div></div>', unsafe_allow_html=True)

    # ── Revenue ───────────────────────────────────────────────────────────────
    elif active_tab == "Revenue":
        # Match partner name to rev share data (fuzzy)
        rev_match = None
        pname_lower = p["name"].lower()
        for rk, rv in _REVSHARE_BY_PARTNER.items():
            if rk.lower() in pname_lower or pname_lower.split("/")[0].split("(")[0].strip() in rk.lower() or rk.lower().split("/")[0] in pname_lower:
                rev_match = (rk, rv)
                break
        region = p.get("region", "")
        region_pct = _REVSHARE_BY_REGION.get(region, 0)
        region_stats = _REGION_STATS.get(region, {})

        if rev_match or p.get("revshare_active"):
            rev_name, rev_val = rev_match if rev_match else (p["name"], 0)
            rev_display = f"${rev_val:,.0f}" if rev_val else "Active"
            arr_est = f"${rev_val * 12:,.0f}" if rev_val else "-"
            st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:20px;">Revenue Summary</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px;">
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Feb 2026 Rev Share</div><div style="font-size:22px;font-weight:700;color:#3F5208;">{rev_display}</div></div>
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Est. ARR</div><div style="font-size:22px;font-weight:700;color:#10131C;">{arr_est}</div></div>
    <div style="border:1px solid #E2E6F4;border-radius:8px;padding:18px;"><div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Region Rev Share</div><div style="font-size:22px;font-weight:700;color:#10131C;">{region_stats.get('revshare','-')}</div></div>
  </div>
  <div style="font-size:13px;font-weight:600;color:#10131C;margin-bottom:10px;">Portfolio Revenue Context</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;">
    <div style="padding:10px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;color:#858CA6;">Total Feb 2026</div><div style="font-size:14px;font-weight:600;color:#10131C;">$123K</div></div>
    <div style="padding:10px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;color:#858CA6;">Portfolio ARR</div><div style="font-size:14px;font-weight:600;color:#10131C;">$1.48M</div></div>
    <div style="padding:10px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;color:#858CA6;">2025 Total</div><div style="font-size:14px;font-weight:600;color:#10131C;">$1.78M</div></div>
    <div style="padding:10px 0;border-bottom:1px solid #F1F3FB;"><div style="font-size:11px;color:#858CA6;">Peak Month</div><div style="font-size:14px;font-weight:600;color:#10131C;">$245K (Oct 25)</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="border:1px solid #E2E6F4;border-radius:10px;padding:48px;margin-top:16px;background:#fff;text-align:center;"><div style="font-size:14px;color:#858CA6;">No revenue data yet</div><div style="font-size:12px;color:#D2D7EA;margin-top:4px;">Revenue data will populate once rev share is active.</div></div>', unsafe_allow_html=True)

    # ── Questionnaires ────────────────────────────────────────────────────────
    elif active_tab == "Questionnaires":
        kyp_done = bool(p.get("integration_ready"))
        st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:20px;">Questionnaires</div>
  <div style="border:1px solid #E2E6F4;border-radius:8px;padding:16px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:14px;font-weight:600;color:#10131C;">Know Your Partner (KYP)</div><div style="font-size:12px;color:#858CA6;margin-top:2px;">Due diligence, compliance, and operational assessment</div></div><span style="background:{'#F0F5DC' if kyp_done else '#FAF0D0'};color:{'#3F5208' if kyp_done else '#6E3C00'};font-size:11px;font-weight:600;padding:3px 12px;border-radius:20px;">{'COMPLETED' if kyp_done else 'PENDING'}</span></div></div>
  <div style="border:1px solid #E2E6F4;border-radius:8px;padding:16px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:14px;font-weight:600;color:#10131C;">Technical Integration Assessment</div><div style="font-size:12px;color:#858CA6;margin-top:2px;">API capabilities, payment methods, certification</div></div><span style="background:{'#F0F5DC' if p.get('integration_ready') else '#F7F8FD'};color:{'#3F5208' if p.get('integration_ready') else '#676E8A'};font-size:11px;font-weight:600;padding:3px 12px;border-radius:20px;">{'COMPLETED' if p.get('integration_ready') else 'NOT STARTED'}</span></div></div>
  <div style="border:1px solid #E2E6F4;border-radius:8px;padding:16px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:14px;font-weight:600;color:#10131C;">Commercial Terms Review</div><div style="font-size:12px;color:#858CA6;margin-top:2px;">Pricing, SLAs, revenue share, exclusivity</div></div><span style="background:{'#F0F5DC' if p.get('revshare') else '#F7F8FD'};color:{'#3F5208' if p.get('revshare') else '#676E8A'};font-size:11px;font-weight:600;padding:3px 12px;border-radius:20px;">{'COMPLETED' if p.get('revshare') else 'NOT STARTED'}</span></div></div>
</div>""", unsafe_allow_html=True)

    # ── Audit Log ─────────────────────────────────────────────────────────────
    elif active_tab == "Audit Log":
        manager = p.get("manager", "Team")
        st.markdown(f"""
<div style="border:1px solid #E2E6F4;border-radius:10px;padding:24px;margin-top:16px;background:#fff;">
  <div style="font-size:16px;font-weight:700;color:#10131C;margin-bottom:24px;">Audit Log</div>
  <div style="border-left:2px solid #E2E6F4;margin-left:8px;padding-left:24px;">
    <div style="position:relative;padding-bottom:24px;"><div style="position:absolute;left:-31px;top:2px;width:12px;height:12px;border-radius:50%;background:#3E4FE0;border:2px solid #fff;"></div><div style="font-size:13px;font-weight:600;color:#10131C;">Status updated to {p['status']}</div><div style="font-size:12px;color:#858CA6;">{manager} &middot; March 2026</div></div>
    <div style="position:relative;padding-bottom:24px;"><div style="position:absolute;left:-31px;top:2px;width:12px;height:12px;border-radius:50%;background:#E2E6F4;border:2px solid #fff;"></div><div style="font-size:13px;font-weight:600;color:#10131C;">{'NDA signed and uploaded' if p.get('nda') else 'NDA requested'}</div><div style="font-size:12px;color:#858CA6;">{manager} &middot; February 2026</div></div>
    <div style="position:relative;padding-bottom:24px;"><div style="position:absolute;left:-31px;top:2px;width:12px;height:12px;border-radius:50%;background:#E2E6F4;border:2px solid #fff;"></div><div style="font-size:13px;font-weight:600;color:#10131C;">Partner account created</div><div style="font-size:12px;color:#858CA6;">{manager} &middot; January 2026</div></div>
  </div>
</div>""", unsafe_allow_html=True)


def _build_partners_df():
    """Build a DataFrame from PARTNERS_DATA for export."""
    rows = []
    for p in PARTNERS_DATA:
        manager = p.get("manager", "—")
        if manager == "nan": manager = "—"
        country = p.get("country", "")
        if country == "nan": country = "—"
        rows.append({
            "Partner Name": p["name"],
            "Category": p.get("cat", ""),
            "Region": p.get("region", "—"),
            "Country": country,
            "Status": p["status"],
        })
    return pd.DataFrame(rows)


def _export_excel(df):
    import io
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as XlImage
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "Partner Portfolio"
    ws.sheet_view.showGridLines = False
    nc = len(df.columns)
    last_col = get_column_letter(nc)
    thin_border = Side(style="hair", color="E4DEF5")
    # Logo area — merged
    ws.merge_cells(f"A1:{last_col}4")
    ws.row_dimensions[1].height = 60
    logo_path = _os.path.join(_BASE, "Yuno logo.png")
    if _os.path.exists(logo_path):
        img = XlImage(logo_path)
        img.width = 110
        img.height = 110
        ws.add_image(img, "A1")
    # Title — merged
    ws.merge_cells(f"A5:{last_col}5")
    ws["A5"] = "Yuno - Partner Portfolio"
    ws["A5"].font = Font(name="Arial", size=18, bold=True, color="14141A")
    ws["A5"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[5].height = 30
    # Date — merged
    ws.merge_cells(f"A6:{last_col}6")
    ws["A6"] = f"Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}"
    ws["A6"].font = Font(name="Arial", size=10, color="8A8A95")
    ws["A6"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[6].height = 18
    # Metrics — merged
    ws.merge_cells(f"A7:{last_col}7")
    total = len(df)
    by_type = df["Category"].value_counts().to_dict() if "Category" in df.columns else {}
    type_str = "   |   ".join(f"{k}: {v}" for k, v in by_type.items())
    ws["A7"] = f"Total Partners: {total}     {type_str}"
    ws["A7"].font = Font(name="Arial", size=9, color="6E6E78")
    ws["A7"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[7].height = 18
    # Spacer
    ws.row_dimensions[8].height = 6
    # Header row
    hr = 9
    header_fill = PatternFill(start_color="3E4FE0", end_color="3E4FE0", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    header_border = Border(top=Side(style="thin", color="3E4FE0"), bottom=Side(style="thin", color="3E4FE0"),
                           left=Side(style="thin", color="3E4FE0"), right=Side(style="thin", color="3E4FE0"))
    for c_idx, col in enumerate(df.columns, 1):
        cell = ws.cell(row=hr, column=c_idx, value=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = header_border
    ws.row_dimensions[hr].height = 26
    # Data rows
    alt_fill = PatternFill(start_color="FAF8FE", end_color="FAF8FE", fill_type="solid")
    data_font = Font(name="Arial", size=9, color="14141A")
    data_border = Border(bottom=thin_border, left=thin_border, right=thin_border)
    for r_idx, row in enumerate(df.itertuples(index=False)):
        rn = hr + 1 + r_idx
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=rn, column=c_idx, value=val)
            cell.font = data_font
            cell.alignment = Alignment(vertical="center")
            cell.border = data_border
            if r_idx % 2 == 1:
                cell.fill = alt_fill
        ws.row_dimensions[rn].height = 22
    # Footer — merged
    fr = hr + 1 + len(df) + 1
    ws.merge_cells(f"A{fr}:{last_col}{fr}")
    ws[f"A{fr}"] = "Yuno x Mastercard Confidential"
    ws[f"A{fr}"].font = Font(name="Arial", size=10, bold=True, italic=True, color="3E4FE0")
    ws[f"A{fr}"].alignment = Alignment(horizontal="center", vertical="center")
    ws[f"A{fr}"].fill = PatternFill(start_color="F2E9FF", end_color="F2E9FF", fill_type="solid")
    ws[f"A{fr}"].border = Border(top=Side(style="thin", color="3E4FE0"), bottom=Side(style="thin", color="3E4FE0"))
    ws.row_dimensions[fr].height = 28
    # Column widths
    for c_idx, col in enumerate(df.columns, 1):
        max_len = max(len(str(col)), df[col].astype(str).str.len().max())
        ws.column_dimensions[get_column_letter(c_idx)].width = 35 if c_idx == 1 else min(max_len + 5, 28)
    # Auto-filter
    ws.auto_filter.ref = f"A{hr}:{last_col}{hr + len(df)}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _export_pdf(df):
    from fpdf import FPDF
    pdf = FPDF(orientation="L", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(255, 255, 255)
    # Yuno logo
    logo_path = _os.path.join(_BASE, "Yuno logo.png")
    if _os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=35, h=35)
    # Title next to logo
    pdf.set_xy(50, 14)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(62, 79, 224)
    pdf.cell(0, 10, "Yuno", ln=False)
    pdf.set_xy(50, 24)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(28, 20, 51)
    pdf.cell(0, 8, "Partner Portfolio Export", ln=True)
    pdf.set_xy(50, 33)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(8)
    # Table
    cols = list(df.columns)
    n_cols = len(cols)
    avail_w = 277
    col_w = avail_w / n_cols
    col_widths = [col_w] * n_cols
    # Header
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(62, 79, 224)
    pdf.set_text_color(255, 255, 255)
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 7, col, border=0, fill=True)
    pdf.ln()
    # Rows
    pdf.set_font("Helvetica", "", 7)
    for r_idx, (_, row) in enumerate(df.iterrows()):
        if r_idx % 2 == 1:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(28, 20, 51)
        for i, col in enumerate(cols):
            val = str(row[col]) if pd.notna(row[col]) else ""
            val = val.replace("\u2014", "-").replace("\u2013", "-").replace("\u2018","'").replace("\u2019","'").replace("\u201c",'"').replace("\u201d",'"')
            pdf.cell(col_widths[i], 6, val[:35], border=0, fill=True)
        pdf.ln()
    # Footer line
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, "Yuno x Mastercard Confidential", align="C")
    return bytes(pdf.output())


def _export_pptx(df):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    import io
    # Use Yuno template if available
    tpl_path = _os.path.join(_BASE, "data", "template.pptx")
    if _os.path.exists(tpl_path):
        prs = Presentation(tpl_path)
        # Remove all existing slides (keep template layouts/master)
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]
    else:
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    # Find title layout (first with TITLE placeholder) or fallback to first
    title_layout = prs.slide_layouts[0]
    content_layout = prs.slide_layouts[0]
    for sl in prs.slide_layouts:
        if "title" in sl.name.lower():
            title_layout = sl
            break
    for sl in prs.slide_layouts:
        if "content" in sl.name.lower():
            content_layout = sl
            break
    # Brand colors from template theme
    brand_blue = RGBColor(0x3E, 0x4F, 0xE0)
    dark = RGBColor(0x28, 0x2A, 0x30)
    white = RGBColor(0xFF, 0xFF, 0xFF)
    gray = RGBColor(0x6B, 0x72, 0x80)
    # Title slide
    slide = prs.slides.add_slide(title_layout)
    for ph in slide.placeholders:
        if ph.placeholder_format.type is not None:
            if ph.placeholder_format.idx == 0:
                ph.text = "Partner Portfolio"
                for p in ph.text_frame.paragraphs:
                    p.font.size = Pt(36)
                    p.font.bold = True
                    p.font.color.rgb = dark
                    p.font.name = "Arial"
            elif ph.placeholder_format.idx == 1:
                ph.text = f"Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}"
                for p in ph.text_frame.paragraphs:
                    p.font.size = Pt(16)
                    p.font.color.rgb = gray
                    p.font.name = "Arial"
    # Data slides
    cols = list(df.columns)
    chunk_size = 22
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start + chunk_size]
        slide_n = prs.slides.add_slide(content_layout)
        # Clear placeholders
        for ph in slide_n.placeholders:
            ph.text = ""
        # Add table
        n_rows = len(chunk) + 1
        tbl_shape = slide_n.shapes.add_table(n_rows, len(cols), Inches(0.4), Inches(0.9), Inches(12.5), Inches(6.0))
        tbl = tbl_shape.table
        # Header
        for i, col in enumerate(cols):
            cell = tbl.cell(0, i)
            cell.text = col
            cell.fill.solid()
            cell.fill.fore_color.rgb = brand_blue
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(9)
                p.font.bold = True
                p.font.color.rgb = white
                p.font.name = "Arial"
        # Rows
        for r_idx in range(len(chunk)):
            for c_idx, col in enumerate(cols):
                cell = tbl.cell(r_idx + 1, c_idx)
                val = str(chunk.iloc[r_idx][col]) if pd.notna(chunk.iloc[r_idx][col]) else ""
                cell.text = val
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xF8, 0xFA, 0xFC) if r_idx % 2 == 1 else white
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(8)
                    p.font.color.rgb = dark
                    p.font.name = "Arial"
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


# ══ Merchant category codes ════════════════════════════════════════════════════
# A merchant name is the most natural thing to type and the least useful thing to
# match on directly. MCC is the bridge: it turns "Rappi" into a category, and the
# category into the acceptance and capability requirements a connector must meet.
_MCC_TABLE = {
    "4121": ("Taxicabs & Rideshare",        ["ride", "rideshare", "taxi", "mobility", "cab"],           {"payouts": True}),
    "4131": ("Bus Lines",                   ["bus", "coach"],                                            {}),
    "4214": ("Freight & Delivery",          ["delivery", "courier", "logistics", "freight", "shipping"], {"payouts": True}),
    "4511": ("Airlines",                    ["airline", "flight", "aviation", "airways"],                {"airlines": True, "high_risk": True}),
    "4722": ("Travel Agencies",             ["travel", "ota", "booking", "tourism", "trip"],             {"high_risk": True}),
    "4816": ("Computer Network Services",   ["saas", "hosting", "cloud", "network", "platform"],         {"recurring": True}),
    "4899": ("Streaming & Cable",           ["streaming", "cable", "satellite", "tv"],                   {"recurring": True}),
    "5192": ("Books & Periodicals",         ["book", "publisher", "magazine", "news"],                   {}),
    "5411": ("Grocery Stores",              ["grocery", "supermarket", "market", "food retail"],         {}),
    "5462": ("Bakeries",                    ["bakery", "patisserie"],                                    {}),
    "5499": ("Convenience & Specialty Food",["convenience", "specialty food"],                           {}),
    "5541": ("Service Stations",            ["fuel", "gas station", "petrol"],                           {}),
    "5651": ("Family Clothing",             ["clothing", "apparel", "fashion", "wear"],                  {}),
    "5691": ("Men's & Women's Clothing",    ["boutique", "menswear", "womenswear"],                      {}),
    "5722": ("Household Appliances",        ["appliance", "white goods"],                                {"installments": True}),
    "5732": ("Electronics",                 ["electronics", "gadget", "computer", "phone"],              {"installments": True}),
    "5812": ("Restaurants",                 ["restaurant", "dining", "eatery"],                          {}),
    "5814": ("Fast Food",                   ["fast food", "quick service", "qsr", "burger", "pizza"],    {}),
    "5815": ("Digital Goods — Media",       ["music", "video", "movie", "media", "audio"],               {"recurring": True}),
    "5816": ("Digital Goods — Games",       ["game", "gaming", "esport", "console"],                     {"gaming": True}),
    "5817": ("Digital Goods — Applications",["app", "application", "mobile app", "software"],            {"recurring": True}),
    "5818": ("Digital Goods — Large Merchant",["marketplace digital", "digital large"],                  {"recurring": True}),
    "5912": ("Drug Stores & Pharmacies",    ["pharmacy", "drugstore", "chemist"],                        {}),
    "5941": ("Sporting Goods",              ["sport", "fitness gear", "outdoor"],                        {}),
    "5964": ("Direct Marketing — Catalog",  ["catalog", "direct marketing"],                             {"high_risk": True}),
    "5967": ("Direct Marketing — Inbound",  ["inbound teleservices", "telemarketing"],                   {"high_risk": True, "adult": True}),
    "5969": ("Direct Marketing — Other",    ["direct sales"],                                            {"high_risk": True}),
    "5999": ("Miscellaneous Retail",        ["retail", "shop", "store", "ecommerce", "e-commerce"],      {}),
    "6012": ("Financial Institutions",      ["bank", "banking", "financial institution", "fintech"],     {"payouts": True}),
    "6051": ("Quasi-Cash & Crypto",         ["crypto", "bitcoin", "exchange", "wallet", "stablecoin"],   {"crypto": True, "high_risk": True}),
    "6211": ("Securities & Brokers",        ["broker", "forex", "trading", "securities", "invest"],      {"forex": True, "high_risk": True}),
    "7011": ("Lodging & Hotels",            ["hotel", "lodging", "hospitality", "resort", "stay"],       {"high_risk": True}),
    "7273": ("Dating Services",             ["dating", "match"],                                         {"adult": True, "high_risk": True}),
    "7297": ("Massage Parlours",            ["massage"],                                                 {"adult": True, "high_risk": True}),
    "7372": ("Computer Programming & SaaS", ["software", "b2b saas", "subscription software"],           {"recurring": True}),
    "7995": ("Betting & Gambling",          ["betting", "gambling", "casino", "sportsbook", "lottery"],  {"gambling": True, "high_risk": True}),
    "7997": ("Membership Clubs",            ["membership", "club", "gym"],                               {"recurring": True}),
    "7999": ("Recreation Services",         ["recreation", "leisure", "entertainment"],                  {}),
    "8011": ("Doctors & Physicians",        ["clinic", "doctor", "medical", "health"],                   {}),
    "8299": ("Educational Services",        ["education", "school", "course", "learning", "edtech"],     {"recurring": True}),
    "8398": ("Charitable Organisations",    ["charity", "donation", "ngo", "nonprofit"],                 {"recurring": True}),
}

# Merchants Yuno already tracks map straight to their MCC; anything else falls
# through to keyword matching on the sector.
_MERCHANT_MCC = {
    "uber": "4121", "cabify": "4121", "didi": "4121", "lyft": "4121", "beat": "4121",
    "rappi": "4214", "ifood": "5814", "pedidosya": "5814", "doordash": "5814",
    "glovo": "4214", "deliveroo": "4214",
    "netflix": "4899", "spotify": "5815", "disney": "4899", "hbo": "4899",
    "globoplay": "4899", "deezer": "5815", "youtube": "4899",
    "mercadolibre": "5999", "mercado libre": "5999", "amazon": "5999",
    "falabella": "5651", "linio": "5999", "magalu": "5999", "americanas": "5999",
    "despegar": "4722", "booking": "7011", "latam": "4511", "avianca": "4511",
    "gol": "4511", "azul": "4511", "copa": "4511", "airbnb": "7011",
    "binance": "6051", "coinbase": "6051", "bitso": "6051", "ripio": "6051",
    "betano": "7995", "bet365": "7995", "rushbet": "7995", "codere": "7995",
    "nubank": "6012", "ualá": "6012", "uala": "6012", "revolut": "6012",
    "duolingo": "8299", "platzi": "8299", "crehana": "8299",
}


def resolve_mcc(text):
    """Merchant or sector text → (mcc, label, implications). Deterministic."""
    t = " " + str(text).strip().lower() + " "
    for name, code in sorted(_MERCHANT_MCC.items(), key=lambda kv: -len(kv[0])):
        if f" {name} " in t or t.strip() == name:
            label, _, impl = _MCC_TABLE[code]
            return code, label, impl, f"'{name.title()}' is a known merchant"
    best = None
    for code, (label, kws, impl) in _MCC_TABLE.items():
        for kw in kws:
            if f" {kw} " in t or f" {kw}s " in t:
                if best is None or len(kw) > best[4]:
                    best = (code, label, impl, f"matched on '{kw}'", len(kw))
    if best:
        return best[0], best[1], best[2], best[3]
    return None, None, {}, ""

# ══ Natural-language connector search ══════════════════════════════════════════
# The Type dropdown asked one closed question. This box takes whatever the user
# actually has in their head — a merchant, a market, a card brand, a partner — and
# resolves it against the real vocabularies in the data. The parse is
# deterministic so it works in a meeting with no network; Claude is optional
# enrichment for phrasing the tokeniser missed, and never produces a number.

_REGION_WORDS = {
    "latam": ["SOUTH_AMERICA"], "latin america": ["SOUTH_AMERICA"],
    "south america": ["SOUTH_AMERICA"], "north america": ["NORTH_AMERICA"],
    "apac": ["ASIA", "OCEANIA"], "asia": ["ASIA"], "oceania": ["OCEANIA"],
    "emea": ["EUROPE", "AFRICA"], "europe": ["EUROPE"], "eu": ["EUROPE"],
    "africa": ["AFRICA"], "global": ["GLOBAL"], "worldwide": ["GLOBAL"],
    "mena": ["AFRICA"], "menat": ["AFRICA"],
}
_CARD_WORDS = {
    "visa": "VISA", "mastercard": "MASTERCARD", "master card": "MASTERCARD",
    "amex": "AMEX", "american express": "AMEX", "elo": "ELO", "hipercard": "ELO",
    "diners": "DINERS", "discover": "DISCOVER", "jcb": "JCB", "rupay": "RUPAY",
    "maestro": "MAESTRO", "interac": "INTERAC", "union pay": "CHINA UNION PAY INT",
    "unionpay": "CHINA UNION PAY INT", "eftpos": "EFTPOS_AUSTRALIA", "mpu": "MPU",
}
_TYPE_WORDS = {
    "acquirer": "Acquirer", "acquiring": "Acquirer", "bank": "Acquirer",
    "psp": "PSP/Aggregator", "aggregator": "PSP/Aggregator", "gateway": "PSP/Aggregator",
    "processor": "PSP/Aggregator", "apm": "APM", "alternative payment": "APM",
    "wallet": "APM", "local method": "APM", "fraud": "Fraud Provider",
    "risk": "Fraud Provider", "baas": "BaaS", "plug-in": "Plug-In", "plugin": "Plug-In",
}
_CAP_WORDS = {
    "recurring": "recurring", "subscription": "recurring", "subscriptions": "recurring",
    "token": "tokenization", "tokenisation": "tokenization", "tokenization": "tokenization",
    "payout": "payouts", "payouts": "payouts", "disbursement": "payouts",
    "installment": "installments", "installments": "installments", "cuotas": "installments",
    "parcelamento": "installments", "msi": "installments",
}
_VERT_WORDS = {
    "gaming": "gaming", "games": "gaming", "gambling": "gambling", "betting": "gambling",
    "casino": "gambling", "crypto": "crypto", "bitcoin": "crypto", "stablecoin": "crypto",
    "forex": "forex", "adult": "adult", "airline": "airlines", "airlines": "airlines",
    "high risk": "high_risk", "high-risk": "high_risk",
}
_PROC_WORDS = {"local acquiring": "LOCAL", "local": "LOCAL",
               "cross border": "CROSS_BORDER", "cross-border": "CROSS_BORDER"}


@st.cache_data(show_spinner=False)
def _search_vocab():
    """Vocabularies drawn from the data, so the box can only resolve real things."""
    partners = {p["name"].lower(): p["name"] for p in PARTNERS_DATA}
    countries, iso = {}, {}
    if len(_SOT_DF) > 0:
        for code in _SOT_DF["COUNTRY_ISO"].dropna().unique():
            name = _ISO_TO_COUNTRY.get(str(code).strip().upper())
            if name:
                countries[name.lower()] = str(code).strip().upper()
                iso[str(code).strip().upper()] = name
    # a few endonyms and shorthands the ISO list will not carry
    countries.update({"brasil": "BR", "usa": "US", "us": "US", "uk": "GB",
                      "uae": "AE", "korea": "KR", "mexico": "MX", "méxico": "MX"})
    return partners, countries, iso


def resolve_search(text):
    """Free text → a structured intent. No network, no guessing at numbers."""
    partners, countries, iso_name = _search_vocab()
    q = " " + _re.sub(r"[,;/]", " ", str(text or "").lower()).strip() + " "
    hit = {"partners": [], "countries": [], "regions": [], "cards": [], "types": [],
           "caps": [], "verticals": [], "processing": None, "merchant": None,
           "mcc": None, "mcc_label": None, "mcc_why": "", "unmatched": []}

    def take(phrase):
        nonlocal q
        q = q.replace(f" {phrase} ", " ")

    # longest phrases first so "north america" beats "america"
    for name in sorted(partners, key=len, reverse=True):
        if len(name) > 2 and f" {name} " in q:
            hit["partners"].append(partners[name]); take(name)
    for word in sorted(_REGION_WORDS, key=len, reverse=True):
        for form in (word, word + "s"):
            if f" {form} " in q:
                hit["regions"] += _REGION_WORDS[word]; take(form); break
    for name in sorted(countries, key=len, reverse=True):
        if f" {name} " in q:
            hit["countries"].append(countries[name]); take(name)
    for group, dest in ((_CARD_WORDS, "cards"), (_TYPE_WORDS, "types"),
                        (_CAP_WORDS, "caps"), (_VERT_WORDS, "verticals")):
        for word in sorted(group, key=len, reverse=True):
            # people type "acquirers", not "acquirer"
            for form in (word, word + "s", word + "es"):
                if f" {form} " in q:
                    hit[dest].append(group[word]); take(form); break
    for word in sorted(_PROC_WORDS, key=len, reverse=True):
        if f" {word} " in q and not hit["processing"]:
            hit["processing"] = _PROC_WORDS[word]; take(word)

    code, label, impl, why = resolve_mcc(text)
    if code:
        hit["mcc"], hit["mcc_label"], hit["mcc_why"] = code, label, why
        for k, v in impl.items():
            if k in ("gaming", "gambling", "crypto", "forex", "adult", "airlines", "high_risk"):
                hit["verticals"].append(k)
            elif v:
                hit["caps"].append(k)
        m = _re.search(r"\b([a-z][a-z0-9.&'-]{2,})\b", why)
        if "known merchant" in why:
            hit["merchant"] = why.split("'")[1]

    for d in ("regions", "countries", "cards", "types", "caps", "verticals", "partners"):
        hit[d] = sorted(set(hit[d]))
    consumed = set(_STOPWORDS)
    if hit["merchant"]:
        consumed |= set(str(hit["merchant"]).lower().split())
    if hit["mcc_label"]:
        consumed |= {w.strip("&,").lower() for w in hit["mcc_label"].split()}
    hit["unmatched"] = [w for w in q.split() if len(w) > 2 and w not in consumed][:6]
    return hit


_STOPWORDS = {"the", "and", "for", "with", "that", "who", "what", "which", "can",
              "need", "want", "looking", "find", "show", "give", "list", "best",
              "support", "supports", "accept", "accepts", "does", "are", "any",
              "our", "their", "them", "has", "have", "into", "from", "top"}


def describe_intent(hit):
    """The rephrase: what the portal understood, in plain words."""
    bits = []
    if hit["types"]:     bits.append(" or ".join(_TYPE_SHORT.get(t, t) for t in hit["types"]) + "s")
    else:                bits.append("connectors")
    if hit["partners"]:  bits.append("named " + ", ".join(hit["partners"][:3]))
    if hit["countries"]:
        _, _, iso_name = _search_vocab()
        bits.append("live in " + ", ".join(iso_name.get(c, c) for c in hit["countries"][:3]))
    elif hit["regions"]: bits.append("in " + ", ".join(r.replace("_", " ").title() for r in hit["regions"]))
    if hit["cards"]:     bits.append("carrying " + ", ".join(c.title() for c in hit["cards"]))
    if hit["verticals"]: bits.append("that accept " + ", ".join(v.replace("_", " ") for v in hit["verticals"]))
    if hit["caps"]:      bits.append("with " + ", ".join(hit["caps"]))
    if hit["processing"]: bits.append(hit["processing"].replace("_", "-").lower() + " processing")
    return " ".join(bits).strip() or "every connector"

def _conn_matches(c, hit):
    """Score one connector against the intent. Reasons are collected as we go, so
    the shortlist can always say why a row is on it."""
    caps = c.get("caps", {}) or {}
    reasons, hard_fail = [], False

    if hit["partners"]:
        if c["name"] in hit["partners"]: reasons.append(("named", 40, f"asked for by name"))
        else: hard_fail = True
    if hit["countries"]:
        live = set(caps.get("countries", []))
        got = [x for x in hit["countries"] if x in live]
        if got: reasons.append(("country", 30, f"live in {', '.join(got)}"))
        else: hard_fail = True
    if hit["regions"]:
        live = set(caps.get("regions", []))
        got = [x for x in hit["regions"] if x in live]
        if got: reasons.append(("region", 18, f"covers {', '.join(r.replace('_',' ').title() for r in got)}"))
        elif not hit["countries"]: hard_fail = True
    if hit["types"]:
        if c.get("type") in hit["types"]: reasons.append(("type", 22, f"is a {_TYPE_SHORT.get(c['type'], c['type'])}"))
        else: hard_fail = True
    for v in hit["verticals"]:
        if caps.get(v if v != "high_risk" else "gambling"):
            reasons.append((v, 16, f"accepts {v.replace('_',' ')}"))
        elif v in ("gambling", "gaming", "crypto", "airlines"):
            hard_fail = True
    for cap in hit["caps"]:
        if caps.get(cap): reasons.append((cap, 10, f"supports {cap}"))
    if hit["cards"]:
        pms = " ".join(c.get("paymentMethods", []) or []).upper()
        got = [b for b in hit["cards"] if b.split()[0] in pms]
        if got: reasons.append(("card", 12, f"carries {', '.join(b.title() for b in got)}"))
    if c.get("status") == "Live": reasons.append(("live", 14, "already live with Yuno"))

    return (0 if hard_fail else sum(r[1] for r in reasons)), reasons, hard_fail


def rank_connectors(connectors, hit, limit=8):
    out = []
    for c in connectors:
        score, reasons, failed = _conn_matches(c, hit)
        if failed or score <= 0:
            continue
        out.append({"c": c, "score": score, "reasons": reasons})
    out.sort(key=lambda r: (-r["score"], r["c"]["name"]))
    return out[:limit], len(out)


# ── Optional enrichment ───────────────────────────────────────────────────────
_EXTRACT_TOOL = {
    "name": "extract_search_intent",
    "description": "Return the payment-search entities present in the user's query.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "merchant_or_sector": {"type": ["string", "null"],
                "description": "Merchant brand or business sector mentioned, else null."},
            "countries": {"type": "array", "items": {"type": "string"},
                "description": "Country names mentioned, in English."},
            "card_brands": {"type": "array", "items": {"type": "string"}},
            "connector_types": {"type": "array", "items": {"type": "string"},
                "description": "One or more of: acquirer, psp, apm, fraud, baas."},
            "capabilities": {"type": "array", "items": {"type": "string"},
                "description": "One or more of: recurring, tokenization, payouts, installments."},
            "verticals": {"type": "array", "items": {"type": "string"},
                "description": "One or more of: gaming, gambling, crypto, forex, adult, airlines, high_risk."},
        },
        "required": ["merchant_or_sector", "countries", "card_brands",
                     "connector_types", "capabilities", "verticals"],
    },
}


def _anthropic_client():
    try:
        key = st.secrets["anthropic"]["api_key"]
    except Exception:
        return None, None
    if not key:
        return None, None
    try:
        import anthropic
    except ImportError:
        return None, None
    try:
        model = st.secrets["anthropic"].get("model", "claude-opus-5")
    except Exception:
        model = "claude-opus-5"
    return anthropic.Anthropic(api_key=key, timeout=6.0, max_retries=0), model


@st.cache_data(show_spinner=False, ttl=900)
def enrich_intent(text):
    """One short call, entities only. Never returns a number, never a ranking.

    Cached so repeating a query in a meeting costs nothing, and wrapped so a
    missing key, a timeout, or a bad response simply leaves the deterministic
    parse untouched.
    """
    client, model = _anthropic_client()
    if client is None:
        return None, "no API key configured — deterministic parse only"
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=512,
            output_config={"effort": "low"},          # latency budget, not cost
            system=("Extract payment-connector search entities from the query. "
                    "Return only what is explicitly present. Never invent a merchant."),
            tools=[_EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_search_intent"},
            messages=[{"role": "user", "content": str(text)[:400]}],
        )
        for block in resp.content:
            if block.type == "tool_use":
                return dict(block.input), f"enriched by {model}"
        return None, "no entities returned"
    except Exception as e:
        return None, f"enrichment unavailable ({type(e).__name__}) — deterministic parse used"


def merge_enrichment(hit, extra):
    """Enrichment can only ADD entities the tokeniser missed, never overrule it."""
    if not extra:
        return hit
    _, countries, _ = _search_vocab()
    for name in extra.get("countries") or []:
        iso = countries.get(str(name).strip().lower())
        if iso and iso not in hit["countries"]:
            hit["countries"].append(iso)
    for b in extra.get("card_brands") or []:
        k = _CARD_WORDS.get(str(b).strip().lower())
        if k and k not in hit["cards"]:
            hit["cards"].append(k)
    for t in extra.get("connector_types") or []:
        k = _TYPE_WORDS.get(str(t).strip().lower())
        if k and k not in hit["types"]:
            hit["types"].append(k)
    for c in extra.get("capabilities") or []:
        k = str(c).strip().lower()
        if k in ("recurring", "tokenization", "payouts", "installments") and k not in hit["caps"]:
            hit["caps"].append(k)
    for v in extra.get("verticals") or []:
        k = str(v).strip().lower()
        if k in ("gaming", "gambling", "crypto", "forex", "adult", "airlines", "high_risk") \
                and k not in hit["verticals"]:
            hit["verticals"].append(k)
    if not hit["mcc"] and extra.get("merchant_or_sector"):
        code, label, impl, why = resolve_mcc(extra["merchant_or_sector"])
        if code:
            hit["mcc"], hit["mcc_label"] = code, label
            hit["mcc_why"] = why + " (via enrichment)"
            for k, v in impl.items():
                if k in ("gaming", "gambling", "crypto", "forex", "adult", "airlines", "high_risk"):
                    hit["verticals"].append(k)
                elif v:
                    hit["caps"].append(k)
    for d in ("countries", "cards", "types", "caps", "verticals"):
        hit[d] = sorted(set(hit[d]))
    return hit

def show_connector_search(connectors):
    """The AI box that replaced the Type dropdown. Returns the filtered set."""
    st.markdown(
        '<div style="margin:2px 0 8px;">'
        '<div style="font-size:16px;font-weight:600;color:#10131C;letter-spacing:-.02em;">'
        'Describe what you need</div>'
        '<div style="font-size:13px;color:#4A5170;margin-top:3px;line-height:1.6;">'
        'A merchant, a market, a card, a partner — type it how you\'d say it. '
        'Yuno resolves the merchant to an MCC and maps that to the connectors that can actually take it.</div></div>',
        unsafe_allow_html=True)

    with st.form("conn_search", clear_on_submit=False, border=False):
        q = st.text_input("Search", key="conn_q", label_visibility="collapsed",
                          placeholder="e.g. Rappi expanding into Colombia, needs PSE and installments")
        cc1, cc2 = st.columns([1, 5])
        go = cc1.form_submit_button("Search", use_container_width=True, type="primary")
        cc2.form_submit_button("Clear", use_container_width=False, on_click=lambda: st.session_state.update(conn_q=""))

    # One search, so the prompts that used to live in the table's own box run here.
    examples = ["Rappi into Colombia with PSE", "acquirers in Brazil that take gambling",
                "who carries Amex in Mexico", "crypto exchange needing payouts in APAC",
                "contact for Adyen", "tokenization in LATAM", "recurring payments",
                "payouts support", "live connectors in APAC", "T+1 settlement"]
    with st.container(key="conn_examples"):
        cols = st.columns(5)
        for i, e in enumerate(examples):
            if cols[i % 5].button(e, key=f"conn_ex_{i}", use_container_width=True):
                st.session_state.conn_q = e
                st.rerun()

    text = (q or "").strip()
    if not text:
        return connectors, None

    hit = resolve_search(text)
    extra, note = enrich_intent(text)
    hit = merge_enrichment(hit, extra)
    shortlist, total = rank_connectors(connectors, hit)

    # ── what we understood ───────────────────────────────────────────────────
    chips = []
    _, _, iso_name = _search_vocab()
    for label, vals, kind in [
        ("Partner", hit["partners"], "data"),
        ("Market", [iso_name.get(c, c) for c in hit["countries"]], "market"),
        ("Region", [r.replace("_", " ").title() for r in hit["regions"]], "market"),
        ("Type", [_TYPE_SHORT.get(t, t) for t in hit["types"]], "data"),
        ("Card", [c.title() for c in hit["cards"]], "data"),
        ("Vertical", [v.replace("_", " ") for v in hit["verticals"]], "assume"),
        ("Capability", hit["caps"], "data"),
    ]:
        for v in vals:
            chips.append(_chip(f"{label} · {v}", kind))
    if hit["mcc"]:
        chips.insert(0, _chip(f"MCC {hit['mcc']} · {hit['mcc_label']}", "assume"))

    st.markdown(
        f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
        f'border-left:3px solid var(--indigo);border-radius:14px;padding:17px 20px;margin-bottom:12px;">'
        f'<div style="font-size:10px;color:#676E8A;text-transform:uppercase;letter-spacing:.1em;'
        f'font-weight:600;margin-bottom:8px;">What I understood</div>'
        f'<div style="font-size:15px;color:#10131C;line-height:1.6;margin-bottom:12px;">'
        f'You\'re looking for <b>{describe_intent(hit)}</b>.</div>'
        + (f'<div style="font-size:12.5px;color:#4A5170;line-height:1.6;margin-bottom:11px;">'
           f'<b>{hit["mcc_label"]}</b> (MCC {hit["mcc"]}) — {hit["mcc_why"]}. '
           f'That category sets the acceptance and capability tests below.</div>' if hit["mcc"] else "")
        + f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{"".join(chips) or _chip("no entities resolved", "assume")}</div>'
        + (f'<div style="margin-top:11px;font-size:11px;color:#676E8A;">Not used: '
           + ", ".join(hit["unmatched"]) + '</div>' if hit["unmatched"] else "")
        + f'<div style="margin-top:11px;padding-top:9px;border-top:1px solid rgba(35,42,61,.08);'
        f'font-size:11px;color:#676E8A;">{note} · matching is deterministic over '
        f'source_of_truth.xlsx — the model only reads your sentence, never the ranking.</div></div>',
        unsafe_allow_html=True)

    # ── the shortlist ────────────────────────────────────────────────────────
    if not shortlist:
        st.markdown(
            '<div style="padding:16px 19px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
            'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
            'Nothing in the book satisfies all of that. Drop the tightest constraint — usually '
            'the vertical or the exact market — and try again.</div>', unsafe_allow_html=True)
        return connectors, hit

    st.markdown(
        f'<div style="font-size:11px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;'
        f'color:#676E8A;margin:16px 0 9px;">Recommended shortlist — {len(shortlist)} of {total} matches</div>',
        unsafe_allow_html=True)
    for i, row in enumerate(shortlist):
        c, why = row["c"], row["reasons"]
        top = " · ".join(r[2] for r in sorted(why, key=lambda r: -r[1])[:4])
        st.markdown(
            f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            f'border-left:3px solid {"var(--indigo)" if i == 0 else "rgba(62,79,224,.32)"};'
            f'border-radius:12px;padding:14px 18px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
            f'<span style="font-size:11px;color:#858CA6;font-variant-numeric:tabular-nums;width:16px;">{i+1}</span>'
            f'<span style="font-size:14.5px;font-weight:600;color:#10131C;">{c["name"]}</span>'
            f'<span style="font-size:11px;color:#676E8A;">{_TYPE_SHORT.get(c.get("type",""), c.get("type",""))} · '
            f'{c.get("region","—")} · {c.get("country","—")}</span>'
            f'<span style="margin-left:auto;font-size:10.5px;font-weight:600;padding:2px 9px;'
            f'border-radius:999px;background:{"rgba(90,122,0,.14)" if c.get("status")=="Live" else "rgba(35,42,61,.07)"};'
            f'color:{"#48610A" if c.get("status")=="Live" else "#676E8A"};">{c.get("status","—")}</span></div>'
            f'<div style="font-size:12px;color:#4A5170;margin-top:7px;line-height:1.55;">{top}</div></div>',
            unsafe_allow_html=True)

    keep = {r["c"]["name"] for r in shortlist}
    return [c for c in connectors if c["name"] in keep] or connectors, hit


# ── Partner tiering UI ─────────────────────────────────────────────────────────
# What each tier means, and — the part that actually changes behaviour — what you
# are supposed to DO about it. Thresholds come from the Framework sheet; the
# operating posture is the partnerships call layered on top.
# ══ Tiering automation — refresh, alerts, ownership ════════════════════════════
# The model re-runs whenever the page opens and a snapshot is kept once a week.
# Anything that moved tier raises an alert addressed to the partner manager who
# owns the account; where no one owns it, the alert goes to Daniela Reyes rather
# than nowhere.

_TIER_RANK = {"Strategic": 3, "Tier 1": 2, "T1": 2, "Tier 2": 1, "T2": 1,
              "Tier 3": 0, "T3": 0, "—": -1, "": -1, "nan": -1}
_TIER_NORM = {"T1": "Tier 1", "T2": "Tier 2", "T3": "Tier 3", "Strategic": "Strategic"}
_NO_OWNER = {"not assigned/ not relevant", "not assigned", "tbd", "unassigned",
             "nan", "", "—", "none", "new pm br", "new pm", "not relevant"}
# The book writes owners as "Sumit/MENA" and "Chee/APAC" — the suffix is a region,
# not a second person, so splitting on "/" invents managers who do not exist.
_REGION_TOKENS = {"mena", "apac", "latam", "emea", "turkey", "br", "brazil",
                  "menat", "eu", "europe", "na", "us", "global"}
# One person, two spellings on file. Merged so their alerts do not split in two.
_MANAGER_ALIASES = {"alessandra rospligliossi": "Alessandra Rospigliosi"}
_ESCALATION = "Daniela Reyes"

_CONSOLE = {
    "void": "#080911", "panel": "#10131C", "panel2": "#141827",
    "line": "#232A3D", "line2": "#38415C",
    "ink": "#EEF0FA", "dim": "#8991AC", "faint": "#565D78",
    "blue": "#5468F5", "blue_ink": "#8B9BFF",
    "lime": "#E0ED80", "coral": "#FF6B7D", "amber": "#FFD400",
}
_TIER_CONSOLE = {"Strategic": "#8B9BFF", "Tier 1": "#E0ED80",
                 "Tier 2": "#FFB84D", "Tier 3": "#8991AC"}


def split_managers(raw):
    """The book records owners as free text — 'Talita Gama, New PM BR'. Split it."""
    s = str(raw or "").strip()
    if not s or s.lower() in _NO_OWNER:
        return []
    parts = [p.strip(" -\t") for p in _re.split(r",|/| - ", s)]
    out = []
    for p in parts:
        k = p.lower()
        if not p or k in _NO_OWNER or k in _REGION_TOKENS or len(p) <= 2:
            continue
        p = _MANAGER_ALIASES.get(k, p)
        if p not in out:
            out.append(p)
    return out


def alert_recipient(raw):
    """Who hears about a change to this account, and why."""
    owners = split_managers(raw)
    if owners:
        return owners[0], owners, False
    return _ESCALATION, [], True


@st.cache_data(show_spinner=False)
def manager_roster(_rows_key=None):
    """Every individual named as an owner anywhere in the book."""
    rows, _, _ = run_tiering()
    names = set()
    for r in rows:
        names.update(split_managers(r["manager"]))
    return sorted(names)


def tier_alerts(rows):
    """Every account whose modelled tier differs from the tier on record."""
    out = []
    for r in rows:
        was = _TIER_NORM.get(str(r["current_tier"]).strip(), str(r["current_tier"]).strip())
        now = r["final"]
        if was == now or _TIER_RANK.get(was, -1) < 0:
            continue
        direction = "up" if _TIER_RANK.get(now, 0) > _TIER_RANK.get(was, 0) else "down"
        to, owners, escalated = alert_recipient(r["manager"])
        out.append({"row": r, "was": was, "now": now, "direction": direction,
                    "to": to, "owners": owners, "escalated": escalated})
    out.sort(key=lambda a: (a["direction"] != "up", -a["row"]["score"]))
    return out


_TIER_DEFS = {
    "Strategic": {
        "gate": "Score ≥ 75%",
        "mode": "focus",
        "one_line": "The must-have providers — the largest rails in the world, and the "
                    "partners that open merchant and banking demand Yuno cannot reach alone.",
        "what": [
            "A named must-have: a provider a global orchestrator has to carry",
            "Global reach — every market they enter is one Yuno can enter with them",
            "A FinX rail Yuno can sell through today, signed and live",
            "A structural source of merchant leads, or a brand merchants ask for by name",
        ],
        "do": [
            "Joint lead generation into their merchant and banking pipeline — the primary motion",
            "Upsell plan per account: which Yuno products, into which of their merchants",
            "Exec sponsor on both sides; QBR against a <b>pipeline</b> number",
            "Roadmap access and early integration so the partnership compounds",
        ],
        "guard": "RevShare is deliberately not scored. A must-have can pay Yuno nothing "
                 "today and still be Strategic. Every seat costs a named owner and a QBR.",
    },
    "Tier 1": {
        "gate": "Score ≥ 55%",
        "mode": "focus",
        "one_line": "The upsell and lead engine — FinX rails that are live, scaling, "
                    "and already sending merchants our way.",
        "what": [
            "A FinX rail (acquirer, PSP, APM / wallet, fraud, crypto) with a contract and an integration",
            "Global or regional reach with real Yuno volume behind it",
            "A referral motion — Crossbeam, a partner programme, or a live acquirer feeding leads",
            "Room to grow: more products to sell, more merchants to reach",
        ],
        "do": [
            "Lead generation both directions — this is where pipeline comes from",
            "Upsell campaign: Yuno products into the partner's merchant base",
            "A named partner manager and a quarterly plan",
            "Push toward Strategic on evidence: reach, leads, volume",
        ],
        "guard": "The promotion pool. Tier 1 is where the next Strategic seat is "
                 "earned, so review it every week, not annually.",
    },
    "Tier 2": {
        "gate": "Score ≥ 30%",
        "mode": "automate",
        "one_line": "Real but not yet a lead source. Automate, and let the data promote them.",
        "what": [
            "A FinX rail that is signed or in negotiation, with little volume yet",
            "Country or regional reach, no structured referral motion",
            "Live with minimal or early activity",
            "An adjacent partner (plug-in, BaaS, payouts) with a contract",
        ],
        "do": [
            "Templated onboarding and self-serve enablement — no bespoke work",
            "Automated volume alerts; a threshold crossing triggers the review",
            "Weekly re-score, no standing meeting",
            "Promote on evidence, never on who shouted loudest",
        ],
        "guard": "The trap is attention: a Tier 2 that gets Tier 1 handling starves "
                 "a Tier 1. Let the threshold decide, not the relationship.",
    },
    "Tier 3": {
        "gate": "Below 30%",
        "mode": "automate",
        "one_line": "Dormant, lost or not started. Fully automated — keep the record, not the calendar.",
        "what": [
            "Lost, stopped or non-qualified — or never past opportunity identification",
            "Not a FinX rail, or one with no contract and no integration",
            "No Yuno volume and no referral motion in either direction",
            "Niche or product partner with no route to merchants",
        ],
        "do": [
            "No named owner and no recurring meeting",
            "Keep the account record accurate so a signal can find it",
            "Let the weekly re-score promote them — automatically",
            "Revisit only when volume, a merchant request, or a market gap appears",
        ],
        "guard": "Most of the book sits here carrying almost none of the volume. That is "
                 "correct — it is coverage, not neglect. It only becomes neglect "
                 "if the record rots.",
    },
}

_TIER_COLOR = {"Strategic": "#3E4FE0", "Tier 1": "#0086A8", "Tier 2": "#C24E00", "Tier 3": "#676E8A"}


def _score_bar(score, height=8, show_ticks=True):
    """Score bar with the real cutoffs marked at 30 / 55 / 75."""
    pct = max(0.0, min(1.0, score)) * 100
    col = ("#3E4FE0" if score >= .75 else "#0086A8" if score >= .55
           else "#C24E00" if score >= .30 else "#676E8A")
    ticks = "".join(
        f'<div style="position:absolute;left:{t}%;top:-3px;bottom:-3px;width:1px;'
        f'background:rgba(16,19,28,.28);"></div>' for t in (30, 55, 75)) if show_ticks else ""
    return (f'<div style="position:relative;height:{height}px;background:var(--sunk);'
            f'border-radius:999px;overflow:visible;">'
            f'<div style="width:{pct:.1f}%;height:100%;background:{col};border-radius:999px;"></div>'
            f'{ticks}</div>')


def _gate_text(r):
    """Why this partner landed where it did — in the model's own terms."""
    s = r["score"] * 100
    seat = ""
    if r.get("manual"):
        who = "the Head of Partnerships" if r.get("placed_by") in ("", "seed") else r["placed_by"]
        when = f' on {r["placed_when"]}' if r.get("placed_when") else ""
        return (f'<span style="color:#2F3FC4;font-weight:600;">Manual placement</span> — '
                f'moved to {r["manual"]} by {who}{when}; the model scores it {s:.0f}% '
                f'({r["computed"]}). The placement wins, the score stays visible.')
    if r["override"]:
        return (f'<span style="color:#2F3FC4;font-weight:600;">Named must-have</span> — '
                f'scored {s:.0f}%, below the 75% Strategic gate. Lifted because a signed or live '
                f'must-have provider is Strategic by definition, not by the model.{seat}')
    if r["final"] == "Strategic":
        return f'Cleared the 75% Strategic gate on merit at {s:.0f}%.{seat}'
    if r["final"] == "Tier 1":
        return f'{s:.0f}% — clears Tier 1 (55%), short of Strategic (75%).'
    if r["final"] == "Tier 2":
        return f'{s:.0f}% — clears Tier 2 (30%), short of Tier 1 (55%).'
    return f'{s:.0f}% — below the Tier 2 gate (30%).'


def _partner_volume(rows):
    """Regional rows share their partner's traffic — count it once."""
    return sum({r["key"]: r["approved"] for r in rows}.values())


def _tier_stats(rows, split):
    total_v = _partner_volume(rows) or 1
    out = {}
    for t, g in split.items():
        v = _partner_volume(g)
        out[t] = {"n": len(g), "share": len(g) / len(rows) * 100,
                  "vol": v, "vol_share": v / total_v * 100,
                  "with_vol": sum(1 for r in g if r["approved"] > 0),
                  "overrides": sum(1 for r in g if r["override"])}
    return out, total_v


def _fmt_txn(v):
    if v >= 1e9: return f"{v/1e9:.1f}B"
    if v >= 1e6: return f"{v/1e6:.0f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:.0f}"


def _c(k):
    return _CONSOLE[k]


def _console_panel(inner, pad="20px 22px", extra=""):
    return (f'<div style="background:{_c("panel")};border:1px solid {_c("line")};'
            f'border-radius:14px;padding:{pad};{extra}">{inner}</div>')


# ══ Weekly review — snapshots, deltas, export ══════════════════════════════════
# The model is deterministic, so between two runs the only thing that changes is
# the book. Every account's tier is written to a snapshot once per ISO week; the
# review compares this week's run with the last one and says exactly what moved,
# so the team knows the list is current before working it for upsell.

_SNAPSHOT_FILE = _os.path.join(_BASE, "data", "tier_snapshots.jsonl")
_TIERS = ("Strategic", "Tier 1", "Tier 2", "Tier 3")


def _iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def review_period():
    """This week's run, when it was taken, and when the next review is due."""
    import datetime as _dt
    today = _dt.date.today()
    next_mon = today + _dt.timedelta(days=(7 - today.weekday()) or 7)
    return {"week": _iso_week(today), "today": today, "next": next_mon,
            "days_to_next": (next_mon - today).days}


def load_tier_snapshots():
    import json as _json
    out = []
    try:
        with open(_SNAPSHOT_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(_json.loads(line))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return out


def _snapshot_of(rows):
    import datetime as _dt
    return {"week": _iso_week(_dt.date.today()),
            "taken": _dt.datetime.now().isoformat(timespec="seconds"),
            "accounts": {r["name"]: {"tier": r["final"], "score": round(r["score"], 4),
                                     "approved": r["approved"], "type": r["type"]}
                         for r in rows}}


def ensure_weekly_snapshot(rows, force=False):
    """Write this week's snapshot if it is missing. A forced re-run inside the
    same week replaces that week's row, so the log stays one line per week.
    Returns (history, current, previous)."""
    import json as _json
    hist = load_tier_snapshots()
    week = _iso_week(review_period()["today"])
    if force or not hist or hist[-1]["week"] != week:
        snap = _snapshot_of(rows)
        try:
            _os.makedirs(_os.path.dirname(_SNAPSHOT_FILE), exist_ok=True)
            if hist and hist[-1]["week"] == week:
                hist[-1] = snap
                with open(_SNAPSHOT_FILE, "w") as f:
                    for h in hist:
                        f.write(_json.dumps(h) + "\n")
            else:
                hist.append(snap)
                with open(_SNAPSHOT_FILE, "a") as f:
                    f.write(_json.dumps(snap) + "\n")
        except Exception:
            if not hist or hist[-1]["week"] != week:
                hist.append(snap)   # still usable on screen even if the disk write failed
    return hist, hist[-1], (hist[-2] if len(hist) > 1 else None)


def _taken_label(snap):
    import datetime as _dt
    try:
        return _dt.datetime.fromisoformat(snap["taken"]).strftime("%-d %b %Y")
    except Exception:
        return snap.get("week", "—")


def weekly_changes(rows, previous):
    """What moved since the last review. With no earlier snapshot the tier on file
    in the workbook is the baseline, so the first review is still an honest diff."""
    prev = (previous or {}).get("accounts")
    baseline = _taken_label(previous) if previous else "tier on file"
    out, seen = [], set()
    for r in rows:
        seen.add(r["name"])
        now = r["final"]
        if prev is not None:
            p = prev.get(r["name"])
            if p is None:
                out.append({"row": r, "name": r["name"], "type": r["type"], "kind": "new",
                            "was": "—", "now": now, "direction": "up",
                            "d_score": 0.0, "d_vol": 0.0})
                continue
            was = p["tier"]
            d_score, d_vol = r["score"] - p.get("score", r["score"]), r["approved"] - p.get("approved", r["approved"])
        else:
            was = _TIER_NORM.get(str(r["current_tier"]).strip(), str(r["current_tier"]).strip())
            if _TIER_RANK.get(was, -1) < 0:
                continue
            d_score, d_vol = 0.0, 0.0
        if was != now:
            out.append({"row": r, "name": r["name"], "type": r["type"], "kind": "moved",
                        "was": was, "now": now,
                        "direction": "up" if _TIER_RANK.get(now, 0) > _TIER_RANK.get(was, 0) else "down",
                        "d_score": d_score, "d_vol": d_vol})
    if prev is not None:
        for name, p in prev.items():
            if name not in seen:
                out.append({"row": None, "name": name, "type": p.get("type", "—"), "kind": "dropped",
                            "was": p["tier"], "now": "—", "direction": "down",
                            "d_score": 0.0, "d_vol": 0.0})
    order = {"moved": 0, "new": 1, "dropped": 2}
    out.sort(key=lambda c: (order[c["kind"]], c["direction"] != "up",
                            -(c["row"]["score"] if c["row"] else 0)))
    return out, baseline


def _change_matrix(changes, tiers=_TIERS):
    """Arrivals per tier, split by how they got there."""
    m = {t: {"Promoted into": 0, "Demoted into": 0, "New to book": 0, "Left": 0} for t in tiers}
    for c in changes:
        if c["kind"] == "moved" and c["now"] in m:
            m[c["now"]]["Promoted into" if c["direction"] == "up" else "Demoted into"] += 1
        elif c["kind"] == "new" and c["now"] in m:
            m[c["now"]]["New to book"] += 1
        elif c["kind"] == "dropped" and c["was"] in m:
            m[c["was"]]["Left"] += 1
    return m


def _history_counts(hist, names=None):
    """Tier head-count per snapshot, optionally restricted to a set of accounts."""
    out = []
    for h in hist:
        counts = {t: 0 for t in _TIERS}
        for n, a in h["accounts"].items():
            if names is not None and n not in names:
                continue
            if a["tier"] in counts:
                counts[a["tier"]] += 1
        out.append({"week": h["week"], "taken": _taken_label(h), **counts})
    return out


def _tier_on_file(r):
    t = str(r["current_tier"]).strip()
    return _TIER_NORM.get(t, t if t in _TIERS else "Tier 3")


def tier_list_df(rows, changes):
    ch = {c["name"]: c for c in changes if c["row"] is not None}
    recs = []
    for r in rows:
        c = ch.get(r["name"])
        recs.append({
            "Account": r["name"], "Partner": r["partner"],
            "Tier on file": _tier_on_file(r),
            "Model proposes": r["final"], "Score %": round(r["score"] * 100),
            "Tier": r["final"],
            "Type": r["type"], "Focus": r["focus"],
            "Region": r["region"], "Country": r["country"],
            "Integration": r["integration"], "Deal stage": r["stage"],
            "Approved txns / mo": int(r["approved"]),
            "Change this week": (f'{c["was"]} → {c["now"]}' if c and c["kind"] == "moved"
                                 else "new to book" if c else "—"),
            "Owner": r["manager"], "Must-have": "yes" if r["must_have"] else "",
            "Why": "; ".join(f"{k}: {why}" for k, _, _, why in r["criteria"]),
        })
    return pd.DataFrame(recs)


def changes_df(changes):
    return pd.DataFrame([{
        "Partner": c["name"], "Type": c["type"], "Change": c["kind"],
        "Was": c["was"], "Now": c["now"],
        "Direction": "↑" if c["direction"] == "up" else "↓",
        "Score %": round(c["row"]["score"] * 100) if c["row"] else None,
        "Score Δ pp": round(c["d_score"] * 100, 1),
        "Approved txns Δ": int(c["d_vol"]),
        "Focus": c["row"]["focus"] if c["row"] else "—",
        "Owner": c["row"]["manager"] if c["row"] else "—",
    } for c in changes])


def changes_figure(changes, hist, current, baseline, names=None, height=300):
    """The graph the review ends on: arrivals per tier this week, and the tier
    head-count across every snapshot so a trend is visible once there is one.
    Drawn for the light page ground the chart actually sits on."""
    from plotly.subplots import make_subplots
    m = _change_matrix(changes)
    series = [("Promoted into", "#2F8A1F"), ("Demoted into", "#B3261E"),
              ("New to book", "#3E4FE0"), ("Left", "#9AA0B4")]
    hc = _history_counts(hist, names)
    fig = make_subplots(rows=1, cols=2, column_widths=[0.5, 0.5], horizontal_spacing=0.1,
                        subplot_titles=(f"What changed · last update {_taken_label(current)} · vs {baseline}",
                                        f"Head-count by tier · {len(hc)} weekly snapshot{'s' if len(hc)!=1 else ''}"))
    for lbl, col in series:
        fig.add_trace(go.Bar(name=lbl, x=list(_TIERS), y=[m[t][lbl] for t in _TIERS],
                             marker_color=col, marker_line_width=0), row=1, col=1)
    for t in _TIERS:
        fig.add_trace(go.Scatter(name=t, x=[h["taken"] for h in hc], y=[h[t] for h in hc],
                                 mode="lines+markers", line=dict(color=_TIER_COLOR[t], width=2),
                                 marker=dict(size=7)), row=1, col=2)
    fig.update_layout(
        barmode="group", height=height, margin=dict(l=10, r=10, t=36, b=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#676E8A", size=10.5),
        legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=10)),
    )
    for ann in fig.layout.annotations:
        ann.font = dict(size=11, color="#10131C")
        ann.x = ann.x - 0.25 if ann.x < 0.5 else ann.x - 0.25
        ann.xanchor = "left"
    fig.update_xaxes(gridcolor="rgba(0,0,0,.05)", zeroline=False, type="category")
    fig.update_yaxes(gridcolor="rgba(0,0,0,.07)", zeroline=False, rangemode="tozero")
    return fig


def export_tier_excel(df, changes, hist, current, baseline, scope_label, names=None, per_tier=False,
                      tier_col="Tier"):
    """One workbook: the list, what changed, the snapshot log — and the chart
    on the last sheet, so a printed copy ends the same way the screen does."""
    import io
    buf = io.BytesIO()
    hc = _history_counts(hist, names)
    m = _change_matrix(changes)
    cdf = changes_df(changes)
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        wb = xw.book
        h_fmt = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#10131C",
                               "font_name": "Arial", "font_size": 10, "border": 0})
        t_fmt = wb.add_format({"bold": True, "font_size": 16, "font_name": "Arial", "font_color": "#10131C"})
        s_fmt = wb.add_format({"font_size": 10, "font_name": "Arial", "font_color": "#676E8A"})
        n_fmt = wb.add_format({"num_format": "#,##0", "font_name": "Arial", "font_size": 10})
        b_fmt = wb.add_format({"font_name": "Arial", "font_size": 10})
        meta = [f"Last update: {_taken_label(current)} ({current['week']})",
                f"Compared to: {baseline}", f"Scope: {scope_label}",
                f"Focus flags: FinX upsell = {', '.join(sorted(_FINX_TYPES))} (plus wallets / stablecoins filed elsewhere); "
                f"Merchant lead source = live acquirer with ≥ {_SIGNIFICANT_VOLUME:,} approved txns / month, "
                f"or a card scheme (Visa, Mastercard)"]

        def sheet(name, frame, title, start=6):
            frame.to_excel(xw, sheet_name=name, index=False, startrow=start)
            ws = xw.sheets[name]
            ws.hide_gridlines(2)
            ws.write(0, 0, title, t_fmt)
            for i, line in enumerate(meta):
                ws.write(1 + i, 0, line, s_fmt)
            for j, col in enumerate(frame.columns):
                ws.write(start, j, col, h_fmt)
                width = min(48, max(10, int(frame[col].astype(str).str.len().quantile(.9)) + 2)) if len(frame) else 14
                ws.set_column(j, j, width, n_fmt if frame[col].dtype.kind in "if" else b_fmt)
            ws.freeze_panes(start + 1, 1)
            if len(frame):
                ws.autofilter(start, 0, start + len(frame), len(frame.columns) - 1)
            return ws

        sheet("Tier list", df, f"Yuno partner tiers · {scope_label}")
        if per_tier and tier_col in df.columns:
            for t in _TIERS:
                part = df[df[tier_col] == t].reset_index(drop=True)
                sheet(t, part, f"{t} · {len(part)} accounts")
        log = pd.DataFrame([{"Week": h["week"], "Taken": h["taken"], **{t: h[t] for t in _TIERS}} for h in hc])
        sheet("Snapshot log", log, "Weekly snapshot log")
        # last sheet: the diff, and the graph underneath it
        ws2 = sheet("What changed", cdf if len(cdf) else pd.DataFrame({"Partner": ["nothing moved"]}),
                    "What changed since the last review")

        # the graph at the end — a summary table the chart reads from, then the chart
        r0 = 6 + len(cdf) + 3
        ws2.write(r0, 0, "Arrivals per tier", h_fmt)
        keys = ["Promoted into", "Demoted into", "New to book", "Left"]
        for j, k in enumerate(keys):
            ws2.write(r0, 1 + j, k, h_fmt)
        for i, t in enumerate(_TIERS):
            ws2.write(r0 + 1 + i, 0, t, b_fmt)
            for j, k in enumerate(keys):
                ws2.write(r0 + 1 + i, 1 + j, m[t][k], n_fmt)
        ch = wb.add_chart({"type": "column"})
        for j, k in enumerate(keys):
            ch.add_series({"name": ["What changed", r0, 1 + j],
                           "categories": ["What changed", r0 + 1, 0, r0 + len(_TIERS), 0],
                           "values": ["What changed", r0 + 1, 1 + j, r0 + len(_TIERS), 1 + j],
                           "fill": {"color": ["#37610A", "#B3261E", "#3E4FE0", "#9AA0B4"][j]}})
        ch.set_title({"name": f"What changed · last update {_taken_label(current)} · vs {baseline}",
                      "name_font": {"size": 11}})
        ch.set_legend({"position": "bottom"})
        ch.set_size({"width": 620, "height": 300})
        ws2.insert_chart(r0 + len(_TIERS) + 2, 0, ch)

        r1 = r0 + len(_TIERS) + 2 + 16
        ws2.write(r1, 0, "Head-count by tier, per weekly snapshot", h_fmt)
        for j, t in enumerate(_TIERS):
            ws2.write(r1, 1 + j, t, h_fmt)
        for i, h in enumerate(hc):
            ws2.write(r1 + 1 + i, 0, h["taken"], b_fmt)
            for j, t in enumerate(_TIERS):
                ws2.write(r1 + 1 + i, 1 + j, h[t], n_fmt)
        if len(hc) > 1:
            ln = wb.add_chart({"type": "line"})
            for j, t in enumerate(_TIERS):
                ln.add_series({"name": ["What changed", r1, 1 + j],
                               "categories": ["What changed", r1 + 1, 0, r1 + len(hc), 0],
                               "values": ["What changed", r1 + 1, 1 + j, r1 + len(hc), 1 + j],
                               "marker": {"type": "circle", "size": 5},
                               "line": {"color": _TIER_COLOR[t], "width": 2}})
            ln.set_title({"name": "Tier head-count over time", "name_font": {"size": 11}})
            ln.set_legend({"position": "bottom"})
            ln.set_size({"width": 620, "height": 300})
            ws2.insert_chart(r1 + len(hc) + 2, 0, ln)
    return buf.getvalue()


_SCREEN_COLS = ["Account", "Type", "Focus", "Region", "Country", "Integration", "Deal stage",
                "Approved txns / mo", "Tier on file", "Model proposes", "Score %", "Owner"]


def _tier_reason(r):
    """Why this account sits where it does — every criterion, its weight, and the
    row in the book it was read from."""
    tc = _TIER_COLOR[r["final"]]
    on_file = _tier_on_file(r)
    crit = "".join(
        f'<div style="display:grid;grid-template-columns:210px 56px 1fr;gap:12px;align-items:center;'
        f'padding:8px 0;border-top:1px solid #EEF0F6;">'
        f'<div style="font-size:12.5px;color:#10131C;font-weight:500;">{k}'
        f'<span style="color:#9AA0B4;font-weight:400;"> · {wt*100:.0f}%</span></div>'
        f'<div style="font-size:13px;font-weight:600;color:#10131C;font-variant-numeric:tabular-nums;">{v:.0f} / 5</div>'
        f'<div style="font-size:12px;color:#676E8A;">{why}</div></div>'
        for k, v, wt, why in r["criteria"])
    flags = " · ".join(x for x in [
        "named must-have" if r["must_have"] else "",
        "FinX upsell" if r["finx"] else "", "merchant lead source" if r["lead_source"] else ""] if x) or "no focus flag"
    st.markdown(
        f'<div style="background:#F7F8FF;border:1px solid #C9D0FF;border-left:3px solid {tc};'
        f'border-radius:0 0 12px 12px;padding:14px 20px 16px;margin:-8px 0 12px;">'
        f'<div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-size:16px;font-weight:600;color:#10131C;">{r["name"]}</span>'
        f'<span style="margin-left:auto;font-size:12px;color:#676E8A;">on file '
        f'<b style="color:#10131C;">{on_file}</b> &nbsp;→&nbsp; model '
        f'<b style="color:{tc};">{r["final"]}</b> · <b style="color:#10131C;">{r["score"]*100:.0f}%</b></span></div>'
        f'<div style="font-size:12px;color:#676E8A;margin-top:3px;">{r["type"]} · {r["region"]} · {r["country"]} · '
        f'{r["integration"]} · {r["stage"]} · owner {r["manager"]}</div>'
        f'<div style="margin:10px 0 6px;">{_score_bar(r["score"], height=7)}</div>'
        f'<div style="font-size:12px;color:#676E8A;margin-bottom:8px;">{_gate_text(r)} &nbsp;·&nbsp; {flags}</div>'
        f'{crit}'
        f'<div style="font-size:11px;color:#9AA0B4;margin-top:10px;">Score = Σ criterion × weight ÷ 5. '
        f'Volume is the partner\'s live traffic ({_fmt_txn(r["approved"])} approved txns / month). '
        + (f'Consolidated from {len(r["accounts"])} accounts on file ({", ".join(r["accounts"])}) — '
           f'scored on {r["scored_account"]}, the strongest. ' if len(r.get("accounts", [])) > 1 else "")
        + f'Source: partnerships_accounts.xlsx.</div></div>',
        unsafe_allow_html=True)


def _move_control(r):
    """Move a partner to another bucket, or hand it back to the model. Written
    to disk, so the whole team sees the same placement next week."""
    m1, m2, m3 = st.columns([1.1, 2.6, 2.3])
    m1.markdown('<div style="font-size:12px;color:#676E8A;padding-top:9px;">Move to</div>',
                unsafe_allow_html=True)
    # A fresh widget after every move, so a stale pill can never re-apply itself.
    nonce = st.session_state.get("move_nonce", 0)
    with m2:
        target = st.pills("Move to", list(_TIERS), default=None, key=f"move_{r['key']}_{nonce}",
                          label_visibility="collapsed")
    if target and target != r["final"]:
        save_placement(r["key"], r["name"], target)
        run_tiering.clear()
        st.session_state.tier_pick = target
        st.session_state.move_nonce = nonce + 1
        st.rerun()
    with m3:
        if r.get("manual"):
            if st.button(f"Back to model ({r['computed']})", key=f"unmove_{r['key']}"):
                save_placement(r["key"], r["name"], None)
                run_tiering.clear()
                st.session_state.tier_pick = r["computed"]
                st.session_state.move_nonce = nonce + 1
                st.rerun()
        else:
            st.markdown(f'<div style="font-size:11px;color:#9AA0B4;padding-top:9px;">'
                        f'Placed by the model at {r["score"]*100:.0f}%. A move is kept on file and '
                        f'shown as a manual placement.</div>', unsafe_allow_html=True)


def _account_list(view, tier, basis):
    """Every account in the tier as a clickable row. The chosen one opens in
    place, with the reason it landed where it did."""
    sel = st.session_state.get("tier_sel")
    if sel not in {r["name"] for r in view}:
        sel = None
    q = st.text_input("Find an account", key=f"tier_find_{tier.replace(' ', '')}",
                      placeholder="Find an account…", label_visibility="collapsed")
    shown = [r for r in view if not q or q.lower() in (r["name"] + " " + r["partner"]).lower()]
    if not shown:
        st.markdown('<div style="font-size:12.5px;color:#676E8A;padding:10px 4px;">'
                    'No account matches that search.</div>', unsafe_allow_html=True)
        return
    with st.container(key="tierlist", height=min(58 * len(shown) + (500 if sel else 0) + 12, 800)):
        for i, r in enumerate(shown):
            other = (f"model {r['final']}" if basis == "Tier on file" else f"on file {_tier_on_file(r)}")
            meta = " · ".join(x for x in [
                r["type"], r["region"], r["integration"],
                f"{_fmt_txn(r['approved'])} txns/mo" if r["approved"] > 0 else "",
                r["focus"] if r["focus"] != "—" else "",
                f"owner {r['manager']}", f"{other} · {r['score']*100:.0f}%"] if x)
            if st.button(f"{_md(r['name'])}\n\n{_md(meta)}", key=f"acct_{tier.replace(' ', '')}_{i}",
                         use_container_width=True,
                         type="primary" if sel == r["name"] else "secondary"):
                st.session_state.tier_sel = None if sel == r["name"] else r["name"]
                st.rerun()
            if sel == r["name"]:
                _tier_reason(r)
                _move_control(r)


def _tier_browser(rows, changes, hist, current, baseline, refresh):
    """One instrument: pick a tier, see who is in it, click one for the reason,
    download the whole tiering."""
    basis = st.session_state.get("tier_basis", "Modelled")
    tier_of = (lambda r: _tier_on_file(r)) if basis == "Tier on file" else (lambda r: r["final"])
    book = rows

    # ── Whose book ───────────────────────────────────────────────────────────
    roster = [m for m in manager_roster() if any(m in split_managers(r["manager"]) for r in rows)]
    o1, o2, o3, o4 = st.columns([2.0, 2.05, 1.15, 1.5])
    with o1:
        owner = st.selectbox("Partner manager", ["All partner managers"] + roster, key="tier_owner",
                             label_visibility="collapsed")
    if owner != "All partner managers":
        rows = [r for r in rows if owner in split_managers(r["manager"])]
    split = {t: [] for t in _TIERS}
    for r in rows:
        split[tier_of(r)].append(r)
    stats, _ = _tier_stats(rows, split)
    tier = st.session_state.get("tier_pick", "Strategic")
    with o4, st.container(key="tierdl"):
        st.download_button(
            "Download entire tiering",
            data=export_tier_excel(tier_list_df(book, changes), changes, hist, current, baseline,
                                   f"whole book · {len(book)} accounts · tiers {basis.lower()}",
                                   per_tier=True, tier_col="Tier on file" if basis == "Tier on file" else "Tier"),
            file_name=f"Yuno_partner_tiering_{current['week']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="tier_dl_book", use_container_width=True)

    # ── Pick a tier ──────────────────────────────────────────────────────────
    with st.container(key="tierpick"):
        cc = st.columns(4)
        for c, t in zip(cc, _TIERS):
            n, v = stats[t]["n"], stats[t]["vol_share"]
            fx = sum(1 for r in split[t] if r["finx"])
            sub = f"{n} account{'s' if n != 1 else ''} · {fx} FinX · {v:.0f}% of volume"
            if c.button(f"{_md(t)}\n\n{_md(sub)}", key=f"tierpick_{t.replace(' ', '')}",
                        use_container_width=True, type="primary" if tier == t else "secondary"):
                st.session_state.tier_pick = t
                st.session_state.tier_sel = None
                st.rerun()

    # ── Filter + basis ───────────────────────────────────────────────────────
    f1, f2 = st.columns([2.2, 2.8])
    with f1:
        show = st.pills("Show", ["All", "FinX upsell", "Merchant lead sources"], default="All",
                        key="tier_show", label_visibility="collapsed") or "All"
    with f2:
        new_basis = st.pills("Tiers", ["Modelled", "Tier on file"], default="Modelled",
                             key="tier_basis_pick", label_visibility="collapsed") or "Modelled"
        if new_basis != basis:
            st.session_state.tier_basis = new_basis
            st.session_state.tier_sel = None
            st.rerun()
    view = [r for r in split[tier]
            if show == "All" or (show == "FinX upsell" and r["finx"])
            or (show == "Merchant lead sources" and r["lead_source"])]
    df = tier_list_df(view, changes)
    with o3:
        st.download_button(
            "Download this list", data=export_tier_excel(
                df, [c for c in changes if c["now"] == tier or c["was"] == tier],
                hist, current, baseline,
                f"{tier} · {show} · {owner} · tiers {basis.lower()}",
                {r["name"] for r in split[tier]}),
            file_name=f"Yuno_{tier.replace(' ', '')}_{current['week']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="tier_dl_tier", use_container_width=True)

    # ── The list ─────────────────────────────────────────────────────────────
    n_finx = sum(1 for r in view if r["finx"])
    n_lead = sum(1 for r in view if r["lead_source"])
    n_must = sum(1 for r in view if r["must_have"])
    tc = _TIER_COLOR[tier]
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:6px 0 8px;">'
        f'<span style="font-size:15px;font-weight:600;color:#10131C;">'
        f'<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:{tc};'
        f'margin-right:8px;vertical-align:1px;"></span>{tier} <span style="font-weight:400;color:#9AA0B4;">'
        f'· {basis.lower()}{"" if owner == "All partner managers" else " · " + owner}</span></span>'
        f'<span style="font-size:12px;color:#676E8A;">'
        f'<b style="color:#10131C;">{len(view)}</b> accounts · '
        f'<b style="color:#10131C;">{n_must}</b> must-have · '
        f'<b style="color:#10131C;">{n_finx}</b> FinX upsell · '
        f'<b style="color:#10131C;">{n_lead}</b> merchant lead sources</span>'
        f'<span style="margin-left:auto;font-size:11px;color:#9AA0B4;">click an account for the reason · '
        f'{_TIER_DEFS[tier]["gate"]}</span></div>', unsafe_allow_html=True)
    if not view:
        st.markdown('<div style="background:#fff;border:1px solid #E4E6F0;border-radius:12px;'
                    'padding:22px;font-size:13px;color:#676E8A;text-align:center;">'
                    f'No {tier} accounts match that filter.</div>', unsafe_allow_html=True)
    else:
        _account_list(view, tier, basis)

    # ── Weekly review strip, then the graph ──────────────────────────────────
    moved = [c for c in changes if c["kind"] == "moved"]
    ups = sum(1 for c in moved if c["direction"] == "up")
    new = sum(1 for c in changes if c["kind"] == "new")
    gone = sum(1 for c in changes if c["kind"] == "dropped")
    w1, w2 = st.columns([5.2, 1])
    w1.markdown(
        f'<div style="background:#fff;border:1px solid #E4E6F0;border-radius:12px;padding:12px 16px;'
        f'margin-top:14px;display:flex;gap:18px;flex-wrap:wrap;align-items:baseline;font-size:12px;'
        f'color:#676E8A;">'
        f'<span style="font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;'
        f'color:#3E4FE0;">Weekly review</span>'
        f'<span>Last update <b style="color:#10131C;">{_taken_label(current)}</b> · {current["week"]}</span>'
        f'<span>Compared to <b style="color:#10131C;">{baseline}</b></span>'
        f'<span>Next review <b style="color:#10131C;">{refresh["next"].strftime("%a %-d %b")}</b></span>'
        f'<span style="margin-left:auto;"><b style="color:#10131C;">{len(moved)}</b> moved '
        f'(<span style="color:#2F8A1F;">{ups} ↑</span> · <span style="color:#B3261E;">{len(moved)-ups} ↓</span>) · '
        f'<b style="color:#10131C;">{new}</b> new · <b style="color:#10131C;">{gone}</b> left</span></div>',
        unsafe_allow_html=True)
    with w2:
        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        if st.button("Re-run scoring", key="tier_rerun", use_container_width=True,
                     help="Reads the workbook again and replaces this week's snapshot."):
            for fn in (run_tiering, load_live_traffic, load_tiering_framework, manager_roster):
                try: fn.clear()
                except Exception: pass
            st.session_state.tier_force_rerun = True
            st.rerun()
    st.plotly_chart(changes_figure(changes, hist, current, baseline, height=270),
                    use_container_width=True, config={"displayModeBar": False})


def show_partner_tiers():
    rows, w, cuts = run_tiering()
    if not rows:
        st.markdown(
            f'<div style="background:{_c("panel")};border:1px solid rgba(255,184,77,.34);'
            f'border-radius:14px;padding:18px 20px;font-size:13px;color:#FFB84D;line-height:1.6;">'
            f'<b>Partner accounts workbook not found.</b><br>Put <code>partnerships_accounts.xlsx</code> '
            f'and <code>partner_tiering_model.xlsx</code> in <code>data/</code> and reload.</div>',
            unsafe_allow_html=True)
        return

    refresh = review_period()
    alerts_all = tier_alerts(rows)
    hist, current, previous = ensure_weekly_snapshot(
        rows, force=st.session_state.pop("tier_force_rerun", False))
    changes, baseline = weekly_changes(rows, previous)

    # ── Console shell ────────────────────────────────────────────────────────
    n_strat = sum(1 for r in rows if r["final"] == "Strategic")
    n_t1 = sum(1 for r in rows if r["final"] == "Tier 1")
    n_finx = sum(1 for r in rows if r["finx"] and r["final"] in ("Strategic", "Tier 1", "Tier 2"))
    n_lead = sum(1 for r in rows if r["lead_source"])
    st.markdown(f"""
<div class="tc-shell"><div class="tc-in">
  <div class="tc-top">
    <span class="tc-live" style="width:7px;height:7px;border-radius:50%;
          background:{_c('lime')};box-shadow:0 0 8px {_c('lime')};"></span>
    <span class="tc-eyebrow">Tiering automation · live</span>
    <span class="tc-clock">Review {refresh['week']} · updated {_taken_label(current)} · next review
      {refresh['next'].strftime('%-d %b')} ({refresh['days_to_next']}d)</span>
  </div>
  <div class="tc-h">Partner tiering</div>
  <div class="tc-sub">The partner network run as a revenue engine and a lead machine. Every account
    is scored 0–5 on five weighted criteria — Yuno volume and growth (today's revenue), external
    market weight (the must-have providers), co-sell and referral activity (who sends merchants to
    Yuno), deal and integration stage (can we sell through it now) and upsell potential (a FinX rail
    with more Yuno products to sell) — and placed against fixed gates, one row per partner.
    Strategic partners get a named owner, an upsell plan and a pipeline QBR; Tier 1 is the promotion
    pool and the lead engine; Tier 2 and Tier 3 run on automation and are promoted on evidence.
    Re-scored every week.</div>
  <div class="tc-rail">
    <div class="tc-stat"><div class="v" style="color:#EEF0FA;">{len(rows)}</div>
      <div class="k">Accounts scored</div></div>
    <div class="tc-stat"><div class="v" style="color:{_TIER_CONSOLE['Strategic']};">{n_strat}</div>
      <div class="k">Strategic</div></div>
    <div class="tc-stat"><div class="v" style="color:{_TIER_CONSOLE['Tier 1']};">{n_t1}</div>
      <div class="k">Tier 1</div></div>
    <div class="tc-stat"><div class="v" style="color:{_c('amber')};">{n_finx}</div>
      <div class="k">FinX upsell targets</div></div>
    <div class="tc-stat"><div class="v" style="color:{_c('lime')};">{n_lead}</div>
      <div class="k">Merchant lead sources</div></div>
    <div class="tc-stat"><div class="v" style="color:{_c('blue_ink')};">{len(alerts_all)}</div>
      <div class="k">Differ from tier on file</div></div>
  </div>
</div></div>""", unsafe_allow_html=True)

    # ── The tiering itself ───────────────────────────────────────────────────
    # Pick a tier, see every account in it, download the whole thing. The weekly
    # diff and its graph close the section, the same way the export does.
    _tier_browser(rows, changes, hist, current, baseline, refresh)


# ── Contacts View ──────────────────────────────────────────────────────────────


# ── Performance View ───────────────────────────────────────────────────────────

# ── Insights View ──────────────────────────────────────────────────────────────

# ── Merchants ──────────────────────────────────────────────────────────────────

# ── Benchmarks ─────────────────────────────────────────────────────────────────

# ── Payment Recommendations ──────────────────────────────────────────────────
# Partner enrichment data for expanded detail view



# ── Partners In Flight ─────────────────────────────────────────────────────────






# ── Merchant Simulation ──────────────────────────────────────────────────────




# ── Home / Welcome Panel ────────────────────────────────────────────────────────
# ── Market Expansion ───────────────────────────────────────────────────────────
# ══ Integration overview ═══════════════════════════════════════════════════════
# What Yuno actually built against the partner's API, in the partner's own
# vocabulary. The fact sheet is the solutions team's, not a marketing summary:
# where a capability is unconfirmed it says so rather than rounding up to a tick.

_INTEG_STATUS = {
    "Implemented":   ("#EAF3E3", "#37610A", "rgba(55,97,10,.22)"),
    "Unknown":       ("#FDF8E8", "#8A4B00", "rgba(138,106,0,.26)"),
    "Not supported": ("#F3F0F2", "#7A2233", "rgba(122,34,51,.20)"),
}

# Matrix cell vocabulary, straight from the document's legend.
_CELL = {
    "✓": ("#37610A", "#EAF3E3", "supported"),
    "?": ("#8A4B00", "#FDF8E8", "confirm against live config"),
    "~": ("#00697F", "#DDEFF4", "typical — varies by method"),
    "—": ("#8991AC", "transparent", "not applicable to this rail"),
    "":  ("#C3C8DC", "transparent", "not available"),
}


def integration_for(name):
    """The fact sheet for this partner, or None when we hold none."""
    if not name:
        return None
    return _INTEGRATIONS.get(str(name).strip().upper())


def _integ_totals(d):
    """Headline counts — derived here, never typed into the data file."""
    methods = {m[0] for m in d.get("global_methods", [])}
    markets = set()
    for r in d.get("regions", []):
        for row in r["rows"]:
            methods.add(row[0])
            for code, cell in zip(r["countries"], row[2]):
                if cell in ("✓", "?"):
                    markets.add(code)
    ops = d.get("card_capabilities", []) + d.get("card_operations", [])
    live = sum(1 for _, v in ops if v == "Implemented")
    return len(methods), len(markets), live, len(ops)


def _cell_html(v):
    ink, bg, _ = _CELL.get(v, _CELL[""])
    glyph = v or "·"
    weight = 700 if v in ("✓", "?") else 400
    return (f'<td style="text-align:center;padding:6px 4px;font-size:12px;font-weight:{weight};'
            f'color:{ink};background:{bg};">{glyph}</td>')


def _matrix_table(countries, rows):
    head = "".join(
        f'<th style="padding:7px 4px;font-size:9.5px;font-weight:600;color:#676E8A;'
        f'text-transform:uppercase;letter-spacing:.06em;text-align:center;'
        f'border-bottom:1px solid rgba(35,42,61,.12);">{c}</th>' for c in countries)
    body = ""
    for name, kind, cells in rows:
        body += (
            '<tr>'
            f'<td style="padding:6px 10px 6px 0;font-size:11.5px;font-weight:600;color:#10131C;'
            f'white-space:nowrap;border-bottom:1px solid rgba(35,42,61,.055);">{name}</td>'
            f'<td style="padding:6px 14px 6px 0;font-size:11px;color:#676E8A;white-space:nowrap;'
            f'border-bottom:1px solid rgba(35,42,61,.055);">{kind}</td>'
            + "".join(_cell_html(c).replace(
                'padding:6px 4px;', 'padding:6px 4px;border-bottom:1px solid rgba(35,42,61,.055);')
                for c in cells)
            + '</tr>')
    return (
        '<div style="overflow-x:auto;">'
        '<table style="width:100%;border-collapse:collapse;font-family:var(--font);'
        'font-variant-numeric:tabular-nums;">'
        '<thead><tr>'
        '<th style="text-align:left;padding:7px 10px 7px 0;font-size:9.5px;font-weight:600;'
        'color:#676E8A;text-transform:uppercase;letter-spacing:.06em;'
        'border-bottom:1px solid rgba(35,42,61,.12);">Payment method</th>'
        '<th style="text-align:left;padding:7px 14px 7px 0;font-size:9.5px;font-weight:600;'
        'color:#676E8A;text-transform:uppercase;letter-spacing:.06em;'
        'border-bottom:1px solid rgba(35,42,61,.12);">Type</th>'
        f'{head}</tr></thead><tbody>{body}</tbody></table></div>')


def _legend(text):
    return (f'<div style="font-size:10.5px;color:#858CA6;line-height:1.6;margin-top:9px;'
            f'font-family:var(--font);">{text}</div>')


def _panel(inner, pad="18px 20px"):
    return (f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            f'border-radius:14px;padding:{pad};margin-bottom:12px;'
            f'box-shadow:var(--shadow);font-family:var(--font);">{inner}</div>')


def _status_pill(v):
    bg, ink, br = _INTEG_STATUS.get(v, _INTEG_STATUS["Unknown"])
    return (f'<span style="display:inline-flex;align-items:center;font-size:9.5px;font-weight:600;'
            f'padding:2px 7px;border-radius:5px;background:{bg};color:{ink};'
            f'border:1px solid {br};white-space:nowrap;">{v}</span>')


def _kv_status_rows(pairs):
    return "".join(
        '<div style="display:flex;align-items:center;gap:10px;padding:6px 0;'
        'border-bottom:1px solid rgba(35,42,61,.055);">'
        f'<span style="font-size:11.5px;color:#10131C;font-family:var(--mono);">{k}</span>'
        f'<span style="margin-left:auto;">{_status_pill(v)}</span></div>'
        for k, v in pairs)


def show_integration_overview(acct, name):
    """The full fact sheet — what Yuno consumes from this partner's API."""
    d = integration_for(name) or integration_for(acct.get("name"))

    if st.button("← Back to your record", key="integ_back"):
        st.session_state.integration_open = False
        st.rerun()

    if not d:
        st.markdown(hero("Integration overview", eyebrow="Integration",
                         subtitle=f"We do not yet hold a published integration fact sheet for {name}."),
                    unsafe_allow_html=True)
        st.markdown(
            '<div style="padding:18px 20px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
            'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
            '<b>Nothing published yet.</b><br>Your Yuno solutions engineer assembles this sheet '
            'from the live connector configuration. Ask your partner manager to have it published '
            'and it appears here.</div>', unsafe_allow_html=True)
        return

    n_methods, n_markets, n_live, n_total = _integ_totals(d)
    st.markdown(hero(
        f"Yuno × {d['provider']} integration",
        eyebrow="Integration overview",
        subtitle=("Everything Yuno consumes from your API — payment method and country coverage, "
                  "card capabilities and operations, and how each family settles and disputes."),
        tiles=[(str(n_methods), "Methods", "#E0ED80"),
               (str(n_markets), "Markets", "#8B9BFF"),
               (f"{n_live}/{n_total}", "Card items live", "#B9C2FF"),
               (str(len(d["channels"])), "Channels", "#FFD400")]),
        unsafe_allow_html=True)

    # ── Channels ──────────────────────────────────────────────────────────────
    st.markdown(_section_label("Channels integrated", top=6), unsafe_allow_html=True)
    cols = st.columns(len(d["channels"]))
    for col, ch in zip(cols, d["channels"]):
        note = (f'<div style="margin-top:10px;padding:9px 11px;background:#FDF8E8;'
                f'border:1px solid rgba(138,106,0,.22);border-radius:8px;font-size:10.5px;'
                f'color:#6E5400;line-height:1.55;">{ch["note"]}</div>') if ch["note"] else ""
        col.markdown(_panel(
            f'<div style="font-size:14px;font-weight:600;color:#10131C;letter-spacing:-.01em;">'
            f'{ch["name"]}</div>'
            f'<div style="font-size:10px;font-weight:600;letter-spacing:{_TRACK};'
            f'text-transform:uppercase;color:#2F3FC4;margin-top:5px;">{ch["channel"]}</div>'
            f'<div style="font-size:12px;color:#676E8A;line-height:1.6;margin-top:8px;">'
            f'{ch["detail"]}</div>{note}'), unsafe_allow_html=True)

    # ── The four views ────────────────────────────────────────────────────────
    view = nav_radio("Integration view",
                     ["Method coverage", "Card capabilities", "Features by family",
                      "Settlement & disputes"], "integ_view")

    if view == "Method coverage":
        st.markdown(_section_label("Global methods"), unsafe_allow_html=True)
        rows = "".join(
            '<div style="display:flex;align-items:baseline;gap:12px;padding:8px 0;'
            'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<span style="font-size:12px;font-weight:600;color:#10131C;min-width:96px;">{m}</span>'
            f'<span style="font-size:11px;color:#2F3FC4;min-width:104px;">{t}</span>'
            f'<span style="font-size:11.5px;color:#676E8A;line-height:1.55;">{c}</span></div>'
            for m, t, c in d["global_methods"])
        st.markdown(_panel(rows + _legend(d["legend_coverage"])), unsafe_allow_html=True)

        for r in d["regions"]:
            st.markdown(_section_label(f'{r["name"]} — {len(r["rows"])} methods'),
                        unsafe_allow_html=True)
            st.markdown(_panel(_matrix_table(r["countries"], r["rows"])),
                        unsafe_allow_html=True)

        st.markdown(_panel(
            f'<div style="font-size:11.5px;color:#676E8A;line-height:1.65;">{d["coverage_note"]}</div>'
            f'<div style="margin-top:11px;">{_chip(d["source"] + " · " + d["as_of"], "data")}</div>',
            pad="15px 18px"), unsafe_allow_html=True)

    elif view == "Card capabilities":
        st.markdown(_section_label(
            "Card integration — capabilities & operations", top=6), unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:12px;color:#676E8A;line-height:1.6;margin-bottom:12px;">'
            f'Applies to the CARD method. <b>{n_live} of {n_total}</b> items are implemented; '
            f'the rest are unconfirmed in the current configuration rather than known gaps.'
            f'</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(_panel(
            '<div style="font-size:10px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;'
            'color:#676E8A;margin-bottom:8px;">Capabilities</div>'
            + _kv_status_rows(d["card_capabilities"])), unsafe_allow_html=True)
        c2.markdown(_panel(
            '<div style="font-size:10px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;'
            'color:#676E8A;margin-bottom:8px;">Operations</div>'
            + _kv_status_rows(d["card_operations"])), unsafe_allow_html=True)
        st.markdown(f'<div style="margin-bottom:14px;">{_chip(d["source"] + " · card config", "data")}</div>',
                    unsafe_allow_html=True)

    elif view == "Features by family":
        st.markdown(_section_label("Features enabled per method family", top=6),
                    unsafe_allow_html=True)
        head = "".join(
            f'<th style="padding:8px 10px;font-size:9.5px;font-weight:600;color:#676E8A;'
            f'text-transform:uppercase;letter-spacing:.06em;text-align:center;'
            f'border-bottom:1px solid rgba(35,42,61,.12);">{c}</th>' for c in d["family_columns"])
        body = ""
        for feat, cells in d["family_rows"]:
            body += ('<tr>'
                     f'<td style="padding:8px 10px 8px 0;font-size:12px;color:#10131C;'
                     f'border-bottom:1px solid rgba(35,42,61,.055);">{feat}</td>'
                     + "".join(_cell_html(c).replace(
                         'padding:6px 4px;',
                         'padding:8px 10px;border-bottom:1px solid rgba(35,42,61,.055);')
                         for c in cells) + '</tr>')
        st.markdown(_panel(
            '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;'
            'font-family:var(--font);font-variant-numeric:tabular-nums;"><thead><tr>'
            '<th style="text-align:left;padding:8px 10px 8px 0;font-size:9.5px;font-weight:600;'
            'color:#676E8A;text-transform:uppercase;letter-spacing:.06em;'
            'border-bottom:1px solid rgba(35,42,61,.12);">Feature</th>'
            f'{head}</tr></thead><tbody>{body}</tbody></table></div>'
            + _legend(d["family_legend"])), unsafe_allow_html=True)
        st.markdown(_panel(
            f'<div style="font-size:11.5px;color:#676E8A;line-height:1.65;">{d["family_note"]}</div>',
            pad="15px 18px"), unsafe_allow_html=True)

    else:
        st.markdown(_section_label("Settlement & dispute model by family", top=6),
                    unsafe_allow_html=True)
        for fam, model, dispute, timing in d["settlement"]:
            st.markdown(_panel(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                f'<span style="font-size:13.5px;font-weight:600;color:#10131C;">{fam}</span>'
                f'<span style="margin-left:auto;font-size:10.5px;color:#2F3FC4;background:#E9ECFC;'
                f'border:1px solid rgba(84,104,245,.22);border-radius:5px;padding:2px 8px;">'
                f'{timing}</span></div>'
                f'<div style="display:flex;gap:18px;flex-wrap:wrap;">'
                f'<div style="flex:1;min-width:220px;">'
                f'<div style="font-size:9.5px;font-weight:600;letter-spacing:.09em;'
                f'text-transform:uppercase;color:#858CA6;margin-bottom:4px;">Settlement</div>'
                f'<div style="font-size:12px;color:#676E8A;line-height:1.6;">{model}</div></div>'
                f'<div style="flex:1;min-width:220px;">'
                f'<div style="font-size:9.5px;font-weight:600;letter-spacing:.09em;'
                f'text-transform:uppercase;color:#858CA6;margin-bottom:4px;">Disputes</div>'
                f'<div style="font-size:12px;color:#676E8A;line-height:1.6;">{dispute}</div></div>'
                f'</div>', pad="16px 18px"), unsafe_allow_html=True)

        st.markdown(_section_label("Transaction flows"), unsafe_allow_html=True)
        st.markdown(_panel("".join(
            '<div style="display:flex;gap:12px;padding:9px 0;'
            'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<div style="font-size:12px;font-weight:600;color:#10131C;min-width:210px;">{t}</div>'
            f'<div style="font-size:11.5px;color:#676E8A;line-height:1.6;">{b}</div></div>'
            for t, b in d["flows"])
            + _legend(d["settlement_note"])), unsafe_allow_html=True)


def _show_own_record(acct):
    """Everything Yuno holds on this one partner — and nothing on any other."""
    name = acct["name"]

    # The integration sheet is a page of its own — too much to inline, and the
    # partner's engineers want a link they can send on.
    if st.session_state.get("integration_open"):
        return show_integration_overview(acct, name)

    st.markdown(hero(
        name, lockup=yuno_lockup(name, 20), badge="Your record",
        subtitle=(f"This is the record Yuno holds on {name}. Other partners in the "
                  f"programme are not shown.")), unsafe_allow_html=True)

    show_e2e_flow(acct, name)

    rows = [("Partner name", acct["name"]), ("Account", acct["account"]),
            ("Type", acct["type"]),
            ("Region", acct["region"]), ("Country", acct["country"]),
            ("Classification", acct["classification"]), ("Deal stage", friendly_stage(acct["stage"])),
            ("Integration", acct["integration"]), ("Your Yuno manager", acct["manager"])]
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:0;background:#fff;'
        'border:1px solid rgba(35,42,61,.10);border-radius:14px;padding:18px 22px;margin-bottom:12px;">'
        + "".join(
            f'<div style="flex:1;min-width:158px;padding:8px 16px 8px 0;">'
            f'<div style="font-size:9.5px;color:#676E8A;text-transform:uppercase;letter-spacing:.09em;'
            f'font-weight:600;margin-bottom:4px;">{k}</div>'
            f'<div style="font-size:13.5px;font-weight:500;color:#10131C;">{v}</div></div>'
            for k, v in rows)
        + f'<div style="width:100%;margin-top:10px;padding-top:11px;'
        f'border-top:1px solid rgba(35,42,61,.08);">'
        f'{_chip("Your record only · maintained by your Yuno manager", "data")}</div></div>',
        unsafe_allow_html=True)

    integration_cta(name)

    st.markdown(
        '<div style="padding:15px 19px;background:#E9ECFC;border:1px solid rgba(84,104,245,.22);'
        'border-radius:var(--r-ctl);font-size:12.5px;color:#3A4155;line-height:1.65;margin-top:12px;">'
        'Something here out of date? Your Yuno manager owns this record — tell them and it is '
        'corrected at source, which keeps every number on Partner Health consistent with it.</div>',
        unsafe_allow_html=True)
    if st.button("Tell Yuno what changed", key="rec_share"):
        st.session_state.page = "Share"; st.query_params["page"] = "Share"; st.rerun()


def integration_cta(name, key="integ_open"):
    """The clickable way into the fact sheet. Rendered wherever we know the company."""
    _integ = integration_for(name)
    st.markdown(_section_label("Integration overview"), unsafe_allow_html=True)
    if _integ:
        _n_methods, _n_markets, _n_live, _n_total = _integ_totals(_integ)
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#10131C 0%,#191E2F 100%);'
            f'border:1px solid #232A3D;border-radius:14px;padding:20px 22px;margin-bottom:10px;'
            f'font-family:var(--font);position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:-70px;right:-50px;width:300px;height:300px;'
            f'border-radius:50%;background:radial-gradient(circle,rgba(84,104,245,0.20),'
            f'transparent 65%);pointer-events:none;"></div>'
            f'<div style="position:relative;z-index:1;">'
            f'<div style="font-size:14.5px;font-weight:600;color:#EEF0FA;letter-spacing:-.01em;">'
            f'What Yuno has integrated from your API</div>'
            f'<div style="font-size:12px;color:#8991AC;line-height:1.6;margin-top:6px;'
            f'max-width:620px;">Payment method and country coverage, card capabilities and '
            f'operations, the features live per method family, and how each family settles '
            f'and disputes.</div>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;">'
            + "".join(
                f'<div style="background:rgba(255,255,255,0.04);'
                f'border:.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:9px 13px;'
                f'text-align:center;min-width:84px;">'
                f'<div style="font-size:15px;font-weight:700;color:{c};'
                f'font-variant-numeric:tabular-nums;">{v}</div>'
                f'<div style="font-size:9.5px;color:#4A5170;text-transform:uppercase;'
                f'letter-spacing:.06em;margin-top:2px;">{k}</div></div>'
                for v, k, c in [(str(_n_methods), "Methods", "#E0ED80"),
                                (str(_n_markets), "Markets", "#8B9BFF"),
                                (f"{_n_live}/{_n_total}", "Card items live", "#B9C2FF"),
                                (str(len(_integ["channels"])), "Channels", "#FFD400")])
            + '</div></div></div>', unsafe_allow_html=True)
        if st.button("Open integration overview  →", key=key,
                     use_container_width=True, type="primary"):
            st.session_state.integration_open = True
            st.rerun()
    else:
        st.markdown(
            '<div style="padding:16px 19px;background:#F1F3FB;border:1px solid rgba(35,42,61,.10);'
            'border-radius:var(--r-ctl);font-size:12.5px;color:#4A5170;line-height:1.65;">'
            '<b>No integration sheet published yet.</b><br>Once your Yuno solutions engineer '
            'publishes the connector configuration, the full method, capability and settlement '
            'breakdown appears here.</div>', unsafe_allow_html=True)


def show_partners():
    # An external partner has no business browsing the connector directory — that
    # list is their competitors. They are routed to their own record only.
    _ext = external_account()
    if _ext is not None:
        return _show_own_record(_ext)
    if st.session_state.role == "partner":
        # We could not match a row in the account book — but the sign-in domain
        # still names the company, and the integration sheet is keyed on that.
        # Show what we can rather than a dead end.
        _ident = st.session_state.get("partner_identity") or {}
        _company = _ident.get("company") or ""
        if st.session_state.get("integration_open") and integration_for(_company):
            return show_integration_overview({"name": _company}, _company)

        st.markdown(hero(
            "Partner Portfolio",
            eyebrow="Your record",
            subtitle=("We could not match your company to a row in Yuno's account book, so the "
                      "record below is incomplete. Your partner manager can link it at source."),
            badge="Partial"), unsafe_allow_html=True)
        st.markdown(
            '<div style="padding:18px 20px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
            'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
            '<b>We could not identify your company.</b><br>Sign in with your work email so we can '
            'show your record. The partner directory is internal to Yuno.</div>', unsafe_allow_html=True)
        if integration_for(_company):
            integration_cta(_company, key="integ_open_partial")
        return

    # Internal-only view switch: the connector directory, or the tiering model run
    # over the same book of accounts.
    if st.session_state.role == "internal":
        view = nav_radio("Partner Portfolio view", ["Connectors", "Partner tiers"],
                         "partners_view")
        if view == "Partner tiers":
            return show_partner_tiers()

    if st.session_state.selected_partner is not None:
        sel = st.session_state.selected_partner
        partner = next((p for p in PARTNERS_DATA if p["name"] == sel), None)
        if partner:
            _partner_detail(partner)
            return
        else:
            st.session_state.selected_partner = None

    # ── Build connector data for HTML component (cached) ────────────────────
    _connector_data, total, sot_live_ct, countries_ct = _build_connector_data()

    # The Type dropdown asked one closed question; this asks an open one.
    _connector_data, _intent = show_connector_search(_connector_data)
    if _intent:
        total = len(_connector_data)

    import json as _json
    _data_json = _json.dumps(_connector_data).replace("'","\\'").replace("</","<\\/")

    # Read the HTML template and inject data
    _html_file = _os.path.join(_BASE, "yuno_connectors.html")
    with open(_html_file, "r") as _f:
        _html_content = _f.read()

    # Replace the hardcoded DATA array with our dynamic data
    _html_content = _html_content.replace(
        "var DATA = [",
        f"var DATA = {_data_json}; var _ORIGINAL_DATA = ["
    )
    # Update stat numbers
    _html_content = _html_content.replace(">460<", f">{total}<")
    _html_content = _html_content.replace(">97<", f">{sot_live_ct}<")
    _html_content = _html_content.replace(">189<", f">{countries_ct}<")
    _html_content = _html_content.replace("var YUNO_LOGO_B64='';", f"var YUNO_LOGO_B64='{_LOGO_B64}';")

    # Hidden download buttons (triggered by JS Export menu)
    _partners_df = _build_partners_df()
    st.markdown("""<style>
    [data-testid="stDownloadButton"] {position:absolute !important;opacity:0 !important;height:0 !important;overflow:hidden !important;pointer-events:auto !important;z-index:-1 !important;}
    </style>""", unsafe_allow_html=True)
    st.download_button("Download PDF", data=_export_pdf(_partners_df),
                       file_name="Yuno_Partner_Portfolio.pdf", mime="application/pdf", key="st_pdf_dl")
    st.download_button("Download Excel", data=_export_excel(_partners_df),
                       file_name="Yuno_Partner_Portfolio.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="st_xlsx_dl")

    components.html(_html_content, height=2400, scrolling=True)
    return


@st.cache_data
def _build_connector_data():
    total = len(PARTNERS_DATA)
    live_all = sum(1 for p in PARTNERS_DATA if p["status"] == "Live")
    countries_ct = len(set(p.get("country","") for p in PARTNERS_DATA if p.get("country","") and p.get("country","") != "nan"))
    sot_live_ct = len(_SOT_DF[_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live"]["PROVIDER_NAME"].unique()) if len(_SOT_DF) > 0 else live_all

    import json as _json
    _connector_data = []
    for p in PARTNERS_DATA:
        enrich = _PARTNER_ENRICHMENT.get(p["name"].upper().replace("(","").replace(")","").strip())
        manager = p.get("manager","—")
        if manager == "nan": manager = "—"
        # Payment methods from SOT
        sot_pms = []
        if len(_SOT_DF) > 0:
            pm_rows = _SOT_DF[(_SOT_DF["PROVIDER_NAME"].str.upper() == p["name"].upper()) & (_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live")]
            sot_pms = sorted(pm_rows["PAYMENT_METHOD_TYPE"].dropna().unique().tolist())[:8]
        country = p.get("country","")
        if country == "nan": country = "—"
        # SOT capabilities lookup
        _sot_caps = {}
        if len(_SOT_DF) > 0:
            _p_sot = _SOT_DF[_SOT_DF["PROVIDER_NAME"].str.upper() == p["name"].upper()]
            _sot_caps = {
                "gaming": bool(any(_p_sot["ACCEPTS_GAMING"].isin([True, 1, 1.0]))),
                "gambling": bool(any(_p_sot["ACCEPTS_GAMBLING"].isin([True, 1, 1.0]))),
                "crypto": bool(any(_p_sot["ACCEPTS_CRYPTO"].isin([True, 1, 1.0]))),
                "recurring": bool(any(_p_sot["SUPPORTS_RECURRING_PAYMENTS"].isin([True, 1, 1.0]))),
                "tokenization": bool(any(_p_sot["SUPPORTS_TOKENIZATION"].isin([True, 1, 1.0]))),
                "payouts": bool(any(_p_sot["SUPPORTS_PAYOUTS"].isin([True, 1, 1.0]))),
                "installments": bool(any(_p_sot["SUPPORTS_INSTALLMENTS"].isin([True, 1, 1.0]))),
                "airlines": bool(any(_p_sot["ACCEPTS_AIRLINES"].isin([1, 1.0]))),
                "regions": sorted(_p_sot["REGION"].dropna().unique().tolist()),
                "countries": sorted(_p_sot["COUNTRY_ISO"].dropna().unique().tolist()),
            }

        # External contacts from partner files
        _ext_key = p["name"].upper().replace("(","").replace(")","").strip()
        _ext = _EXT_CONTACTS.get(_ext_key, {})
        _comm_name = _ext.get("commercial_contact","") or (enrich["commercial_contact"] if enrich else "") or "TBD"
        _comm_email = _ext.get("commercial_email","") or "TBD"
        _comm_phone = _ext.get("commercial_phone","") or "TBD"
        _tech_name = _ext.get("technical_contact","") or (enrich["technical_contact"] if enrich else "") or "TBD"
        _tech_email = _ext.get("technical_email","") or "TBD"
        _tech_phone = _ext.get("technical_phone","") or "TBD"
        # Verticals from external data (Source of Truth features)
        _ext_verts = _ext.get("verticals","")
        _verticals_list = [v.strip() for v in _ext_verts.split(",") if v.strip()] if _ext_verts else (enrich["verticals"].split(", ") if enrich and enrich.get("verticals") else ["TBD"])

        _connector_data.append({
            "name": p["name"], "type": p["cat"], "region": p.get("region","—"), "country": country, "status": p["status"],
            "caps": _sot_caps,
            "contacts": [
                {"name": _comm_name, "role": "Commercial", "email": _comm_email, "phone": _comm_phone, "color": "#5A6486"},
                {"name": _tech_name, "role": "Technical", "email": _tech_email, "phone": _tech_phone, "color": "#5A7A00"},
                {"name": manager if manager != "—" else "Partnerships Team", "role": "Escalation", "email": "", "phone": "", "color": "#C4384A"},
            ],
            "verticals": _verticals_list,
            "currencies": ["USD","Local"],
            "auth": {"type": "Full Auth", "settlement": "T+1", "settleCurrency": "Local / USD", "chargebackWindow": "90 days"},
            "onboarding": {"kyb": bool(p.get("nda")), "integration": enrich["onboarding"].split(",")[0] if enrich else "API", "timeline": enrich["onboarding"].split(",")[-1].strip() if enrich else "2-4 weeks", "localEntity": False, "jurisdiction": "—", "entityType": "Contact partnerships"},
            "pricing": {"standard": enrich["avg_pricing"] if enrich else "TBD", "discount": enrich["discount_rate"] if enrich else "TBD", "discountWhen": enrich["discount_condition"] if enrich else "TBD", "mdr": "Blended", "fx": "TBD", "minimums": "TBD"},
            "paymentMethods": sot_pms if sot_pms else ["Card"],
            "health": {"score": 85 if p["status"]=="Live" else 55 if "Agreement" in p["status"] else 30, "label": enrich["health"] if enrich else ("Live" if p["status"]=="Live" else "Pipeline")},
            "tier": p.get("tier","—").replace("Partners","").replace("(Global)","").replace("Strategic Partners: Very Important","Strategic").strip().rstrip(":").strip() or "—",
            "strategic": bool(p.get("strategic")),
            "intReady": bool(p.get("int_ready")),
            "intUsed": bool(p.get("int_used")),
            "nda": bool(p.get("nda")),
            "revshare": enrich["revshare"] if enrich else ("Yes" if p.get("revshare") else "No"),
        })
    return _connector_data, total, sot_live_ct, countries_ct

    # ── OLD CODE (kept for reference, never executes) ─────────────────────────
    st.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="font-size:22px;font-weight:700;color:#10131C;letter-spacing:-0.8px;margin-bottom:4px;">Yuno Connectors</div>
  <div style="font-size:13px;color:#858CA6;">Search, filter and explore Yuno's payment partner ecosystem. Find the right connector for your merchant.</div>
</div>""", unsafe_allow_html=True)

    # ── Stat cards ────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:20px;text-align:center;"><div style="font-size:22px;font-weight:700;color:#3E4FE0;letter-spacing:-1px;">{total}</div><div style="font-size:11px;color:#858CA6;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;">Total Connectors</div></div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:20px;text-align:center;"><div style="font-size:22px;font-weight:700;color:#5A7A00;letter-spacing:-1px;">{sot_live_ct}</div><div style="font-size:11px;color:#858CA6;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;">Live & Active</div></div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:20px;text-align:center;"><div style="font-size:22px;font-weight:700;color:#5A6486;letter-spacing:-1px;">{countries_ct}</div><div style="font-size:11px;color:#858CA6;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;">Countries Covered</div></div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:20px;text-align:center;"><div style="font-size:22px;font-weight:700;color:#B36200;letter-spacing:-1px;">89.4%</div><div style="font-size:11px;color:#858CA6;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;">Avg Approval Rate</div></div>
</div>""", unsafe_allow_html=True)

    # ── AI Search box ─────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(160deg,#080911,#10131C);border-radius:14px;padding:24px 28px 18px;margin-bottom:0;position:relative;overflow:hidden;">
  <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:radial-gradient(circle,rgba(84,104,245,0.1),transparent 65%);pointer-events:none;"></div>
  <div style="position:relative;z-index:1;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <span style="font-size:15px;">✦</span>
      <span style="font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#8B9BFF;">Smart Search</span>
    </div>
    <div style="font-size:12px;color:#676E8A;line-height:1.6;margin-bottom:6px;">Search by name, type, country, or describe what you need — even with typos. We'll find the closest match.</div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="background:#fff;border:1px solid #E2E6F4;border-radius:0 0 14px 14px;padding:14px 22px 8px;margin-bottom:4px;"></div>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Describe what you're looking for...", key="partner_search_input", label_visibility="collapsed")

    # Quick search prompts
    _QS_PROMPTS = [
        "Copa Airlines expanding into the U.S.",
        "Uber needs local processing in Brazil",
        "iGaming operator entering Turkey",
        "Crypto exchange launching in UAE",
        "SaaS recurring payments in Saudi Arabia",
    ]
    st.markdown('<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1px;margin:4px 0 6px;">Quick Search</div>', unsafe_allow_html=True)
    qs_cols = st.columns(len(_QS_PROMPTS))
    for qi, prompt in enumerate(_QS_PROMPTS):
        if qs_cols[qi].button(prompt, key=f"qs_conn_{qi}", use_container_width=True):
            st.session_state["qs_search"] = prompt
            st.rerun()

    # Apply quick search if set
    if st.session_state.get("qs_search"):
        if not search:
            search = st.session_state["qs_search"]
        else:
            st.session_state["qs_search"] = ""

    # Style quick search buttons
    components.html("""<script>
setTimeout(function(){
  var doc = window.parent.document;
  var prompts = ['Copa Airlines','Uber needs','iGaming','Crypto exchange','SaaS recurring'];
  doc.querySelectorAll('button').forEach(function(btn){
    if(prompts.some(function(p){return btn.textContent.trim().startsWith(p);})){
      btn.style.cssText='background:#E9ECFC !important;border:1px solid #B9C2FF !important;border-radius:10px !important;padding:10px 12px !important;font-size:12px !important;color:#3E4FE0 !important;font-weight:500 !important;cursor:pointer !important;box-shadow:none !important;text-align:left !important;line-height:1.3 !important;min-height:0 !important;';
    }
  });
},200);
</script>""", height=0)

    # ── Filters (collapsible) ─────────────────────────────────────────────────
    with st.expander("Filters & Export", expanded=False):
        fc = st.columns([1, 1, 1, 1])
        with fc[0]:
            type_filter = st.selectbox("Type", ["Type","PSP","Acquirer","APM","Fraud","BaaS","Other"], key="pd_type_filter", label_visibility="collapsed")
        with fc[1]:
            _pd_regions = sorted(set(p.get("region","") for p in PARTNERS_DATA if p.get("region","")))
            region_filter = st.selectbox("Region", ["Region"] + _pd_regions, key="pd_region_filter", label_visibility="collapsed")
        with fc[2]:
            _pd_countries = sorted(set(p.get("country","") for p in PARTNERS_DATA if p.get("country","") and p.get("country","") != "nan"))
            country_filter = st.selectbox("Country", ["Country"] + _pd_countries[:40], key="pd_country_filter", label_visibility="collapsed")
        with fc[3]:
            stage_filter = st.selectbox("Status", ["Status","Live","Agreement Signed","Agreement Review","Negotiation","Prospect"], key="pd_stage_filter", label_visibility="collapsed")
        fc2 = st.columns([1, 1, 1, 1])
        with fc2[0]:
            _pm_options = ["Payment Method"]
            if len(_SOT_DF) > 0:
                _pm_options += sorted(_SOT_DF["PAYMENT_METHOD_TYPE"].dropna().unique().tolist())[:30]
            pm_filter = st.selectbox("PM", _pm_options, key="pd_pm_filter", label_visibility="collapsed")
        with fc2[1]:
            vert_filter = st.selectbox("Vertical", ["Vertical","High Risk","Gambling","Gaming","Forex","Crypto","Airlines"], key="pd_vert_filter", label_visibility="collapsed")
        with fc2[2]:
            sort_by = st.selectbox("Sort", ["Sort by","Popularity","Cost effective","High performance"], key="pd_sort", label_visibility="collapsed")
        with fc2[3]:
            export_fmt = st.selectbox("Export", ["Export","CSV","PDF","Excel","PPTX"], key="pd_export", label_visibility="collapsed")
        if export_fmt != "Export":
            st.info(f"Generating {export_fmt}... (production: file download with merchant logo)")
            st.session_state["pd_export"] = "Export"

    # ── Filter logic ──────────────────────────────────────────────────────────
    filt = list(PARTNERS_DATA)
    if type_filter != "Type":
        filt = [p for p in filt if p["cat"] == type_filter]
    if stage_filter != "Status":
        filt = [p for p in filt if p["status"] == stage_filter]
    if region_filter != "Region":
        filt = [p for p in filt if p.get("region") == region_filter]
    if country_filter != "Country":
        filt = [p for p in filt if p.get("country") == country_filter]
    # ── AI Smart Search ────────────────────────────────────────────────────────
    _ai_rec = None  # Will hold recommendation if complex query detected
    if search:
        sl = search.lower()
        _search_aliases = {"u.s.":"united states","u.s":"united states","usa":"united states","us":"united states",
                           "uk":"united kingdom","uae":"united arab emirates","emirates":"united arab emirates",
                           "brasil":"brazil","ksa":"saudi arabia","saudi":"saudi arabia","dubai":"united arab emirates",
                           "igaming":"gambling","betting":"gambling","casino":"gambling",
                           "crypto":"crypto","airline":"airlines","aviation":"airlines","flight":"airlines",
                           "forex":"forex","trading":"forex","saas":"psp","recurring":"psp"}
        _stop_words = {"the","a","an","in","into","for","to","and","or","of","with","is","by","on","at","from",
                        "needs","need","wants","want","expanding","entering","launching","looking","operator",
                        "exchange","company","processing","local","payments","payment","top","best","find",
                        "can","you","provide","short","list","partners","partner","high","low","rates","rate",
                        "approvals","approval","please","help","me","what","are","which","should","recommend",
                        "we","our","their","them","this","that","these","those"}
        # Detect intent qualifiers
        wants_low_cost = any(w in sl for w in ["low rate","low cost","cheap","cost effective","affordable","discount"])
        wants_high_perf = any(w in sl for w in ["high approval","high performance","best approval","top perform","reliable"])
        wants_live = any(w in sl for w in ["live","active","ready","available"])
        wants_acquirer = "acquir" in sl
        wants_psp = "psp" in sl or "gateway" in sl or "aggregat" in sl
        wants_apm = "apm" in sl or "wallet" in sl or "local method" in sl
        # Detect country from aliases
        detected_country = ""
        for alias, full in sorted(_search_aliases.items(), key=lambda x: -len(x[0])):
            if alias in sl:
                detected_country = full
                break
        # Also check raw country names in partner data
        if not detected_country:
            for p in PARTNERS_DATA:
                cname = p.get("country","").lower()
                if cname and cname != "nan" and cname in sl:
                    detected_country = p.get("country","")
                    break
        # Expand aliases
        expanded = sl
        for alias, replacement in _search_aliases.items():
            if alias in sl:
                expanded = expanded + " " + replacement
        tokens = [t.strip(".,!?") for t in expanded.split() if t.strip(".,!?").lower() not in _stop_words and len(t.strip(".,!?")) > 1]
        if not tokens:
            tokens = [sl]
        def _smart_match(p, tokens):
            searchable = f"{p['name']} {p['cat']} {p.get('region','')} {p.get('country','')} {p['status']} {p.get('offering_raw','')} {p.get('tier','')} {p.get('manager','')}".lower()
            for t in tokens:
                if t in searchable:
                    return True
                if len(t) >= 3 and any(w.startswith(t[:3]) for w in searchable.split()):
                    return True
            return False
        filt = [p for p in filt if _smart_match(p, tokens)]
        # Apply intent filters
        if wants_acquirer:
            filt = [p for p in filt if p["cat"] == "Acquirer"]
        elif wants_psp:
            filt = [p for p in filt if p["cat"] == "PSP"]
        elif wants_apm:
            filt = [p for p in filt if p["cat"] == "APM"]
        if wants_live:
            filt = [p for p in filt if p["status"] == "Live"]
        if detected_country:
            country_filt = [p for p in filt if detected_country.lower() in p.get("country","").lower() or detected_country.lower() in p.get("region","").lower()]
            if country_filt:
                filt = country_filt
        # Sort by intent
        if wants_low_cost:
            filt = sorted(filt, key=lambda x: 0 if x.get("strategic") else 1)
        if wants_high_perf:
            filt = sorted(filt, key=lambda x: (0 if x.get("int_used") else 1, 0 if x["status"]=="Live" else 1))
        # Build AI recommendation if this looks like a complex query (>4 words)
        if len(search.split()) > 3 and filt:
            top = filt[:5]
            top_names = [p["name"] for p in top]
            rec_type = "acquirers" if wants_acquirer else "PSPs" if wants_psp else "APMs" if wants_apm else "connectors"
            rec_country = detected_country if detected_country else "your target market"
            rec_why = []
            if wants_live: rec_why.append("live and processing")
            if wants_high_perf: rec_why.append("high approval rates")
            if wants_low_cost: rec_why.append("competitive pricing")
            if not rec_why: rec_why.append("best overall fit")
            _ai_rec = {"names": top_names, "type": rec_type, "country": rec_country, "why": rec_why, "count": len(filt)}
    if vert_filter != "Vertical" and len(_SOT_DF) > 0:
        vert_col = _VERTICAL_COLS.get(vert_filter)
        if vert_col and vert_col in _SOT_DF.columns:
            vert_providers = set(_SOT_DF[(_SOT_DF[vert_col] == True) | (_SOT_DF[vert_col] == 1)]["PROVIDER_NAME"].str.upper().unique())
            filt = [p for p in filt if p["name"].upper() in vert_providers]
    if pm_filter != "Payment Method" and len(_SOT_DF) > 0:
        pm_providers = set(_SOT_DF[_SOT_DF["PAYMENT_METHOD_TYPE"] == pm_filter]["PROVIDER_NAME"].str.upper().unique())
        filt = [p for p in filt if p["name"].upper() in pm_providers]
    if sort_by == "Popularity":
        filt = sorted(filt, key=lambda x: 0 if x["status"] == "Live" else 1)
    elif sort_by == "High performance":
        filt = sorted(filt, key=lambda x: (0 if x.get("int_used") else 1, 0 if x.get("revshare_active") else 1))

    # ── AI Recommendation card ──────────────────────────────────────────────
    _STATUS_TAG = {"Live":("#F0F5DC","#3F5208"),"Agreement Signed":("#DFE3F2","#464F6E"),"Agreement Review":("#FAF0D0","#8A4B00"),"Negotiation":("#FAF0D0","#8A4B00"),"Prospect":("#F1F3FB","#4A5170"),"Lost":("#FAE2E5","#C4384A")}
    _TYPE_TAG = {"PSP":("#DFE3F2","#464F6E"),"Acquirer":("#DFE3F2","#464F6E"),"APM":("#E9ECFC","#2F3FC4"),"Fraud":("#FAE2E5","#C4384A"),"BaaS":("#FAF0D0","#8A4B00"),"Other":("#F1F3FB","#4A5170")}

    if _ai_rec:
        r = _ai_rec
        top_pills = "".join(f'<span style="font-size:12px;font-weight:700;padding:4px 14px;border-radius:8px;background:#E9ECFC;color:#3E4FE0;border:0.5px solid #B9C2FF;">{n}</span>' for n in r["names"])
        why_text = ", ".join(r["why"])
        # Get enrichment data for top picks
        detail_rows = ""
        for pname in r["names"]:
            enrich = _PARTNER_ENRICHMENT.get(pname.upper().replace("(","").replace(")","").strip())
            pricing = enrich["avg_pricing"] if enrich else "—"
            discount = enrich["discount_rate"] if enrich else "—"
            health = enrich["health"] if enrich else "—"
            detail_rows += (f'<tr style="border-bottom:0.5px solid #E9ECFC;">'
                            f'<td style="padding:8px 12px;font-size:13px;font-weight:700;color:#10131C;">{pname}</td>'
                            f'<td style="padding:8px 12px;font-size:12px;color:#676E8A;">{pricing}</td>'
                            f'<td style="padding:8px 12px;font-size:12px;font-weight:700;color:#3F5208;">{discount}</td>'
                            f'<td style="padding:8px 12px;font-size:12px;color:#676E8A;">{health}</td>'
                            f'</tr>')
        th_r = "padding:6px 12px;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#858CA6;border-bottom:1px solid #E9ECFC;"
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#E9ECFC,#F7F8FD);border:1px solid #B9C2FF;border-radius:14px;padding:22px 24px;margin-bottom:16px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
    <span style="font-size:14px;">✦</span>
    <span style="font-size:11px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:0.8px;">AI Recommendation</span>
  </div>
  <div style="font-size:14px;font-weight:600;color:#10131C;line-height:1.6;margin-bottom:12px;">
    Based on your query, here are the <strong>top {len(r["names"])} {r["type"]}</strong> for <strong>{r["country"]}</strong> — selected for {why_text}.
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">{top_pills}</div>
  <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;">
    <thead><tr><th style="{th_r}">Partner</th><th style="{th_r}">Std Rate</th><th style="{th_r}">Best Rate</th><th style="{th_r}">Health</th></tr></thead>
    <tbody>{detail_rows}</tbody>
  </table>
  <div style="margin-top:12px;font-size:11px;color:#676E8A;line-height:1.5;">Click any partner below to see full details — contacts, payment methods, integration status, and onboarding requirements.</div>
</div>""", unsafe_allow_html=True)

    # ── Results table + expandable details ────────────────────────────────────
    th = "padding:10px 14px;text-align:left;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#858CA6;border-bottom:1px solid #E2E6F4;background:#F7F8FD;"
    rows_html = ""
    for i, p in enumerate(filt[:80]):
        s_bg, s_color = _STATUS_TAG.get(p["status"], ("#F1F3FB","#4A5170"))
        t_bg, t_color = _TYPE_TAG.get(p["cat"], ("#F1F3FB","#4A5170"))
        country = p.get("country","")
        if country == "nan": country = "—"
        bb = "border-bottom:0.5px solid #F1F3FB;" if i < min(len(filt),80)-1 else ""
        td = f"padding:11px 14px;{bb}font-size:13px;vertical-align:middle;"
        rows_html += (f'<tr onmouseover="this.style.background=\'#F7F8FD\'" onmouseout="this.style.background=\'#fff\'">'
                      f'<td style="{td}font-weight:700;color:#10131C;">{p["name"]}</td>'
                      f'<td style="{td}"><span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:5px;background:{t_bg};color:{t_color};">{p["cat"]}</span></td>'
                      f'<td style="{td}color:#676E8A;">{p.get("region","—")}</td>'
                      f'<td style="{td}color:#676E8A;">{country}</td>'
                      f'<td style="{td}"><span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:5px;background:{s_bg};color:{s_color};">{p["status"]}</span></td>'
                      f'</tr>')

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin:8px 0 10px;"><span style="font-size:14px;font-weight:700;color:#10131C;">{len(filt)}</span><span style="font-size:11px;color:#858CA6;">connectors found</span></div>
<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:12px;overflow:hidden;margin-bottom:14px;">
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr>
      <th style="{th}">Connector Name</th>
      <th style="{th}">Type</th>
      <th style="{th}">Region</th>
      <th style="{th}">Country</th>
      <th style="{th}">Status</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

    # Expandable detail per partner
    st.markdown('<div style="font-size:11px;color:#858CA6;margin-bottom:6px;">Click any connector below to view full details</div>', unsafe_allow_html=True)

    for i, p in enumerate(filt[:80]):
        s_bg, s_color = _STATUS_TAG.get(p["status"], ("#F1F3FB","#4A5170"))
        t_bg, t_color = _TYPE_TAG.get(p["cat"], ("#F1F3FB","#4A5170"))
        country = p.get("country","")
        if country == "nan": country = "—"

        with st.expander(p["name"], expanded=False):
            manager = p.get("manager","—")
            if manager == "nan": manager = "—"
            tier_short = p.get("tier","").replace("Partners","").replace("(Global)","").replace("Strategic Partners: Very Important","Strategic").strip().rstrip(":").strip()
            if not tier_short or tier_short == "nan": tier_short = "—"

            health_map = {"Live":85,"Agreement Signed":55,"Agreement Review":45,"Negotiation":40,"Prospect":25,"Lost":10}
            health = health_map.get(p["status"], 30)
            if p.get("int_used"): health = min(health + 10, 98)
            if p.get("revshare_active"): health = min(health + 5, 99)
            h_color = "#5A7A00" if health >= 70 else "#B36200" if health >= 40 else "#C4384A"
            h_text = "#3F5208" if health >= 70 else "#8A4B00" if health >= 40 else "#C4384A"

            # Enrichment data lookup
            enrich = _PARTNER_ENRICHMENT.get(p["name"].upper().replace("(","").replace(")","").strip())
            _ext_d = _EXT_CONTACTS.get(p["name"].upper().replace("(","").replace(")","").strip(), {})
            comm_contact = _ext_d.get("commercial_contact","") or (enrich["commercial_contact"] if enrich else "") or "TBD"
            tech_contact = _ext_d.get("technical_contact","") or (enrich["technical_contact"] if enrich else "") or "TBD"
            _ext_verts_d = _ext_d.get("verticals","")
            verticals = _ext_verts_d if _ext_verts_d else (enrich["verticals"] if enrich else "TBD")
            pricing = enrich["avg_pricing"] if enrich else "TBD"
            discount = enrich["discount_rate"] if enrich else "TBD"
            discount_cond = enrich["discount_condition"] if enrich else "TBD"
            revshare_status = enrich["revshare"] if enrich else ("Yes" if p.get("revshare") else "TBD")
            onboarding = enrich["onboarding"] if enrich else "TBD"
            merch_live = enrich["merchants_live"] if enrich else 0
            merch_names = enrich["merchants"] if enrich else "TBD"
            p_health_label = enrich["health"] if enrich else ("Good" if health >= 50 else "New")

            # Payment methods from SOT
            sot_pms = []
            if len(_SOT_DF) > 0:
                pm_rows = _SOT_DF[(_SOT_DF["PROVIDER_NAME"].str.upper() == p["name"].upper()) & (_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live")]
                sot_pms = sorted(pm_rows["PAYMENT_METHOD_TYPE"].dropna().unique().tolist())[:10]
            pm_display = sot_pms if sot_pms else ["Card"]

            # Tick/cross helper
            def _tick(val):
                return '<span style="width:18px;height:18px;border-radius:50%;background:#F0F5DC;display:inline-flex;align-items:center;justify-content:center;font-size:11px;color:#3F5208;">&#10003;</span>' if val else '<span style="width:18px;height:18px;border-radius:50%;background:#F1F3FB;display:inline-flex;align-items:center;justify-content:center;font-size:11px;color:#D2D7EA;">&#10007;</span>'

            # Panel container
            st.markdown(f'<div style="background:#F7F8FD;border:1px solid #3E4FE0;border-top:none;border-radius:0 0 12px 12px;padding:20px 22px;margin:0 0 6px;">', unsafe_allow_html=True)

            # Health + Status bar
            h_label_bg = "#F0F5DC" if health >= 70 else "#FAF0D0" if health >= 40 else "#FAE2E5"
            h_label_color = "#3F5208" if health >= 70 else "#8A4B00" if health >= 40 else "#C4384A"
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #E9ECFC;">'
                        f'<div style="display:flex;align-items:center;gap:8px;"><span style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;">Health</span>'
                        f'<div style="width:120px;height:6px;border-radius:3px;background:#F1F3FB;"><div style="height:100%;border-radius:3px;width:{health}%;background:{h_color};"></div></div>'
                        f'<span style="font-size:14px;font-weight:700;color:{h_text};font-family:var(--font);font-variant-numeric:tabular-nums;">{health}</span></div>'
                        f'<span style="font-size:10px;font-weight:700;padding:3px 10px;border-radius:6px;background:{h_label_bg};color:{h_label_color};">{p_health_label}</span>'
                        f'<div style="margin-left:auto;display:flex;align-items:center;gap:8px;">'
                        f'<span style="font-size:10px;color:#858CA6;">Tier</span><span style="font-size:12px;font-weight:700;color:#10131C;">{tier_short}</span>'
                        f'<span style="font-size:10px;color:#858CA6;margin-left:8px;">Status</span><span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:6px;background:{s_bg};color:{s_color};">{p["status"]}</span>'
                        f'</div></div>', unsafe_allow_html=True)

            # Row 1: Contacts + Commercial
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:10px;padding:16px 18px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">Key Contacts</div>'
                            f'<div style="display:flex;flex-direction:column;gap:10px;">'
                            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:#F7F8FD;border-radius:8px;">'
                            f'<div style="width:28px;height:28px;border-radius:50%;background:#DFE3F2;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#464F6E;flex-shrink:0;">BD</div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Commercial Contact</div><div style="font-size:12px;font-weight:600;color:#10131C;">{comm_contact}</div></div></div>'
                            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:#F7F8FD;border-radius:8px;">'
                            f'<div style="width:28px;height:28px;border-radius:50%;background:#DDEFF4;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#3F5208;flex-shrink:0;">TC</div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Technical Contact</div><div style="font-size:12px;font-weight:600;color:#10131C;">{tech_contact}</div></div></div>'
                            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:#F7F8FD;border-radius:8px;">'
                            f'<div style="width:28px;height:28px;border-radius:50%;background:#FAE2E5;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#C4384A;flex-shrink:0;">ES</div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Escalation / Partner Manager</div><div style="font-size:12px;font-weight:600;color:#10131C;">{manager if manager != "—" else "Partnerships Team"}</div></div></div>'
                            f'</div></div>', unsafe_allow_html=True)
            with col_b:
                st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:10px;padding:16px 18px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">Pricing & Commercial</div>'
                            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Standard Rate</div><div style="font-size:13px;font-weight:700;color:#10131C;margin-top:1px;">{pricing}</div></div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Discounted Rate</div><div style="font-size:13px;font-weight:700;color:#3F5208;margin-top:1px;">{discount}</div></div>'
                            f'<div style="grid-column:span 2;"><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Discount Applies When</div><div style="font-size:11px;color:#3A4155;margin-top:1px;">{discount_cond}</div></div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Rev Share</div><div style="font-size:12px;font-weight:600;color:#10131C;margin-top:1px;">{revshare_status}</div></div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Merchants Live</div><div style="font-size:12px;font-weight:600;color:#10131C;margin-top:1px;">{merch_live}</div></div>'
                            f'</div></div>', unsafe_allow_html=True)

            # Row 2: Verticals + Features + Onboarding
            col_c, col_d = st.columns(2)
            with col_c:
                vert_pills = " ".join(f'<span style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:#F1F3FB;color:#3A4155;">{v.strip()}</span>' for v in verticals.split(",")) if verticals != "—" else '<span style="font-size:11px;color:#858CA6;">—</span>'
                pm_pills = " ".join(f'<span style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:#EFF1F9;color:#464F6E;">{pm}</span>' for pm in pm_display[:8])
                st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:10px;padding:16px 18px;margin-top:10px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Verticals & Payment Methods</div>'
                            f'<div style="font-size:10px;color:#858CA6;text-transform:uppercase;margin-bottom:4px;">Key Verticals</div>'
                            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">{vert_pills}</div>'
                            f'<div style="font-size:10px;color:#858CA6;text-transform:uppercase;margin-bottom:4px;">Payment Methods Supported</div>'
                            f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{pm_pills}</div>'
                            f'</div>', unsafe_allow_html=True)
            with col_d:
                st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:10px;padding:16px 18px;margin-top:10px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Integration & Onboarding</div>'
                            f'<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px;">'
                            f'<div style="display:flex;align-items:center;gap:8px;">{_tick(p.get("int_ready"))}<span style="font-size:12px;color:#10131C;">Integration Ready</span></div>'
                            f'<div style="display:flex;align-items:center;gap:8px;">{_tick(p.get("nda"))}<span style="font-size:12px;color:#10131C;">NDA Signed</span></div>'
                            f'<div style="display:flex;align-items:center;gap:8px;">{_tick(p.get("int_ready"))}<span style="font-size:12px;color:#10131C;">Latest API Integrated</span></div>'
                            f'<div style="display:flex;align-items:center;gap:8px;">{_tick(p.get("int_used"))}<span style="font-size:12px;color:#10131C;">Merchant Using Integration</span></div>'
                            f'</div>'
                            f'<div style="font-size:10px;color:#858CA6;text-transform:uppercase;margin-bottom:3px;">Onboarding Requirements</div>'
                            f'<div style="font-size:11px;color:#3A4155;line-height:1.5;">{onboarding}</div>'
                            f'</div>', unsafe_allow_html=True)

            # Merchants row (if data available)
            if merch_names and merch_names != "—":
                st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:10px;padding:12px 18px;margin-top:10px;display:flex;align-items:center;gap:12px;">'
                            f'<span style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;">Merchants</span>'
                            f'<span style="font-size:12px;color:#3A4155;">{merch_names}</span>'
                            f'<button style="margin-left:auto;background:#EFF1F9;border:0.5px solid #AAB3D8;border-radius:6px;padding:5px 12px;font-size:11px;font-weight:600;color:#464F6E;cursor:pointer;display:flex;align-items:center;gap:4px;font-family:inherit;">'
                            f'<svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="#464F6E" stroke-width="1.5" stroke-linecap="round"><path d="M5.5 1v6M3.5 5l2 2 2-2"/><path d="M2 9h7"/></svg>Download RFI/RFP</button>'
                            f'</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # No extra JS needed — st.expander handles everything
    components.html("""<script>
setTimeout(function(){
</script>""", height=0)

# ── Contacts View ──────────────────────────────────────────────────────────────
YUNO_CONTACTS = [
    {"init":"DR","bg":"rgba(84,104,245,0.2)","color":"#8B9BFF","name":"Daniela Reyes","role":"Head of Partnerships","dept":"Partnerships · Yuno","badge":"Your Lead","badge_class":"p-purple","last":"Today","rel":"Primary contact","scope":"Strategy & commercial terms"},
    {"init":"MS","bg":"rgba(84,104,245,0.2)","color":"#8B9BFF","name":"Marco Silva","role":"Partnership Manager · LATAM","dept":"Partnerships · Yuno","badge":"BD","badge_class":"p-blue","last":"1d ago","rel":"Day-to-day","scope":"Pipeline & deal support"},
    {"init":"LG","bg":"rgba(84,104,245,0.2)","color":"#8B9BFF","name":"Laura Gómez","role":"Partnership Manager · MX & COL","dept":"Partnerships · Yuno","badge":"BD","badge_class":"p-blue","last":"3d ago","rel":"Day-to-day","scope":"MX & COL opportunities"},
    {"init":"JR","bg":"rgba(0,134,168,0.2)","color":"#3FA8C4","name":"Jorge Restrepo","role":"Delivery Manager","dept":"Integrations · Yuno","badge":"Technical","badge_class":"p-teal","last":"2d ago","rel":"Integration lead","scope":"Onboarding & go-live"},
    {"init":"VP","bg":"rgba(0,134,168,0.2)","color":"#3FA8C4","name":"Valentina Perez","role":"Solutions Engineer","dept":"Integrations · Yuno","badge":"Technical","badge_class":"p-teal","last":"5d ago","rel":"Tech support","scope":"API & certification queries"},
    {"init":"AS","bg":"rgba(90,107,0,0.2)","color":"#8FA300","name":"Andrés Suárez","role":"Marketing Manager · Partners","dept":"Marketing · Yuno","badge":"Marketing","badge_class":"p-green","last":"1w ago","rel":"Co-marketing","scope":"Joint campaigns & content"},
    {"init":"CB","bg":"rgba(90,107,0,0.2)","color":"#8FA300","name":"Carolina Blanco","role":"Partner Marketing Specialist","dept":"Marketing · Yuno","badge":"Marketing","badge_class":"p-green","last":"4d ago","rel":"Co-marketing","scope":"Case studies & events"},
    {"init":"RM","bg":"rgba(47,138,31,0.2)","color":"#D08A1A","name":"Rafael Mendoza","role":"Customer Success Manager","dept":"Success · Yuno","badge":"Success","badge_class":"p-amber","last":"Today","rel":"Escalation point","scope":"Performance & health"},
    {"init":"NF","bg":"rgba(47,138,31,0.2)","color":"#D08A1A","name":"Natalia Ferro","role":"Revenue Operations","dept":"RevOps · Yuno","badge":"Ops","badge_class":"p-amber","last":"2d ago","rel":"Reporting","scope":"Invoicing & SLAs"},
]

def show_contacts():
    is_internal = st.session_state.role == "internal"

    BADGE_STYLES = {
        "p-green":  ("background:#10131C;color:#fff;", "#3F5208"),
        "p-blue":   ("background:#DFE3F2;color:#464F6E;", "#464F6E"),
        "p-amber":  ("background:#FAF0D0;color:#6E3C00;", "#6E3C00"),
        "p-teal":   ("background:#DDEFF4;color:#00697F;", "#00697F"),
        "p-purple": ("background:#3E4FE0;color:#fff;", "#3E4FE0"),
    }

    if not is_internal:
        st.markdown('<div style="font-size:22px;font-weight:700;color:#10131C;letter-spacing:-0.8px;margin-bottom:4px;">Your Yuno Team</div>'
                    '<div style="font-size:13px;color:#676E8A;margin-bottom:24px;">Your dedicated Yuno contacts across partnerships, integrations, marketing & success</div>', unsafe_allow_html=True)
        contacts_data = YUNO_CONTACTS
    else:
        st.markdown('<div style="font-size:22px;font-weight:700;color:#10131C;letter-spacing:-0.8px;margin-bottom:4px;">Key Contacts</div>'
                    '<div style="font-size:13px;color:#676E8A;margin-bottom:24px;">BD counterparts, technical leads & executive sponsors across partner organizations</div>', unsafe_allow_html=True)
        contacts_data = CONTACTS

    # ── Summary table ─────────────────────────────────────────────────────────
    header_cols = ["Name", "Role", "Department" if not is_internal else "Company", "Status", "Last Contact"]
    header_html = "".join(f'<th style="padding:10px 14px;font-size:11px;font-weight:600;color:#676E8A;text-transform:uppercase;letter-spacing:0.5px;text-align:left;border-bottom:2px solid #E2E6F4;">{h}</th>' for h in header_cols)
    rows_html = ""
    for c in contacts_data:
        badge_style = BADGE_STYLES.get(c['badge_class'], ("background:#F1F3FB;color:#4A5170;", "#4A5170"))[0]
        org = c.get('dept', '') if not is_internal else c.get('company', '')
        rows_html += f"""<tr style="border-bottom:1px solid #F1F3FB;">
  <td style="padding:12px 14px;font-size:13px;font-weight:600;color:#10131C;">{c['name']}</td>
  <td style="padding:12px 14px;font-size:13px;color:#676E8A;">{c['role']}</td>
  <td style="padding:12px 14px;font-size:13px;color:#676E8A;">{org}</td>
  <td style="padding:12px 14px;"><span style="{badge_style}font-size:11px;font-weight:600;padding:3px 12px;border-radius:20px;white-space:nowrap;">{c['badge']}</span></td>
  <td style="padding:12px 14px;font-size:13px;color:#676E8A;font-variant-numeric:tabular-nums;">{c['last']}</td>
</tr>"""
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E2E6F4;border-radius:8px;overflow:hidden;margin-bottom:28px;">
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr>{header_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

    # ── Detail cards (partner-detail style) ───────────────────────────────────
    cols_per_row = 2
    for i in range(0, len(contacts_data), cols_per_row):
        row = contacts_data[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, c in zip(cols, row):
            badge_style, badge_border = BADGE_STYLES.get(c['badge_class'], ("background:#F1F3FB;color:#4A5170;", "#4A5170"))
            org = c.get('dept', '') if not is_internal else c.get('company', '')

            if not is_internal:
                fields = [
                    ("Department", org),
                    ("Last Contact", c['last']),
                    ("Relationship", c.get('rel', '-')),
                    ("Scope", c.get('scope', '-')),
                ]
            else:
                fields = [
                    ("Company", org),
                    ("Last Contact", c['last']),
                    ("Relationship", c.get('rel', '-')),
                    ("Active Deals", c.get('deals', '-')),
                ]

            fields_html = ""
            for fi, (label, value) in enumerate(fields):
                border_b = "border-bottom:1px solid #F1F3FB;padding-bottom:12px;margin-bottom:12px;" if fi < len(fields) - 1 else ""
                fields_html += f"""<div style="{border_b}">
  <div style="font-size:12px;color:#676E8A;margin-bottom:2px;">{label}</div>
  <div style="font-size:14px;font-weight:600;color:#10131C;">{value}</div>
</div>"""

            subtitle = f"{c['role']} &middot; {org}"

            col.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
    <div>
      <div style="font-size:18px;font-weight:700;color:#10131C;letter-spacing:-0.4px;text-transform:uppercase;">{c['name']}</div>
      <div style="font-size:13px;color:#676E8A;margin-top:2px;">{subtitle}</div>
    </div>
    <span style="{badge_style}font-size:11px;font-weight:600;padding:4px 14px;border-radius:20px;white-space:nowrap;">{c['badge']}</span>
  </div>
  <div style="border:1px solid #E2E6F4;border-radius:8px;padding:20px;">
    <div style="font-size:15px;font-weight:700;color:#10131C;margin-bottom:16px;">Contact Details</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 40px;">
      {fields_html}
    </div>
    <div style="display:flex;gap:8px;margin-top:16px;border-top:1px solid #F1F3FB;padding-top:14px;">
      <button style="flex:1;padding:7px;border-radius:6px;font-size:11px;font-weight:600;background:#10131C;color:#fff;border:none;cursor:pointer;font-family:inherit;">Email</button>
      <button style="flex:1;padding:7px;border-radius:6px;font-size:11px;font-weight:600;background:#fff;color:#10131C;border:1px solid #E2E6F4;cursor:pointer;font-family:inherit;">Schedule</button>
      <button style="flex:1;padding:7px;border-radius:6px;font-size:11px;font-weight:600;background:#fff;color:#10131C;border:1px solid #E2E6F4;cursor:pointer;font-family:inherit;">{"Slack" if not is_internal else "Note"}</button>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    if is_internal:
        st.markdown("""
<div style="border:1px solid rgba(47,138,31,.22);background:rgba(47,138,31,.04);border-radius:8px;padding:16px 20px;margin-top:8px;">
  <div style="font-size:10px;font-weight:700;color:#6E3C00;letter-spacing:.8px;text-transform:uppercase;margin-bottom:12px;">Internal BD Notes — Not Visible to Partners</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:13px;"><span style="color:#676E8A;">Tom Kuehn (Adyen) — negotiating exclusivity window on MX corridor, do not share with other acquirers</span><span style="font-size:11px;font-weight:600;color:#6E3C00;">Confidential</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:13px;"><span style="color:#676E8A;">Felipe Morales (Getnet) — board approval needed above $500K. Target Jan board meeting.</span><span style="font-size:11px;font-weight:600;color:#6E3C00;">Action needed</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;font-size:13px;"><span style="color:#676E8A;">Martín Castillo (Pomelo) — exploring white-label orchestration. High strategic value for BaaS play.</span><span style="font-size:11px;font-weight:600;color:#6E3C00;">Strategic</span></div>
</div>""", unsafe_allow_html=True)

# ── Performance View ───────────────────────────────────────────────────────────
# ── Partner Health · y.uno look ────────────────────────────────────────────────
# The website's own tokens: Geist for text and Geist Mono for the small
# uppercase eyebrows, indigo #3E4FE0 as the one brand colour, lime #C7E956 as
# the highlight, black sections against white cards, hairline zinc borders,
# rounded-full pills and the diagonal indigo stripe as the accent texture.
_YW = {
    "indigo": "#3E4FE0", "indigo_dk": "#3040C8", "indigo_lt": "#6B7BFF", "tint": "#DDE6FF",
    "lime": "#C7E956", "black": "#1A1A1A", "ink2": "#52525B", "ink3": "#71717A", "ink4": "#A1A1AA",
    "line": "#E4E4E7", "wash": "#F4F4F5", "red": "#EF4444",
}
# Chart series — brand-adjacent hues in a fixed order, validated for CVD
# separation and contrast on white (dataviz validator, all checks pass).
_YW_SERIES = {"Acquirers": "#3E4FE0", "PSPs": "#7E9B0A", "APMs": "#0F8FA0",
              "Fraud": "#9A5CE6", "BaaS": "#B7822B"}
_YW_STATUS = {"good": "#7E9B0A", "warn": "#B7822B", "bad": "#EF4444"}


def _yw_css():
    """Page-scoped styles: cards, eyebrows, pills, bordered containers as cards."""
    st.markdown(f"""<style>
.yw-card {{ background:#fff;border:1px solid {_YW['line']};border-radius:12px;padding:18px 20px;font-family:var(--font); }}
.yw-eyebrow {{ font-family:var(--mono);font-size:10.5px;font-weight:400;letter-spacing:.12em;text-transform:uppercase;color:{_YW['ink3']}; }}
.yw-title {{ font-size:15px;font-weight:600;color:{_YW['black']};letter-spacing:-.015em;margin-top:3px; }}
.yw-sub {{ font-size:11.5px;color:{_YW['ink3']};margin-top:2px; }}
.yw-pill {{ display:inline-flex;align-items:center;font-size:10.5px;font-weight:500;padding:3px 10px;border-radius:999px;
           white-space:nowrap;font-family:var(--font);font-variant-numeric:tabular-nums;line-height:1.4; }}
.yw-pill.lime {{ background:{_YW['lime']};color:{_YW['black']}; }}
.yw-pill.tint {{ background:{_YW['tint']};color:{_YW['indigo_dk']}; }}
.yw-pill.wash {{ background:{_YW['wash']};color:{_YW['ink2']}; }}
.yw-pill.red  {{ background:#FEE2E2;color:#B91C1C; }}
.yw-pill.ghost {{ background:#fff;color:{_YW['ink2']};border:1px solid {_YW['line']}; }}
.yw-stripe {{ background-color:#F7F9FF;background-image:repeating-linear-gradient(-45deg,{_YW['tint']} 0,{_YW['tint']} 2px,transparent 2px,transparent 9px); }}
.yw-num {{ font-family:var(--mono);font-variant-numeric:tabular-nums; }}
/* Keyed chart containers become white Yuno cards */
.st-key-yw_tpv, .st-key-yw_mix, .st-key-yw_auth {{
  background:#fff;border:1px solid {_YW['line']};border-radius:12px;padding:14px 16px 6px;gap:0 !important; }}
</style>""", unsafe_allow_html=True)


def _yw_head(eyebrow, title, sub=""):
    return (f'<div style="margin-bottom:6px;"><div class="yw-eyebrow">{eyebrow}</div>'
            f'<div class="yw-title">{title}</div>'
            + (f'<div class="yw-sub">{sub}</div>' if sub else "") + '</div>')


def _yw_stats(stats):
    """Stat tiles the way y.uno shows numbers: mono label, black figure, lime delta."""
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        kind = {"up": "lime", "down": "red", "flat": "wash"}.get(s.get("delta_type", "flat"), "wash")
        col.markdown(
            f'<div class="yw-card" style="padding:16px 18px;">'
            f'<div class="yw-eyebrow">{s["label"]}</div>'
            f'<div style="font-size:26px;font-weight:600;color:{_YW["black"]};letter-spacing:-.03em;'
            f'line-height:1.1;margin:10px 0 10px;font-variant-numeric:tabular-nums;">{s["value"]}</div>'
            f'<span class="yw-pill {kind}">{s["delta"]}</span></div>', unsafe_allow_html=True)


def _yw_plotly(fig, height, legend=True, **axes):
    """The one chart frame: Geist, recessive grid, no chrome, legend on top."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Geist, GeistSans, -apple-system, sans-serif", color=_YW["ink3"], size=11),
        margin=dict(l=8, r=8, t=8 if not legend else 34, b=8), height=height,
        showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, font=dict(size=11, color=_YW["ink2"]),
                    bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=_YW["black"], font=dict(color="#fff", size=11, family="Geist, sans-serif"),
                        bordercolor=_YW["black"]),
    )
    base = dict(gridcolor="#F4F4F5", zerolinecolor="#E4E4E7", linecolor="rgba(0,0,0,0)",
                tickfont=dict(color=_YW["ink3"]))
    fig.update_xaxes(**{**base, **axes.get("x", {})})
    fig.update_yaxes(**{**base, **axes.get("y", {})})
    return fig


def show_performance():
    is_internal = st.session_state.role == "internal"
    _ext = external_account()
    if _ext is not None:
        return show_own_health(_ext)
    if not is_internal:
        return _ext_locked("Partner Health needs your record",
                           "Sign in with your company email so we can show your own numbers.")
    _yw_css()

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(hero(
        "Partner Health", eyebrow="Performance",
        subtitle="Performance analytics across partners and merchants.",
        badge="Live data" if is_internal else None),
        unsafe_allow_html=True)

    # ── View toggle — a y.uno pill switch ─────────────────────────────────────
    perf_view = st.session_state.get("perf_view", "partners")
    vc1, vc2, _ = st.columns([1.2, 1.2, 3])
    with vc1:
        if st.button("Partnership Performance", key="pv_partners", use_container_width=True):
            st.session_state["perf_view"] = "partners"
            st.rerun()
    with vc2:
        if st.button("Merchant Performance", key="pv_merchants", use_container_width=True):
            st.session_state["perf_view"] = "merchants"
            st.rerun()

    def _pill(active):
        return ("background:{ink} !important;border:1px solid {ink} !important;color:#fff !important;"
                if active else
                "background:#fff !important;border:1px solid {line} !important;color:{ink3} !important;"
                ).format(ink=_YW["black"], line=_YW["line"], ink3=_YW["ink3"]) + \
               "border-radius:999px !important;padding:8px 16px !important;font-size:12.5px !important;" \
               "font-weight:500 !important;box-shadow:none !important;min-height:36px !important;" \
               "font-family:var(--font) !important;letter-spacing:-.005em !important;"
    components.html(f"""<script>
setTimeout(function(){{
  var doc = window.parent.document;
  doc.querySelectorAll('button').forEach(function(btn){{
    var t = btn.textContent.trim();
    if(t==='Partnership Performance') btn.style.cssText='{_pill(perf_view=="partners")}';
    if(t==='Merchant Performance')    btn.style.cssText='{_pill(perf_view=="merchants")}';
  }});
}},150);
</script>""", height=0)

    # ══════════════════════════════════════════════════════════════════════════
    # MERCHANT PERFORMANCE VIEW
    # ══════════════════════════════════════════════════════════════════════════
    if perf_view == "merchants":
        _MERCH_DATA = [
            {"name":"Uber","tpv":"$5.9M","txns":"323K","ar":93.4,"providers":["Adyen","dLocal","Stripe"],"country":"MX","missing":["Smart retries","PIX in BR"],"upsell":"Add Cielo for local acquiring in Brazil — +3% auth rate"},
            {"name":"Netflix","tpv":"$4.8M","txns":"306K","ar":95.6,"providers":["Stripe","Adyen","dLocal"],"country":"US","missing":["Installments in LATAM"],"upsell":"Enable parcelamento via Cielo/PagBank — unlock +20% AOV in Brazil"},
            {"name":"Spotify","tpv":"$4.2M","txns":"421K","ar":94.8,"providers":["Adyen","Ebanx","dLocal"],"country":"BR","missing":["OXXO in MX","Nequi in CO"],"upsell":"Add Kushki for Colombia APMs — reduce decline rate by 4%"},
            {"name":"Rappi","tpv":"$8.4M","txns":"259K","ar":91.2,"providers":["Adyen","Kushki","MercadoPago"],"country":"CO","missing":["Fraud layer","3DS optimization"],"upsell":"Add SEON fraud screening — reduce chargebacks by 40%"},
            {"name":"MercadoLibre","tpv":"$7.3M","txns":"62K","ar":88.7,"providers":["MercadoPago","Adyen","Cielo"],"country":"AR","missing":["Network tokens","Smart routing"],"upsell":"Enable network tokens via Adyen — +2% auth rate on recurring"},
            {"name":"Falabella","tpv":"$3.1M","txns":"36K","ar":87.1,"providers":["Transbank","Kushki","Adyen"],"country":"CL","missing":["Installments","Webpay Plus"],"upsell":"Upgrade Transbank to Webpay Plus — unlock 6/12 month installments"},
            {"name":"iFood","tpv":"$2.9M","txns":"103K","ar":91.8,"providers":["Cielo","PagBank","Stone"],"country":"BR","missing":["Apple Pay","Google Pay"],"upsell":"Add Apple Pay/Google Pay — +8% mobile conversion"},
            {"name":"Despegar","tpv":"$3.8M","txns":"12K","ar":82.3,"providers":["Cybersource","Adyen","dLocal"],"country":"AR","missing":["Airline data","3DS exemptions"],"upsell":"Enable airline data passthrough — +5% auth rate on high-value bookings"},
        ]

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        _yw_stats([
            {"label":"Live merchants","value":"12","delta":"+2 this quarter","delta_type":"up"},
            {"label":"Total TPV","value":"$40.4M","delta":"+28% QoQ","delta_type":"up"},
            {"label":"Avg auth rate","value":"90.6%","delta":"+1.4 pts","delta_type":"up"},
            {"label":"Cross-sell opps","value":"8","delta":"Actionable now","delta_type":"flat"},
        ])

        st.markdown(f'<div style="margin:22px 0 10px;">{_yw_head("Merchant portfolio", "Partners & performance", "Each merchant, the rails it runs on, and the next thing to sell it.")}</div>',
                    unsafe_allow_html=True)

        for m in _MERCH_DATA:
            ar_tone = "good" if m["ar"] >= 90 else "warn" if m["ar"] >= 85 else "bad"
            providers_pills = " ".join(f'<span class="yw-pill ghost">{p}</span>' for p in m["providers"])
            missing_pills = " ".join(f'<span class="yw-pill tint">{f}</span>' for f in m["missing"])

            with st.expander(f"{m['name']}  ·  {m['tpv']} TPV  ·  {m['ar']}% auth  ·  {m['country']}", expanded=False):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(
                        f'<div class="yw-card" style="height:100%;">'
                        f'<div class="yw-eyebrow" style="margin-bottom:12px;">Performance</div>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 8px;">'
                        + "".join(
                            f'<div><div class="yw-eyebrow" style="font-size:9.5px;">{k}</div>'
                            f'<div style="font-size:17px;font-weight:600;color:{c};letter-spacing:-.02em;'
                            f'margin-top:3px;font-variant-numeric:tabular-nums;">{v}</div></div>'
                            for k, v, c in [("TPV / mo", m["tpv"], _YW["black"]), ("Txns / mo", m["txns"], _YW["black"]),
                                            ("Auth rate", f'{m["ar"]}%', _YW_STATUS[ar_tone]), ("Country", m["country"], _YW["black"])])
                        + f'</div><div style="margin-top:14px;"><div class="yw-eyebrow" style="font-size:9.5px;margin-bottom:6px;">Live partners</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{providers_pills}</div></div></div>',
                        unsafe_allow_html=True)
                with col_m2:
                    st.markdown(
                        f'<div class="yw-card yw-stripe" style="border-color:rgba(62,79,224,.25);height:100%;">'
                        f'<div class="yw-eyebrow" style="color:{_YW["indigo"]};margin-bottom:12px;">Optimization opportunities</div>'
                        f'<div class="yw-eyebrow" style="font-size:9.5px;margin-bottom:6px;">Missing features</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px;">{missing_pills}</div>'
                        f'<div class="yw-eyebrow" style="font-size:9.5px;margin-bottom:6px;">Recommended action</div>'
                        f'<div style="font-size:13px;color:{_YW["black"]};line-height:1.55;font-weight:500;">{m["upsell"]}</div>'
                        f'</div>', unsafe_allow_html=True)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # PARTNERSHIP PERFORMANCE VIEW
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    _yw_stats([
        {"label":"Total TPV · live partners","value":"$2.4B","delta":"+34% YoY","delta_type":"up"},
        {"label":"Transactions / mo","value":"142M","delta":"+22% MoM","delta_type":"up"},
        {"label":"Auth rate · avg","value":"89.4%","delta":"+1.2 pts","delta_type":"up"},
        {"label":"Partner revenue","value":"$18.6M","delta":"+28% QoQ","delta_type":"up"},
        {"label":"NPS · partners","value":"72","delta":"+8 pts","delta_type":"up"},
    ])
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    col_tpv, col_mix = st.columns([2.2, 1])
    months = ["May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    datasets = [("Acquirers",[820,880,910,950,1020,1100,1180,1240]),
                ("PSPs",[420,460,490,530,580,640,700,780]),
                ("APMs",[180,200,230,260,300,340,390,440]),
                ("Fraud",[60,70,80,90,100,115,130,150]),
                ("BaaS",[0,0,0,0,10,25,45,80])]

    with col_tpv:
        with st.container(key="yw_tpv"):
            st.markdown(_yw_head("Monthly TPV", "Volume by partner category", "USD millions · stacked"),
                        unsafe_allow_html=True)
            fig = go.Figure()
            for name, data in datasets:
                fig.add_trace(go.Bar(name=name, x=months, y=data, marker_color=_YW_SERIES[name],
                                     marker_line_color="#ffffff", marker_line_width=2,
                                     hovertemplate=f"{name} · %{{x}}: $%{{y}}M<extra></extra>"))
            fig.update_layout(barmode="stack", bargap=0.42)
            _yw_plotly(fig, 270, y=dict(ticksuffix="M"), x=dict(showgrid=False))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_mix:
        with st.container(key="yw_mix"):
            st.markdown(_yw_head("TPV mix", "Share by category", "Last month"), unsafe_allow_html=True)
            labels = [d[0] for d in datasets]
            values = [38, 31, 19, 8, 4]
            fig2 = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.72, sort=False, direction="clockwise",
                marker_colors=[_YW_SERIES[l] for l in labels],
                marker_line_color="#ffffff", marker_line_width=2,
                textinfo="none", hovertemplate="%{label}: %{value}%<extra></extra>",
            ))
            fig2.add_annotation(text=f'<b>{values[0]}%</b><br><span style="font-size:10px">{labels[0]}</span>',
                                x=0.5, y=0.5, showarrow=False,
                                font=dict(size=18, color=_YW["black"], family="Geist, sans-serif"))
            _yw_plotly(fig2, 270, legend=True)
            fig2.update_layout(legend=dict(orientation="v", y=0.5, x=1.02, xanchor="left"),
                               margin=dict(l=0, r=90, t=8, b=8))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    col_auth, col_health = st.columns(2)

    with col_auth:
        with st.container(key="yw_auth"):
            st.markdown(_yw_head("Auth rate", "By partner · top 8", "Approval rate on live volume, last 30 days"),
                        unsafe_allow_html=True)
            partners_list = list(_PH_AUTH)
            rates = list(_PH_AUTH.values())
            tones = ["good" if r >= 90 else "warn" if r >= 87 else "bad" for r in rates]
            fig3 = go.Figure(go.Bar(
                x=rates, y=partners_list, orientation="h",
                marker_color=[_YW_STATUS[t] for t in tones], marker=dict(cornerradius=4),
                text=[f"{r}%" for r in rates], textposition="outside",
                textfont=dict(size=11, color=_YW["ink2"], family="Geist Mono, monospace"),
                hovertemplate="%{y}: %{x}%<extra></extra>", width=0.55))
            _yw_plotly(fig3, 290, legend=False,
                       x=dict(range=[80, 104], ticksuffix="%", dtick=5),
                       y=dict(autorange="reversed", showgrid=False, tickfont=dict(color=_YW["black"], size=11.5)))
            fig3.update_layout(margin=dict(l=8, r=44, t=8, b=8))
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                '<div style="display:flex;gap:6px;flex-wrap:wrap;margin:-4px 0 8px;">'
                + "".join(f'<span class="yw-pill wash"><span style="width:7px;height:7px;border-radius:50%;'
                          f'background:{_YW_STATUS[t]};margin-right:6px;"></span>{lbl}</span>'
                          for t, lbl in [("good", "≥ 90% healthy"), ("warn", "87–90% watch"), ("bad", "< 87% at risk")])
                + '</div>', unsafe_allow_html=True)

    with col_health:
        rows = [(p, *v) for p, v in _PH_SCORE.items()]
        def _health(h):
            k = "lime" if h >= 85 else "tint" if h >= 75 else "wash"
            return f'<span class="yw-pill {k}">{h}</span>'
        def _issues(n):
            c = _YW["ink4"] if n == 0 else _YW["black"] if n < 3 else _YW["red"]
            return f'<span class="yw-num" style="color:{c};font-weight:{500 if n else 400};">{n}</span>'
        th = (f'style="text-align:left;padding:8px 8px;font-family:var(--mono);font-size:9.5px;font-weight:400;'
              f'letter-spacing:.12em;text-transform:uppercase;color:{_YW["ink3"]};border-bottom:1px solid {_YW["line"]};"')
        body = "".join(
            f'<tr>'
            f'<td style="padding:9px 8px;font-weight:500;color:{_YW["black"]};border-bottom:1px solid {_YW["wash"]};">{p}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid {_YW["wash"]};">{_health(h)}</td>'
            f'<td class="yw-num" style="padding:9px 8px;border-bottom:1px solid {_YW["wash"]};'
            f'color:{_YW["red"] if t.startswith("−") else _YW["black"]};">{t}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid {_YW["wash"]};">{_issues(n)}</td></tr>'
            for p, h, t, n in rows)
        st.markdown(
            f'<div class="yw-card" style="padding:14px 16px 10px;">{_yw_head("Scorecard", "Partner health", "Integration quality · engagement · growth")}'
            f'<table style="width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px;">'
            f'<thead><tr><th {th}>Partner</th><th {th}>Health</th><th {th}>TPV trend</th><th {th}>Issues</th></tr></thead>'
            f'<tbody>{body}</tbody></table>'
            f'<div style="display:flex;gap:6px;margin-top:12px;flex-wrap:wrap;">'
            f'<span class="yw-pill lime">85+ strong</span><span class="yw-pill tint">75–84 stable</span>'
            f'<span class="yw-pill wash">&lt; 75 needs attention</span></div></div>',
            unsafe_allow_html=True)

    if is_internal:
        # The site's black section: lime eyebrow, white figures, hairline rows.
        items = [("Blended take rate (all live partners)", "0.048%", None),
                 ("Adyen contract renewal date", "Mar 2025 · auto-renew flag on", None),
                 ("Nuvei performance clause risk", "Below SLA — escalate", "red"),
                 ("BaaS vertical projected ARR (12 mo)", "$2.1M if 4 deals close", "lime")]
        rows_html = "".join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;gap:16px;padding:10px 0;'
            f'border-top:1px solid rgba(255,255,255,.10);font-size:12.5px;">'
            f'<span style="color:{_YW["ink4"]};">{k}</span>'
            + (f'<span class="yw-pill {tone}">{v}</span>' if tone else
               f'<span class="yw-num" style="color:#fff;font-weight:500;">{v}</span>')
            + '</div>' for k, v, tone in items)
        st.markdown(
            f'<div style="background:{_YW["black"]};border-radius:12px;padding:20px 22px;margin-top:14px;font-family:var(--font);">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span class="yw-eyebrow" style="color:{_YW["lime"]};">Internal · revenue intelligence</span>'
            f'<span class="yw-pill" style="background:rgba(255,255,255,.08);color:{_YW["ink4"]};">Yuno only</span></div>'
            f'{rows_html}</div>', unsafe_allow_html=True)

# ── What Yuno has in a market ──────────────────────────────────────────────────
# Live providers and payment methods per country come straight from
# source_of_truth.xlsx; the match against a market's published mix is by name,
# and says so on screen.
_MIX_FAMILIES = {
    "wallet": {"APPLE_PAY", "GOOGLE_PAY", "SAMSUNG_PAY", "PAYPAL", "MERCADO_PAGO", "GRABPAY", "GOPAY", "OVO",
               "DANA", "GCASH", "MAYA", "TRUEMONEY", "LINE_PAY", "KAKAO_PAY", "NAVER_PAY", "TOUCH_N_GO", "YAPE",
               "PLIN", "NEQUI", "DAVIPLATA", "PICPAY", "MOMO", "ZALOPAY", "VNPAY", "TWINT", "MOBILEPAY", "VIPPS",
               "SWISH", "BLIK", "BIZUM", "SATISPAY", "PAYME", "ALIPAY", "ALIPAY+", "WECHAT_PAY", "SKRILL",
               "NETELLER", "ASTROPAY", "MUCH_BETTER", "PAYMAYA", "OKTO", "TIGO_MONEY", "M_PESA", "MPESA",
               "JAZZ_CASH", "EASYPAISA", "MAYA_WALLET", "SHOPEEPAY", "WALLETPH"},
    "bank": {"TRANSFER", "SEPA", "PSE", "SPEI", "PIX", "IDEAL", "EPS", "BANCONTACT", "SOFORT", "TRUSTLY",
             "OPEN_BANKING", "BANK", "FPX", "PROMPTPAY", "DUITNOW", "UPI", "INSTAPAY", "PAYNOW", "MULTIBANCO",
             "MB_WAY", "BLIK", "PAY_BY_BANK", "A2A", "KHIPU", "WEBPAY", "SINPE", "DEBIN", "CODI", "GIROPAY",
             "PRZELEWY", "P24", "FASTER", "ACH", "INTERAC", "POLI", "PAYID", "PAYTO", "FPS", "VIETQR", "QRIS"},
    "cash": {"OXXO", "BOLETO", "EFECTY", "BALOTO", "PAGO_EFECTIVO", "RAPIPAGO", "PAGO_FACIL", "CASH", "7ELEVEN",
             "SEVEN_ELEVEN", "CONVENIENCE", "ABITAB", "REDPAGOS", "FAWRY", "VOUCHER", "PAYSAFECARD", "CEBUANA",
             "SENCILLITO", "SERVIPAG", "PAGOEFECTIVO", "KONBINI", "CODI"},
    "bnpl": {"KLARNA", "AFTERPAY", "CLEARPAY", "ZIP", "AFFIRM", "TABBY", "TAMARA", "ADDI", "KUESKI", "SCALAPAY",
             "ATOME", "RIVERTY", "WALLEY", "BILLIE", "BNPL", "INSTALLMENT", "CUOTAS", "PAGALEVE", "ADDI"},
    "crypto": {"CRYPTO", "BIT_PAY", "BITPAY", "COINBASE", "STABLECOIN", "USDC", "BINANCE"},
}
_MIX_GENERIC = {"wallet": "wallet", "wallets": "wallet", "mobile": "wallet", "e-wallets": "wallet",
                "transfer": "bank", "banking": "bank", "a2a": "bank", "instant": "bank", "ach": "bank",
                "cash": "cash", "voucher": "cash", "convenience": "cash", "otc": "cash", "delivery": "cash",
                "bnpl": "bnpl", "invoice": "bnpl", "installments": "bnpl",
                "crypto": "crypto", "stablecoin": "crypto"}


def _mix_match(method, types):
    """Which of Yuno's live payment-method types answer this market method.
    A named match (Swish, PIX, GCash) wins; the family match (any wallet, any
    bank transfer) is only the fallback for generic mix labels."""
    name = method.lower()
    if "card" in name and "cash" not in name:
        return sorted(t for t in types if t == "CARD" or t.endswith("_CARD"))
    words = [w for w in _re.split(r"[^a-z0-9+]+", name) if w]
    toks = [w for w in words if len(w) >= 3 and w not in
            ("the", "and", "with", "via", "local", "national", "bank", "digital", "online", "pay",
             "payment", "cash", "mobile", "wallet", "wallets", "transfer", "instant", "other")]
    hits = set()
    for t in types:
        tw = t.lower().replace("_", " ").replace("-", " ").split()
        tflat = "".join(tw)
        for tok in toks:
            if tok in tw or (len(tok) >= 5 and tok in tflat):
                hits.add(t)
    if hits:
        return sorted(hits)
    for w in words:
        fam = _MIX_GENERIC.get(w)
        if fam:
            fam_set = _MIX_FAMILIES[fam]
            wallets = _MIX_FAMILIES["wallet"]
            hits.update(t for t in types
                        if (t in fam_set or any(f in t for f in fam_set if len(f) >= 4))
                        and not (fam == "cash" and t in wallets))
    return sorted(hits)


@st.cache_data(show_spinner=False)
def yuno_market_coverage(market):
    """What Yuno can already offer a merchant in this market."""
    iso = market_iso(market)
    df = _SOT_DF
    if len(df) == 0:
        return None
    live = df[(df["Live/NonLive Partner/Contract signed"] == "Live") & (df["COUNTRY_ISO"] == iso)]
    if live.empty:
        return {"iso": iso, "providers": [], "by_cat": {}, "types": [], "mix": [], "covered": 0, "n_types": 0}
    types = sorted(t for t in live["PAYMENT_METHOD_TYPE"].dropna().unique().tolist())
    by_cat = {}
    for cat, grp in live.groupby("PROVIDER_CATEGORY"):
        by_cat[str(cat).replace("AGREGATOR", "Aggregator").title()] = grp["PROVIDER_NAME"].nunique()
    prov = (live.groupby("PROVIDER_NAME")["PAYMENT_METHOD_TYPE"].nunique()
            .sort_values(ascending=False))
    providers = [{"name": n.replace("_", " ").title(), "methods": int(k)} for n, k in prov.items()]
    mix, covered = [], 0
    for method, share in _MARKET_PROFILES.get(market, {}).get("payment_methods", []):
        if method.strip().lower() in ("other", "others"):
            continue
        via = _mix_match(method, types)
        n_prov = int(live[live["PAYMENT_METHOD_TYPE"].isin(via)]["PROVIDER_NAME"].nunique()) if via else 0
        if via:
            covered += share
        mix.append({"method": method, "share": share, "live": bool(via), "types": via, "providers": n_prov})
    return {"iso": iso, "providers": providers, "by_cat": by_cat, "types": types, "n_types": len(types),
            "mix": mix, "covered": covered}


def _yuno_here(name, compact=False):
    """The block that turns market intel into a sales conversation: what Yuno
    already has live in this market, and which of its rails are still gaps."""
    cov = yuno_market_coverage(name)
    if cov is None:
        return
    n_prov = len(cov["providers"])
    if not n_prov:
        st.markdown(
            f'<div style="background:#FFF8EA;border:1px solid rgba(179,116,0,.28);border-radius:12px;'
            f'padding:13px 16px;margin-bottom:10px;font-size:12px;color:#7A4E00;line-height:1.6;">'
            f'<b>Yuno is not live in {name} yet.</b> No connector in source_of_truth.xlsx carries '
            f'{cov["iso"]}. Route through a regional or global acquirer, or treat it as a partner gap.</div>',
            unsafe_allow_html=True)
        return
    cats = " · ".join(f"{v} {k.lower()}{'s' if v != 1 else ''}" for k, v in sorted(cov["by_cat"].items(), key=lambda kv: -kv[1]))
    chips = "".join(
        f'<span style="font-size:11px;font-weight:600;color:#10131C;background:#fff;border:1px solid #D5D9E8;'
        f'padding:3px 9px;border-radius:999px;white-space:nowrap;">{p["name"]}'
        f'<span style="color:#858CA6;font-weight:500;"> · {p["methods"]}</span></span>'
        for p in cov["providers"][:8 if compact else 14])
    more = n_prov - (8 if compact else 14)
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-top:1px solid rgba(62,79,224,.10);font-size:11.5px;">'
        f'<span style="width:14px;font-weight:700;color:{"#2F8A1F" if m["live"] else "#B3261E"};">{"✓" if m["live"] else "✗"}</span>'
        f'<span style="flex:1;color:#10131C;">{m["method"]}</span>'
        f'<span style="color:#858CA6;font-variant-numeric:tabular-nums;">{m["share"]}% of mix</span>'
        f'<span style="min-width:150px;text-align:right;color:{"#2F8A1F" if m["live"] else "#B3261E"};">'
        + (f'live via {m["providers"]} provider{"s" if m["providers"] != 1 else ""}' if m["live"] else "gap — not on Yuno rails")
        + '</span></div>'
        for m in cov["mix"])
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#EEF0FF,#F7F8FF);border:1px solid rgba(62,79,224,.22);'
        f'border-left:3px solid #3E4FE0;border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
        f'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">'
        f'<span style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#3E4FE0;">What Yuno has here</span>'
        f'<span style="font-size:11.5px;color:#4A5170;">{n_prov} live providers · {cov["n_types"]} payment methods · {cats}</span>'
        f'<span style="margin-left:auto;font-size:12.5px;font-weight:700;color:#10131C;">{cov["covered"]}%'
        f'<span style="font-weight:500;color:#676E8A;"> of the market mix live via Yuno</span></span></div>'
        f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin:9px 0 8px;">{chips}'
        + (f'<span style="font-size:11px;color:#858CA6;padding:3px 4px;">+{more} more</span>' if more > 0 else "")
        + f'</div>{rows}'
        f'<div style="font-size:10px;color:#9AA0B4;margin-top:7px;">Live connectors from source_of_truth.xlsx · '
        f'mix matched to Yuno method types by name</div></div>', unsafe_allow_html=True)


def _profile_card(name, c, compact=False):
    fig = go.Figure(go.Bar(
        x=[pm[1] for pm in c["payment_methods"]],
        y=[pm[0] for pm in c["payment_methods"]],
        orientation="h",
        marker_color=["#3E4FE0", "#8B9BFF", "#8B9BFF", "#B9C2FF", "#D6DCFA", "#E9ECFC"][:len(c["payment_methods"])],
        text=[f"{pm[1]}%" for pm in c["payment_methods"]], textposition="outside",
    ))
    fig.update_layout(
        height=190 if compact else 220, margin=dict(l=0, r=40, t=6, b=6),
        xaxis=dict(range=[0, 80], showgrid=True, gridcolor="rgba(0,0,0,0.05)", title=None),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(size=10.5),
    )
    region = _MARKET_REGION.get(name, "")
    st.markdown(f'''<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:12px;padding:16px 20px;margin-bottom:10px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:24px;">{c["flag"]}</span>
    <div style="flex:1;">
      <div style="font-size:17px;font-weight:700;color:#10131C;letter-spacing:-0.4px;">{name}
        <span style="font-size:10px;font-weight:700;color:#3E4FE0;background:#E9ECFC;padding:2px 7px;border-radius:5px;margin-left:6px;vertical-align:2px;">{region}</span></div>
      <div style="font-size:11px;color:#858CA6;">Population {c["population"]} &nbsp;·&nbsp; GDP {c["gdp"]} &nbsp;·&nbsp; eCommerce {c["ecom_size"]}</div>
    </div>
  </div>
  <div style="font-size:10.5px;font-weight:600;color:#3E4FE0;margin-top:8px;">{c["instore_online"]}</div>
</div>''', unsafe_allow_html=True)
    _yuno_here(name, compact)
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#858CA6;margin:2px 0 -6px;">Payment method mix</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                    key=f"mix_{name}")
    for icon, title, key in [("🏦", "Top acquirers / PSPs", "top_acquirers"),
                             ("📋", "Regulatory highlights", "regulatory"),
                             ("⏱", "Settlement times", "settlement"),
                             ("💱", "FX considerations", "fx")]:
        st.markdown(f'''<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:10px;padding:13px 15px;margin-bottom:9px;">
  <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#858CA6;margin-bottom:6px;">{icon} {title}</div>
  <div style="font-size:12px;color:#10131C;line-height:1.65;">{c[key]}</div>
</div>''', unsafe_allow_html=True)


def _market_profiles_tab(countries):
    """Every market, filterable by region, several at once side by side."""
    regions = ["All"] + [r for r in _REGION_ORDER if any(_MARKET_REGION.get(m) == r for m in countries)]
    region = st.pills("Region", regions, default="All", key="mi_region",
                      label_visibility="collapsed") or "All"
    pool = [m for m in countries if region == "All" or _MARKET_REGION.get(m) == region]
    pool.sort(key=lambda m: (_REGION_ORDER.index(_MARKET_REGION.get(m, "APAC")), m))
    prev = [m for m in st.session_state.get("mi_markets", []) if m in pool]
    picked = st.multiselect("Markets", pool, default=prev or pool[:1], key=f"mi_markets_{region}",
                            format_func=lambda m: f'{countries[m].get("flag", "")} {m}',
                            placeholder="Add a market — pick several to compare",
                            label_visibility="collapsed")
    st.session_state.mi_markets = picked
    st.markdown(f'<div style="font-size:11px;color:#858CA6;margin:-4px 0 12px;">'
                f'{len(countries)} markets profiled across {len(regions)-1} regions · '
                f'{len(picked)} selected · figures are desk research, indicative</div>',
                unsafe_allow_html=True)
    if not picked:
        st.markdown('<div style="background:#fff;border:1px dashed #D5D9E8;border-radius:12px;padding:24px;'
                    'text-align:center;font-size:13px;color:#676E8A;">Pick at least one market.</div>',
                    unsafe_allow_html=True)
        return

    # ── side-by-side when comparing ──────────────────────────────────────────
    if len(picked) > 1:
        def _yl(c, m):
            cov = yuno_market_coverage(m) or {}
            n = len(cov.get("providers", []))
            return (f'<b style="color:#3E4FE0;">{n} live providers</b> · {cov.get("n_types", 0)} methods · '
                    f'{cov.get("covered", 0)}% of mix' if n else '<span style="color:#B3261E;">not live yet</span>')
        rows = [("Yuno live here", _yl),
                ("Region", lambda c, m: _MARKET_REGION.get(m, "—")),
                ("Population", lambda c, m: c["population"]),
                ("GDP", lambda c, m: c["gdp"]),
                ("eCommerce", lambda c, m: c["ecom_size"]),
                ("Leading method", lambda c, m: f'{c["payment_methods"][0][0]} · {c["payment_methods"][0][1]}%'),
                ("Online / in-store", lambda c, m: c["instore_online"].split(".")[0]),
                ("Settlement", lambda c, m: c["settlement"]),
                ("FX", lambda c, m: c["fx"].split(".")[0] + ".")]
        head = "".join(f'<th style="text-align:left;padding:10px 12px;font-size:12.5px;color:#10131C;'
                       f'border-bottom:1px solid #E4E6F0;white-space:nowrap;">{countries[m]["flag"]} {m}</th>'
                       for m in picked)
        body = "".join(
            f'<tr><td style="padding:9px 12px;font-size:10px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:#858CA6;border-bottom:1px solid #F0F1F6;white-space:nowrap;">{lbl}</td>'
            + "".join(f'<td style="padding:9px 12px;font-size:12px;color:#10131C;border-bottom:1px solid #F0F1F6;'
                      f'vertical-align:top;min-width:180px;">{fn(countries[m], m)}</td>' for m in picked)
            + '</tr>' for lbl, fn in rows)
        st.markdown(
            f'<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);'
            f'border-radius:12px;padding:6px 8px;margin-bottom:14px;overflow-x:auto;">'
            f'<table style="border-collapse:collapse;width:100%;"><thead><tr>'
            f'<th style="padding:10px 12px;border-bottom:1px solid #E4E6F0;"></th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>', unsafe_allow_html=True)

    per_row = 1 if len(picked) == 1 else 2 if len(picked) < 5 else 3
    for i in range(0, len(picked), per_row):
        cols = st.columns(per_row)
        for c, m in zip(cols, picked[i:i + per_row]):
            with c:
                _profile_card(m, countries[m], compact=per_row > 1)


# ── Insights View ──────────────────────────────────────────────────────────────
def show_insights():
    is_internal = st.session_state.role == "internal"
    st.markdown(hero(
        "Global Market Intel", eyebrow="Intelligence",
        subtitle="Payment landscape insights across key markets worldwide."),
        unsafe_allow_html=True)

    stat_row([
        {"label":"Markets Covered","value":f"{len(_MARKET_PROFILES)}","delta":"LATAM · North America · Europe · Nordics · MENA · Africa · APAC","delta_type":"flat","val_color":"#8B9BFF"},
        {"label":"Payment Methods Tracked","value":"300+","delta":"Cards, wallets, A2A, BNPL, crypto","delta_type":"flat"},
        {"label":"Avg. Approval Rate (Global)","value":"89.2%","delta":"↑ 1.4pp vs prior year","delta_type":"up"},
        {"label":"Coverage Source","value":"Live","delta":"Yuno connector data · profiles are desk research","delta_type":"flat","val_color":"#5A7A00"},
    ])

    tab_options = ["Country Profiles","Payment Trends","Regulatory Updates","Market News"]
    tab = nav_radio("insights_tab", tab_options, "insight_tab_radio")

    # ── Country Profiles Data ─────────────────────────────────────────────────
    _COUNTRIES = _MARKET_PROFILES

    if tab == "Country Profiles":
        _market_profiles_tab(_COUNTRIES)

    elif tab == "Payment Trends":
        _TRENDS = [
            {
                "icon":"⚡","title":"Rise of Account-to-Account (A2A) Instant Payments",
                "body":"PIX (Brazil) now processes 4B+ monthly transactions. UPI (India) exceeds 15B/month. FPS (UK) and AANI (UAE) expanding merchant acceptance. A2A payments offer lower costs (0-0.5% vs 1.5-3% for cards), instant settlement, and zero chargeback risk. Projected to capture 25% of global eCommerce payments by 2028.",
                "stats":"PIX: 4B txns/mo · UPI: 15B txns/mo · FPS: 400M txns/mo",
                "tag":"Instant Payments","tag_color":"#48610A","tag_bg":"#F0F5DC",
            },
            {
                "icon":"🛒","title":"BNPL Adoption Varies Sharply by Region",
                "body":"BNPL represents ~5% of global eCommerce but adoption varies widely. Nordic countries lead at 12-15%, followed by Australia (10%), UK (8%), and Germany (7% via invoice model). In MENA, Tamara and Tabby are growing 80% YoY. LATAM adoption is 3-4% but growing fast. Regulatory scrutiny increasing globally — UK and EU introducing BNPL-specific frameworks.",
                "stats":"Global BNPL: $350B GMV · MENA growth: 80% YoY · EU regulation pending",
                "tag":"BNPL","tag_color":"#2F3FC4","tag_bg":"#E9ECFC",
            },
            {
                "icon":"🌐","title":"Cross-Border Payment Costs Declining",
                "body":"Average cost of sending $200 cross-border has dropped from 6.3% (2020) to 4.1% (2026). Swift GPI now delivers 50% of payments in under 30 minutes. Visa Direct and Mastercard Send enabling real-time cross-border. Wise, Airwallex, and Nium offering 0.5-1.5% FX margins vs 2-4% from traditional banks. G20 target of 3% average cost by 2027 on track.",
                "stats":"Avg cost: 4.1% (down from 6.3%) · Swift GPI: 50% <30min · G20 target: 3%",
                "tag":"Cross-Border","tag_color":"#00697F","tag_bg":"#DDEFF4",
            },
            {
                "icon":"📱","title":"Mobile Wallet Penetration Accelerating",
                "body":"Global mobile wallet users projected at 5.2B by 2027. In APAC, wallets already account for 60%+ of eCommerce payments (Alipay, WeChat Pay, GCash, GrabPay). In Africa, M-Pesa and MTN Mobile Money process $1.2B daily. Apple Pay and Google Pay growing in developed markets. Super-app wallets (Grab, GoTo, Rappi) blurring lines between payments and commerce.",
                "stats":"5.2B wallet users by 2027 · APAC: 60%+ eCom share · Africa: $1.2B/day",
                "tag":"Mobile Wallets","tag_color":"#C24E00","tag_bg":"#FDF8E8",
            },
            {
                "icon":"₿","title":"Crypto Payment Adoption in Emerging Markets",
                "body":"Stablecoin transaction volume surpassed $10T in 2025. USDT dominates in LATAM, Africa, and Southeast Asia as a remittance and savings tool. Merchants in Argentina, Nigeria, and Turkey increasingly accepting stablecoins to hedge local currency volatility. Stripe and PayPal now support USDC settlements. CBDCs progressing: eNaira (live), Digital Real (pilot), Digital Rupee (pilot).",
                "stats":"Stablecoin vol: $10T+ (2025) · eNaira: live · Digital Real: pilot phase",
                "tag":"Crypto/Stablecoins","tag_color":"#B36200","tag_bg":"#FAF0D0",
            },
            {
                "icon":"📶","title":"Contactless & Tap-to-Phone In-Store Growth",
                "body":"Contactless penetration exceeds 75% of in-store card transactions in Europe and MENA. Tap-to-phone (SoftPOS) eliminating need for dedicated terminals — Stripe Terminal, Adyen Tap to Pay, and Square enabling any smartphone as a POS. In-store/online convergence accelerating via unified commerce platforms. Apple Tap to Pay expanding to 15+ markets.",
                "stats":"EU contactless: 75%+ · Tap-to-phone: 15+ markets · SoftPOS reducing terminal costs by 60%",
                "tag":"In-Store Innovation","tag_color":"#C4187F","tag_bg":"#F7DFEC",
            },
        ]

        for t in _TRENDS:
            st.markdown(f'''<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:10px;padding:16px 18px;margin-bottom:10px;">
  <div style="display:flex;align-items:flex-start;gap:12px;">
    <span style="font-size:20px;flex-shrink:0;margin-top:2px;">{t["icon"]}</span>
    <div style="flex:1;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <div style="font-size:14px;font-weight:700;color:#10131C;">{t["title"]}</div>
        <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;background:{t["tag_bg"]};color:{t["tag_color"]};white-space:nowrap;">{t["tag"]}</span>
      </div>
      <div style="font-size:12px;color:#676E8A;line-height:1.65;margin-bottom:8px;">{t["body"]}</div>
      <div style="font-size:10px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#3E4FE0;background:#F7F8FD;padding:6px 10px;border-radius:6px;">{t["stats"]}</div>
    </div>
  </div>
</div>''', unsafe_allow_html=True)

    elif tab == "Regulatory Updates":
        _REGULATIONS = [
            {
                "icon":"🇪🇺","region":"Europe","title":"EU PSD3 & Payment Services Regulation (PSR)",
                "status":"Draft Published — Expected adoption 2026-2027",
                "status_color":"#8A4B00","status_bg":"#FAF0D0",
                "body":"PSD3 introduces stronger SCA exemptions for low-risk transactions under EUR 500 with merchant Transaction Risk Analysis (TRA). The PSR (a directly applicable regulation replacing PSD2 directives) will harmonize rules across all EU member states. Key changes: expanded open banking access, fraud liability shifts, non-bank PSP access to payment systems, and enhanced consumer rights. Merchants can expect 3-5% auth rate improvement from relaxed SCA and lower friction at checkout.",
            },
            {
                "icon":"🇧🇷","region":"LATAM","title":"Brazil PIX Credit Launch & Open Finance Expansion",
                "status":"Launching Q2 2026",
                "status_color":"#48610A","status_bg":"#F0F5DC",
                "body":"The Central Bank of Brazil (BCB) is launching PIX Credit, allowing consumers to make PIX payments using credit lines from their banks. This effectively creates an instant BNPL mechanism on existing PIX rails. Expected to increase eCommerce conversion by 15-20% by combining PIX simplicity with installment flexibility. Additionally, Open Finance Phase 4 expands data sharing to investments and insurance. Merchants should prepare checkout flows to support PIX Credit alongside standard PIX.",
            },
            {
                "icon":"🇮🇳","region":"APAC","title":"India MDR Regulation & Digital Payment Incentives",
                "status":"Under Review — Policy update expected H2 2026",
                "status_color":"#464F6E","status_bg":"#DFE3F2",
                "body":"RBI maintains zero MDR on UPI and RuPay debit transactions, subsidized via government reimbursement to banks (~$350M annually). The sustainability of this model is under review. Industry bodies are lobbying for a small MDR (0.15-0.3%) to fund infrastructure investment. Separately, RBI's e-mandate framework now supports recurring UPI payments up to INR 1 lakh. The Digital Personal Data Protection Act (2023) impacts how payment data can be stored and processed, with compliance deadlines in 2026.",
            },
            {
                "icon":"🇸🇦","region":"MENA","title":"Saudi SAMA Mada Requirements & Open Banking",
                "status":"Mandatory — Enforcement active",
                "status_color":"#C4384A","status_bg":"#FAE2E5",
                "body":"SAMA mandates that all domestic debit card transactions route through the Mada scheme. By Q3 2026, merchants without Mada certification will see 100% decline rates on local debit cards (which represent ~45% of all card payments). Open Banking framework launched with 8 banks in phase 1. BNPL regulation formalized — all BNPL providers must be SAMA-licensed. Vision 2030 cashless target of 70% non-cash transactions is driving aggressive fintech licensing and payment modernization.",
            },
            {
                "icon":"🇳🇬","region":"Africa","title":"Nigeria eNaira & CBN Cashless Policy Updates",
                "status":"In Effect — Evolving framework",
                "status_color":"#2F3FC4","status_bg":"#E9ECFC",
                "body":"The eNaira (CBDC) is live but adoption remains modest (~$80M in circulation). CBN continues enforcing cashless policy with withdrawal limits (NGN 500K/individual, NGN 5M/corporate per week). Cash processing fees of 5-10% apply above limits. The NIBSS Instant Payment (NIP) system processes 1B+ transactions annually. CBN has issued new Payment Service Bank (PSB) licenses expanding mobile money. New regulations require payment processors to maintain local data storage and obtain CBN licensing.",
            },
            {
                "icon":"🌎","region":"LATAM","title":"Data Localization Trends Across Latin America",
                "status":"Varies by Country — Monitoring recommended",
                "status_color":"#4A5170","status_bg":"#F1F3FB",
                "body":"Brazil (LGPD) does not mandate data localization but requires consent for cross-border transfers and BCB mandates local payment data processing. Mexico (Ley Fintech) requires financial data to be accessible to Mexican regulators. Colombia requires certain financial records to remain accessible domestically. Argentina's data protection law requires adequate protection for cross-border transfers. Chile is updating its data protection framework (GDPR-aligned). Merchants operating across LATAM should evaluate whether a regional data center strategy is needed.",
            },
        ]

        for r in _REGULATIONS:
            st.markdown(f'''<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:10px;padding:16px 18px;margin-bottom:10px;">
  <div style="display:flex;align-items:flex-start;gap:12px;">
    <span style="font-size:20px;flex-shrink:0;margin-top:2px;">{r["icon"]}</span>
    <div style="flex:1;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <div style="font-size:14px;font-weight:700;color:#10131C;">{r["title"]}</div>
        <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;background:#E9ECFC;color:#3E4FE0;white-space:nowrap;">{r["region"]}</span>
      </div>
      <div style="margin-bottom:8px;"><span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;background:{r["status_bg"]};color:{r["status_color"]};">{r["status"]}</span></div>
      <div style="font-size:12px;color:#676E8A;line-height:1.65;">{r["body"]}</div>
    </div>
  </div>
</div>''', unsafe_allow_html=True)

    elif tab == "Market News":
        _NEWS = [
            {"date":"Mar 22, 2026","region":"LATAM","title":"Brazil Central Bank announces PIX credit launch for Q2 2026","body":"PIX credit will allow merchants to offer instant BNPL at checkout via PIX rails — expected to increase conversion by 15-20% for Brazilian merchants. Cielo, PagBank, and Stone are early adopters.","impact":"High","tag":"Regulation"},
            {"date":"Mar 20, 2026","region":"MENAT","title":"Saudi Arabia mandates Mada scheme for all local transactions","body":"SAMA has confirmed that all domestic card transactions must route through Mada by Q3 2026. Merchants without Mada support will see 100% decline rates on local cards. Checkout.com and Tap Payments are certified.","impact":"Critical","tag":"Compliance"},
            {"date":"Mar 18, 2026","region":"APAC","title":"India UPI crosses 15 billion monthly transactions","body":"UPI volume continues to grow at 40% YoY. RazorPay and Cashfree are leading PSPs for UPI acceptance. Google Pay and PhonePe dominate market share.","impact":"Medium","tag":"Market Growth"},
            {"date":"Mar 15, 2026","region":"Europe","title":"EU PSD3 draft published — stronger SCA exemptions for low-risk transactions","body":"The draft PSD3 regulation proposes wider SCA exemptions for transactions under EUR 500 with merchant TRA. This could improve auth rates by 3-5% for European merchants using Adyen and Stripe.","impact":"High","tag":"Regulation"},
            {"date":"Mar 12, 2026","region":"Global","title":"Visa and Mastercard announce 2026 fee increases for cross-border transactions","body":"Interchange fees for cross-border transactions increasing by 8-12 basis points effective July 2026. Local acquiring becomes even more critical for cost optimization.","impact":"High","tag":"Pricing"},
            {"date":"Mar 10, 2026","region":"LATAM","title":"Colombia launches instant payment system — Transfiya 2.0","body":"Banco de la Republica upgrades Transfiya with merchant acceptance capabilities. PSE alternative expected to reduce costs and increase real-time settlement options.","impact":"Medium","tag":"Infrastructure"},
            {"date":"Mar 8, 2026","region":"MENAT","title":"UAE Central Bank launches AANI instant payments nationwide","body":"AANI is now available across all UAE banks. Merchants can accept instant A2A payments with zero chargeback risk. Integration via Checkout.com and Tap Payments.","impact":"High","tag":"Infrastructure"},
            {"date":"Mar 5, 2026","region":"Global","title":"Apple Pay Later discontinued — shifts focus to issuer installments","body":"Apple confirms BNPL product sunset. Market opportunity for Tamara, Tabby, Klarna, and local BNPL providers to fill the gap.","impact":"Medium","tag":"Competitive"},
        ]
        _impact_style = {"Critical":("#C4384A","#FAE2E5"),"High":("#8A4B00","#FAF0D0"),"Medium":("#464F6E","#DFE3F2")}

        for n in _NEWS:
            ic, ibg = _impact_style.get(n["impact"], ("#4A5170","#F1F3FB"))
            st.markdown(f'<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:10px;padding:16px 18px;margin-bottom:8px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">'
                        f'<div style="flex:1;"><div style="font-size:14px;font-weight:700;color:#10131C;line-height:1.4;margin-bottom:4px;">{n["title"]}</div>'
                        f'<div style="display:flex;gap:6px;align-items:center;">'
                        f'<span style="font-size:10px;color:#858CA6;">{n["date"]}</span>'
                        f'<span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;background:#E9ECFC;color:#3E4FE0;">{n["region"]}</span>'
                        f'<span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;background:#F1F3FB;color:#4A5170;">{n["tag"]}</span>'
                        f'<span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;background:{ibg};color:{ic};">{n["impact"]}</span>'
                        f'</div></div></div>'
                        f'<div style="font-size:12px;color:#676E8A;line-height:1.6;">{n["body"]}</div>'
                        f'</div>', unsafe_allow_html=True)

# ── Merchants ──────────────────────────────────────────────────────────────────
def show_merchants():
    # name, country, region, tpv_m, aov, transactions, auth_rate
    MERCHANTS = [
        ("Rappi",        "Colombia",  "LATAM",     8.42,  32.5,  259077, 91.2),
        ("MercadoLibre", "Argentina", "LATAM",     7.31, 118.4,   61739, 88.9),
        ("Uber",         "Mexico",    "LATAM",     5.89,  18.2,  323626, 93.4),
        ("Netflix",      "USA",       "N. America",4.75,  15.5,  306452, 95.6),
        ("Spotify",      "Brazil",    "LATAM",     4.21,  10.0,  421421, 94.8),
        ("Despegar",     "Argentina", "LATAM",     3.84, 312.5,   12288, 87.5),
        ("Falabella",    "Chile",     "LATAM",     3.12,  87.3,   35739, 88.2),
        ("iFood",        "Brazil",    "LATAM",     2.93,  28.4,  103169, 91.8),
        ("Cinépolis",    "Mexico",    "LATAM",     2.14,  24.5,   62857, 92.4),
        ("PedidosYa",    "Argentina", "LATAM",     1.87,  35.8,   62570, 90.1),
        ("Claro",        "Mexico",    "LATAM",     1.52,  22.8,   49123, 89.7),
        ("Linio",        "Colombia",  "LATAM",     1.11,  72.1,   25936, 87.1),
    ]

    st.markdown("""
<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:4px;">
  <span style="font-size:22px;font-weight:700;color:#10131C;">Merchants</span>
</div>
<div style="font-size:11px;color:#858CA6;margin-bottom:18px;">Your Merchants</div>
""", unsafe_allow_html=True)

    stat_row([
        {"label":"Merchants Live",    "value":"12",     "delta":"Active & connected",    "delta_type":"flat"},
        {"label":"Total TPV",         "value":"$47.24M","delta":"This month · USD",       "delta_type":"up","val_color":"#8B9BFF"},
        {"label":"Avg AOV",           "value":"$64.8",  "delta":"Across all merchants",   "delta_type":"flat"},
        {"label":"Avg Approval Rate", "value":"90.2%",  "delta":"↑ +1.2pp vs last mo.", "delta_type":"up"},
    ])

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Row 1: TPV + Approval Rate
    col_l, col_r = st.columns(2)
    with col_l:
        data = sorted(MERCHANTS, key=lambda x: x[3], reverse=True)
        fig = go.Figure(go.Bar(
            x=[r[3] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color="#3E4FE0",
            text=[f"${r[3]}M" for r in data], textposition="outside",
            textfont=dict(size=10, color="#676E8A"),
        ))
        fig.update_layout(
            title=dict(text="TPV by Merchant", font=dict(size=12, color="#10131C"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=70, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        data = sorted(MERCHANTS, key=lambda x: x[6], reverse=True)
        colors = ["#5A7A00" if r[6] >= 92 else "#B36200" if r[6] >= 89 else "#C4384A" for r in data]
        fig = go.Figure(go.Bar(
            x=[r[6] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color=colors,
            text=[f"{r[6]}%" for r in data], textposition="outside",
            textfont=dict(size=10, color="#676E8A"),
        ))
        fig.update_layout(
            title=dict(text="Approval Rate by Merchant", font=dict(size=12, color="#10131C"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=60, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[80, 100]),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 2: AOV + Total Transactions
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        data = sorted(MERCHANTS, key=lambda x: x[4], reverse=True)
        fig = go.Figure(go.Bar(
            x=[r[4] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color="#8B9BFF",
            text=[f"${r[4]}" for r in data], textposition="outside",
            textfont=dict(size=10, color="#676E8A"),
        ))
        fig.update_layout(
            title=dict(text="Average Order Value (AOV)", font=dict(size=12, color="#10131C"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=70, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        data = sorted(MERCHANTS, key=lambda x: x[5], reverse=True)
        fig = go.Figure(go.Bar(
            x=[r[5] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color="#3E4FE0",
            text=[f"{r[5]:,}" for r in data], textposition="outside",
            textfont=dict(size=10, color="#676E8A"),
        ))
        fig.update_layout(
            title=dict(text="Total Transactions", font=dict(size=12, color="#10131C"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=80, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Merchant Summary table
    def auth_bar(v):
        color = "#5A7A00" if v >= 92 else "#B36200" if v >= 89 else "#C4384A"
        pct = int((v - 80) / 20 * 100)
        return f'<div style="display:flex;align-items:center;gap:8px;"><div style="flex:1;background:#F1F3FB;border-radius:2px;height:4px;"><div style="width:{pct}%;height:4px;background:{color};border-radius:2px;"></div></div><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:{color};min-width:38px;">{v}%</span></div>'

    rows_html = ""
    for i, r in enumerate(MERCHANTS):
        border = "" if i == len(MERCHANTS)-1 else "border-bottom:1px solid rgba(0,0,0,0.05);"
        rows_html += f"""
  <div style="display:grid;grid-template-columns:1.5fr 1fr 1fr 0.9fr 0.8fr 1fr 1.6fr;padding:9px 16px;{border}align-items:center;">
    <span style="font-size:12px;font-weight:600;color:#10131C;">{r[0]}</span>
    <span style="font-size:11px;color:#676E8A;">{r[1]}</span>
    <span style="font-size:11px;color:#676E8A;">{r[2]}</span>
    <span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#10131C;">${r[3]}M</span>
    <span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#676E8A;">${r[4]}</span>
    <span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#676E8A;">{r[5]:,}</span>
    {auth_bar(r[6])}
  </div>"""

    st.markdown(f"""
<div style="font-size:13px;font-weight:700;color:#10131C;margin:20px 0 10px;">Merchant Summary</div>
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;overflow:hidden;">
  <div style="display:grid;grid-template-columns:1.5fr 1fr 1fr 0.9fr 0.8fr 1fr 1.6fr;padding:9px 16px;border-bottom:1px solid rgba(0,0,0,0.07);font-size:10px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#858CA6;">
    <span>Merchant</span><span>Country</span><span>Region</span><span>TPV (M USD)</span><span>AOV (USD)</span><span>Transactions</span><span>Approval Rate</span>
  </div>
  {rows_html}
</div>
""", unsafe_allow_html=True)

# ── Benchmarks ─────────────────────────────────────────────────────────────────
def show_benchmarks():
    _ext = external_account()
    if _ext is not None:
        return show_own_benchmarks(_ext)
    if st.session_state.role != "internal":
        return _ext_locked("Benchmarks need your record",
                           "Sign in with your company email so we can place you against the programme.")
    # ── Rev Share Dashboard ───────────────────────────────────────────────────
    st.markdown(hero(
        "Revenue Share", eyebrow="Rev share",
        subtitle="Partner rev share earned by Yuno — Feb 2026.",
        tiles=[("$732K", "2024 Total", "#E68ABE"),
               ("$123K", "Feb 2026", "#E0ED80"),
               ("$1.48M", "ARR", "#8B9BFF"),
               ("$245K", "Peak (Oct 25)", "#D08A1A"),
               ("$1.78M", "2025 Total", "#B9C2FF"),
               ("+33%", "vs Feb 25", "#E0ED80")]), unsafe_allow_html=True)

    # ── Rev Share by Region (bar chart) + Top Partners table ──────────────────
    _rev_regions = [
        ("LATAM", 47600, 42, "#3E4FE0"),
        ("Brasil", 32900, 29, "#5A7A00"),
        ("Global", 28300, 25, "#5A6486"),
        ("APAC", 3300, 3, "#0086A8"),
        ("N. America", 400, 0, "#48610A"),
    ]
    _top_partners = [
        ("DLocal", "$25,338"),
        ("Stripe", "$21,705"),
        ("Cielo", "$17,635"),
        ("Bamboo", "$9,491"),
        ("Mercado Pago", "$7,365"),
        ("Unlimint", "$5,949"),
        ("PagBank", "$4,516"),
        ("Nuvei/Paymentez", "$3,772"),
        ("Pagar.me", "$3,441"),
        ("PicPay", "$3,180"),
    ]

    col_chart, col_table = st.columns([1.5, 1])

    with col_chart:
        # Region bars
        max_rev = max(r[1] for r in _rev_regions)
        bars_html = ""
        for region, rev, pct, color in _rev_regions:
            w = int(rev / max_rev * 100)
            bars_html += (f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                          f'<span style="font-size:12px;color:#676E8A;min-width:80px;text-align:right;">{region}</span>'
                          f'<div style="flex:1;height:28px;background:#F1F3FB;border-radius:6px;overflow:hidden;position:relative;">'
                          f'<div style="width:{w}%;height:100%;background:{color};border-radius:6px;display:flex;align-items:center;padding-left:10px;">'
                          f'<span style="font-size:11px;font-weight:700;color:#fff;">${rev/1000:.1f}K</span></div></div>'
                          f'<span style="font-size:11px;font-weight:600;color:#676E8A;min-width:30px;">{pct}%</span></div>')
        st.markdown(f'<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:12px;padding:20px;">'
                    f'<div style="font-size:14px;font-weight:700;color:#10131C;margin-bottom:14px;">Rev Share by Region</div>'
                    f'{bars_html}</div>', unsafe_allow_html=True)

    with col_table:
        # Top partners table
        rows_html = ""
        for i, (name, amount) in enumerate(_top_partners):
            bg = "#F7F8FD" if i % 2 == 0 else "#fff"
            rows_html += (f'<tr style="background:{bg};">'
                          f'<td style="padding:8px 12px;font-size:12px;color:#858CA6;font-weight:600;">{i+1}</td>'
                          f'<td style="padding:8px 12px;font-size:13px;font-weight:700;color:#10131C;">{name}</td>'
                          f'<td style="padding:8px 12px;font-size:13px;font-weight:700;color:#3F5208;font-family:var(--font);font-variant-numeric:tabular-nums;text-align:right;">{amount}</td></tr>')
        st.markdown(f'<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:12px;overflow:hidden;">'
                    f'<div style="padding:16px 16px 8px;font-size:14px;font-weight:700;color:#10131C;">Top Partners — Feb 2026</div>'
                    f'<table style="width:100%;border-collapse:collapse;">'
                    f'<thead><tr><th style="padding:6px 12px;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#858CA6;text-align:left;border-bottom:1px solid #E2E6F4;">#</th>'
                    f'<th style="padding:6px 12px;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#858CA6;text-align:left;border-bottom:1px solid #E2E6F4;">Partner</th>'
                    f'<th style="padding:6px 12px;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#858CA6;text-align:right;border-bottom:1px solid #E2E6F4;">Rev Share</th></tr></thead>'
                    f'<tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)

    # ── Monthly trend chart ───────────────────────────────────────────────────
    _monthly = [("Nov 24",61),("Dec 24",61),("Jan 25",122),("Feb 25",122),("Mar 25",183),("Apr 25",183),("May 25",144),("Jun 25",145),("Jul 25",166),("Aug 25",219),("Sep 25",245),("Oct 25",245),("Nov 25",178),("Dec 25",161),("Jan 26",123),("Feb 26",123)]
    max_m = max(v for _, v in _monthly)
    trend_bars = ""
    for month, val in _monthly:
        h = int(val / max_m * 100)
        is_peak = val == max_m
        color = "#B36200" if is_peak else "#3E4FE0"
        trend_bars += (f'<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
                       f'<div style="font-size:10px;font-weight:600;color:#676E8A;margin-bottom:2px;">${val}K</div>'
                       f'<div style="width:100%;height:120px;display:flex;align-items:flex-end;">'
                       f'<div style="width:100%;height:{h}%;background:{color};border-radius:4px 4px 0 0;min-height:4px;"></div></div>'
                       f'<div style="font-size:10px;color:#858CA6;margin-top:4px;white-space:nowrap;">{month}</div></div>')
    st.markdown(f'<div style="background:#fff;border:0.5px solid #E2E6F4;border-radius:12px;padding:20px;margin-top:14px;">'
                f'<div style="font-size:14px;font-weight:700;color:#10131C;margin-bottom:14px;">Monthly Revenue Share Trend</div>'
                f'<div style="display:flex;gap:4px;align-items:flex-end;">{trend_bars}</div></div>', unsafe_allow_html=True)

    return  # Rev Share section complete — benchmarks removed

    months = ["Aug/24","Sep/24","Oct/24","Nov/24","Dec/24","Jan/25"]
    st.markdown("", unsafe_allow_html=True)

    stat_row([
        {"label":"Your Avg Approval Rate", "value":"90.2%",  "delta":"↑ +1.2pp vs last mo.", "delta_type":"up"},
        {"label":"Network Avg",            "value":"87.6%",  "delta":"→ stable",              "delta_type":"flat"},
        {"label":"Top Performer",          "value":"95.6%",  "delta":"↑ Netflix · Streaming", "delta_type":"up", "val_color":"#5A7A00"},
        {"label":"Your Recovery Rate",     "value":"4.1%",   "delta":"↑ +0.4pp MoM",          "delta_type":"up"},
        {"label":"Network Recovery Avg",   "value":"3.8%",   "delta":"→ stable",              "delta_type":"flat"},
    ])

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        yuno_approval   = [68.2, 67.1, 65.8, 64.3, 62.1, 58.4]
        peer2_approval  = [95.1, 96.2, 96.8, 96.4, 96.9, 97.2]
        peer3_approval  = [82.4, 83.1, 82.7, 82.9, 82.1, 81.8]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="You (Yuno)", x=months, y=yuno_approval,  marker_color="#3E4FE0", text=[f"{v}%" for v in yuno_approval],  textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig.add_trace(go.Bar(name="Peer Avg",   x=months, y=peer2_approval, marker_color="#0086A8", text=[f"{v}%" for v in peer2_approval], textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig.add_trace(go.Bar(name="Top Peer",   x=months, y=peer3_approval, marker_color="#B36200", text=[f"{v}%" for v in peer3_approval], textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig.update_layout(
            title=dict(text="Approval Rate Benchmark", font=dict(size=12, color="#10131C"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=10, t=40, b=30),
            legend=dict(orientation="h", y=-0.15, font=dict(size=10,color="#676E8A"), bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)", ticksuffix="%", range=[0,105]),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_r:
        yuno_recovery  = [0.9, 0.8, 0.9, 0.7, 0.6, 0.5]
        peer2_recovery = [4.8, 5.1, 5.0, 5.3, 2.7, 3.9]
        peer3_recovery = [3.8, 3.9, 4.1, 4.3, 5.2, 2.6]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="You (Yuno)", x=months, y=yuno_recovery,  marker_color="#3E4FE0", text=[f"{v}%" for v in yuno_recovery],  textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig2.add_trace(go.Bar(name="Peer Avg",   x=months, y=peer2_recovery, marker_color="#0086A8", text=[f"{v}%" for v in peer2_recovery], textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig2.add_trace(go.Bar(name="Top Peer",   x=months, y=peer3_recovery, marker_color="#B36200", text=[f"{v}%" for v in peer3_recovery], textposition="outside", textfont=dict(size=9, color="#676E8A")))
        fig2.update_layout(
            title=dict(text="Recovery Rate of Rejected Transactions — Benchmark", font=dict(size=12, color="#10131C"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=10, t=40, b=30),
            legend=dict(orientation="h", y=-0.15, font=dict(size=10,color="#676E8A"), bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)", ticksuffix="%"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Second row — decline reasons + TPV benchmark
    col_l2, col_r2 = st.columns(2)

    with col_l2:
        reasons = ["Insufficient funds","Do not honor","Invalid card","Expired card","Fraud suspected","Limit exceeded","Tech error"]
        you_pct  = [31.2, 22.4, 14.1, 9.8, 8.3, 7.6, 6.6]
        peer_pct = [28.5, 20.1, 12.8, 11.2, 10.4, 9.5, 7.5]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="You", x=you_pct,  y=reasons, orientation="h", marker_color="#3E4FE0"))
        fig3.add_trace(go.Bar(name="Peer Avg", x=peer_pct, y=reasons, orientation="h", marker_color="#0086A8"))
        fig3.update_layout(
            title=dict(text="Decline Reason Breakdown vs Peers", font=dict(size=12, color="#10131C"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#676E8A"),
            margin=dict(l=10, r=40, t=40, b=10),
            legend=dict(orientation="h", y=1.1, font=dict(size=10,color="#676E8A"), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)", ticksuffix="%"),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
            height=320,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_r2:
        st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;height:100%;">
  <div style="font-size:12px;font-weight:700;color:#10131C;margin-bottom:14px;">How You Rank</div>
  <div style="display:flex;flex-direction:column;gap:10px;">
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#676E8A;">Approval Rate</span><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#8B9BFF;">90.2% · <span style="color:#5A7A00;">Top 30%</span></span></div>
      <div style="background:#E2E6F4;border-radius:4px;height:6px;"><div style="width:70%;height:6px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#676E8A;">Recovery Rate</span><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#8B9BFF;">4.1% · <span style="color:#5A7A00;">Top 25%</span></span></div>
      <div style="background:#E2E6F4;border-radius:4px;height:6px;"><div style="width:75%;height:6px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#676E8A;">Fraud Rate</span><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#8B9BFF;">0.8% · <span style="color:#5A7A00;">Top 20%</span></span></div>
      <div style="background:#E2E6F4;border-radius:4px;height:6px;"><div style="width:80%;height:6px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#676E8A;">Avg Response Time</span><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#8B9BFF;">1.2s · <span style="color:#B36200;">Top 50%</span></span></div>
      <div style="background:#E2E6F4;border-radius:4px;height:6px;"><div style="width:50%;height:6px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#676E8A;">Chargeback Rate</span><span style="font-size:11px;font-family:var(--font);font-variant-numeric:tabular-nums;color:#8B9BFF;">0.3% · <span style="color:#5A7A00;">Top 15%</span></span></div>
      <div style="background:#E2E6F4;border-radius:4px;height:6px;"><div style="width:85%;height:6px;background:linear-gradient(90deg,#3E4FE0,#8B9BFF);border-radius:4px;"></div></div>
    </div>
  </div>
  <div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(0,0,0,0.07);font-size:10px;color:#858CA6;">Peers = anonymised merchants in same category & region · Updated monthly</div>
</div>
""", unsafe_allow_html=True)

# ── Payment Recommendations ──────────────────────────────────────────────────
# Partner enrichment data for expanded detail view
_PARTNER_ENRICHMENT = {
    "ADYEN": {"commercial_contact":"Tom Kuehn","technical_contact":"Jorge Restrepo","verticals":"Retail, Travel, Mobility, Streaming, Marketplaces","revshare":"Yes","avg_pricing":"€0.11 + scheme fees","discount_rate":"—","discount_condition":"—","onboarding":"API keys + KYC docs, 2-4 weeks","health":"Strong","merchants_live":5,"merchants":"Uber, Netflix, Spotify, Rappi, MercadoLibre"},
    "CIELO": {"commercial_contact":"Talita Diaz Gama","technical_contact":"Valentina Perez","verticals":"Retail, eCommerce, Food Delivery, Subscriptions","revshare":"Yes — active","avg_pricing":"From 4.99%","discount_rate":"—","discount_condition":"—","onboarding":"Brazilian CNPJ required, 3-4 weeks","health":"Strong","merchants_live":3,"merchants":"Rappi, iFood, Falabella"},
    "DLOCAL": {"commercial_contact":"Daniela Reyes","technical_contact":"Jorge Restrepo","verticals":"Streaming, Gaming, SaaS, Marketplaces, Ride-hailing","revshare":"Yes — active","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Single API, no local entity needed, 1-2 weeks","health":"Strong","merchants_live":4,"merchants":"Spotify, Netflix, Uber, MercadoLibre"},
    "STRIPE": {"commercial_contact":"Daniela Reyes","technical_contact":"Valentina Perez","verticals":"SaaS, Marketplaces, eCommerce, On-demand","revshare":"Yes — active","avg_pricing":"2.9% + $0.30","discount_rate":"—","discount_condition":"—","onboarding":"Self-serve API, 1 week","health":"Strong","merchants_live":2,"merchants":"Netflix, Despegar"},
    "CHECKOUT": {"commercial_contact":"Francisco Quintana","technical_contact":"Jorge Restrepo","verticals":"Travel, Gaming, Crypto, Forex, Marketplaces","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"API integration, 2-3 weeks","health":"Strong","merchants_live":0,"merchants":"No merchants live yet — in onboarding"},
    "CHECKOUT MENA": {"commercial_contact":"Francisco Quintana","technical_contact":"Jorge Restrepo","verticals":"Travel, Gaming, Crypto, Forex, Marketplaces","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"API integration, 2-3 weeks","health":"Strong","merchants_live":0,"merchants":"No merchants live yet — in onboarding"},
    "GETNET BR": {"commercial_contact":"Johanderson Guevara","technical_contact":"Valentina Perez","verticals":"Retail, Food Delivery, Subscriptions","revshare":"Yes","avg_pricing":"From 2%","discount_rate":"—","discount_condition":"—","onboarding":"Brazilian CNPJ, Santander relationship helps, 3 weeks","health":"Good","merchants_live":2,"merchants":"Rappi, Falabella"},
    "MERCADOPAGO BR": {"commercial_contact":"Johanderson Guevara","technical_contact":"Jorge Restrepo","verticals":"eCommerce, Marketplaces, Retail, Delivery","revshare":"Yes — active","avg_pricing":"4.99%","discount_rate":"—","discount_condition":"—","onboarding":"API + MercadoLibre ecosystem, 2 weeks","health":"Strong","merchants_live":3,"merchants":"MercadoLibre, Rappi, PedidosYa"},
    "EBANX": {"commercial_contact":"Talita Diaz Gama","technical_contact":"Valentina Perez","verticals":"SaaS, Gaming, Streaming, Digital Goods","revshare":"Yes — active","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"No local entity needed, 1-2 weeks","health":"Good","merchants_live":2,"merchants":"Spotify, Uber"},
    "BAMBOO PAYMENTS": {"commercial_contact":"Talita Diaz Gama","technical_contact":"Jorge Restrepo","verticals":"eCommerce, Retail, Delivery, Fintech","revshare":"Yes — active","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Single API for LATAM, 2 weeks","health":"Good","merchants_live":2,"merchants":"Rappi, PedidosYa"},
    "NUVEI": {"commercial_contact":"Alessandra Rospigliosi","technical_contact":"Valentina Perez","verticals":"Gaming, Crypto, Forex, Travel, iGaming","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"API + compliance review, 3-4 weeks","health":"Good","merchants_live":0,"merchants":"No merchants live yet — in pipeline"},
    "TAP PAYMENTS": {"commercial_contact":"Francisco Quintana","technical_contact":"Jorge Restrepo","verticals":"eCommerce, Retail, Food Delivery, SaaS","revshare":"Yes","avg_pricing":"2.75% + $0.30","discount_rate":"—","discount_condition":"—","onboarding":"GCC entity required, 2-3 weeks","health":"Good","merchants_live":0,"merchants":"No merchants live yet — in pipeline"},
    "PAYMOB": {"commercial_contact":"Francisco Quintana","technical_contact":"Valentina Perez","verticals":"eCommerce, Retail, SME, Food Delivery","revshare":"Pending","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Local partnership, 2-3 weeks","health":"New","merchants_live":0,"merchants":"No merchants live yet — prospecting"},
    "PAGBANK BRASIL": {"commercial_contact":"Johanderson Guevara","technical_contact":"Jorge Restrepo","verticals":"eCommerce, Retail, SME, Subscriptions","revshare":"Yes — active","avg_pricing":"From 4.99%","discount_rate":"—","discount_condition":"—","onboarding":"Brazilian CNPJ required, 2 weeks","health":"Good","merchants_live":2,"merchants":"iFood, Claro"},
    "STONE": {"commercial_contact":"Johanderson Guevara","technical_contact":"Valentina Perez","verticals":"Retail, eCommerce, SME","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Brazilian CNPJ required, 3 weeks","health":"Good","merchants_live":1,"merchants":"Falabella"},
    "PAGAR.ME": {"commercial_contact":"Johanderson Guevara","technical_contact":"Jorge Restrepo","verticals":"eCommerce, SaaS, Subscriptions, Marketplaces","revshare":"Yes — active","avg_pricing":"From 3.49% + R$0.39","discount_rate":"—","discount_condition":"—","onboarding":"Brazilian CNPJ, 2-3 weeks","health":"Strong","merchants_live":2,"merchants":"Spotify, Netflix"},
    "KUSHKI": {"commercial_contact":"Talita Diaz Gama","technical_contact":"Valentina Perez","verticals":"eCommerce, Ride-hailing, Delivery, SaaS","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Single API, 2 weeks","health":"Good","merchants_live":2,"merchants":"Uber, Rappi"},
    "CYBERSOURCE": {"commercial_contact":"Francisco Quintana","technical_contact":"Jorge Restrepo","verticals":"Enterprise, Travel, Retail, eCommerce","revshare":"Yes","avg_pricing":"—","discount_rate":"—","discount_condition":"—","onboarding":"Visa subsidiary, 3-4 weeks","health":"Strong","merchants_live":1,"merchants":"Despegar"},
    "RAZORPAY": {"commercial_contact":"Francisco Quintana","technical_contact":"Valentina Perez","verticals":"eCommerce, SaaS, Fintech, Subscriptions","revshare":"Yes","avg_pricing":"2% per txn","discount_rate":"—","discount_condition":"—","onboarding":"Indian entity required, 2 weeks","health":"Good","merchants_live":0,"merchants":"No merchants live yet — in pipeline"},
    "XENDIT": {"commercial_contact":"Francisco Quintana","technical_contact":"Jorge Restrepo","verticals":"eCommerce, Marketplaces, Fintech, Gaming","revshare":"Yes","avg_pricing":"~2.9% + fixed fee","discount_rate":"—","discount_condition":"—","onboarding":"SEA entity required, 2 weeks","health":"Good","merchants_live":0,"merchants":"No merchants live yet — in pipeline"},
}

def show_payment_recs():
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(160deg,#080911 0%,#10131C 40%,#141827 100%);border-radius:20px;padding:48px 44px 40px;margin-bottom:0;position:relative;overflow:hidden;">
  <div style="position:absolute;top:-80px;right:-80px;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(84,104,245,0.12),transparent 65%);"></div>
  <div style="position:absolute;bottom:-60px;left:30%;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(0,134,168,0.06),transparent 65%);"></div>
  <div style="position:absolute;top:20px;right:40px;font-size:120px;font-weight:700;color:rgba(255,255,255,0.02);letter-spacing:-6px;line-height:1;">PIE</div>
  <div style="position:relative;z-index:1;">
    <div style="display:inline-flex;align-items:center;gap:8px;padding:4px 14px;border-radius:20px;background:rgba(84,104,245,0.12);border:1px solid rgba(84,104,245,0.2);margin-bottom:16px;">
      <span style="font-size:14px;">✦</span>
      <span style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#8B9BFF;">Payment Intelligence Engine</span>
    </div>
    <div style="font-size:26px;font-weight:700;color:#fff;letter-spacing:-1px;line-height:1.15;margin-bottom:10px;">Find the right payment<br>partner for any market</div>
    <div style="font-size:13px;color:#858CA6;line-height:1.7;max-width:480px;">Describe where your merchant is expanding. We match them to the best-fit payment partners — with live integration status, pricing, onboarding timeline, and merchant traction across 189 countries.</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Search bar ────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:#fff;border:1px solid #E2E6F4;border-radius:0 0 20px 20px;padding:20px 28px 10px;margin-bottom:4px;box-shadow:0 8px 32px rgba(0,0,0,0.04);">
  <div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px;">Describe your merchant's needs</div>
</div>""", unsafe_allow_html=True)

    # Free-text search
    free_search = st.text_input("Describe the merchant", placeholder="e.g. Uber wants to expand into Brazil with local processing...", key="payrec_free_search", label_visibility="collapsed")

    # Parse free text into filters
    _COUNTRY_KEYWORDS = {name.lower(): iso for iso, name in _ISO_TO_COUNTRY.items()}
    # Common aliases and abbreviations
    _COUNTRY_ALIASES = {
        "u.s.": "US", "u.s": "US", "usa": "US", "united states": "US", "the us": "US", "the u.s.": "US",
        "estados unidos": "US", "america": "US",
        "u.k.": "GB", "uk": "GB", "united kingdom": "GB", "england": "GB", "britain": "GB",
        "uae": "AE", "u.a.e.": "AE", "u.a.e": "AE", "emirates": "AE", "dubai": "AE", "abu dhabi": "AE",
        "ksa": "SA", "saudi": "SA", "saudi arabia": "SA", "arabia": "SA",
        "brasil": "BR", "brazil": "BR",
        "mexico": "MX", "méxico": "MX",
        "colombia": "CO",
        "argentina": "AR",
        "chile": "CL",
        "peru": "PE", "perú": "PE",
        "turkey": "TR", "türkiye": "TR", "turkiye": "TR",
        "singapore": "SG",
        "india": "IN",
        "indonesia": "ID",
        "japan": "JP",
        "south korea": "KR", "korea": "KR",
        "germany": "DE",
        "france": "FR",
        "spain": "ES",
        "italy": "IT",
        "netherlands": "NL", "holland": "NL",
        "nigeria": "NG",
        "south africa": "ZA",
        "egypt": "EG",
        "qatar": "QA",
        "kuwait": "KW",
        "bahrain": "BH",
        "oman": "OM",
        "jordan": "JO",
        "iraq": "IQ",
        "morocco": "MA",
        "canada": "CA",
        "australia": "AU",
        "philippines": "PH",
        "thailand": "TH",
        "vietnam": "VN",
        "malaysia": "MY",
        "pakistan": "PK",
        "bangladesh": "BD",
        "kenya": "KE",
        "ghana": "GH",
        "uruguay": "UY",
        "ecuador": "EC",
        "panama": "PA",
        "costa rica": "CR",
        "guatemala": "GT",
        "dominican republic": "DO",
        "puerto rico": "PR",
        "el salvador": "SV",
        "honduras": "HN",
        "bolivia": "BO",
        "paraguay": "PY",
    }
    _auto_country = ""
    _auto_vertical = "All Verticals"
    _auto_proc = "Any"
    if free_search:
        fs_lower = free_search.lower()
        # Try aliases first (longest match)
        for alias, iso in sorted(_COUNTRY_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in fs_lower:
                _auto_country = _ISO_TO_COUNTRY.get(iso, "")
                break
        # Fallback to full country names from pycountry
        if not _auto_country:
            for cname, ciso in sorted(_COUNTRY_KEYWORDS.items(), key=lambda x: -len(x[0])):
                if cname in fs_lower:
                    _auto_country = _ISO_TO_COUNTRY.get(ciso, "")
                    break
        # Verticals — expanded keywords
        vertical_kw = {
            "gambling":"Gambling", "igaming":"Gambling", "betting":"Gambling", "casino":"Gambling",
            "gaming":"Gaming", "game":"Gaming", "esports":"Gaming",
            "crypto":"Crypto", "cryptocurrency":"Crypto", "bitcoin":"Crypto", "web3":"Crypto",
            "forex":"Forex", "trading":"Forex", "fx":"Forex",
            "airline":"Airlines", "airlines":"Airlines", "aviation":"Airlines", "flight":"Airlines", "travel":"Airlines",
            "high risk":"High Risk", "high-risk":"High Risk",
            "adult":"Adult",
            "mlm":"MLM", "multi-level":"MLM",
        }
        for kw, vl in sorted(vertical_kw.items(), key=lambda x: -len(x[0])):
            if kw in fs_lower:
                _auto_vertical = vl
                break
        if "local" in fs_lower and "processing" in fs_lower:
            _auto_proc = "LOCAL"
        elif "local" in fs_lower:
            _auto_proc = "LOCAL"
        elif "cross-border" in fs_lower or "cross border" in fs_lower or "crossborder" in fs_lower:
            _auto_proc = "CROSS_BORDER"

    st.markdown('<div style="font-size:10px;color:#858CA6;margin:-8px 0 10px;">or refine with filters</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1.5, 1.5])
    with col1:
        country_options = [""] + _SOT_COUNTRIES
        default_idx = country_options.index(_auto_country) if _auto_country in country_options else 0
        selected_country = st.selectbox("Target Country", country_options, key="payrec_country",
                                        index=default_idx if not st.session_state.get("payrec_country") else 0,
                                        format_func=lambda x: "Select target market..." if x == "" else x)
        # If free search found a country but dropdown wasn't set, use it
        if not selected_country and _auto_country:
            selected_country = _auto_country
    with col2:
        vertical_options = ["All Verticals"] + list(_VERTICAL_COLS.keys())
        selected_vertical = st.selectbox("Merchant Vertical", vertical_options, key="payrec_vertical")
        if selected_vertical == "All Verticals" and _auto_vertical != "All Verticals":
            selected_vertical = _auto_vertical
    with col3:
        proc_options = ["Any", "LOCAL", "CROSS_BORDER", "BOTH"]
        selected_proc = st.selectbox("Processing Type", proc_options, key="payrec_proc",
                                     format_func=lambda x: {"Any":"Any processing","LOCAL":"Local processing","CROSS_BORDER":"Cross-border","BOTH":"Both"}[x])
        if selected_proc == "Any" and _auto_proc != "Any":
            selected_proc = _auto_proc

    col_live, col_region = st.columns([1, 2])
    with col_live:
        live_only = st.checkbox("Show live partners only", value=True, key="payrec_live")
    with col_region:
        region_filter = st.selectbox("Filter by region", ["All Regions","LATAM","Brasil","MENAT","APAC","Europe","North America","Africa"], key="payrec_region_filter", label_visibility="collapsed",
                                     format_func=lambda x: "All Regions" if x == "All Regions" else x)

    # ── Landing state ─────────────────────────────────────────────────────────
    if not selected_country:
        total_p = len(PARTNERS_DATA)
        live_p = sum(1 for p in PARTNERS_DATA if p["status"] == "Live")
        st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:8px 0 16px;">
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:14px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#10131C;">{total_p}</div>
    <div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Partners</div>
  </div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:14px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#5A7A00;">{live_p}</div>
    <div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Live</div>
  </div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:14px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#3E4FE0;">189</div>
    <div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Countries</div>
  </div>
  <div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:14px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#B36200;">7</div>
    <div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Regions</div>
  </div>
</div>""", unsafe_allow_html=True)

        # Clickable sample prompts
        _PROMPTS = [
            ("Copa Airlines expanding into the U.S.", "United States", "Airlines", "Any"),
            ("Uber needs local processing in Brazil", "Brazil", "All Verticals", "LOCAL"),
            ("iGaming operator entering Turkey", "Turkey", "Gambling", "Any"),
            ("Crypto exchange launching in UAE", "United Arab Emirates", "Crypto", "Any"),
            ("SaaS recurring payments in Saudi Arabia", "Saudi Arabia", "All Verticals", "Any"),
        ]
        st.markdown('<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Quick search</div>', unsafe_allow_html=True)
        prompt_cols = st.columns(len(_PROMPTS))
        for pi, (plabel, pcountry, pvert, pproc) in enumerate(_PROMPTS):
            if prompt_cols[pi].button(plabel, key=f"prompt_{pi}", use_container_width=True):
                st.session_state["payrec_country"] = pcountry
                st.session_state["payrec_vertical"] = pvert
                st.session_state["payrec_proc"] = pproc
                st.session_state["payrec_free_search"] = plabel
                st.rerun()

        # Style prompt buttons
        components.html("""<script>
setTimeout(function(){
  var doc = window.parent.document;
  doc.querySelectorAll('button').forEach(function(btn){
    var t = btn.textContent.trim();
    var prompts = ['Copa Airlines','Uber needs','iGaming','Crypto exchange','SaaS recurring'];
    if(prompts.some(function(p){ return t.startsWith(p); })){
      btn.style.cssText='background:#E9ECFC !important;border:1px solid #D6DCFA !important;border-radius:20px !important;padding:8px 14px !important;font-size:11px !important;color:#3E4FE0 !important;font-weight:600 !important;cursor:pointer !important;box-shadow:none !important;white-space:normal !important;line-height:1.3 !important;text-align:left !important;min-height:0 !important;';
    }
  });
},250);
</script>""", height=0)

        # Region data with insights from PPTX
        _REGION_HEATMAP = {
            "LATAM":         {"count":"105","color":"#3E4FE0","countries":["Brazil","Mexico","Colombia","Argentina","Chile","Peru"],
                              "live":15,"strategic":2,"tier1":31,"revshare":"$47.6K/mo",
                              "offering_mix":{"Acquirer":48,"PSP":27,"APM":15,"Other":10},
                              "pipeline":{"Prospect":24,"Negotiation":12,"Review":8,"Signed":32,"Live":15},
                              "trends":["Fastest-growing eCommerce region globally","PIX in Brazil driving APM adoption","BNPL and wallet penetration accelerating"]},
            "Brasil":        {"count":"73","color":"#3E4FE0","countries":["Brazil"],
                              "live":32,"strategic":9,"tier1":4,"revshare":"$32.9K/mo",
                              "offering_mix":{"Acquirer":26,"PSP":24,"APM":12,"Other":5},
                              "pipeline":{"Prospect":7,"Negotiation":2,"Review":2,"Signed":14,"Live":32},
                              "trends":["PIX represents 40%+ of online payments","CNPJ required for local acquiring","Installments (parcelamento) expected at checkout"]},
            "MENAT":         {"count":"81","color":"#2F3FC4","countries":["Saudi Arabia","United Arab Emirates","Turkey","Qatar","Kuwait","Egypt"],
                              "live":2,"strategic":3,"tier1":21,"revshare":"—",
                              "offering_mix":{"Acquirer":31,"APM":22,"PSP":21,"Other":6},
                              "pipeline":{"Prospect":29,"Negotiation":9,"Review":19,"Signed":15,"Live":2},
                              "trends":["GCC Vision 2030 driving cashless economies","BNPL (Tamara/Tabby) becoming standard","Local card schemes (MADA, TROY, KNET) are mandatory"]},
            "APAC":          {"count":"53","color":"#00697F","countries":["Singapore","Thailand","Philippines","Japan","India","Indonesia"],
                              "live":6,"strategic":4,"tier1":10,"revshare":"$32.9K/mo",
                              "offering_mix":{"PSP":41,"Acquirer":7,"Fraud":2,"Other":2},
                              "pipeline":{"Prospect":8,"Negotiation":8,"Review":17,"Signed":10,"Live":6},
                              "trends":["Wallet-first markets (GrabPay, GCash, PayPay)","Real-time payments rails maturing","Data localization requirements in India, Indonesia"]},
            "Europe":        {"count":"82","color":"#5A6486","countries":["United Kingdom","Germany","France","Spain","Netherlands","Italy"],
                              "live":2,"strategic":3,"tier1":21,"revshare":"—",
                              "offering_mix":{"Acquirer":31,"APM":22,"PSP":21,"Other":6},
                              "pipeline":{"Prospect":29,"Negotiation":9,"Review":19,"Signed":15,"Live":2},
                              "trends":["iDEAL (NL), Bancontact (BE), SEPA dominate locally","Strong Data Privacy (GDPR) requirements","Open Banking / PSD2 enabling A2A payments"]},
            "North America": {"count":"37","color":"#48610A","countries":["United States","Canada","Mexico"],
                              "live":3,"strategic":5,"tier1":4,"revshare":"$0.4K/mo",
                              "offering_mix":{"Acquirer":35,"APM":1,"PSP":1},
                              "pipeline":{"Prospect":6,"Negotiation":6,"Review":4,"Signed":14,"Live":3},
                              "trends":["Cards dominate (Visa/MC/Amex/Discover)","ACH and real-time payments (FedNow) emerging","Highly regulated, PCI DSS compliance critical"]},
            "Africa":        {"count":"5","color":"#B36200","countries":["South Africa","Nigeria","Kenya"],
                              "live":0,"strategic":0,"tier1":2,"revshare":"—",
                              "offering_mix":{"PSP":3,"Acquirer":2},
                              "pipeline":{"Prospect":0,"Negotiation":0,"Review":1,"Signed":4,"Live":0},
                              "trends":["Mobile money dominant (M-Pesa, MTN)","Low card penetration, high cash usage","Frontier market with long-term upside"]},
        }

        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin:4px 0 14px;">
  <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,#E2E6F4,transparent);"></div>
  <span style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;">Global Coverage</span>
  <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,#E2E6F4,transparent);"></div>
</div>""", unsafe_allow_html=True)

        region_list = list(_REGION_HEATMAP.keys())
        for ci, region in enumerate(region_list):
            rd = _REGION_HEATMAP[region]
            exp_key = f"reg_exp_{region}"
            is_open = st.session_state.get(exp_key, False)

            if st.button(region, key=f"region_{ci}", use_container_width=True):
                for rr in region_list:
                    st.session_state[f"reg_exp_{rr}"] = False
                st.session_state[exp_key] = not is_open
                st.rerun()

            live_pct = int(int(rd["live"]) / int(rd["count"]) * 100) if int(rd["count"]) else 0
            border_c = rd["color"] if is_open else "#F1F3FB"
            bg = "#F7F8FD" if is_open else "#fff"
            radius = "14px 14px 0 0" if is_open else "14px"
            st.markdown(f'<div style="background:{bg};border:1px solid {border_c};border-radius:{radius};padding:16px 22px;margin:-14px 0 {"0" if is_open else "6"}px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                        f'<div style="display:flex;align-items:center;gap:16px;">'
                        f'<div style="width:40px;height:40px;border-radius:10px;background:{rd["color"]}10;display:flex;align-items:center;justify-content:center;border:1px solid {rd["color"]}20;">'
                        f'<div style="width:10px;height:10px;border-radius:50%;background:{rd["color"]};"></div></div>'
                        f'<div><div style="font-size:14px;font-weight:700;color:#10131C;letter-spacing:-0.3px;">{region}</div>'
                        f'<div style="font-size:11px;color:#858CA6;margin-top:1px;">{rd["count"]} partners &middot; {rd["live"]} live &middot; {rd["revshare"]}</div></div></div>'
                        f'<div style="display:flex;align-items:center;gap:14px;">'
                        f'<div style="text-align:right;"><div style="font-size:14px;font-weight:700;color:{rd["color"]};">{live_pct}%</div>'
                        f'<div style="font-size:10px;color:#858CA6;">live</div></div>'
                        f'<div style="width:60px;height:5px;background:#F1F3FB;border-radius:3px;overflow:hidden;"><div style="width:{live_pct}%;height:100%;background:{rd["color"]};border-radius:3px;"></div></div>'
                        f'<span style="font-size:18px;color:{rd["color"] if is_open else "#D2D7EA"};font-weight:200;">{"−" if is_open else "+"}</span>'
                        f'</div></div></div>', unsafe_allow_html=True)

            if is_open:
                st.markdown(f'<div style="background:{bg};border:1px solid {rd["color"]};border-top:none;border-radius:0 0 14px 14px;padding:4px 22px 22px;margin:0 0 6px;">', unsafe_allow_html=True)

                st.markdown(f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:12px 0 14px;border-bottom:1px solid #E9ECFC;">'
                            f'<div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:1px solid #F1F3FB;"><div style="font-size:18px;font-weight:700;color:#10131C;">{rd["count"]}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;">Total</div></div>'
                            f'<div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:1px solid #F1F3FB;"><div style="font-size:18px;font-weight:700;color:#5A7A00;">{rd["live"]}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;">Live</div></div>'
                            f'<div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:1px solid #F1F3FB;"><div style="font-size:18px;font-weight:700;color:#8B9BFF;">{rd["strategic"]}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;">Strategic</div></div>'
                            f'<div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:1px solid #F1F3FB;"><div style="font-size:18px;font-weight:700;color:#B36200;">{rd["tier1"]}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;">Tier 1</div></div>'
                            f'<div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:1px solid #F1F3FB;"><div style="font-size:18px;font-weight:700;color:{rd["color"]};">{rd["revshare"]}</div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;">Rev Share</div></div>'
                            f'</div>', unsafe_allow_html=True)

                # Offering mix + Pipeline
                col_o, col_p = st.columns(2)
                with col_o:
                    mix_bars = ""
                    total_mix = sum(rd["offering_mix"].values())
                    for cat, val in sorted(rd["offering_mix"].items(), key=lambda x: -x[1]):
                        pct = int(val / total_mix * 100)
                        mix_bars += (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                                     f'<span style="font-size:11px;color:#676E8A;min-width:65px;">{cat}</span>'
                                     f'<div style="flex:1;height:8px;background:#E9ECFC;border-radius:4px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{rd["color"]},{rd["color"]}88);border-radius:4px;"></div></div>'
                                     f'<span style="font-size:11px;font-weight:700;color:#10131C;min-width:24px;text-align:right;">{val}</span></div>')
                    st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:16px 18px;margin-top:14px;">'
                                f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px;">Offering Mix</div>'
                                f'{mix_bars}</div>', unsafe_allow_html=True)
                with col_p:
                    pipe_stages = [("Prospect","#858CA6"),("Negotiation","#B36200"),("Review","#3E4FE0"),("Signed","#5A6486"),("Live","#5A7A00")]
                    pipe_bars = ""
                    for stage, scolor in pipe_stages:
                        val = rd["pipeline"].get(stage, 0)
                        max_v = max(rd["pipeline"].values()) if rd["pipeline"] else 1
                        pct = int(val / max_v * 100) if max_v else 0
                        pipe_bars += (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                                      f'<span style="font-size:11px;color:#676E8A;min-width:65px;">{stage}</span>'
                                      f'<div style="flex:1;height:8px;background:#F1F3FB;border-radius:4px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:{scolor};border-radius:4px;"></div></div>'
                                      f'<span style="font-size:11px;font-weight:700;color:#10131C;min-width:24px;text-align:right;">{val}</span></div>')
                    st.markdown(f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:16px 18px;margin-top:14px;">'
                                f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px;">Pipeline Stage</div>'
                                f'{pipe_bars}</div>', unsafe_allow_html=True)

                trends_html = "".join(f'<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:{rd["color"]};flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">{t}</span></div>' for t in rd["trends"])
                country_pills = " ".join(f'<span style="font-size:11px;font-weight:600;padding:6px 14px;border-radius:8px;background:#fff;color:#10131C;border:1px solid #F1F3FB;">{c}</span>' for c in rd["countries"])
                st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;">'
                            f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:16px 18px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Market Trends</div>'
                            f'{trends_html}</div>'
                            f'<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:16px 18px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Key Markets</div>'
                            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">{country_pills}</div></div>'
                            f'</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

        # Style region toggle buttons to be invisible (card above handles visuals)
        components.html("""<script>
setTimeout(function(){
  var doc = window.parent.document;
  var main = doc.querySelector('[data-testid="stMainBlockContainer"]');
  if(!main) return;
  main.querySelectorAll('button').forEach(function(btn){
    var t = btn.textContent.trim();
    var regions = ['LATAM','Brasil','MENAT','APAC','Europe','North America','Africa'];
    if(regions.indexOf(t) !== -1){
      btn.style.cssText = 'width:100% !important;background:none !important;border:none !important;box-shadow:none !important;padding:0 !important;margin:0 !important;height:1px !important;min-height:0 !important;opacity:0 !important;cursor:pointer !important;position:absolute !important;z-index:10 !important;';
    }
  });
},200);
</script>""", height=0)

        # ── Global Insights Report ────────────────────────────────────────────
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin:28px 0 16px;">
  <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,#E2E6F4,transparent);"></div>
  <span style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;">Global Payments Landscape</span>
  <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,#E2E6F4,transparent);"></div>
</div>""", unsafe_allow_html=True)

        # Industry snapshot
        st.markdown("""
<div style="background:linear-gradient(160deg,#080911,#10131C,#141827);border-radius:14px;padding:28px 30px;margin-bottom:14px;">
  <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:16px;">Industry Snapshot — 2026</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
    <div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:20px;font-weight:700;color:#8B9BFF;">$8.5T</div>
      <div style="font-size:10px;color:#676E8A;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">Global eComm Volume</div>
    </div>
    <div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:20px;font-weight:700;color:#3FA8C4;">62%</div>
      <div style="font-size:10px;color:#676E8A;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">Digital Wallet Share</div>
    </div>
    <div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:20px;font-weight:700;color:#D08A1A;">$1.2T</div>
      <div style="font-size:10px;color:#676E8A;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">BNPL Market</div>
    </div>
    <div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:20px;font-weight:700;color:#D9737F;">14%</div>
      <div style="font-size:10px;color:#676E8A;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">YoY Growth</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # Two columns: eComm trends + POS trends
        col_ec, col_pos = st.columns(2)
        with col_ec:
            st.markdown("""
<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:20px;">
  <div style="font-size:12px;font-weight:700;color:#10131C;margin-bottom:14px;">eCommerce Trends</div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#3E4FE0;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">Digital wallets overtook cards as #1 global eComm payment method in 2025</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#3E4FE0;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">A2A / real-time payments (PIX, UPI, SEPA Instant) are the fastest-growing rail globally</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#3E4FE0;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">BNPL adoption accelerating in MENAT (+18% CAGR) and LATAM (+22% CAGR)</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;"><span style="width:6px;height:6px;border-radius:50%;background:#3E4FE0;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">Cross-border eCommerce growing 2x faster than domestic — orchestration is key</span></div>
</div>""", unsafe_allow_html=True)
        with col_pos:
            st.markdown("""
<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:20px;">
  <div style="font-size:12px;font-weight:700;color:#10131C;margin-bottom:14px;">POS & In-Store Trends</div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#5A7A00;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">Contactless payments represent 75%+ of in-store transactions in Europe and APAC</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#5A7A00;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">QR code payments dominating LATAM and SEA — PIX QR, PromptPay, GCash</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #F7F8FD;"><span style="width:6px;height:6px;border-radius:50%;background:#5A7A00;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">Tap-to-Pay on phone (SoftPOS) eliminating hardware dependency for SMEs</span></div>
  <div style="display:flex;gap:8px;padding:8px 0;"><span style="width:6px;height:6px;border-radius:50%;background:#5A7A00;flex-shrink:0;margin-top:6px;"></span><span style="font-size:12px;color:#3A4155;line-height:1.6;">Unified commerce (online + POS) is becoming table stakes for enterprise merchants</span></div>
</div>""", unsafe_allow_html=True)

        # Yuno coverage summary
        acq_ct = sum(1 for p in PARTNERS_DATA if p["cat"] == "Acquirer" and p["status"] == "Live")
        psp_ct = sum(1 for p in PARTNERS_DATA if p["cat"] == "PSP" and p["status"] == "Live")
        apm_ct = sum(1 for p in PARTNERS_DATA if p["cat"] == "APM" and p["status"] == "Live")
        fraud_ct = sum(1 for p in PARTNERS_DATA if p["cat"] == "Fraud" and p["status"] == "Live")
        sot_live_providers = len(_SOT_DF[_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live"]["PROVIDER_NAME"].unique()) if len(_SOT_DF) > 0 else 0
        sot_live_countries = len(_SOT_DF[_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live"]["COUNTRY_ISO"].unique()) if len(_SOT_DF) > 0 else 0
        sot_pm_count = len(_SOT_DF[_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live"]["PAYMENT_METHOD_TYPE"].unique()) if len(_SOT_DF) > 0 else 0

        st.markdown(f"""
<div style="background:#fff;border:1px solid #F1F3FB;border-radius:12px;padding:22px;margin-top:12px;">
  <div style="font-size:12px;font-weight:700;color:#10131C;margin-bottom:16px;">What Yuno Has Integrated</div>
  <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px;">
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#5A6486;">{sot_live_providers}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">LIVE PROVIDERS</div></div>
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#5A7A00;">{sot_live_countries}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">COUNTRIES</div></div>
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#3E4FE0;">{sot_pm_count}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">PAYMENT METHODS</div></div>
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#5A6486;">{acq_ct}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">ACQUIRERS</div></div>
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#3E4FE0;">{psp_ct}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">PSPs</div></div>
    <div style="text-align:center;padding:12px;background:#F7F8FD;border-radius:10px;"><div style="font-size:16px;font-weight:700;color:#0086A8;">{apm_ct}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">APMs</div></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
    <div style="padding:12px 16px;background:#E9ECFC;border-radius:10px;border:1px solid #D6DCFA;">
      <div style="font-size:11px;font-weight:700;color:#3E4FE0;margin-bottom:4px;">Orchestration Layer</div>
      <div style="font-size:12px;color:#3A4155;line-height:1.5;">Yuno routes transactions across multiple providers per country — enabling smart retries, cost optimization, and approval rate maximization through a single API.</div>
    </div>
    <div style="padding:12px 16px;background:#F4F8E4;border-radius:10px;border:1px solid #E7F0C4;">
      <div style="font-size:11px;font-weight:700;color:#3F5208;margin-bottom:4px;">Integration Speed</div>
      <div style="font-size:12px;color:#3A4155;line-height:1.5;">New payment providers can be integrated in under 30 days. Merchants connect once to Yuno and gain access to the entire partner ecosystem — no additional development required.</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        return

    # ── Find ISO + run search ─────────────────────────────────────────────────
    country_iso = None
    for iso, name in _ISO_TO_COUNTRY.items():
        if name == selected_country:
            country_iso = iso
            break

    verticals_filter = [selected_vertical] if selected_vertical != "All Verticals" else None
    proc_filter = selected_proc if selected_proc != "Any" else None
    results = find_partners(country_iso=country_iso, verticals=verticals_filter, live_only=live_only, processing_type=proc_filter)
    v_label = selected_vertical if selected_vertical != "All Verticals" else "all verticals"

    # ── Results header ────────────────────────────────────────────────────────
    st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:18px 22px;margin:8px 0 12px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div><div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1px;">Results for {selected_country}</div>'
                f'<div style="font-size:20px;font-weight:700;color:#10131C;margin-top:2px;">{len(results)} partner{"s" if len(results)!=1 else ""} found</div>'
                f'<div style="font-size:12px;color:#676E8A;margin-top:2px;">{v_label}</div></div>'
                f'<div style="font-size:48px;font-weight:700;color:#3E4FE0;opacity:0.1;">{len(results)}</div></div></div>', unsafe_allow_html=True)

    if not results:
        st.markdown('<div style="border:1px solid #E6CE7A;border-radius:10px;padding:24px;background:#FDF8E8;text-align:center;">'
                    '<div style="font-size:14px;font-weight:600;color:#6E3C00;">No partners match this combination</div>'
                    '<div style="font-size:13px;color:#8A4B00;margin-top:4px;">Try broadening your filters.</div></div>', unsafe_allow_html=True)
        return

    # ── Results with inline expandable profiles ───────────────────────────────
    CAT_LABELS = {"ACQUIRER":"Acquirer","GATEWAY":"PSP/Gateway","AGREGATOR":"Aggregator","AGREGATOR / GATEWAY":"Aggregator/Gateway","PAYMENT_METHOD":"APM"}

    for idx, r in enumerate(results):
        cat_label = CAT_LABELS.get(r["categories"][0], r["categories"][0]) if r["categories"] else ""
        pm_display = ", ".join(r["payment_methods"][:5])
        if len(r["payment_methods"]) > 5:
            pm_display += f" +{len(r['payment_methods'])-5}"
        proc_display = " / ".join(r["processing_types"])
        rank_color = "#3E4FE0" if idx < 3 else "#858CA6"
        s_bg = "#F4F8E4" if r["status"] == "Live" else "#F7F8FD"
        s_color = "#3F5208" if r["status"] == "Live" else "#676E8A"

        # Card header
        st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:14px 20px;margin-top:6px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                    f'<div style="display:flex;align-items:center;gap:10px;">'
                    f'<span style="font-size:15px;font-weight:700;color:{rank_color};">#{idx+1}</span>'
                    f'<span style="font-size:14px;font-weight:700;color:#10131C;">{r["name"]}</span>'
                    f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:4px;background:#EFF1F9;color:#464F6E;">{cat_label}</span></div>'
                    f'<span style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;background:{s_bg};color:{s_color};">{r["status"]}</span></div>'
                    f'<div style="display:grid;grid-template-columns:1fr 2fr 1fr;gap:8px;">'
                    f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Processing</div><div style="font-size:12px;font-weight:600;color:#10131C;">{proc_display}</div></div>'
                    f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Payment Methods</div><div style="font-size:12px;color:#676E8A;">{pm_display}</div></div>'
                    f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Countries</div><div style="font-size:12px;font-weight:600;color:#10131C;">{r["countries_count"]}</div></div>'
                    f'</div></div>', unsafe_allow_html=True)

        # Expand button (Streamlit native — clean toggle)
        enrich_key = r["name"].upper().replace("(","").replace(")","").strip()
        enrich = _PARTNER_ENRICHMENT.get(enrich_key)

        exp_key = f'exp_{r["name"]}'
        is_expanded = st.session_state.get(exp_key, False)
        arrow = "▾" if is_expanded else "▸"
        btn_label = f"{arrow} {r['name']} — Details"
        if st.button(btn_label, key=f"btn_exp_{idx}", use_container_width=True):
            st.session_state[exp_key] = not is_expanded
            st.rerun()

        if is_expanded:
            feat_map = {"SUPPORTS_TOKENIZATION":"Tokenization","SUPPORTS_RECURRING_PAYMENTS":"Recurring","SUPPORTS_PAYOUTS":"Payouts","SUPPORTS_INSTALLMENTS":"Installments","SUPPORTS_PAYFAC":"PayFac","SUPPORTS_SPLIT_PAYMENTS":"Split Pay","3DS":"3D Secure"}
            on_pills = " ".join(f'<span style="font-size:10px;padding:3px 8px;border-radius:4px;background:#F4F8E4;color:#3F5208;">{v}</span>' for k,v in feat_map.items() if r["supports"].get(k))
            off_pills = " ".join(f'<span style="font-size:10px;padding:3px 8px;border-radius:4px;background:#F7F8FD;color:#D2D7EA;text-decoration:line-through;">{v}</span>' for k,v in feat_map.items() if not r["supports"].get(k))

            if enrich:
                h_color = "#3F5208" if enrich["health"] == "Strong" else "#B36200" if enrich["health"] == "Good" else "#858CA6"
                h_bg = "#F4F8E4" if enrich["health"] == "Strong" else "#FDF8E8" if enrich["health"] == "Good" else "#F7F8FD"

                # Integrated features
                st.markdown(f'<div style="background:#F7F8FD;border:1px solid #E2E6F4;border-radius:10px;padding:18px 20px;margin:-4px 0 4px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Yuno Integrated Capabilities</div>'
                            f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{on_pills} {off_pills}</div></div>', unsafe_allow_html=True)

                # Detail grid — contacts + commercial
                dc1, dc2 = st.columns(2)
                with dc1:
                    _pkey = r["name"].upper().replace("(","").replace(")","").strip()
                    _ec = _EXT_CONTACTS.get(_pkey, {})
                    _cl = _ec.get("commercial_contact","") or enrich["commercial_contact"]
                    _tl = _ec.get("technical_contact","") or enrich["technical_contact"]
                    _ce = _ec.get("commercial_email","")
                    _te = _ec.get("technical_email","")
                    _ev = _ec.get("verticals","") or enrich["verticals"]
                    _cl_line = f'{_cl}<br><span style="font-size:10px;color:#676E8A;">{_ce}</span>' if _ce else _cl
                    _tl_line = f'{_tl}<br><span style="font-size:10px;color:#676E8A;">{_te}</span>' if _te else _tl
                    st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:18px 20px;">'
                                f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px;">Contacts & Verticals</div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Commercial Lead</div><div style="font-size:13px;font-weight:600;color:#10131C;">{_cl_line}</div></div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Technical Lead</div><div style="font-size:13px;font-weight:600;color:#10131C;">{_tl_line}</div></div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Focus Verticals</div><div style="font-size:12px;color:#3A4155;">{_ev}</div></div>'
                                f'<div><div style="font-size:10px;color:#858CA6;">Rev Share</div><div style="font-size:13px;font-weight:600;color:#10131C;">{enrich["revshare"]}</div></div>'
                                f'</div>', unsafe_allow_html=True)
                with dc2:
                    st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:18px 20px;">'
                                f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px;">Pricing & Onboarding</div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Standard Rate</div><div style="font-size:13px;font-weight:600;color:#10131C;">{enrich["avg_pricing"]}</div></div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Discounted Rate</div><div style="font-size:13px;font-weight:700;color:#3F5208;">{enrich["discount_rate"]}</div></div>'
                                f'<div style="margin-bottom:10px;"><div style="font-size:10px;color:#858CA6;">Discount Condition</div><div style="font-size:12px;color:#3A4155;">{enrich["discount_condition"]}</div></div>'
                                f'<div><div style="font-size:10px;color:#858CA6;">Onboarding</div><div style="font-size:12px;color:#3A4155;">{enrich["onboarding"]}</div></div>'
                                f'</div>', unsafe_allow_html=True)

                # Health + merchants bar
                st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:14px 20px;margin-bottom:4px;">'
                            f'<div style="display:flex;gap:20px;align-items:center;">'
                            f'<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:10px;color:#858CA6;">Health</span><span style="font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;background:{h_bg};color:{h_color};">{enrich["health"]}</span></div>'
                            f'<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:10px;color:#858CA6;">Live Merchants</span><span style="font-size:13px;font-weight:700;color:#10131C;">{enrich["merchants_live"]}</span></div>'
                            f'<div style="flex:1;display:flex;align-items:center;gap:6px;"><span style="font-size:10px;color:#858CA6;">Merchants</span><span style="font-size:12px;color:#3A4155;">{enrich["merchants"]}</span></div>'
                            f'</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#F7F8FD;border:1px solid #E2E6F4;border-radius:10px;padding:18px 20px;margin:-4px 0 4px;">'
                            f'<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Yuno Integrated Capabilities</div>'
                            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">{on_pills} {off_pills}</div>'
                            f'<div style="font-size:12px;color:#858CA6;">Full commercial profile pending — contact partnerships team.</div></div>', unsafe_allow_html=True)

    # Style detail toggle buttons
    components.html("""<script>
setTimeout(function(){
  var doc = window.parent.document;
  doc.querySelectorAll('button').forEach(function(btn){
    var t = btn.textContent.trim();
    if(t.includes('— Details')){
      btn.style.cssText='background:none !important;border:1px solid #E2E6F4 !important;border-radius:8px !important;padding:6px 16px !important;margin:-2px 0 2px !important;font-size:11px !important;color:#3E4FE0 !important;font-weight:600 !important;cursor:pointer !important;box-shadow:none !important;text-align:left !important;';
    }
  });
},300);
</script>""", height=0)

    # Summary insight
    top3 = [r["name"] for r in results[:3]]
    has_local = any("LOCAL" in r.get("processing_types",[]) for r in results[:3])
    st.markdown(f'<div style="background:linear-gradient(135deg,#F7F8FD,#EFF1F9);border:1px solid #E2E6F4;border-radius:10px;padding:18px 22px;margin-top:16px;">'
                f'<div style="font-size:11px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Recommendation</div>'
                f'<div style="font-size:14px;color:#10131C;line-height:1.6;">For <strong>{selected_country}</strong> ({v_label}), your top options are <strong>{", ".join(top3)}</strong>. '
                f'{"These partners offer local processing with established merchant volume." if has_local else "Consider cross-border routing for initial testing before local entity setup."}'
                f'</div></div>', unsafe_allow_html=True)

    # ── Market Intelligence (MENAT insights from PPTX) ────────────────────────
    _MARKET_INSIGHTS = {
        "Saudi Arabia": {
            "tier": "Tier 1", "tier_color": "#3F5208", "tier_bg": "#F4F8E4",
            "population": "36M", "ecomm_size": "$13.3B", "ecomm_growth": "12.5%",
            "smartphone": "97%", "internet": "99%",
            "digital_trends": [
                "Vision 2030 targets cashless economy",
                "Surge in online fashion, electronics, and food delivery post-pandemic",
                "Saudis spend ~$7B/year buying goods from cross-border e-commerce merchants",
            ],
            "pro_tips": [
                "MADA is the national debit scheme — mandatory for local card acceptance",
                "SARIE (A2A) delivers cost savings and eliminates chargeback exposure",
                "BNPL via Tamara/Tabby is becoming a standard checkout expectation",
            ],
            "key_verticals": ["Electronics", "Fashion", "Health & Beauty", "Groceries & Deliveries"],
            "local_methods": ["MADA", "SARIE", "Tamara", "Tabby", "Apple Pay", "STC Pay"],
        },
        "United Arab Emirates": {
            "tier": "Tier 1", "tier_color": "#3F5208", "tier_bg": "#F4F8E4",
            "population": "10M", "ecomm_size": "$8B", "ecomm_growth": "11%",
            "smartphone": "96%", "internet": "99%",
            "digital_trends": [
                "Credit cards dominant in eCommerce, wallets rising fast",
                "New local card rail Jaywan emerging",
                "BNPL becoming standard checkout expectation",
            ],
            "pro_tips": [
                "Local entity or free zone setup is required to operate",
                "~90% of population are expats — extremely diverse payment preferences",
                "Arabic RTL checkout support is expected, not optional",
            ],
            "key_verticals": ["Electronics", "Fashion", "Health & Beauty", "Groceries", "Baby Products"],
            "local_methods": ["Jaywan", "AANI", "Tamara", "Tabby", "Apple Pay"],
        },
        "Turkey": {
            "tier": "Tier 1", "tier_color": "#3F5208", "tier_bg": "#F4F8E4",
            "population": "86M", "ecomm_size": "$28B", "ecomm_growth": "6.5% of GDP",
            "smartphone": "92%", "internet": "88%",
            "digital_trends": [
                "eCommerce scaling to ~$45B by 2030, 6.5% of GDP (highest in region)",
                "Consumers expect 3/6/12-month installment splits — primary driver of card dominance",
                "With ~39% inflation, BNPL and installments are survival tools, not convenience",
            ],
            "pro_tips": [
                "Turkey mandates data localization for payment data, BDDK/CBT licensing required",
                "TROY must be enabled alongside Visa & Mastercard — skipping it increases costs and declines",
                "FAST (A2A) delivers meaningful savings while removing dispute exposure",
            ],
            "key_verticals": ["Electronics", "Beauty", "Fashion", "Food Delivery", "Gaming"],
            "local_methods": ["TROY", "FAST", "BKM Express", "Papara"],
        },
        "Qatar": {
            "tier": "Tier 2", "tier_color": "#464F6E", "tier_bg": "#EFF1F9",
            "population": "3M", "ecomm_size": "$3.8B", "ecomm_growth": "10.3%",
            "smartphone": "95%", "internet": "99%",
            "digital_trends": [
                "eCommerce growing at 9.31% CAGR, transactions up 15% YoY",
                "Digital economy pillar of Qatar National Vision 2030",
                "69% of eCommerce revenue comes via smartphones, 5G covers 99% of population",
            ],
            "pro_tips": [
                "Qatar is small — Doha covers majority of merchant customer base",
                "BNPL growing at 18%+ CAGR, directly lifts AOV",
                "Winning checkout must cover cards, Fawran and digital wallets",
            ],
            "key_verticals": ["Electronics", "Beauty", "Fashion", "Food Delivery", "Travel"],
            "local_methods": ["NAPS", "Fawran", "QMP", "Dynamic QR"],
        },
        "Kuwait": {
            "tier": "Tier 2", "tier_color": "#464F6E", "tier_bg": "#EFF1F9",
            "population": "4.3M", "ecomm_size": "$1.85B", "ecomm_growth": "5.5%",
            "smartphone": "98%", "internet": "99%",
            "digital_trends": [
                "KNET national debit network used in ~80% of all online transactions",
                "WAMD instant payments processed $1.5B across 5.4M txns in launch month",
                "eCommerce projected to reach $2.42B by 2030",
            ],
            "pro_tips": [
                "KNET is non-negotiable — local debit network supported by all 11 national banks",
                "Add WAMD for instant A2A payments — brand new and growing rapidly",
                "Younger demographics actively seek BNPL installment options",
            ],
            "key_verticals": ["Electronics", "Beauty", "Fashion", "Home & Furniture", "Groceries"],
            "local_methods": ["KNET", "WAMD", "Tamara", "Tabby"],
        },
        "Bahrain": {
            "tier": "Tier 2", "tier_color": "#464F6E", "tier_bg": "#EFF1F9",
            "population": "1.5M", "ecomm_size": "$1.2B", "ecomm_growth": "8%",
            "smartphone": "92%", "internet": "99%",
            "digital_trends": [
                "BenefitPay holds 46.8% of eCommerce payment share — highest wallet dominance in GCC",
                "Cash on Delivery fallen below 10% — lowest in GCC",
                "Two-thirds of all transactions happen via mobile",
            ],
            "pro_tips": [
                "Integrate BenefitPay — it's the market's payment spine (debit, QR, A2A, direct debit)",
                "BNPL reduces abandonment and increases AOV simultaneously",
                "Don't assume GCC incorporation elsewhere automatically covers Bahrain operations",
            ],
            "key_verticals": ["Electronics", "Beauty", "Fashion", "Home & Furniture", "Food Delivery"],
            "local_methods": ["BENEFIT", "Fawri+", "Tamara", "Tabby"],
        },
        "Egypt": {
            "tier": "Tier 3", "tier_color": "#6E3C00", "tier_bg": "#FDF8E8",
            "population": "106M", "ecomm_size": "$10B", "ecomm_growth": "25%",
            "smartphone": "78%", "internet": "72%",
            "digital_trends": [
                "eCommerce scaling to ~$19B by 2030",
                "Cash on Delivery remains dominant at ~45-50%",
                "Digital wallets surging: 50-55M active e-wallets, 80% YoY volume growth",
            ],
            "pro_tips": [
                "Multi-wallet integration is mandatory, not optional",
                "InstaPay (A2A) is maturing — low cost and high adoption",
                "Currency devaluation impacts consumer purchasing power and merchant economics",
                "Incentivize digital payments at checkout to convert CoD users",
            ],
            "key_verticals": ["Electronics", "Food Delivery", "Grocery", "Pharmacy", "Home & Furniture"],
            "local_methods": ["MEEZA", "InstaPay", "Fawry", "Vodafone Cash"],
        },
        "Iraq": {
            "tier": "High Risk", "tier_color": "#C4384A", "tier_bg": "#FDF1F2",
            "population": "47M", "ecomm_size": "$780M", "ecomm_growth": "11.2%",
            "smartphone": "87%", "internet": "83%",
            "digital_trends": [
                "Over $15B+ in electronic transactions processed last year",
                "CBI launched National Financial Inclusion Strategy 2025-2029",
                "Fewer than 20% hold a formal bank account, 85% of eCommerce is cash",
            ],
            "pro_tips": [
                "Millions receive salaries via QiCard — leverage this as a competitive advantage",
                "E-wallets are essential given low banked population, not just a convenience",
                "Offer intelligent retries across PSPs and wallets given infrastructure instability",
            ],
            "key_verticals": ["Electronics", "Beauty", "Fashion", "Home & Appliances", "Daily Essentials"],
            "local_methods": ["QiCard", "Zain Cash", "IPS"],
        },
    }

    market = _MARKET_INSIGHTS.get(selected_country)
    if market:
        # Market overview card
        st.markdown(f'<div style="margin-top:24px;margin-bottom:8px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;">Market Intelligence</div></div>', unsafe_allow_html=True)

        # Hero stats bar
        st.markdown(f'<div style="background:linear-gradient(135deg,#10131C,#262C3E);border-radius:12px;padding:28px 32px;margin-bottom:12px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">'
                    f'<div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:-0.5px;">{selected_country}</div>'
                    f'<span style="font-size:10px;font-weight:700;padding:4px 14px;border-radius:20px;background:{market["tier_bg"]};color:{market["tier_color"]};">{market["tier"]}</span>'
                    f'</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">'
                    f'<div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#fff;">{market["population"]}</div><div style="font-size:10px;color:#676E8A;margin-top:2px;">Population</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#8B9BFF;">{market["ecomm_size"]}</div><div style="font-size:10px;color:#676E8A;margin-top:2px;">eCommerce Size</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#3FA8C4;">{market["ecomm_growth"]}</div><div style="font-size:10px;color:#676E8A;margin-top:2px;">Growth Rate</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#fff;">{market["smartphone"]}</div><div style="font-size:10px;color:#676E8A;margin-top:2px;">Smartphone</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#fff;">{market["internet"]}</div><div style="font-size:10px;color:#676E8A;margin-top:2px;">Internet</div></div>'
                    f'</div></div>', unsafe_allow_html=True)

        # Two-column: Digital Trends + Pro Tips
        col_t, col_p = st.columns(2)
        with col_t:
            trends_html = "".join(f'<div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #F1F3FB;"><span style="color:#8B9BFF;font-size:14px;flex-shrink:0;">&#9672;</span><span style="font-size:13px;color:#3A4155;line-height:1.5;">{t}</span></div>' for t in market["digital_trends"])
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:20px;height:100%;">'
                        f'<div style="font-size:13px;font-weight:700;color:#10131C;margin-bottom:12px;">Digital Trends</div>'
                        f'{trends_html}</div>', unsafe_allow_html=True)
        with col_p:
            tips_html = "".join(f'<div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #F1F3FB;"><span style="color:#B36200;font-size:12px;flex-shrink:0;font-weight:700;">TIP</span><span style="font-size:13px;color:#3A4155;line-height:1.5;">{t}</span></div>' for t in market["pro_tips"])
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:20px;height:100%;">'
                        f'<div style="font-size:13px;font-weight:700;color:#10131C;margin-bottom:12px;">Pro Tips</div>'
                        f'{tips_html}</div>', unsafe_allow_html=True)

        # Bottom row: Verticals + Local Payment Methods
        col_v, col_m = st.columns(2)
        with col_v:
            vert_pills = " ".join(f'<span style="font-size:11px;font-weight:600;padding:6px 14px;border-radius:8px;background:#F7F8FD;color:#3A4155;border:1px solid #E2E6F4;">{v}</span>' for v in market["key_verticals"])
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:20px;margin-top:10px;">'
                        f'<div style="font-size:13px;font-weight:700;color:#10131C;margin-bottom:12px;">Key eCommerce Verticals</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{vert_pills}</div></div>', unsafe_allow_html=True)
        with col_m:
            # Check which methods Yuno has available via which partner
            method_items = []
            for m in market["local_methods"]:
                # Search SOT for this payment method in this country
                m_upper = m.upper().replace(" ","_")
                matches = _SOT_DF[(_SOT_DF["COUNTRY_ISO"] == country_iso) & (_SOT_DF["PAYMENT_METHOD_TYPE"].str.upper().str.contains(m_upper, na=False)) & (_SOT_DF["Live/NonLive Partner/Contract signed"] == "Live")]
                if len(matches) > 0:
                    via_partner = matches["PROVIDER_NAME"].iloc[0]
                    method_items.append(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #F1F3FB;">'
                                        f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:8px;height:8px;border-radius:50%;background:#5A7A00;flex-shrink:0;"></span>'
                                        f'<span style="font-size:13px;font-weight:600;color:#10131C;">{m}</span></div>'
                                        f'<span style="font-size:11px;color:#3F5208;font-weight:600;">via {via_partner}</span></div>')
                else:
                    # Check non-live
                    matches_nl = _SOT_DF[(_SOT_DF["COUNTRY_ISO"] == country_iso) & (_SOT_DF["PAYMENT_METHOD_TYPE"].str.upper().str.contains(m_upper, na=False))]
                    if len(matches_nl) > 0:
                        via_partner = matches_nl["PROVIDER_NAME"].iloc[0]
                        method_items.append(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #F1F3FB;">'
                                            f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:8px;height:8px;border-radius:50%;background:#B36200;flex-shrink:0;"></span>'
                                            f'<span style="font-size:13px;font-weight:600;color:#10131C;">{m}</span></div>'
                                            f'<span style="font-size:11px;color:#6E3C00;font-weight:600;">pipeline — {via_partner}</span></div>')
                    else:
                        method_items.append(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #F1F3FB;">'
                                            f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:8px;height:8px;border-radius:50%;background:#C4384A;flex-shrink:0;"></span>'
                                            f'<span style="font-size:13px;font-weight:600;color:#10131C;">{m}</span></div>'
                                            f'<span style="font-size:11px;color:#C4384A;font-weight:600;">not available</span></div>')
            methods_html = "".join(method_items)
            available_ct = sum(1 for m in market["local_methods"] if any(m.upper().replace(" ","_") in str(row).upper() for row in _SOT_DF[(_SOT_DF["COUNTRY_ISO"]==country_iso)&(_SOT_DF["Live/NonLive Partner/Contract signed"]=="Live")]["PAYMENT_METHOD_TYPE"].dropna().values))
            coverage_pct = int(available_ct / len(market["local_methods"]) * 100) if market["local_methods"] else 0
            cov_color = "#3F5208" if coverage_pct >= 70 else "#B36200" if coverage_pct >= 40 else "#C4384A"
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:10px;padding:20px;margin-top:10px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
                        f'<div style="font-size:13px;font-weight:700;color:#10131C;">Must-Have Payment Methods</div>'
                        f'<span style="font-size:11px;font-weight:700;color:{cov_color};">{coverage_pct}% covered</span></div>'
                        f'{methods_html}</div>', unsafe_allow_html=True)


# ── Partners In Flight ─────────────────────────────────────────────────────────
_MC_STAGES = [
    {"id":"prospect","label":"Prospect","short":"PROS","owner":"Partnership BD","owner_color":"#858CA6","desc":"Market assessment, initial contact, opportunity identification"},
    {"id":"negotiation","label":"Negotiation","short":"NEG","owner":"Partnership BD","owner_color":"#3E4FE0","desc":"Commercial terms discussion, pricing alignment, scope definition"},
    {"id":"agreement","label":"Agreement Review","short":"AGR","owner":"Partnerships + Legal","owner_color":"#3E4FE0","desc":"NDA review, contract drafting, compliance checks, legal sign-off"},
    {"id":"agreement_signed","label":"Agreement Signed","short":"SIGN","owner":"Partnerships + Legal","owner_color":"#2F3FC4","desc":"Contract executed, ready for prioritization"},
    {"id":"prioritized","label":"Prioritized","short":"PRI","owner":"Product + Partnerships","owner_color":"#00697F","desc":"Roadmap slot confirmed, resources allocated, kickoff planned"},
    {"id":"in_development","label":"In Development","short":"DEV","owner":"Integrations","owner_color":"#5A6486","desc":"API integration, sandbox testing, certification in progress"},
    {"id":"integration_complete","label":"Development Complete","short":"QA","owner":"Integrations","owner_color":"#48610A","desc":"Testing passed, sandbox certified, ready for production"},
    {"id":"go_live","label":"Go Live","short":"LIVE","owner":"Merchant BD/KAM + Partnerships + Product","owner_color":"#5A7A00","desc":"Production deployment, merchant activation, initial transaction flow"},
    {"id":"pilot","label":"Pilot Phase","short":"PILOT","owner":"Merchant BD/KAM + Partnerships","owner_color":"#B36200","desc":"First merchant onboarding, volume ramp, performance validation"},
    {"id":"g2m","label":"Go to Market","short":"G2M","owner":"Marketing + Partnerships","owner_color":"#C4384A","desc":"Joint GTM campaigns, co-marketing, case studies, press releases"},
    {"id":"live_processing","label":"Live & Processing","short":"LIVE+","owner":"Partnership Account Mgmt","owner_color":"#3F5208","desc":"Active volume, rev share collecting, ongoing optimization"},
]

def _map_deal_stage_to_mc(row):
    """Map Excel deal stage + integration columns to mission control stage."""
    stage = str(row.get("Deal Stage","")).strip()
    int_ready = bool(row.get("Integration Ready by Yuno", False))
    int_used = bool(row.get("Integration Used by Merchants", False))
    revshare_active = bool(row.get("Revshare active", False))
    nda = bool(row.get("NDA Signed and in drive", False))
    revshare_contract = bool(row.get("Revshare Contract", False))
    mgmt = str(row.get("Type of Management","")).strip()

    if stage == "Live Partner" and int_used and revshare_active:
        return 10  # live_processing
    elif stage == "Live Partner" and int_used:
        return 9  # g2m
    elif stage == "Live Partner" and int_ready:
        return 8  # pilot
    elif stage == "Live Partner":
        return 7  # go_live
    elif stage == "Agreement Signed" and int_ready:
        return 6  # integration_complete
    elif stage == "Agreement Signed" and nda:
        return 5  # in_development
    elif stage == "Agreement Signed":
        return 4  # prioritized
    elif stage == "Agreement Review":
        return 2  # agreement review
    elif stage == "Initial Negotiation":
        return 1  # negotiation
    elif stage == "Opportunity Identification":
        return 0  # prospect
    else:
        return 0

def _get_pending_task(row, stage_idx):
    """Determine who currently holds the ball and what's pending."""
    nda = bool(row.get("NDA Signed and in drive", False))
    revshare = bool(row.get("Revshare Contract", False))
    int_ready = bool(row.get("Integration Ready by Yuno", False))

    if stage_idx == 0:
        return ("Partnership BD", "Qualify opportunity & initial outreach")
    elif stage_idx == 1:
        return ("Partnership BD", "Align commercial terms & pricing")
    elif stage_idx == 2:
        if not nda:
            return ("Legal", "NDA pending signature")
        return ("Legal", "Contract under review")
    elif stage_idx == 3:
        return ("Partnerships + Legal", "Awaiting final contract sign-off")
    elif stage_idx == 4:
        return ("Product", "Awaiting roadmap slot & resource allocation")
    elif stage_idx == 5:
        return ("Integrations", "API integration in progress")
    elif stage_idx == 6:
        return ("Integrations", "QA certification & sandbox testing")
    elif stage_idx == 7:
        return ("Merchant BD/KAM", "Production go-live & merchant activation")
    elif stage_idx == 8:
        return ("Merchant BD/KAM", "First merchant onboarding & volume ramp")
    elif stage_idx == 9:
        return ("Marketing + Partnerships", "GTM campaigns, co-marketing & case studies")
    elif stage_idx == 10:
        if not revshare:
            return ("Partnership BD", "Rev share contract pending")
        return ("Partnership Acct Mgmt", "Ongoing management & optimization")
    return ("—", "—")

@st.cache_data
def load_mission_control_data():
    try:
        df = pd.read_excel(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "strategic_accounts.xlsx"), sheet_name="All partners")
        strat = df[df["Strategic?"] == True].drop_duplicates(subset="Provider")
        partners = []
        for _, row in strat.iterrows():
            name = str(row.get("Provider","")).strip()
            if not name or name == "nan":
                continue
            mc_stage = _map_deal_stage_to_mc(row)
            pending_owner, pending_task = _get_pending_task(row, mc_stage)
            partners.append({
                "name": name,
                "region": str(row.get("Region","")).strip(),
                "country": str(row.get("Country","")).strip(),
                "manager": str(row.get("Partner Manager","")).strip(),
                "offering": str(row.get("Partner offering (acquirer, APM, Fraud etc)","")).strip(),
                "mgmt_type": str(row.get("Type of Management","")).strip(),
                "stage_idx": mc_stage,
                "deal_stage": str(row.get("Deal Stage","")).strip(),
                "nda": bool(row.get("NDA Signed and in drive", False)),
                "int_ready": bool(row.get("Integration Ready by Yuno", False)),
                "int_used": bool(row.get("Integration Used by Merchants", False)),
                "revshare": bool(row.get("Revshare Contract", False)),
                "revshare_active": bool(row.get("Revshare active", False)),
                "pending_owner": pending_owner,
                "pending_task": pending_task,
            })
        return sorted(partners, key=lambda x: (-x["stage_idx"], x["name"]))
    except Exception:
        return []

def show_mission_control():
    mc_data = load_mission_control_data()

    # Build JSON for HTML component
    import json as _json
    _mc_json = _json.dumps(mc_data).replace("'", "\\'").replace("</", "<\\/")

    _html_file = _os.path.join(_BASE, "partners_in_flight.html")
    with open(_html_file, "r") as _f:
        _html_content = _f.read()
    _html_content = _html_content.replace("var DATA = [];", f"var DATA = {_mc_json};")
    components.html(_html_content, height=1800, scrolling=True)
    return

    # ── OLD CODE (kept for reference) ─────────────────────────────────────────
    stage_counts = [0] * len(_MC_STAGES)
    for p in mc_data:
        stage_counts[p["stage_idx"]] += 1
    total_mc = len(mc_data)
    live_mc = stage_counts[10] if len(stage_counts) > 10 else 0
    in_dev = stage_counts[5] + stage_counts[6] if len(stage_counts) > 6 else 0

    st.markdown(f"""
<div style="background:#080911;border-radius:16px;padding:24px 28px;margin-bottom:14px;position:relative;overflow:hidden;">
  <div style="position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,0.03) 1px,transparent 0);background-size:22px 22px;pointer-events:none;"></div>
  <div style="position:relative;z-index:1;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
      <span style="width:6px;height:6px;border-radius:50%;background:#5A7A00;"></span>
      <span style="font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#8FA300;">Live Tracker</span>
    </div>
    <div style="font-size:20px;font-weight:700;color:#F1F3FB;letter-spacing:-0.02em;margin-bottom:4px;">Partners In Flight</div>
    <div style="font-size:12px;color:#676E8A;margin-bottom:14px;">End-to-end lifecycle of every strategic partner — from prospect to live processing.</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#B9C2FF;">{total_mc}</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Strategic</div></div>
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#E0ED80;">{live_mc}</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">Live</div></div>
      <div style="background:rgba(255,255,255,0.04);border:0.5px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;text-align:center;"><div style="font-size:16px;font-weight:700;color:#8B9BFF;">{in_dev}</div><div style="font-size:10px;color:#4A5170;text-transform:uppercase;margin-top:2px;">In Dev</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Region toggles ────────────────────────────────────────────────────────
    mc_regions = sorted(set(p["region"] for p in mc_data if p["region"] and p["region"] != "nan"))
    _region_colors = {"Global":"#3E4FE0","LATAM":"#3E4FE0","Brasil":"#5A7A00","EMEA":"#3E4FE0","APAC":"#0086A8","North America":"#48610A","Africa":"#B36200"}

    sel_region = st.session_state.get("mc_region_sel", "All")
    region_opts = ["All"] + mc_regions
    reg_cols = st.columns(len(region_opts))
    for ri, rname in enumerate(region_opts):
        rcount = len([p for p in mc_data if p["region"] == rname]) if rname != "All" else total_mc
        if reg_cols[ri].button(f"{rname} ({rcount})", key=f"mc_reg_{ri}", use_container_width=True):
            st.session_state["mc_region_sel"] = rname
            st.rerun()

    # Style region buttons
    components.html(f"""<script>
setTimeout(function(){{
  var doc = window.parent.document;
  var active = '{sel_region}';
  doc.querySelectorAll('button').forEach(function(btn){{
    var t = btn.textContent.trim();
    if(t.match(/^(All|Global|LATAM|Brasil|EMEA|APAC|North America|Africa)\s*\(/)){{
      var isOn = t.startsWith(active+' (') || (active==='All' && t.startsWith('All ('));
      btn.style.cssText='background:'+(isOn?'#080911':'#fff')+' !important;border:1px solid '+(isOn?'#3E4FE0':'#E2E6F4')+' !important;border-radius:8px !important;padding:8px 10px !important;font-size:11px !important;color:'+(isOn?'#8B9BFF':'#676E8A')+' !important;font-weight:'+(isOn?'700':'500')+' !important;cursor:pointer !important;box-shadow:none !important;';
    }}
  }});
}},200);
</script>""", height=0)

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        mc_owners = sorted(set(p["manager"] for p in mc_data if p["manager"] and p["manager"] != "nan"))
        mc_owner_filter = st.selectbox("Manager", ["Manager"] + mc_owners, key="mc_owner_f", label_visibility="collapsed")
    with col_f2:
        active_stage_filter = st.selectbox("Stage", ["Stage"] + [s["label"] for s in _MC_STAGES], key="mc_stage_sel", label_visibility="collapsed")

    # ── Filter logic ──────────────────────────────────────────────────────────
    filtered = list(mc_data)
    if sel_region != "All":
        filtered = [p for p in filtered if p["region"] == sel_region]
    if mc_owner_filter != "Manager":
        filtered = [p for p in filtered if p["manager"] == mc_owner_filter]
    if active_stage_filter != "Stage":
        stage_idx = next((i for i, s in enumerate(_MC_STAGES) if s["label"] == active_stage_filter), -1)
        if stage_idx >= 0:
            filtered = [p for p in filtered if p["stage_idx"] == stage_idx]

    # ── Pipeline progress bar ─────────────────────────────────────────────────
    filt_counts = [0] * len(_MC_STAGES)
    for p in filtered:
        filt_counts[p["stage_idx"]] += 1
    vis_total = sum(filt_counts) or 1
    bar_html = '<div style="display:flex;gap:1px;height:6px;margin:10px 0 14px;border-radius:3px;overflow:hidden;">'
    for si, s in enumerate(_MC_STAGES):
        w = max(int(filt_counts[si] / vis_total * 100), 1) if filt_counts[si] > 0 else 0
        if w > 0:
            bar_html += f'<div style="width:{w}%;background:{s["owner_color"]};"></div>'
    bar_html += '</div>'
    st.markdown(bar_html, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:12px;color:#858CA6;margin-bottom:8px;"><b style="color:#10131C;">{len(filtered)}</b> partners</div>', unsafe_allow_html=True)

    # ── Partner list by stage (expanders) ─────────────────────────────────────
    owner_colors = {"Legal":"#3E4FE0","Partnership BD":"#3E4FE0","Partnerships + Legal":"#2F3FC4","Product":"#00697F","Integrations":"#5A6486","Merchant BD/KAM":"#B36200","Marketing + Partnerships":"#C4384A","Partnership Acct Mgmt":"#3F5208"}

    for si, s in enumerate(_MC_STAGES):
        partners_in_stage = [p for p in filtered if p["stage_idx"] == si]
        if not partners_in_stage:
            continue

        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:12px 0 4px;padding-bottom:4px;border-bottom:2px solid {s["owner_color"]}20;">'
                    f'<span style="font-size:13px;font-weight:700;color:#10131C;">{s["label"]}</span>'
                    f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:5px;background:{s["owner_color"]}10;color:{s["owner_color"]};">{s["owner"]}</span>'
                    f'<span style="margin-left:auto;font-size:12px;font-weight:700;color:#10131C;">{len(partners_in_stage)}</span></div>', unsafe_allow_html=True)

        for p in partners_in_stage:
            po = p.get("pending_owner", "")
            pt = p.get("pending_task", "")
            po_color = owner_colors.get(po, "#858CA6")
            checks = [("NDA", p["nda"]), ("Int", p["int_ready"]), ("Merch", p["int_used"]), ("Rev$", p["revshare"])]
            ch = " ".join(f'<span style="font-size:10px;padding:1px 5px;border-radius:3px;background:{"#F4F8E4" if v else "#F7F8FD"};color:{"#3F5208" if v else "#D2D7EA"};">{l}</span>' for l, v in checks)

            with st.expander(f"{p['name']}  ·  {p['offering']}  ·  {p['region']}  ·  {p['manager']}", expanded=False):
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
                            f'<span style="font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;background:{po_color}10;color:{po_color};border:0.5px solid {po_color}20;">{po}</span>'
                            f'<span style="font-size:11px;color:#676E8A;">{pt}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="display:flex;gap:3px;margin-bottom:8px;">{ch}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Country</div><div style="font-size:12px;font-weight:600;color:#10131C;">{p["country"]}</div></div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Deal Stage</div><div style="font-size:12px;font-weight:600;color:#10131C;">{p["deal_stage"]}</div></div>'
                            f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;">Management</div><div style="font-size:12px;font-weight:600;color:#10131C;">{p.get("mgmt_type","—")}</div></div>'
                            f'</div>', unsafe_allow_html=True)


# ── Merchant Simulation ──────────────────────────────────────────────────────
_MERCHANT_PROFILES = {
    "uber":      {"name":"Uber","sector":"Mobility & Delivery","countries":["MX","BR","CO","AR","CL"],"aov":18.2,"txn_mo":323000,"ar":93.4,"methods":["Card Visa","Card Mastercard","PIX","OXXO","Nequi"],"providers":["Adyen","dLocal","Stripe"],"color":"#10131C"},
    "rappi":     {"name":"Rappi","sector":"Super App / Delivery","countries":["CO","MX","BR","CL","PE"],"aov":32.5,"txn_mo":259000,"ar":91.2,"methods":["Card Visa","Card Mastercard","PSE","Nequi","PIX","OXXO"],"providers":["Adyen","Kushki","MercadoPago"],"color":"#FF5722"},
    "netflix":   {"name":"Netflix","sector":"Streaming / Subscriptions","countries":["US","MX","BR","AR","CO"],"aov":15.5,"txn_mo":306000,"ar":95.6,"methods":["Card Visa","Card Mastercard","Amex"],"providers":["Stripe","Adyen","dLocal"],"color":"#E50914"},
    "spotify":   {"name":"Spotify","sector":"Streaming / Subscriptions","countries":["BR","MX","AR","CO","CL"],"aov":9.99,"txn_mo":421000,"ar":94.8,"methods":["Card Visa","Card Mastercard","PIX","Boleto"],"providers":["Adyen","Ebanx","dLocal"],"color":"#1DB954"},
    "mercadolibre":{"name":"MercadoLibre","sector":"Marketplace / eCommerce","countries":["AR","BR","MX","CO","CL"],"aov":118.4,"txn_mo":61000,"ar":88.7,"methods":["Card Visa","Card Mastercard","PIX","Boleto","MercadoPago"],"providers":["MercadoPago","Adyen","Cielo"],"color":"#FFE600"},
    "falabella": {"name":"Falabella","sector":"Retail / eCommerce","countries":["CL","CO","PE","AR"],"aov":87.3,"txn_mo":35000,"ar":87.1,"methods":["Card Visa","Card Mastercard","Webpay","PSE"],"providers":["Transbank","Kushki","Adyen"],"color":"#009900"},
    "ifood":     {"name":"iFood","sector":"Food Delivery","countries":["BR"],"aov":28.4,"txn_mo":103000,"ar":91.8,"methods":["Card Visa","Card Mastercard","PIX","Boleto"],"providers":["Cielo","PagBank","Stone"],"color":"#EA1D2C"},
    "despegar":  {"name":"Despegar","sector":"Travel / OTA","countries":["AR","BR","MX","CO","CL"],"aov":312.5,"txn_mo":12000,"ar":82.3,"methods":["Card Visa","Card Mastercard","Amex","PIX","Installments"],"providers":["Cybersource","Adyen","dLocal"],"color":"#0066CC"},
}

_OPTIMIZATION_TIPS = {
    "low_ar": {"title":"Approval Rate Below 90%","desc":"Enable smart retries across multiple acquirers. Route declines to a secondary provider — this alone can recover 3-5% of failed transactions.","impact":"+3-5% approval rate"},
    "single_provider": {"title":"Single Provider Risk","desc":"Relying on one provider creates a single point of failure. Add a backup acquirer for failover routing and cost negotiation leverage.","impact":"+99.9% uptime, -15% processing cost"},
    "no_apm": {"title":"Missing Local Payment Methods","desc":"Offer local APMs (PIX in Brazil, OXXO in Mexico, PSE in Colombia). Merchants see 15-25% conversion lift when local methods are available.","impact":"+15-25% conversion"},
    "no_installments": {"title":"No Installment Options","desc":"In LATAM, 60%+ of card transactions use installments. Enable parcelamento/MSI to unlock higher AOV and reduce cart abandonment.","impact":"+20% AOV"},
    "high_aov": {"title":"High-AOV Without Fraud Layer","desc":"Transactions above $100 need a fraud prevention layer. Add 3DS and a fraud partner (SEON, Riskified) to reduce chargebacks.","impact":"-40% chargebacks"},
    "cross_border": {"title":"Cross-Border Processing","desc":"Local acquiring delivers 8-12% higher approval rates vs cross-border. Establish local entity or use a provider with local acquiring license.","impact":"+8-12% approval rate"},
}

def show_merchant_sim():
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(160deg,#080911 0%,#080911 40%,#141827 100%);border-radius:20px;padding:44px 44px 36px;margin-bottom:4px;position:relative;overflow:hidden;">
  <div style="position:absolute;top:-60px;right:-40px;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,rgba(209,78,0,0.1),transparent 65%);"></div>
  <div style="position:relative;z-index:1;">
    <div style="display:inline-flex;align-items:center;gap:8px;padding:4px 14px;border-radius:20px;background:rgba(209,78,0,0.12);border:1px solid rgba(209,78,0,0.2);margin-bottom:16px;">
      <span style="font-size:14px;">◇</span>
      <span style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#B9C2FF;">Merchant Simulation</span>
    </div>
    <div style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.8px;line-height:1.2;margin-bottom:8px;">Simulate. Optimize. Close.</div>
    <div style="font-size:13px;color:#858CA6;line-height:1.7;max-width:520px;">Enter a merchant name to generate a checkout flow mockup, identify payment optimization opportunities, and model the revenue impact of adding new Yuno partners to their stack.</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Search bar ────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:#fff;border:1px solid #E2E6F4;border-radius:0 0 20px 20px;padding:18px 28px 10px;margin-bottom:16px;box-shadow:0 8px 32px rgba(0,0,0,0.04);">
  <div style="font-size:10px;font-weight:700;color:#3E4FE0;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:4px;">Enter merchant name</div>
</div>""", unsafe_allow_html=True)

    merchant_input = st.text_input("Merchant name", placeholder="e.g. Uber, Rappi, Netflix, Spotify, Falabella...", key="merchsim_input", label_visibility="collapsed")

    # Use quick-select override if set
    active_merchant = merchant_input or st.session_state.get("merchsim_selected", "")

    if not active_merchant:
        # Landing state
        st.markdown("""
<div style="border:1px solid #E2E6F4;border-radius:14px;padding:48px 40px;text-align:center;background:#fff;margin-top:4px;">
  <div style="font-size:36px;margin-bottom:14px;opacity:0.2;">◇</div>
  <div style="font-size:18px;font-weight:700;color:#10131C;margin-bottom:8px;">Enter a merchant to begin</div>
  <div style="font-size:13px;color:#858CA6;max-width:440px;margin:0 auto;line-height:1.6;">Type a merchant name above. We'll generate their checkout flow, flag optimization gaps, and let you model the impact of adding new payment partners.</div>
</div>""", unsafe_allow_html=True)

        # Quick select
        st.markdown('<div style="font-size:10px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1px;margin:20px 0 8px;">Quick select</div>', unsafe_allow_html=True)
        qcols = st.columns(4)
        for qi, (mkey, mdata) in enumerate(list(_MERCHANT_PROFILES.items())[:8]):
            if qcols[qi % 4].button(mdata["name"], key=f"qs_{mkey}", use_container_width=True):
                st.session_state["merchsim_selected"] = mdata["name"]
                st.rerun()

        components.html("""<script>
setTimeout(function(){
  var doc = window.parent.document;
  var names = ['Uber','Rappi','Netflix','Spotify','MercadoLibre','Falabella','iFood','Despegar'];
  doc.querySelectorAll('button').forEach(function(btn){
    if(names.indexOf(btn.textContent.trim()) !== -1){
      btn.style.cssText='background:#E9ECFC !important;border:1px solid #D6DCFA !important;border-radius:10px !important;padding:10px !important;font-size:13px !important;color:#2F3FC4 !important;font-weight:700 !important;cursor:pointer !important;box-shadow:none !important;';
    }
  });
},250);
</script>""", height=0)
        return
    else:
        # Clear quick-select if user typed something
        if merchant_input:
            st.session_state["merchsim_selected"] = ""

    # ── Find merchant profile ─────────────────────────────────────────────────
    # Back button if loaded via quick-select
    if st.session_state.get("merchsim_selected"):
        if st.button("← Back to merchant select", key="merchsim_back"):
            st.session_state["merchsim_selected"] = ""
            st.rerun()

    m_key = active_merchant.lower().replace(" ", "")
    profile = _MERCHANT_PROFILES.get(m_key)

    if not profile:
        # Generate a generic profile
        profile = {
            "name": active_merchant, "sector": "eCommerce", "countries": ["BR","MX","CO"],
            "aov": 45.0, "txn_mo": 50000, "ar": 88.0,
            "methods": ["Card Visa","Card Mastercard"],
            "providers": ["Adyen"], "color": "#3E4FE0",
        }

    m = profile
    tpv_mo = m["aov"] * m["txn_mo"]
    tpv_display = f"${tpv_mo/1e6:.1f}M" if tpv_mo >= 1e6 else f"${tpv_mo/1e3:.0f}K"
    country_names = [_ISO_TO_COUNTRY.get(c, c) for c in m["countries"]]

    # ── Merchant header ───────────────────────────────────────────────────────
    st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:22px 26px;margin-bottom:14px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div style="display:flex;align-items:center;gap:16px;">'
                f'<div style="width:48px;height:48px;border-radius:12px;background:{m["color"]};display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;color:#fff;">{m["name"][0]}</div>'
                f'<div><div style="font-size:18px;font-weight:700;color:#10131C;letter-spacing:-0.5px;">{m["name"]}</div>'
                f'<div style="font-size:12px;color:#858CA6;margin-top:1px;">{m["sector"]} &middot; {", ".join(country_names)}</div></div></div>'
                f'<div style="display:flex;gap:12px;">'
                f'<div style="text-align:center;"><div style="font-size:16px;font-weight:700;color:#10131C;">{tpv_display}</div><div style="font-size:10px;color:#858CA6;">TPV/mo</div></div>'
                f'<div style="text-align:center;"><div style="font-size:16px;font-weight:700;color:#10131C;">${m["aov"]:.0f}</div><div style="font-size:10px;color:#858CA6;">AOV</div></div>'
                f'<div style="text-align:center;"><div style="font-size:16px;font-weight:700;color:{"#5A7A00" if m["ar"]>=90 else "#B36200" if m["ar"]>=85 else "#C4384A"};">{m["ar"]}%</div><div style="font-size:10px;color:#858CA6;">Auth Rate</div></div>'
                f'<div style="text-align:center;"><div style="font-size:16px;font-weight:700;color:#10131C;">{m["txn_mo"]:,}</div><div style="font-size:10px;color:#858CA6;">Txn/mo</div></div>'
                f'</div></div></div>', unsafe_allow_html=True)

    # ── Checkout Flow Mockup ──────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;margin:8px 0 10px;">Checkout Flow Simulation</div>', unsafe_allow_html=True)

    steps = [
        ("Cart","Customer adds items","#858CA6"),
        ("Checkout","Selects payment method","#3E4FE0"),
        ("Auth","Transaction processed","#B36200"),
        ("3DS","Identity verified","#3E4FE0"),
        ("Approve","Payment confirmed","#5A7A00"),
    ]
    steps_html = ""
    for si, (step, desc, scolor) in enumerate(steps):
        arrow = '<div style="font-size:15px;color:#D2D7EA;margin:0 4px;">&#8594;</div>' if si < len(steps)-1 else ""
        steps_html += f'<div style="display:flex;align-items:center;gap:0;"><div style="text-align:center;padding:14px 16px;background:#fff;border:1px solid #E2E6F4;border-radius:12px;min-width:100px;"><div style="font-size:13px;font-weight:700;color:{scolor};">{step}</div><div style="font-size:10px;color:#858CA6;margin-top:2px;">{desc}</div></div>{arrow}</div>'
    st.markdown(f'<div style="display:flex;align-items:center;justify-content:center;gap:0;padding:16px;background:#F7F8FD;border:1px solid #E2E6F4;border-radius:14px;margin-bottom:14px;">{steps_html}</div>', unsafe_allow_html=True)

    # Payment methods mockup
    methods_html = "".join(f'<div style="display:flex;align-items:center;gap:8px;padding:10px 14px;background:#fff;border:1px solid #E2E6F4;border-radius:10px;"><span style="width:8px;height:8px;border-radius:50%;background:#5A7A00;"></span><span style="font-size:12px;font-weight:600;color:#10131C;">{pm}</span></div>' for pm in m["methods"])
    providers_html = "".join(f'<span style="font-size:11px;font-weight:600;padding:5px 14px;border-radius:8px;background:#E9ECFC;color:#3E4FE0;border:1px solid #D6DCFA;">{pv}</span>' for pv in m["providers"])

    col_pm, col_pv = st.columns(2)
    with col_pm:
        st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:18px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Active Payment Methods</div>'
                    f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{methods_html}</div></div>', unsafe_allow_html=True)
    with col_pv:
        st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:18px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Current Providers</div>'
                    f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{providers_html}</div></div>', unsafe_allow_html=True)

    # ── Optimization Tips ─────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;margin:20px 0 10px;">Optimization Opportunities</div>', unsafe_allow_html=True)

    # Determine which tips apply
    tips = []
    if m["ar"] < 90:
        tips.append(_OPTIMIZATION_TIPS["low_ar"])
    if len(m["providers"]) <= 1:
        tips.append(_OPTIMIZATION_TIPS["single_provider"])
    if not any(pm in ["PIX","OXXO","PSE","Nequi","Boleto"] for pm in m["methods"]):
        tips.append(_OPTIMIZATION_TIPS["no_apm"])
    if "Installments" not in " ".join(m["methods"]) and m["aov"] > 30:
        tips.append(_OPTIMIZATION_TIPS["no_installments"])
    if m["aov"] > 100:
        tips.append(_OPTIMIZATION_TIPS["high_aov"])
    if len(m["countries"]) > 2 and len(m["providers"]) < 3:
        tips.append(_OPTIMIZATION_TIPS["cross_border"])
    if not tips:
        tips.append({"title":"Well Optimized","desc":"This merchant has a solid payment setup. Consider fine-tuning routing rules and exploring new markets for growth.","impact":"Maintain & grow"})

    for tip in tips:
        st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:16px 20px;margin-bottom:8px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                    f'<div style="flex:1;"><div style="font-size:14px;font-weight:700;color:#10131C;margin-bottom:4px;">{tip["title"]}</div>'
                    f'<div style="font-size:12px;color:#676E8A;line-height:1.6;">{tip["desc"]}</div></div>'
                    f'<span style="font-size:11px;font-weight:700;padding:4px 12px;border-radius:8px;background:#F4F8E4;color:#3F5208;white-space:nowrap;margin-left:16px;">{tip["impact"]}</span>'
                    f'</div></div>', unsafe_allow_html=True)

    # ── Partner Impact Simulator ──────────────────────────────────────────────
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:#858CA6;text-transform:uppercase;letter-spacing:1.5px;margin:24px 0 10px;">Partner Impact Simulator</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:12px;color:#676E8A;margin-bottom:10px;">Add a payment partner and see the projected impact on this merchant.</div>', unsafe_allow_html=True)

    col_add, col_country = st.columns(2)
    with col_add:
        add_options = ["Select a partner..."] + _SOT_PROVIDERS[:50]
        add_partner = st.selectbox("Add Partner", add_options, key="sim_add_partner", label_visibility="collapsed")
    with col_country:
        sim_country = st.selectbox("Target Country", [""] + _SOT_COUNTRIES, key="sim_country",
                                   format_func=lambda x: "Select country..." if x == "" else x, label_visibility="collapsed")

    if add_partner != "Select a partner..." and sim_country:
        # Find partner capabilities
        sim_iso = None
        for iso, name in _ISO_TO_COUNTRY.items():
            if name == sim_country:
                sim_iso = iso
                break

        sim_results = find_partners(country_iso=sim_iso, live_only=False) if sim_iso else []
        partner_match = next((r for r in sim_results if r["name"].upper() == add_partner.upper()), None)

        # Projected impact
        ar_boost = 3.5 if len(m["providers"]) <= 1 else 1.8
        new_ar = min(m["ar"] + ar_boost, 99.5)
        recovered_txn = int(m["txn_mo"] * (ar_boost / 100))
        revenue_gain = recovered_txn * m["aov"]
        rev_display = f"${revenue_gain/1e3:.0f}K" if revenue_gain >= 1000 else f"${revenue_gain:.0f}"

        st.markdown(f'<div style="background:linear-gradient(160deg,#080911,#10131C);border-radius:14px;padding:24px 28px;margin-top:10px;">'
                    f'<div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:16px;">Projected Impact: Adding {add_partner} in {sim_country}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">'
                    f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);"><div style="font-size:20px;font-weight:700;color:#5A7A00;">{new_ar:.1f}%</div><div style="font-size:10px;color:#676E8A;margin-top:3px;">New Auth Rate</div><div style="font-size:10px;color:#5A7A00;margin-top:2px;">+{ar_boost:.1f}%</div></div>'
                    f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);"><div style="font-size:20px;font-weight:700;color:#8B9BFF;">{recovered_txn:,}</div><div style="font-size:10px;color:#676E8A;margin-top:3px;">Recovered Txns/mo</div><div style="font-size:10px;color:#8B9BFF;margin-top:2px;">previously declined</div></div>'
                    f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);"><div style="font-size:20px;font-weight:700;color:#D08A1A;">{rev_display}</div><div style="font-size:10px;color:#676E8A;margin-top:3px;">Revenue Recovered/mo</div><div style="font-size:10px;color:#D08A1A;margin-top:2px;">from retries</div></div>'
                    f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);"><div style="font-size:20px;font-weight:700;color:#fff;">{len(m["providers"])+1}</div><div style="font-size:10px;color:#676E8A;margin-top:3px;">Total Providers</div><div style="font-size:10px;color:#5A7A00;margin-top:2px;">redundancy added</div></div>'
                    f'</div></div>', unsafe_allow_html=True)

        # Partner details if found
        if partner_match:
            pm_list = ", ".join(partner_match["payment_methods"][:5])
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:16px 20px;margin-top:8px;">'
                        f'<div style="font-size:12px;font-weight:700;color:#10131C;margin-bottom:8px;">{add_partner} in {sim_country}</div>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">'
                        f'<div><div style="font-size:10px;color:#858CA6;">Status</div><div style="font-size:13px;font-weight:600;color:#10131C;">{partner_match["status"]}</div></div>'
                        f'<div><div style="font-size:10px;color:#858CA6;">Payment Methods</div><div style="font-size:12px;color:#3A4155;">{pm_list}</div></div>'
                        f'<div><div style="font-size:10px;color:#858CA6;">Processing</div><div style="font-size:13px;font-weight:600;color:#10131C;">{" / ".join(partner_match["processing_types"])}</div></div>'
                        f'</div></div>', unsafe_allow_html=True)

        # Before/After comparison
        st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">'
                    f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:12px;padding:16px 20px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#C4384A;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Before</div>'
                    f'<div style="margin-bottom:6px;"><span style="font-size:12px;color:#858CA6;">Auth Rate</span><span style="font-size:14px;font-weight:700;color:#10131C;float:right;">{m["ar"]}%</span></div>'
                    f'<div style="margin-bottom:6px;"><span style="font-size:12px;color:#858CA6;">Providers</span><span style="font-size:14px;font-weight:700;color:#10131C;float:right;">{len(m["providers"])}</span></div>'
                    f'<div><span style="font-size:12px;color:#858CA6;">Failed Txns/mo</span><span style="font-size:14px;font-weight:700;color:#C4384A;float:right;">{int(m["txn_mo"]*(1-m["ar"]/100)):,}</span></div>'
                    f'</div>'
                    f'<div style="background:#fff;border:1px solid #E7F0C4;border-radius:12px;padding:16px 20px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#5A7A00;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">After (Projected)</div>'
                    f'<div style="margin-bottom:6px;"><span style="font-size:12px;color:#858CA6;">Auth Rate</span><span style="font-size:14px;font-weight:700;color:#5A7A00;float:right;">{new_ar:.1f}%</span></div>'
                    f'<div style="margin-bottom:6px;"><span style="font-size:12px;color:#858CA6;">Providers</span><span style="font-size:14px;font-weight:700;color:#10131C;float:right;">{len(m["providers"])+1}</span></div>'
                    f'<div><span style="font-size:12px;color:#858CA6;">Failed Txns/mo</span><span style="font-size:14px;font-weight:700;color:#5A7A00;float:right;">{int(m["txn_mo"]*(1-new_ar/100)):,}</span></div>'
                    f'</div></div>', unsafe_allow_html=True)


# ── Home / Welcome Panel ────────────────────────────────────────────────────────
# ── Market Expansion ───────────────────────────────────────────────────────────
def _chip(text, kind="data"):
    """Provenance chip. Every number on this page wears one."""
    c = {"data":   ("#E9ECFC", "#2F3FC4", "rgba(84,104,245,.22)"),
         "assume": ("#FDF8E8", "#8A4B00", "rgba(138,106,0,.28)"),
         "market": ("#DDEFF4", "#00697F", "rgba(0,105,127,.25)")}[kind]
    return (f'<span style="display:inline-flex;align-items:center;font-family:var(--font);font-variant-numeric:tabular-nums;'
            f'font-size:10px;font-weight:500;letter-spacing:.02em;padding:2px 7px;border-radius:5px;'
            f'background:{c[0]};color:{c[1]};border:1px solid {c[2]};white-space:nowrap;">{text}</span>')


def show_expansion():
    is_internal = st.session_state.role == "internal"
    who = "partner" if not is_internal else "customer"

    st.markdown(hero(
        "What changes if you launch this market with Yuno?",
        eyebrow="Market expansion simulator",
        subtitle=("Pick a market, add a provider, and see the modelled effect on approval, "
                  "declines and chargebacks — benchmarked against the merchants already "
                  "processing there.")), unsafe_allow_html=True)

    # ── 1. Who ────────────────────────────────────────────────────────────────
    st.markdown(_section_label("1 · Who is expanding", top=18), unsafe_allow_html=True)

    c1, c2 = st.columns([1.3, 1])
    with c1:
        names = {k: v["name"] for k, v in _MERCHANT_PROFILES.items()}
        pick = st.selectbox("Business", list(names) + ["__custom__"],
                            format_func=lambda k: "Custom profile…" if k == "__custom__" else names[k],
                            key="exp_merchant")
    with c2:
        vert = st.selectbox("Vertical exposure", ["None"] + list(_VERTICAL_COLS),
                            key="exp_vertical",
                            help="Filters the provider list to those that accept this vertical, "
                                 "per source_of_truth.xlsx.")

    if pick == "__custom__":
        d1, d2, d3, d4 = st.columns(4)
        merchant = {
            "name": d1.text_input("Business name", "Your business", key="exp_cname"),
            "sector": d2.text_input("Sector", "eCommerce", key="exp_csector"),
            "aov": d3.number_input("Average order (USD)", 1.0, 5000.0, 60.0, 1.0, key="exp_caov"),
            "txn_mo": d4.number_input("Transactions / month", 100, 5_000_000, 50_000, 1000, key="exp_ctxn"),
            "countries": [], "methods": ["Card Visa", "Card Mastercard"], "providers": ["Existing provider"],
        }
        merchant["ar"] = st.slider("Current approval rate (%)", 60.0, 99.0, 88.0, 0.1, key="exp_car")
    else:
        merchant = dict(_MERCHANT_PROFILES[pick], key=pick)

    # ── 2. Where ──────────────────────────────────────────────────────────────
    st.markdown(_section_label("2 · Target market", top=22), unsafe_allow_html=True)

    here = [m for m in _MARKET_PROFILES if market_iso(m) in merchant.get("countries", [])]
    new_markets = [m for m in _MARKET_PROFILES if m not in here]
    m1, m2 = st.columns([1, 2])
    with m1:
        market = st.selectbox("Market", new_markets + here, key="exp_market",
                              format_func=lambda m: f"{_MARKET_PROFILES[m].get('flag','')} {m}"
                                                    + ("  · already live" if m in here else ""))
    iso = market_iso(market)
    prof = _MARKET_PROFILES[market]
    with m2:
        st.markdown(
            f'<div style="display:flex;gap:22px;align-items:center;padding:13px 18px;background:#fff;'
            f'border:1px solid rgba(0,0,0,.075);border-radius:var(--r-ctl);margin-top:26px;">'
            + "".join(
                f'<div><div style="font-size:10px;color:#858CA6;text-transform:uppercase;'
                f'letter-spacing:.08em;font-weight:600;">{k}</div>'
                f'<div style="font-size:14px;font-weight:600;color:#10131C;font-family:var(--font);font-variant-numeric:tabular-nums;">{v}</div></div>'
                for k, v in [("Population", prof["population"]), ("eCommerce", prof["ecom_size"]),
                             ("Online share", prof["instore_online"].split("/")[0].strip())])
            + f'<div style="margin-left:auto;">{_chip("Market profile", "market")}</div></div>',
            unsafe_allow_html=True)

    # ── 3. Provider ───────────────────────────────────────────────────────────
    st.markdown(_section_label("3 · Provider to add", top=22), unsafe_allow_html=True)

    verticals = None if vert == "None" else [vert]
    live = market_providers(iso, verticals)
    if not live:
        st.markdown(
            f'<div style="padding:16px 18px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
            f'border-radius:var(--r-ctl);font-size:13px;color:#8A4B00;">'
            f'No live Yuno provider in <b>{market}</b> matches that vertical filter. '
            f'Clear the vertical, or talk to your Partner Manager about coverage here.</div>',
            unsafe_allow_html=True)
        return

    p1, p2 = st.columns([1.3, 1])
    with p1:
        chosen = st.multiselect(
            "Add provider(s)", [p["name"] for p in live],
            default=[live[0]["name"]], key="exp_providers",
            help="Only providers live in this market, read from source_of_truth.xlsx.")
    with p2:
        fraud = st.checkbox("Add a fraud layer (3DS + fraud provider)", value=False, key="exp_fraud")

    caps = {}
    for p in live:
        if p["name"] in chosen:
            for k, v in p["supports"].items():
                caps[k] = caps.get(k, False) or v

    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:2px 0 4px;">'
        f'{_chip(f"{len(live)} live providers in {iso}", "data")}'
        + "".join(_chip(lbl, "data") for lbl, k in
                  [("tokenisation", "SUPPORTS_TOKENIZATION"), ("recurring", "SUPPORTS_RECURRING_PAYMENTS"),
                   ("payouts", "SUPPORTS_PAYOUTS"), ("installments", "SUPPORTS_INSTALLMENTS"),
                   ("3DS", "3DS")] if caps.get(k))
        + '</div>', unsafe_allow_html=True)

    # ── Assumptions ───────────────────────────────────────────────────────────
    A = _assumption_defaults()
    with st.expander("Model assumptions — every uplift below comes from these", expanded=False):
        st.markdown('<div style="font-size:12px;color:#4A5170;line-height:1.6;margin-bottom:12px;">'
                    'These are assumptions, not measurements. Move them and every figure on the page '
                    'moves with them.</div>', unsafe_allow_html=True)
        ac = st.columns(2)
        for i, (key, (dflt, label, lo, hi, why)) in enumerate(_ASSUMPTIONS.items()):
            with ac[i % 2]:
                A[key] = st.slider(label, lo, hi, dflt, 0.5, key=f"exp_a_{key}", help=why)

    sim = simulate_expansion(merchant=merchant, market=market, added_providers=chosen,
                             assumptions=A, has_fraud_layer=fraud, provider_caps=caps)

    # ── Impact ────────────────────────────────────────────────────────────────
    st.markdown(_section_label(f'Impact on {merchant["name"]} in {market}', top=26),
                unsafe_allow_html=True)

    def tile(label, value, sub, chip, color="#3E4FE0"):
        return (f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);border-radius:14px;'
                f'padding:18px 20px;height:100%;">'
                f'<div style="font-size:10px;color:#858CA6;letter-spacing:.09em;text-transform:uppercase;'
                f'font-weight:600;margin-bottom:9px;">{label}</div>'
                f'<div style="font-size:22px;font-weight:600;font-family:var(--font);font-variant-numeric:tabular-nums;'
                f'letter-spacing:-.03em;line-height:1;color:{color};">{value}</div>'
                f'<div style="font-size:11px;color:#4A5170;margin:8px 0 10px;line-height:1.5;">{sub}</div>'
                f'{chip}</div>')

    t = st.columns(4)
    t[0].markdown(tile("Approval rate", f"{sim['ar1']:.1f}%",
                       f"from {sim['ar_entry']:.1f}% on entry · {sim['uplift_pp']:+.1f}pp vs today",
                       _chip("assumption", "assume")), unsafe_allow_html=True)
    t[1].markdown(tile("Declines recovered", f"{sim['recovered_txn']:,.0f}",
                       f"per month, of {sim['declines0']:,.0f} failing today",
                       _chip("assumption", "assume"), "#5A7A00"), unsafe_allow_html=True)
    t[2].markdown(tile("Revenue recovered", f"${sim['recovered_rev']:,.0f}",
                       f"per month · ${sim['annual_rev']:,.0f} annualised",
                       _chip("assumption", "assume"), "#5A7A00"), unsafe_allow_html=True)
    t[3].markdown(tile("Chargebacks", f"{sim['cb_bps1']:.0f} bps",
                       (f"−{sim['cb_avoided']:,.0f} cases/mo · ${sim['cb_cost_avoided']:,.0f} saved"
                        if fraud else "no fraud layer added — unchanged"),
                       _chip("assumption", "assume"),
                       "#5A7A00" if fraud else "#B36200"), unsafe_allow_html=True)

    # ── Where the uplift comes from ───────────────────────────────────────────
    b1, b2 = st.columns([1.15, 1])
    with b1:
        st.markdown('<div style="font-size:14px;font-weight:600;color:#10131C;margin:22px 0 4px;">'
                    'Where the uplift comes from</div>'
                    '<div style="font-size:11px;color:#676E8A;margin-bottom:10px;">'
                    'Each step is capped by the headroom left beneath the ceiling, so they never '
                    'sum past what is achievable.</div>', unsafe_allow_html=True)
        if sim["steps"]:
            fig = go.Figure(go.Bar(
                x=[s["pp"] for s in sim["steps"]], y=[s["label"] for s in sim["steps"]],
                orientation="h", marker_color="#3E4FE0", marker=dict(cornerradius=4),
                text=[f"+{s['pp']:.2f}pp" for s in sim["steps"]], textposition="outside",
                textfont=dict(size=10, color="#4A5170"),
                hovertext=[s["why"] for s in sim["steps"]],
                hovertemplate="%{y}: +%{x:.2f}pp<br>%{hovertext}<extra></extra>"))
            fig.update_layout(
                height=52 * len(sim["steps"]) + 70, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                font=dict(color="#4A5170", size=11),
                margin=dict(l=0, r=52, t=6, b=6), showlegend=False,
                xaxis=dict(title="", showgrid=True, gridcolor="#F1F3FB", zeroline=False,
                           ticksuffix="pp", range=[0, max(s["pp"] for s in sim["steps"]) * 1.32]),
                yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div style="padding:16px 18px;background:#F7F8FD;border:1px solid rgba(0,0,0,.075);'
                        'border-radius:var(--r-ctl);font-size:13px;color:#4A5170;">'
                        'Pick a provider above to model the uplift.</div>', unsafe_allow_html=True)

    with b2:
        st.markdown(f'<div style="font-size:14px;font-weight:600;color:#10131C;margin:22px 0 4px;">'
                    f'Local method coverage</div>'
                    f'<div style="font-size:11px;color:#676E8A;margin-bottom:10px;">'
                    f'You cover <b style="color:#10131C;">{sim["method_covered"]}%</b> of how '
                    f'{market} actually pays. {_chip("Market profile", "market")}</div>',
                    unsafe_allow_html=True)
        rows = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
            f'border-bottom:1px solid rgba(0,0,0,.055);">'
            f'<span style="width:7px;height:7px;border-radius:2px;flex:0 0 7px;'
            f'background:{"#5A7A00" if g["covered"] else "#C4384A"};"></span>'
            f'<span style="font-size:12px;color:#10131C;flex:1;">{g["method"]}</span>'
            f'<span style="font-family:var(--font);font-variant-numeric:tabular-nums;font-size:12px;color:#4A5170;">{g["share"]}%</span>'
            f'<span style="font-size:10px;font-weight:600;color:{"#5A7A00" if g["covered"] else "#C4384A"};'
            f'width:52px;text-align:right;">{"accepted" if g["covered"] else "missing"}</span></div>'
            for g in sim["method_gap"])
        st.markdown(f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);'
                    f'border-radius:14px;padding:6px 18px 10px;">{rows}</div>', unsafe_allow_html=True)

    # ── Competitor benchmark ──────────────────────────────────────────────────
    peers = competitor_benchmark(market, exclude=merchant.get("key"))
    st.markdown(_section_label(f"Who else processes in {market}", top=26),
                unsafe_allow_html=True)
    if peers:
        best = max(p["ar"] for p in peers)
        med = sorted(p["ar"] for p in peers)[len(peers) // 2]
        k1, k2 = st.columns([1.1, 1])
        with k1:
            allrows = peers + [dict(merchant, name=merchant["name"] + " (you, modelled)", ar=sim["ar1"])]
            allrows.sort(key=lambda m: m["ar"])
            fig2 = go.Figure(go.Bar(
                x=[m["ar"] for m in allrows], y=[m["name"] for m in allrows], orientation="h",
                marker_color=["#3E4FE0" if "(you" in m["name"] else "#B9C2FF" for m in allrows],
                marker=dict(cornerradius=4),
                text=[f"{m['ar']:.1f}%" for m in allrows], textposition="outside",
                textfont=dict(size=10, color="#4A5170"),
                hovertemplate="%{y}: %{x:.1f}% approval<extra></extra>"))
            fig2.update_layout(
                height=42 * len(allrows) + 60, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                font=dict(color="#4A5170", size=11),
                margin=dict(l=0, r=56, t=6, b=6), showlegend=False,
                xaxis=dict(range=[min(m["ar"] for m in allrows) - 6, 100], ticksuffix="%",
                           showgrid=True, gridcolor="#F1F3FB", zeroline=False))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        with k2:
            pos = ("ahead of every merchant we track here" if sim["ar1"] >= best
                   else "above the median" if sim["ar1"] >= med else "below the median")
            st.markdown(
                f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);border-radius:14px;'
                f'padding:20px;margin-top:22px;">'
                f'<div style="font-size:13px;color:#10131C;line-height:1.65;margin-bottom:14px;">'
                f'At <b>{sim["ar1"]:.1f}%</b> you would land <b>{pos}</b>. '
                f'The strongest here is <b>{max(peers, key=lambda p: p["ar"])["name"]}</b> at '
                f'{best:.1f}%; the median is {med:.1f}%.</div>'
                + "".join(
                    f'<div style="display:flex;gap:9px;align-items:center;padding:7px 0;'
                    f'border-top:1px solid rgba(0,0,0,.055);">'
                    f'<span style="width:8px;height:8px;border-radius:50%;flex:0 0 8px;background:{p["color"]};"></span>'
                    f'<span style="font-size:12px;color:#10131C;font-weight:500;flex:1;">{p["name"]}</span>'
                    f'<span style="font-size:11px;color:#676E8A;">{" · ".join(p["providers"][:2])}</span></div>'
                    for p in peers[:6])
                + f'<div style="margin-top:12px;">{_chip("Merchant profiles", "data")}</div></div>',
                unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:16px 18px;background:#F7F8FD;border:1px solid rgba(0,0,0,.075);'
                    'border-radius:var(--r-ctl);font-size:13px;color:#4A5170;">'
                    'No tracked merchant processes in this market yet — no benchmark to show.</div>',
                    unsafe_allow_html=True)

    # ── Tips ──────────────────────────────────────────────────────────────────
    tips = expansion_tips(sim, merchant, market, chosen, caps, fraud)
    if tips:
        st.markdown(_section_label("Tips for this launch", top=26), unsafe_allow_html=True)
        tc = st.columns(2)
        for i, (title, body, note) in enumerate(tips):
            tc[i % 2].markdown(
                f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);border-left:3px solid #3E4FE0;'
                f'border-radius:12px;padding:16px 18px;margin-bottom:10px;min-height:118px;">'
                f'<div style="font-size:13px;font-weight:600;color:#10131C;margin-bottom:6px;">{title}</div>'
                f'<div style="font-size:12px;color:#4A5170;line-height:1.6;margin-bottom:10px;">{body}</div>'
                f'<div style="font-size:11px;color:#2F3FC4;font-family:var(--font);font-variant-numeric:tabular-nums;">{note}</div></div>',
                unsafe_allow_html=True)

    st.markdown(
        f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:20px 0 6px;'
        f'padding-top:14px;border-top:1px solid rgba(0,0,0,.075);">'
        f'<span style="font-size:11px;color:#858CA6;">Provenance</span>'
        f'{_chip("source_of_truth.xlsx · coverage + capabilities", "data")}'
        f'{_chip("market profiles · payment mix, settlement, FX", "market")}'
        f'{_chip("assumption · adjustable above", "assume")}'
        f'<span style="font-size:11px;color:#858CA6;margin-left:auto;">'
        f'Modelled, not measured. No figure here is a promise.</span></div>',
        unsafe_allow_html=True)


# ══ External Partner Health & Benchmarks ═══════════════════════════════════════
# A partner sees their own performance and where it sits against the programme
# — never another partner's name. The programme figures are the same ones the
# internal page shows; the comparison is to an average, not to a peer.

_PH_AUTH = {"OpenPix": 99.1, "Adyen": 92.4, "Prosa": 90.1, "Getnet": 89.6, "Kushki": 88.2,
            "Cielo": 86.9, "SEON": 85.0, "Nuvei": 84.1}
_PH_SCORE = {"Adyen": (95, "+18%", 0), "Getnet": (88, "+42%", 1), "Kushki": (81, "+9%", 2),
             "OpenPix": (79, "+31%", 1), "SEON": (71, "+6%", 3), "Nuvei": (68, "−4%", 4)}
_PH_PROGRAMME = {"auth": 89.4, "health": 80, "tpv_growth": "+34% YoY"}

# The book's stage vocabulary, said the way a partner would say it.
_STAGE_FRIENDLY = {
    "Only Integrated": "Integrated", "Only to be integrated": "Integration pending",
    "Only to be Integrated": "Integration pending", "Agreement Signed": "Agreement signed",
    "Agreement Signed - Only referrals": "Referral agreement", "Agreement Review": "Agreement in review",
    "Initial Negotiation": "In negotiation", "Opportunity Identification": "Getting started",
    "Live Partner": "Live", "Lost": "Paused", "Stop at this Stage": "Paused", "Non-qualified Partner": "Paused",
}


def friendly_stage(stage):
    return _STAGE_FRIENDLY.get((stage or "").strip(), stage or "—")


def _ph_lookup(table, name):
    """Match the account name to the performance tables loosely: 'Getnet BR' → Getnet."""
    n = (name or "").lower()
    for k, v in table.items():
        if k.lower() in n or n in k.lower():
            return k, v
    return None, None


def _enrichment_for(name):
    n = (name or "").upper().strip()
    if n in _PARTNER_ENRICHMENT:
        return _PARTNER_ENRICHMENT[n]
    for k, v in _PARTNER_ENRICHMENT.items():
        if k.split()[0] in n or n.split()[0] in k:
            return v
    return None


def _ext_locked(title, body):
    """What a partner sees on a page that is Yuno's own tool."""
    st.markdown(
        f'<div style="background:linear-gradient(160deg,#080911 0%,#10131C 55%,#141827 100%);'
        f'border:1px solid #232A3D;border-radius:16px;padding:26px 28px;font-family:var(--font);">'
        f'<div style="font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;'
        f'color:#8B9BFF;font-family:var(--mono);margin-bottom:10px;">Yuno internal</div>'
        f'<div style="font-size:18px;font-weight:600;color:#EEF0FA;letter-spacing:-.02em;margin-bottom:8px;">{title}</div>'
        f'<div style="font-size:13px;color:#8991AC;line-height:1.65;max-width:620px;">{body}</div></div>',
        unsafe_allow_html=True)


def show_own_health(acct):
    """Partner Health, scoped to one partner."""
    name = acct["name"]
    _yw_css()
    st.markdown(hero(
        "Partner Health", eyebrow="Performance", lockup=yuno_lockup(name, 20), badge="Your numbers only",
        subtitle=f"How {name} is performing on Yuno, and where that sits against the programme average. "
                 f"No other partner is shown here."), unsafe_allow_html=True)

    enr = _enrichment_for(name) or {}
    _, auth = _ph_lookup(_PH_AUTH, name)
    _, score = _ph_lookup(_PH_SCORE, name)
    health, trend, issues = score if score else (None, None, None)

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    _yw_stats([
        {"label": "Health score", "value": f"{health}" if health is not None else "—",
         "delta": (f"programme avg {_PH_PROGRAMME['health']}" if health is not None else "being wired"),
         "delta_type": "up" if health and health >= _PH_PROGRAMME["health"] else "flat"},
        {"label": "Auth rate", "value": f"{auth}%" if auth else "—",
         "delta": (f"{auth - _PH_PROGRAMME['auth']:+.1f} pts vs programme" if auth else "being wired"),
         "delta_type": "up" if auth and auth >= _PH_PROGRAMME["auth"] else ("down" if auth else "flat")},
        {"label": "TPV trend", "value": trend or "—", "delta": "last quarter" if trend else "being wired",
         "delta_type": "up" if trend and not trend.startswith("−") else ("down" if trend else "flat")},
        {"label": "Open issues", "value": f"{issues}" if issues is not None else "0",
         "delta": "nothing open" if not issues else "being worked with you",
         "delta_type": "flat" if not issues else "down"},
        {"label": "Merchants live", "value": f"{enr.get('merchants_live', '—')}",
         "delta": "on your rails via Yuno", "delta_type": "up" if enr.get("merchants_live") else "flat"},
    ])
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        with st.container(key="yw_auth"):
            st.markdown(_yw_head("Auth rate", "You vs the programme", "Approval on live volume, last 30 days"),
                        unsafe_allow_html=True)
            if auth:
                fig = go.Figure(go.Bar(
                    x=[auth, _PH_PROGRAMME["auth"]], y=[name, "Programme average"], orientation="h",
                    marker_color=[_YW["indigo"], _YW["ink4"]], marker=dict(cornerradius=4), width=0.5,
                    text=[f"{auth}%", f"{_PH_PROGRAMME['auth']}%"], textposition="outside",
                    textfont=dict(size=11, color=_YW["ink2"], family="Geist Mono, monospace"),
                    hovertemplate="%{y}: %{x}%<extra></extra>"))
                _yw_plotly(fig, 190, legend=False, x=dict(range=[80, 104], ticksuffix="%", dtick=5),
                           y=dict(autorange="reversed", showgrid=False, tickfont=dict(color=_YW["black"], size=11.5)))
                fig.update_layout(margin=dict(l=8, r=44, t=8, b=8))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown(f'<div style="font-size:12.5px;color:{_YW["ink3"]};padding:18px 0 22px;">'
                            f'Your live approval numbers are being wired to this page. Until then, your Yuno '
                            f'manager shares them in your monthly review.</div>', unsafe_allow_html=True)
    with c2:
        items = [("Integration", acct.get("integration") or "—"), ("Deal stage", friendly_stage(acct.get("stage"))),
                 ("Rev share", enr.get("revshare", "—")), ("Onboarding", enr.get("onboarding", "—")),
                 ("Verticals", enr.get("verticals", "—"))]
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;gap:14px;padding:9px 0;'
            f'border-bottom:1px solid {_YW["wash"]};font-size:12.5px;">'
            f'<span style="color:{_YW["ink3"]};white-space:nowrap;">{k}</span>'
            f'<span style="color:{_YW["black"]};font-weight:500;text-align:right;">{v}</span></div>' for k, v in items)
        st.markdown(f'<div class="yw-card" style="padding:14px 16px 8px;">{_yw_head("Your setup", "On Yuno today")}'
                    f'<div style="margin-top:6px;">{rows}</div></div>', unsafe_allow_html=True)

    if enr.get("merchants"):
        pills = "".join(f'<span class="yw-pill ghost">{m.strip()}</span>' for m in enr["merchants"].split(","))
        st.markdown(f'<div class="yw-card" style="margin-top:12px;">{_yw_head("Merchants", "Live on your rails through Yuno")}'
                    f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">{pills}</div></div>',
                    unsafe_allow_html=True)

    st.markdown(
        f'<div style="margin-top:14px;padding:16px 20px;border-radius:12px;background:{_YW["black"]};font-family:var(--font);'
        f'display:flex;align-items:center;gap:14px;flex-wrap:wrap;">'
        f'<span class="yw-eyebrow" style="color:{_YW["lime"]};">Grow together</span>'
        f'<span style="font-size:13px;color:#EEF0FA;flex:1;min-width:240px;">The fastest way to move these numbers is a merchant '
        f'you already know. Refer one and a named Yuno BDM picks it up within 48 hours.</span></div>',
        unsafe_allow_html=True)
    if st.button("Send a lead to Yuno", key="ph_lead", type="primary"):
        st.session_state.page = "Share"; st.query_params["page"] = "Share"; st.rerun()


def show_own_benchmarks(acct):
    """Benchmarks, scoped: the partner against anonymised programme figures."""
    name = acct["name"]
    _yw_css()
    st.markdown(hero(
        "Benchmarks", eyebrow="Performance", lockup=yuno_lockup(name, 20), badge="Anonymised",
        subtitle="Where you sit against the programme. Averages only — no other partner is named."),
        unsafe_allow_html=True)
    _, auth = _ph_lookup(_PH_AUTH, name)
    _, score = _ph_lookup(_PH_SCORE, name)
    health = score[0] if score else None
    enr = _enrichment_for(name) or {}
    n_live = sum(1 for p in PARTNERS_DATA if p.get("status") == "Live")

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    _yw_stats([
        {"label": "Your auth rate", "value": f"{auth}%" if auth else "—",
         "delta": f"programme {_PH_PROGRAMME['auth']}%", "delta_type": "up" if auth and auth >= _PH_PROGRAMME["auth"] else "flat"},
        {"label": "Your health score", "value": f"{health}" if health else "—",
         "delta": f"programme {_PH_PROGRAMME['health']}", "delta_type": "up" if health and health >= _PH_PROGRAMME["health"] else "flat"},
        {"label": "Programme TPV growth", "value": _PH_PROGRAMME["tpv_growth"], "delta": "all live partners", "delta_type": "up"},
        {"label": "Live partners", "value": f"{n_live}", "delta": "in the Alliance today", "delta_type": "flat"},
        {"label": "Rev share", "value": "Active" if str(enr.get("revshare", "")).lower().startswith("yes") else "—",
         "delta": "with Yuno" if enr.get("revshare") else "ask your manager", "delta_type": "up" if enr.get("revshare") else "flat"},
    ])
    st.markdown(
        f'<div style="margin-top:16px;padding:14px 18px;border-radius:12px;background:#fff;border:1px solid {_YW["line"]};'
        f'font-size:12.5px;color:{_YW["ink2"]};line-height:1.6;font-family:var(--font);">'
        f'<b style="color:{_YW["black"]};">How to read this.</b> Programme figures are the average across every live partner on Yuno. '
        f'Peer names, volumes and revenue are never shown to another partner. Want a deeper cut for a market you care about? '
        f'Ask through <b>Send to Yuno</b>.</div>', unsafe_allow_html=True)


# ══ External scope ═════════════════════════════════════════════════════════════
# An external partner may see their own record and nothing else. The connector
# directory, Yuno's pipeline, and other partners' names are all internal data —
# a partner browsing that list is looking at their competitors.

def external_account():
    """The one account an external user is entitled to. None when internal."""
    if st.session_state.get("role") == "internal":
        return None
    ident = st.session_state.get("partner_identity") or {}
    return ident.get("account")


def external_partner_name():
    a = external_account()
    return a["name"] if a else None


def yuno_lockup(name, size=20, on_dark=True):
    """Yuno × Partner. The co-branding an external user should see everywhere."""
    ink = "#EEF0FA" if on_dark else "#10131C"
    dim = "#8991AC" if on_dark else "#676E8A"
    return (f'<span style="display:inline-flex;align-items:baseline;gap:9px;'
            f'font-family:var(--font);font-size:{size}px;font-weight:600;'
            f'letter-spacing:-.025em;color:{ink};">'
            f'<span>yuno</span>'
            f'<span style="font-weight:400;color:{dim};font-size:{size*0.85:.0f}px;">&times;</span>'
            f'<span>{name}</span></span>')


# ── The end-to-end partnership process ────────────────────────────────────────
# Stages come from the account book's own vocabulary, so a partner sees the same
# lifecycle Yuno runs internally — and exactly where they sit on it.
_E2E_STAGES = [
    ("Identified",  ["Opportunity Identification"],
     "We've identified the fit and named an owner on both sides."),
    ("Negotiation", ["Initial Negotiation"],
     "Commercials, coverage and revenue share under discussion."),
    ("Review",      ["Agreement Review"],
     "Legal and compliance review — NDA, KYP and the agreement itself."),
    ("Signed",      ["Agreement Signed", "Only to be Integrated"],
     "Agreement executed. Technical scoping begins."),
    ("Integration", ["Only Integrated"],
     "API integration, certification and test transactions."),
    ("Live",        [],
     "Processing real volume through Yuno, monitored on Partner Health."),
    ("Scaling",     [],
     "Joint go-to-market: lead generation into banking and merchant demand."),
]


def e2e_position(account):
    """Which stage this partner is at, from Deal Stage + Integration Stage."""
    if not account:
        return 0, False
    deal = (account.get("stage") or "").strip()
    integ = (account.get("integration") or "").strip().lower()
    if integ == "live":
        # live partners are at Live, or Scaling once there is a real motion
        return (6 if deal == "Agreement Signed" and account.get("tier") in ("Strategic", "T1") else 5), False
    if integ in ("in development", "just referrals"):
        return 4, False
    for i, (_, deals, _) in enumerate(_E2E_STAGES):
        if deal in deals:
            return i, False
    if deal in ("Lost", "Stop at this Stage", "Non-qualified Partner"):
        return 0, True
    return 0, False


def show_e2e_flow(account, name):
    """Animated lifecycle. Motion carries the meaning — the pulse travels the
    path already completed and stops at where the partner actually is."""
    at, stalled = e2e_position(account)
    nodes, rails = [], []
    for i, (label, _, blurb) in enumerate(_E2E_STAGES):
        done, here = i < at, i == at
        colour = "#E0ED80" if done else ("#5468F5" if here else "rgba(255,255,255,.14)")
        ring = ("box-shadow:0 0 0 4px rgba(84,104,245,.22);" if here else "")
        nodes.append(
            f'<div class="e2e-node{" e2e-here" if here else ""}" style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:center;gap:0;">'
            f'<span style="width:11px;height:11px;border-radius:50%;flex:0 0 11px;'
            f'background:{colour};{ring}"></span>'
            + (f'<span class="e2e-rail" style="flex:1;height:2px;'
               f'background:{"#E0ED80" if done else "rgba(255,255,255,.10)"};"></span>'
               if i < len(_E2E_STAGES) - 1 else "")
            + f'</div>'
            f'<div style="font-size:11.5px;font-weight:{"600" if here else "500"};'
            f'color:{"#EEF0FA" if (done or here) else "#565D78"};margin-top:9px;">{label}</div>'
            f'<div style="font-size:10px;color:{"#8991AC" if here else "#565D78"};'
            f'margin-top:3px;line-height:1.45;padding-right:12px;">{blurb}</div></div>')

    st.markdown(f"""
<style>
@keyframes e2ePulse {{
  0%   {{ transform:scale(1);   box-shadow:0 0 0 0   rgba(84,104,245,.55); }}
  70%  {{ transform:scale(1.12);box-shadow:0 0 0 9px rgba(84,104,245,0);   }}
  100% {{ transform:scale(1);   box-shadow:0 0 0 0   rgba(84,104,245,0);   }}
}}
@keyframes e2eTravel {{
  0%   {{ left:-18%; opacity:0; }}
  12%  {{ opacity:1; }}
  88%  {{ opacity:1; }}
  100% {{ left:102%; opacity:0; }}
}}
.e2e-here > div > span:first-child {{ animation:e2ePulse 2.2s var(--ease) infinite; }}
.e2e-track {{ position:relative; overflow:hidden; }}
.e2e-track::after {{
  content:""; position:absolute; top:0; bottom:0; width:16%;
  background:linear-gradient(90deg,transparent,rgba(84,104,245,.30),transparent);
  animation:e2eTravel 3.6s linear infinite; pointer-events:none;
}}
@media (prefers-reduced-motion: reduce) {{
  .e2e-here > div > span:first-child {{ animation:none; }}
  .e2e-track::after {{ display:none; }}
}}
</style>
<div style="background:linear-gradient(160deg,#080911 0%,#10131C 48%,#141827 100%);
            border:1px solid #232A3D;border-radius:18px;padding:26px 28px 24px;margin-bottom:12px;">
  <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px;">
    <span style="font-size:10px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;
                 color:#8B9BFF;">Your journey with Yuno</span>
    <span style="margin-left:auto;font-size:11px;color:#8991AC;">
      Stage {at+1} of {len(_E2E_STAGES)} · {_E2E_STAGES[at][0]}</span>
  </div>
  <div style="font-size:15px;color:#EEF0FA;line-height:1.6;margin-bottom:20px;">
    {_E2E_STAGES[at][2]}</div>
  <div class="e2e-track" style="display:flex;align-items:flex-start;gap:0;">{''.join(nodes)}</div>
  {'<div style="margin-top:18px;padding:11px 14px;border-radius:10px;background:rgba(255,107,125,.10);border:1px solid rgba(255,107,125,.28);font-size:12px;color:#FF9AA6;">This account is not currently progressing. Your Yuno manager can pick it back up.</div>' if stalled else ''}
</div>""", unsafe_allow_html=True)


# ── Welcome hero ───────────────────────────────────────────────────────────────
# Both doors open on the same three things: who you are (by name, from where),
# the Yuno Alliance sign, and the wheel of partnership types that make up the
# ecosystem. Only the greeting and the numbers differ between the two roles.

# The ecosystem in three themes. Each theme groups the provider types in the
# account book's own offering vocabulary; a click on a theme opens the types.
# Card schemes, crypto rails and A2A rails live inside "Other"/"APM" in the
# book, so they are counted by name rather than by column.
_ECOSYSTEM_THEMES = [
    ("outperformers", "Outperformers", "#6B7BFF",
     "The rails at scale — the acquirers, PSPs and schemes that carry most of the world's volume.",
     [("Acquirer",       "Acquirers",          "Card acquiring and local processing"),
      ("PSP/Aggregator", "PSPs & Aggregators", "Gateways and aggregated rails"),
      ("Scheme",         "Card schemes",       "Visa, Mastercard, Amex, Diners")]),
    ("disruptors", "Disruptors", "#C7E956",
     "The methods rewriting how people pay — wallets, local rails, instant transfers and stablecoins.",
     [("APM",    "APMs & Wallets",        "Local methods and digital wallets"),
      ("A2A",    "A2A & instant rails",   "PIX, SPEI, PSE, open banking"),
      ("Crypto", "Crypto & stablecoins",  "On-chain settlement and stablecoin rails")]),
    ("innovators", "Innovators", "#5FD4E8",
     "The layer that makes acceptance smarter — risk, banking infrastructure and commerce tooling.",
     [("Fraud Provider", "Fraud & Risk",   "Fraud decisioning and 3DS"),
      ("BaaS",           "BaaS",           "Banking-as-a-service rails"),
      ("Plug-In",        "Plug-Ins",       "Commerce platforms and plugins")]),
]

# Name tests for the types the book has no column for. A scheme is the scheme
# itself, not a product built on one ("Tink by Visa" is open banking).
_SCHEME_RE = _re.compile(r"^(visa|mastercard|american express|amex|diners)\b")
_CRYPTO_WORDS = ("crypto", "stablecoin", "bitcoin", "usdc", "usdt", "blockchain", "binance", "coinbase",
                 "circle", "ripple", "bitso")
_A2A_WORDS = ("pix", "spei", "pse", "open banking", "openbanking", "a2a", "transfer", "aiia", "tink",
              "trustly", "sepa", "ideal", "bank")



def signed_in_email():
    """The address this session signed in with — the IdP's if one ran, else the typed one."""
    try:
        if st.user.is_logged_in and getattr(st.user, "email", ""):
            return str(st.user.email)
    except Exception:
        pass
    return st.session_state.get("auth_email_used", "") or ""


def signed_in_name(email=None):
    """A person's name. The IdP gives a real one; otherwise the mailbox is the
    best we have: daniela.reyes@ → Daniela Reyes."""
    try:
        if st.user.is_logged_in and getattr(st.user, "name", ""):
            return str(st.user.name).strip()
    except Exception:
        pass
    local = (email or signed_in_email()).split("@", 1)[0]
    parts = [p for p in _re.split(r"[._\-+]+", local) if p and not p.isdigit()]
    return " ".join(p[:1].upper() + p[1:] for p in parts) or "there"


def company_from_domain(email):
    """adyen.com → Adyen. The label before the public suffix, tidied."""
    dom = (email or "").rsplit("@", 1)[-1].lower().strip()
    if not dom or "." not in dom or dom in _PUBLIC_DOMAINS:
        return ""      # a personal mailbox names nobody's company
    labels = dom.split(".")
    # skip a country second-level (co.uk, com.br) to reach the real name
    label = labels[-3] if len(labels) >= 3 and labels[-2] in ("co", "com", "org", "net", "ac", "gov") else labels[-2]
    return label.replace("-", " ").title()


def _ecosystem_counts():
    """Accounts in the book per provider type — for the internal wheel only."""
    counts = {}
    for p in PARTNERS_DATA:
        name = (p.get("name") or "").lower().strip()
        key = p.get("offering_raw") or "Other"
        if _SCHEME_RE.match(name):
            key = "Scheme"
        elif any(w in name for w in _CRYPTO_WORDS):
            key = "Crypto"
        elif key == "APM" and any(w in name for w in _A2A_WORDS):
            key = "A2A"
        counts[key] = counts.get(key, 0) + 1
    return counts


def show_welcome_hero(res=None):
    is_internal = st.session_state.role == "internal"
    email = signed_in_email()
    name = signed_in_name(email)
    if is_internal:
        greeting = f'Welcome back, <b style="color:#EEF0FA;">{name}</b> from Yuno'
        eyebrow, eyebrow_note = "Internal", "Yuno staff only"
        counts = _ecosystem_counts()
    else:
        company = (res or {}).get("company") or company_from_domain(email)
        greeting = f'Welcome, <b style="color:#EEF0FA;">{name}</b>' + (f" from {company}" if company else "")
        eyebrow, eyebrow_note = "External", "Your data only"
        counts = {}

    # ── Wheel geometry ─────────────────────────────────────────────────────
    # Three wedges, one per theme, and a chip at the middle of each. Chips
    # counter-rotate so the words stay upright while the wheel turns. A chip is
    # a <label> for a hidden radio: checking it opens that theme's panel below
    # and pauses the wheel (pure CSS — no script runs inside st.markdown).
    n = len(_ECOSYSTEM_THEMES)
    step = 360 / n
    radius = 168
    wedges, nodes, panels, chips_flat, sel_css = [], [], [], [], []
    for i, (key, label, colour, tagline, types) in enumerate(_ECOSYSTEM_THEMES):
        a0, a1 = i * step, (i + 1) * step
        wedges.append(f"{colour}CC {a0:.2f}deg {a1 - 1.5:.2f}deg, transparent {a1 - 1.5:.2f}deg {a1:.2f}deg")
        mid = a0 + step / 2 - 90
        total = sum(counts.get(t, 0) for t, _, _ in types)
        chip = (
            f'<label for="eco-r-{key}" class="eco-chip" style="--c:{colour};animation-delay:{0.9 + i * 0.14:.2f}s;">'
            f'<span class="eco-dot"></span>'
            f'<span class="eco-chip-label">{label}'
            + (f'<span class="eco-count">{total}</span>' if total else "")
            + f'</span><span class="eco-chip-blurb">{len(types)} provider types · tap to open</span></label>')
        chips_flat.append(chip)
        nodes.append(
            f'<div class="eco-node" style="transform:rotate({mid:.2f}deg) translate({radius}px);">'
            f'<div style="transform:rotate({-mid:.2f}deg);">{chip}</div></div>')
        cards = "".join(
            f'<div class="eco-type" style="--c:{colour};animation-delay:{0.05 * j:.2f}s;">'
            f'<div class="eco-type-head"><span class="eco-dot"></span><span>{tl}</span>'
            + (f'<span class="eco-count">{counts[tk]}</span>' if counts.get(tk) else "")
            + f'</div><div class="eco-type-blurb">{tb}</div></div>'
            for j, (tk, tl, tb) in enumerate(types))
        panels.append(
            f'<div class="eco-panel eco-panel-{key}" style="--c:{colour};">'
            f'<div class="eco-panel-head">'
            f'<div><div class="eco-panel-k">{label}</div><div class="eco-panel-t">{tagline}</div></div>'
            f'<label for="eco-r-none" class="eco-close" title="Close">×</label></div>'
            f'<div class="eco-types">{cards}</div></div>')
        sel_css.append(
            f'.eco-hero:has(#eco-r-{key}:checked) .eco-panel-{key} {{ display:block; }}\n'
            f'.eco-hero:has(#eco-r-{key}:checked) label[for="eco-r-{key}"] {{ background:var(--c);color:#10131C;border-color:var(--c); }}\n'
            f'.eco-hero:has(#eco-r-{key}:checked) label[for="eco-r-{key}"] .eco-chip-label,'
            f'.eco-hero:has(#eco-r-{key}:checked) label[for="eco-r-{key}"] .eco-chip-blurb {{ color:#10131C; }}\n'
            f'.eco-hero:has(#eco-r-{key}:checked) label[for="eco-r-{key}"] .eco-dot {{ background:#10131C;box-shadow:none; }}')
    radios = '<input type="radio" name="eco-theme" id="eco-r-none" checked>' + "".join(
        f'<input type="radio" name="eco-theme" id="eco-r-{key}">' for key, *_ in _ECOSYSTEM_THEMES)

    letters = "".join(
        f'<span style="animation-delay:{0.25 + i * 0.06:.2f}s;">{ch if ch != " " else "&nbsp;"}</span>'
        for i, ch in enumerate("YUNO ALLIANCE"))

    status_pill = ""
    if res is not None and not is_internal:
        colour, label, line = _ALLIANCE_STATUS.get(res["status"], _ALLIANCE_STATUS["unknown"])
        status_pill = (
            f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:6px 14px;'
            f'border-radius:999px;background:{colour}22;border:1px solid {colour}55;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{colour};"></span>'
            f'<span style="font-size:12px;font-weight:600;color:#EEF0FA;">{label}</span>'
            f'<span style="font-size:12px;color:#8991AC;">· {line}</span></div>')

    st.markdown(f"""
<style>
@keyframes ecoSpin   {{ to {{ transform:rotate(360deg); }} }}
@keyframes ecoUnspin {{ to {{ transform:rotate(-360deg); }} }}
@keyframes ecoRise   {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
@keyframes ecoLetter {{ 0% {{ opacity:0; transform:translateY(18px) scale(.92); filter:blur(6px); }}
                        60% {{ filter:blur(0); }} 100% {{ opacity:1; transform:none; filter:blur(0); }} }}
@keyframes ecoSheen  {{ 0% {{ background-position:-220% 0; }} 100% {{ background-position:220% 0; }} }}
@keyframes ecoGlow   {{ 0%,100% {{ opacity:.45; }} 50% {{ opacity:.9; }} }}
@keyframes ecoHub    {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(224,237,128,.28), 0 0 40px rgba(84,104,245,.35); }}
                        50%     {{ box-shadow:0 0 0 14px rgba(224,237,128,0), 0 0 60px rgba(84,104,245,.55); }} }}
@keyframes ecoDash   {{ to {{ stroke-dashoffset:-48; }} }}

.eco-hero {{ background:linear-gradient(160deg,#080911 0%,#10131C 45%,#141827 100%);
            border:1px solid #232A3D;border-radius:20px;padding:44px 46px 40px;margin-bottom:12px;
            position:relative;overflow:hidden;font-family:var(--font); }}
.eco-hero::before {{ content:"";position:absolute;top:-120px;right:-90px;width:520px;height:520px;border-radius:50%;
            background:radial-gradient(circle,rgba(84,104,245,.26),transparent 62%);animation:ecoGlow 6s ease-in-out infinite; }}
.eco-hero::after {{ content:"";position:absolute;bottom:-160px;left:-120px;width:460px;height:460px;border-radius:50%;
            background:radial-gradient(circle,rgba(224,237,128,.13),transparent 62%);animation:ecoGlow 7.5s ease-in-out infinite reverse; }}
.eco-hero > * {{ position:relative; }}
.eco-hero input[type=radio] {{ position:absolute;opacity:0;width:0;height:0;pointer-events:none; }}
.eco-greet {{ animation:ecoRise .7s var(--ease) both; }}
.eco-greet .h {{ font-size:26px;font-weight:600;color:#C7CCE0;letter-spacing:-.03em;line-height:1.14;margin-bottom:8px; }}
.eco-greet .p {{ font-size:13.5px;color:#8991AC;line-height:1.6; }}

.eco-sign {{ text-align:center;margin:34px 0 8px;line-height:1; }}
.eco-sign .w {{ display:inline-block;font-size:clamp(34px,5.4vw,64px);font-weight:700;letter-spacing:.14em;
            text-transform:uppercase;padding-left:.14em;
            background:linear-gradient(100deg,#EEF0FA 0%,#EEF0FA 38%,#E0ED80 50%,#8B9BFF 62%,#EEF0FA 74%,#EEF0FA 100%);
            background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;
            animation:ecoSheen 5.5s linear 1.4s infinite; }}
.eco-sign .w span {{ display:inline-block;animation:ecoLetter .8s cubic-bezier(.2,.8,.2,1) both; }}
.eco-sign .u {{ display:block;width:120px;height:2px;margin:16px auto 0;border-radius:2px;
            background:linear-gradient(90deg,transparent,#E0ED80,transparent);animation:ecoRise .9s var(--ease) 1.1s both; }}
.eco-sign .t {{ font-size:10.5px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:#8991AC;
            margin-top:12px;animation:ecoRise .9s var(--ease) 1.2s both; }}

.eco-stage {{ position:relative;width:min(460px,92vw);aspect-ratio:1;margin:26px auto 0;
             display:flex;align-items:center;justify-content:center;animation:ecoRise 1s var(--ease) .6s both; }}
.eco-ring {{ position:absolute;inset:6%;border-radius:50%;
            background:conic-gradient(from 0deg,{", ".join(wedges)});
            -webkit-mask:radial-gradient(circle,transparent 63%,#000 64%,#000 68%,transparent 69%);
            mask:radial-gradient(circle,transparent 63%,#000 64%,#000 68%,transparent 69%);
            animation:ecoSpin 54s linear infinite;opacity:.95; }}
.eco-ticks {{ position:absolute;inset:0;animation:ecoSpin 54s linear infinite reverse; }}
.eco-ticks circle {{ fill:none;stroke:rgba(255,255,255,.14);stroke-width:1;stroke-dasharray:2 10;animation:ecoDash 4s linear infinite; }}
.eco-orbit {{ position:absolute;inset:0;animation:ecoSpin 54s linear infinite; }}
.eco-node {{ position:absolute;top:50%;left:50%;width:0;height:0;display:flex;align-items:center;justify-content:center; }}
.eco-chip {{ animation:ecoUnspin 54s linear infinite, ecoRise .7s var(--ease) both;cursor:pointer;
            display:flex;flex-direction:column;align-items:center;gap:3px;text-align:center;width:136px;
            padding:10px 10px 11px;border-radius:14px;background:rgba(16,19,28,.84);backdrop-filter:blur(6px);
            border:1px solid color-mix(in srgb,var(--c) 60%,transparent);box-shadow:0 6px 22px rgba(0,0,0,.35);
            transition:transform .2s var(--ease),border-color .2s,background .2s; }}
.eco-chip:hover {{ border-color:var(--c);transform:scale(1.06); }}
.eco-dot {{ width:9px;height:9px;border-radius:50%;background:var(--c);box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 22%,transparent);flex:0 0 9px; }}
.eco-chip-label {{ font-size:12.5px;font-weight:600;color:#EEF0FA;letter-spacing:-.01em;display:flex;align-items:center;gap:5px;justify-content:center; }}
.eco-count {{ font-size:9.5px;font-weight:700;padding:1px 6px;border-radius:999px;background:color-mix(in srgb,var(--c) 26%,transparent);
             color:#EEF0FA;font-variant-numeric:tabular-nums; }}
.eco-chip-blurb {{ font-size:9.5px;color:#8991AC;line-height:1.35; }}
.eco-hub {{ position:relative;width:46%;aspect-ratio:1;border-radius:50%;display:flex;flex-direction:column;align-items:center;
           justify-content:center;text-align:center;padding:14px;
           background:radial-gradient(circle at 40% 35%,#1B2140,#0C0F1A 70%);border:1px solid rgba(224,237,128,.35);
           animation:ecoHub 3.2s ease-in-out infinite; }}
.eco-hub .k {{ font-size:9.5px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:#E0ED80;margin-bottom:6px; }}
.eco-hub .n {{ font-size:15px;font-weight:600;color:#EEF0FA;letter-spacing:-.02em;line-height:1.25; }}
.eco-hub .s {{ font-size:10px;color:#8991AC;margin-top:6px;line-height:1.4; }}

/* Opened theme: wheel pauses, chip fills with its colour, panel unfolds below */
.eco-hero:has(input[type=radio]:not(#eco-r-none):checked) .eco-ring,
.eco-hero:has(input[type=radio]:not(#eco-r-none):checked) .eco-orbit,
.eco-hero:has(input[type=radio]:not(#eco-r-none):checked) .eco-chip,
.eco-hero:has(input[type=radio]:not(#eco-r-none):checked) .eco-ticks {{ animation-play-state:paused; }}
{"".join(sel_css)}
.eco-panel {{ display:none;margin:22px auto 0;max-width:820px;border-radius:16px;padding:18px 20px 16px;
             background:rgba(255,255,255,.04);border:1px solid color-mix(in srgb,var(--c) 45%,transparent);
             animation:ecoRise .45s var(--ease) both; }}
.eco-panel-head {{ display:flex;align-items:flex-start;gap:14px;margin-bottom:14px; }}
.eco-panel-k {{ font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--c);margin-bottom:4px; }}
.eco-panel-t {{ font-size:13px;color:#C7CCE0;line-height:1.55;max-width:640px; }}
.eco-close {{ margin-left:auto;flex:0 0 28px;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;
             cursor:pointer;color:#8991AC;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.10);font-size:16px;line-height:1; }}
.eco-close:hover {{ color:#EEF0FA;background:rgba(255,255,255,.12); }}
.eco-types {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px; }}
.eco-type {{ background:rgba(16,19,28,.7);border:1px solid rgba(255,255,255,.08);border-left:3px solid var(--c);border-radius:12px;
            padding:12px 14px;animation:ecoRise .45s var(--ease) both; }}
.eco-type-head {{ display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;color:#EEF0FA; }}
.eco-type-blurb {{ font-size:11px;color:#8991AC;margin-top:5px;line-height:1.45; }}
.eco-hint {{ text-align:center;font-size:10.5px;color:#565D78;margin-top:14px;letter-spacing:.04em; }}
.eco-hero:has(input[type=radio]:not(#eco-r-none):checked) .eco-hint {{ display:none; }}

@media (max-width:640px) {{
  .eco-hero {{ padding:30px 22px 28px; }}
  .eco-node {{ transform:none !important; }}
  .eco-orbit, .eco-ring, .eco-ticks {{ display:none; }}
  .eco-stage {{ display:block;aspect-ratio:auto; }}
  .eco-hub {{ width:100%;aspect-ratio:auto;border-radius:16px;margin-bottom:12px; }}
  .eco-fallback {{ display:grid !important;grid-template-columns:1fr 1fr 1fr;gap:8px; }}
  .eco-fallback .eco-chip {{ width:auto;animation:none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .eco-hero *, .eco-hero::before, .eco-hero::after {{ animation:none !important; }}
  .eco-sign .w span, .eco-chip, .eco-greet, .eco-stage, .eco-sign .u, .eco-sign .t, .eco-panel, .eco-type {{ opacity:1; transform:none; filter:none; }}
}}
</style>
<div class="eco-hero">
  {radios}
  <div class="eco-greet">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
      <span style="font-size:10px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;
        background:{'rgba(84,104,245,.16)' if is_internal else 'rgba(224,237,128,.16)'};
        color:{'#B9C2FF' if is_internal else '#E0ED80'};
        border:1px solid {'rgba(84,104,245,.40)' if is_internal else 'rgba(224,237,128,.34)'};
        padding:3px 9px;border-radius:5px;">{eyebrow}</span>
      <span style="font-size:11px;color:#8991AC;">{eyebrow_note}</span>
      <span style="margin-left:auto;font-size:11px;color:#565D78;">{email}</span>
    </div>
    {'<div style="margin-bottom:12px;">' + yuno_lockup(res["company"], 18) + '</div>' if (res or {}).get("company") and not is_internal else ''}
    <div class="h">{greeting}</div>
    <div class="p">{"Your centralized platform to find the information you need on Yuno Partners."
                    if is_internal else "Yuno partner program empowering mutual success."}</div>
    {status_pill}
  </div>

  <div class="eco-sign">
    <div class="w">{letters}</div>
    <span class="u"></span>
    <div class="t">{"Partner Portal" if is_internal else "Partner Program"}</div>
  </div>

  <div class="eco-stage">
    <div class="eco-ring"></div>
    <svg class="eco-ticks" viewBox="0 0 100 100"><circle cx="50" cy="50" r="49"/></svg>
    <div class="eco-orbit">{"".join(nodes)}</div>
    <div class="eco-hub">
      <div class="k">Yuno</div>
      <div class="n">Partner<br>Ecosystem</div>
      <div class="s">{f"{sum(counts.values())} accounts · {n} themes" if counts else f"{n} themes"}</div>
    </div>
    <div class="eco-fallback" style="display:none;">{"".join(chips_flat)}</div>
  </div>
  <div class="eco-hint">Tap a theme to see the provider types inside it</div>
  {"".join(panels)}
</div>""", unsafe_allow_html=True)


# ── Partner Alliance welcome ───────────────────────────────────────────────────
_ALLIANCE_STATUS = {
    "partner":  ("#5A7A00", "Live partner", "You're in the Alliance."),
    "prospect": ("#B36200", "In progress",  "Your agreement is still moving."),
    "closed":   ("#676E8A", "Not active",   "This account isn't currently active."),
    "unknown":  ("#C4384A", "Not yet a partner", "We don't have an account for you yet."),
    "public":   ("#C4384A", "Unrecognised", "That looks like a personal mailbox."),
}


def show_alliance_welcome():
    res = st.session_state.get("partner_identity")
    if not res:
        res = resolve_partner(st.session_state.get("auth_email_used", ""))
    colour, label, line = _ALLIANCE_STATUS.get(res["status"], _ALLIANCE_STATUS["unknown"])
    acct = res["account"]

    show_welcome_hero(res)

    # ── Recognised partner ────────────────────────────────────────────────────
    if acct and res["status"] in ("partner", "prospect"):
        show_e2e_flow(acct, res["company"])
        _share_result_banner()
        show_pipeline_comment(res, key="home")
        st.markdown(
            '<div style="display:flex;gap:0;flex-wrap:wrap;background:#fff;border:1px solid rgba(0,0,0,.075);'
            'border-radius:14px;padding:16px 20px;margin-bottom:14px;">'
            + "".join(
                f'<div style="flex:1;min-width:118px;padding-right:14px;">'
                f'<div style="font-size:10px;color:#858CA6;text-transform:uppercase;letter-spacing:.09em;'
                f'font-weight:600;margin-bottom:5px;">{k}</div>'
                f'<div style="font-size:13px;font-weight:500;color:#10131C;">{v}</div></div>'
                for k, v in [("Type", acct["type"]),
                             ("Region", acct["region"]), ("Deal stage", friendly_stage(acct["stage"])),
                             ("Integration", acct["integration"]),
                             ("Your Yuno manager", acct["manager"])])
            + f'<div style="width:100%;margin-top:12px;padding-top:11px;'
            f'border-top:1px solid rgba(0,0,0,.055);">'
            f'{_chip("Matched from your work email · your record only", "data")}</div></div>',
            unsafe_allow_html=True)

        st.markdown(_section_label("What you can do here"), unsafe_allow_html=True)
        cards = [("Partner Portfolio", "Partners", "Your record, contacts, contracts and integration status."),
                 ("Partner Health", "Performance", "Approval rates, volumes and the issues we're tracking."),
                 ("Joint GTM", "GTM", "The decks and briefs we sell with together — add yours, comment on ours."),
                 ("Send to Yuno", "Share", "Mandates, API and feature updates, leads — straight to your partner manager."),
                 ("Market Intel", "Insights", "Payment landscape, regulation and settlement by market.")]
        cc = st.columns(2)
        for i, (title, page, desc) in enumerate(cards):
            with cc[i % 2]:
                st.markdown(
                    f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);border-top:3px solid #3E4FE0;'
                    f'border-radius:14px;padding:18px 20px;margin-bottom:10px;min-height:104px;">'
                    f'<div style="font-size:14px;font-weight:600;color:#10131C;margin-bottom:6px;">{title}</div>'
                    f'<div style="font-size:12px;color:#4A5170;line-height:1.6;">{desc}</div></div>',
                    unsafe_allow_html=True)
                if st.button(f"Open {title}", key=f"al_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.query_params["page"] = page
                    st.rerun()
        return

    # ── Not a partner (or a closed / unidentifiable account) ──────────────────
    if not st.session_state.get("alliance_alerted"):
        delivered, detail, channel = alert_unrecognised_provider(res, st.session_state.get("auth_email_used", ""))
        st.session_state.alliance_alerted = {"delivered": delivered, "detail": detail, "channel": channel}
    alert = st.session_state.alliance_alerted

    reason = {
        "unknown": f"<b>{res['domain']}</b> doesn't match any account in the partner book.",
        "public": "You signed in from a personal mailbox, so we can't tell which company you're with.",
        "closed": f"<b>{res['company']}</b> is on the book, but the account is marked "
                  f"<b>{acct['stage'] if acct else 'inactive'}</b>.",
    }.get(res["status"], "We couldn't match you to a partner account.")

    st.markdown(
        f'<div style="background:#fff;border:1px solid rgba(0,0,0,.075);border-left:3px solid {colour};'
        f'border-radius:14px;padding:22px 24px;margin-bottom:12px;">'
        f'<div style="font-size:15px;font-weight:600;color:#10131C;margin-bottom:8px;">'
        f'We don\'t have you on the Alliance yet</div>'
        f'<div style="font-size:13px;color:#4A5170;line-height:1.7;margin-bottom:14px;">{reason}<br>'
        f'That isn\'t a no — it means nobody at Yuno owns this relationship yet. '
        f'We\'ve told the partnerships team you were here.</div>'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;">'
        f'{_chip("checked against the partner book", "data")}'
        f'{_chip(res["via"], "market")}</div></div>', unsafe_allow_html=True)

    ok = alert["delivered"]
    st.markdown(
        f'<div style="background:{"#F0F5DC" if ok else "#FDF8E8"};'
        f'border:1px solid {"rgba(90,107,0,.3)" if ok else "rgba(138,106,0,.28)"};'
        f'border-radius:var(--r-ctl);padding:14px 18px;font-size:12px;line-height:1.6;'
        f'color:{"#3F5208" if ok else "#8A4B00"};">'
        + (f'<b>Partnerships alerted.</b> {alert["detail"]}.' if ok else
           f'<b>Alert queued locally.</b> {alert["detail"]}. '
           f'It is written to <code>data/unrecognised_providers.jsonl</code> and will post to '
           f'<code>{alert["channel"]}</code> once Slack credentials are set in '
           f'<code>.streamlit/secrets.toml</code>.')
        + '</div>', unsafe_allow_html=True)


# ══ Send to Yuno · partner inbox ═══════════════════════════════════════════════
# The external door's one write path. A partner tells Yuno about a scheme
# mandate, an API or feature change, a merchant lead, or leaves a comment on
# their own pipeline stage. Every submission is logged locally first, then
# posted to the partnerships channel with the partner manager named — leads
# take the same route as Yuno's own lead desk so the assigned BDM hears first.

_PARTNER_INBOX = _os.path.join(_BASE, "data", "partner_submissions.jsonl")

_SHARE_KINDS = [
    ("mandate", "Mandate",          "A scheme, regulator or network mandate Yuno should be ready for."),
    ("api",     "API update",       "A change to your API — versions, deprecations, breaking changes."),
    ("feature", "Feature update",   "Something new you've launched that Yuno merchants can use."),
    ("lead",    "Lead",             "A merchant you'd like to introduce to Yuno."),
    ("comment", "Pipeline comment", "A note on where your partnership sits and what should happen next."),
]
_SHARE_LABEL = {k: l for k, l, _ in _SHARE_KINDS}
_SHARE_ICON = {"mandate": ":scroll:", "api": ":gear:", "feature": ":sparkles:",
               "lead": ":inbox_tray:", "comment": ":speech_balloon:"}


def _slack_send(text, blocks=None, channel=None):
    """Post one message. Webhook wins over bot token; neither → logged only."""
    import json as _json
    webhook, token, default = _slack_config()
    channel = channel or default
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    if webhook:
        try:
            import urllib.request as _u
            req = _u.Request(webhook, data=_json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"})
            _u.urlopen(req, timeout=5).read()
            return True, f"posted to {channel}", channel
        except Exception as e:
            return False, f"Slack webhook failed: {e}", channel
    if token:
        try:
            import urllib.request as _u
            req = _u.Request("https://slack.com/api/chat.postMessage",
                             data=_json.dumps({"channel": channel, **payload}).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {token}"})
            resp = _json.loads(_u.urlopen(req, timeout=5).read().decode())
            ok = bool(resp.get("ok"))
            return ok, (f"posted to {channel}" if ok else f"Slack API: {resp.get('error')}"), channel
        except Exception as e:
            return False, f"Slack API failed: {e}", channel
    return False, "no Slack credentials configured — logged locally only", channel


def _manager_mention(manager):
    """The partner manager as a Slack mention when the roster has a handle."""
    for b in _RT.BDMS:
        if b["name"].lower() in (manager or "").lower():
            return _mention(b)
    return manager or _ESCALATION


def submit_to_yuno(kind, fields, res):
    """Log a partner submission, then announce it. Returns (ok, detail, channel)."""
    import json as _json, datetime as _dt
    acct = res.get("account") or {}
    company = res.get("company") or company_from_domain(signed_in_email()) or res.get("domain") or "Unknown partner"
    record = {
        "ts": _dt.datetime.utcnow().isoformat() + "Z", "kind": kind,
        "company": company, "domain": res.get("domain", ""), "from": signed_in_email(),
        "manager": acct.get("manager", ""), "stage": acct.get("stage", ""), **fields,
    }
    try:
        with open(_PARTNER_INBOX, "a") as f:
            f.write(_json.dumps(record) + "\n")
    except Exception as e:
        return False, f"log write failed: {e}", ""

    # Leads go where every other lead goes: routed to a BDM, SLA attached.
    if kind == "lead":
        lead = {"name": fields["title"], "track": fields.get("track", "Merchants"),
                "region": fields.get("region", "Other"), "source": "Partner referral",
                "note": f"Referred by {company}" + (f" — {fields['body']}" if fields.get("body") else "")}
        pool = _RT.REGION_ROUTING.get(lead["region"], [])
        by_key = {b["key"]: b for b in _RT.BDMS}
        bdm = by_key[pool[0]] if pool else by_key.get(_RT.FALLBACK_BDM, _RT.BDMS[0])
        return post_lead_alert(lead, bdm, gm_for_region(lead["region"]), not pool)

    who = _manager_mention(acct.get("manager", ""))
    head = f"{_SHARE_ICON[kind]} *{_SHARE_LABEL[kind]} from {company}*"
    lines = [head, f"*{fields['title']}*" if fields.get("title") else ""]
    for k, lbl in [("markets", "Markets"), ("effective", "Effective"), ("version", "Version"),
                   ("breaking", "Breaking change"), ("link", "Link"), ("stage", "Stage")]:
        v = fields.get(k)
        if v not in (None, "", [], False):
            lines.append(f"*{lbl}:* {', '.join(v) if isinstance(v, list) else ('yes' if v is True else v)}")
    if fields.get("body"):
        lines.append("> " + fields["body"].replace("\n", "\n> "))
    lines.append(f"_Partner manager: {who} · sent from the Partner Alliance by {signed_in_email()}_")
    return _slack_send("\n".join(l for l in lines if l))


def partner_submissions(company, domain, n=10):
    """This partner's own submissions, newest first. Nobody else's."""
    import json as _json
    try:
        with open(_PARTNER_INBOX) as f:
            rows = [_json.loads(x) for x in f if x.strip()]
    except Exception:
        return []
    mine = [r for r in rows if (company and r.get("company") == company) or (domain and r.get("domain") == domain)]
    return list(reversed(mine))[:n]


def _share_result_banner():
    result = st.session_state.pop("share_result", None)
    if result:
        ok, detail = result
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:9px;padding:12px 15px;border-radius:11px;'
            f'margin-bottom:12px;font-family:var(--font);'
            f'background:{"#EAF3E3" if ok else "#FDF8E8"};'
            f'border:1px solid {"rgba(55,97,10,.22)" if ok else "rgba(138,106,0,.28)"};">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{"#37610A" if ok else "#8A4B00"};"></span>'
            f'<span style="font-size:12.5px;color:{"#2E5208" if ok else "#6E5400"};">'
            f'<b>{"Sent to Yuno" if ok else "Saved for Yuno"}</b> · {detail}</span></div>',
            unsafe_allow_html=True)


def show_pipeline_comment(res, key="home"):
    """A comment box under the partner's own journey. One line, one button."""
    acct = res.get("account") or {}
    at, _ = e2e_position(acct)
    stage = _E2E_STAGES[at][0]
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:10px;margin:2px 0 6px;font-family:var(--font);">'
        f'<span style="font-size:10px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:#858CA6;">'
        f'Comment on your pipeline</span>'
        f'<span style="font-size:11px;color:#858CA6;">stage {at + 1} · {stage} · goes to '
        f'{acct.get("manager") or "your partner manager"}</span></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    text = c1.text_input("Comment", placeholder="What should happen next, what's blocking, what changed on your side…",
                         key=f"pc_text_{key}", label_visibility="collapsed")
    if c2.button("Send", key=f"pc_send_{key}", type="primary", use_container_width=True,
                 disabled=not (text or "").strip()):
        ok, detail, _ = submit_to_yuno("comment", {"title": f"Stage {at + 1} · {stage}", "stage": stage,
                                                   "body": text.strip()}, res)
        st.session_state.share_result = (ok, detail)
        st.rerun()


def show_partner_share():
    res = st.session_state.get("partner_identity") or resolve_partner(st.session_state.get("auth_email_used", ""))
    acct = res.get("account") or {}
    company = res.get("company") or company_from_domain(signed_in_email()) or "your company"
    manager = acct.get("manager") or "the partnerships team"

    st.markdown(hero(
        "Send to Yuno", eyebrow="Partner Alliance",
        subtitle=(f"Mandates, API and feature updates, merchant leads and pipeline comments from "
                  f"{company} go straight to {manager}. Everything is logged, nothing gets lost in email."),
        badge="External"), unsafe_allow_html=True)

    _share_result_banner()

    # ── What are you sending? ────────────────────────────────────────────────
    kind = st.radio("What are you sending?", [k for k, _, _ in _SHARE_KINDS],
                    format_func=lambda k: _SHARE_LABEL[k], horizontal=True, key="share_kind",
                    label_visibility="collapsed")
    blurb = next(b for k, _, b in _SHARE_KINDS if k == kind)
    st.markdown(f'<div style="font-size:12.5px;color:#4A5170;margin:-2px 0 14px;font-family:var(--font);">{blurb}</div>',
                unsafe_allow_html=True)

    regions = sorted(_RT.REGION_ROUTING) + ["Other"]
    fields = {}
    with st.form(f"share_{kind}", clear_on_submit=True, border=False):
        if kind == "lead":
            c1, c2 = st.columns([1.5, 1])
            fields["title"] = c1.text_input("Merchant", placeholder="Merchant or company name")
            fields["track"] = c2.radio("Track", _RT.TRACKS, horizontal=True)
            c3, c4 = st.columns(2)
            fields["region"] = c3.selectbox("Region", regions)
            fields["contact"] = c4.text_input("Their contact (optional)", placeholder="name@merchant.com")
            fields["body"] = st.text_area("Why Yuno, why now?", height=96,
                                          placeholder="What they process today, the markets, the gap you see.")
        elif kind == "comment":
            at, _ = e2e_position(acct)
            stage = _E2E_STAGES[at][0]
            fields["stage"] = stage
            fields["title"] = f"Stage {at + 1} · {stage}"
            st.markdown(
                f'<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;'
                f'background:#E9ECFC;border:1px solid rgba(84,104,245,.22);font-size:12px;color:#2F3FC4;'
                f'font-family:var(--font);margin-bottom:8px;">You are at stage {at + 1} of {len(_E2E_STAGES)} · <b>{stage}</b></div>',
                unsafe_allow_html=True)
            fields["body"] = st.text_area("Your comment", height=120,
                                          placeholder="What should happen next, what's blocking, what changed on your side…")
        else:
            c1, c2 = st.columns([1.6, 1])
            fields["title"] = c1.text_input("Title", placeholder={
                "mandate": "e.g. Visa CE 3.0 compelling evidence — LATAM issuers",
                "api": "e.g. v2 tokenisation endpoint — v1 sunset",
                "feature": "e.g. Network tokens now live for Brazil domestic cards"}[kind])
            fields["effective"] = c2.date_input("Effective date").isoformat()
            c3, c4 = st.columns(2)
            fields["markets"] = c3.multiselect("Markets affected", regions)
            if kind == "api":
                fields["version"] = c4.text_input("Version", placeholder="e.g. v2.3")
                fields["breaking"] = st.checkbox("This is a breaking change")
            else:
                fields["link"] = c4.text_input("Link (optional)", placeholder="Docs, bulletin or announcement URL")
            if kind == "api":
                fields["link"] = st.text_input("Docs link (optional)", placeholder="https://")
            fields["body"] = st.text_area("Summary", height=110,
                                          placeholder="What changes, who it affects, and what you need from Yuno.")
        sent = st.form_submit_button(f"Send {_SHARE_LABEL[kind].lower()} to Yuno", type="primary")

    if sent:
        need = (fields.get("title") or "").strip() if kind != "comment" else (fields.get("body") or "").strip()
        if not need:
            st.session_state.share_result = (False, "add a title before sending" if kind != "comment" else "write a comment first")
        else:
            clean = {k: (v.strip() if isinstance(v, str) else v) for k, v in fields.items()}
            ok, detail, _ = submit_to_yuno(kind, clean, res)
            st.session_state.share_result = (ok, detail)
        st.rerun()

    # ── Your recent submissions ──────────────────────────────────────────────
    mine = partner_submissions(res.get("company"), res.get("domain"))
    st.markdown(_section_label("Your recent submissions", top=22), unsafe_allow_html=True)
    if not mine:
        st.markdown('<div style="background:#fff;border:1px dashed #D5D9E8;border-radius:12px;padding:20px;'
                    'text-align:center;font-size:12.5px;color:#676E8A;font-family:var(--font);">'
                    'Nothing sent yet. Whatever you send appears here with its date and where it went.</div>',
                    unsafe_allow_html=True)
        return
    tone = {"mandate": "#B36200", "api": "#2F3FC4", "feature": "#37610A", "lead": "#00697F", "comment": "#5A6486"}
    st.markdown(
        '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;padding:6px 18px;font-family:var(--font);">'
        + "".join(
            f'<div style="display:flex;gap:12px;align-items:flex-start;padding:11px 0;'
            f'border-bottom:1px solid rgba(35,42,61,.06);">'
            f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap;'
            f'background:{tone.get(r["kind"], "#5A6486")}14;color:{tone.get(r["kind"], "#5A6486")};margin-top:2px;">'
            f'{_SHARE_LABEL.get(r["kind"], r["kind"])}</span>'
            f'<div style="flex:1;min-width:0;"><div style="font-size:13px;font-weight:500;color:#10131C;">{r.get("title") or r.get("name") or "—"}</div>'
            + (f'<div style="font-size:11.5px;color:#4A5170;margin-top:2px;line-height:1.5;">{(r.get("body") or r.get("note") or "")[:180]}</div>'
               if (r.get("body") or r.get("note")) else "")
            + f'</div><span style="font-size:10.5px;color:#858CA6;white-space:nowrap;font-variant-numeric:tabular-nums;">'
            f'{r["ts"][:10]}</span></div>'
            for r in mine)
        + '</div>', unsafe_allow_html=True)


# ══ Co-sell · Stablecoin Provider Sprint ═══════════════════════════════════════
# The execution plan the team runs between September and November 2026, made
# operable: who owns what and where it stands, the pricing playbook as a
# calculator rather than a table to read off, and the partner story deck with
# the partner's own name in it.
#
# Salesforce stays the system of record. Stage here is a local planning view.

_PLAY_TONE = {
    "full":   ("#E9ECFC", "#2F3FC4", "rgba(84,104,245,.22)"),
    "stage5": ("#EAF3E3", "#37610A", "rgba(55,97,10,.22)"),
    "upsell": ("#DDEFF4", "#00697F", "rgba(0,105,127,.25)"),
    "carved": ("#F1F3FB", "#5A6486", "rgba(90,100,134,.22)"),
}

# Stage ramp: dim while pre-cycle, warming through the cycle, lime at live.
_STAGE_TONE = ["#5C6480", "#8B9BFF", "#5FD4E8", "#B9C2FF",
               "#FFD400", "#FFA53D", "#A9DE4E", "#E0ED80"]


# Streamlit runs st.markdown through its markdown parser even with
# unsafe_allow_html, so a pair of dollar signs anywhere in one call is read as
# inline LaTeX and comes back in a maths italic. USD is the HTML entity, which
# renders as an ordinary dollar and the parser never sees.
USD = "&#36;"


def _h(text):
    """Prose from a data file, made safe for Streamlit's markdown parser."""
    return str(text).replace("$", USD)


def _money(n):
    """Whole dollars, or $1.2M / $840k once it gets long."""
    n = float(n)
    if abs(n) >= 1_000_000:
        return f"{USD}{n/1_000_000:.2f}M".replace(".00M", "M")
    if abs(n) >= 1_000:
        return f"{USD}{n/1_000:,.0f}k"
    return f"{USD}{n:,.0f}"


def trx_tier(monthly_trx):
    """The per-transaction price for this monthly count, and its band label."""
    for lo, hi, price, label in _CS.TRX_TIERS:
        if monthly_trx >= lo and (hi is None or monthly_trx < hi):
            return price, label
    return _CS.TRX_TIERS[-1][2], _CS.TRX_TIERS[-1][3]


def price_provider(monthly_trx, atv, platform_fee):
    """The greater-of rule, run end to end.

    Returns per-transaction and basis-point revenue side by side, which model is
    operative, and what approval the platform fee needs. Every figure derives
    from the two inputs — nothing here is typed in.
    """
    monthly_trx = max(0.0, float(monthly_trx))
    atv = max(0.0, float(atv))
    volume = monthly_trx * atv

    per_trx_price, tier_label = trx_tier(monthly_trx)
    per_trx_rev = monthly_trx * per_trx_price
    bps_rev = volume * _CS.BPS_FLOOR

    operative = "bps" if bps_rev > per_trx_rev else "trx"
    monthly_txn_rev = max(per_trx_rev, bps_rev)

    # The ATV at which 10 bps overtakes this tier's per-transaction price.
    breakeven = (per_trx_price / _CS.BPS_FLOOR) if _CS.BPS_FLOOR else 0.0

    fee = float(platform_fee)
    if fee >= _CS.PLATFORM_FEE["owner_limit"]:
        approval, appr_tone = "Deal owner, at their discretion", "ok"
    elif fee >= _CS.PLATFORM_FEE["floor"]:
        approval, appr_tone = "Daniela's approval required", "warn"
    else:
        approval, appr_tone = "Not available — trade elsewhere or walk away", "stop"

    return {
        "volume": volume, "monthly_volume": volume, "annual_volume": volume * 12,
        "tier_label": tier_label, "per_trx_price": per_trx_price,
        "per_trx_rev": per_trx_rev, "bps_rev": bps_rev,
        "operative": operative, "breakeven_atv": breakeven,
        "monthly_txn_rev": monthly_txn_rev, "annual_txn_rev": monthly_txn_rev * 12,
        "platform_fee": fee, "annual_platform": fee * 12,
        "annual_total": monthly_txn_rev * 12 + fee * 12,
        "approval": approval, "approval_tone": appr_tone,
    }


def _partner_slug(name):
    return _re.sub(r"[^a-z0-9]+", "", (name or "").lower()) or "partner"


def build_story_deck(name, accent="#00A3E0", category="Fraud", verb="decisioning"):
    """The partner story deck with this partner's name substituted throughout."""
    try:
        path = _os.path.join(_BASE, "assets", "cosell_story_template.html")
        html = open(path, encoding="utf-8").read()
    except Exception:
        return None
    name = (name or "Partner").strip() or "Partner"
    for token, value in [
        ("__PARTNER_NAME__", name),
        ("__PARTNER_SLUG__", _partner_slug(name)),
        ("__PARTNER_ACCENT__", accent),
        ("__PARTNER_CATEGORY__", category),
        ("__PARTNER_VERB__", verb),
        ("__PARTNER_INITIAL__", name[0].upper()),
    ]:
        html = html.replace(token, value)
    return html


def show_cosell():
    """Internal co-sell workspace for the stablecoin sprint."""
    fee_candidates = [p for p in _CS.PROVIDERS if p["platform_fee"]]
    floor_year = _CS.PLATFORM_FEE["floor"] * 12 * len(fee_candidates)
    list_year = _CS.PLATFORM_FEE["list"] * 12 * len(fee_candidates)

    st.markdown(hero(
        _CS.SPRINT["title"], eyebrow="Co-sell mission control",
        subtitle=_CS.SPRINT["subtitle"],
        tiles=[(str(len(_CS.PROVIDERS)), "Providers", "#E0ED80"),
               (str(len(fee_candidates)), "Fee candidates", "#8B9BFF"),
               (_money(floor_year), "At the floor", "#B9C2FF"),
               (_money(list_year), "At list", "#FFD400"),
               (_CS.SPRINT["window"], "Window", "#E68ABE")]),
        unsafe_allow_html=True)

    view = nav_radio("Co-sell view",
                     ["Board", "Movement", "Pricing", "Deck", "Playbook"], "cosell_view")

    {"Board": _cs_tracker, "Movement": _cs_movement, "Pricing": _cs_pricing,
     "Deck": _cs_deck, "Playbook": _cs_playbook}.get(view, _cs_tracker)()


def _cs_payload():
    """Everything the board and the movement view need, as plain JSON."""
    import json as _json
    providers = []
    for p in _CS.PROVIDERS:
        m = _CS.manager(p["owner"])
        providers.append({
            "name": p["name"], "owner": p["owner"], "manager": m["name"],
            "region": m["region"], "accent": m["accent"], "stage": p["stage"],
            "standing": p["standing"], "play": _CS.PLAYS[p["play"]],
            "play_note": p["play_note"], "platform_fee": p["platform_fee"],
            "support": p.get("support"), "owner_plan": p.get("owner_plan"),
        })
    stages = [{"name": n, "color": _STAGE_TONE[i]} for i, n in enumerate(_CS.STAGES)]
    managers = [{"key": m["key"], "name": m["name"], "region": m["region"],
                 "accent": m["accent"]} for m in _CS.MANAGERS]
    if any(p["owner"] == "Unassigned" for p in _CS.PROVIDERS):
        u = _CS.UNASSIGNED
        managers.append({"key": u["key"], "name": u["name"], "region": u["region"],
                         "accent": u["accent"]})
    enc = lambda o: _json.dumps(o).replace("</", "<\\/")
    return enc(providers), enc(stages), enc(managers)


def _cs_component(filename, height):
    """Render one of the co-sell HTML components with the sprint data injected."""
    try:
        path = _os.path.join(_BASE, "assets", filename)
        html = open(path, encoding="utf-8").read()
    except Exception:
        st.markdown(
            f'<div style="padding:16px 19px;background:#FDF8E8;'
            f'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
            f'font-size:12.5px;color:#6E5400;">'
            f'<b>Board component missing.</b> Expected <code>assets/{filename}</code>.</div>',
            unsafe_allow_html=True)
        return
    providers, stages, managers = _cs_payload()
    html = (html.replace("var DATA = [];", f"var DATA = {providers};")
                .replace("var STAGES = [];", f"var STAGES = {stages};")
                .replace("var MANAGERS = [];", f"var MANAGERS = {managers};"))
    components.html(html, height=height, scrolling=False)


def _cs_tracker():
    """The board. Drag a partner between stages; click one to read it."""
    _cs_component("cosell_board.html", 620)
    st.markdown(
        f'<div style="margin-top:2px;">'
        f'{_chip("Yuno_Stablecoin_Provider_Sprint.docx · Draft v1", "data")}'
        f'<span style="font-size:10.5px;color:#858CA6;margin-left:8px;">Stage is a local '
        f'planning view held in this browser — Salesforce remains the tracker.</span></div>',
        unsafe_allow_html=True)


def _cs_movement():
    """Lifecycle overview — what moved since the baseline, and what did not.

    The board keeps stage in the browser, so this reads the same store rather
    than a server-side copy. The baseline rolls on Monday, matching the sprint
    review, and can be re-anchored by hand when the head of the desk wants a
    fresh starting point.
    """
    st.markdown(
        '<div style="font-size:12.5px;color:#676E8A;line-height:1.65;margin-bottom:10px;">'
        'Week-over-week movement across the sprint: which partners advanced, which slipped '
        'back, and which have not moved at all since the baseline was taken.</div>',
        unsafe_allow_html=True)
    _cs_component("cosell_movement.html", 900)
    st.markdown(
        f'<div style="margin-top:2px;">'
        f'{_chip("Yuno_Stablecoin_Provider_Sprint.docx · Draft v1", "data")}'
        f'<span style="font-size:10.5px;color:#858CA6;margin-left:8px;">Movement is measured '
        f'against the stages held in this browser, not Salesforce.</span></div>',
        unsafe_allow_html=True)


def tier_slices(annual_tx):
    """Marginal tiering: each band bills its own slice of the monthly volume."""
    monthly = annual_tx / 12.0
    out, remaining = [], monthly
    for lo, hi, price, note in _PR.TIER_BANDS:
        cap = (hi - lo) if hi is not None else float("inf")
        take = max(0.0, min(remaining, cap))
        out.append({"lo": lo, "hi": hi, "price": price, "note": note,
                    "tx": take, "bills": take * price})
        remaining -= take
        if remaining <= 0:
            remaining = 0.0
    return out, monthly


def price_deal(tpv, annual_tx, complexity, mode, fixed_per_tx, addons_monthly):
    """The workbook's Calculator, end to end.

    Every output derives from the four inputs and the Assumptions tab — the
    effective price per Tx and the control blend are outputs, never entries.
    """
    tpv = max(0.0, float(tpv))
    annual_tx = max(0.0, float(annual_tx))
    addons_monthly = max(0.0, float(addons_monthly))
    atv = (tpv / annual_tx) if annual_tx else 0.0

    implementation = _PR.IMPLEMENTATION_FEE[complexity]
    platform_monthly = _PR.PLATFORM_FEE_MONTHLY[complexity]

    slices, monthly_tx = tier_slices(annual_tx)
    if mode == "Tiered":
        band_total = sum(s["bills"] for s in slices)
        per_tx = (band_total / monthly_tx) if monthly_tx else 0.0
    else:
        per_tx = max(0.0, float(fixed_per_tx))

    platform_addons_annual = (platform_monthly + addons_monthly) * 12
    per_tx_annual = annual_tx * per_tx
    recurring_annual = platform_addons_annual + per_tx_annual
    total_year1 = recurring_annual + implementation

    # The two control outputs.
    effective_per_tx = (recurring_annual / annual_tx) if annual_tx else 0.0
    blend_bps = (recurring_annual / tpv * 10_000) if tpv else 0.0

    # Guards, in the workbook's own terms.
    below_floor = per_tx < _PR.COST_FLOOR_PER_TX
    platform_share = (platform_addons_annual / total_year1) if total_year1 else 0.0
    over_cap = platform_share > _PR.PLATFORM_FEE_CAP
    needs_finance = total_year1 > _PR.FINANCE_REVIEW_THRESHOLD

    if blend_bps < _PR.BLEND_TARGET_BPS:
        blend_state = "under"
    elif blend_bps <= _PR.BLEND_CEILING_BPS:
        blend_state = "healthy"
    else:
        blend_state = "over"

    return {
        "atv": atv, "monthly_tx": monthly_tx, "slices": slices,
        "implementation": implementation, "platform_monthly": platform_monthly,
        "addons_monthly": addons_monthly,
        "platform_addons_annual": platform_addons_annual,
        "per_tx": per_tx, "per_tx_annual": per_tx_annual,
        "recurring_annual": recurring_annual, "total_year1": total_year1,
        "effective_per_tx": effective_per_tx, "blend_bps": blend_bps,
        "blend_state": blend_state, "below_floor": below_floor,
        "platform_share": platform_share, "over_cap": over_cap,
        "needs_finance": needs_finance,
    }


def suggest_complexity(tpv):
    """The primary criterion: deal size by client TPV."""
    if tpv < _PR.TPV_SIMPLE_MAX:
        return "Simple"
    if tpv <= _PR.TPV_MEDIUM_MAX:
        return "Medium"
    return "Complex"


def _md(text):
    """Escape markdown that Streamlit would otherwise interpret in a widget label.

    A pair of dollar signs in a label — "$15k impl · $10k/mo" — is read as LaTeX
    and comes back set in a maths italic, which is where the cursive came from.
    """
    return str(text).replace("\\", "\\\\").replace("$", "\\$")


def _seg(key, options, state_key, default, cols=None):
    """A segmented toggle. Each option is (value, headline, sub)."""
    cur = st.session_state.get(state_key, default)
    with st.container(key=key):
        cc = st.columns(cols or len(options))
        for c, (val, head, sub) in zip(cc, options):
            if c.button(f"{_md(head)}\n\n{_md(sub)}", key=f"{key}_{val}",
                        use_container_width=True,
                        type="primary" if cur == val else "secondary"):
                st.session_state[state_key] = val
                st.rerun()
    return cur


def _cs_pricing():
    st.markdown(
        f'<div style="font-size:12.5px;color:#676E8A;line-height:1.7;margin-bottom:12px;">'
        f'{_h(_PR.PHILOSOPHY)}</div>', unsafe_allow_html=True)

    # ── 1 · Deal inputs ───────────────────────────────────────────────────────
    st.markdown(_section_label("1 · Deal inputs", top=4), unsafe_allow_html=True)
    i1, i2 = st.columns(2)
    tpv = i1.number_input("Client annual TPV ($)", min_value=0, value=1_500_000_000,
                          step=50_000_000, key="px_tpv",
                          help="Total payment volume to process per year.")
    ntx = i2.number_input("Annual transaction volume (#)", min_value=0, value=30_000_000,
                          step=1_000_000, key="px_tx",
                          help="Number of transactions per year.")

    suggested = suggest_complexity(tpv)
    complexity = _seg("segcx",
                      [(c, c, f'${_PR.IMPLEMENTATION_FEE[c]/1000:.0f}k impl · '
                              f'${_PR.PLATFORM_FEE_MONTHLY[c]/1000:.0f}k/mo')
                       for c in _PR.COMPLEXITY],
                      "px_complexity", suggested)
    mode = _seg("segmode",
                [("Fixed", "Fixed", "one flat $/Tx"),
                 ("Tiered", "Tiered", "marginal bands by monthly volume")],
                "px_mode", "Fixed")

    fixed_per_tx = st.session_state.get("px_pertx", 0.02)

    # Preview the per-Tx before charging add-ons, so the input can be shown in place.
    peek = price_deal(tpv, ntx, complexity, mode, fixed_per_tx, 0)
    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:-4px 0 14px;">'
        + "".join(
            f'<span style="font-size:11px;color:#4A5170;background:#F1F3FB;'
            f'border:1px solid rgba(35,42,61,.10);border-radius:6px;padding:4px 10px;'
            f'font-variant-numeric:tabular-nums;">{k} <b style="color:#10131C;">{v}</b></span>'
            for k, v in [("Average ticket", f"{USD}{peek['atv']:,.2f}"),
                         ("Tx / month", f"{peek['monthly_tx']:,.0f}"),
                         ("TPV / month", _money(tpv / 12))])
        + '</div>', unsafe_allow_html=True)

    if complexity != suggested:
        st.markdown(
            f'<div style="padding:11px 14px;background:#FDF8E8;'
            f'border:1px solid rgba(138,106,0,.26);border-radius:9px;font-size:11.5px;'
            f'color:#6E5400;line-height:1.6;margin:-6px 0 12px;font-family:var(--font);">'
            f'TPV of {_money(tpv)} points at <b>{suggested}</b> on the primary criterion. '
            f'You have set <b>{complexity}</b> — fine if the other dimensions justify it.'
            f'</div>', unsafe_allow_html=True)

    # ── 3 · Per-Tx ────────────────────────────────────────────────────────────
    if mode == "Fixed":
        fixed_per_tx = st.number_input(
            "\\$ per transaction", min_value=0.0, value=float(fixed_per_tx), step=0.0025,
            format="%.4f", key="px_pertx",
            help=f"Never below the {USD}{_PR.COST_FLOOR_PER_TX:.2f} cost floor.")
    else:
        st.markdown(_section_label("Bands billing this deal", top=6), unsafe_allow_html=True)
        def _band_row(b):
            hi = f"{b['hi']:,}" if b["hi"] else "+"
            dim = "" if b["tx"] else "opacity:.42;"
            return (
                f'<div style="display:flex;align-items:center;gap:12px;padding:7px 0;'
                f'border-bottom:1px solid rgba(35,42,61,.055);{dim}">'
                f'<span style="font-size:11.5px;color:#10131C;min-width:168px;'
                f'font-variant-numeric:tabular-nums;">{b["lo"]:,} – {hi}</span>'
                f'<span style="font-size:11.5px;color:#2F3FC4;min-width:62px;'
                f'font-variant-numeric:tabular-nums;">{USD}{b["price"]:.4f}</span>'
                f'<span style="font-size:11.5px;color:#676E8A;min-width:110px;'
                f'font-variant-numeric:tabular-nums;">{b["tx"]:,.0f} tx</span>'
                f'<span style="font-size:11.5px;font-weight:600;color:#10131C;'
                f'font-variant-numeric:tabular-nums;">{_money(b["bills"])}/mo</span>'
                f'<span style="margin-left:auto;font-size:10.5px;color:#858CA6;">'
                f'{b["note"]}</span></div>')

        rows = "".join(_band_row(b) for b in peek["slices"])
        st.markdown(
            f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            f'border-radius:14px;padding:15px 18px;margin-bottom:12px;'
            f'font-family:var(--font);">{rows}'
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:11px;'
            f'padding-top:10px;border-top:1px solid rgba(35,42,61,.10);">'
            f'<span style="font-size:11px;font-weight:600;letter-spacing:.09em;'
            f'text-transform:uppercase;color:#858CA6;">Equivalent {USD}/Tx</span>'
            f'<span style="margin-left:auto;font-size:15px;font-weight:700;color:#10131C;'
            f'font-variant-numeric:tabular-nums;">{USD}{peek["per_tx"]:.4f}</span></div></div>',
            unsafe_allow_html=True)

    # ── 4 · Add-ons ───────────────────────────────────────────────────────────
    st.markdown(_section_label(f"Add-ons · what you leave at {USD}0 is a lever"),
                unsafe_allow_html=True)
    addons_total = 0.0
    acols = st.columns(4)
    for n, (name, note, free) in enumerate(_PR.ADDONS):
        with acols[n % 4]:
            addons_total += st.number_input(
                name, min_value=0.0, value=0.0, step=250.0, key=f"px_addon_{n}",
                help=note, format="%.0f")
            st.markdown(
                f'<div style="font-size:9.5px;color:{"#37610A" if free else "#8A4B00"};'
                f'margin:-10px 0 10px;line-height:1.4;font-family:var(--font);">'
                f'{"Free to Yuno — lever" if free else "Third-party cost"}</div>',
                unsafe_allow_html=True)

    r = price_deal(tpv, ntx, complexity, mode, fixed_per_tx, addons_total)

    # ── Result ────────────────────────────────────────────────────────────────
    st.markdown(_section_label("Result · both figures are outputs, never entries"),
                unsafe_allow_html=True)
    flag = {"healthy": ("#E0ED80", f"Within healthy range "
                                   f"({_PR.BLEND_TARGET_BPS}–{_PR.BLEND_CEILING_BPS} bps)"),
            "under": ("#5FD4E8", f"Below the {_PR.BLEND_TARGET_BPS} bps market centre — "
                                 f"room to charge more"),
            "over": ("#FF6B7D", f"Above the {_PR.BLEND_CEILING_BPS} bps ceiling — "
                                f"pull a lever back")}[r["blend_state"]]
    floor_flag = ("" if not r["below_floor"] else
                  f'<div class="px-band"><span class="px-dot" style="background:#FF6B7D;"></span>'
                  f'<span class="px-flag" style="color:#FF6B7D;">Below the '
                  f'{USD}{_PR.COST_FLOOR_PER_TX:.2f} cost floor</span></div>')
    st.markdown(
        f'<div class="px-out">'
        f'<div class="px-big"><div class="px-k">Effective price per Tx</div>'
        f'<div class="px-v" style="color:#EEF0FA;">{USD}{r["effective_per_tx"]:.4f}</div>'
        f'<div class="px-s">Recurring revenue ÷ annual transactions</div>{floor_flag}</div>'
        f'<div class="px-big"><div class="px-k">Control blend</div>'
        f'<div class="px-v" style="color:{flag[0]};">{r["blend_bps"]:.1f}'
        f'<span style="font-size:15px;font-weight:600;letter-spacing:0;"> bps</span></div>'
        f'<div class="px-s">Recurring revenue as bps on TPV</div>'
        f'<div class="px-band"><span class="px-dot" style="background:{flag[0]};'
        f'box-shadow:0 0 7px {flag[0]};"></span>'
        f'<span class="px-flag" style="color:{flag[0]};">{flag[1]}</span></div></div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="display:flex;gap:9px;flex-wrap:wrap;margin-bottom:12px;">' + "".join(
            f'<div style="flex:1;min-width:142px;background:#fff;'
            f'border:1px solid rgba(35,42,61,.10);border-radius:12px;padding:14px 16px;'
            f'font-family:var(--font);">'
            f'<div style="font-size:9px;font-weight:600;letter-spacing:.09em;'
            f'text-transform:uppercase;color:#858CA6;margin-bottom:6px;">{k}</div>'
            f'<div style="font-size:18px;font-weight:700;color:{c};letter-spacing:-.02em;'
            f'font-variant-numeric:tabular-nums;">{v}</div></div>'
            for k, v, c in [
                ("Implementation", _money(r["implementation"]), "#676E8A"),
                ("Platform / mo", _money(r["platform_monthly"]), "#0086A8"),
                ("Add-ons / mo", _money(r["addons_monthly"]), "#0086A8"),
                ("Platform + add-ons annual", _money(r["platform_addons_annual"]), "#0086A8"),
                ("Per-Tx annual", _money(r["per_tx_annual"]), "#3E4FE0"),
                ("Recurring annual", _money(r["recurring_annual"]), "#3E4FE0"),
                ("Total year 1", _money(r["total_year1"]), "#37610A")])
        + '</div>', unsafe_allow_html=True)

    # ── Guards ────────────────────────────────────────────────────────────────
    guards = []
    if r["below_floor"]:
        guards.append(("stop", f'Per-Tx of {USD}{r["per_tx"]:.4f} is below the '
                               f'{USD}{_PR.COST_FLOOR_PER_TX:.2f} cost floor. This one does not bend.'))
    if r["over_cap"]:
        guards.append(("warn", f'Platform + add-ons is {r["platform_share"]*100:.0f}% of total '
                               f'revenue, over the {_PR.PLATFORM_FEE_CAP*100:.2f}% cap.'))
    if r["needs_finance"]:
        guards.append(("info", f'Total year 1 of {_money(r["total_year1"])} is over '
                               f'{_money(_PR.FINANCE_REVIEW_THRESHOLD)} — Finance + Product sign-off.'))
    tone = {"stop": ("#FBECEE", "#8C2233", "rgba(140,34,51,.24)"),
            "warn": ("#FDF8E8", "#8A4B00", "rgba(138,106,0,.28)"),
            "info": ("#E9ECFC", "#2F3FC4", "rgba(84,104,245,.22)")}
    for kind, text in guards:
        bg, ink, br = tone[kind]
        st.markdown(
            f'<div style="padding:12px 15px;background:{bg};border:1px solid {br};'
            f'border-radius:10px;font-size:12px;color:{ink};line-height:1.6;margin-bottom:8px;'
            f'font-family:var(--font);">{text}</div>', unsafe_allow_html=True)

    with st.expander("How to classify complexity"):
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:12px;'
            'padding:14px 17px;font-family:var(--font);">' + "".join(
                f'<div style="display:flex;gap:14px;padding:8px 0;flex-wrap:wrap;'
                f'border-bottom:1px solid rgba(35,42,61,.055);">'
                f'<span style="font-size:12px;color:#10131C;flex:1;min-width:210px;">'
                f'{star}{dim}{prim}</span>'
                f'<span style="font-size:11.5px;color:#676E8A;flex:1.3;min-width:230px;">'
                f'{_h(how)}</span></div>'
                for dim, tag, how, star, prim in (
                    (d, t, h, "★ " if t else "",
                     ' <span style="color:#858CA6;">(primary)</span>' if t else "")
                    for d, t, h in _PR.COMPLEXITY_GUIDE))
            + f'<div style="font-size:11.5px;color:#676E8A;line-height:1.65;margin-top:10px;">'
            f'{_h(_PR.COMPLEXITY_RULE)}</div></div>', unsafe_allow_html=True)

    with st.expander("Floors, caps and the benchmark"):
        st.markdown(
            f'<div style="font-size:12px;color:#4A5170;line-height:1.75;'
            f'font-family:var(--font);">{_h(_PR.NEVER_BEND)}<br><br>'
            f'Cost floor <b>{USD}{_PR.COST_FLOOR_PER_TX:.2f}</b> per transaction · '
            f'platform fee capped at <b>{_PR.PLATFORM_FEE_CAP*100:.2f}%</b> of total deal '
            f'revenue · blend target <b>{_PR.BLEND_TARGET_BPS} bps</b> for pure '
            f'orchestration, <b>{_PR.BLEND_CEILING_BPS} bps</b> ceiling with value add-ons · '
            f'support person cost <b>{_money(_PR.SUPPORT_COST_MONTHLY)}</b> per month is '
            f'context only and never enters the formula.<br><br>'
            f'{_h(_PR.LANDING_BENCHMARK_NOTE)}<br><br>{_h(_PR.REVIEW_NOTE)}</div>',
            unsafe_allow_html=True)

    with st.expander("Stablecoin sprint pricing — the separate playbook"):
        st.markdown(
            f'<div style="font-size:12px;color:#4A5170;line-height:1.7;'
            f'font-family:var(--font);">The nine stablecoin providers price off their own '
            f'sheet, not this one: platform fee '
            f'<b>{_money(_CS.PLATFORM_FEE["list"])}</b> list with a '
            f'<b>{_money(_CS.PLATFORM_FEE["floor"])}</b> floor, transaction tiers from '
            f'<b>{USD}0.08</b>, and the greater-of rule against 10 bps. '
            f'{_h(_CS.PRICING_RULE)}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="margin-top:9px;">' + "".join(
                f'<div style="display:flex;align-items:center;gap:11px;padding:6px 0;'
                f'border-bottom:1px solid rgba(35,42,61,.055);font-family:var(--font);">'
                f'<span style="width:19px;height:19px;border-radius:5px;background:#E9ECFC;'
                f'color:#2F3FC4;font-size:10px;font-weight:700;display:grid;'
                f'place-items:center;flex-shrink:0;">{i+1}</span>'
                f'<span style="font-size:12px;color:#10131C;">{_h(c)}</span></div>'
                for i, c in enumerate(_CS.CONCESSION_ORDER)) + '</div>',
            unsafe_allow_html=True)

    st.markdown(
        f'<div style="margin-top:10px;">'
        f'{_chip("Pricing_Calculator_Financial_Services.xlsx", "data")}</div>',
        unsafe_allow_html=True)


# ── Partner deck ──────────────────────────────────────────────────────────────
_DECK_PRESETS = {
    "Stablecoin / crypto": ("Stablecoin", "settlement", "#00A3E0"),
    "Fraud / risk":        ("Fraud", "decisioning", "#00A3E0"),
    "Acquirer":            ("Acquirer", "acquiring", "#3E4FE0"),
    "PSP":                 ("PSP", "processing", "#5A7A00"),
    "Wallet":              ("Wallet", "wallet rail", "#C24E00"),
}


def _cs_deck():
    """One artefact, one action. Choose the partner, see it, take it."""
    names = [p["name"] for p in _CS.PROVIDERS]

    # ── Who it is for ────────────────────────────────────────────────────────
    st.markdown(_section_label("Who the deck is for", top=4), unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    pick = c1.selectbox("Partner", names + ["Type a name…"], key="cs_deck_pick",
                        label_visibility="collapsed")
    preset = c2.selectbox("Partner type", list(_DECK_PRESETS), key="cs_deck_preset",
                          label_visibility="collapsed")
    if pick == "Type a name…":
        partner = (st.text_input("Partner name", placeholder="Partner name",
                                 key="cs_deck_name",
                                 label_visibility="collapsed") or "").strip()
    else:
        partner = pick
    partner = partner or "Partner"

    cat, verb, default_accent = _DECK_PRESETS[preset]
    accent = st.session_state.get("cs_deck_accent", default_accent)
    html = build_story_deck(partner, accent=accent, category=cat, verb=verb)
    if html is None:
        st.markdown(
            '<div style="padding:16px 19px;background:#FDF8E8;'
            'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
            'font-size:12.5px;color:#6E5400;">'
            '<b>Deck template missing.</b> Expected '
            '<code>assets/cosell_story_template.html</code>.</div>', unsafe_allow_html=True)
        return

    # ── The artefact, and the one action ─────────────────────────────────────
    st.markdown(
        f'<div style="background:linear-gradient(150deg,#0E1119,#141827 60%,#191E2F);'
        f'border:1px solid #232A3D;border-radius:14px;padding:20px 22px;margin:2px 0 10px;'
        f'position:relative;overflow:hidden;font-family:var(--font);">'
        f'<div style="position:absolute;top:-80px;right:-60px;width:300px;height:300px;'
        f'border-radius:50%;background:radial-gradient(circle,{accent}2E,transparent 66%);'
        f'pointer-events:none;"></div>'
        f'<div style="position:relative;z-index:1;display:flex;align-items:center;gap:14px;'
        f'flex-wrap:wrap;">'
        f'<span style="display:grid;place-items:center;width:42px;height:42px;'
        f'border-radius:11px;background:{accent};color:#0E0F14;font-weight:700;'
        f'font-size:20px;flex-shrink:0;">{partner[0].upper()}</span>'
        f'<div style="min-width:0;">'
        f'<div style="font-size:18px;font-weight:600;color:#EEF0FA;letter-spacing:-.02em;">'
        f'Yuno &times; {partner}</div>'
        f'<div style="font-size:11px;color:#8991AC;margin-top:3px;">'
        f'{cat} · 15 scenes · {len(html)//1024}&nbsp;KB · one self-contained file</div>'
        f'</div></div></div>', unsafe_allow_html=True)

    a1, a2, _sp = st.columns([1, 1, 2.1])
    a1.download_button("Download", data=html.encode("utf-8"),
                       file_name=f"yuno-{_partner_slug(partner)}-story.html",
                       mime="text/html", use_container_width=True, type="primary",
                       key="cs_deck_dl")
    show = a2.toggle("Preview", key="cs_deck_preview")

    # ── Preview sits where the eye already is, not below the fold ────────────
    if show:
        components.html(html, height=520, scrolling=False)

    # ── Everything else is one click down ────────────────────────────────────
    with st.expander("Appearance"):
        st.color_picker("Accent colour", default_accent, key="cs_deck_accent")
        st.markdown(
            f'<div style="font-size:11.5px;color:#676E8A;line-height:1.7;'
            f'font-family:var(--font);">The partner type sets two things the accent '
            f'cannot: the network-ring label (<b>{cat}</b>) and the phrase the narrative '
            f'uses for their step (&ldquo;{partner} {verb}&rdquo;).</div>',
            unsafe_allow_html=True)

    with st.expander("What gets substituted"):
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            'border-radius:12px;padding:14px 17px;font-family:var(--font);">' + "".join(
                f'<div style="display:flex;gap:14px;padding:7px 0;flex-wrap:wrap;'
                f'border-bottom:1px solid rgba(35,42,61,.055);">'
                f'<span style="font-size:11.5px;color:#858CA6;flex:1;min-width:150px;">'
                f'{where}</span>'
                f'<span style="font-size:12px;color:#10131C;flex:1.4;min-width:210px;'
                f'font-weight:500;">{what}</span></div>'
                for where, what in [
                    ("Title and lockup", f"Yuno &times; {partner}, with a {partner[0].upper()} monogram"),
                    ("Connector mock", f"connectors/{_partner_slug(partner)}.yuno"),
                    ("Network ring", f"{partner} listed as {cat}"),
                    ("Narrative phrase", f"&ldquo;{partner} {verb}&rdquo;"),
                    ("Accent colour", f'<span style="color:{accent};">{accent}</span>'),
                ]) + '</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="margin-top:9px;padding:10px 13px;background:#FDF8E8;'
            'border:1px solid rgba(138,106,0,.26);border-radius:9px;font-size:11.5px;'
            'color:#6E5400;line-height:1.6;font-family:var(--font);">'
            'The narrative still describes a decisioning-style integration — read it through '
            'before sending to a partner whose motion is different.</div>',
            unsafe_allow_html=True)


# ── Playbook ──────────────────────────────────────────────────────────────────
def _cs_playbook():
    for s_ in _CS.PLAYBOOK:
        with st.expander(f'{s_["n"]} · {s_["title"]}'):
            st.markdown(
                f'<div style="font-size:10px;font-weight:600;letter-spacing:.11em;'
                f'text-transform:uppercase;color:#2F3FC4;margin-bottom:9px;'
                f'font-family:var(--font);">{s_["when"]}</div>' + "".join(
                    f'<div style="font-size:12.5px;color:#4A5170;line-height:1.7;'
                    f'margin-bottom:9px;font-family:var(--font);">{b}</div>'
                    for b in s_["body"])
                + f'<div style="margin-top:6px;padding:10px 13px;background:#EAF3E3;'
                f'border:1px solid rgba(55,97,10,.20);border-radius:9px;font-size:12px;'
                f'color:#2E5208;line-height:1.6;font-family:var(--font);">'
                f'<b>Done when</b> · {s_["done"]}</div>', unsafe_allow_html=True)

    st.markdown(_section_label("Contracts"), unsafe_allow_html=True)
    for tag, title, body in _CS.CONTRACTS:
        with st.expander(f"{tag} · {title}"):
            st.markdown(
                f'<div style="font-size:12.5px;color:#4A5170;line-height:1.7;'
                f'font-family:var(--font);">{body}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="padding:13px 16px;background:#FDF8E8;border:1px solid rgba(138,106,0,.26);'
        f'border-radius:10px;font-size:12px;color:#6E5400;line-height:1.65;'
        f'font-family:var(--font);">{_CS.LEGAL_DEPENDENCY}</div>', unsafe_allow_html=True)

    st.markdown(_section_label("Decisions needed before we start"), unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:14px;'
        'padding:16px 18px;font-family:var(--font);">' + "".join(
            f'<div style="display:flex;gap:11px;padding:8px 0;'
            f'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<span style="width:19px;height:19px;border-radius:5px;background:#FDF8E8;'
            f'color:#8A4B00;font-size:10px;font-weight:700;display:grid;place-items:center;'
            f'flex-shrink:0;">{i+1}</span>'
            f'<span style="font-size:12.5px;color:#10131C;line-height:1.6;">{d}</span></div>'
            for i, d in enumerate(_CS.DECISIONS)) + '</div>', unsafe_allow_html=True)

    with st.expander("Appendix A · Sample outreach note"):
        st.markdown(
            '<div style="font-size:11.5px;color:#676E8A;margin-bottom:8px;'
            'font-family:var(--font);">Adapt it to each provider. It should read like it '
            'came from you, not from a campaign.</div>', unsafe_allow_html=True)
        st.code(_CS.OUTREACH_NOTE, language=None)

    with st.expander("Appendix B · Data request"):
        _cs_data_request()


def _cs_data_request():
    st.markdown(
        '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:14px;'
        'padding:16px 18px;font-family:var(--font);">' + "".join(
            f'<div style="display:flex;gap:16px;padding:8px 0;flex-wrap:wrap;'
            f'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<span style="font-size:12.5px;color:#10131C;flex:1;min-width:220px;'
            f'line-height:1.55;">{what}</span>'
            f'<span style="font-size:11.5px;color:#676E8A;flex:1;min-width:220px;'
            f'line-height:1.55;">{why}</span></div>'
            for what, why in _CS.DATA_REQUEST)
        + '<div style="font-size:11.5px;color:#8A4B00;margin-top:10px;line-height:1.6;">'
        'No data, no pricing.</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="margin-top:10px;">'
                f'{_chip("Yuno_Stablecoin_Provider_Sprint.docx · Draft v1", "data")}</div>',
                unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_finx_leads():
    """Every partner still at the front of the funnel, with the owner on record."""
    if not _ACCOUNTS_BOOK:
        return []
    try:
        df = pd.read_excel(_ACCOUNTS_BOOK, sheet_name="All Partners")
    except Exception:
        return []
    early = ("Opportunity Identification", "Initial Negotiation")
    out = []
    for _, r in df.iterrows():
        name = str(r.get("Partner Name", "") or "").strip()
        stage = str(r.get("Deal Stage", "") or "").strip()
        if not name or stage not in early:
            continue
        out.append({
            "name": name,
            "region": str(r.get("Region", "") or "—").strip(),
            "country": str(r.get("Country", "") or "—").strip(),
            "stage": stage,
            "type": str(r.get("Type", "") or "—").strip(),
            "owner": str(r.get("Partner Manager", "") or "Unassigned").strip() or "Unassigned",
        })
    out.sort(key=lambda x: (x["stage"] != "Initial Negotiation", x["name"].lower()))
    return out


# ══ Lead generation ════════════════════════════════════════════════════════════
# Where the next leads come from, who is working which route this week, and the
# tip that makes each one land. Two tracks: merchant demand, and the financial
# institutions that carry it.

def _lg_play_card(pl):
    pc, pnote = _LG.PRIORITIES[pl["p"]]
    tr = _LG.TRACKS[pl["track"]]
    owner = pl["owner"]
    own_accent = ("#676E8A" if owner == "Desk"
                  else _CS.manager(owner)["accent"] if _CS else "#3E4FE0")
    return (
        f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
        f'border-left:3px solid {pc};border-radius:13px;padding:15px 17px;margin-bottom:9px;'
        f'box-shadow:var(--shadow);font-family:var(--font);">'
        f'<div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:8px;">'
        f'<span style="font-size:9.5px;font-weight:700;letter-spacing:.06em;padding:2px 7px;'
        f'border-radius:5px;background:{pc}18;color:{pc};border:1px solid {pc}38;">'
        f'{pl["p"]}</span>'
        f'<span style="font-size:14px;font-weight:600;color:#10131C;letter-spacing:-.012em;">'
        f'{pl["title"]}</span>'
        f'<span style="margin-left:auto;font-size:10px;font-weight:600;letter-spacing:.06em;'
        f'text-transform:uppercase;padding:2px 8px;border-radius:5px;'
        f'background:{tr["accent"]}14;color:{tr["accent"]};">{pl["track"]}</span></div>'
        f'<div style="font-size:12.5px;color:#4A5170;line-height:1.7;margin-bottom:10px;">'
        f'{pl["task"]}</div>'
        f'<div style="padding:10px 13px;background:#F1F3FB;border-radius:9px;'
        f'font-size:11.5px;color:#3A4155;line-height:1.65;margin-bottom:10px;">'
        f'<b style="color:#2F3FC4;">Tip</b> · {pl["tip"]}</div>'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;'
        f'padding-top:9px;border-top:1px solid rgba(35,42,61,.07);">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{own_accent};'
        f'flex-shrink:0;"></span>'
        f'<span style="font-size:11.5px;font-weight:600;color:#10131C;">{owner}</span>'
        f'<span style="font-size:11px;color:#858CA6;">· {pl["cadence"]}</span>'
        f'<span style="margin-left:auto;font-size:11px;color:#676E8A;'
        f'font-variant-numeric:tabular-nums;">Target <b style="color:#10131C;">'
        f'{pl["target"]}</b></span></div></div>')


# ══ Joint go-to-market · shared collateral ═════════════════════════════════════
# One shelf for what Yuno and a partner sell with together. Yuno's side is
# generated or filed here; the partner's side is whatever they upload once the
# contributions toggle is on. Comments sit on the asset they are about, and
# every upload or comment is announced to the partnerships channel.

_GTM_UPLOADS = _os.path.join(_BASE, "data", "gtm_uploads")
_GTM_LIBRARY = _os.path.join(_BASE, "data", "gtm_library.jsonl")
_GTM_COMMENTS = _os.path.join(_BASE, "data", "gtm_comments.jsonl")
_GTM_KINDS = ["Deck", "Brief", "One-pager", "Case study", "Battlecard", "Co-marketing", "Other"]
_GTM_TONE = {"Deck": "#2F3FC4", "Brief": "#B36200", "One-pager": "#00697F", "Case study": "#37610A",
             "Battlecard": "#7A2233", "Co-marketing": "#C4187F", "Other": "#5A6486"}
_GTM_ALLOWED = ["pdf", "pptx", "ppt", "docx", "doc", "xlsx", "csv", "png", "jpg", "jpeg", "gif", "mp4", "html", "key"]


def _gtm_slug(res):
    return _partner_slug(res.get("company") or res.get("domain") or "partner")


def _deck_preset_for(acct):
    """Which story-deck angle fits this partner, from its offering in the book."""
    t = (acct or {}).get("type", "") or ""
    n = ((acct or {}).get("name", "") or "").lower()
    if any(w in n for w in _CRYPTO_WORDS):
        return _DECK_PRESETS["Stablecoin / crypto"]
    if t.startswith("Fraud"):
        return _DECK_PRESETS["Fraud / risk"]
    if t.startswith("PSP"):
        return _DECK_PRESETS["PSP"]
    if t == "APM":
        return _DECK_PRESETS["Wallet"]
    return _DECK_PRESETS["Acquirer"]


def _read_jsonl(path):
    import json as _json
    try:
        with open(path) as f:
            return [_json.loads(x) for x in f if x.strip()]
    except Exception:
        return []


def _append_jsonl(path, record):
    import json as _json
    _os.makedirs(_os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(_json.dumps(record) + "\n")


def gtm_assets(res):
    """Everything on this partner's shelf: Yuno's pieces first, then their uploads."""
    acct = res.get("account") or {}
    company = res.get("company") or company_from_domain(signed_in_email()) or "Partner"
    out = []
    cat, verb, accent = _deck_preset_for(acct)
    deck = build_story_deck(company, accent=accent, category=cat, verb=verb)
    if deck:
        out.append({"id": "yuno-story-deck", "kind": "Deck", "by": "Yuno",
                    "title": f"Yuno × {company} — partner story",
                    "desc": f"The joint narrative deck, with {company} named throughout. Opens in any browser; present it as-is or lift the slides.",
                    "file": f"yuno-x-{_partner_slug(company)}-story.html", "mime": "text/html",
                    "data": deck.encode("utf-8"), "ts": ""})
    if "adyen" in company.lower():
        p = _os.path.join(_BASE, "Copy of Yuno-Adyen Partnership Brief_Final v6.docx.pdf")
        if _os.path.exists(p):
            out.append({"id": "yuno-brief-adyen", "kind": "Brief", "by": "Yuno",
                        "title": "Yuno × Adyen — partnership brief (v6)",
                        "desc": "The commercial brief behind the partnership: scope, merchant revenue gap, joint plan.",
                        "file": "Yuno-Adyen-Partnership-Brief-v6.pdf", "mime": "application/pdf", "path": p, "ts": ""})
    slug = _gtm_slug(res)
    for r in _read_jsonl(_GTM_LIBRARY):
        if r.get("slug") == slug and _os.path.exists(r.get("path", "")):
            out.append({**r, "by": r.get("by") or "You", "mime": r.get("mime") or "application/octet-stream"})
    return out


def gtm_comments(res):
    slug = _gtm_slug(res)
    return [c for c in _read_jsonl(_GTM_COMMENTS) if c.get("slug") == slug]


def gtm_upload(res, uploaded, kind, title, desc):
    """Save the file under the partner's own folder, register it, tell Yuno."""
    import datetime as _dt
    slug = _gtm_slug(res)
    folder = _os.path.join(_GTM_UPLOADS, slug)
    _os.makedirs(folder, exist_ok=True)
    stamp = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe = _re.sub(r"[^A-Za-z0-9._-]+", "_", uploaded.name)
    path = _os.path.join(folder, f"{stamp}_{safe}")
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    company = res.get("company") or company_from_domain(signed_in_email()) or "Partner"
    record = {"id": f"up-{stamp}", "slug": slug, "company": company, "kind": kind,
              "title": title or uploaded.name, "desc": desc, "file": uploaded.name, "path": path,
              "mime": uploaded.type, "size": int(uploaded.size), "by": "You",
              "uploader": signed_in_email(), "ts": _dt.datetime.utcnow().isoformat() + "Z"}
    _append_jsonl(_GTM_LIBRARY, record)
    acct = res.get("account") or {}
    _slack_send(f":open_file_folder: *{company} added GTM collateral* — {kind}: *{record['title']}*\n"
                f"{desc}\n_{uploaded.name} · {uploaded.size/1024:.0f} KB · saved to `{_os.path.relpath(path, _BASE)}` · "
                f"partner manager {_manager_mention(acct.get('manager', ''))}_")
    return record


def gtm_comment(res, asset, text):
    import datetime as _dt
    company = res.get("company") or company_from_domain(signed_in_email()) or "Partner"
    record = {"slug": _gtm_slug(res), "company": company, "asset_id": asset["id"], "asset": asset["title"],
              "text": text, "by": signed_in_email(), "ts": _dt.datetime.utcnow().isoformat() + "Z"}
    _append_jsonl(_GTM_COMMENTS, record)
    acct = res.get("account") or {}
    return _slack_send(f":speech_balloon: *{company} commented on* _{asset['title']}_\n> {text}\n"
                       f"_partner manager {_manager_mention(acct.get('manager', ''))} · via the Partner Alliance_")


# ── Joint GTM · sections ───────────────────────────────────────────────────────
# Five shelves behind one switch. Decks is the collateral shelf; Events and
# Enablement are things the two teams run together — Yuno's entries come from
# the shared logs, the partner's proposals and requests go in through the
# forms; the two contact matrices are who-to-call, in both directions.

_GTM_EVENTS = _os.path.join(_BASE, "data", "gtm_events.jsonl")
_GTM_ENABLE = _os.path.join(_BASE, "data", "gtm_enablement.jsonl")
_GTM_MATRIX = _os.path.join(_BASE, "data", "contact_matrix")

_GTM_SECTIONS = [("decks", "Decks"), ("events", "Events"), ("enablement", "Enablement Sessions"),
                 ("yuno_matrix", "Contact Matrix Yuno"), ("partner_matrix", "Upload Contact Matrix Partner")]

_EVENT_FORMATS = ["Joint webinar", "Conference · shared stand", "Roundtable / dinner", "Merchant workshop",
                  "Launch announcement", "Other"]

# What Yuno runs with a partner. The product workshop is the sprint's own
# format (data/cosell.py); the rest are the standing sessions the team offers.
_ENABLEMENT_CATALOGUE = [
    ("Platform & routing overview", "60 min", "How merchants connect once to Yuno and reach every provider — routing, smart retries, tokenisation. For your commercial team."),
    ("Technical API session", "60 min", "You present your API for 30 minutes; we spend 30 on how it connects into Yuno. Bring product or solutions engineering — it is a technical session, not a second sales call."),
    ("Co-sell playbook", "45 min", "How a joint lead moves: who owns it, the 48-hour first contact, what to send and when. For anyone who will refer merchants."),
    ("Market deep-dive", "45 min", "One market, end to end — mix, regulation, settlement, who is live — and where you and Yuno win together."),
    ("Partner Alliance walkthrough", "30 min", "This portal: your record, health, GTM shelf and how to send Yuno updates and leads."),
]

_MATRIX_ROLES = ["Partnership lead", "Commercial", "Technical / integration", "Support / operations",
                 "Finance / settlement", "Escalation"]


def _gtm_toggle():
    """The section switch, remembered across reruns."""
    keys = [k for k, _ in _GTM_SECTIONS]
    labels = dict(_GTM_SECTIONS)
    pick = st.radio("Section", keys, format_func=lambda k: labels[k], horizontal=True,
                    key="gtm_section", label_visibility="collapsed")
    return pick


def yuno_contact_matrix(acct):
    """Who at Yuno a partner should call, and for what."""
    region = (acct or {}).get("region") or "Global"
    manager = (acct or {}).get("manager") or _ESCALATION
    pool = _RT.REGION_ROUTING.get(region, []) if _RT else []
    by_key = {b["key"]: b for b in _RT.BDMS} if _RT else {}
    bdms = ", ".join(by_key[k]["name"] for k in pool if k in by_key) or "via your partner manager"
    gm = gm_for_region(region)["name"] if _RT else "Regional GM"
    return [
        ("Partner manager", manager, "Your first call for anything — commercials, the record, the plan.", "#3E4FE0"),
        ("Regional BD", bdms, f"Merchant leads and co-sell in {region}. Every referred merchant lands here within 48h.", "#0086A8"),
        ("Regional GM", gm, "Named on every lead alert; the executive sponsor for the region.", "#5A6486"),
        ("Solutions engineering", "via your partner manager", "Integration scoping, certification, the technical API session.", "#7A2233"),
        ("Partner support", "via your partner manager", "Live issues on volume already flowing through Yuno.", "#B36200"),
        ("Escalation", _ESCALATION, "When something is stuck. Head of Partnerships.", "#C4187F"),
    ]


def partner_matrix_path(res):
    return _os.path.join(_GTM_MATRIX, f"{_gtm_slug(res)}.json")


def load_partner_matrix(res):
    """The partner's own matrix if they have saved one, else what Yuno holds on file."""
    import json as _json
    try:
        with open(partner_matrix_path(res)) as f:
            d = _json.load(f)
            return d.get("rows", []), d.get("saved", ""), True
    except Exception:
        pass
    name = ((res.get("account") or {}).get("name") or res.get("company") or "").upper().strip()
    src = (_EXT_CONTACTS.get(name) if "_EXT_CONTACTS" in globals() and _EXT_CONTACTS else None) or _enrichment_for(name) or {}
    rows = []
    if src.get("commercial_contact"):
        rows.append({"Role": "Commercial", "Name": src["commercial_contact"], "Email": src.get("commercial_email", ""),
                     "Phone": src.get("commercial_phone", ""), "Notes": "on file with Yuno"})
    if src.get("technical_contact"):
        rows.append({"Role": "Technical / integration", "Name": src["technical_contact"], "Email": src.get("technical_email", ""),
                     "Phone": src.get("technical_phone", ""), "Notes": "on file with Yuno"})
    return rows, "", False


def save_partner_matrix(res, rows, how):
    import json as _json, datetime as _dt
    _os.makedirs(_GTM_MATRIX, exist_ok=True)
    company = res.get("company") or company_from_domain(signed_in_email()) or "Partner"
    doc = {"company": company, "slug": _gtm_slug(res), "saved": _dt.datetime.utcnow().isoformat() + "Z",
           "by": signed_in_email(), "how": how, "rows": rows}
    with open(partner_matrix_path(res), "w") as f:
        _json.dump(doc, f, indent=2)
    acct = res.get("account") or {}
    lines = "\n".join(f"• *{r.get('Role') or '—'}* — {r.get('Name') or '—'} · {r.get('Email') or '—'}"
                      + (f" · {r['Phone']}" if r.get("Phone") else "") for r in rows)
    return _slack_send(f":busts_in_silhouette: *{company} updated their contact matrix* ({how}, {len(rows)} contacts)\n{lines}\n"
                       f"_partner manager {_manager_mention(acct.get('manager', ''))} · saved to "
                       f"`{_os.path.relpath(partner_matrix_path(res), _BASE)}`_")


def _matrix_from_upload(up):
    """Read a CSV/XLSX and map its columns onto the matrix, however they are named."""
    try:
        df = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
    except Exception:
        return None
    cols = {c: str(c).strip().lower() for c in df.columns}
    def pick(*words):
        for c, lc in cols.items():
            if any(w in lc for w in words):
                return c
        return None
    m = {"Role": pick("role", "function", "title"), "Name": pick("name", "contact"),
         "Email": pick("email", "mail"), "Phone": pick("phone", "tel", "mobile"), "Notes": pick("note", "comment", "scope")}
    rows = []
    for _, r in df.iterrows():
        row = {k: (str(r[c]).strip() if c is not None and str(r[c]) != "nan" else "") for k, c in m.items()}
        if row["Name"] or row["Email"]:
            rows.append(row)
    return rows


def _gtm_event_list(res, contrib):
    company = res.get("company") or "you"
    slug = _gtm_slug(res)
    events = [e for e in _read_jsonl(_GTM_EVENTS) if e.get("slug") in (slug, "*")]
    st.markdown(_section_label(f"Joint events · {len(events)}", top=16), unsafe_allow_html=True)
    if not events:
        st.markdown(f'<div style="background:#fff;border:1px dashed #D5D9E8;border-radius:12px;padding:20px;text-align:center;'
                    f'font-size:12.5px;color:#676E8A;font-family:var(--font);">No joint events on the calendar with {company} yet. '
                    f'{"Propose one below." if contrib else "Switch on Partner contributions to propose one."}</div>',
                    unsafe_allow_html=True)
    else:
        events.sort(key=lambda e: e.get("date", ""), reverse=True)
        tone = {"proposed": "#B36200", "confirmed": "#37610A", "done": "#5A6486"}
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;padding:6px 18px;font-family:var(--font);">'
            + "".join(
                f'<div style="display:flex;gap:14px;align-items:flex-start;padding:11px 0;border-bottom:1px solid rgba(35,42,61,.06);">'
                f'<div style="min-width:78px;font-family:var(--mono);font-size:11px;color:#10131C;padding-top:2px;">{e.get("date") or "TBC"}</div>'
                f'<div style="flex:1;"><div style="font-size:13.5px;font-weight:600;color:#10131C;">{e["title"]}</div>'
                f'<div style="font-size:11.5px;color:#4A5170;margin-top:2px;line-height:1.5;">{e.get("format","")}'
                + (f' · {e["where"]}' if e.get("where") else "") + (f'<br>{e["body"]}' if e.get("body") else "") + '</div></div>'
                f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap;'
                f'background:{tone.get(e.get("status","proposed"), "#5A6486")}14;color:{tone.get(e.get("status","proposed"), "#5A6486")};">'
                f'{e.get("status","proposed")}</span>'
                f'<span style="font-size:10.5px;color:#858CA6;white-space:nowrap;">{"by " + ("you" if e.get("by_partner") else "Yuno")}</span></div>'
                for e in events)
            + '</div>', unsafe_allow_html=True)
    if contrib:
        st.markdown(_section_label("Propose an event", top=18), unsafe_allow_html=True)
        with st.form("gtm_event", clear_on_submit=True, border=False):
            c1, c2 = st.columns([1.6, 1])
            title = c1.text_input("Event", placeholder="e.g. Joint webinar — PIX for cross-border merchants")
            fmt = c2.selectbox("Format", _EVENT_FORMATS)
            c3, c4 = st.columns(2)
            date = c3.date_input("Date").isoformat()
            where = c4.text_input("Where", placeholder="City, venue or online")
            body = st.text_area("What we'd do together", height=90,
                                placeholder="Audience, the story, what each side brings, what a good outcome looks like.")
            go = st.form_submit_button("Propose to Yuno", type="primary")
        if go:
            if not title.strip():
                st.session_state.share_result = (False, "give the event a name")
            else:
                import datetime as _dt
                rec = {"slug": slug, "company": company, "title": title.strip(), "format": fmt, "date": date,
                       "where": where.strip(), "body": body.strip(), "status": "proposed", "by_partner": True,
                       "by": signed_in_email(), "ts": _dt.datetime.utcnow().isoformat() + "Z"}
                _append_jsonl(_GTM_EVENTS, rec)
                acct = res.get("account") or {}
                ok, detail, _ = _slack_send(f":calendar: *{company} proposed a joint event* — *{title.strip()}*\n"
                                            f"{fmt} · {date}" + (f" · {where.strip()}" if where.strip() else "") +
                                            (f"\n> {body.strip()}" if body.strip() else "") +
                                            f"\n_partner manager {_manager_mention(acct.get('manager', ''))}_")
                st.session_state.share_result = (ok, detail)
            st.rerun()


def _gtm_enablement(res, contrib):
    company = res.get("company") or "you"
    slug = _gtm_slug(res)
    reqs = [r for r in _read_jsonl(_GTM_ENABLE) if r.get("slug") == slug]
    by_topic = {}
    for r in reqs:
        by_topic.setdefault(r["topic"], []).append(r)
    st.markdown(_section_label("Sessions Yuno runs with partners", top=16), unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (topic, length, blurb) in enumerate(_ENABLEMENT_CATALOGUE):
        mine = by_topic.get(topic, [])
        latest = mine[-1] if mine else None
        with cols[i % 2]:
            st.markdown(
                f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-top:3px solid #3E4FE0;'
                f'border-radius:14px 14px 0 0;padding:16px 18px 12px;font-family:var(--font);">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                f'<span style="font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#858CA6;">{length}</span>'
                + (f'<span style="margin-left:auto;font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;'
                   f'background:{"#EAF3E3" if latest.get("status") == "scheduled" else "#FDF8E8"};'
                   f'color:{"#37610A" if latest.get("status") == "scheduled" else "#8A4B00"};">'
                   f'{"scheduled " + latest.get("when", "") if latest.get("status") == "scheduled" else "requested " + latest["ts"][:10]}</span>' if latest else "")
                + f'</div><div style="font-size:14px;font-weight:600;color:#10131C;letter-spacing:-.01em;">{topic}</div>'
                f'<div style="font-size:12px;color:#4A5170;line-height:1.55;margin-top:5px;min-height:54px;">{blurb}</div></div>',
                unsafe_allow_html=True)
            if contrib:
                with st.form(f"en_{i}", clear_on_submit=True, border=False):
                    c1, c2 = st.columns([1.4, 1])
                    who = c1.text_input("Who should attend", placeholder="names or team", label_visibility="collapsed")
                    when = c2.text_input("Preferred timing", placeholder="e.g. w/c 6 Oct", label_visibility="collapsed")
                    go = st.form_submit_button("Request this session", use_container_width=True)
                if go:
                    import datetime as _dt
                    rec = {"slug": slug, "company": company, "topic": topic, "attendees": who.strip(), "when": when.strip(),
                           "status": "requested", "by": signed_in_email(), "ts": _dt.datetime.utcnow().isoformat() + "Z"}
                    _append_jsonl(_GTM_ENABLE, rec)
                    acct = res.get("account") or {}
                    ok, detail, _ = _slack_send(f":mortar_board: *{company} requested an enablement session* — *{topic}*\n"
                                                f"Attendees: {who.strip() or '—'} · Timing: {when.strip() or 'flexible'}\n"
                                                f"_partner manager {_manager_mention(acct.get('manager', ''))}_")
                    st.session_state.share_result = (ok, detail)
                    st.rerun()
            else:
                st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    if reqs:
        st.markdown(_section_label(f"Your requests · {len(reqs)}", top=16), unsafe_allow_html=True)
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;padding:4px 18px;font-family:var(--font);">'
            + "".join(f'<div style="display:flex;gap:12px;padding:9px 0;border-bottom:1px solid rgba(35,42,61,.06);font-size:12.5px;">'
                      f'<span style="font-family:var(--mono);font-size:11px;color:#858CA6;min-width:82px;">{r["ts"][:10]}</span>'
                      f'<span style="flex:1;color:#10131C;font-weight:500;">{r["topic"]}</span>'
                      f'<span style="color:#4A5170;">{r.get("attendees") or ""}</span>'
                      f'<span style="color:#858CA6;">{r.get("when") or ""}</span>'
                      f'<span style="font-size:10px;font-weight:600;color:#8A4B00;">{r.get("status")}</span></div>'
                      for r in reversed(reqs))
            + '</div>', unsafe_allow_html=True)


def _gtm_yuno_matrix(res):
    acct = res.get("account") or {}
    rows = yuno_contact_matrix(acct)
    st.markdown(_section_label("Who to call at Yuno", top=16), unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (role, who, when, tone) in enumerate(rows):
        with cols[i % 2]:
            st.markdown(
                f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-left:3px solid {tone};border-radius:12px;'
                f'padding:14px 16px;margin-bottom:10px;font-family:var(--font);">'
                f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:{tone};">{role}</div>'
                f'<div style="font-size:15px;font-weight:600;color:#10131C;margin:4px 0 4px;letter-spacing:-.01em;">{who}</div>'
                f'<div style="font-size:12px;color:#4A5170;line-height:1.5;">{when}</div></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="padding:13px 16px;background:#E9ECFC;border:1px solid rgba(84,104,245,.22);border-radius:var(--r-ctl);'
        'font-size:12.5px;color:#3A4155;line-height:1.6;font-family:var(--font);">Everything sent from this portal — leads, '
        'updates, comments, uploads — reaches your partner manager in Slack the moment you send it. You never have to guess who.</div>',
        unsafe_allow_html=True)


def _gtm_partner_matrix(res, contrib):
    company = res.get("company") or "your company"
    rows, saved, own = load_partner_matrix(res)
    st.markdown(_section_label(f"{company} contacts on file with Yuno", top=16), unsafe_allow_html=True)
    if rows:
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;padding:4px 18px;font-family:var(--font);margin-bottom:10px;">'
            + "".join(f'<div style="display:flex;gap:12px;padding:9px 0;border-bottom:1px solid rgba(35,42,61,.06);font-size:12.5px;flex-wrap:wrap;">'
                      f'<span style="font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#858CA6;min-width:150px;padding-top:2px;">{r.get("Role") or "—"}</span>'
                      f'<span style="color:#10131C;font-weight:500;min-width:160px;">{r.get("Name") or "—"}</span>'
                      f'<span style="color:#4A5170;">{r.get("Email") or ""}</span>'
                      f'<span style="color:#858CA6;">{r.get("Phone") or ""}</span>'
                      f'<span style="color:#858CA6;font-size:11px;margin-left:auto;">{r.get("Notes") or ""}</span></div>'
                      for r in rows)
            + f'<div style="font-size:10.5px;color:#858CA6;padding:8px 0;">{"Saved by you · " + saved[:10] if own else "From Yuno’s partner book — update it below"}</div></div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#fff;border:1px dashed #D5D9E8;border-radius:12px;padding:20px;text-align:center;'
                    'font-size:12.5px;color:#676E8A;font-family:var(--font);">Yuno has no contacts on file for you yet.</div>',
                    unsafe_allow_html=True)
    if not contrib:
        st.markdown('<div style="font-size:12px;color:#676E8A;margin-top:6px;font-family:var(--font);">Switch on Partner contributions to upload or edit your matrix.</div>',
                    unsafe_allow_html=True)
        return

    st.markdown(_section_label("Upload a file", top=18), unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#4A5170;margin:-4px 0 8px;font-family:var(--font);">CSV or Excel with columns for role, name, email, phone — any order, any header wording.</div>',
                unsafe_allow_html=True)
    up = st.file_uploader("Contact matrix", type=["csv", "xlsx", "xls"], key="cm_upload", label_visibility="collapsed")
    if up is not None:
        parsed = _matrix_from_upload(up)
        if not parsed:
            st.markdown('<div style="padding:12px 15px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                        'font-size:12.5px;color:#6E5400;">Could not read contacts from that file. Check it has a name or email column.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:12px;color:#37610A;margin:4px 0 6px;font-family:var(--font);">Read {len(parsed)} contacts — review below, then save.</div>',
                        unsafe_allow_html=True)
            rows = parsed

    st.markdown(_section_label("Or edit in place", top=16), unsafe_allow_html=True)
    base = rows or [{"Role": r, "Name": "", "Email": "", "Phone": "", "Notes": ""} for r in _MATRIX_ROLES]
    edited = st.data_editor(
        pd.DataFrame(base, columns=["Role", "Name", "Email", "Phone", "Notes"]),
        num_rows="dynamic", use_container_width=True, hide_index=True, key="cm_editor",
        column_config={"Role": st.column_config.SelectboxColumn("Role", options=_MATRIX_ROLES + ["Other"], required=False)})
    c1, c2 = st.columns([1, 3])
    if c1.button("Save contact matrix", key="cm_save", type="primary", use_container_width=True):
        clean = [{k: (str(v).strip() if str(v) != "nan" else "") for k, v in r.items()}
                 for r in edited.to_dict("records")]
        clean = [r for r in clean if r.get("Name") or r.get("Email")]
        if not clean:
            st.session_state.share_result = (False, "add at least one contact")
        else:
            ok, detail, _ = save_partner_matrix(res, clean, "file upload" if up is not None else "edited in the portal")
            st.session_state.share_result = (ok, f"{len(clean)} contacts saved · {detail}")
        st.rerun()
    c2.markdown('<div style="font-size:11.5px;color:#858CA6;padding:9px 0;font-family:var(--font);">Saving replaces the matrix on file and tells your partner manager.</div>',
                unsafe_allow_html=True)


def show_joint_gtm():
    res = st.session_state.get("partner_identity") or resolve_partner(st.session_state.get("auth_email_used", ""))
    acct = res.get("account") or {}
    company = res.get("company") or company_from_domain(signed_in_email()) or "your company"
    manager = acct.get("manager") or "your partner manager"

    st.markdown(hero(
        "Joint go-to-market", eyebrow="Partner Alliance",
        subtitle=(f"The collateral Yuno and {company} sell with, in one place. Yuno's pieces are here already; "
                  f"switch on contributions to add your own and leave comments where {manager} will see them."),
        badge="External"), unsafe_allow_html=True)

    _share_result_banner()

    t1, t2 = st.columns([1.6, 3])
    contrib = t1.toggle("Partner contributions — upload & comment", key="gtm_contrib")
    t2.markdown(
        f'<div style="font-size:12px;color:#676E8A;padding:8px 0 0;font-family:var(--font);">'
        + ("Uploads, proposals, requests and your contact matrix go to a space only you and Yuno can see. "
           f"Each one is posted to {manager} in Slack." if contrib else
           "Switch on to add collateral, propose events, request sessions and keep your contact matrix current.")
        + '</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    section = _gtm_toggle()
    if section == "events":
        return _gtm_event_list(res, contrib)
    if section == "enablement":
        return _gtm_enablement(res, contrib)
    if section == "yuno_matrix":
        return _gtm_yuno_matrix(res)
    if section == "partner_matrix":
        return _gtm_partner_matrix(res, contrib)

    # ── Decks · upload ───────────────────────────────────────────────────────
    if contrib:
        st.markdown(_section_label("Add collateral", top=14), unsafe_allow_html=True)
        with st.form("gtm_upload", clear_on_submit=True, border=False):
            up = st.file_uploader("File", type=_GTM_ALLOWED, label_visibility="collapsed")
            c1, c2 = st.columns([1, 2])
            kind = c1.selectbox("Type", _GTM_KINDS)
            title = c2.text_input("Title", placeholder="How it should read on the shelf")
            desc = st.text_input("What it's for", placeholder="One line — who it's aimed at and when to use it")
            go = st.form_submit_button("Add to the shelf", type="primary")
        if go:
            if up is None:
                st.session_state.share_result = (False, "pick a file first")
            else:
                r = gtm_upload(res, up, kind, title.strip(), desc.strip())
                st.session_state.share_result = (True, f"{r['title']} is on the shelf and {manager} has been told")
            st.rerun()

    # ── The shelf ────────────────────────────────────────────────────────────
    assets = gtm_assets(res)
    comments = gtm_comments(res)
    by_asset = {}
    for c in comments:
        by_asset.setdefault(c["asset_id"], []).append(c)

    st.markdown(_section_label(f"On the shelf · {len(assets)}", top=18), unsafe_allow_html=True)
    if not assets:
        st.markdown('<div style="background:#fff;border:1px dashed #D5D9E8;border-radius:12px;padding:20px;'
                    'text-align:center;font-size:12.5px;color:#676E8A;">Nothing here yet.</div>', unsafe_allow_html=True)
        return

    cols = st.columns(2)
    for i, a in enumerate(assets):
        tone = _GTM_TONE.get(a["kind"], "#5A6486")
        mine = a["by"] != "Yuno"
        thread = by_asset.get(a["id"], [])
        with cols[i % 2]:
            st.markdown(
                f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-top:3px solid {tone};'
                f'border-radius:14px 14px 0 0;padding:16px 18px 12px;font-family:var(--font);">'
                f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">'
                f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;background:{tone}14;color:{tone};">{a["kind"]}</span>'
                f'<span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;'
                f'background:{"#E0ED80" if mine else "#10131C"};color:{"#10131C" if mine else "#EEF0FA"};">{"Added by you" if mine else "From Yuno"}</span>'
                + (f'<span style="margin-left:auto;font-size:10.5px;color:#858CA6;font-variant-numeric:tabular-nums;">{a["ts"][:10]}</span>' if a.get("ts") else "")
                + f'</div><div style="font-size:14px;font-weight:600;color:#10131C;letter-spacing:-.01em;">{a["title"]}</div>'
                f'<div style="font-size:12px;color:#4A5170;line-height:1.55;margin-top:5px;min-height:36px;">{a.get("desc") or ""}</div>'
                f'<div style="font-size:10.5px;color:#858CA6;margin-top:8px;">{a["file"]}'
                + (f' · {a["size"]/1024:.0f} KB' if a.get("size") else "")
                + (f' · {len(thread)} comment{"s" if len(thread) != 1 else ""}' if thread else "")
                + '</div></div>', unsafe_allow_html=True)
            data = a.get("data")
            if data is None and a.get("path"):
                try:
                    data = open(a["path"], "rb").read()
                except Exception:
                    data = b""
            st.download_button("Download", data=data or b"", file_name=a["file"], mime=a["mime"],
                               key=f"gtm_dl_{a['id']}", use_container_width=True)
            if contrib or thread:
                with st.expander(f"Comments · {len(thread)}" if thread else "Comment", expanded=bool(thread) and contrib):
                    for c in thread:
                        st.markdown(
                            f'<div style="padding:8px 0;border-bottom:1px solid rgba(35,42,61,.06);font-family:var(--font);">'
                            f'<div style="font-size:12.5px;color:#10131C;line-height:1.5;">{c["text"]}</div>'
                            f'<div style="font-size:10.5px;color:#858CA6;margin-top:3px;">{c["by"]} · {c["ts"][:10]}</div></div>',
                            unsafe_allow_html=True)
                    if contrib:
                        k1, k2 = st.columns([4, 1])
                        txt = k1.text_input("Comment", key=f"gtm_c_{a['id']}", label_visibility="collapsed",
                                            placeholder="What works, what's missing, what you'd change…")
                        if k2.button("Send", key=f"gtm_cs_{a['id']}", type="primary", use_container_width=True,
                                     disabled=not (txt or "").strip()):
                            ok, detail, _ = gtm_comment(res, a, txt.strip())
                            st.session_state.share_result = (ok, detail)
                            st.rerun()
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)


def show_leadgen():
    """Internal lead-generation desk."""
    plays = _LG.PLAYS
    p1 = [p for p in plays if p["p"] == "P1"]

    st.markdown(hero(
        "Lead generation", eyebrow="Demand desk",
        subtitle=("Where the next leads come from, who is working which route this week, "
                  "and the tip that makes each one land."),
        tiles=[(str(len(plays)), "Plays", "#E0ED80"),
               (str(len(p1)), "P1 this week", "#FF6B7D"),
               (str(len([p for p in plays if p["track"] == "Merchants"])), "Merchants", "#B9C2FF"),
               (str(len([p for p in plays if p["track"] == "FinX"])), "FinX", "#5FD4E8")]),
        unsafe_allow_html=True)

    view = nav_radio("Lead gen view",
                     ["Leads", "Alerts", "This week", "Channels", "Sources", "Discipline"],
                     "lg_view")

    if view == "Alerts" and _RT is None:
        st.markdown(
            '<div style="padding:16px 19px;background:#FDF8E8;'
            'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
            'font-size:12.5px;color:#6E5400;">'
            '<b>Routing config missing.</b> Expected <code>data/routing.py</code>.</div>',
            unsafe_allow_html=True)
        return

    {"Leads": _lg_leads, "Alerts": _lg_alerts, "This week": lambda: _lg_week(plays),
     "Channels": _lg_channels, "Sources": _lg_sources,
     "Discipline": _lg_discipline}.get(view, _lg_leads)()


def _lg_alerts():
    """Where a new lead is logged, routed to a BDM and announced to the GMs."""
    channel = leads_channel()
    webhook, token, _ = _slack_config()
    wired = bool(webhook or token)

    st.markdown(
        '<div class="lg-rail">' + "".join(
            f'<div class="lg-stat"><div class="v" style="color:{c};">{v}</div>'
            f'<div class="k">{k}</div></div>'
            for v, k, c in [
                (str(len(_RT.GMS)), "GMs alerted", "#E0ED80"),
                (str(len(_RT.BDMS)), "BDMs in pool", "#8B9BFF"),
                (str(len(_RT.REGION_ROUTING)), "Regions routed", "#5FD4E8"),
                (f"{_RT.SLA_HOURS}h", "First contact", "#FFA53D")])
        + '</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;'
        f'padding:12px 15px;border-radius:11px;font-family:var(--font);margin-bottom:12px;'
        f'background:{"#EAF3E3" if wired else "#FDF8E8"};'
        f'border:1px solid {"rgba(55,97,10,.22)" if wired else "rgba(138,106,0,.28)"};">'
        f'<span style="width:8px;height:8px;border-radius:50%;'
        f'background:{"#37610A" if wired else "#8A4B00"};flex-shrink:0;"></span>'
        f'<span style="font-size:12.5px;color:{"#2E5208" if wired else "#6E5400"};">'
        f'{"Slack is wired — alerts post to" if wired else "Slack not configured — alerts are logged locally only, destined for"}'
        f' <b><code>{channel}</code></b></span></div>', unsafe_allow_html=True)

    result = st.session_state.pop("al_result", None)
    if result:
        (st.success if result[0] else st.warning)(
            f"{'Alerted' if result[0] else 'Logged'} · {result[1]}")

    # ── Log a lead ───────────────────────────────────────────────────────────
    st.markdown(_section_label("Log a lead", top=4), unsafe_allow_html=True)
    regions = sorted(_RT.REGION_ROUTING) + ["Other"]
    c1, c2 = st.columns([1.4, 1])
    name = c1.text_input("Company", placeholder="Company name", key="al_name",
                         label_visibility="collapsed")
    track = c2.radio("Track", _RT.TRACKS, horizontal=True, key="al_track",
                     label_visibility="collapsed")
    c3, c4 = st.columns(2)
    region = c3.selectbox("Region", regions, key="al_region", label_visibility="collapsed")
    source = c4.selectbox("Source", _RT.SOURCES, key="al_source",
                          label_visibility="collapsed")
    note = st.text_input("Context", placeholder="One line of context — why now?",
                         key="al_note", label_visibility="collapsed")

    lead = {"name": (name or "").strip() or "—", "track": track,
            "region": region, "source": source, "note": (note or "").strip()}
    pool = _RT.REGION_ROUTING.get(region, [])
    by_key = {b["key"]: b for b in _RT.BDMS}
    unrouted = not pool
    bdm = by_key[pool[0]] if pool else by_key.get(_RT.FALLBACK_BDM, _RT.BDMS[0])
    gm = gm_for_region(region)

    # ── Who it goes to ───────────────────────────────────────────────────────
    alt = (f' · alternates with {by_key[pool[1]]["name"]}'
           if len(pool) > 1 else "")
    st.markdown(
        f'<div class="lg-route">'
        f'<div class="lg-route-r"><span class="lg-route-k">Assigned BDM</span>'
        f'<span class="lg-route-v" style="color:#E0ED80;">{bdm["name"]}</span>'
        f'<span class="lg-route-n">{("no BDM covers " + region + " — fallback" ) if unrouted else region + alt}</span></div>'
        f'<div class="lg-route-r"><span class="lg-route-k">Regional GM</span>'
        f'<span class="lg-route-v" style="color:#8B9BFF;">{gm["name"]}</span>'
        f'<span class="lg-route-n">named in the post; all {len(_RT.GMS)} GMs see the channel</span></div>'
        f'<div class="lg-route-r"><span class="lg-route-k">Channel</span>'
        f'<span class="lg-route-v" style="color:#5FD4E8;">{channel}</span>'
        f'<span class="lg-route-n">first contact within {_RT.SLA_HOURS}h</span></div>'
        f'</div>', unsafe_allow_html=True)

    # ── The message, exactly as it will arrive ───────────────────────────────
    with st.expander("The message Slack will receive", expanded=True):
        st.code(lead_alert_text(lead, bdm, gm, unrouted), language=None)

    b1, b2, _s = st.columns([1.1, 1, 2])
    ready = lead["name"] != "—"
    if b1.button("Log and alert", key="al_send", type="primary",
                 use_container_width=True, disabled=not ready):
        ok, detail, ch = post_lead_alert(lead, bdm, gm, unrouted, channel)
        # Held in state, not printed here — the rerun below would wipe it.
        st.session_state.al_result = (ok, f"{lead['name']} → {bdm['name']} · {detail}")
        st.rerun()
    if not ready:
        b2.markdown(
            '<div style="font-size:11px;color:#858CA6;padding:9px 2px;'
            'font-family:var(--font);">Add a company name first.</div>',
            unsafe_allow_html=True)

    # ── Rules and recent traffic ─────────────────────────────────────────────
    st.markdown(_section_label("How routing decides"), unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:13px;'
        'padding:15px 18px;margin-bottom:12px;font-family:var(--font);">' + "".join(
            f'<div style="display:flex;gap:15px;padding:8px 0;flex-wrap:wrap;'
            f'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<span style="font-size:12px;font-weight:600;color:#10131C;flex:1;'
            f'min-width:118px;">{k}</span>'
            f'<span style="font-size:11.5px;color:#676E8A;flex:2.4;min-width:250px;'
            f'line-height:1.6;">{_h(v)}</span></div>' for k, v in _RT.ALERT_RULES)
        + '</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    g1.markdown(
        '<div class="lg-roster"><div class="lg-roster-h">GMs · alerted on every lead</div>'
        + "".join(
            f'<div class="lg-roster-r"><span class="lg-roster-n">{g["name"]}</span>'
            f'<span class="lg-roster-m">{", ".join(g["regions"])}</span>'
            f'<span class="lg-roster-h2" style="color:{"#37610A" if g["handle"] else "#B36200"};">'
            f'{g["handle"] or "handle needed"}</span></div>' for g in _RT.GMS)
        + '</div>', unsafe_allow_html=True)
    g2.markdown(
        '<div class="lg-roster"><div class="lg-roster-h">BDMs · assignment pool</div>'
        + "".join(
            f'<div class="lg-roster-r"><span class="lg-roster-n">{b["name"]}</span>'
            f'<span class="lg-roster-m">{", ".join(b["regions"][:3])}</span>'
            f'<span class="lg-roster-h2" style="color:{"#37610A" if b["handle"] else "#B36200"};">'
            f'{b["handle"] or "handle needed"}</span></div>' for b in _RT.BDMS)
        + '</div>', unsafe_allow_html=True)

    recent = recent_lead_alerts()
    st.markdown(_section_label(f"Recent alerts · {len(recent)}"), unsafe_allow_html=True)
    if not recent:
        st.markdown('<div class="lg-empty">No leads logged yet.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="lg-board"><div style="position:relative;z-index:1;">'
                    + "".join(
            f'<div class="lg-feed">'
            f'<span class="lg-feed-t">{r.get("ts","")[:16].replace("T"," ")}</span>'
            f'<span class="lg-feed-n">{r.get("name","—")}</span>'
            f'<span class="lg-tag" style="background:rgba(139,155,255,.14);color:#8B9BFF;">'
            f'{r.get("track","—")}</span>'
            f'<span class="lg-feed-r">{r.get("region","—")}</span>'
            f'<span class="lg-feed-a">{r.get("assigned","—")}</span></div>'
            for r in recent) + '</div></div>', unsafe_allow_html=True)


def _lg_leads():
    """Named leads on both tracks — FinX live from the book, merchants from the base."""
    finx = load_finx_leads()
    base = _LG.MERCHANT_BASE

    neg = [l for l in finx if l["stage"] == "Initial Negotiation"]
    opp = [l for l in finx if l["stage"] != "Initial Negotiation"]
    st.markdown(
        '<div class="lg-rail">' + "".join(
            f'<div class="lg-stat"><div class="v" style="color:{c};">{v}</div>'
            f'<div class="k">{k}</div></div>'
            for v, k, c in [(str(len(finx)), "FinX leads", "#5FD4E8"),
                            (str(len(neg)), "In negotiation", "#E0ED80"),
                            (str(len(opp)), "Identified", "#8B9BFF"),
                            (str(len(base)), "Referral sources", "#B9C2FF")])
        + '</div>', unsafe_allow_html=True)

    track = nav_radio("Lead track", ["FinX", "Merchants"], "lg_leadtrack")

    if track == "FinX":
        if not finx:
            st.markdown(
                '<div style="padding:16px 19px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:12.5px;color:#6E5400;line-height:1.6;">'
                '<b>Account book not found.</b><br>Put <code>partnerships_accounts.xlsx</code> '
                'in <code>data/</code> and the live lead list appears here.</div>',
                unsafe_allow_html=True)
            return
        owners = sorted({l["owner"] for l in finx})
        regions = sorted({l["region"] for l in finx if l["region"] != "—"})
        f1, f2, f3 = st.columns([1.3, 1, 1])
        who = f1.selectbox("Owner", ["All owners"] + owners, key="lg_lead_owner",
                           label_visibility="collapsed")
        reg = f2.selectbox("Region", ["All regions"] + regions, key="lg_lead_region",
                           label_visibility="collapsed")
        stg = f3.selectbox("Stage", ["All stages", "Initial Negotiation",
                                     "Opportunity Identification"],
                           key="lg_lead_stage", label_visibility="collapsed")
        rows = [l for l in finx
                if (who == "All owners" or l["owner"] == who)
                and (reg == "All regions" or l["region"] == reg)
                and (stg == "All stages" or l["stage"] == stg)]

        st.markdown(
            f'<div class="lg-count">{len(rows)} of {len(finx)} shown</div>',
            unsafe_allow_html=True)
        if not rows:
            st.markdown('<div class="lg-empty">Nothing matches that filter.</div>',
                        unsafe_allow_html=True)
            return
        st.markdown('<div class="lg-board"><div class="lg-grid">' + "".join(
            _lg_lead_tile(l) for l in rows[:120]) + '</div></div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="lg-note">{_LG.FINX_SOURCE_NOTE}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="lg-note" style="margin-bottom:11px;">'
            f'{_LG.MERCHANT_SOURCE_NOTE}</div>', unsafe_allow_html=True)
        st.markdown('<div class="lg-board"><div class="lg-grid">' + "".join(
            f'<div class="lg-tile" style="border-left-color:#3E4FE0;">'
            f'<div class="lg-n">{n}</div>'
            f'<div class="lg-m"><span class="lg-tag" '
            f'style="background:rgba(139,155,255,.14);color:#8B9BFF;">{vert}</span>'
            f'<span class="lg-r">{country}</span></div>'
            f'<div class="lg-ask">Ask for one peer in {vert.lower()}</div></div>'
            for n, country, region, vert in _LG.MERCHANT_BASE) + '</div></div>',
            unsafe_allow_html=True)


def _lg_lead_tile(l):
    hot = l["stage"] == "Initial Negotiation"
    tone = "#E0ED80" if hot else "#8B9BFF"
    return (
        f'<div class="lg-tile" style="border-left-color:{tone};">'
        f'<div class="lg-n">{l["name"]}</div>'
        f'<div class="lg-m">'
        f'<span class="lg-tag" style="background:{tone}1F;color:{tone};">'
        f'{"NEGOTIATING" if hot else "IDENTIFIED"}</span>'
        f'<span class="lg-r">{l["region"]}</span></div>'
        f'<div class="lg-ask">{l["owner"]}</div></div>')


def _lg_channels():
    """Events, webinars and the rest — how we go and find them."""
    st.markdown(
        '<div class="lg-rail">' + "".join(
            f'<div class="lg-stat"><div class="v" style="color:{c["accent"]};">'
            f'{c["icon"]}</div><div class="k">{c["name"].split(" ")[0]}</div></div>'
            for c in _LG.CHANNELS) + '</div>', unsafe_allow_html=True)

    for c in _LG.CHANNELS:
        tracks = "".join(
            f'<span class="lg-tag" style="background:{_LG.TRACKS[t]["accent"]}18;'
            f'color:{_LG.TRACKS[t]["accent"]};margin-left:5px;">{t}</span>'
            for t in c["tracks"])
        steps = "".join(
            f'<div style="display:flex;gap:9px;padding:5px 0;">'
            f'<span style="color:{c["accent"]};font-size:10px;flex-shrink:0;">▪</span>'
            f'<span style="font-size:11.5px;color:#8991AC;line-height:1.55;">{x}</span>'
            f'</div>' for x in c["steps"])
        st.markdown(
            f'<div class="lg-ch" style="--a:{c["accent"]};">'
            f'<div style="position:absolute;left:0;right:0;top:0;height:2px;'
            f'background:{c["accent"]};"></div>'
            f'<div class="lg-ch-h">'
            f'<span class="lg-ch-i" style="background:{c["accent"]}1F;color:{c["accent"]};">'
            f'{c["icon"]}</span>'
            f'<span class="lg-ch-n">{c["name"]}</span>{tracks}'
            f'<span class="lg-ch-c">{c["cadence"]}</span></div>'
            f'<div class="lg-ch-tip"><b style="color:{c["accent"]};">Tip</b> · {c["tip"]}</div>'
            f'<div class="lg-ch-body">{steps}</div>'
            f'<div class="lg-ch-f">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{c["accent"]};'
            f'flex-shrink:0;"></span>'
            f'<span style="font-size:11.5px;font-weight:600;color:#EEF0FA;">{c["owner"]}</span>'
            f'<span style="margin-left:auto;font-size:11px;color:#8991AC;'
            f'font-variant-numeric:tabular-nums;">Target '
            f'<b style="color:#EEF0FA;">{c["target"]}</b></span></div></div>',
            unsafe_allow_html=True)


def _lg_week(plays):
    owners = ["Everyone"] + sorted({p["owner"] for p in plays})
    f1, f2 = st.columns([1.5, 1])
    with f1:
        track = nav_radio("Track", ["Both tracks", "Merchants", "FinX"], "lg_track")
    with f2:
        who = st.selectbox("Owner", owners, key="lg_owner", label_visibility="collapsed")

    rows = [p for p in plays
            if (track == "Both tracks" or p["track"] == track)
            and (who == "Everyone" or p["owner"] == who)]

    # Priority legend — what P1/P2/P3 actually commit you to.
    st.markdown(
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:2px 0 12px;">' + "".join(
            f'<div style="flex:1;min-width:172px;background:#fff;'
            f'border:1px solid rgba(35,42,61,.10);border-left:3px solid {c};'
            f'border-radius:10px;padding:9px 12px;font-family:var(--font);">'
            f'<div style="display:flex;align-items:baseline;gap:7px;">'
            f'<span style="font-size:12px;font-weight:700;color:{c};">{k}</span>'
            f'<span style="margin-left:auto;font-size:15px;font-weight:700;color:#10131C;'
            f'font-variant-numeric:tabular-nums;">'
            f'{sum(1 for p in rows if p["p"] == k)}</span></div>'
            f'<div style="font-size:10px;color:#858CA6;margin-top:2px;line-height:1.4;">'
            f'{note}</div></div>'
            for k, (c, note) in _LG.PRIORITIES.items()) + '</div>', unsafe_allow_html=True)

    if not rows:
        st.markdown(
            '<div style="padding:16px 19px;background:#F1F3FB;border:1px solid rgba(35,42,61,.10);'
            'border-radius:var(--r-ctl);font-size:12.5px;color:#4A5170;">'
            'Nothing on the board for that filter.</div>', unsafe_allow_html=True)
        return

    for p in sorted(rows, key=lambda x: (x["p"], x["track"])):
        st.markdown(_lg_play_card(p), unsafe_allow_html=True)

    st.markdown(_section_label("The week's rhythm"), unsafe_allow_html=True)
    st.markdown(
        '<div style="display:flex;gap:9px;flex-wrap:wrap;">' + "".join(
            f'<div style="flex:1;min-width:212px;background:#fff;'
            f'border:1px solid rgba(35,42,61,.10);border-radius:12px;padding:14px 16px;'
            f'font-family:var(--font);">'
            f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.1em;'
            f'text-transform:uppercase;color:#2F3FC4;">{day}</div>'
            f'<div style="font-size:13px;font-weight:600;color:#10131C;margin-top:5px;">'
            f'{what}</div>'
            f'<div style="font-size:11.5px;color:#676E8A;line-height:1.6;margin-top:5px;">'
            f'{how}</div></div>' for day, what, how in _LG.RHYTHM) + '</div>',
        unsafe_allow_html=True)


def _lg_sources():
    for name, tr in _LG.TRACKS.items():
        st.markdown(
            f'<div style="background:linear-gradient(150deg,#0E1119,#141827 60%,#191E2F);'
            f'border:1px solid #232A3D;border-radius:14px;padding:18px 20px;margin-bottom:10px;'
            f'position:relative;overflow:hidden;font-family:var(--font);">'
            f'<div style="position:absolute;top:-70px;right:-50px;width:280px;height:280px;'
            f'border-radius:50%;background:radial-gradient(circle,{tr["accent"]}33,'
            f'transparent 66%);pointer-events:none;"></div>'
            f'<div style="position:relative;z-index:1;">'
            f'<div style="font-size:17px;font-weight:600;color:#EEF0FA;letter-spacing:-.02em;">'
            f'{name}</div>'
            f'<div style="font-size:12px;color:#8991AC;line-height:1.6;margin-top:5px;">'
            f'{tr["blurb"]}</div></div></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            'border-radius:13px;padding:15px 18px;margin-bottom:16px;font-family:var(--font);">'
            + "".join(
                f'<div style="display:flex;gap:14px;padding:9px 0;flex-wrap:wrap;'
                f'border-bottom:1px solid rgba(35,42,61,.055);">'
                f'<span style="font-size:12.5px;font-weight:600;color:#10131C;flex:1;'
                f'min-width:176px;">{src}</span>'
                f'<span style="font-size:11.5px;color:#676E8A;flex:1.7;min-width:250px;'
                f'line-height:1.6;">{why}</span></div>' for src, why in tr["sources"])
            + '</div>', unsafe_allow_html=True)

    st.markdown(_section_label("What to establish on the first call"), unsafe_allow_html=True)
    qc = st.columns(2)
    for col, (name, items) in zip(qc, _LG.QUALIFY):
        tr = _LG.TRACKS[name]
        col.markdown(
            f'<div style="background:#fff;border:1px solid rgba(35,42,61,.10);'
            f'border-top:2px solid {tr["accent"]};border-radius:13px;padding:15px 17px;'
            f'height:100%;font-family:var(--font);">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{tr["accent"]};margin-bottom:9px;">{name}</div>'
            + "".join(
                f'<div style="display:flex;gap:9px;padding:6px 0;'
                f'border-bottom:1px solid rgba(35,42,61,.055);">'
                f'<span style="color:{tr["accent"]};font-size:11px;flex-shrink:0;">▪</span>'
                f'<span style="font-size:12px;color:#4A5170;line-height:1.55;">{q}</span></div>'
                for q in items) + '</div>', unsafe_allow_html=True)


def _lg_discipline():
    st.markdown(
        '<div style="background:#fff;border:1px solid rgba(35,42,61,.10);border-radius:14px;'
        'padding:17px 19px;margin-bottom:12px;font-family:var(--font);">' + "".join(
            f'<div style="display:flex;gap:12px;padding:10px 0;'
            f'border-bottom:1px solid rgba(35,42,61,.055);">'
            f'<span style="width:21px;height:21px;border-radius:6px;background:#E9ECFC;'
            f'color:#2F3FC4;font-size:10.5px;font-weight:700;display:grid;place-items:center;'
            f'flex-shrink:0;">{i+1}</span>'
            f'<span style="font-size:12.5px;color:#10131C;line-height:1.65;">{d}</span></div>'
            for i, d in enumerate(_LG.DISCIPLINE)) + '</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="padding:14px 17px;background:#E9ECFC;border:1px solid rgba(84,104,245,.22);'
        'border-radius:var(--r-ctl);font-size:12.5px;color:#3A4155;line-height:1.7;'
        'font-family:var(--font);">Every lead lands in Salesforce with a source and an owner '
        'before Friday closes. The portal is where the week is planned; Salesforce is where '
        'it is recorded.</div>', unsafe_allow_html=True)


def show_home():
    is_internal = st.session_state.role == "internal"
    # The two doors are different products and must never read as the same one.
    # A Yuno address lands in the internal Partner Portal; anyone else lands in
    # the external Partner Alliance (see show_alliance_welcome). Both open on
    # the same welcome hero — greeting by name, the Alliance sign, the wheel.
    show_welcome_hero()
    st.markdown(_section_label("Where to go", top=8), unsafe_allow_html=True)

    if is_internal:
        # 4 action cards — grouped by purpose
        cards = [
            ("Partners & Connectors", "#3E4FE0", "◈",
             "Yuno Connectors — search, filter and explore 460+ payment partners. Partners In Flight — track every deal from prospect to live.",
             [("Partner Portfolio","Partners"),("Partners In Flight","MissionCtrl")]),
            ("Intelligence", "#0086A8", "✦",
             "Market insights across LATAM, MENAT, APAC and Europe. Coverage analysis and strategic context.",
             [("Market Intel","Insights")]),
            ("Pipeline & Merchants", "#2F8A1F", "⟳",
             "24 active deals in pipeline. Live merchant analytics — TPV, AOV, approval rates across all merchants.",
             [("Partner Leads","Pipeline"),("Merchants","Merchants")]),
            ("Performance & Tools", "#C24E00", "▲",
             "Partner health dashboards, rev share tracking ($123K/mo), and merchant checkout simulator.",
             [("Partner Health","Performance"),("Rev Share","Benchmarks"),("Merchant Sim","MerchSim")]),
        ]
    else:
        cards = [
            ("Partners", "#3E4FE0", "◈",
             "Browse partner details, contacts, contracts, SLAs and integration status.",
             [("Partner Portfolio","Partners")]),
            ("Pipeline & Merchants", "#2F8A1F", "⟳",
             "Shared merchant pipeline and live performance data — TPV, AOV, approval rates.",
             [("Partner Leads","Pipeline"),("Merchants","Merchants")]),
            ("Performance", "#C24E00", "▲",
             "Monitor TPV, auth rates, and transaction volumes for your Yuno integration.",
             [("Partner Health","Performance"),("Benchmarks","Benchmarks")]),
            ("Market Intel", "#0086A8", "◎",
             "Coverage analysis, payment trends, and strategic context for your region.",
             [("Market Intel","Insights")]),
        ]

    cols = st.columns(2)
    for ci, (title, color, icon, desc, links) in enumerate(cards):
        with cols[ci % 2]:
            link_pills = " ".join(f'<span style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:{color}10;color:{color};border:0.5px solid {color}25;cursor:pointer;">{lbl}</span>' for lbl, _ in links)
            st.markdown(f'<div style="background:#fff;border:1px solid #E2E6F4;border-radius:14px;padding:22px;margin-bottom:10px;border-top:3px solid {color};min-height:180px;display:flex;flex-direction:column;">'
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                        f'<span style="font-size:18px;">{icon}</span>'
                        f'<span style="font-size:14px;font-weight:700;color:#10131C;">{title}</span></div>'
                        f'<div style="font-size:12px;color:#676E8A;line-height:1.6;flex:1;">{desc}</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:14px;">{link_pills}</div>'
                        f'</div>', unsafe_allow_html=True)



# ══ Gisele · the Alliance guide ════════════════════════════════════════════════
# An animated concierge pinned to the bottom-right of every external page. She
# knows which page you are on, says the one useful thing about it, and never
# lets a partner forget that referring a merchant is the fastest way to grow
# together. Rendered into the parent document from a zero-height component so
# she floats over Streamlit's own layout; her nav buttons press the sidebar.

def _gisele_tips(page, name, res):
    acct = res.get("account") or {}
    manager = acct.get("manager") or "your partner manager"
    at, _ = e2e_position(acct) if acct else (0, False)
    stage = _E2E_STAGES[at][0]
    first = (name or "there").split(" ")[0]
    cosell = {"t": "Co-sell reminder: every merchant you refer is routed to a named Yuno BDM within 48 hours. "
                   "Got one in mind?", "cta": "Send a lead", "nav": "Send to Yuno", "tag": "co-sell"}
    by_page = {
        "Home": [
            {"t": f"Hi {first}, I'm Gisele — your guide on the Alliance. Tap a theme on the wheel to see who's in the ecosystem with you.", "tag": "hello"},
            {"t": f"You're at stage {at + 1} · {stage}. Leave a comment under your journey and {manager} sees it in Slack.", "cta": "Comment", "nav": None, "tag": "pipeline"},
            cosell],
        "Partners": [
            {"t": "This is your record — contacts, contracts, integration status. Spot something off? Tell Yuno and it gets fixed.", "cta": "Send to Yuno", "nav": "Send to Yuno", "tag": "record"},
            cosell],
        "Performance": [
            {"t": "An auth rate under 90% in a market is a co-sell conversation, not a support ticket. Let's fix it together.", "cta": "Joint GTM", "nav": "Joint GTM", "tag": "health"},
            cosell],
        "Benchmarks": [
            {"t": "Rev share grows with volume. The quickest volume is a merchant you already know — refer them.", "cta": "Send a lead", "nav": "Send to Yuno", "tag": "co-sell"}],
        "Insights": [
            {"t": "Pick a market where you're strong and Yuno isn't live yet — that gap is a lead waiting to happen.", "cta": "Send a lead", "nav": "Send to Yuno", "tag": "co-sell"}],
        "GTM": [
            {"t": f"Add your one-pager or deck here and I'll make sure {manager} sees it. Comment on the story deck — it's yours too.", "tag": "gtm"},
            {"t": "Switch on Partner contributions to upload and comment.", "tag": "gtm"},
            cosell],
        "Share": [
            {"t": "A merchant you'd introduce to Yuno? That's co-selling. Send the lead — a BDM picks it up within 48h.", "tag": "co-sell"},
            {"t": "Mandates and API changes sent here reach Yuno before they reach your inbox. Keep them coming.", "tag": "updates"}],
    }
    tips = by_page.get(page, [{"t": f"Need a hand, {first}? I know every corner of this portal.", "tag": "hello"}, cosell])
    if cosell not in tips:
        tips.append(cosell)
    return tips


def show_gisele(page):
    import json as _json
    res = st.session_state.get("partner_identity") or {}
    tips = _gisele_tips(page, signed_in_name(), res)
    payload = _json.dumps({"tips": tips, "page": page})
    components.html(f"""<script>
(function(){{
  var D = window.parent.document;
  var cfg = {payload};
  var old = D.getElementById('gisele'); if (old) old.remove();
  if (!D.getElementById('gisele-css')) {{
    var css = D.createElement('style'); css.id = 'gisele-css';
    css.textContent = `
#gisele{{position:fixed;right:22px;bottom:22px;z-index:99999;display:flex;align-items:flex-end;gap:12px;
  font-family:'Geist','GeistSans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
#gisele.min .gs-bubble{{display:none}}
.gs-bubble{{max-width:300px;background:#10131C;color:#EEF0FA;border:1px solid #232A3D;border-radius:16px 16px 4px 16px;
  padding:13px 15px 12px;box-shadow:0 14px 40px rgba(0,0,0,.35);animation:gsPop .45s cubic-bezier(.2,.8,.2,1) both;position:relative;}}
.gs-name{{display:flex;align-items:center;gap:7px;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#E0ED80;margin-bottom:6px;}}
.gs-name .gs-tag{{margin-left:auto;font-size:9px;letter-spacing:.08em;padding:1px 7px;border-radius:999px;background:rgba(255,255,255,.08);color:#8991AC;}}
.gs-name .gs-tag.co-sell{{background:rgba(224,237,128,.18);color:#E0ED80;animation:gsPulse 2.4s ease-in-out infinite;}}
.gs-text{{font-size:12.5px;line-height:1.55;color:#EEF0FA;min-height:38px;}}
.gs-text .gs-cur{{display:inline-block;width:1px;height:12px;background:#E0ED80;margin-left:2px;vertical-align:-2px;animation:gsBlinkCur 1s steps(2) infinite;}}
.gs-row{{display:flex;align-items:center;gap:6px;margin-top:10px;}}
.gs-btn{{font:inherit;font-size:11px;font-weight:600;padding:6px 11px;border-radius:999px;border:1px solid transparent;cursor:pointer;
  background:#E0ED80;color:#10131C;transition:transform .15s,filter .15s;}}
.gs-btn:hover{{transform:translateY(-1px);filter:brightness(1.05);}}
.gs-btn.ghost{{background:transparent;color:#8991AC;border-color:rgba(255,255,255,.14);}}
.gs-btn.ghost:hover{{color:#EEF0FA;border-color:rgba(255,255,255,.3);}}
.gs-dots{{margin-left:auto;display:flex;gap:4px;}}
.gs-dots span{{width:5px;height:5px;border-radius:50%;background:rgba(255,255,255,.18);}}
.gs-dots span.on{{background:#E0ED80;}}
.gs-x{{position:absolute;top:8px;right:10px;width:18px;height:18px;border-radius:50%;border:none;background:transparent;color:#565D78;cursor:pointer;font-size:14px;line-height:1;}}
.gs-x:hover{{color:#EEF0FA;}}
.gs-av{{width:84px;height:84px;border-radius:50%;cursor:pointer;position:relative;flex:0 0 84px;
  background:radial-gradient(circle at 35% 30%,#1B2140,#0C0F1A 72%);border:2px solid #E0ED80;
  box-shadow:0 10px 30px rgba(0,0,0,.35),0 0 0 6px rgba(224,237,128,.10);animation:gsFloat 4s ease-in-out infinite;overflow:hidden;}}
.gs-av:hover{{box-shadow:0 10px 30px rgba(0,0,0,.35),0 0 0 8px rgba(224,237,128,.18);}}
.gs-av svg{{width:100%;height:100%;display:block;}}
.gs-hair{{transform-origin:50% 20%;animation:gsSway 5s ease-in-out infinite;}}
.gs-lid{{transform-origin:center;animation:gsBlink 4.6s infinite;}}
.gs-lid.r{{animation-delay:.08s}}
.gs-hand{{transform-origin:78% 92%;animation:gsWave 6s ease-in-out infinite;}}
.gs-spark{{animation:gsSpark 3s ease-in-out infinite;transform-origin:center;}}
.gs-spark.b{{animation-delay:1.3s}}
.gs-badge{{position:absolute;right:-2px;bottom:-2px;width:22px;height:22px;border-radius:50%;background:#E0ED80;color:#10131C;
  font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;border:2px solid #10131C;animation:gsPulse 2.4s ease-in-out infinite;}}
#gisele.min .gs-badge{{display:flex}}
@keyframes gsFloat{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
@keyframes gsSway{{0%,100%{{transform:rotate(-1.5deg)}}50%{{transform:rotate(1.5deg)}}}}
@keyframes gsBlink{{0%,92%,100%{{transform:scaleY(1)}}95%{{transform:scaleY(.08)}}}}
@keyframes gsWave{{0%,70%,100%{{transform:rotate(0)}}76%{{transform:rotate(-18deg)}}82%{{transform:rotate(12deg)}}88%{{transform:rotate(-14deg)}}94%{{transform:rotate(6deg)}}}}
@keyframes gsSpark{{0%,100%{{opacity:0;transform:scale(.4) rotate(0)}}50%{{opacity:1;transform:scale(1) rotate(45deg)}}}}
@keyframes gsPop{{from{{opacity:0;transform:translateY(10px) scale(.96)}}to{{opacity:1;transform:none}}}}
@keyframes gsPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(224,237,128,.5)}}60%{{box-shadow:0 0 0 8px rgba(224,237,128,0)}}}}
@keyframes gsBlinkCur{{to{{opacity:0}}}}
@media (max-width:640px){{#gisele{{right:12px;bottom:12px}}.gs-bubble{{max-width:min(78vw,300px)}}.gs-av{{width:64px;height:64px;flex-basis:64px}}}}
@media (prefers-reduced-motion:reduce){{#gisele *{{animation:none !important}}}}`;
    D.head.appendChild(css);
  }}
  var root = D.createElement('div'); root.id = 'gisele';
  try {{ if (localStorage.getItem('gisele-min') === '1') root.classList.add('min'); }} catch(e) {{}}
  root.innerHTML = `
  <div class="gs-bubble" role="status" aria-live="polite">
    <button class="gs-x" title="Minimise Gisele">×</button>
    <div class="gs-name"><span>✦ Gisele</span><span class="gs-tag"></span></div>
    <div class="gs-text"></div>
    <div class="gs-row"><button class="gs-btn gs-cta"></button><button class="gs-btn ghost gs-next">Next tip</button><div class="gs-dots"></div></div>
  </div>
  <div class="gs-av" title="Gisele — click for a tip">
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <g class="gs-spark"><path d="M14 22l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#E0ED80"/></g>
      <g class="gs-spark b"><path d="M86 18l1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5z" fill="#8B9BFF"/></g>
      <path d="M22 100 C22 78 32 70 50 70 C68 70 78 78 78 100Z" fill="#C7E956"/>
      <path d="M44 72 L50 84 L56 72 L50 78Z" fill="#10131C"/>
      <path d="M50 70 L46 100 L54 100Z" fill="#EEF0FA"/>
      <g class="gs-hair"><path d="M27 54 C22 30 34 16 50 16 C66 16 78 30 73 54 L70 62 L64 34 C58 40 42 40 36 34 L30 62Z" fill="#1A1424"/></g>
      <rect x="44" y="58" width="12" height="12" rx="5" fill="#C98A64"/>
      <ellipse cx="50" cy="46" rx="16.5" ry="19" fill="#E0A883"/>
      <path d="M33.5 44 C34 30 42 26 50 26 C58 26 66 30 66.5 44 C62 38 56 36 50 36 C44 36 38 38 33.5 44Z" fill="#1A1424"/>
      <circle cx="34" cy="49" r="2.4" fill="#3E4FE0"/><circle cx="66" cy="49" r="2.4" fill="#3E4FE0"/>
      <path d="M40.5 44.5 Q44 42.5 47.5 44.5" stroke="#1A1424" stroke-width="1.6" fill="none" stroke-linecap="round"/>
      <path d="M52.5 44.5 Q56 42.5 59.5 44.5" stroke="#1A1424" stroke-width="1.6" fill="none" stroke-linecap="round"/>
      <g><ellipse cx="44" cy="49" rx="3" ry="2.6" fill="#fff"/><circle cx="44.4" cy="49.2" r="1.7" fill="#2A1F1A"/><circle cx="45" cy="48.5" r=".6" fill="#fff"/>
         <rect class="gs-lid" x="40.5" y="46" width="7" height="6" fill="#E0A883" style="transform-box:fill-box"/></g>
      <g><ellipse cx="56" cy="49" rx="3" ry="2.6" fill="#fff"/><circle cx="56.4" cy="49.2" r="1.7" fill="#2A1F1A"/><circle cx="57" cy="48.5" r=".6" fill="#fff"/>
         <rect class="gs-lid r" x="52.5" y="46" width="7" height="6" fill="#E0A883" style="transform-box:fill-box"/></g>
      <path d="M49 52 L50 55.5 L51.5 55" stroke="#C98A64" stroke-width="1.2" fill="none" stroke-linecap="round"/>
      <path d="M44.5 59.5 Q50 63.5 55.5 59.5" stroke="#B5443F" stroke-width="2" fill="none" stroke-linecap="round"/>
      <circle cx="40" cy="55" r="2.6" fill="#F2B7A6" opacity=".7"/><circle cx="60" cy="55" r="2.6" fill="#F2B7A6" opacity=".7"/>
      <g class="gs-hand"><rect x="74" y="60" width="9" height="20" rx="4.5" fill="#E0A883"/>
        <path d="M74 60 l0 -6 M77 59 l0 -8 M80 59 l0 -7 M83 61 l0 -5" stroke="#E0A883" stroke-width="3" stroke-linecap="round"/></g>
    </svg>
    <span class="gs-badge">✦</span>
  </div>`;
  D.body.appendChild(root);
  var tips = cfg.tips, i = 0, timer = null, typing = null;
  var txt = root.querySelector('.gs-text'), cta = root.querySelector('.gs-cta'), tag = root.querySelector('.gs-name .gs-tag'),
      dots = root.querySelector('.gs-dots'), av = root.querySelector('.gs-av');
  tips.forEach(function(){{ var s = D.createElement('span'); dots.appendChild(s); }});
  function nav(label){{
    var btns = D.querySelectorAll('[data-testid="stSidebar"] button');
    for (var b of btns) if (b.textContent.trim() === label) {{ b.click(); return; }}
  }}
  function show(n){{
    i = (n + tips.length) % tips.length; var t = tips[i];
    dots.querySelectorAll('span').forEach(function(s, k){{ s.classList.toggle('on', k === i); }});
    tag.textContent = t.tag || ''; tag.className = 'gs-tag ' + (t.tag === 'co-sell' ? 'co-sell' : '');
    if (t.cta && t.nav) {{ cta.style.display = ''; cta.textContent = t.cta; cta.onclick = function(){{ nav(t.nav); }}; }}
    else if (t.cta) {{ cta.style.display = ''; cta.textContent = t.cta; cta.onclick = function(){{
      var el = D.querySelector('input[aria-label="Comment"]'); if (el) {{ el.scrollIntoView({{behavior:'smooth', block:'center'}}); el.focus(); }} }}; }}
    else cta.style.display = 'none';
    clearInterval(typing); txt.innerHTML = '<span class="gs-cur"></span>'; var k = 0;
    typing = setInterval(function(){{ k++; txt.innerHTML = t.t.slice(0, k) + (k < t.t.length ? '<span class="gs-cur"></span>' : '');
      if (k >= t.t.length) clearInterval(typing); }}, 16);
    clearInterval(timer); timer = setInterval(function(){{ show(i + 1); }}, 11000);
  }}
  root.querySelector('.gs-next').onclick = function(){{ show(i + 1); }};
  av.onclick = function(){{
    if (root.classList.contains('min')) {{ root.classList.remove('min'); try {{ localStorage.setItem('gisele-min','0'); }} catch(e) {{}} show(i); }}
    else show(i + 1);
  }};
  root.querySelector('.gs-x').onclick = function(){{ root.classList.add('min'); clearInterval(timer); try {{ localStorage.setItem('gisele-min','1'); }} catch(e) {{}} }};
  if (!root.classList.contains('min')) show(0);
}})();
</script>""", height=0)


# ── Main App ───────────────────────────────────────────────────────────────────
inject_css(st.session_state.role)

if st.session_state.role is None:
    show_landing()
else:
    show_sidebar()
    # Top-right sign out button
    _top_left, _top_right = st.columns([9, 1])
    with _top_right:
        if st.button("Sign out", key="goto_landing", use_container_width=True):
            st.session_state.role = None
            st.session_state.sso_method = None
            st.session_state.page = "Home"
            st.query_params.clear()
            # End the identity-provider session too when one was actually used,
            # otherwise "sign out" silently signs you straight back in.
            try:
                if st.user.is_logged_in:
                    st.logout()
                    st.stop()
            except Exception:
                pass
            st.rerun()
    # Style the sign-out button
    st.markdown("""<style>
    button[data-testid="baseButton-secondary"][kind="secondary"]:has(~ div) {},
    [data-testid="stMain"] [data-testid="stColumns"]:first-of-type [data-testid="stColumn"]:last-child button {
        background: transparent !important;
        border: 1px solid rgba(16,19,28,.10) !important;
        border-radius: var(--r-ctl) !important;
        color: var(--text3) !important;
        font-family: var(--font) !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        min-height: 32px !important;
        padding: 5px 13px !important;
        transition: all .16s var(--ease) !important;
        letter-spacing: -0.005em !important;
        box-shadow: none !important;
    }
    [data-testid="stMain"] [data-testid="stColumns"]:first-of-type [data-testid="stColumn"]:last-child button:hover {
        background: var(--sunk) !important;
        border-color: rgba(16,19,28,.16) !important;
        color: var(--text) !important;
    }
    </style>""", unsafe_allow_html=True)
    page = st.session_state.page
    if st.session_state.role == "partner":
        show_gisele(page)
    if page == "Home":
        if st.session_state.role == "partner" and st.session_state.get("partner_identity"):
            show_alliance_welcome()
        else:
            show_home()
    elif page == "LeadGen":
        if st.session_state.role != "internal":
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Not available on external access.</b><br>Lead generation is Yuno\'s own '
                'demand desk.</div>', unsafe_allow_html=True)
        elif _LG is None:
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:13px;color:#6E5400;">'
                '<b>Lead-gen data missing.</b> Expected <code>data/leadgen.py</code>.</div>',
                unsafe_allow_html=True)
        else:
            show_leadgen()
    elif page == "Cosell":
        if st.session_state.role != "internal":
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Not available on external access.</b><br>Co-sell is Yuno\'s own sprint '
                'plan, pricing authority and partner pipeline.</div>', unsafe_allow_html=True)
        elif _CS is None:
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Sprint data missing.</b><br>Expected <code>data/cosell.py</code>.'
                '</div>', unsafe_allow_html=True)
        else:
            show_cosell()
    elif page == "GTM":
        if st.session_state.role == "internal":
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
                'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Partner-facing page.</b><br>Joint GTM is each partner\'s own shelf. Uploads land in '
                '<code>data/gtm_uploads/</code>, comments in <code>data/gtm_comments.jsonl</code>.</div>',
                unsafe_allow_html=True)
        else:
            show_joint_gtm()
    elif page == "Share":
        if st.session_state.role == "internal":
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
                'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Partner-facing page.</b><br>Send to Yuno is the external door\'s inbox. '
                'Submissions land in Slack and in <code>data/partner_submissions.jsonl</code>.</div>',
                unsafe_allow_html=True)
        else:
            show_partner_share()
    elif page == "Pipeline" and st.session_state.role == "partner":
        st.markdown(
            '<div style="padding:18px 20px;background:#FDF8E8;border:1px solid rgba(138,106,0,.28);'
            'border-radius:var(--r-ctl);font-size:13px;color:#6E5400;line-height:1.6;">'
            '<b>Not available on external access.</b><br>Partner Leads is Yuno\'s own pipeline across '
            'the whole programme. Your own progress is on your record and on Partner Health.</div>',
            unsafe_allow_html=True)
    elif page == "Pipeline":
        show_pipeline()
    elif page == "Partners":
        show_partners()
    elif page == "Merchants":
        if st.session_state.role != "internal":
            _ext_locked("Yuno's merchant book stays with Yuno",
                        "The merchants live on your rails through Yuno are listed on Partner Health. "
                        "The full merchant portfolio is Yuno's own view.")
        else:
            show_merchants()
    elif page == "Contacts":
        st.session_state.page = "Partners"
        st.rerun()
    elif page == "Performance":
        show_performance()
    elif page == "Benchmarks":
        show_benchmarks()
    elif page == "Insights":
        show_insights()
    elif page == "PayRec":
        if st.session_state.role != "internal":
            _ext_locked("The Payment Intelligence Engine is Yuno's sales desk",
                        "It matches merchants to providers across the whole programme. Your own coverage "
                        "is on your record; market context is on Market Intel.")
        else:
            show_payment_recs()
    elif page == "Expansion":
        if st.session_state.role != "internal":
            st.markdown(
                '<div style="padding:18px 20px;background:#FDF8E8;'
                'border:1px solid rgba(138,106,0,.28);border-radius:var(--r-ctl);'
                'font-size:13px;color:#6E5400;line-height:1.6;">'
                '<b>Not available on external access.</b><br>The market expansion simulator is '
                'an internal Yuno tool.</div>', unsafe_allow_html=True)
        else:
            show_expansion()
    elif page == "MerchSim":
        if st.session_state.role != "internal":
            _ext_locked("Merchant Sim is Yuno's modelling tool",
                        "It models a merchant's stack across every provider. If there is a merchant you want "
                        "to model together, send the lead and we will run it with you.")
        else:
            show_merchant_sim()
    elif page == "MissionCtrl":
        show_mission_control()
