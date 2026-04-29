import altair as alt
import streamlit as st
from streamlit_color_chart import ColorChart
from streamlit_logic import (
    avg_emotion_score,
    emotion_by_category,
    emotion_distribution,
    energy_by_node,
    energy_by_pipeline,
    energy_timeline,
    get_emotion_posts,
    get_energy_df,
    get_posts,
    posts_per_hour,
    send_message_api,
    top_users_per_category,
    trending_keywords,
)

# ── Page config — must be first Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="FakeShield",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

C = ColorChart

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown(
    f"""
<style>
/* ─ Fonts ─────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
}}

/* ─ Hide toolbar / status / sidebar / header ──────────────────────────── */
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] {{ display: none !important; }}
.stAppHeader {{ display: none !important; }}

/* ─ Dark base — aurora shows through transparent stApp ───────────────── */
body {{
    background: {C.BG_BASE} !important;
    overflow-x: hidden;
}}
.stApp {{
    background: transparent !important;
    min-height: 100vh;
}}

/* ─ Aurora orbs ───────────────────────────────────────────────────────── */
#aurora-bg {{
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    overflow: hidden;
}}
.aurora-orb {{
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
    will-change: transform;
}}
.aurora-1 {{
    width: 85vmin; height: 85vmin;
    background: radial-gradient(circle at center, rgba(124,58,237,0.48) 0%, transparent 65%);
    filter: blur(90px);
    top: -25%; left: -18%;
    animation: af1 24s ease-in-out infinite alternate;
}}
.aurora-2 {{
    width: 72vmin; height: 72vmin;
    background: radial-gradient(circle at center, rgba(37,99,235,0.38) 0%, transparent 65%);
    filter: blur(85px);
    top: 8%; right: -12%;
    animation: af2 31s ease-in-out infinite alternate;
}}
.aurora-3 {{
    width: 62vmin; height: 62vmin;
    background: radial-gradient(circle at center, rgba(6,182,212,0.28) 0%, transparent 65%);
    filter: blur(75px);
    bottom: -18%; left: 18%;
    animation: af3 20s ease-in-out infinite alternate;
}}
.aurora-4 {{
    width: 48vmin; height: 48vmin;
    background: radial-gradient(circle at center, rgba(168,85,247,0.32) 0%, transparent 65%);
    filter: blur(65px);
    top: 42%; left: 42%;
    animation: af4 38s ease-in-out infinite alternate;
}}
@keyframes af1 {{ to {{ transform: translate(22vw, 16vh) scale(1.14) rotate(8deg);  }} }}
@keyframes af2 {{ to {{ transform: translate(-20vw, -12vh) scale(0.88) rotate(-6deg); }} }}
@keyframes af3 {{ to {{ transform: translate(12vw, -22vh) scale(1.22) rotate(5deg);  }} }}
@keyframes af4 {{ to {{ transform: translate(-10vw, 9vh) scale(1.1) rotate(-10deg);  }} }}

/* ─ Select / input base ───────────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {{
    background: rgba(255,255,255,0.05) !important;
    border-color: {C.GLASS_BORDER} !important;
    border-radius: 12px !important;
    color: {C.TEXT_MAIN} !important;
}}

/* ─ Spinner ───────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {{
    border-top-color: {C.ACCENT_PRIMARY} !important;
}}

/* ─ Progress bar ──────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {{
    background: linear-gradient(90deg, #7c3aed, #a78bfa) !important;
    border-radius: 99px !important;
}}

/* ─ Alerts ────────────────────────────────────────────────────────────── */
[data-testid="stAlert"][kind="info"] {{
    background: rgba(59,130,246,0.12) !important;
    border-color: rgba(59,130,246,0.28) !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="warning"] {{
    background: rgba(251,191,36,0.10) !important;
    border-color: rgba(251,191,36,0.28) !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="error"] {{
    background: rgba(248,113,113,0.12) !important;
    border-color: rgba(248,113,113,0.28) !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="success"] {{
    background: rgba(52,211,153,0.10) !important;
    border-color: rgba(52,211,153,0.28) !important;
    border-radius: 14px !important;
}}

/* ─ Main container ────────────────────────────────────────────────────── */
.block-container {{
    padding: 1rem 0.9rem 5rem !important;
    max-width: 100% !important;
}}
@media (min-width: 640px) {{
    .block-container {{
        padding: 1.5rem 1.5rem 4rem !important;
        max-width: 720px !important;
    }}
}}
@media (min-width: 1024px) {{
    .block-container {{
        padding: 2rem 2rem 3rem !important;
        max-width: 880px !important;
    }}
}}

/* ─ Headings ──────────────────────────────────────────────────────────── */
h1 {{ color: {C.TEXT_MAIN}; font-weight: 700; letter-spacing: -0.5px; font-size: 1.5rem; }}
h2 {{ color: {C.TEXT_MAIN}; font-weight: 600; font-size: 1.15rem; }}
h3 {{ color: {C.TEXT_MAIN}; font-weight: 600; font-size: 1rem; }}
p, li, span {{ color: {C.TEXT_MUTED}; }}

/* ─ Glass card ────────────────────────────────────────────────────────── */
.glass-card {{
    background: {C.GLASS_BG};
    backdrop-filter: blur(28px) saturate(200%);
    -webkit-backdrop-filter: blur(28px) saturate(200%);
    border-radius: 20px;
    border: 1px solid {C.GLASS_BORDER};
    box-shadow: {C.GLASS_SHADOW};
    padding: 1.1rem;
    margin-bottom: 0.85rem;
}}
@media (min-width: 640px) {{
    .glass-card {{
        padding: 1.4rem 1.5rem;
        margin-bottom: 1rem;
    }}
}}

/* ─ Metric cards ──────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {C.GLASS_BG} !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border-radius: 18px !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    box-shadow: {C.GLASS_SHADOW} !important;
    padding: 0.9rem 1rem !important;
    transition: border-color 0.2s ease !important;
}}
[data-testid="metric-container"]:hover {{
    border-color: {C.ACCENT_BORDER} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C.TEXT_MAIN} !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
    letter-spacing: -0.5px !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    color: {C.TEXT_MUTED} !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* ─ Buttons ───────────────────────────────────────────────────────────── */
.stButton > button {{
    background: {C.ACCENT_SOFT} !important;
    color: {C.ACCENT_PRIMARY} !important;
    border: 1px solid {C.ACCENT_BORDER} !important;
    border-radius: 14px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    min-height: 44px !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.20s ease !important;
    width: 100% !important;
    letter-spacing: 0.01em;
}}
.stButton > button:hover {{
    background: rgba(167,139,250,0.16) !important;
    border-color: {C.ACCENT_PRIMARY} !important;
    transform: translateY(-1px) !important;
    box-shadow: {C.ACCENT_GLOW} !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* ─ Chat messages ────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {{
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.30) !important;
    margin-bottom: 0.55rem !important;
    padding: 0.75rem 1rem !important;
    color: {C.TEXT_MAIN} !important;
}}

/* ─ Chat input ───────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {{
    background: rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 0 0 0 rgba(167,139,250,0) !important;
    transition: box-shadow 0.2s ease !important;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: {C.ACCENT_BORDER} !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), {C.ACCENT_GLOW} !important;
}}
[data-testid="stChatInput"] textarea {{
    color: {C.TEXT_MAIN} !important;
    background: transparent !important;
    font-size: 0.95rem !important;
    min-height: 44px !important;
}}

/* ─ Text inputs ──────────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.05) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: {C.TEXT_MAIN} !important;
    font-size: 0.95rem !important;
    min-height: 44px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.20) !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {C.ACCENT_BORDER} !important;
    box-shadow: {C.ACCENT_GLOW} !important;
}}

/* ─ Tabs ──────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {{
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    padding: 0.2rem !important;
    gap: 0.1rem !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.30) !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
}}
[data-baseweb="tab"] {{
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: {C.TEXT_MUTED} !important;
    padding: 0.45rem 0.9rem !important;
    min-height: 40px !important;
    transition: all 0.18s ease !important;
    white-space: nowrap !important;
}}
[aria-selected="true"][data-baseweb="tab"] {{
    background: rgba(167,139,250,0.14) !important;
    color: {C.TEXT_MAIN} !important;
    font-weight: 600 !important;
    box-shadow: inset 0 1px 0 rgba(167,139,250,0.25), 0 2px 8px rgba(0,0,0,0.20) !important;
}}

/* ─ Expander ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: {C.GLASS_BG} !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    border-radius: 16px !important;
    backdrop-filter: blur(20px) !important;
}}

/* ─ Dataframe ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 16px !important;
    overflow: hidden;
}}
[data-testid="stDataFrame"] iframe {{
    border-radius: 16px;
}}

/* ─ Bottom container ──────────────────────────────────────────────────── */
.stBottomBlockContainer {{
    background: rgba(5,5,16,0.88) !important;
    backdrop-filter: blur(28px) !important;
    border-top: 1px solid rgba(255,255,255,0.07) !important;
}}

/* ─ Divider ───────────────────────────────────────────────────────────── */
hr {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 0.85rem 0;
}}

/* ─ Scrollbar ─────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: rgba(167,139,250,0.22);
    border-radius: 2px;
}}

/* ─ Selection ─────────────────────────────────────────────────────────── */
::selection {{
    background: rgba(167,139,250,0.30);
    color: {C.TEXT_MAIN};
}}
</style>
""",
    unsafe_allow_html=True,
)

