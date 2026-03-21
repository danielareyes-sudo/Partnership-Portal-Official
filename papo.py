import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import base64 as _b64

try:
    _LOGO_B64 = _b64.b64encode(open("/Users/danielareyes/Desktop/Assignment-claude/Yuno logo.png","rb").read()).decode()
except:
    _LOGO_B64 = ""

try:
    _DANIELA_B64 = _b64.b64encode(open("/Users/danielareyes/Desktop/Assignment-claude/daniela.png","rb").read()).decode()
except:
    _DANIELA_B64 = ""

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PAPO · Yuno Partner Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ──────────────────────────────────────────────────────────────
for k, v in [("role", None), ("pending_role", None), ("pw_error", False), ("page", "Home"), ("cat_filter", "all"), ("insight_tab", "market")]:
    if k not in st.session_state:
        st.session_state[k] = v

# Sync page from URL query params on first load
_qp = st.query_params
if "role" in _qp and st.session_state.role is None:
    if _qp["role"] in ("internal", "partner"):
        st.session_state.role = _qp["role"]
if "page" in _qp:
    valid_pages = {"Home","Pipeline","Partners","Merchants","Contacts","Performance","Benchmarks","Insights"}
    if _qp["page"] in valid_pages:
        st.session_state.page = _qp["page"]

# ── Data ───────────────────────────────────────────────────────────────────────
PARTNERS_DATA = [
    {"name":"Adyen",            "type":"PSP",        "region":"Global · LATAM",      "status":"Live",        "tpv":"$890M", "auth":"92.4%","logo":"AD","color":"#3b82f6","cat":"PSP"},
    {"name":"Nuvei",            "type":"PSP",        "region":"BR · MX · COL",        "status":"Live",        "tpv":"$310M", "auth":"87.1%","logo":"NV","color":"#a855f7","cat":"PSP"},
    {"name":"Stripe",           "type":"PSP",        "region":"MX · CO",              "status":"Live",        "tpv":"$120M", "auth":"91.8%","logo":"ST","color":"#a855f7","cat":"PSP"},
    {"name":"Getnet (Santander)","type":"Acquirer",  "region":"Brazil",               "status":"Live",        "tpv":"$440M", "auth":"89.6%","logo":"GN","color":"#3b82f6","cat":"Acquirer"},
    {"name":"Kushki",           "type":"Acquirer",   "region":"COL · MX · EC · PE",   "status":"Live",        "tpv":"$280M", "auth":"88.2%","logo":"KU","color":"#3b82f6","cat":"Acquirer"},
    {"name":"Cielo",            "type":"Acquirer",   "region":"Brazil",               "status":"Live",        "tpv":"$520M", "auth":"86.9%","logo":"CI","color":"#3b82f6","cat":"Acquirer"},
    {"name":"Conekta",          "type":"Acquirer",   "region":"Mexico",               "status":"Integration", "tpv":"—",     "auth":"—",    "logo":"CN","color":"#3b82f6","cat":"Acquirer"},
    {"name":"Prosa",            "type":"Acquirer",   "region":"Mexico",               "status":"Live",        "tpv":"$190M", "auth":"90.1%","logo":"PR","color":"#3b82f6","cat":"Acquirer"},
    {"name":"OpenPix",          "type":"APM",        "region":"Brazil (PIX)",         "status":"Live",        "tpv":"$210M", "auth":"99.1%","logo":"OP","color":"#14b8a6","cat":"APM"},
    {"name":"MercadoPago",      "type":"APM",        "region":"MX · AR · BR · COL",   "status":"Live",        "tpv":"$380M", "auth":"97.4%","logo":"MP","color":"#14b8a6","cat":"APM"},
    {"name":"Rappi Pay",        "type":"APM",        "region":"COL · MX · BR",        "status":"Integration", "tpv":"—",     "auth":"—",    "logo":"RP","color":"#14b8a6","cat":"APM"},
    {"name":"Khipu",            "type":"APM",        "region":"Chile",                "status":"Live",        "tpv":"$45M",  "auth":"98.2%","logo":"KH","color":"#14b8a6","cat":"APM"},
    {"name":"Yape",             "type":"APM",        "region":"Peru",                 "status":"Live",        "tpv":"$38M",  "auth":"97.8%","logo":"YP","color":"#14b8a6","cat":"APM"},
    {"name":"OXXO Pay",         "type":"APM",        "region":"Mexico (Cash)",        "status":"Live",        "tpv":"$72M",  "auth":"99.5%","logo":"OX","color":"#14b8a6","cat":"APM"},
    {"name":"SEON",             "type":"Fraud",      "region":"Global",               "status":"Live",        "tpv":"N/A",   "auth":"N/A",  "logo":"SN","color":"#ef4444","cat":"Fraud"},
    {"name":"Truora",           "type":"Fraud / KYC","region":"COL · MX · BR",        "status":"Integration", "tpv":"N/A",   "auth":"N/A",  "logo":"TR","color":"#ef4444","cat":"Fraud"},
    {"name":"Kount (Equifax)",  "type":"Fraud",      "region":"Global",               "status":"Prospect",    "tpv":"N/A",   "auth":"N/A",  "logo":"KT","color":"#ef4444","cat":"Fraud"},
    {"name":"Pomelo",           "type":"BaaS",       "region":"AR · MX · COL",        "status":"Prospect",    "tpv":"—",     "auth":"—",    "logo":"PM","color":"#f59e0b","cat":"BaaS"},
    {"name":"Stori",            "type":"BaaS",       "region":"Mexico",               "status":"Prospect",    "tpv":"—",     "auth":"—",    "logo":"SO","color":"#f59e0b","cat":"BaaS"},
    {"name":"Bnext",            "type":"BaaS",       "region":"MX · COL",             "status":"Prospect",    "tpv":"—",     "auth":"—",    "logo":"BN","color":"#f59e0b","cat":"BaaS"},
    {"name":"Minka",            "type":"BaaS",       "region":"Colombia",             "status":"Integration", "tpv":"—",     "auth":"—",    "logo":"MK","color":"#f59e0b","cat":"BaaS"},
]

CAT_CLASS   = {"PSP":"cat-psp","Acquirer":"cat-acquirer","APM":"cat-apm","Fraud":"cat-fraud","Fraud / KYC":"cat-fraud","BaaS":"cat-baas"}
STATUS_CLASS = {"Live":"p-green","Integration":"p-blue","Prospect":"p-amber","In Dev":"p-purple"}

PIPELINE_STAGES = {
    "Prospect":    {"color":"#86868b","count":3},
    "Qualified":   {"color":"#60a5fa","count":3},
    "Evaluation":  {"color":"#c084fc","count":4},
    "Negotiation": {"color":"#fbbf24","count":2},
    "Won":         {"color":"#4ade80","count":2},
}

CONTACTS = [
    {"init":"TK","bg":"rgba(59,130,246,.2)","color":"#60a5fa","name":"Tom Kuehn","role":"Head of LATAM Partnerships","company":"Adyen · PSP","badge":"Champion","badge_class":"p-green","last":"2d ago","rel":"★★★★★","deals":"3 active"},
    {"init":"RV","bg":"rgba(168,85,247,.2)","color":"#c084fc","name":"Ricardo Vega","role":"VP Business Development","company":"Nuvei · PSP","badge":"Warm","badge_class":"p-amber","last":"5h ago","rel":"★★★★☆","deals":"1 active"},
    {"init":"AP","bg":"rgba(20,184,166,.2)","color":"#2dd4bf","name":"Ana Pacheco","role":"Strategic Partnerships Director","company":"Kushki · Acquirer","badge":"Active","badge_class":"p-blue","last":"1w ago","rel":"★★★★☆","deals":"2 active"},
    {"init":"FM","bg":"rgba(245,158,11,.2)","color":"#fbbf24","name":"Felipe Morales","role":"Head of Digital Products","company":"Getnet · Acquirer (Santander)","badge":"Executive Sponsor","badge_class":"p-green","last":"Today","rel":"★★★★★","deals":"1 at Negotiation"},
    {"init":"DH","bg":"rgba(239,68,68,.2)","color":"#fca5a5","name":"Diana Herrera","role":"Fraud Partnerships Lead","company":"SEON · Fraud & Risk","badge":"Live Partner","badge_class":"p-green","last":"3d ago","rel":"★★★★☆","deals":"Integration live"},
    {"init":"MC","bg":"rgba(245,158,11,.2)","color":"#fde68a","name":"Martín Castillo","role":"CEO & Co-Founder","company":"Pomelo · BaaS","badge":"New Vertical","badge_class":"p-amber","last":"Yesterday","rel":"★★★☆☆","deals":"1 at Evaluation"},
]

