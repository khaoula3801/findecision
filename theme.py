"""Thème visuel FinDecision : fond blanc (lisible au rétroprojecteur) + bandeau fluo. Aucune logique MCDM ici."""
import streamlit as st

NEON = ["#6D28D9", "#E11DBA", "#06B6D4", "#F59E0B", "#10B981", "#EF4444", "#3B82F6", "#84CC16"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');
:root{--bg:#FFFFFF;--s1:#FFFFFF;--s2:#F6F5FF;--line:#E3E6F3;--tx:#161A38;--mut:#59608A;
  --vi:#6D28D9;--ma:#E11DBA;--cy:#06B6D4;--li:#65A30D;--am:#F59E0B;}
html,body,[class*="css"],.stApp{font-family:'Space Grotesk',system-ui,sans-serif;}
.stApp{background:#FFFFFF!important;color:var(--tx)!important;}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stAppViewContainer"] .block-container{max-width:1500px!important;padding:1.1rem 2.2rem 4rem!important;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{color:var(--tx)!important;letter-spacing:-.02em;font-weight:700;}
.stApp h2{font-size:1.75rem!important;} .stApp h3{font-size:1.2rem!important;}
.stApp [data-testid="stMarkdownContainer"] p,.stApp [data-testid="stMarkdownContainer"] li,.stApp label,
.stApp [data-testid="stWidgetLabel"] p{color:var(--tx)!important;opacity:1!important;}
.stApp [data-testid="stCaptionContainer"] p{color:var(--mut)!important;}
.section-intro{color:var(--mut)!important;font-size:.98rem;line-height:1.65;margin:-.4rem 0 1.1rem;}

/* ============ HERO FLUO ============ */
.fd-hero{position:relative;isolation:isolate;overflow:hidden;border-radius:26px;padding:2rem 2.4rem 0;margin:0 0 1.3rem;
  background:linear-gradient(115deg,#4B2BFF 0%,#9B1BFF 38%,#F0189E 72%,#FF8A1F 100%);
  box-shadow:0 18px 50px rgba(155,27,255,.35),0 4px 14px rgba(240,24,158,.25);}
.fd-grid{position:absolute;inset:0;z-index:-3;opacity:.5;
  background-image:linear-gradient(rgba(255,255,255,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.18) 1px,transparent 1px);
  background-size:42px 42px;-webkit-mask-image:linear-gradient(180deg,transparent,#000 35%,#000 70%,transparent);mask-image:linear-gradient(180deg,transparent,#000 35%,#000 70%,transparent);
  animation:fdgrid 14s linear infinite;}
@keyframes fdgrid{to{background-position:42px 42px;}}
.fd-orb{position:absolute;border-radius:50%;filter:blur(50px);z-index:-2;animation:fdfloat 9s ease-in-out infinite alternate;}
.fd-orb.o1{width:320px;height:320px;right:-50px;top:-110px;background:rgba(0,229,255,.65);}
.fd-orb.o2{width:280px;height:280px;left:35%;bottom:-160px;background:rgba(190,255,60,.55);animation-delay:-4s;}
.fd-orb.o3{width:220px;height:220px;left:-60px;top:-80px;background:rgba(255,255,255,.35);animation-delay:-2s;}
@keyframes fdfloat{from{transform:translate(0,0) scale(1);}to{transform:translate(-30px,24px) scale(1.18);}}
.fd-scan{position:absolute;left:0;right:0;height:110px;z-index:-1;top:-110px;background:linear-gradient(180deg,transparent,rgba(255,255,255,.18),transparent);animation:fdscan 6s linear infinite;}
@keyframes fdscan{to{transform:translateY(420px);}}
.fd-top{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;}
.fd-live{display:inline-flex;align-items:center;gap:.55rem;font:700 .74rem 'JetBrains Mono',monospace;letter-spacing:.18em;color:#fff;}
.fd-live i{width:10px;height:10px;border-radius:50%;background:#B6FF3B;box-shadow:0 0 0 3px rgba(182,255,59,.3),0 0 16px #B6FF3B;animation:fdpulse 1.4s ease-in-out infinite;}
@keyframes fdpulse{50%{opacity:.4;transform:scale(.75);}}
.fd-chip{font:700 .72rem 'JetBrains Mono',monospace;letter-spacing:.14em;color:#fff;padding:.38rem .85rem;border-radius:50px;border:1px solid rgba(255,255,255,.7);background:rgba(255,255,255,.16);}
.fd-title{font-weight:700;font-size:clamp(2.6rem,6.2vw,5rem);line-height:1;letter-spacing:-.045em;margin:.9rem 0 .35rem;color:#fff;text-shadow:0 4px 24px rgba(40,0,90,.35);}
.fd-title span{color:#E8FF4D;text-shadow:0 0 22px rgba(232,255,77,.6),0 4px 24px rgba(40,0,90,.3);}
.fd-sub{color:#FFFFFF;font-size:1.05rem;max-width:800px;line-height:1.6;margin:0 0 1.3rem;text-shadow:0 1px 10px rgba(40,0,90,.45);}
.stApp .fd-hero .fd-sub{color:#FFFFFF!important;}
.stApp .fd-hero .fd-sub b{color:#E8FF4D!important;font-weight:700;}
.fd-kpis{display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:.85rem;margin-bottom:1.3rem;}
.fd-kpi{position:relative;border-radius:16px;padding:.85rem 1.05rem;background:rgba(255,255,255,.18);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,.55);overflow:hidden;transition:transform .18s ease,box-shadow .18s ease;}
.fd-kpi:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(40,0,90,.3);}
.fd-kpi small{display:block;font:700 .66rem 'JetBrains Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.9);}
.fd-kpi strong{display:block;font-size:1.6rem;font-weight:700;color:#fff;letter-spacing:-.02em;margin-top:.15rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.fd-kpi em{font-style:normal;font-size:.76rem;color:rgba(255,255,255,.88);}
.fd-kpi.lead{background:#FFFFFF;border-color:#fff;}
.fd-kpi.lead small{color:#59608A;} .fd-kpi.lead strong{color:#D4128F;} .fd-kpi.lead em{color:#59608A;}
.fd-ticker{margin:0 -2.4rem;background:rgba(20,8,60,.55);overflow:hidden;white-space:nowrap;padding:.65rem 0;}
.fd-track{display:inline-block;animation:fdmarq 32s linear infinite;}
.fd-track span{font:700 .76rem 'JetBrains Mono',monospace;letter-spacing:.16em;color:#fff;margin:0 1.3rem;}
.fd-track span:nth-child(3n+2){color:#8FF3FF;} .fd-track span:nth-child(3n){color:#E8FF4D;}
.fd-track b{color:#FFB020;margin-left:2.6rem;}
@keyframes fdmarq{to{transform:translateX(-50%);}}
@media(max-width:900px){.fd-hero{padding:1.3rem 1.2rem 0;}.fd-kpis{grid-template-columns:1fr 1fr;}.fd-ticker{margin:0 -1.2rem;}}
@media(prefers-reduced-motion:reduce){.fd-grid,.fd-orb,.fd-scan,.fd-live i,.fd-track{animation:none!important;}}

/* ============ ONGLETS ============ */
div[data-testid="stTabs"] [data-baseweb="tab-list"],div[data-testid="stTabs"] [role="tablist"]{gap:.25rem;background:#F6F5FF!important;border:1px solid var(--line)!important;border-radius:16px!important;padding:.35rem!important;margin-bottom:1.2rem;}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"],div[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none!important;}
div[data-testid="stTabs"] [role="tablist"]::after,div[data-testid="stTabs"] [role="tablist"]::before{display:none!important;}
[data-testid="stTab"],button[data-baseweb="tab"]{color:#3E4470!important;font-weight:600!important;font-size:.92rem!important;border-radius:11px!important;padding:.65rem 1.1rem!important;transition:all .18s ease!important;opacity:1!important;}
[data-testid="stTab"] p,button[data-baseweb="tab"] p{color:inherit!important;}
[data-testid="stTab"]:hover,button[data-baseweb="tab"]:hover{color:var(--vi)!important;background:#ECE8FF!important;}
[data-testid="stTab"][aria-selected="true"],button[data-baseweb="tab"][aria-selected="true"]{color:#fff!important;background:linear-gradient(90deg,#6D28D9,#E11DBA)!important;box-shadow:0 6px 18px rgba(109,40,217,.35);}
[data-testid="stTab"][aria-selected="true"] p{color:#fff!important;}
div[data-testid="stTabsContent"]{animation:fdin .3s ease;}
@keyframes fdin{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#F5F2FF,#FFFFFF 70%)!important;border-right:1px solid var(--line);}
.sidebar-brand{font-size:1.65rem;font-weight:700;letter-spacing:-.03em;background:linear-gradient(90deg,#6D28D9,#E11DBA);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.sidebar-sub{font-size:.82rem;color:var(--mut);line-height:1.5;margin:.2rem 0 1rem;}
.sidebar-section{font:700 .68rem 'JetBrains Mono',monospace;letter-spacing:.18em;text-transform:uppercase;color:var(--vi);margin:.4rem 0 .8rem;}
.sidebar-pill{display:inline-block;font:700 .72rem 'JetBrains Mono',monospace;color:#4C1D95;background:#EDE9FE;border:1px solid #D8CCFB;border-radius:50px;padding:.28rem .7rem;margin:.15rem .25rem .4rem 0;}

/* ============ COMPOSANTS ============ */
.stApp [data-testid="stMetric"]{background:#fff!important;border:1px solid var(--line)!important;border-top:4px solid var(--vi)!important;border-radius:16px!important;padding:1rem 1.2rem!important;min-height:112px;box-shadow:0 6px 20px rgba(60,50,120,.08);transition:transform .18s,box-shadow .18s!important;}
.stApp [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"]{border-top-color:var(--ma)!important;}
.stApp [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"]{border-top-color:var(--cy)!important;}
.stApp [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"]{border-top-color:var(--am)!important;}
.stApp [data-testid="stMetric"]:hover{transform:translateY(-4px);box-shadow:0 14px 30px rgba(60,50,120,.16)!important;}
.stApp [data-testid="stMetricLabel"] p{color:var(--mut)!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.08em;font-size:.76rem!important;}
.stApp [data-testid="stMetricValue"]{color:var(--tx)!important;font-size:1.8rem!important;font-weight:700!important;}
.stApp .stButton>button,.stApp .stDownloadButton>button{min-height:44px;font-weight:700!important;border-radius:12px;border:1.5px solid #6D28D9;background:#fff;color:#4C1D95!important;transition:all .16s ease;}
.stApp .stButton>button:hover,.stApp .stDownloadButton>button:hover{transform:translateY(-2px);background:#F3EFFF;box-shadow:0 8px 20px rgba(109,40,217,.22);}
.stApp .stButton>button[kind="primary"],.stApp button[kind="primaryFormSubmit"]{background:linear-gradient(90deg,#E11DBA,#6D28D9)!important;border:none!important;color:#fff!important;box-shadow:0 8px 22px rgba(225,29,186,.35);}
.stApp .stButton>button[kind="primary"] p,.stApp button[kind="primaryFormSubmit"] p{color:#fff!important;}
.stApp .stButton>button[kind="primary"]:hover,.stApp button[kind="primaryFormSubmit"]:hover{filter:brightness(1.08);box-shadow:0 12px 28px rgba(225,29,186,.5);}
.stApp [data-testid="stExpander"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:14px!important;box-shadow:0 3px 12px rgba(60,50,120,.05);}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary p{color:var(--tx)!important;font-weight:600;}
.stApp [data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)!important;background:#FCFBFF;border-radius:16px;}
.stApp [data-testid="stDataFrame"],.stApp [data-testid="stDataEditor"]{border:1px solid var(--line)!important;border-radius:14px!important;overflow:hidden;box-shadow:0 6px 20px rgba(60,50,120,.07);}
.stApp [data-baseweb="select"]>div,.stApp [data-baseweb="input"]>div,.stApp [data-testid="stNumberInput"] input,.stApp [data-testid="stTextInput"] input,.stApp textarea{
  background:#fff!important;color:var(--tx)!important;-webkit-text-fill-color:var(--tx)!important;border-color:#CFD3E8!important;border-radius:10px!important;}
.stApp [data-baseweb="select"] svg{fill:var(--vi)!important;}
.stApp [role="radiogroup"] label p{color:var(--tx)!important;font-weight:500;}
.stApp [data-testid="stAlert"]{border-radius:14px;}
.stApp [data-testid="stAlert"] p{color:var(--tx)!important;}
.stApp hr{border-color:var(--line)!important;}

.slabel,.kicker{font:700 .72rem 'JetBrains Mono',monospace;letter-spacing:.2em;text-transform:uppercase;color:var(--vi);margin:1.4rem 0 .7rem;display:flex;align-items:center;gap:.7rem;}
.slabel:after,.kicker:after{content:"";flex:1;height:2px;background:linear-gradient(90deg,#6D28D9,#E11DBA 40%,transparent);border-radius:2px;opacity:.55;}
.featurecard{position:relative;border:1px solid var(--line);background:#fff;padding:1.1rem 1.2rem;border-radius:18px;min-height:135px;box-shadow:0 6px 20px rgba(60,50,120,.07);transition:transform .18s,box-shadow .18s;}
.featurecard:hover{transform:translateY(-5px);box-shadow:0 16px 32px rgba(60,50,120,.16);}
.featurecard .num{display:inline-flex;align-items:center;justify-content:center;border-radius:10px;width:40px;height:34px;font:700 .82rem 'JetBrains Mono',monospace;color:#fff;background:linear-gradient(135deg,#6D28D9,#E11DBA);margin-bottom:.6rem;box-shadow:0 6px 14px rgba(109,40,217,.35);}
.featurecard b{display:block;font-size:1.02rem;color:var(--tx);margin-bottom:.25rem;}
.featurecard small{font-size:.85rem;line-height:1.5;color:var(--mut);display:block;}
.winner-card{position:relative;overflow:hidden;background:linear-gradient(130deg,#FFF0FB,#F1EBFF);border:2px solid #E11DBA;border-radius:20px;padding:1.1rem 1.35rem;box-shadow:0 10px 30px rgba(225,29,186,.18);}
.winner-card .eyebrow{font:700 .7rem 'JetBrains Mono',monospace;color:#C0129A;text-transform:uppercase;letter-spacing:.16em;}
.winner-card .name{display:block;font-size:1.9rem;font-weight:700;color:var(--tx);letter-spacing:-.03em;margin:.2rem 0;}
.winner-card .score{font-size:.92rem;color:var(--mut);}
.podium{border-radius:18px;padding:1.2rem 1rem;text-align:center;background:#fff;border:2px solid var(--pc);box-shadow:0 10px 26px color-mix(in srgb,var(--pc) 25%,transparent);transition:transform .18s,box-shadow .18s;}
.podium:hover{transform:translateY(-5px);box-shadow:0 16px 34px color-mix(in srgb,var(--pc) 40%,transparent);}
.podium .lab{font:700 .74rem 'JetBrains Mono',monospace;color:var(--pc);letter-spacing:.2em;text-transform:uppercase;}
.podium .alt{font-size:1.45rem;font-weight:700;color:var(--tx);margin:.3rem 0;letter-spacing:-.02em;}
.podium .sc{color:var(--mut);font-size:.9rem;}
.podium.p1{--pc:#F59E0B;background:linear-gradient(160deg,#FFFBEB,#fff);} .podium.p2{--pc:#06B6D4;background:linear-gradient(160deg,#ECFEFF,#fff);} .podium.p3{--pc:#E11DBA;background:linear-gradient(160deg,#FFF0FB,#fff);}
@media(prefers-reduced-motion:reduce){.featurecard,.podium,.fd-kpi,.stApp [data-testid="stMetric"]{transition:none!important;}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(leader, method, n_alt, n_crit, n_methods, weighting, ticker):
    items = "".join(f"<span>{t}</span>" for t in ticker)
    track = items + "<b>◆</b>" + items + "<b>◆</b>"
    leader_html = leader if leader else "—"
    st.markdown(
        f'<div class="fd-hero"><div class="fd-grid"></div><div class="fd-orb o1"></div><div class="fd-orb o2"></div><div class="fd-orb o3"></div><div class="fd-scan"></div>'
        f'<div class="fd-top"><span class="fd-live"><i></i>SYSTÈME EN LIGNE</span><span class="fd-chip">MCDM LAB · ANALYSE MULTICRITÈRE</span></div>'
        f'<div class="fd-title">Fin<span>Decision</span></div>'
        f'<p class="fd-sub">Aide multicritère à la <b>décision d’investissement</b> : pondère, classe, compare et teste la robustesse de tes choix en temps réel.</p>'
        f'<div class="fd-kpis">'
        f'<div class="fd-kpi lead"><small>N°1 · {method}</small><strong>{leader_html}</strong><em>Pondération {weighting}</em></div>'
        f'<div class="fd-kpi"><small>Entreprises</small><strong>{n_alt}</strong><em>alternatives</em></div>'
        f'<div class="fd-kpi"><small>Critères</small><strong>{n_crit}</strong><em>financiers & ESG</em></div>'
        f'<div class="fd-kpi"><small>Méthodes</small><strong>{n_methods}</strong><em>de classement</em></div>'
        f'</div>'
        f'<div class="fd-ticker"><div class="fd-track">{track}</div></div></div>',
        unsafe_allow_html=True,
    )