# ── Aurora animated background ─────────────────────────────────────────────
st.markdown(
    """
<div id="aurora-bg" aria-hidden="true">
    <div class="aurora-orb aurora-1"></div>
    <div class="aurora-orb aurora-2"></div>
    <div class="aurora-orb aurora-3"></div>
    <div class="aurora-orb aurora-4"></div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Top nav header ─────────────────────────────────────────────────────────
st.markdown(
    f"""
<div style="display:flex; align-items:center; gap:0.75rem;
            margin-bottom:1.5rem; padding:0 0.15rem;">
    <div style="
        width:40px; height:40px; border-radius:12px; flex-shrink:0;
        background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
        display:flex; align-items:center; justify-content:center;
        font-size:1.2rem;
        box-shadow: 0 0 28px rgba(124,58,237,0.45), 0 4px 12px rgba(0,0,0,0.4);
    ">🔍</div>
    <div>
        <div style="font-size:1.25rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.5px; line-height:1.2;">FakeShield</div>
        <div style="font-size:0.65rem; color:{C.TEXT_MUTED}; margin-top:1px;
                    letter-spacing:0.10em; text-transform:uppercase;">
            Bluesky Intelligence Platform
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

nav_tab1, nav_tab2, nav_tab3 = st.tabs(
    ["  Fact-Check  ", "  Analytics  ", "  Energy  "]
)


# ── Load corpus data (cached 5 min) ────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    df = get_posts()
    if df.empty:
        return df, None, None, None
    return (
        df,
        top_users_per_category(df),
        trending_keywords(df),
        posts_per_hour(df),
    )


# ── Load emotion data (cached 5 min) ────────────────────────────────────────
@st.cache_data(ttl=300)
def load_emotion_data():
    df = get_emotion_posts()
    if df.empty:
        return df, None, None, None
    return (
        df,
        emotion_distribution(df),
        emotion_by_category(df),
        avg_emotion_score(df),
    )


df_posts, df_category, df_trend, df_hour = load_data()
df_emotion, df_emo_dist, df_emo_cat, df_emo_score = load_emotion_data()
has_data = df_posts is not None and not df_posts.empty


# ── Altair dark-mode theme ─────────────────────────────────────────────────
def glass_chart(chart):
    return (
        chart.configure_view(strokeWidth=0, fill="transparent")
        .configure_axis(
            labelColor=C.TEXT_MUTED,
            titleColor=C.TEXT_MUTED,
            gridColor="rgba(255,255,255,0.05)",
            domainColor="rgba(255,255,255,0.08)",
            labelFont="Inter, sans-serif",
            titleFont="Inter, sans-serif",
        )
        .configure_legend(
            labelColor=C.TEXT_MUTED,
            titleColor=C.TEXT_MUTED,
            labelFont="Inter, sans-serif",
            titleFont="Inter, sans-serif",
            fillColor="transparent",
            strokeColor="rgba(255,255,255,0.08)",
        )
        .configure_title(
            color=C.TEXT_MAIN,
            font="Inter, sans-serif",
            fontSize=13,
            fontWeight=600,
        )
    )


# ══════════════════════════════════════════════════════════════════════════
# PAGE — FACT-CHECK CHATBOT
# ══════════════════════════════════════════════════════════════════════════
with nav_tab1:
    st.markdown(
        f"""
    <div class="glass-card">
        <div style="font-size:1.1rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.3px; margin-bottom:4px;">
            Fact-Check a Claim
        </div>
        <div style="font-size:0.84rem; color:{C.TEXT_MUTED}; line-height:1.6;">
            Paste any post or headline — the model checks it against
            the Bluesky corpus and returns a verdict.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("is_html"):
                st.html(msg["content"])
            else:
                st.markdown(msg["content"])

    user_input = st.chat_input("Paste a claim, post, or headline…")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Checking…"):
                result = send_message_api(user_input)

            verdict = result["verdict"]
            color = result["color"]
            expl = result["explanation"]
            prob = result["probability"]
            source = result["based_on"]

            source_label = {
                "kmeans": "◆ KMeans classifier",
                "rag": "◆ Bluesky corpus",
                "general_knowledge": "◆ General knowledge",
                "error": "◆ API error",
            }.get(source, f"◆ {source}")

            prob_bar = ""
            if prob is not None:
                pct = int(prob * 100)
                prob_bar = f"""
                <div style="margin:0.75rem 0 0.4rem;">
                    <div style="display:flex; justify-content:space-between;
                                font-size:0.73rem; color:{C.TEXT_MUTED};
                                margin-bottom:6px; letter-spacing:0.04em;
                                text-transform:uppercase;">
                        <span>Confidence</span><span>{pct}%</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.07); border-radius:99px;
                                height:5px; overflow:hidden;">
                        <div style="width:{pct}%; height:100%;
                                    background:linear-gradient(90deg, {color}88, {color});
                                    border-radius:99px;
                                    box-shadow: 0 0 8px {color}60;">
                        </div>
                    </div>
                </div>"""

            html = f"""
            <div style="
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 18px;
                padding: 1rem 1.15rem;
                backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.4),
                            inset 0 1px 0 rgba(255,255,255,0.06);
            ">
                <div style="
                    display: inline-flex; align-items: center; gap: 6px;
                    background: {color}18;
                    border: 1.5px solid {color}55;
                    border-radius: 99px;
                    padding: 0.22rem 0.9rem;
                    font-size: 0.76rem; font-weight: 700;
                    color: {color};
                    letter-spacing: 0.06em; text-transform: uppercase;
                    box-shadow: 0 0 14px {color}30;
                ">
                    {verdict}
                </div>
                {prob_bar}
                <div style="font-size:0.9rem; color:{C.TEXT_MAIN};
                            line-height:1.7; margin-top:0.55rem;">
                    {expl}
                </div>
                <div style="font-size:0.70rem; color:{C.TEXT_SUBTLE};
                            margin-top:0.65rem; padding-top:0.55rem;
                            border-top:1px solid rgba(255,255,255,0.06);
                            letter-spacing:0.04em;">
                    {source_label}
                </div>
            </div>"""

            st.html(html)
            st.session_state.messages.append(
                {"role": "assistant", "content": html, "is_html": True}
            )

    if not st.session_state.messages:
        st.markdown(
            f"""
        <div style="text-align:center; padding:3rem 0 1.5rem;
                    color:{C.TEXT_SUBTLE}; font-size:0.86rem; letter-spacing:0.02em;">
            ↑ Enter a claim above to get started
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("↺  Clear conversation", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# PAGE — ANALYTICS
# ══════════════════════════════════════════════════════════════════════════
with nav_tab2:
    st.markdown(
        f"""
    <div style="font-size:1.1rem; font-weight:700; color:{C.TEXT_MAIN};
                letter-spacing:-0.3px; margin-bottom:1rem;">
        Analytics
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not has_data:
        st.markdown(
            f"""
        <div class="glass-card" style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📭</div>
            <div style="color:{C.TEXT_MUTED}; font-size:0.9rem;">
                No data yet — run the ingestion pipeline first.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    top_kw = df_trend.iloc[0]["keyword"] if not df_trend.empty else "—"

    r1c1, r1c2 = st.columns(2)
    r1c1.metric("Total Posts", f"{len(df_posts):,}")
    r1c2.metric("Authors", f"{df_posts['username'].nunique():,}")

    r2c1, r2c2 = st.columns(2)
    r2c1.metric("Categories", f"{df_posts['category'].nunique():,}")
    r2c2.metric("Top Keyword", top_kw)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if st.button("↺  Reload data", key="reload_data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Keywords", "Authors", "By Hour", "Emotions"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        base = alt.Chart(df_trend).encode(
            y=alt.Y("keyword:N", sort="-x", title="", axis=alt.Axis(labelLimit=140)),
            x=alt.X("count:Q", title="Occurrences"),
            tooltip=["keyword:N", "count:Q"],
        )
        chart = (
            base.mark_bar(
                color=C.ACCENT_PRIMARY,
                opacity=0.20,
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
            )
            + base.mark_point(filled=True, size=70, color=C.ACCENT_PRIMARY)
            + base.mark_rule(color=C.ACCENT_PRIMARY, opacity=0.35, strokeWidth=1.5)
        ).properties(height=380)
        st.altair_chart(glass_chart(chart), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        categories = df_category["category"].unique().tolist()
        for cat in categories:
            df_cat = df_category[df_category["category"] == cat].head(8)
            pie = (
                alt.Chart(df_cat)
                .mark_arc(innerRadius=48, outerRadius=92)
                .encode(
                    theta=alt.Theta("post_count:Q"),
                    color=alt.Color(
                        "username:N",
                        scale=alt.Scale(scheme="viridis"),
                        legend=alt.Legend(orient="bottom", labelLimit=120, columns=2),
                    ),
                    tooltip=["username:N", "post_count:Q"],
                )
                .properties(title=cat, height=240)
            )
            st.altair_chart(glass_chart(pie), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        area = (
            alt.Chart(df_hour)
            .mark_area(
                color=C.ACCENT_PRIMARY,
                opacity=0.12,
                line={"color": C.ACCENT_PRIMARY, "strokeWidth": 2},
                point=alt.OverlayMarkDef(color=C.ACCENT_PRIMARY, filled=True, size=55),
            )
            .encode(
                x=alt.X(
                    "hour:Q",
                    title="Hour of day",
                    axis=alt.Axis(tickCount=12, format="d"),
                ),
                y=alt.Y("count:Q", title="Posts"),
                tooltip=["hour:Q", "count:Q"],
            )
            .properties(height=260)
        )
        st.altair_chart(glass_chart(area), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        # Ekman palette — consistent across both charts
        EMOTION_COLORS = {
            "joy": "#34d399",
            "surprise": "#c084fc",
            "neutral": "#7878a0",
            "fear": "#fb923c",
            "sadness": "#60a5fa",
            "anger": "#f87171",
            "disgust": "#94a3b8",
        }

        if df_emo_dist is None or df_emo_dist.empty:
            st.markdown(
                f"""
            <div class="glass-card" style="text-align:center; padding:2.5rem 1rem;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">🧠</div>
                <div style="color:{C.TEXT_MUTED}; font-size:0.88rem;">
                    No emotion data yet — run the
                    <code>emotion_classification</code> pipeline first.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            emo_domain = df_emo_dist["emotion"].tolist()
            emo_range = [EMOTION_COLORS.get(e, C.ACCENT_PRIMARY) for e in emo_domain]

            # ── Top metric: dominant emotion ──────────────────────────────
            dominant = df_emo_dist.iloc[0]["emotion"].capitalize()
            total_emoed = int(df_emo_dist["count"].sum())
            ec1, ec2 = st.columns(2)
            ec1.metric("Posts analysed", f"{total_emoed:,}")
            ec2.metric("Dominant emotion", dominant)
            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

            # ── Chart 1: donut — overall emotion distribution ─────────────
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            donut = (
                alt.Chart(df_emo_dist)
                .mark_arc(
                    innerRadius=55,
                    outerRadius=110,
                    stroke="rgba(0,0,0,0.15)",
                    strokeWidth=1,
                )
                .encode(
                    theta=alt.Theta("count:Q"),
                    color=alt.Color(
                        "emotion:N",
                        scale=alt.Scale(domain=emo_domain, range=emo_range),
                        legend=alt.Legend(
                            orient="right",
                            title=None,
                            labelFontSize=12,
                            symbolSize=120,
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("emotion:N", title="Emotion"),
                        alt.Tooltip("count:Q", title="Posts"),
                    ],
                )
                .properties(height=280, title="Emotion distribution")
            )
            st.altair_chart(glass_chart(donut), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Chart 2: bar — avg BERT confidence per emotion ────────────
            if df_emo_score is not None and not df_emo_score.empty:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                score_colors = [
                    EMOTION_COLORS.get(e, C.ACCENT_PRIMARY)
                    for e in df_emo_score["emotion"].tolist()
                ]
                conf_bar = (
                    alt.Chart(df_emo_score)
                    .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                    .encode(
                        y=alt.Y(
                            "emotion:N",
                            sort="-x",
                            title="",
                            axis=alt.Axis(labelLimit=110),
                        ),
                        x=alt.X(
                            "avg_score:Q",
                            title="Avg BERT confidence",
                            scale=alt.Scale(domain=[0, 1]),
                        ),
                        color=alt.Color(
                            "emotion:N",
                            scale=alt.Scale(
                                domain=df_emo_score["emotion"].tolist(),
                                range=score_colors,
                            ),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("emotion:N", title="Emotion"),
                            alt.Tooltip(
                                "avg_score:Q", title="Avg confidence", format=".3f"
                            ),
                        ],
                    )
                    .properties(
                        height=220, title="Average model confidence per emotion"
                    )
                )
                st.altair_chart(glass_chart(conf_bar), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Chart 3: heatmap — emotion × category ─────────────────────
            if df_emo_cat is not None and not df_emo_cat.empty:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                heatmap = (
                    alt.Chart(df_emo_cat)
                    .mark_rect(cornerRadius=4)
                    .encode(
                        x=alt.X("emotion:N", title="", axis=alt.Axis(labelAngle=-30)),
                        y=alt.Y("category:N", title=""),
                        color=alt.Color(
                            "count:Q",
                            scale=alt.Scale(scheme="purples"),
                            legend=alt.Legend(title="Posts"),
                        ),
                        tooltip=[
                            alt.Tooltip("category:N", title="Category"),
                            alt.Tooltip("emotion:N", title="Emotion"),
                            alt.Tooltip("count:Q", title="Posts"),
                        ],
                    )
                    .properties(
                        height=max(160, df_emo_cat["category"].nunique() * 42),
                        title="Emotion breakdown by category",
                    )
                )
                st.altair_chart(glass_chart(heatmap), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
    <div style="text-align:center; margin-top:2.5rem;
                font-size:0.68rem; color:{C.TEXT_SUBTLE}; letter-spacing:0.06em;">
        M1 DATA SCIENCE · 2024
    </div>
    """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# PAGE — ENERGY REPORT
# ══════════════════════════════════════════════════════════════════════════
with nav_tab3:
    st.markdown(
        f"""
    <div style="font-size:1.1rem; font-weight:700; color:{C.TEXT_MAIN};
                letter-spacing:-0.3px; margin-bottom:1rem;">
        ⚡ Energy Report
    </div>
    """,
        unsafe_allow_html=True,
    )

    @st.cache_data(ttl=60)
    def load_energy():
        df = get_energy_df()
        if df.empty:
            return df, None, None, None
        return df, energy_by_pipeline(df), energy_by_node(df), energy_timeline(df)

    df_energy, df_by_pipeline, df_by_node, df_timeline = load_energy()

    if st.button("↺  Reload energy data", key="reload_energy_top"):
        st.cache_data.clear()
        st.rerun()

    if df_energy.empty:
        st.markdown(
            f"""
        <div class="glass-card" style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔋</div>
            <div style="color:{C.TEXT_MUTED}; font-size:0.9rem;">
                No energy data yet — run a pipeline first.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        total_wh = df_energy["energy_wh"].sum()
        total_co2 = df_energy["co2_mg"].sum()
        total_runs = df_energy["run_id"].nunique()
        heaviest = df_by_node.iloc[0]["node_name"] if not df_by_node.empty else "—"

        c1, c2 = st.columns(2)
        c1.metric("Total Energy", f"{total_wh:.2f} Wh")
        c2.metric("Total CO₂", f"{total_co2:.1f} mg")

        c3, c4 = st.columns(2)
        c3.metric("Pipeline Runs", str(total_runs))
        c4.metric("Heaviest Node", heaviest)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        # Neon pipeline colours for dark mode
        PIPELINE_COLORS = {
            "ingest_from_bluesky": "#60a5fa",
            "nlp_transform": "#c084fc",
            "vectorisation": "#34d399",
            "default": "#fbbf24",
        }

        etab1, etab2, etab3, etab4 = st.tabs(
            ["By Pipeline", "By Node", "Breakdown", "Timeline"]
        )

        with etab1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            p_colors = [
                PIPELINE_COLORS.get(p, C.ACCENT_PRIMARY)
                for p in df_by_pipeline["pipeline_name"].tolist()
            ]
            bar_pipeline = (
                alt.Chart(df_by_pipeline)
                .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
                .encode(
                    y=alt.Y(
                        "pipeline_name:N",
                        sort="-x",
                        title="",
                        axis=alt.Axis(labelLimit=160),
                    ),
                    x=alt.X("total_wh:Q", title="Energy (Wh)"),
                    color=alt.Color(
                        "pipeline_name:N",
                        scale=alt.Scale(
                            domain=df_by_pipeline["pipeline_name"].tolist(),
                            range=p_colors,
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("pipeline_name:N", title="Pipeline"),
                        alt.Tooltip("total_wh:Q", title="Energy (Wh)", format=".4f"),
                        alt.Tooltip("total_co2_mg:Q", title="CO₂ (mg)", format=".2f"),
                        alt.Tooltip("runs:Q", title="Runs"),
                        alt.Tooltip(
                            "total_duration_s:Q", title="Duration (s)", format=".1f"
                        ),
                    ],
                )
                .properties(height=max(120, len(df_by_pipeline) * 55))
            )
            st.altair_chart(glass_chart(bar_pipeline), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with etab2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            n_colors = [
                PIPELINE_COLORS.get(p, C.ACCENT_PRIMARY)
                for p in df_by_node["pipeline_name"].tolist()
            ]
            bar_node = (
                alt.Chart(df_by_node)
                .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
                .encode(
                    y=alt.Y(
                        "node_name:N",
                        sort="-x",
                        title="",
                        axis=alt.Axis(labelLimit=200),
                    ),
                    x=alt.X("total_wh:Q", title="Total Energy (Wh)"),
                    color=alt.Color(
                        "pipeline_name:N",
                        scale=alt.Scale(
                            domain=list(PIPELINE_COLORS.keys()),
                            range=list(PIPELINE_COLORS.values()),
                        ),
                        legend=alt.Legend(title="Pipeline", orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("node_name:N", title="Node"),
                        alt.Tooltip("pipeline_name:N", title="Pipeline"),
                        alt.Tooltip("total_wh:Q", title="Total (Wh)", format=".4f"),
                        alt.Tooltip("avg_wh:Q", title="Avg/run (Wh)", format=".4f"),
                        alt.Tooltip(
                            "avg_duration_s:Q", title="Avg duration (s)", format=".2f"
                        ),
                        alt.Tooltip("runs:Q", title="Runs"),
                    ],
                )
                .properties(height=max(180, len(df_by_node) * 38))
            )
            st.altair_chart(glass_chart(bar_node), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with etab3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            breakdown = df_by_node[
                ["node_name", "avg_cpu_wh", "avg_ram_wh", "avg_gpu_wh"]
            ].melt(id_vars="node_name", var_name="component", value_name="avg_wh")
            breakdown["component"] = breakdown["component"].map(
                {"avg_cpu_wh": "CPU", "avg_ram_wh": "RAM", "avg_gpu_wh": "GPU"}
            )
            stacked = (
                alt.Chart(breakdown)
                .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                .encode(
                    y=alt.Y("node_name:N", title="", axis=alt.Axis(labelLimit=200)),
                    x=alt.X("avg_wh:Q", title="Avg Energy/run (Wh)", stack="zero"),
                    color=alt.Color(
                        "component:N",
                        scale=alt.Scale(
                            domain=["CPU", "RAM", "GPU"],
                            range=["#60a5fa", "#c084fc", "#34d399"],
                        ),
                        legend=alt.Legend(title="Component", orient="bottom"),
                    ),
                    order=alt.Order("component:N"),
                    tooltip=[
                        alt.Tooltip("node_name:N", title="Node"),
                        alt.Tooltip("component:N", title="Component"),
                        alt.Tooltip("avg_wh:Q", title="Avg (Wh)", format=".5f"),
                    ],
                )
                .properties(height=max(180, len(df_by_node) * 38))
            )
            st.altair_chart(glass_chart(stacked), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with etab4:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if df_timeline is not None and not df_timeline.empty:
                scatter = (
                    alt.Chart(df_timeline)
                    .mark_point(filled=True, size=80, opacity=0.80)
                    .encode(
                        x=alt.X("timestamp:T", title="Date"),
                        y=alt.Y("total_wh:Q", title="Energy / run (Wh)"),
                        color=alt.Color(
                            "pipeline_name:N",
                            scale=alt.Scale(
                                domain=list(PIPELINE_COLORS.keys()),
                                range=list(PIPELINE_COLORS.values()),
                            ),
                            legend=alt.Legend(title="Pipeline", orient="bottom"),
                        ),
                        tooltip=[
                            alt.Tooltip(
                                "timestamp:T", title="Date", format="%Y-%m-%d %H:%M"
                            ),
                            alt.Tooltip("pipeline_name:N", title="Pipeline"),
                            alt.Tooltip(
                                "total_wh:Q", title="Energy (Wh)", format=".4f"
                            ),
                            alt.Tooltip(
                                "total_co2_mg:Q", title="CO₂ (mg)", format=".2f"
                            ),
                        ],
                    )
                    .properties(height=280)
                )
                st.altair_chart(glass_chart(scatter), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
        <div style="font-size:0.78rem; font-weight:600; color:{C.TEXT_MUTED};
                    text-transform:uppercase; letter-spacing:0.07em;
                    margin:1.25rem 0 0.6rem;">
            Recent runs
        </div>
        """,
            unsafe_allow_html=True,
        )
        display_cols = {
            "timestamp": "Time",
            "pipeline_name": "Pipeline",
            "node_name": "Node",
            "energy_wh": "Energy (Wh)",
            "co2_mg": "CO₂ (mg)",
            "duration_s": "Duration (s)",
        }
        df_display = (
            df_energy[list(display_cols.keys())]
            .head(40)
            .rename(columns=display_cols)
            .assign(
                **{
                    "Energy (Wh)": lambda d: d["Energy (Wh)"].map("{:.4f}".format),
                    "CO₂ (mg)": lambda d: d["CO₂ (mg)"].map("{:.3f}".format),
                    "Duration (s)": lambda d: d["Duration (s)"].map("{:.2f}".format),
                    "Time": lambda d: d["Time"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