# ── CSS ─────────────────────────────────────────────────────────────────────────
_STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700&display=swap');
:root {
  --bg:#f5f5f7; --bg2:#ffffff; --bg3:#f0f0f5; --bg4:#e8e8ed; --bg5:#d1d1d6;
  --border:rgba(0,0,0,0.07); --border2:rgba(0,0,0,0.13);
  --text:#1d1d1f; --text2:#6e6e73; --text3:#86868b;
  --indigo:#4F46E5; --indigo-light:rgba(79,70,229,0.08); --indigo-mid:rgba(79,70,229,0.15);
  --blue:#2563eb; --green:#16a34a; --red:#dc2626; --amber:#d97706;
  --purple:#7c3aed; --teal:#0d9488;
  --shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);
  --shadow-md:0 4px 16px rgba(0,0,0,0.08),0 0 0 1px rgba(0,0,0,0.04);
  --font:'Titillium Web',sans-serif; --mono:Menlo,'Courier New',monospace;
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
[data-testid="stSidebar"] { background:var(--bg2) !important; border-right:1px solid rgba(0,0,0,0.07) !important; }
[data-testid="stSidebar"] > div:first-child { padding:0 !important; }
/* Role toggle buttons (inside columns in sidebar) */
[data-testid="stSidebar"] [data-testid="column"] [data-testid="stButton"] > button {
  border-radius:20px !important; border:none !important; font-size:11.5px !important; font-weight:600 !important; padding:7px 12px !important;
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
  content:attr(data-badge); margin-left:auto; font-size:10px; font-family:var(--mono);
  background:var(--bg3); color:var(--text3); padding:2px 7px; border-radius:10px; flex-shrink:0;
}
[data-testid="stSidebar"] button[data-nav-active="true"][data-badge]::after {
  background:var(--indigo-mid); color:var(--indigo);
}
[data-testid="stTextInput"] input { background:#fff !important; border:1px solid var(--border2) !important; color:var(--text) !important; border-radius:8px !important; font-family:var(--font) !important; font-size:15px !important; }
[data-testid="stTextInput"] input[type="password"] { background:#fff !important; color:var(--text) !important; -webkit-text-fill-color:var(--text) !important; caret-color:var(--text) !important; }
[data-testid="stTextInput"] input::placeholder { color:var(--text3) !important; }
[data-testid="stTextInput"] input:focus { border-color:var(--indigo) !important; box-shadow:0 0 0 3px rgba(79,70,229,0.12) !important; }
.stButton > button { background:#fff !important; color:var(--text2) !important; border:1px solid var(--border2) !important; border-radius:8px !important; font-family:var(--font) !important; font-weight:600 !important; font-size:14px !important; }
.stButton > button:hover { border-color:var(--indigo) !important; color:var(--indigo) !important; }
.stButton > button[data-testid="baseButton-primary"] { background:var(--indigo) !important; color:#fff !important; border:none !important; }
.stButton > button[data-testid="baseButton-primary"]:hover { background:#4338ca !important; }
.pill{display:inline-flex;align-items:center;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:var(--mono);letter-spacing:.2px;white-space:nowrap;}
.p-green{background:rgba(22,163,74,.1);color:#15803d;}
.p-blue{background:rgba(37,99,235,.1);color:#1d4ed8;}
.p-amber{background:rgba(217,119,6,.1);color:#b45309;}
.p-red{background:rgba(220,38,38,.1);color:#b91c1c;}
.p-purple{background:rgba(124,58,237,.1);color:#6d28d9;}
.p-teal{background:rgba(13,148,136,.1);color:#0f766e;}
.p-grey{background:rgba(107,114,128,.1);color:#4b5563;}
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
.stage-head{padding:10px 14px;background:#fafafa;border-bottom:1px solid rgba(0,0,0,0.06);display:flex;align-items:center;justify-content:space-between;}
.stage-name{font-size:9.5px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;}
.stage-num{font-size:10px;font-family:var(--mono);background:var(--bg3);color:var(--text3);padding:2px 7px;border-radius:10px;}
.pcard{margin:8px;padding:11px 12px;background:#fff;border:1px solid rgba(0,0,0,0.06);border-radius:10px;cursor:pointer;transition:box-shadow .12s,border-color .12s;}
.pcard:hover{box-shadow:var(--shadow-md);border-color:rgba(0,0,0,0.1);}
.pcard-name{font-size:12.5px;font-weight:600;margin-bottom:5px;color:var(--text);}
.pcard-meta{display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:5px;}
.pcard-val{font-family:var(--mono);font-size:10.5px;color:var(--text2);}
.pcard-owner{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--text3);margin-top:7px;}
.mini-av{width:16px;height:16px;border-radius:50%;font-size:7px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;}
.ma-y{background:rgba(79,70,229,0.15);color:#4F46E5;}
.ma-e{background:rgba(37,99,235,0.15);color:#2563eb;}
.pbar{height:3px;background:var(--bg3);border-radius:2px;margin-top:9px;overflow:hidden;}
.pfill{height:100%;border-radius:2px;}
"""

_LANDING_CSS = """
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp, section[data-testid="stMain"], .main, .block-container { background: #f5f5f7 !important; }
.main .block-container { max-width: 100% !important; padding: 0 !important; }
div[data-testid="column"] { padding: 0 6px !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { gap: 0 !important; }
div[data-testid="stButton"] { margin-top: -1px !important; }
div[data-testid="stButton"] button {
  border-radius: 0 0 12px 12px !important; border: none !important;
  font-size: 11px !important; font-weight: 600 !important;
  padding: 10px 16px !important; width: 100% !important;
  background: #4F46E5 !important; color: #fff !important;
}
div[data-testid="stButton"] button[data-partner-btn="true"] {
  background: #fff !important; color: #4F46E5 !important;
  border: 1.5px solid rgba(79,70,229,.3) !important;
}
div[data-testid="stButton"] button:hover { opacity: 0.88 !important; }
"""

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
      allBtns[1].style.setProperty('color','#4F46E5','important');
      allBtns[1].style.setProperty('border','1.5px solid rgba(79,70,229,.3)','important');
    }
  }
},100);"""
    else:
        current_page = st.session_state.get('page', 'Pipeline')
        btn_js = f"""
setTimeout(function(){{
  var pageToLabel={{'Pipeline':'Pipeline','Partners':'Partner Directory','Merchants':'Merchants','Contacts':'Key Contacts','Performance':'Performance','Benchmarks':'Benchmarks','Insights':'Insights'}};
  var labelBadge={{'Pipeline':'24','Partner Directory':'47','Merchants':'12','Key Contacts':'86','Performance':'','Benchmarks':'','Insights':''}};
  var activeLabel=pageToLabel['{current_page}']||'Pipeline';
  var sidebar=window.parent.document.querySelector('[data-testid="stSidebar"]');
  if(!sidebar)return;
  sidebar.querySelectorAll('button').forEach(function(btn){{
    var text=btn.textContent.trim();
    var found=Object.keys(labelBadge).find(function(k){{return text.includes(k);}});
    if(!found)return;
    var badge=labelBadge[found];
    var isActive=found===activeLabel;
    if(badge)btn.setAttribute('data-badge',badge);
    btn.setAttribute('data-nav-active',isActive?'true':'false');
  }});
  window.parent.document.querySelectorAll('button').forEach(function(btn){{
    if(btn.textContent.trim()==='← Landing'){{
      btn.style.cssText+='background:rgba(79,70,229,0.1)!important;color:#818cf8!important;border:1px solid rgba(79,70,229,0.25)!important;border-radius:20px!important;font-size:11px!important;padding:5px 14px!important;';
    }}
  }});
}},400);"""
    components.html(
        f"<script>var old=window.parent.document.getElementById('papo-css');if(old)old.remove();var s=window.parent.document.createElement('style');s.id='papo-css';s.textContent=`{escaped}`;window.parent.document.head.appendChild(s);{btn_js}</script>",
        height=0,
    )

# ── Landing Page ───────────────────────────────────────────────────────────────
def show_landing():
    LOGO = _LOGO_B64
    pending = st.session_state.get("pending_role")

    # ── Password screen ────────────────────────────────────────────────────────
    if pending:
        label      = "Yuno A-Team" if pending == "internal" else "Partner BD"
        icon       = "⚡" if pending == "internal" else "◈"
        icon_bg    = "#4F46E5" if pending == "internal" else "rgba(79,70,229,.12)"
        correct_pw = "Yuno" if pending == "internal" else "Partners"

        st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;background:transparent;">
  <div style="position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,70,229,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,70,229,.04) 1px,transparent 1px);background-size:48px 48px;-webkit-mask-image:radial-gradient(ellipse 80% 80% at 50% 50%,black 30%,transparent 100%);z-index:0;"></div>
  <div style="position:fixed;top:0;left:50%;transform:translateX(-50%);width:700px;height:500px;pointer-events:none;background:radial-gradient(ellipse,rgba(79,70,229,.10) 0%,transparent 70%);z-index:0;"></div>
  <div style="position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;">
    <img src="data:image/png;base64,{LOGO}" style="height:56px;object-fit:contain;margin-bottom:32px;opacity:.7;">
    <div style="width:56px;height:56px;border-radius:16px;background:{icon_bg};display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:20px;">{icon}</div>
    <div style="font-size:20px;font-weight:700;color:#1d1d1f;margin-bottom:6px;">Access {label}</div>
    <div style="font-size:12.5px;color:#6e6e73;margin-bottom:32px;">Enter your access code to continue</div>
  </div>
</div>
""", unsafe_allow_html=True)

        _, mc, _ = st.columns([1, 1.2, 1])
        with mc:
            pw = st.text_input("Access code", type="password", key="pw_input",
                               placeholder="Enter password…", label_visibility="collapsed")
            if st.session_state.get("pw_error"):
                st.markdown('<p style="color:#ef4444;font-size:11px;text-align:center;margin:4px 0 8px;">Incorrect password — try again.</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back", key="pw_back", use_container_width=True):
                    st.session_state.pending_role = None
                    st.session_state.pw_error = False
                    st.rerun()
            with c2:
                if st.button("Enter →", key="pw_submit", use_container_width=True, type="primary"):
                    if pw == correct_pw:
                        st.session_state.role = pending
                        st.session_state.pending_role = None
                        st.session_state.pw_error = False
                        st.session_state.page = "Home"
                        st.query_params["role"] = pending
                        st.query_params["page"] = "Home"
                        st.rerun()
                    else:
                        st.session_state.pw_error = True
                        st.rerun()
        return  # don't render cards below

    # ── Card selection screen ──────────────────────────────────────────────────
    st.markdown(f"""
<div style="text-align:center;padding:36px 24px 20px;position:relative;overflow:hidden;">
  <div style="position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,70,229,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,70,229,.04) 1px,transparent 1px);background-size:48px 48px;-webkit-mask-image:radial-gradient(ellipse 80% 80% at 50% 50%,black 30%,transparent 100%);z-index:0;"></div>
  <div style="position:fixed;top:0;left:50%;transform:translateX(-50%);width:700px;height:500px;pointer-events:none;background:radial-gradient(ellipse,rgba(79,70,229,.12) 0%,transparent 70%);z-index:0;"></div>
  <div style="position:relative;z-index:1;">
    <img src="data:image/png;base64,{LOGO}" style="height:200px;object-fit:contain;margin-bottom:16px;">
    <div style="font-size:22px;font-weight:700;letter-spacing:-0.8px;line-height:1.2;margin-bottom:8px;color:#1d1d1f;">Welcome to the<br><span style="color:#4F46E5;">Partner Portal</span></div>
    <p style="font-size:12.5px;color:#6e6e73;line-height:1.6;max-width:400px;margin:0 auto 28px;">Your unified workspace for managing the Yuno partner ecosystem.</p>
  </div>
</div>
""", unsafe_allow_html=True)

    _, col1, col2, _ = st.columns([1.5, 2, 2, 1.5])

    with col1:
        st.markdown("""
<div style="background:#4F46E5;border:1.5px solid #4F46E5;border-radius:14px 14px 0 0;padding:20px 20px 14px;text-align:left;">
  <div style="width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:17px;margin-bottom:12px;">⚡</div>
  <div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:12px;">Yuno A-Team</div>
  <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px;">
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(255,255,255,.18);color:#fff;font-family:monospace;">Full pipeline</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(255,255,255,.18);color:#fff;font-family:monospace;">Internal notes</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(255,255,255,.18);color:#fff;font-family:monospace;">Revenue intel</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(255,255,255,.18);color:#fff;font-family:monospace;">Strategy</span>
  </div>
</div>
""", unsafe_allow_html=True)
        if st.button("Get Started  →", key="btn_internal", use_container_width=True):
            st.session_state.pending_role = "internal"
            st.session_state.pw_error = False
            st.rerun()

    with col2:
        st.markdown("""
<div style="background:#fff;border:1.5px solid #fff;border-radius:14px 14px 0 0;padding:20px 20px 14px;text-align:left;">
  <div style="width:38px;height:38px;border-radius:10px;background:rgba(79,70,229,.1);display:flex;align-items:center;justify-content:center;font-size:17px;margin-bottom:12px;">◈</div>
  <div style="font-size:14px;font-weight:700;color:#4F46E5;margin-bottom:12px;">Partner BD</div>
  <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px;">
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(79,70,229,.12);color:#4F46E5;font-family:monospace;">Shared pipeline</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(79,70,229,.12);color:#4F46E5;font-family:monospace;">Performance</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(79,70,229,.12);color:#4F46E5;font-family:monospace;">Your contacts</span>
    <span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;background:rgba(79,70,229,.12);color:#4F46E5;font-family:monospace;">Insights</span>
  </div>
</div>
""", unsafe_allow_html=True)
        if st.button("Get Started  →", key="btn_partner", use_container_width=True):
            st.session_state.pending_role = "partner"
            st.session_state.pw_error = False
            st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────────
def show_sidebar():
    is_internal = st.session_state.role == "internal"
    role_label = "INTERNAL" if is_internal else "PARTNER"
    role_bg = "rgba(79,70,229,0.12)" if is_internal else "rgba(79,70,229,0.08)"
    role_color = "#4F46E5" if is_internal else "#4F46E5"

    with st.sidebar:
        # User identity — top of sidebar
        if is_internal:
            top_user_html = f"""
<div style="padding:14px 16px 12px;border-bottom:1px solid rgba(0,0,0,0.07);display:flex;align-items:center;gap:10px;">
  <img src="data:image/png;base64,{_DANIELA_B64}" style="width:30px;height:30px;border-radius:50%;object-fit:cover;flex-shrink:0;">
  <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;">Daniela Reyes</div><div style="font-size:10px;color:#86868b;">Head of Partnerships · Yuno</div></div>
</div>"""
        else:
            top_user_html = """
<div style="padding:14px 16px 12px;border-bottom:1px solid rgba(0,0,0,0.07);display:flex;align-items:center;gap:10px;">
  <div style="width:30px;height:30px;border-radius:50%;background:rgba(37,99,235,0.1);color:#2563eb;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;">TK</div>
  <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;">Tom Kuehn</div><div style="font-size:10px;color:#86868b;">LATAM Partnerships · Adyen</div></div>
</div>"""
        st.markdown(top_user_html, unsafe_allow_html=True)

        # Logo header
        st.markdown(f"""
<div style="padding:20px 16px 16px;border-bottom:1px solid rgba(0,0,0,0.07);text-align:center;">
  <img src="data:image/png;base64,{_LOGO_B64}" style="width:100%;max-width:180px;object-fit:contain;display:block;margin:0 auto 12px;">
  <div style="font-size:9px;font-weight:700;background:{role_bg};color:{role_color};padding:3px 12px;border-radius:20px;letter-spacing:1px;text-transform:uppercase;font-family:monospace;display:inline-block;">{role_label}</div>
</div>
""", unsafe_allow_html=True)

        # WORKSPACE nav
        st.markdown('<div style="padding:20px 12px 6px;font-size:9px;font-weight:700;letter-spacing:1.2px;color:#86868b;text-transform:uppercase;">Workspace</div>', unsafe_allow_html=True)

        NAV = [
            ("Pipeline",    "⟳  Pipeline"),
            ("Merchants",   "◻  Merchants"),
            ("Contacts",    "◉  Key Contacts"),
            ("Performance", "▲  Performance"),
            ("Benchmarks",  "◑  Benchmarks"),
            ("Insights",    "◎  Insights"),
        ]
        if is_internal:
            NAV.insert(1, ("Partners", "◈  Partner Directory"))
        for page_key, label in NAV:
            if st.button(label, key=f"nav_{page_key}", use_container_width=True,
                         type="secondary"):
                st.session_state.page = page_key
                st.query_params["page"] = page_key
                st.query_params["role"] = st.session_state.role
                st.rerun()


# ── Stat Row ───────────────────────────────────────────────────────────────────
def stat_row(stats):
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        val_color = f"color:{s.get('val_color','#4F46E5')};"
        delta_color = {"up":"#16a34a","down":"#dc2626","flat":"#86868b"}.get(s.get("delta_type","flat"), "#86868b")
        col.markdown(f"""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border-radius:12px;padding:18px 20px;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:12px 12px 0 0;"></div>
  <div style="font-size:10px;color:#86868b;letter-spacing:0.5px;text-transform:uppercase;font-weight:600;margin-bottom:8px;">{s['label']}</div>
  <div style="font-size:22px;font-weight:700;font-family:'Menlo',monospace;letter-spacing:-1px;line-height:1;{val_color}">{s['value']}</div>
  <div style="font-size:11px;margin-top:6px;color:{delta_color};">{s['delta']}</div>
</div>""", unsafe_allow_html=True)

# ── Pipeline View ──────────────────────────────────────────────────────────────
def show_pipeline():
    is_internal = st.session_state.role == "internal"

    st.markdown("""
<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid rgba(0,0,0,0.07);">
  <span style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.5px;">Merchant Pipeline</span>
  <span style="font-size:12px;color:#86868b;">24 active opportunities</span>
</div>
""", unsafe_allow_html=True)

    stat_row([
        {"label":"Pipeline Value","value":"$4.2M","delta":"↑ 18% vs last qtr","delta_type":"up","val_color":"#818cf8"},
        {"label":"Active Deals","value":"24","delta":"↑ 3 this week","delta_type":"up"},
        {"label":"Avg Deal Size","value":"$175K","delta":"→ steady","delta_type":"flat"},
        {"label":"Win Rate","value":"38%","delta":"↑ 4pts QoQ","delta_type":"up"},
    ])

    st.markdown("""
<div style="margin-top:20px;margin-bottom:10px;">
  <span style="font-size:16px;font-weight:700;color:#1d1d1f;letter-spacing:-0.3px;">Deal Board</span>
  <span style="font-size:11px;color:#86868b;margin-left:10px;">Drag to move · Click to open · Internal notes visible to Yuno BD only</span>
</div>
""", unsafe_allow_html=True)

    # Kanban board as HTML (no <style> tag — styles injected via JS already)
    kanban_html = """
<div class="pipeline-wrap">
<div class="pipeline-board">

<!-- Prospect -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#6e6e73;">Prospect</span><span class="stage-num">6</span></div>
  <div class="pcard"><div class="pcard-name">Qatar Airways</div><div class="pcard-meta"><span class="pill cat-psp">Travel</span><span class="pill p-amber">Warm</span></div><div class="pcard-val">$80K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R. · via Adyen ref</div><div class="pbar"><div class="pfill" style="width:15%;background:#86868b;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Bancolombia</div><div class="pcard-meta"><span class="pill cat-acquirer">Banking</span><span class="pill p-blue">Inbound</span></div><div class="pcard-val">$120K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">JL</span>Jorge L. · Direct</div><div class="pbar"><div class="pfill" style="width:10%;background:#3b82f6;"></div></div></div>
  <div class="pcard"><div class="pcard-name">iFood</div><div class="pcard-meta"><span class="pill cat-baas">Food</span><span class="pill p-amber">Pilot</span></div><div class="pcard-val">$200K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">MC</span>Maria C. · Direct</div><div class="pbar"><div class="pfill" style="width:12%;background:#f59e0b;"></div></div></div>
</div>

<!-- Qualified -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#60a5fa;">Qualified</span><span class="stage-num">5</span></div>
  <div class="pcard"><div class="pcard-name">Rappi</div><div class="pcard-meta"><span class="pill cat-apm">Super App</span><span class="pill p-green">Hot</span></div><div class="pcard-val">$350K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:30%;background:#22c55e;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Falabella</div><div class="pcard-meta"><span class="pill cat-acquirer">Retail</span><span class="pill p-blue">Active</span></div><div class="pcard-val">$180K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">AP</span>Ana P. · Partner ref</div><div class="pbar"><div class="pfill" style="width:28%;background:#3b82f6;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Despegar</div><div class="pcard-meta"><span class="pill cat-fraud">Travel</span><span class="pill p-purple">Trial</span></div><div class="pcard-val">$95K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DG</span>Diego G.</div><div class="pbar"><div class="pfill" style="width:25%;background:#a855f7;"></div></div></div>
</div>

<!-- Evaluation -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#c084fc;">Evaluation</span><span class="stage-num">7</span></div>
  <div class="pcard"><div class="pcard-name">Spotify</div><div class="pcard-meta"><span class="pill cat-psp">Streaming</span><span class="pill p-green">Hot</span></div><div class="pcard-val">$620K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">RV</span>Ricardo V. · Direct</div><div class="pbar"><div class="pfill" style="width:55%;background:#a855f7;"></div></div></div>
  <div class="pcard"><div class="pcard-name">PedidosYa</div><div class="pcard-meta"><span class="pill cat-apm">Food</span><span class="pill p-teal">Active</span></div><div class="pcard-val">$240K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:50%;background:#14b8a6;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Claro</div><div class="pcard-meta"><span class="pill cat-acquirer">Telco</span><span class="pill p-amber">Stalled</span></div><div class="pcard-val">$310K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">LM</span>Luisa M. · Partner</div><div class="pbar"><div class="pfill" style="width:48%;background:#f59e0b;"></div></div></div>
  <div class="pcard"><div class="pcard-name">MercadoLibre</div><div class="pcard-meta"><span class="pill cat-baas">E-commerce</span><span class="pill p-amber">New</span></div><div class="pcard-val">$440K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">MC</span>Maria C.</div><div class="pbar"><div class="pfill" style="width:42%;background:#f59e0b;"></div></div></div>
</div>

<!-- Negotiation -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#fbbf24;">Negotiation</span><span class="stage-num">2</span></div>
  <div class="pcard"><div class="pcard-name">Uber</div><div class="pcard-meta"><span class="pill cat-acquirer">Mobility</span><span class="pill p-green">High Priority</span></div><div class="pcard-val">$850K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-e">FM</span>Felipe M. · Direct</div><div class="pbar"><div class="pfill" style="width:75%;background:#4F46E5;"></div></div></div>
  <div class="pcard"><div class="pcard-name">Cinépolis</div><div class="pcard-meta"><span class="pill cat-apm">Entertainment</span><span class="pill p-blue">Regional</span></div><div class="pcard-val">$110K ARR est.</div><div class="pcard-owner"><span class="mini-av ma-y">DG</span>Diego G.</div><div class="pbar"><div class="pfill" style="width:70%;background:#14b8a6;"></div></div></div>
</div>

<!-- Won -->
<div class="stage-col">
  <div class="stage-head"><span class="stage-name" style="color:#4ade80;">Won</span><span class="stage-num">2</span></div>
  <div class="pcard" style="border-color:rgba(34,197,94,.25);"><div class="pcard-name">Netflix</div><div class="pcard-meta"><span class="pill cat-psp">Streaming</span><span class="pill p-green">Live</span></div><div class="pcard-val">$1.2M ARR signed</div><div class="pcard-owner"><span class="mini-av ma-e">TK</span>Tom K. · Direct</div><div class="pbar"><div class="pfill" style="width:100%;background:#22c55e;"></div></div></div>
  <div class="pcard" style="border-color:rgba(34,197,94,.25);"><div class="pcard-name">Linio</div><div class="pcard-meta"><span class="pill cat-fraud">E-commerce</span><span class="pill p-green">Live</span></div><div class="pcard-val">$290K ARR signed</div><div class="pcard-owner"><span class="mini-av ma-y">DR</span>Daniela R.</div><div class="pbar"><div class="pfill" style="width:100%;background:#22c55e;"></div></div></div>
</div>

</div></div>"""
    st.markdown(kanban_html, unsafe_allow_html=True)

    # Bottom row: funnel + activity
    col_funnel, col_activity = st.columns([3, 2])

    with col_funnel:
        st.markdown('<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:18px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;font-weight:700;color:#1d1d1f;margin-bottom:2px;">Pipeline Funnel</div><div style="font-size:11px;color:#86868b;margin-bottom:14px;">Current quarter · all categories</div>', unsafe_allow_html=True)
        funnel_data = [("Prospect",6,100,"#86868b"),("Qualified",5,83,"#6e6e73"),("Evaluation",7,100,"#a855f7"),("Negotiation",4,50,"#f59e0b"),("Won",2,33,"#22c55e")]
        funnel_html = ""
        for label, count, pct, color in funnel_data:
            funnel_html += f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
  <span style="font-size:11px;color:#6e6e73;width:90px;text-align:right;flex-shrink:0;">{label}</span>
  <div style="flex:1;height:24px;background:#f9f9fb;border-radius:4px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:{color};display:flex;align-items:center;padding-left:10px;font-size:10px;font-family:monospace;font-weight:600;color:rgba(0,0,0,0.7);">{count} deals</div>
  </div>
  <span style="font-size:11px;font-family:monospace;color:#6e6e73;width:20px;">{count}</span>
</div>"""
        st.markdown(funnel_html, unsafe_allow_html=True)

        if is_internal:
            st.markdown("""
<div style="border:1px solid rgba(245,158,11,.22);background:rgba(245,158,11,.04);border-radius:10px;padding:13px 16px;margin-top:16px;">
  <div style="font-size:9.5px;font-weight:700;color:#d97706;letter-spacing:.9px;text-transform:uppercase;margin-bottom:10px;">🔒 Internal Yuno Only</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Blended margin (est.)</span><span style="font-family:monospace;color:#d97706;">61%</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Committed quota coverage</span><span style="font-family:monospace;color:#d97706;">2.4×</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;"><span style="color:#6e6e73;">At-risk deals (&gt;90d stalled)</span><span style="font-family:monospace;color:#d97706;">3</span></div>
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_activity:
        st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:18px;">
  <div style="font-size:13px;font-weight:700;color:#1d1d1f;margin-bottom:2px;">Recent Activity</div>
  <div style="font-size:11px;color:#86868b;margin-bottom:14px;">Last 48 hours</div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#22c55e;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#6e6e73;line-height:1.55;"><strong style="color:#1d1d1f;">Uber</strong> moved to Negotiation. MSA draft sent.</div><div style="font-size:10px;color:#86868b;font-family:monospace;margin-top:2px;">2h ago · Daniela R.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#3b82f6;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#6e6e73;line-height:1.55;"><strong style="color:#1d1d1f;">Spotify</strong> technical review call scheduled for Dec 18.</div><div style="font-size:10px;color:#86868b;font-family:monospace;margin-top:2px;">5h ago · Ricardo V.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#f59e0b;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#6e6e73;line-height:1.55;"><strong style="color:#1d1d1f;">MercadoLibre</strong> added as new e-commerce opportunity.</div><div style="font-size:10px;color:#86868b;font-family:monospace;margin-top:2px;">Yesterday · Maria C.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <div style="width:7px;height:7px;border-radius:50%;background:#4F46E5;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#6e6e73;line-height:1.55;"><strong style="color:#1d1d1f;">Netflix</strong> integration live. First transaction processed.</div><div style="font-size:10px;color:#86868b;font-family:monospace;margin-top:2px;">Yesterday · Tom K.</div></div>
  </div>
  <div style="display:flex;gap:10px;padding:9px 0;">
    <div style="width:7px;height:7px;border-radius:50%;background:#a855f7;margin-top:4px;flex-shrink:0;"></div>
    <div><div style="font-size:12px;color:#6e6e73;line-height:1.55;"><strong style="color:#1d1d1f;">Despegar</strong> trial extended to Jan 15. Positive signal.</div><div style="font-size:10px;color:#86868b;font-family:monospace;margin-top:2px;">2d ago · Diego G.</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Partners View ──────────────────────────────────────────────────────────────
def show_partners():
    st.markdown('<div style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.8px;margin-bottom:4px;">Partner Directory</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:16px;">47 partners across 5 categories</div>', unsafe_allow_html=True)

    stat_row([
        {"label":"Total Partners","value":"47","delta":"↑ 6 this quarter","delta_type":"up"},
        {"label":"Live Integrations","value":"31","delta":"→ 66% of total","delta_type":"flat"},
        {"label":"In Development","value":"11","delta":"↑ 3 new","delta_type":"up"},
        {"label":"Avg Integration","value":"42d","delta":"↓ 5d faster","delta_type":"down"},
        {"label":"BaaS Pipeline","value":"4","delta":"★ New vertical","delta_type":"up","val_color":"#818cf8"},
    ])

    # Filters
    search = st.text_input("", placeholder="⌕  Search partners...", key="partner_search_input", label_visibility="collapsed")
    components.html("""<script>
function attachLiveSearch(){
  var doc = window.parent.document;
  var inputs = doc.querySelectorAll('input[type="text"]');
  inputs.forEach(function(el){
    if(el.placeholder && el.placeholder.includes('Search partners')){
      if(el._liveSearch) return;
      el._liveSearch = true;
      el.addEventListener('keyup', function(e){
        if(e.key === 'Enter') return;
        var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        nativeSetter.call(el, el.value);
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new KeyboardEvent('keydown', {bubbles:true, cancelable:true, key:'Enter', keyCode:13, which:13}));
        setTimeout(function(){
          el.dispatchEvent(new KeyboardEvent('keyup', {bubbles:true, cancelable:true, key:'Enter', keyCode:13, which:13}));
        }, 10);
      });
    }
  });
}
var interval = setInterval(function(){
  var doc = window.parent.document;
  var el = doc.querySelector('input[placeholder*="Search partners"]');
  if(el && !el._liveSearch){ attachLiveSearch(); }
}, 300);
setTimeout(function(){ clearInterval(interval); }, 15000);
</script>""", height=0)
    cats   = ["All","Acquirers","PSPs","APMs","Fraud & Risk","BaaS","🟢 Live only"]
    cat_cols = st.columns(len(cats))
    for i, (col, cat) in enumerate(zip(cat_cols, cats)):
        if col.button(cat, key=f"cat_{i}", use_container_width=True):
            st.session_state.cat_filter = cat

    # Filter logic
    filt = PARTNERS_DATA.copy()
    if st.session_state.cat_filter not in ["All", ""]:
        cat_map = {"Acquirers":"Acquirer","PSPs":"PSP","APMs":"APM","Fraud & Risk":"Fraud","BaaS":"BaaS"}
        if st.session_state.cat_filter == "🟢 Live only":
            filt = [p for p in filt if p["status"] == "Live"]
        elif st.session_state.cat_filter in cat_map:
            filt = [p for p in filt if p["cat"] == cat_map[st.session_state.cat_filter]]
    if search:
        filt = [p for p in filt if p["name"].lower().startswith(search.lower())]

    # Render grid
    cols_per_row = 4
    for i in range(0, len(filt), cols_per_row):
        row_partners = filt[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, p in zip(cols, row_partners):
            sc = STATUS_CLASS.get(p["status"], "p-grey")
            cc = CAT_CLASS.get(p["type"], "p-grey")
            col.markdown(f"""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:9px;padding:11px 13px;margin-bottom:9px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:30px;height:30px;border-radius:7px;background:{p['color']}22;color:{p['color']};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;">{p['logo']}</div>
      <div><div style="font-size:12px;font-weight:700;color:#1d1d1f;line-height:1.2;">{p['name']}</div><div style="font-size:10px;color:#86868b;">{p['region']}</div></div>
    </div>
    <span class="pill {sc}" style="font-size:9px;padding:2px 6px;">{p['status']}</span>
  </div>
  <span class="pill {cc}" style="margin-bottom:8px;display:inline-flex;font-size:9px;padding:2px 6px;">{p['type']}</span>
  <hr style="border:none;border-top:1px solid rgba(0,0,0,0.06);margin:7px 0;">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;">
    <div style="background:#f5f5f7;border-radius:6px;padding:6px 8px;border:1px solid rgba(0,0,0,0.05);"><div style="font-size:8.5px;color:#86868b;margin-bottom:1px;">TPV Routed</div><div style="font-size:12px;font-weight:700;font-family:monospace;color:{p['color']};">{p['tpv']}</div></div>
    <div style="background:#f5f5f7;border-radius:6px;padding:6px 8px;border:1px solid rgba(0,0,0,0.05);"><div style="font-size:8.5px;color:#86868b;margin-bottom:1px;">Auth Rate</div><div style="font-size:12px;font-weight:700;font-family:monospace;color:#1d1d1f;">{p['auth']}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Contacts View ──────────────────────────────────────────────────────────────
YUNO_CONTACTS = [
    {"init":"DR","bg":"rgba(79,70,229,0.2)","color":"#818cf8","name":"Daniela Reyes","role":"Head of Partnerships","dept":"Partnerships · Yuno","badge":"Your Lead","badge_class":"p-purple","last":"Today","rel":"Primary contact","scope":"Strategy & commercial terms"},
    {"init":"MS","bg":"rgba(79,70,229,0.2)","color":"#818cf8","name":"Marco Silva","role":"Partnership Manager · LATAM","dept":"Partnerships · Yuno","badge":"BD","badge_class":"p-blue","last":"1d ago","rel":"Day-to-day","scope":"Pipeline & deal support"},
    {"init":"LG","bg":"rgba(79,70,229,0.2)","color":"#818cf8","name":"Laura Gómez","role":"Partnership Manager · MX & COL","dept":"Partnerships · Yuno","badge":"BD","badge_class":"p-blue","last":"3d ago","rel":"Day-to-day","scope":"MX & COL opportunities"},
    {"init":"JR","bg":"rgba(20,184,166,0.2)","color":"#2dd4bf","name":"Jorge Restrepo","role":"Delivery Manager","dept":"Integrations · Yuno","badge":"Technical","badge_class":"p-teal","last":"2d ago","rel":"Integration lead","scope":"Onboarding & go-live"},
    {"init":"VP","bg":"rgba(20,184,166,0.2)","color":"#2dd4bf","name":"Valentina Perez","role":"Solutions Engineer","dept":"Integrations · Yuno","badge":"Technical","badge_class":"p-teal","last":"5d ago","rel":"Tech support","scope":"API & certification queries"},
    {"init":"AS","bg":"rgba(34,197,94,0.2)","color":"#4ade80","name":"Andrés Suárez","role":"Marketing Manager · Partners","dept":"Marketing · Yuno","badge":"Marketing","badge_class":"p-green","last":"1w ago","rel":"Co-marketing","scope":"Joint campaigns & content"},
    {"init":"CB","bg":"rgba(34,197,94,0.2)","color":"#4ade80","name":"Carolina Blanco","role":"Partner Marketing Specialist","dept":"Marketing · Yuno","badge":"Marketing","badge_class":"p-green","last":"4d ago","rel":"Co-marketing","scope":"Case studies & events"},
    {"init":"RM","bg":"rgba(245,158,11,0.2)","color":"#fbbf24","name":"Rafael Mendoza","role":"Customer Success Manager","dept":"Success · Yuno","badge":"Success","badge_class":"p-amber","last":"Today","rel":"Escalation point","scope":"Performance & health"},
    {"init":"NF","bg":"rgba(245,158,11,0.2)","color":"#fbbf24","name":"Natalia Ferro","role":"Revenue Operations","dept":"RevOps · Yuno","badge":"Ops","badge_class":"p-amber","last":"2d ago","rel":"Reporting","scope":"Invoicing & SLAs"},
]

def show_contacts():
    is_internal = st.session_state.role == "internal"

    if not is_internal:
        st.markdown('<div style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.8px;margin-bottom:4px;">Your Yuno Team</div>'
                    '<div style="font-size:11px;color:#86868b;margin-bottom:16px;">Your dedicated Yuno contacts across partnerships, integrations, marketing & success</div>', unsafe_allow_html=True)
        contacts_data = YUNO_CONTACTS
        label_a, label_b = "Scope", "Role"
    else:
        st.markdown('<div style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.8px;margin-bottom:4px;">Key Contacts</div>'
                    '<div style="font-size:11px;color:#86868b;margin-bottom:16px;">BD counterparts, technical leads & executive sponsors across partner organizations</div>', unsafe_allow_html=True)
        contacts_data = CONTACTS
        label_a, label_b = "Deals involved", "Relationship"

    cols_per_row = 3
    for i in range(0, len(contacts_data), cols_per_row):
        row = contacts_data[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, c in zip(cols, row):
            if not is_internal:
                detail_a = c['scope']
                detail_b = c['dept']
                actions = f"""
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:rgba(79,70,229,0.12);color:#818cf8;border:1px solid rgba(79,70,229,0.25);cursor:pointer;font-family:inherit;">📧 Email</button>
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:#f9f9fb;color:#6e6e73;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;cursor:pointer;font-family:inherit;">📅 Schedule</button>
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:#f9f9fb;color:#6e6e73;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;cursor:pointer;font-family:inherit;">💬 Slack</button>"""
            else:
                detail_a = c['deals']
                detail_b = c['rel']
                actions = f"""
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:rgba(79,70,229,0.1);color:#4F46E5;border:1px solid rgba(79,70,229,0.25);cursor:pointer;font-family:inherit;">📧 Email</button>
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:#f9f9fb;color:#6e6e73;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;cursor:pointer;font-family:inherit;">📅 Schedule</button>
    <button style="flex:1;padding:6px;border-radius:6px;font-size:10px;font-weight:600;background:#f9f9fb;color:#6e6e73;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;cursor:pointer;font-family:inherit;">📝 Note</button>"""

            company_key = 'dept' if not is_internal else 'company'
            col.markdown(f"""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;margin-bottom:12px;">
  <div style="display:flex;align-items:flex-start;gap:11px;margin-bottom:12px;">
    <div style="width:36px;height:36px;border-radius:50%;background:{c['bg']};color:{c['color']};display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;">{c['init']}</div>
    <div style="flex:1;">
      <div style="font-size:13px;font-weight:700;color:#1d1d1f;">{c['name']}</div>
      <div style="font-size:11px;color:#6e6e73;margin-top:1px;">{c['role']}</div>
      <div style="font-size:10px;color:#86868b;margin-top:2px;">{c[company_key]}</div>
    </div>
    <span class="pill {c['badge_class']}">{c['badge']}</span>
  </div>
  <hr style="border:none;border-top:1px solid rgba(0,0,0,0.07);margin:0 0 10px;">
  <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><span style="font-size:10.5px;color:#86868b;">Last contact</span><span style="font-size:10.5px;color:#6e6e73;font-family:monospace;">{c['last']}</span></div>
  <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><span style="font-size:10.5px;color:#86868b;">{label_b}</span><span style="font-size:10.5px;color:#6e6e73;font-family:monospace;">{detail_b}</span></div>
  <div style="display:flex;justify-content:space-between;margin-bottom:10px;"><span style="font-size:10.5px;color:#86868b;">{label_a}</span><span style="font-size:10.5px;color:#6e6e73;font-family:monospace;">{detail_a}</span></div>
  <div style="display:flex;gap:6px;">{actions}
  </div>
</div>""", unsafe_allow_html=True)

    if is_internal:
        st.markdown("""
<div style="border:1px solid rgba(245,158,11,.22);background:rgba(245,158,11,.04);border-radius:10px;padding:13px 16px;margin-top:8px;">
  <div style="font-size:9.5px;font-weight:700;color:#d97706;letter-spacing:.9px;text-transform:uppercase;margin-bottom:10px;">🔒 Internal BD Notes — Not Visible to Partners</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Tom Kuehn (Adyen) — negotiating exclusivity window on MX corridor, do not share with other acquirers</span><span style="font-family:monospace;color:#d97706;">Confidential</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Felipe Morales (Getnet) — board approval needed above $500K. Target Jan board meeting.</span><span style="font-family:monospace;color:#d97706;">Action needed</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;"><span style="color:#6e6e73;">Martín Castillo (Pomelo) — exploring white-label orchestration. High strategic value for BaaS play.</span><span style="font-family:monospace;color:#d97706;">Strategic</span></div>
</div>""", unsafe_allow_html=True)

# ── Performance View ───────────────────────────────────────────────────────────
def show_performance():
    is_internal = st.session_state.role == "internal"
    st.markdown('<div style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.8px;margin-bottom:4px;">Performance Dashboard</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:16px;">Live partner analytics</div>', unsafe_allow_html=True)

    stat_row([
        {"label":"Total TPV (Live Partners)","value":"$2.4B","delta":"↑ 34% YoY","delta_type":"up","val_color":"#818cf8"},
        {"label":"Transactions/mo","value":"142M","delta":"↑ 22% MoM","delta_type":"up"},
        {"label":"Auth Rate (avg)","value":"89.4%","delta":"↑ 1.2pts","delta_type":"up"},
        {"label":"Partner Revenue","value":"$18.6M","delta":"↑ 28% QoQ","delta_type":"up"},
        {"label":"NPS (Partners)","value":"72","delta":"↑ 8pts","delta_type":"up"},
    ])

    col_tpv, col_mix = st.columns([2.2, 1])

    with col_tpv:
        months = ["May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        fig = go.Figure()
        datasets = [
            ("Acquirers",[820,880,910,950,1020,1100,1180,1240],"rgba(59,130,246,.7)"),
            ("PSPs",[420,460,490,530,580,640,700,780],"rgba(168,85,247,.7)"),
            ("APMs",[180,200,230,260,300,340,390,440],"rgba(20,184,166,.7)"),
            ("Fraud",[60,70,80,90,100,115,130,150],"rgba(239,68,68,.6)"),
            ("BaaS",[0,0,0,0,10,25,45,80],"rgba(245,158,11,.7)"),
        ]
        for name, data, color in datasets:
            fig.add_trace(go.Bar(name=name, x=months, y=data, marker_color=color))
        fig.update_layout(
            barmode="stack", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", size=10),
            margin=dict(l=40,r=10,t=30,b=30),
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            height=280,
            title=dict(text="Monthly TPV by Partner Category", font=dict(color="#1d1d1f", size=13), x=0),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)", ticksuffix="M"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_mix:
        fig2 = go.Figure(go.Pie(
            labels=["Acquirers","PSPs","APMs","Fraud","BaaS"],
            values=[38,31,19,8,4],
            hole=0.65,
            marker_colors=["rgba(59,130,246,.8)","rgba(168,85,247,.8)","rgba(20,184,166,.8)","rgba(239,68,68,.75)","rgba(245,158,11,.8)"],
            textinfo="none",
        ))
        fig2.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73",size=10),
            margin=dict(l=10,r=10,t=50,b=10),
            legend=dict(font=dict(size=10,color="#6e6e73")),
            height=280,
            title=dict(text="TPV Mix by Category", font=dict(color="#1d1d1f",size=13), x=0),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    col_auth, col_health = st.columns(2)

    with col_auth:
        partners_list = ["Adyen","Prosa","Getnet","OpenPix","Kushki","Cielo","SEON","Nuvei"]
        rates = [92.4, 90.1, 89.6, 99.1, 88.2, 86.9, 85.0, 84.1]
        colors = ["rgba(34,197,94,.7)" if r>=90 else "rgba(59,130,246,.7)" if r>=87 else "rgba(239,68,68,.7)" for r in rates]
        fig3 = go.Figure(go.Bar(x=rates, y=partners_list, orientation="h", marker_color=colors, marker=dict(cornerradius=3)))
        fig3.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73",size=10),
            margin=dict(l=10,r=20,t=50,b=30),
            height=260,
            title=dict(text="Auth Rate by Partner (Top 8)", font=dict(color="#1d1d1f",size=13), x=0),
            xaxis=dict(range=[80,100], ticksuffix="%", gridcolor="rgba(0,0,0,0.06)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_health:
        st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:18px;">
  <div style="font-size:13px;font-weight:700;color:#1d1d1f;margin-bottom:2px;">Partner Health Scorecard</div>
  <div style="font-size:11px;color:#86868b;margin-bottom:14px;">Integration quality · engagement · growth</div>
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <tr style="background:#f5f5f7;"><th style="text-align:left;padding:6px 8px;font-size:9.5px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:#86868b;">Partner</th><th style="padding:6px 8px;font-size:9.5px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:#86868b;">Health</th><th style="padding:6px 8px;font-size:9.5px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:#86868b;">TPV Trend</th><th style="padding:6px 8px;font-size:9.5px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:#86868b;">Issues</th></tr>
    <tr style="border-bottom:1px solid rgba(0,0,0,0.07);"><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">Adyen</td><td style="padding:7px 8px;"><span style="background:rgba(34,197,94,.14);color:#4ade80;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">95</span></td><td style="padding:7px 8px;color:#22c55e;font-family:monospace;">+18%</td><td style="padding:7px 8px;color:#86868b;">0</td></tr>
    <tr style="border-bottom:1px solid rgba(0,0,0,0.07);"><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">Getnet</td><td style="padding:7px 8px;"><span style="background:rgba(34,197,94,.14);color:#4ade80;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">88</span></td><td style="padding:7px 8px;color:#22c55e;font-family:monospace;">+42%</td><td style="padding:7px 8px;color:#86868b;">1</td></tr>
    <tr style="border-bottom:1px solid rgba(0,0,0,0.07);"><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">Kushki</td><td style="padding:7px 8px;"><span style="background:rgba(59,130,246,.14);color:#60a5fa;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">81</span></td><td style="padding:7px 8px;color:#22c55e;font-family:monospace;">+9%</td><td style="padding:7px 8px;color:#86868b;">2</td></tr>
    <tr style="border-bottom:1px solid rgba(0,0,0,0.07);"><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">OpenPix</td><td style="padding:7px 8px;"><span style="background:rgba(59,130,246,.14);color:#60a5fa;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">79</span></td><td style="padding:7px 8px;color:#22c55e;font-family:monospace;">+31%</td><td style="padding:7px 8px;color:#d97706;">1</td></tr>
    <tr style="border-bottom:1px solid rgba(0,0,0,0.07);"><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">SEON</td><td style="padding:7px 8px;"><span style="background:rgba(245,158,11,.14);color:#fbbf24;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">71</span></td><td style="padding:7px 8px;color:#22c55e;font-family:monospace;">+6%</td><td style="padding:7px 8px;color:#d97706;">3</td></tr>
    <tr><td style="padding:7px 8px;font-weight:600;color:#1d1d1f;">Nuvei</td><td style="padding:7px 8px;"><span style="background:rgba(245,158,11,.14);color:#fbbf24;font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;font-family:monospace;">68</span></td><td style="padding:7px 8px;color:#ef4444;font-family:monospace;">−4%</td><td style="padding:7px 8px;color:#ef4444;">4</td></tr>
  </table>
</div>""", unsafe_allow_html=True)

    if is_internal:
        st.markdown("""
<div style="border:1px solid rgba(245,158,11,.22);background:rgba(245,158,11,.04);border-radius:10px;padding:13px 16px;margin-top:16px;">
  <div style="font-size:9.5px;font-weight:700;color:#d97706;letter-spacing:.9px;text-transform:uppercase;margin-bottom:10px;">🔒 Internal Revenue Intelligence</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Blended take rate (all live partners)</span><span style="font-family:monospace;color:#d97706;">0.048%</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Adyen contract renewal date</span><span style="font-family:monospace;color:#d97706;">Mar 2025 · auto-renew flag on</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Nuvei performance clause risk</span><span style="font-family:monospace;color:#d97706;">⚠ Below SLA — escalate</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;"><span style="color:#6e6e73;">BaaS vertical projected ARR (12mo)</span><span style="font-family:monospace;color:#d97706;">$2.1M if 4 deals close</span></div>
</div>""", unsafe_allow_html=True)

# ── Insights View ──────────────────────────────────────────────────────────────
def show_insights():
    is_internal = st.session_state.role == "internal"
    st.markdown('<div style="font-size:28px;font-weight:700;color:#1d1d1f;letter-spacing:-0.8px;margin-bottom:4px;">Intelligence & Insights</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:16px;">Market gaps · signals · strategy</div>', unsafe_allow_html=True)

    stat_row([
        {"label":"Market Coverage","value":"73%","delta":"↑ LATAM payment methods","delta_type":"up","val_color":"#818cf8"},
        {"label":"Gaps Identified","value":"8","delta":"→ 3 in BNPL, 2 in crypto","delta_type":"flat"},
        {"label":"Routing Efficiency","value":"94%","delta":"↑ smart routing gains","delta_type":"up"},
        {"label":"Partner Redundancy","value":"2.1×","delta":"↑ per corridor avg","delta_type":"up"},
        {"label":"Time to Integrate","value":"42d","delta":"↓ 12d vs 2023","delta_type":"down"},
    ])

    tab_options = ["Market Gaps","Partner Signals"] + (["Strategic Recs"] if is_internal else [])
    tab = st.radio("insights_tab", tab_options, horizontal=True, key="insight_tab_radio", label_visibility="collapsed")

    if tab == "Market Gaps":
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;margin-bottom:14px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">🌎 LATAM Coverage Gaps</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">⬛</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">BNPL — No active partner in MX & COL</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Kueski (MX) and Addi (COL) are the dominant players. Neither currently integrated. Estimated $180M TPV opportunity per year if onboarded.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">⬛</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Open Banking / Pix — Single point of failure in BR</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Only OpenPix covers PIX routing. Adding Celcoin as backup would provide redundancy and competitive take rate negotiation.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">⬛</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Crypto payments — zero coverage</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Bitso and MercadoPago crypto rails gaining share in AR and VE. Not yet on roadmap. Consider as Q2 initiative pending regulatory clarity.</div></div>
  </div>
</div>""", unsafe_allow_html=True)
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">⚡ Fraud & Risk Coverage</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">◆</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">SEON live but coverage limited to card fraud</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Merchants requesting ATO and chargeback dispute management. Evaluate Kount or Signifyd as complementary fraud partners.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">◆</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Truora — KYC/KYB coverage for LATAM</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Strong coverage for identity verification in CO, MX, BR. Adds compliance layer that opens regulated merchant segments.</div></div>
  </div>
</div>""", unsafe_allow_html=True)

        with c2:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;margin-bottom:14px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">🏦 BaaS Vertical — New Opportunity</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">★</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Pomelo — White-label orchestration for neobanks</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Pomelo issues cards across LATAM and needs a reliable orchestration layer. Yuno could become embedded infrastructure. Estimated ARR: $440K.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">★</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Bnext / Stori — Card issuers seeking orchestration</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Two card issuers reached out via LinkedIn. Both need multi-acquirer routing for their debit/prepaid portfolios.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">★</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Neobank embedded finance wave</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Nubank, Mercado Pago, and Ualá competing in 3+ countries simultaneously. Winning one creates a network effect across their markets.</div></div>
  </div>
</div>""", unsafe_allow_html=True)
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">📊 Routing Optimization Signals</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">▲</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Getnet outperforming Cielo on BR Visa transactions</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Auth rate delta: +3.1pp. Projected uplift: $4.2M additional authorised TPV per month by shifting routing.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">▲</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">APM share growing 4pp per quarter in Chile & Peru</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Khipu (CL) and Yape (PE) seeing strong adoption. Integrating both adds coverage for ~22M active users in under-served corridors.</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    elif tab == "Partner Signals":
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">🔴 At-Risk Partners</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">⚠</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Nuvei — 4 open SLA incidents</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Auth rate dropped to 84.1% in BR over last 14 days. Merchant escalations received. Schedule urgent technical review with Nuvei engineering.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">⚠</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Conekta MX — stalled commercial negotiations</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Deal stuck at Evaluation for 92 days. Primary contact has gone quiet. Recommend C-level outreach or re-evaluation of strategic fit.</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">🟢 Growth Signals</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
    <span style="font-size:16px;flex-shrink:0;">↑</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Getnet — Rapid TPV ramp post-launch</div><div style="font-size:11px;color:#86868b;line-height:1.55;">+42% TPV growth in first 60 days live. Santander group exploring Getnet rollout in AR and CL — opportunity to extend contract to new markets.</div></div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;">
    <span style="font-size:16px;flex-shrink:0;">↑</span>
    <div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">OpenPix — Pix adoption surging</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Pix now 31% of all BR transactions through Yuno. OpenPix volume up 31% MoM. Strong case for preferential pricing renegotiation at scale.</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    elif tab == "Strategic Recs" and is_internal:
        st.markdown("""
<div style="border:1px solid rgba(245,158,11,.22);background:rgba(245,158,11,.04);border-radius:10px;padding:13px 16px;margin-bottom:16px;">
  <div style="font-size:9.5px;font-weight:700;color:#d97706;letter-spacing:.9px;text-transform:uppercase;margin-bottom:10px;">🔒 Internal — Strategic Recommendations for Q1</div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Priority 1: Close Getnet Santander — activates AR + CL expansion</span><span style="font-family:monospace;color:#d97706;">Jan deadline</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Priority 2: Sign first BaaS partner (Pomelo) — validates new vertical</span><span style="font-family:monospace;color:#d97706;">Q1 OKR</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Priority 3: Add Addi (BNPL COL) to close biggest product gap</span><span style="font-family:monospace;color:#d97706;">Assigned: SR</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;"><span style="color:#6e6e73;">Priority 4: Resolve Nuvei SLA before contract renewal review</span><span style="font-family:monospace;color:#d97706;">Urgent</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;"><span style="color:#6e6e73;">Priority 5: Evaluate Crypto rails for Q2 pipeline readiness</span><span style="font-family:monospace;color:#d97706;">Research phase</span></div>
</div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">🗺 2025 Partner Expansion Map</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);"><span style="font-size:16px;flex-shrink:0;">①</span><div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Deepen LATAM acquirer coverage in CL, PE, AR</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Only 1 active acquirer per country. Target: 2 per market minimum by Q3 2025 to enable true redundancy and competitive routing.</div></div></div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);"><span style="font-size:16px;flex-shrink:0;">②</span><div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Build out BaaS as a formal partner tier</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Create dedicated partner program track — separate commercial terms, embedded orchestration API, dedicated technical success manager.</div></div></div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;"><span style="font-size:16px;flex-shrink:0;">③</span><div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Launch fraud marketplace — 3 partners by EOY</div><div style="font-size:11px;color:#86868b;line-height:1.55;">SEON + Truora + one chargeback specialist would create a credible fraud marketplace offering.</div></div></div>
</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:10px;">💡 Partner Program Recommendations</div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.07);"><span style="font-size:16px;flex-shrink:0;">◈</span><div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Introduce tiered partner program (Silver / Gold / Platinum)</div><div style="font-size:11px;color:#86868b;line-height:1.55;">High-volume partners (Adyen, Getnet) should get dedicated integration support, co-marketing budget, and quarterly business reviews.</div></div></div>
  <div style="display:flex;align-items:flex-start;gap:9px;padding:8px 0;"><span style="font-size:16px;flex-shrink:0;">◈</span><div><div style="font-size:12px;font-weight:600;color:#1d1d1f;margin-bottom:2px;">Partner-sourced deals need clearer attribution model</div><div style="font-size:11px;color:#86868b;line-height:1.55;">Kushki and Adyen have referred 3 merchants each this quarter with no formal incentive structure. Implementing a referral bonus increases deal flow.</div></div></div>
</div>""", unsafe_allow_html=True)

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
  <span style="font-size:28px;font-weight:700;color:#1d1d1f;">Merchants</span>
</div>
<div style="font-size:11px;color:#86868b;margin-bottom:18px;">Your Merchants</div>
""", unsafe_allow_html=True)

    stat_row([
        {"label":"Merchants Live",    "value":"12",     "delta":"Active & connected",    "delta_type":"flat"},
        {"label":"Total TPV",         "value":"$47.24M","delta":"This month · USD",       "delta_type":"up","val_color":"#818cf8"},
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
            marker_color="#6366f1",
            text=[f"${r[3]}M" for r in data], textposition="outside",
            textfont=dict(size=10, color="#6e6e73", family="Menlo"),
        ))
        fig.update_layout(
            title=dict(text="TPV by Merchant", font=dict(size=12, color="#1d1d1f"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=70, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        data = sorted(MERCHANTS, key=lambda x: x[6], reverse=True)
        colors = ["#22c55e" if r[6] >= 92 else "#f59e0b" if r[6] >= 89 else "#ef4444" for r in data]
        fig = go.Figure(go.Bar(
            x=[r[6] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color=colors,
            text=[f"{r[6]}%" for r in data], textposition="outside",
            textfont=dict(size=10, color="#6e6e73", family="Menlo"),
        ))
        fig.update_layout(
            title=dict(text="Approval Rate by Merchant", font=dict(size=12, color="#1d1d1f"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
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
            marker_color="#818cf8",
            text=[f"${r[4]}" for r in data], textposition="outside",
            textfont=dict(size=10, color="#6e6e73", family="Menlo"),
        ))
        fig.update_layout(
            title=dict(text="Average Order Value (AOV)", font=dict(size=12, color="#1d1d1f"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=70, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        data = sorted(MERCHANTS, key=lambda x: x[5], reverse=True)
        fig = go.Figure(go.Bar(
            x=[r[5] for r in data], y=[r[0] for r in data], orientation="h",
            marker_color="#4f46e5",
            text=[f"{r[5]:,}" for r in data], textposition="outside",
            textfont=dict(size=10, color="#6e6e73", family="Menlo"),
        ))
        fig.update_layout(
            title=dict(text="Total Transactions", font=dict(size=12, color="#1d1d1f"), x=0),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=80, t=40, b=10),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Merchant Summary table
    def auth_bar(v):
        color = "#22c55e" if v >= 92 else "#f59e0b" if v >= 89 else "#ef4444"
        pct = int((v - 80) / 20 * 100)
        return f'<div style="display:flex;align-items:center;gap:8px;"><div style="flex:1;background:#f0f0f5;border-radius:2px;height:4px;"><div style="width:{pct}%;height:4px;background:{color};border-radius:2px;"></div></div><span style="font-size:11px;font-family:monospace;color:{color};min-width:38px;">{v}%</span></div>'

    rows_html = ""
    for i, r in enumerate(MERCHANTS):
        border = "" if i == len(MERCHANTS)-1 else "border-bottom:1px solid rgba(0,0,0,0.05);"
        rows_html += f"""
  <div style="display:grid;grid-template-columns:1.5fr 1fr 1fr 0.9fr 0.8fr 1fr 1.6fr;padding:9px 16px;{border}align-items:center;">
    <span style="font-size:12px;font-weight:600;color:#1d1d1f;">{r[0]}</span>
    <span style="font-size:11px;color:#6e6e73;">{r[1]}</span>
    <span style="font-size:11px;color:#6e6e73;">{r[2]}</span>
    <span style="font-size:11px;font-family:monospace;color:#1d1d1f;">${r[3]}M</span>
    <span style="font-size:11px;font-family:monospace;color:#6e6e73;">${r[4]}</span>
    <span style="font-size:11px;font-family:monospace;color:#6e6e73;">{r[5]:,}</span>
    {auth_bar(r[6])}
  </div>"""

    st.markdown(f"""
<div style="font-size:13px;font-weight:700;color:#1d1d1f;margin:20px 0 10px;">Merchant Summary</div>
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;overflow:hidden;">
  <div style="display:grid;grid-template-columns:1.5fr 1fr 1fr 0.9fr 0.8fr 1fr 1.6fr;padding:9px 16px;border-bottom:1px solid rgba(0,0,0,0.07);font-size:9.5px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#86868b;">
    <span>Merchant</span><span>Country</span><span>Region</span><span>TPV (M USD)</span><span>AOV (USD)</span><span>Transactions</span><span>Approval Rate</span>
  </div>
  {rows_html}
</div>
""", unsafe_allow_html=True)

# ── Benchmarks ─────────────────────────────────────────────────────────────────
def show_benchmarks():
    months = ["Aug/24","Sep/24","Oct/24","Nov/24","Dec/24","Jan/25"]

    st.markdown("""
<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:4px;">
  <span style="font-size:28px;font-weight:700;color:#1d1d1f;">Benchmarks</span>
</div>
<div style="font-size:11px;color:#86868b;margin-bottom:18px;">How your integration compares against anonymised peers in the Yuno network</div>
""", unsafe_allow_html=True)

    stat_row([
        {"label":"Your Avg Approval Rate", "value":"90.2%",  "delta":"↑ +1.2pp vs last mo.", "delta_type":"up"},
        {"label":"Network Avg",            "value":"87.6%",  "delta":"→ stable",              "delta_type":"flat"},
        {"label":"Top Performer",          "value":"95.6%",  "delta":"↑ Netflix · Streaming", "delta_type":"up", "val_color":"#22c55e"},
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
        fig.add_trace(go.Bar(name="You (Yuno)", x=months, y=yuno_approval,  marker_color="#6366f1", text=[f"{v}%" for v in yuno_approval],  textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig.add_trace(go.Bar(name="Peer Avg",   x=months, y=peer2_approval, marker_color="#14b8a6", text=[f"{v}%" for v in peer2_approval], textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig.add_trace(go.Bar(name="Top Peer",   x=months, y=peer3_approval, marker_color="#f59e0b", text=[f"{v}%" for v in peer3_approval], textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig.update_layout(
            title=dict(text="Approval Rate Benchmark", font=dict(size=12, color="#1d1d1f"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=10, t=40, b=30),
            legend=dict(orientation="h", y=-0.15, font=dict(size=10,color="#6e6e73"), bgcolor="rgba(0,0,0,0)"),
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
        fig2.add_trace(go.Bar(name="You (Yuno)", x=months, y=yuno_recovery,  marker_color="#6366f1", text=[f"{v}%" for v in yuno_recovery],  textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig2.add_trace(go.Bar(name="Peer Avg",   x=months, y=peer2_recovery, marker_color="#14b8a6", text=[f"{v}%" for v in peer2_recovery], textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig2.add_trace(go.Bar(name="Top Peer",   x=months, y=peer3_recovery, marker_color="#f59e0b", text=[f"{v}%" for v in peer3_recovery], textposition="outside", textfont=dict(size=9, color="#6e6e73")))
        fig2.update_layout(
            title=dict(text="Recovery Rate of Rejected Transactions — Benchmark", font=dict(size=12, color="#1d1d1f"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=10, t=40, b=30),
            legend=dict(orientation="h", y=-0.15, font=dict(size=10,color="#6e6e73"), bgcolor="rgba(0,0,0,0)"),
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
        fig3.add_trace(go.Bar(name="You", x=you_pct,  y=reasons, orientation="h", marker_color="#6366f1"))
        fig3.add_trace(go.Bar(name="Peer Avg", x=peer_pct, y=reasons, orientation="h", marker_color="#14b8a6"))
        fig3.update_layout(
            title=dict(text="Decline Reason Breakdown vs Peers", font=dict(size=12, color="#1d1d1f"), x=0),
            barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#6e6e73", family="Inter"),
            margin=dict(l=10, r=40, t=40, b=10),
            legend=dict(orientation="h", y=1.1, font=dict(size=10,color="#6e6e73"), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)", ticksuffix="%"),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
            height=320,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_r2:
        st.markdown("""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px;height:100%;">
  <div style="font-size:12px;font-weight:700;color:#1d1d1f;margin-bottom:14px;">How You Rank</div>
  <div style="display:flex;flex-direction:column;gap:10px;">
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#6e6e73;">Approval Rate</span><span style="font-size:11px;font-family:monospace;color:#818cf8;">90.2% · <span style="color:#22c55e;">Top 30%</span></span></div>
      <div style="background:#e8e8ed;border-radius:4px;height:6px;"><div style="width:70%;height:6px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#6e6e73;">Recovery Rate</span><span style="font-size:11px;font-family:monospace;color:#818cf8;">4.1% · <span style="color:#22c55e;">Top 25%</span></span></div>
      <div style="background:#e8e8ed;border-radius:4px;height:6px;"><div style="width:75%;height:6px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#6e6e73;">Fraud Rate</span><span style="font-size:11px;font-family:monospace;color:#818cf8;">0.8% · <span style="color:#22c55e;">Top 20%</span></span></div>
      <div style="background:#e8e8ed;border-radius:4px;height:6px;"><div style="width:80%;height:6px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#6e6e73;">Avg Response Time</span><span style="font-size:11px;font-family:monospace;color:#818cf8;">1.2s · <span style="color:#d97706;">Top 50%</span></span></div>
      <div style="background:#e8e8ed;border-radius:4px;height:6px;"><div style="width:50%;height:6px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:4px;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:11px;color:#6e6e73;">Chargeback Rate</span><span style="font-size:11px;font-family:monospace;color:#818cf8;">0.3% · <span style="color:#22c55e;">Top 15%</span></span></div>
      <div style="background:#e8e8ed;border-radius:4px;height:6px;"><div style="width:85%;height:6px;background:linear-gradient(90deg,#4F46E5,#818cf8);border-radius:4px;"></div></div>
    </div>
  </div>
  <div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(0,0,0,0.07);font-size:10px;color:#86868b;">Peers = anonymised merchants in same category & region · Updated monthly</div>
</div>
""", unsafe_allow_html=True)

# ── Home / Welcome Panel ────────────────────────────────────────────────────────
def show_home():
    is_internal = st.session_state.role == "internal"
    if is_internal:
        headline = "Welcome back, A-Team colleague"
        sub = "This is your internal Yuno BD workspace. Everything you need to manage partnerships, track merchant opportunities, and drive revenue — in one place."
        accent = "#4F46E5"
        accent_bg = "rgba(79,70,229,0.08)"
        accent_border = "rgba(79,70,229,0.2)"
        badge = "INTERNAL ACCESS"
        features = [
            ("⟳", "Merchant Pipeline",   "Track all 24 active merchant opportunities across every deal stage — from Prospect to Won. Includes internal notes and revenue intel."),
            ("◈", "Partner Directory",   "Full directory of 47 partners across PSPs, Acquirers, APMs, Fraud & BaaS with live TPV and auth rate data."),
            ("◻", "Merchants",           "Full merchant analytics: TPV, AOV, approval rates and transaction volumes across all 12 live merchants."),
            ("◉", "Key Contacts",        "BD counterparts, technical leads & executive sponsors across partner organizations."),
            ("▲", "Performance",         "Live partner TPV, auth rates, and revenue metrics with full historical trend view and internal targets."),
            ("◎", "Insights",            "Market intelligence, coverage gap analysis, and internal Q1 strategic recommendations — confidential."),
        ]
    else:
        headline = "Welcome, Partner"
        sub = "This is your shared workspace with the Yuno team. Use it to track your joint merchant pipeline, review performance data, and connect with your dedicated Yuno contacts."
        accent = "#4F46E5"
        accent_bg = "rgba(79,70,229,0.08)"
        accent_border = "rgba(79,70,229,0.2)"
        badge = "PARTNER ACCESS"
        features = [
            ("⟳", "Merchant Pipeline",   "See the shared merchant pipeline relevant to your partnership. Track deal stages, ARR estimates, and your involvement in active opportunities."),
            ("◻", "Merchants",           "View performance data for merchants connected through your integration — TPV, AOV, approval rates and total transactions."),
            ("◉", "Your Yuno Team",      "Meet your dedicated Yuno contacts: Partnership Managers, Delivery Manager, Marketing Support, and Customer Success."),
            ("▲", "Performance",         "Monitor live TPV, authorization rates and transaction volumes for your integration with Yuno."),
            ("◎", "Insights",            "Market coverage analysis, payment trends, and strategic context for LATAM — curated for your region and category."),
        ]

    feature_html = "".join(f"""
<div style="background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 0 0 1px rgba(0,0,0,0.04);border:none;border-radius:10px;padding:16px 18px;display:flex;gap:14px;align-items:flex-start;">
  <div style="font-size:18px;flex-shrink:0;margin-top:1px;">{icon}</div>
  <div>
    <div style="font-size:12px;font-weight:700;color:#1d1d1f;margin-bottom:4px;">{title}</div>
    <div style="font-size:11px;color:#86868b;line-height:1.6;">{desc}</div>
  </div>
</div>""" for icon, title, desc in features)

    st.markdown(f"""
<div style="padding:32px 8px 0;">
  <div style="font-size:9px;font-weight:700;letter-spacing:1.2px;background:{accent_bg};color:{accent};border:1px solid {accent_border};padding:3px 12px;border-radius:20px;display:inline-block;font-family:monospace;margin-bottom:16px;">{badge}</div>
  <div style="font-size:26px;font-weight:700;color:#1d1d1f;letter-spacing:-0.7px;line-height:1.25;margin-bottom:10px;">{headline}</div>
  <p style="font-size:12.5px;color:#6e6e73;line-height:1.75;max-width:620px;margin-bottom:28px;">{sub}</p>
  <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#86868b;margin-bottom:12px;">What you can do here</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
    {feature_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main App ───────────────────────────────────────────────────────────────────
inject_css(st.session_state.role)

if st.session_state.role is None:
    show_landing()
else:
    show_sidebar()
    # Top-right "Landing Page" button
    _top_left, _top_right = st.columns([9, 1])
    with _top_right:
        if st.button("← Landing", key="goto_landing", use_container_width=True):
            st.session_state.role = None
            st.session_state.page = "Home"
            st.query_params.clear()
            st.rerun()
    page = st.session_state.page
    if page == "Home":
        show_home()
    elif page == "Pipeline":
        show_pipeline()
    elif page == "Partners":
        show_partners()
    elif page == "Merchants":
        show_merchants()
    elif page == "Contacts":
        show_contacts()
    elif page == "Performance":
        show_performance()
    elif page == "Benchmarks":
        show_benchmarks()
    elif page == "Insights":
        show_insights()
