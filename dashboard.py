import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
from data_fetch import get_stock_data
from monte_carlo import run_simulation
from risk_metrics import calculate_metrics
from valuation_engine import run_valuation
from financial_data import FUNDAMENTAL_DATA
from cross_verify import cross_verify_and_correct
from data_audit import run_data_audit

st.set_page_config(
    page_title="Equity Lab — Arpit Sharma | IPM 2",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
#  CSS — Sandstone & Clay (Organic Premium) Theme
# ═══════════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family:'Inter',sans-serif!important; background-color: #F4F1EE !important; color: #2D2926 !important; }
code, pre { font-family:'JetBrains Mono',monospace!important; }

@keyframes fadeInUp {from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideInLeft {from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:translateX(0)}}
@keyframes pulseRing {0%,100%{box-shadow:0 0 0 0 rgba(140, 120, 81, 0.2)}60%{box-shadow:0 0 0 12px rgba(140, 120, 81, 0)}}

.block-container { padding: 1.2rem 2rem 2rem; max-width: 1440px; }

/* Cards (Soft Stone) */
.card { background: #EBE7E2; border: 1px solid #D6CFC7; border-radius: 14px; padding: 20px 24px; margin: 10px 0;
  box-shadow: 0 1px 3px rgba(0,0,0,.04); transition: all .2s; animation: fadeInUp .4s ease both; }
.card:hover { border-color: #8C7851; box-shadow: 0 4px 18px rgba(140, 120, 81, .15); }
.card-bronze { border-left: 4px solid #8C7851; }
.card-plum { border-left: 4px solid #7A656D; }
.card-sage { border-left: 4px solid #5F7161; }
.card-terra { border-left: 4px solid #A76D60; }

/* Step badges */
.sb { display: inline-flex; align-items: center; padding: 5px 15px; border-radius: 20px; font-weight: 700;
  font-size: .8rem; letter-spacing: .5px; animation: slideInLeft .35s ease both; }
.sb-bronze { background: #8C7851; color: #F4F1EE; }
.sb-terra { background: #A76D60; color: #F4F1EE; }
.sb-plum { background: #7A656D; color: #F4F1EE; }
.sb-sage { background: #5F7161; color: #F4F1EE; }

/* KPI tiles */
.kpi { background: #EBE7E2; border: 1px solid #D6CFC7; border-radius: 12px; padding: 14px 18px;
  text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.03); transition: all .2s; }
.kpi:hover { border-color: #8C7851; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(140, 120, 81, .15); }
.kpi-label { color: #6B6661; font-size: .78rem; font-weight: 600; letter-spacing: .5px; margin: 0; }
.kpi-value { color: #2D2926; font-size: 1.45rem; font-weight: 800; margin: 4px 0 0; }
.kpi-sub { color: #8E8982; font-size: .75rem; margin: 2px 0 0; }

/* Signal banners */
.signal { border-radius: 14px; padding: 24px 20px; text-align: center; margin: 14px 0;
  border: 2px solid; animation: fadeInUp .45s ease both; }
.signal h1 { margin: 0; font-weight: 800; letter-spacing: .5px; }
.signal p { margin: 8px 0 0; font-size: 1rem; opacity: .85; }

/* Intrinsic value hero */
.iv-hero { border: 2px solid #8C7851; border-radius: 16px; padding: 28px; text-align: center;
  background: #EBE7E2; animation: pulseRing 3s ease infinite; }

/* Rationale / rejected blocks */
.rat { background: #EBE7E2; border-left: 3px solid #8C7851; border-radius: 0 8px 8px 0;
  padding: 12px 16px; margin: 8px 0; font-size: .89rem; color: #2D2926; line-height: 1.65; }
.rej { background: #E4D4D3; border-left: 3px solid #9D5C58; border-radius: 0 8px 8px 0;
  padding: 10px 14px; margin: 5px 0; font-size: .87rem; color: #5C3A38; }
.arow { display: flex; justify-content: space-between; padding: 7px 12px; border-radius: 7px;
  margin: 3px 0; font-size: .87rem; background: #EBE7E2; border: 1px solid #D6CFC7; color: #2D2926; }
.arow:hover { background: #D6CFC7; }

/* Live badge */
.lb { background: #8C7851; color: #F4F1EE; padding: 3px 10px; border-radius: 20px;
  font-size: .7rem; font-weight: 700; letter-spacing: .5px; margin-left: 8px; vertical-align: middle; }

/* Sensitivity table cells */
.sens-hot { background: #E4D4D3; color: #5C3A38; font-weight: 700; border-radius: 4px; padding: 4px 8px; }
.sens-mid { background: #E9DFCE; color: #543C16; font-weight: 600; border-radius: 4px; padding: 4px 8px; }
.sens-cold { background: #D2D6D0; color: #2B3A30; font-weight: 700; border-radius: 4px; padding: 4px 8px; }

/* Audit Flags */
.af-r { background: #E4D4D3; border-left: 3px solid #9D5C58; padding: 8px 12px; border-radius: 0 7px 7px 0; margin: 3px 0; color: #5C3A38; font-size: .87rem; }
.af-y { background: #E9DFCE; border-left: 3px solid #B58A54; padding: 8px 12px; border-radius: 0 7px 7px 0; margin: 3px 0; color: #543C16; font-size: .87rem; }
.af-g { background: #D2D6D0; border-left: 3px solid #5F7161; padding: 8px 12px; border-radius: 0 7px 7px 0; margin: 3px 0; color: #2B3A30; font-size: .87rem; }

/* Table styling */
div[data-testid="stTable"] table { background: #EBE7E2; border-radius: 10px; border: 1px solid #D6CFC7; }
div[data-testid="stTable"] th { background: #D6CFC7!important; color: #2D2926!important; font-weight: 700; border-bottom: 2px solid #8C7851!important; }
div[data-testid="stTable"] td { color: #2D2926!important; border-bottom: 1px solid #D6CFC7!important; }

div[data-testid="stMetric"] { background: #EBE7E2; border: 1px solid #D6CFC7; border-radius: 10px;
  padding: 10px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
div[data-testid="stMetric"] label { color: #6B6661!important; font-weight: 600; }
div[data-testid="stMetricValue"] { color: #2D2926!important; }

hr { border-color: #D6CFC7!important; margin: 20px 0!important; }
.stDeployButton { display: none!important; }
.stSpinner > div { border-top-color: #8C7851!important; }
details summary { color: #8C7851!important; font-weight: 600!important; }

/* Fix Streamlit's default background injections */
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #F4F1EE !important; }
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
#  DATA & HELPERS
# ═══════════════════════════════════════════════════════════════════
STOCK_INFO = {
    "TATAMOTORS.NS":("Tata Motors","Rithin Reji"),"M&M.NS":("Mahindra & Mahindra","Vinamra Gupta"),
    "OLECTRA.NS":("Olectra Greentech","Aryan Jha"),"ATHERENERG.NS":("Ather Energy",""),
    "TSLA":("Tesla Inc.",""),"P911.DE":("Porsche AG","Gautam Poturaju"),
    "F":("Ford Motor Co.","Archana V"),"VOW3.DE":("Volkswagen AG","Sunidhi Datar"),
    "HYMTF":("Hyundai Motor","Samarth Rao"),"APOLLOTYRE.NS":("Apollo Tyres","Anirudh Agarwal"),
    "MRF.NS":("MRF Ltd.","Shrisai Hari"),"JKTYRE.NS":("JK Tyre & Industries","Swayam Panigrahi"),
    "CEATLTD.NS":("CEAT Ltd.","Harshini Venkat"),"SBIN.NS":("State Bank of India","Anoushka Gadhwal"),
    "HDFCBANK.NS":("HDFC Bank","Ryan Kidangan"),"ICICIBANK.NS":("ICICI Bank","Himangshi Bose"),
    "AXISBANK.NS":("Axis Bank","Bismaya Nayak"),"LAURUSLABS.NS":("Laurus Labs","Satvik Sharma"),
    "AUROPHARMA.NS":("Aurobindo Pharma","Arya Mukharjee"),"SUNPHARMA.NS":("Sun Pharma","Yogesh Bolkotagi"),
    "DIVISLAB.NS":("Divi's Laboratories","Bhavansh Madan"),"ITC.NS":("ITC Ltd.","Gajanan Kudva / Srutayus Das"),
    "CHALET.NS":("Chalet Hotels","Shreya Joshi"),"MHRIL.NS":("Mahindra Holidays","Gowri Shetty"),
    "INDHOTEL.NS":("Indian Hotels Co.","Aarohi Jain"),"HUL.NS":("Hindustan Unilever","Suhina Sarkar"),
    "NESTLEIND.NS":("Nestlé India","Saaraansh Razdan"),"SHREECEM.NS":("Shree Cement","Anjor Singh"),
    "ULTRACEMCO.NS":("UltraTech Cement","Rahul Gowda"),"DALBHARAT.NS":("Dalmia Bharat","Kushagra Shukla"),
    "RAMCOCEM.NS":("Ramco Cements","Grace Rebecca David"),"ABSLAMC.NS":("Aditya Birla Sun Life AMC","Pallewar Pranav"),
    "HDFCAMC.NS":("HDFC AMC","Rittika Saraswat"),"NAM-INDIA.NS":("Nippon Life India AMC","Sam Phillips"),
    "UTIAMC.NS":("UTI AMC","Abhinav Singh"),"NVDA":("NVIDIA Corp.","Sijal Verma"),
    "MSFT":("Microsoft Corp.","Gurleen Kaur"),"GOOGL":("Alphabet Inc.","Anugraha AB"),
    "META":("Meta Platforms","Senjuti Pal"),"IBM":("IBM Corp.","Biba Pattnaik"),
    "ASML":("ASML Holding","Adaa Gujral"),"INTC":("Intel Corp.","Aditi Ranjan"),
    "QCOM":("Qualcomm Inc.","Arpit Sharma"),"CRM":("Salesforce Inc.","Rishit Hotchandani"),
    "PLTR":("Palantir Technologies","Krrish Bahuguna"),"CRWD":("CrowdStrike Holdings","Ashi Beniwal"),
    "WBD":("Warner Bros. Discovery","Dhairya Vanker"),"NFLX":("Netflix Inc.","Hiya Phatnani"),
    "DIS":("Walt Disney Co.","Siya Sharma"),"PARA":("Paramount Global","Tanvi Gujarathi"),
    "PG":("Procter & Gamble","Nayan Kanchan"),"WMT":("Walmart Inc.",""),
    "LMT":("Lockheed Martin","Siddhant Mehta"),"GD":("General Dynamics","Shlok Pratap Singh"),
    "NOC":("Northrop Grumman","Harshdeep Roshan"),"RTX":("RTX Corporation","Prandeep Poddar"),
}

def _is_indian(t): return t.endswith(".NS") or t.endswith(".BO")
def _cur(t): return "₹" if _is_indian(t) else "$"
def _fmt(v,t): return f"{_cur(t)}{v:,.2f}"
def _pct(v): return f"{v:+.1%}"

GLOBAL_STOCKS = {
    "🚗 Auto (India)":["TATAMOTORS.NS","M&M.NS","OLECTRA.NS","ATHERENERG.NS"],
    "🌍 Auto (Global)":["TSLA","P911.DE","F","VOW3.DE","HYMTF"],
    "🛞 Tyres (India)":["APOLLOTYRE.NS","MRF.NS","JKTYRE.NS","CEATLTD.NS"],
    "🏦 Banking (India)":["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS"],
    "💊 Pharma (India)":["LAURUSLABS.NS","AUROPHARMA.NS","SUNPHARMA.NS","DIVISLAB.NS"],
    "🏨 Consumer & Hotels (India)":["ITC.NS","CHALET.NS","MHRIL.NS","INDHOTEL.NS","HUL.NS","NESTLEIND.NS"],
    "🧱 Cement (India)":["SHREECEM.NS","ULTRACEMCO.NS","DALBHARAT.NS","RAMCOCEM.NS"],
    "📈 AMC / Finance (India)":["ABSLAMC.NS","HDFCAMC.NS","NAM-INDIA.NS","UTIAMC.NS"],
    "💻 Tech (US/Global)":["NVDA","MSFT","GOOGL","META","IBM","ASML","INTC","QCOM","CRM","PLTR","CRWD"],
    "🎬 Media & Consumer (US)":["WBD","NFLX","DIS","PARA","PG","WMT"],
    "🛡️ Defense (US)":["LMT","GD","NOC","RTX"],
}

SECTOR_CLEAN = {}; TICKER_TO_SECTOR = {}
for sec,tickers in GLOBAL_STOCKS.items():
    clean=sec.split(" ",1)[1] if " " in sec else sec
    SECTOR_CLEAN[sec]=clean
    for t in tickers: TICKER_TO_SECTOR[t]=clean

def _dn(t):
    i=STOCK_INFO.get(t)
    if i: c,p=i; return f"{c} ({p})" if p else c
    return t

# Plotly Organic Premium Theme configuration
PL = dict(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#EBE7E2",
          font=dict(family="Inter,sans-serif", color="#2D2926"), margin=dict(l=40, r=40, t=50, b=40),
          legend=dict(bgcolor="rgba(235, 231, 226, .85)", bordercolor="#D6CFC7"))

# ═══════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center;padding:8px 0 4px;animation:fadeInUp .5s ease both;">
  <h1 style="font-size:2.4rem;font-weight:900;margin:0;color:#2D2926;">
     🏛️ Institutional Equity Lab</h1>
  <p style="color:#8C7851;font-size:1rem;margin:5px 0 0;font-weight:500;letter-spacing:.5px;">
     Damodaran DCF &nbsp;·&nbsp; Monte Carlo &nbsp;·&nbsp; Capital Structure &nbsp;·&nbsp; Multi-Source Audit</p>
  <p style="color:#6B6661;font-size:.82rem;margin:3px 0 0;">Built by <b style="color:#2D2926;">Arpit Sharma</b> &nbsp;|&nbsp; IPM 2</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════
st.sidebar.markdown("""<div style="text-align:center;padding:8px 0 16px;">
  <p style="font-size:1.2rem;font-weight:800;margin:0;color:#2D2926;">EQUITY LAB</p>
  <p style="color:#6B6661;font-size:.72rem;margin:2px 0 0;">Arpit Sharma · IPM 2</p>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("### 🎯 Company")
category=st.sidebar.selectbox("Sector",list(GLOBAL_STOCKS.keys()),label_visibility="collapsed")
tlist=GLOBAL_STOCKS[category]; dlist=[_dn(t) for t in tlist]
sel_d=st.sidebar.selectbox("Company",dlist); sel_t=tlist[dlist.index(sel_d)]
custom=st.sidebar.text_input("Custom Ticker","",placeholder="e.g. RELIANCE.NS / AAPL / AMZN")
ticker=custom.strip().upper() if custom.strip() else sel_t
cur=_cur(ticker)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Monte Carlo")
sims=st.sidebar.slider("Simulations",5000,50000,10000,step=1000)
years=st.sidebar.slider("Horizon (Years)",.5,10.,1.,step=.5)
crash=st.sidebar.slider("Market Stress %",0,50,0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏗️ Capital Structure Tool")
st.sidebar.caption("Override assumptions in Tab 5 →")
cs_debt_ratio=st.sidebar.slider("Debt Ratio %",0,80,30,step=5)/100
cs_kd=st.sidebar.slider("Cost of Debt (Kd) %",2,18,6,step=1)/100
cs_tax=st.sidebar.slider("Tax Rate %",10,40,25,step=1)/100
cs_rf=st.sidebar.slider("Risk-Free Rate %",1,12,4,step=1)/100
cs_erp=st.sidebar.slider("Equity Risk Premium %",3,12,5,step=1)/100

# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
try:
  info_t=STOCK_INFO.get(ticker,(ticker,""))
  co_name,person=info_t
  is_live_fetch=ticker not in FUNDAMENTAL_DATA
  live_badge='<span class="lb">⚡ LIVE DATA</span>' if is_live_fetch else ""
  person_html=(f'<span style="background:#EBE7E2;color:#8C7851;padding:3px 10px;border-radius:20px;'
               f'font-size:.82rem;font-weight:500;margin-left:8px;border:1px solid #D6CFC7;">👤 {person}</span>') if person else ""

  st.markdown(f"""
  <div class="card card-bronze" style="padding:18px 24px;">
    <h2 style="margin:0;font-size:1.7rem;color:#2D2926;">{co_name}
      <code style="background:#D6CFC7;color:#2D2926;padding:3px 9px;border-radius:7px;
        font-size:.88rem;margin-left:7px;border:1px solid #8C7851;">{ticker}</code>
      {person_html}{live_badge}</h2>
  </div>""", unsafe_allow_html=True)

  # ── FETCH CORE DATA ───────────────────────────────────────────
  val=None; intrinsic=0; fd=None; our_signal="N/A"; mc_sel=None
  has_dcf=False

  with st.spinner("Running Damodaran DCF…"):
    try:
      val=run_valuation(ticker); has_dcf=True
      mc_sel=val["model_selection"]; vd=val["valuation_detail"]
      fd=val["fundamentals"]; comp=val["computed"]
      intrinsic=val["intrinsic_value_per_share"]; unit=fd["unit"]
    except Exception as e:
      st.warning(f"DCF unavailable: {e}")

  with st.spinner("Fetching price data…"):
    s0,auto_mu,auto_sigma,src_name=get_stock_data(ticker)
  st.sidebar.success(f"✅ {src_name}")

  adj_mu=auto_mu-(crash/100)
  with st.spinner("Monte Carlo…"):
    paths,low_band,high_band=run_simulation(s0,adj_mu,auto_sigma,years,n_sims=sims)
  final_prices=paths[-1]
  metrics=calculate_metrics(final_prices,s0,adj_mu,auto_sigma)

  # Signal mapped to Earthy Theme
  if has_dcf and intrinsic>0:
    mos=(intrinsic-s0)/s0
    if mos>.20: sig_bg,sig_bdr,sig_txt,vt="#D2D6D0","#5F7161","#2B3A30","🟢 UNDERVALUED — BUY"
    elif mos>-.10: sig_bg,sig_bdr,sig_txt,vt="#E9DFCE","#B58A54","#543C16","🟡 FAIRLY VALUED — HOLD"
    else: sig_bg,sig_bdr,sig_txt,vt="#E4D4D3","#9D5C58","#4A2624","🔴 OVERVALUED — AVOID"
    our_signal=vt
    sub_txt=f"Market {_fmt(s0,ticker)} · DCF {_fmt(intrinsic,ticker)} · Margin {_pct(mos)} · MC {_fmt(metrics['Expected Price'],ticker)}"
  else:
    our_signal=metrics["Signal"]
    if "BUY" in our_signal: sig_bg,sig_bdr,sig_txt="#D2D6D0","#5F7161","#2B3A30"
    elif "HOLD" in our_signal: sig_bg,sig_bdr,sig_txt="#E9DFCE","#B58A54","#543C16"
    else: sig_bg,sig_bdr,sig_txt="#E4D4D3","#9D5C58","#4A2624"
    vt=our_signal; sub_txt=f"MC {years}yr Target: {_fmt(metrics['Expected Price'],ticker)}"

  # ── TOP SIGNAL BANNER ─────────────────────────────────────────
  st.markdown(f"""<div class="signal" style="background:{sig_bg};border-color:{sig_bdr};">
    <h1 style="color:{sig_txt};font-size:1.9rem;">{vt}</h1>
    <p style="color:{sig_txt};">{sub_txt}</p>
  </div>""", unsafe_allow_html=True)

  # ── TOP KPI ROW ───────────────────────────────────────────────
  k1,k2,k3,k4,k5,k6=st.columns(6)
  def kpi_html(label,value,sub="",color="#2D2926"):
    return f'<div class="kpi"><p class="kpi-label">{label}</p><p class="kpi-value" style="color:{color};">{value}</p><p class="kpi-sub">{sub}</p></div>'

  with k1: st.markdown(kpi_html("Market Price",_fmt(s0,ticker),"Live"), unsafe_allow_html=True)
  with k2:
    iv_color="#5F7161" if has_dcf and intrinsic>s0 else "#9D5C58" if has_dcf else "#6B6661"
    st.markdown(kpi_html("DCF Intrinsic",_fmt(intrinsic,ticker) if has_dcf else "N/A",
      f"{_pct((intrinsic/s0)-1)} vs mkt" if has_dcf and s0>0 else "",iv_color), unsafe_allow_html=True)
  with k3: st.markdown(kpi_html("VaR 95%",f"{metrics['VaR 95% (Rel)']:.1%}","Downside risk","#9D5C58"), unsafe_allow_html=True)
  with k4: st.markdown(kpi_html("Prob Profit",f"{metrics['Prob. of Profit']:.0f}%","MC estimate","#8C7851"), unsafe_allow_html=True)
  with k5: st.markdown(kpi_html("Sharpe",f"{metrics['Sharpe Ratio']:.2f}","Risk-adjusted"), unsafe_allow_html=True)
  with k6:
    yf_info={}
    try: yf_info=yf.Ticker(ticker).info
    except: pass
    pe=yf_info.get("trailingPE","—"); pe_str=f"{pe:.1f}x" if isinstance(pe,(int,float)) else "—"
    st.markdown(kpi_html("P/E Ratio",pe_str,"Trailing"), unsafe_allow_html=True)

  st.markdown("")

  # ═══════════════════════════════════════════════════════════════
  #  TABS
  # ═══════════════════════════════════════════════════════════════
  tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "📐 DCF Valuation",
    "📊 Financial Analysis",
    "🎲 Monte Carlo",
    "✅ Cross-Verification",
    "🏗️ Capital Structure",
    "🔍 Data Audit",
  ])

  skip_cols=("Year","Phase","Growth","Growth Rate","Expected Growth","Cost of Equity","WACC")

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 1 — DCF VALUATION                                       ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab1:
    if not has_dcf:
      st.error("❌ DCF could not run. Check ticker validity or yfinance availability.")
    else:
      # STEP 1
      st.markdown('<div style="display:flex;align-items:center;gap:10px;margin:20px 0 8px;"><span class="sb sb-bronze">STEP 1</span><span style="font-size:1.2rem;font-weight:700;">Choosing the Right Model</span></div>', unsafe_allow_html=True)
      st.caption("Replicates Damodaran's `model1.xls` decision tree — answered with live company data")

      with st.expander("📝 Q&A Model Inputs", expanded=True):
        cs=""
        for item in mc_sel.get("qa_inputs",[]):
          s=item.get("section","")
          if s and s!=cs:
            st.markdown(f"<p style='color:#8C7851;font-weight:700;margin:14px 0 5px;'>━━ {s} ━━</p>", unsafe_allow_html=True)
            cs=s
          if "formula" in item:
            st.markdown(f"**{item['question']}**"); st.code(item["formula"],language="text")
            st.markdown(f"<p style='color:#8C7851;font-weight:600;'>= {item['answer']}</p>", unsafe_allow_html=True)
          else:
            st.markdown(f"<p style='margin:3px 0;'><span style='color:#6B6661;'>{item['question']}</span> → <code style='color:#2D2926;background:#D6CFC7;padding:2px 6px;border-radius:4px;'>{item['answer']}</code></p>", unsafe_allow_html=True)
          if "note" in item: st.caption(f"ℹ️ {item['note']}")

      with st.expander("🧠 Decision Trail", expanded=True):
        for i,step in enumerate(mc_sel.get("decision_trail",[]),1):
          st.markdown(f"<p style='margin:5px 0;'><span style='color:#8C7851;font-weight:700;'>{i}.</span> <span style='color:#2D2926;'>{step}</span></p>", unsafe_allow_html=True)

      if mc_sel.get("detailed_rationale"):
        with st.expander("📚 Detailed Academic Rationale", expanded=True):
          for p in mc_sel["detailed_rationale"]:
            st.markdown(f'<div class="rat">{p}</div>', unsafe_allow_html=True)

      if mc_sel.get("rejected_alternatives"):
        with st.expander("🚫 Why Other Models Were Rejected"):
          for r in mc_sel["rejected_alternatives"]:
            st.markdown(f'<div class="rej">❌ {r}</div>', unsafe_allow_html=True)

      if mc_sel.get("key_assumptions"):
        with st.expander("📐 Key Assumptions"):
          ka = mc_sel["key_assumptions"]
          if isinstance(ka, dict):
            cols_ka=st.columns(2)
            for i,(k,v) in enumerate(ka.items()):
              with cols_ka[i%2]:
                st.markdown(f'<div class="arow"><span style="color:#6B6661;font-weight:500;">{k}</span><span style="color:#2D2926;font-weight:700;">{v}</span></div>', unsafe_allow_html=True)
          else:
            for item in ka:
              st.markdown(f'<div class="rat">📌 {item}</div>', unsafe_allow_html=True)

      st.markdown(f"""<div class="card" style="border-color:#8C7851;background:#EBE7E2;margin-top:10px;">
        <p style="color:#8C7851;font-weight:700;font-size:.88rem;margin:0 0 10px;letter-spacing:1px;">📐 MODEL SELECTOR OUTPUT</p>
        <table style="width:100%;font-size:.93rem; border: none;">
          <tr><td style="color:#6B6661;padding:6px 0;width:40%;">Type</td><td style="font-weight:600;color:#2D2926;">{mc_sel['model_type']}</td></tr>
          <tr><td style="color:#6B6661;padding:6px 0;">Earnings</td><td style="font-weight:600;color:#2D2926;">{mc_sel['earnings_level']}</td></tr>
          <tr><td style="color:#6B6661;padding:6px 0;">Cashflows</td><td style="font-weight:600;color:#2D2926;">{mc_sel['cashflow_type']}</td></tr>
          <tr><td style="color:#6B6661;padding:6px 0;">Growth</td><td style="font-weight:600;color:#2D2926;">{mc_sel['growth_pattern']}</td></tr>
          <tr style="background:#D6CFC7;">
            <td style="color:#2D2926;font-weight:700;padding:8px 6px;">✅ Selected</td>
            <td style="color:#8C7851;font-weight:800;font-size:1rem;padding:8px 6px;">{mc_sel['model_description']}
              <code style="font-size:.75rem;background:#EBE7E2;padding:2px 6px;border-radius:4px;margin-left:6px;color:#2D2926;">{mc_sel['model_code']}.xls</code>
            </td></tr>
        </table>
      </div>""", unsafe_allow_html=True)
      st.markdown("---")

      # STEP 2
      st.markdown('<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;"><span class="sb sb-bronze">STEP 2</span><span style="font-size:1.2rem;font-weight:700;">Annual Report Data</span></div>', unsafe_allow_html=True)
      c1,c2,c3=st.columns(3)
      with c1:
        st.markdown('<div class="card card-bronze"><p style="color:#8C7851;font-weight:700;font-size:.85rem;margin-bottom:8px;">📄 INCOME STATEMENT</p>', unsafe_allow_html=True)
        for l,k in [("Revenue","revenue"),("EBIT","ebit"),("Net Income","net_income")]:
          st.write(f"{l}: **{cur}{fd[k]:,.0f} {unit}**")
        st.write(f"EPS: **{cur}{comp['EPS']:,.2f}**"); st.write(f"Tax Rate: **{fd['tax_rate']:.0%}**")
        st.markdown("</div>", unsafe_allow_html=True)
      with c2:
        st.markdown('<div class="card card-plum"><p style="color:#7A656D;font-weight:700;font-size:.85rem;margin-bottom:8px;">💰 CASH FLOW</p>', unsafe_allow_html=True)
        for l,k in [("Depreciation","depreciation"),("CapEx","capex"),("ΔWC","delta_wc"),("Dividends","dividends_total")]:
          st.write(f"{l}: **{cur}{fd[k]:,.0f} {unit}**")
        st.markdown(f"<p style='color:#7A656D;font-weight:700;'>FCFE: {cur}{comp['FCFE_total']:,.0f} | FCFF: {cur}{comp['FCFF_total']:,.0f} {unit}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
      with c3:
        st.markdown('<div class="card card-sage"><p style="color:#5F7161;font-weight:700;font-size:.85rem;margin-bottom:8px;">🏗️ BALANCE SHEET & RATES</p>', unsafe_allow_html=True)
        st.write(f"Debt: **{cur}{fd['total_debt']:,.0f}** | Cash: **{cur}{fd['cash']:,.0f} {unit}**")
        st.write(f"D/E: **{fd['debt_ratio']:.1%}** | Beta: **{fd['beta']:.2f}**")
        st.write(f"Ke: **{fd['cost_of_equity']:.1%}** | WACC: **{fd['wacc']:.1%}**")
        st.write(f"Rf: **{fd['risk_free_rate']:.1%}** | ERP: **{fd['erp']:.1%}**")
        st.markdown("</div>", unsafe_allow_html=True)
      st.markdown("---")

      # STEP 3
      st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;"><span class="sb sb-bronze">STEP 3</span><span style="font-size:1.2rem;font-weight:700;">{vd.get("model","DCF")} — Year-by-Year</span></div>', unsafe_allow_html=True)
      if "year_by_year" in vd and vd["year_by_year"]:
        df_yby=pd.DataFrame(vd["year_by_year"])
        for col in df_yby.columns:
          if col in skip_cols: continue
          if df_yby[col].dtype in [np.float64,np.int64,float,int]:
            df_yby[col]=df_yby[col].apply(lambda x: f"{cur}{x:,.2f}" if abs(x)>=1 else f"{x:.6f}")
        st.dataframe(df_yby,use_container_width=True,hide_index=True)
      if "formula" in vd: st.code(vd["formula"],language="text")
      if "summary" in vd:
        with st.expander("📊 Valuation Summary"):
          rows=[{"Item":k,"Value":f"{v:.2%}" if isinstance(v,float) and abs(v)<1 and v!=0 else f"{cur}{v:,.2f}" if isinstance(v,float) else str(v)} for k,v in vd["summary"].items()]
          st.table(pd.DataFrame(rows))

      if intrinsic>0:
        st.markdown(f'<div class="iv-hero"><p style="color:#6B6661;font-size:.85rem;margin:0;font-weight:500;letter-spacing:1px;">INTRINSIC VALUE PER SHARE</p><h1 style="margin:8px 0;font-size:2.6rem;font-weight:900;color:#2D2926;">{_fmt(intrinsic,ticker)}</h1><p style="color:#6B6661;margin:0;font-size:.83rem;">Model: {mc_sel["model_description"]} · <code style="background:#D6CFC7;color:#2D2926;padding:1px 5px;border-radius:3px;">{mc_sel["model_code"]}.xls</code></p></div>', unsafe_allow_html=True)
      else:
        st.warning("⚠️ Intrinsic value ≤ 0 — check input assumptions.")

      st.markdown("---")

      # STEP 4 — DCF SENSITIVITY HEATMAP
      st.markdown('<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;"><span class="sb sb-terra">STEP 4</span><span style="font-size:1.2rem;font-weight:700;">DCF Sensitivity — WACC × Terminal Growth</span></div>', unsafe_allow_html=True)
      st.caption("How intrinsic value changes as WACC and terminal growth rate vary. Your base case is highlighted.")

      base_wacc=fd.get("wacc",0.10); base_sg=fd.get("stable_growth",0.03)
      wacc_range=[round(base_wacc+d,3) for d in [-0.04,-0.03,-0.02,-0.01,0,0.01,0.02,0.03,0.04]]
      sg_range  =[round(base_sg+d,3)  for d in [-0.02,-0.01,0,0.01,0.02]]

      from valuation_models import (fcff_stable,fcff_two_stage,fcff_three_stage,
                                     fcfe_stable,fcfe_two_stage,fcfe_three_stage,
                                     ddm_stable,ddm_two_stage,ddm_three_stage,compute_fcfe,compute_fcff)
      code_s=mc_sel["model_code"]

      def _sens_val(w,g):
        try:
          shares_s=fd["shares_outstanding"]; hg=fd["firm_growth_rate"]
          fcff_t=compute_fcff(fd["ebit"],fd["tax_rate"],fd["depreciation"],fd["capex"],fd["delta_wc"])
          fcfe_t=compute_fcfe(fd["net_income"],fd["depreciation"],fd["capex"],fd["delta_wc"],fd["debt_ratio"])
          fcfe_ps=fcfe_t/shares_s if shares_s>0 else 0
          dps=fd["dividends_total"]/shares_s if shares_s>0 else 0; ke=fd["cost_of_equity"]
          if code_s=="fcffst": r=fcff_stable(fcff_t,w,g,fd["total_debt"],fd["cash"],shares_s)
          elif code_s=="fcff2st": r=fcff_two_stage(fcff_t,w,w*.95,hg,g,7,fd["total_debt"],fd["cash"],shares_s)
          elif code_s=="fcff3st": r=fcff_three_stage(fcff_t,w,w*.95,hg,g,5,5,fd["total_debt"],fd["cash"],shares_s)
          elif code_s=="fcfest": r=fcfe_stable(fcfe_ps,ke,g)
          elif code_s=="fcfe2st": r=fcfe_two_stage(fcfe_ps,ke,hg,g,7)
          elif code_s=="fcfe3st": r=fcfe_three_stage(fcfe_ps,ke,hg,g,5,5)
          elif code_s=="ddmst": r=ddm_stable(dps,ke,g)
          elif code_s=="ddm2st": r=ddm_two_stage(dps,ke,hg,g,7)
          elif code_s=="ddm3st": r=ddm_three_stage(dps,ke,hg,g,5,5)
          else: r=fcff_two_stage(fcff_t,w,w*.95,hg,g,7,fd["total_debt"],fd["cash"],shares_s)
          iv=r.get("intrinsic_value_per_share",r.get("intrinsic_value",0))
          return max(0,iv)
        except: return 0

      sens_data={}
      for w in wacc_range:
        row={}
        for g in sg_range:
          row[f"g={g:.1%}"]=_sens_val(w,g)
        sens_data[f"WACC={w:.1%}"]=row
      df_sens=pd.DataFrame(sens_data).T

      # Color the heatmap (Organic tones)
      z_vals=df_sens.values.tolist()
      fig_sens=go.Figure(data=go.Heatmap(
        z=df_sens.values, x=df_sens.columns.tolist(), y=df_sens.index.tolist(),
        colorscale=[[0,"#E4D4D3"],[0.3,"#E9DFCE"],[0.5,"#D2D6D0"],[0.7,"#D6CFC7"],[1,"#8C7851"]],
        text=[[f"{cur}{v:,.0f}" for v in row] for row in df_sens.values],
        texttemplate="%{text}", textfont={"size":11, "color":"#2D2926"},
        hovertemplate="WACC: %{y}<br>Terminal g: %{x}<br>Value: %{text}<extra></extra>",
        showscale=True, colorbar=dict(title="Value",tickformat=f",.0f",thickness=15)
      ))
      # Highlight base case
      base_wi=[i for i,r in enumerate(df_sens.index) if "0" in r and abs(float(r.split("=")[1].rstrip("%"))/100-base_wacc)<0.001]
      base_gi=[i for i,c in enumerate(df_sens.columns) if abs(float(c.split("=")[1].rstrip("%"))/100-base_sg)<0.001]
      if base_wi and base_gi:
        fig_sens.add_shape(type="rect",xref="x",yref="y",
          x0=base_gi[0]-.5,x1=base_gi[0]+.5,y0=base_wi[0]-.5,y1=base_wi[0]+.5,
          line=dict(color="#2D2926",width=3))
        fig_sens.add_annotation(xref="x",yref="y",x=base_gi[0],y=base_wi[0],text="BASE",
          font=dict(color="#2D2926",size=9,family="Inter"),showarrow=False,yshift=16)
      fig_sens.add_hline(y=df_sens.index.tolist().index(f"WACC={base_wacc:.1%}") if f"WACC={base_wacc:.1%}" in df_sens.index else 0,
        line_dash="dot",line_color="#8C7851",opacity=.6)
      fig_sens.update_layout(**PL,title=f"Intrinsic Value Sensitivity — {co_name}",height=380,xaxis_title="Terminal Growth Rate",yaxis_title="WACC")
      st.plotly_chart(fig_sens,use_container_width=True)

      # Tornado chart — key driver sensitivity
      st.markdown("#### 🌪️ Key Value Drivers — Tornado Chart")
      base_iv=intrinsic if intrinsic>0 else 1
      drivers=[]
      params={"WACC -2pp":(base_wacc-.02,base_sg),"WACC +2pp":(base_wacc+.02,base_sg),
               "Growth -1pp":(base_wacc,base_sg-.01),"Growth +1pp":(base_wacc,base_sg+.01),
               "Growth -2pp":(base_wacc,base_sg-.02),"Growth +2pp":(base_wacc,base_sg+.02)}
      for name,(w,g) in params.items():
        iv=_sens_val(w,g)
        drivers.append({"Driver":name,"Impact":iv-base_iv,"Impact%":(iv-base_iv)/base_iv if base_iv else 0,"New Value":iv})
      df_torn=pd.DataFrame(drivers).sort_values("Impact")
      fig_torn=go.Figure()
      fig_torn.add_trace(go.Bar(y=df_torn["Driver"],x=df_torn["Impact%"],orientation="h",
        marker_color=["#9D5C58" if v<0 else "#5F7161" for v in df_torn["Impact%"]],
        text=[f"{v:+.1%}" for v in df_torn["Impact%"]],textposition="outside",
        hovertemplate="%{y}: %{text} (%{x:.1%})<extra></extra>"))
      fig_torn.add_vline(x=0,line_color="#D6CFC7",line_width=1.5)
      fig_torn.update_layout(**PL,title="Impact on Intrinsic Value",xaxis_title="Change from Base",height=320,showlegend=False)
      st.plotly_chart(fig_torn,use_container_width=True)

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 2 — FINANCIAL ANALYSIS                                  ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab2:
    st.markdown("### 📈 Price History")
    period_map={"1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y","3 Years":"3y","5 Years":"5y"}
    p_col1,p_col2=st.columns([3,1])
    with p_col2:
      chosen_period=st.selectbox("Period",list(period_map.keys()),index=3)
    ph_period=period_map[chosen_period]

    try:
      ph=yf.Ticker(ticker).history(period=ph_period)
      if not ph.empty:
        ph=ph.reset_index()
        fig_ph=go.Figure()
        # Candle or line
        if len(ph)<=200 and "Open" in ph.columns:
          fig_ph.add_trace(go.Candlestick(x=ph["Date"],open=ph["Open"],high=ph["High"],low=ph["Low"],close=ph["Close"],
            increasing=dict(fillcolor="#D2D6D0",line=dict(color="#5F7161")),
            decreasing=dict(fillcolor="#E4D4D3",line=dict(color="#9D5C58")),name="Price"))
        else:
          fig_ph.add_trace(go.Scatter(x=ph["Date"],y=ph["Close"],mode="lines",line=dict(color="#8C7851",width=2),name="Close",fill="tozeroy",fillcolor="rgba(140, 120, 81, .1)"))
        # Moving averages
        if len(ph)>=50: ph["MA50"]=ph["Close"].rolling(50).mean(); fig_ph.add_trace(go.Scatter(x=ph["Date"],y=ph["MA50"],mode="lines",line=dict(color="#B58A54",width=1.5,dash="dot"),name="MA50"))
        if len(ph)>=200: ph["MA200"]=ph["Close"].rolling(200).mean(); fig_ph.add_trace(go.Scatter(x=ph["Date"],y=ph["MA200"],mode="lines",line=dict(color="#7A656D",width=1.5,dash="dash"),name="MA200"))
        if has_dcf and intrinsic>0:
          fig_ph.add_hline(y=intrinsic,line_dash="dot",line_color="#5F7161",annotation_text=f"DCF {_fmt(intrinsic,ticker)}",annotation_font_color="#5F7161")
        fig_ph.update_layout(**PL,title=f"{co_name} — {chosen_period} Price Chart",xaxis_title="Date",yaxis_title=f"Price ({cur})",height=420,xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_ph,use_container_width=True)

        # Volume chart
        if "Volume" in ph.columns:
          fig_vol=go.Figure()
          fig_vol.add_trace(go.Bar(x=ph["Date"],y=ph["Volume"],marker_color="#D6CFC7",name="Volume"))
          fig_vol.update_layout(**PL,title="Volume",height=160,showlegend=False,margin=dict(l=40,r=40,t=30,b=30))
          st.plotly_chart(fig_vol,use_container_width=True)
      else:
        st.warning("No price history available.")
    except Exception as e:
      st.warning(f"Price chart error: {e}")

    st.markdown("---")

    # Financial metrics trend (from yfinance income statement)
    st.markdown("### 📊 Financial Trend Analysis")
    try:
      yfin=yf.Ticker(ticker)
      is_df=yfin.income_stmt
      bs_df=yfin.balance_sheet
      cf_df=yfin.cashflow

      if is_df is not None and not is_df.empty:
        is_t=is_df.T.copy(); is_t.index=pd.to_datetime(is_t.index)
        is_t=is_t.sort_index()
        scale=1e-7 if _is_indian(ticker) else 1e-6; unit_lbl="Cr" if _is_indian(ticker) else "M"
        years_lbl=[str(d.year) for d in is_t.index]

        rev=is_t.get("Total Revenue",is_t.get("Revenue",pd.Series(dtype=float)))*scale
        ni=is_t.get("Net Income",is_t.get("Net Income Common Stockholders",pd.Series(dtype=float)))*scale
        ebit=is_t.get("Operating Income",is_t.get("EBIT",pd.Series(dtype=float)))*scale

        fig_fin=make_subplots(rows=1,cols=2,
          subplot_titles=("Revenue, EBIT & Net Income","Profit Margins"),
          horizontal_spacing=.1)

        if not rev.isnull().all():
          fig_fin.add_trace(go.Bar(name="Revenue",x=years_lbl,y=rev.fillna(0).values,marker_color="#8C7851",text=[f"{v:.0f}" for v in rev.fillna(0)],textposition="outside",textfont=dict(size=10)),row=1,col=1)
        if not ebit.isnull().all():
          fig_fin.add_trace(go.Bar(name="EBIT",x=years_lbl,y=ebit.fillna(0).values,marker_color="#7A656D",text=[f"{v:.0f}" for v in ebit.fillna(0)],textposition="outside",textfont=dict(size=10)),row=1,col=1)
        if not ni.isnull().all():
          fig_fin.add_trace(go.Scatter(name="Net Income",x=years_lbl,y=ni.fillna(0).values,mode="lines+markers",line=dict(color="#5F7161",width=2.5),marker=dict(size=8)),row=1,col=1)

        # Margins
        if not rev.isnull().all() and rev.sum()!=0:
          opm=(ebit/rev*100).fillna(0); npm=(ni/rev*100).fillna(0)
          fig_fin.add_trace(go.Scatter(name="Op. Margin",x=years_lbl,y=opm.values,mode="lines+markers",line=dict(color="#B58A54",width=2),marker=dict(size=8)),row=1,col=2)
          fig_fin.add_trace(go.Scatter(name="Net Margin",x=years_lbl,y=npm.values,mode="lines+markers",line=dict(color="#5F7161",width=2),marker=dict(size=8)),row=1,col=2)

        fig_fin.update_layout(**PL,height=380,showlegend=True,title="Historical Financials",barmode="group")
        fig_fin.update_yaxes(title_text=f"{cur} {unit_lbl}",row=1,col=1)
        fig_fin.update_yaxes(title_text="%",row=1,col=2)
        st.plotly_chart(fig_fin,use_container_width=True)
      else:
        st.info("Income statement data not available from yfinance for this ticker.")
    except Exception as e:
      st.warning(f"Financial trend data unavailable: {e}")

    st.markdown("---")

    # Key Ratios
    st.markdown("### 📐 Valuation & Financial Ratios")
    try:
      info_r=yf.Ticker(ticker).info
      def gr(keys,fb="N/A"):
        for k in keys:
          v=info_r.get(k)
          if v is not None:
            try:
              fv=float(v)
              if abs(fv)<1 and fv!=0: return f"{fv:.1%}"
              if abs(fv)>1e9: return f"{fv/1e9:.1f}B"
              return f"{fv:.2f}"
            except: return str(v)
        return fb

      ratio_cols=st.columns(4)
      ratio_groups=[
        ("📊 Valuation",[("P/E (Trailing)","trailingPE"),("P/E (Forward)","forwardPE"),("P/B Ratio","priceToBook"),("EV/EBITDA","enterpriseToEbitda"),("P/S Ratio","priceToSalesTrailing12Months")]),
        ("💰 Profitability",[("Gross Margin","grossMargins"),("Op. Margin","operatingMargins"),("Net Margin","profitMargins"),("ROE","returnOnEquity"),("ROA","returnOnAssets")]),
        ("⚖️ Leverage",[("Debt/Equity","debtToEquity"),("Current Ratio","currentRatio"),("Quick Ratio","quickRatio"),("Interest Coverage",""),("Beta","beta")]),
        ("📈 Growth",[("Rev Growth (YoY)","revenueGrowth"),("Earnings Growth","earningsGrowth"),("EPS (TTM)","trailingEps"),("Dividend Yield","dividendYield"),("Payout Ratio","payoutRatio")]),
      ]
      for col,(title,metrics_list) in zip(ratio_cols,ratio_groups):
        with col:
          st.markdown(f"<p style='color:#8C7851;font-weight:700;font-size:.85rem;letter-spacing:.5px;margin-bottom:6px;'>{title}</p>", unsafe_allow_html=True)
          for label,key in metrics_list:
            val_r=gr([key]) if key else "—"
            st.write(f"{label}: **{val_r}**")
    except Exception as e:
      st.warning(f"Ratios unavailable: {e}")

    st.markdown("---")

    # Radar chart
    st.markdown("### 🕸️ Financial Profile Radar")
    try:
      info_rad=yf.Ticker(ticker).info
      def pct_score(key,low=0,high=.5):
        v=info_rad.get(key,0)
        if v is None: return .5
        try: return max(0,min(1,(float(v)-low)/(high-low)))
        except: return .5

      radar_cats=["Profitability","Growth","Safety","Efficiency","Dividend","Valuation"]
      radar_vals=[
        pct_score("profitMargins",0,.3)*10,
        pct_score("earningsGrowth",-.1,.5)*10,
        max(0,10-pct_score("debtToEquity",0,300)*10),
        pct_score("returnOnEquity",-0.05,.4)*10,
        pct_score("dividendYield",0,.08)*10,
        max(0,10-pct_score("trailingPE",0,80)*10),
      ]
      fig_rad=go.Figure()
      fig_rad.add_trace(go.Scatterpolar(r=radar_vals+[radar_vals[0]],theta=radar_cats+[radar_cats[0]],
        fill="toself",fillcolor="rgba(140,120,81,.15)",line=dict(color="#8C7851",width=2),name=co_name))
      fig_rad.update_layout(**PL,polar=dict(radialaxis=dict(visible=True,range=[0,10],gridcolor="#D6CFC7"),
        angularaxis=dict(gridcolor="#D6CFC7")),title="Financial Profile (0–10 scale)",height=380)
      st.plotly_chart(fig_rad,use_container_width=True)
    except Exception as e:
      st.warning(f"Radar chart unavailable: {e}")

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 3 — MONTE CARLO                                         ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab3:
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0 16px;"><span class="sb sb-terra">SIMULATION</span><span style="font-size:1.2rem;font-weight:700;">Monte Carlo — {sims:,} paths · {years}yr horizon · {crash}% stress</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="signal" style="background:{sig_bg};border-color:{sig_bdr};"><h1 style="color:{sig_txt};font-size:1.7rem;">{vt}</h1><p style="color:{sig_txt};">{sub_txt}</p></div>', unsafe_allow_html=True)

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Current Price",_fmt(s0,ticker))
    if has_dcf and intrinsic>0: m2.metric("DCF Intrinsic",_fmt(intrinsic,ticker),f"{((intrinsic/s0)-1):+.1%}")
    else: m2.metric("MC Expected",_fmt(metrics["Expected Price"],ticker),f"{((metrics['Expected Price']/s0)-1):+.1%}")
    m3.metric("VaR 95%",f"{metrics['VaR 95% (Rel)']:.1%}")
    m4.metric("Prob. of Profit",f"{metrics['Prob. of Profit']:.1f}%")
    st.markdown("")

    d1,d2,d3,d4=st.columns(4)
    with d1:
      st.markdown("<p style='color:#8C7851;font-weight:700;font-size:.83rem;letter-spacing:.5px;'>📈 PRICE TARGETS</p>", unsafe_allow_html=True)
      for l,k in [("Expected","Expected Price"),("Median","Median Price"),("Best","Best Case Price"),("Worst","Worst Case Price"),("90th %ile","90th Percentile Price"),("10th %ile","10th Percentile Price")]:
        st.write(f"{l}: **{_fmt(metrics[k],ticker)}**")
    with d2:
      st.markdown("<p style='color:#9D5C58;font-weight:700;font-size:.83rem;letter-spacing:.5px;'>⚠️ RISK</p>", unsafe_allow_html=True)
      for l,k in [("VaR 95%","VaR 95% (Rel)"),("CVaR 95%","CVaR 95%"),("VaR 99%","VaR 99% (Rel)"),("CVaR 99%","CVaR 99%"),("Max DD","Max Drawdown"),("Vol","Volatility (Annual)")]:
        fmt=f"{metrics[k]:.2%}" if "%" in str(metrics[k]) or k not in ["Max Drawdown","Volatility (Annual)"] else f"{metrics[k]:.1f}%"
        st.write(f"{l}: **{fmt}**")
    with d3:
      st.markdown("<p style='color:#7A656D;font-weight:700;font-size:.83rem;letter-spacing:.5px;'>📊 PROBABILITY</p>", unsafe_allow_html=True)
      for l,k in [("Profit","Prob. of Profit"),(">10%","Prob. of >10% Gain"),(">25%","Prob. of >25% Gain"),("Loss>10%","Prob. of >10% Loss"),("Avg Up","Avg Upside"),("Avg Down","Avg Downside")]:
        fmt=f"{metrics[k]:.1f}%" if "Avg" in k else f"{metrics[k]:.1f}%"
        st.write(f"{l}: **{'+'if 'Up' in l else ''}{fmt}**")
    with d4:
      st.markdown("<p style='color:#A76D60;font-weight:700;font-size:.83rem;letter-spacing:.5px;'>🏆 RATIOS</p>", unsafe_allow_html=True)
      st.write(f"Sharpe: **{metrics['Sharpe Ratio']:.2f}**"); st.write(f"Sortino: **{metrics['Sortino Ratio']:.2f}**")
      st.write(f"Risk/Reward: **{metrics['Risk-Reward Ratio']:.2f}**"); st.write(f"Exp. Return: **{metrics['Expected Return']:.1f}%**")
      st.write(f"Max Upside: **+{metrics['Max Upside']:.1f}%**")
    st.markdown("")

    cl,cr=st.columns(2)
    with cl:
      fig=go.Figure()
      x=np.arange(len(low_band))
      fig.add_trace(go.Scatter(x=x,y=high_band,fill=None,mode="lines",line=dict(color="rgba(140,120,81,.2)",width=0),name="Top 5%"))
      fig.add_trace(go.Scatter(x=x,y=low_band,fill="tonexty",mode="lines",line=dict(color="rgba(157,92,88,0)",width=0),fillcolor="#D6CFC7",name="90% Band"))
      fig.add_trace(go.Scatter(y=np.mean(paths,axis=1),mode="lines",line=dict(color="#2D2926",width=2.5),name="Expected"))
      if has_dcf and intrinsic>0:
        fig.add_hline(y=intrinsic,line_dash="dot",line_color="#5F7161",annotation_text=f"DCF {_fmt(intrinsic,ticker)}",annotation_font_color="#5F7161")
      fig.add_hline(y=s0,line_dash="dash",line_color="#B58A54",annotation_text="Current Price",annotation_font_color="#B58A54")
      fig.update_layout(**PL,title="Monte Carlo Confidence Bands",xaxis_title="Trading Days",yaxis_title=f"Price ({cur})",height=420)
      st.plotly_chart(fig,use_container_width=True)
    with cr:
      fig2=go.Figure()
      fig2.add_trace(go.Histogram(x=final_prices,nbinsx=60,marker_color="#D6CFC7",marker_line=dict(color="#8C7851",width=.5)))
      fig2.add_vline(x=s0,line_dash="dash",line_color="#B58A54",annotation_text=f"Market {_fmt(s0,ticker)}",annotation_font_color="#B58A54")
      if has_dcf and intrinsic>0:
        fig2.add_vline(x=intrinsic,line_dash="dot",line_color="#5F7161",annotation_text=f"DCF {_fmt(intrinsic,ticker)}",annotation_font_color="#5F7161")
      q05,q95=np.percentile(final_prices,[5,95])
      fig2.add_vrect(x0=0,x1=q05,fillcolor="#E4D4D3",opacity=0.5,line_width=0,annotation_text="VaR 95%",annotation_font_color="#9D5C58")
      fig2.update_layout(**PL,title="Terminal Price Distribution",xaxis_title=f"Price ({cur})",yaxis_title="Frequency",height=420)
      st.plotly_chart(fig2,use_container_width=True)

    st.markdown("#### 📊 vs Benchmarks")
    bn,br=("Nifty 50 (12%)",1.12) if _is_indian(ticker) else ("S&P 500 (10%)",1.10)
    mg=s0*(br**years)
    bench=[]
    if has_dcf and intrinsic>0: bench.append({"Scenario":f"{co_name} — DCF","Value":_fmt(intrinsic,ticker),"Return":f"{((intrinsic/s0)-1):+.1%}"})
    bench.append({"Scenario":f"{co_name} — MC","Value":_fmt(metrics["Expected Price"],ticker),"Return":f"{((metrics['Expected Price']/s0)-1):+.1%}"})
    bench.append({"Scenario":bn,"Value":_fmt(mg,ticker),"Return":f"{((mg/s0)-1):+.1%}"})
    st.table(pd.DataFrame(bench))

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 4 — CROSS-VERIFICATION                                  ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab4:
    if not has_dcf or not intrinsic:
      st.info("DCF must succeed for cross-verification.")
    else:
      st.markdown('<div style="display:flex;align-items:center;gap:10px;margin:4px 0 16px;"><span class="sb sb-plum">STEP 5</span><span style="font-size:1.2rem;font-weight:700;">Cross-Verification & Auto-Correction</span></div>', unsafe_allow_html=True)
      st.caption("DCF vs. analyst consensus & sector. Auto-corrects if deviation >30%.")
      sector=TICKER_TO_SECTOR.get(ticker,SECTOR_CLEAN.get(category,category))
      with st.spinner("Cross-verifying…"):
        cv=cross_verify_and_correct(ticker,intrinsic,s0,our_signal,sector,fd,val)
      consensus=cv["consensus"]; sector_data=cv["sector_data"]; is_india=_is_indian(ticker)
      flag_e="🇮🇳" if is_india else "🇺🇸"
      ct="Indian Brokerage Consensus" if is_india else "Wall Street Analyst Consensus"
      cf=("Motilal Oswal · ICICI Direct · HDFC Securities · Kotak · Jefferies India" if is_india else "Goldman Sachs · Morgan Stanley · JP Morgan · UBS · Bank of America")

      st.markdown(f'<div class="card" style="border-color:#D6CFC7;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="font-size:1.4rem;">{flag_e}</span><span style="font-size:1.05rem;font-weight:700;">{ct}</span></div><p style="color:#6B6661;font-size:.78rem;margin:0;">{cf}</p></div>', unsafe_allow_html=True)

      if consensus["available"]:
        st.caption(f"Source: {consensus.get('source','N/A')}")
        st.table(pd.DataFrame([
          {"Metric":"Consensus Target","Value":f"{cur}{consensus['target_mean']:,.2f}"},
          {"Metric":"Range","Value":f"{cur}{consensus['target_low']:,.2f} — {cur}{consensus['target_high']:,.2f}"},
          {"Metric":"Rating","Value":str(consensus.get('recommendation','N/A')).upper()},
          {"Metric":"Analysts","Value":str(consensus.get('num_analysts','N/A'))},
          {"Metric":"Our DCF","Value":f"{cur}{intrinsic:,.2f}"},
          {"Metric":"Deviation","Value":f"{cv['deviation']:+.1%}" if cv['deviation'] else "N/A"},
        ]))
        brok=consensus.get("top_brokerages",{})
        if brok: st.table(pd.DataFrame([{"Firm":f,"Target":f"{cur}{d['target']:,.2f}","Rating":d["rating"]} for f,d in brok.items()]))
      else: st.warning("Consensus not available.")

      ob={"Bullish":"#D2D6D0","Neutral-Bullish":"#EBE7E2","Neutral":"#E9DFCE","Mixed":"#E9DFCE","Bearish":"#E4D4D3"}.get(sector_data["outlook"],"#EBE7E2")
      ot={"Bullish":"#2B3A30","Neutral-Bullish":"#3A4B40","Neutral":"#543C16","Mixed":"#543C16","Bearish":"#4A2624"}.get(sector_data["outlook"],"#2D2926")
      st.markdown(f'<div class="card" style="border-color:#D6CFC7;margin-top:8px;"><span style="font-size:1.1rem;font-weight:700;">📊 Sector: {sector}</span><br><br><span style="background:{ob};color:{ot};padding:3px 12px;border-radius:20px;font-weight:600;font-size:.83rem;border:1px solid {ot}40;">{sector_data["outlook"]}</span> &nbsp; PE: <b>{sector_data["avg_pe"]}x</b> &nbsp; Growth: <b>{sector_data["avg_growth"]:.0%}</b></div>', unsafe_allow_html=True)
      st.markdown(f"> {sector_data['narrative']}")
      if cv["industry_mismatch"]: st.warning("⚠️ Our signal conflicts with sector outlook.")
      st.markdown("---")

      if cv["needs_correction"]:
        st.error("🔧 AUTO-CORRECTION TRIGGERED — deviation >30%")
        cr_result=cv["corrected_result"]
        if cr_result and cr_result["intrinsic_value"]>0:
          new_iv=cr_result["intrinsic_value"]
          st.markdown("#### ⚖️ Original vs Corrected")
          c1_,c2_=st.columns(2)
          with c1_: st.metric("Original DCF",_fmt(intrinsic,ticker),f"{((intrinsic/s0)-1):+.1%} vs market")
          with c2_: st.metric("Corrected DCF",_fmt(new_iv,ticker),f"{((new_iv/s0)-1):+.1%} vs market")
          chg=(new_iv-intrinsic)/intrinsic if intrinsic else 0
          fig_cv=go.Figure(go.Bar(x=["Market","Original DCF","Corrected DCF"],y=[s0,intrinsic,new_iv],
            marker_color=["#B58A54","#9D5C58","#8C7851"],text=[f"{cur}{v:,.0f}" for v in [s0,intrinsic,new_iv]],textposition="outside",marker_cornerradius=6))
          fig_cv.update_layout(**PL,title="Value Comparison",height=350,showlegend=False)
          st.plotly_chart(fig_cv,use_container_width=True)
      else:
        st.success("✅ No correction needed — DCF aligns with consensus & sector outlook.")
        if consensus["available"] and consensus["target_mean"]:
          fig_ok=go.Figure(go.Bar(x=["Market",f"{'' if is_india else 'WS '}Consensus","Our DCF"],y=[s0,consensus["target_mean"],intrinsic],marker_color=["#B58A54","#7A656D","#8C7851"],text=[f"{cur}{v:,.0f}" for v in [s0,consensus["target_mean"],intrinsic]],textposition="outside",marker_cornerradius=6))
          fig_ok.update_layout(**PL,title="DCF vs Consensus vs Market",height=350,showlegend=False)
          st.plotly_chart(fig_ok,use_container_width=True)

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 5 — CAPITAL STRUCTURE OPTIMIZER                         ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab5:
    st.markdown("""
    <div style="animation:fadeInUp .4s ease both;">
    <h3 style="color:#2D2926;margin-bottom:4px;">🏗️ Capital Structure Optimizer</h3>
    <p style="color:#6B6661;font-size:.9rem;margin-top:0;">
    Adjust the company's capital structure using the sidebar sliders and instantly see how WACC, cost of equity, 
    and intrinsic value change. Based on Modigliani-Miller (with taxes) and the Trade-Off Theory.</p>
    </div>""", unsafe_allow_html=True)

    base_beta=fd.get("beta",1.2) if (has_dcf and fd) else 1.2
    base_dr=fd.get("debt_ratio",0.3) if (has_dcf and fd) else 0.3

    # Compute WACC from sidebar inputs using Hamada equation
    D_over_E_old=base_dr/(1-base_dr) if base_dr<1 else 1
    unlevered_beta=base_beta/(1+((1-cs_tax)*D_over_E_old)) if (1+((1-cs_tax)*D_over_E_old))!=0 else base_beta

    # Re-lever at new debt ratio
    D_over_E_new=cs_debt_ratio/(1-cs_debt_ratio) if cs_debt_ratio<1 else 5
    levered_beta=unlevered_beta*(1+(1-cs_tax)*D_over_E_new)
    cs_ke=cs_rf+levered_beta*cs_erp
    cs_wacc=(1-cs_debt_ratio)*cs_ke + cs_debt_ratio*cs_kd*(1-cs_tax)
    cs_kd_ats=cs_kd*(1-cs_tax)

    # Impact on intrinsic value
    iv_new=0
    if has_dcf and intrinsic>0:
      from valuation_models import compute_fcff
      fcff_t_cs=compute_fcff(fd.get("ebit",0),fd.get("tax_rate",.25),fd.get("depreciation",0),fd.get("capex",0),fd.get("delta_wc",0))
      sg_cs=fd.get("stable_growth", fd.get("inflation_rate",.03)+fd.get("real_growth_rate",.02)*.5) if fd else .03
      hg_cs=fd.get("firm_growth_rate",.08) if fd else .08
      from valuation_models import fcff_two_stage as fts
      try:
        r_cs=fts(fcff_t_cs,cs_wacc,cs_wacc*.95,hg_cs,sg_cs,7,fd["total_debt"],fd["cash"],fd["shares_outstanding"])
        iv_new=max(0,r_cs.get("intrinsic_value_per_share",r_cs.get("intrinsic_value",0)))
      except: iv_new=0

    # KPI row
    st.markdown("#### 📊 New Capital Structure Metrics")
    ck1,ck2,ck3,ck4,ck5=st.columns(5)
    ck1.metric("Debt Ratio",f"{cs_debt_ratio:.0%}",f"{cs_debt_ratio-base_dr:+.0%} vs orig")
    ck2.metric("Re-levered Beta",f"{levered_beta:.2f}",f"{levered_beta-base_beta:+.2f} vs orig")
    ck3.metric("Cost of Equity (Ke)",f"{cs_ke:.2%}","CAPM w/ new beta")
    ck4.metric("WACC",f"{cs_wacc:.2%}",f"{cs_wacc-fd.get('wacc',.10):+.2%} vs orig" if has_dcf else "")
    iv_delta=((iv_new-intrinsic)/intrinsic) if has_dcf and intrinsic>0 and iv_new>0 else 0
    ck5.metric("New Intrinsic Value",_fmt(iv_new,ticker) if iv_new>0 else "N/A",f"{iv_delta:+.1%} vs orig DCF" if iv_new>0 else "")

    st.markdown("---")
    st.markdown("#### 📈 WACC Curve — Trade-Off Theory")

    # Build full WACC curve across debt ratios
    dr_range=np.linspace(0.01,0.90,90)
    wacc_curve=[]; ke_curve=[]; kd_ats_curve=[]; iv_curve=[]
    for dr in dr_range:
      doe=dr/(1-dr)
      lb_=unlevered_beta*(1+(1-cs_tax)*doe)
      ke_=cs_rf+lb_*cs_erp
      distress=max(0,(dr-.6)*.15)
      kd_=cs_kd+distress
      w_=(1-dr)*ke_+dr*kd_*(1-cs_tax)
      wacc_curve.append(w_); ke_curve.append(ke_); kd_ats_curve.append(kd_*(1-cs_tax))
      if has_dcf:
        try:
          r_=fts(fcff_t_cs,max(.01,w_),max(.01,w_*.95),hg_cs,sg_cs,7,fd["total_debt"],fd["cash"],fd["shares_outstanding"])
          iv_curve.append(max(0,r_.get("intrinsic_value_per_share",r_.get("intrinsic_value",0))))
        except: iv_curve.append(0)

    fig_wacc=make_subplots(rows=1,cols=2,subplot_titles=("WACC, Ke & Kd(1-T) vs Debt Ratio","Intrinsic Value vs Debt Ratio"),horizontal_spacing=.1)
    fig_wacc.add_trace(go.Scatter(x=dr_range,y=wacc_curve,mode="lines",name="WACC",line=dict(color="#8C7851",width=2.5)),row=1,col=1)
    fig_wacc.add_trace(go.Scatter(x=dr_range,y=ke_curve,mode="lines",name="Ke (Equity)",line=dict(color="#9D5C58",width=2,dash="dash")),row=1,col=1)
    fig_wacc.add_trace(go.Scatter(x=dr_range,y=kd_ats_curve,mode="lines",name="Kd(1-T)",line=dict(color="#5F7161",width=2,dash="dot")),row=1,col=1)
    # Min WACC point
    min_wacc_idx=int(np.argmin(wacc_curve))
    fig_wacc.add_trace(go.Scatter(x=[dr_range[min_wacc_idx]],y=[wacc_curve[min_wacc_idx]],mode="markers",
      marker=dict(color="#2D2926",size=12,symbol="star"),name=f"Optimal D/E={dr_range[min_wacc_idx]:.0%}"),row=1,col=1)
    # Current point
    fig_wacc.add_vline(x=cs_debt_ratio,line_color="#B58A54",line_dash="dot",row=1,col=1,annotation_text="Current",annotation_font_color="#B58A54")
    if has_dcf and iv_curve:
      fig_wacc.add_trace(go.Scatter(x=dr_range,y=iv_curve,mode="lines",name="Intrinsic Value",line=dict(color="#7A656D",width=2.5)),row=1,col=2)
      max_iv_idx=int(np.argmax(iv_curve))
      fig_wacc.add_trace(go.Scatter(x=[dr_range[max_iv_idx]],y=[iv_curve[max_iv_idx]],mode="markers",
        marker=dict(color="#2D2926",size=12,symbol="star"),name=f"Max Value D/E={dr_range[max_iv_idx]:.0%}"),row=1,col=2)
      fig_wacc.add_vline(x=cs_debt_ratio,line_color="#B58A54",line_dash="dot",row=1,col=2)
      fig_wacc.add_hline(y=s0,line_color="#B58A54",line_dash="dash",row=1,col=2,annotation_text="Market Price",annotation_font_color="#B58A54")
    fig_wacc.update_layout(**PL,height=400,title="Capital Structure Trade-Off Analysis")
    fig_wacc.update_yaxes(title_text="Rate (%)",tickformat=".1%",row=1,col=1)
    if has_dcf: fig_wacc.update_yaxes(title_text=f"Value ({cur})",row=1,col=2)
    st.plotly_chart(fig_wacc,use_container_width=True)

    # Insight card
    opt_dr=dr_range[min_wacc_idx]
    if abs(cs_debt_ratio-opt_dr)<.05:
      cs_insight="✅ The current debt ratio is near the theoretical optimum. Capital structure appears efficient."
      ci_color="#2B3A30"; ci_bg="#D2D6D0"; bdr_clr="#5F7161"
    elif cs_debt_ratio<opt_dr-.10:
      cs_insight=f"📉 The firm is **under-leveraged** relative to the optimum (~{opt_dr:.0%}). More debt could lower WACC and increase firm value — subject to financial flexibility constraints."
      ci_color="#543C16"; ci_bg="#E9DFCE"; bdr_clr="#B58A54"
    else:
      cs_insight=f"📈 The firm is **over-leveraged** relative to the optimum (~{opt_dr:.0%}). Excess debt increases distress risk and raises WACC above the minimum."
      ci_color="#5C3A38"; ci_bg="#E4D4D3"; bdr_clr="#9D5C58"
    st.markdown(f'<div style="background:{ci_bg};border:1px solid {bdr_clr}40;border-left:4px solid {bdr_clr};border-radius:0 10px 10px 0;padding:14px 18px;color:{ci_color};font-size:.92rem;margin-bottom:16px;">{cs_insight}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔁 Scenario Comparison Table")

    scenarios=[
      ("All Equity (0%)",0.0),("Conservative (20%)",0.20),("Current",base_dr),
      (f"Custom ({cs_debt_ratio:.0%})",cs_debt_ratio),("Optimal WACC",opt_dr),("Aggressive (70%)",0.70),
    ]
    scen_rows=[]
    for sname,sdr in scenarios:
      doe_s=sdr/(1-sdr) if sdr<1 else 9
      lb_s=unlevered_beta*(1+(1-cs_tax)*doe_s)
      ke_s=cs_rf+lb_s*cs_erp
      dist_s=max(0,(sdr-.6)*.15)
      kd_s=cs_kd+dist_s
      w_s=(1-sdr)*ke_s+sdr*kd_s*(1-cs_tax)
      iv_s=0
      if has_dcf:
        try:
          r_s=fts(fcff_t_cs,max(.01,w_s),max(.01,w_s*.95),hg_cs,sg_cs,7,fd["total_debt"],fd["cash"],fd["shares_outstanding"])
          iv_s=max(0,r_s.get("intrinsic_value_per_share",r_s.get("intrinsic_value",0)))
        except: pass
      scen_rows.append({"Scenario":sname,"D/E":f"{sdr:.0%}","Beta":f"{lb_s:.2f}","Ke":f"{ke_s:.1%}","WACC":f"{w_s:.1%}","Intrinsic Value":_fmt(iv_s,ticker) if iv_s>0 else "—"})
    st.dataframe(pd.DataFrame(scen_rows),use_container_width=True,hide_index=True)

    st.markdown("---")
    with st.expander("📚 Theory Reference — Modigliani-Miller & Trade-Off Theory"):
      st.markdown("""
**Modigliani-Miller Proposition I (with taxes):** Firm value increases with leverage due to the tax shield on debt interest. V_L = V_U + t×D.

**Modigliani-Miller Proposition II (with taxes):** Cost of equity rises with leverage: Ke = Ku + (Ku − Kd)(1−t)(D/E). This is captured via the Hamada equation in this model.

**Hamada Equation:** β_L = β_U × [1 + (1−t) × D/E]. Levering up increases equity beta and thus the required return on equity.

**Trade-Off Theory:** The optimal capital structure balances the tax shield benefit of debt against the costs of financial distress. The WACC curve has a minimum at the optimal D/E, shown as the star (⭐) on the chart above.

**WACC Formula:** WACC = (E/V)×Ke + (D/V)×Kd×(1−t). Minimising WACC maximises firm value.
      """)

  # ╔═══════════════════════════════════════════════════════════════╗
  # ║  TAB 6 — DATA AUDIT                                          ║
  # ╚═══════════════════════════════════════════════════════════════╝
  with tab6:
    st.markdown('<div style="display:flex;align-items:center;gap:10px;margin:4px 0 16px;"><span class="sb sb-sage">AUDIT</span><span style="font-size:1.2rem;font-weight:700;">Automated Multi-Source Data Audit</span></div>', unsafe_allow_html=True)
    st.caption("Cross-checks price & fundamentals across 3 independent sources.")
    with st.spinner("Running audit…"):
      hardcoded_fd=val["fundamentals"] if val else None
      audit=run_data_audit(ticker,hardcoded_fd=hardcoded_fd)

    status_cfg={"VERIFIED":("#D2D6D0","#5F7161","#2B3A30","✅ VERIFIED"),
      "MINOR DISCREPANCY":("#E9DFCE","#B58A54","#543C16","⚠️ MINOR DISCREPANCY"),
      "MAJOR DISCREPANCY":("#E4D4D3","#9D5C58","#4A2624","🚨 MAJOR DISCREPANCY")}
    sb,sc,st_txt,slbl=status_cfg.get(audit["overall_status"],("#EBE7E2","#D6CFC7","#2D2926","ℹ️ COMPLETE"))
    st.markdown(f'<div style="background:{sb};border:2px solid {sc};border-radius:12px;padding:14px 20px;margin:0 0 18px;"><span style="color:{st_txt};font-weight:800;font-size:1.1rem;">{slbl}</span><p style="color:{st_txt};opacity:.7;font-size:.8rem;margin:2px 0 0;">{len(audit.get("flags",[]))} flag(s)</p></div>', unsafe_allow_html=True)

    flags=audit.get("flags",[])
    if flags:
      with st.expander(f"🚩 {len(flags)} Flag(s)",expanded=True):
        for f in flags:
          if isinstance(f, dict):
            sev=f.get("severity","info"); msg=f.get("message",str(f)); field=f.get("field","")
          else:
            sev="warning" if "⚠️" in str(f) else "critical" if "🔴" in str(f) else "info"
            msg=str(f).lstrip("⚠️🔴✅ "); field=""
          cls="af-r" if sev=="critical" else "af-y" if sev=="warning" else "af-g"
          ic="🔴" if sev=="critical" else "🟡" if sev=="warning" else "🟢"
          label=f"<b>{field}</b>: " if field else ""
          st.markdown(f'<div class="{cls}">{ic} {label}{msg}</div>', unsafe_allow_html=True)
    else:
      st.markdown('<div class="af-g">🟢 All sources in agreement — no flags raised.</div>', unsafe_allow_html=True)

    ps = audit.get("price_sources", [])
    if ps:
      st.markdown("##### 📈 Price Sources")
      pr = []
      items_ps = ps if isinstance(ps, list) else list(ps.values())
      for d in items_ps:
        if not isinstance(d, dict): continue
        if "error" in d:
          pr.append({"Source": d.get("source","—"), "Price": "⚠️ Error", "Status": "FAIL", "Note": str(d.get("error",""))[:60]})
        else:
          pr.append({"Source": d.get("source","—"), "Price": _fmt(d.get("price",0),ticker), "Status": d.get("status","OK"), "Note": d.get("label","")})
      if pr: st.dataframe(pd.DataFrame(pr), use_container_width=True, hide_index=True)

    ag = audit.get("agreement", {})
    if ag:
      st.markdown("##### 📊 Fundamentals Agreement")
      ar = []
      for m, v in ag.items():
        if not isinstance(v, dict): continue
        ar.append({"Metric": m, "Src A": v.get("source_a_val","—"), "Src B": v.get("source_b_val","—"),
                   "Src C": v.get("source_c_val","—"), "Spread": f"{v.get('spread_pct',0):.1f}%",
                   "✓": "✅" if v.get("agree") else "⚠️"})
      if ar: st.dataframe(pd.DataFrame(ar), use_container_width=True, hide_index=True)

    hvl = audit.get("hardcoded_vs_live", {})
    if hvl and isinstance(hvl, dict) and any(isinstance(v,dict) for v in hvl.values()):
      st.markdown("##### 🔄 Hardcoded vs Live")
      hr = [{"Field":f,"Hardcoded":v.get("hardcoded","—"),"Live":v.get("live","—"),
             "Δ":v.get("delta","—"),"⚑":"🚨" if v.get("flag")=="critical" else "⚠️" if v.get("flag")=="warning" else "✅"}
            for f,v in hvl.items() if isinstance(v,dict)]
      if hr: st.dataframe(pd.DataFrame(hr), use_container_width=True, hide_index=True)

    st.markdown(f'<div style="background:#EBE7E2;border:1px solid #D6CFC7;border-radius:8px;padding:10px 14px;margin-top:10px;font-size:.8rem;color:#6B6661;">🔍 Ran: {audit.get("timestamp","N/A")} · Sources: {audit.get("sources_count",3)} · {"🇮🇳 NSE/BSE" if _is_indian(ticker) else "🇺🇸 NYSE/NASDAQ"} · {cur}</div>', unsafe_allow_html=True)

  # FOOTER
  st.markdown("---")
  st.markdown(f"""<div style="text-align:center;padding:20px 0 10px;"><div style="display:inline-block;background:#EBE7E2;border:1px solid #D6CFC7;border-radius:14px;padding:18px 36px;box-shadow:0 2px 12px rgba(0,0,0,.03);">
    <p style="margin:0;font-size:1.2rem;font-weight:800;color:#2D2926;">Arpit Sharma</p>
    <p style="color:#8C7851;font-size:.88rem;margin:3px 0 0;font-weight:500;">IPM 2 · Institutional Equity Lab</p>
    <p style="color:#6B6661;font-size:.73rem;margin:5px 0 0;">Damodaran DCF · Monte Carlo · Capital Structure · Multi-Source Audit · Price: {src_name}</p>
  </div></div>""", unsafe_allow_html=True)

except ValueError as e: st.error(f"Data Error: {e}")
except Exception as e:
  import traceback; st.error(f"Error for {ticker}: {type(e).__name__}: {e}"); st.code(traceback.format_exc())