import altair as alt
import streamlit as st
from streamlit_color_chart import ColorChart
from streamlit_logic import (
    emotion_distribution,
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

# ── Global CSS (mobile-first) ──────────────────────────────────────────────
st.markdown(
    f"""
<style>
/* ─ Fonts ────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
}}

/* ─ Hide toolbar / status widget ─────────────────────────────────────── */
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {{
    display: none !important;
}}

/* ─ Background ───────────────────────────────────────────────────────── */
.stApp {{
    background: {C.BG_GRADIENT};
    min-height: 100vh;
}}

/* ─ Pastel tint on select / multiselect ──────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {{
    background: rgba(200, 218, 255, 0.35) !important;
    border-color: {C.ACCENT_BORDER} !important;
    border-radius: 12px !important;
}}

/* ─ Pastel spinner ───────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {{
    border-top-color: {C.ACCENT_PRIMARY} !important;
}}

/* ─ Pastel progress bar ──────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {{
    background: linear-gradient(90deg, #b5ccff, #c9b8ff) !important;
    border-radius: 99px !important;
}}

/* ─ Pastel info / warning / error alerts ─────────────────────────────── */
[data-testid="stAlert"][kind="info"] {{
    background: rgba(180, 210, 255, 0.40) !important;
    border-color: #93c5fd !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="warning"] {{
    background: rgba(253, 230, 138, 0.40) !important;
    border-color: #fcd34d !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="error"] {{
    background: rgba(252, 165, 165, 0.40) !important;
    border-color: #fca5a5 !important;
    border-radius: 14px !important;
}}
[data-testid="stAlert"][kind="success"] {{
    background: rgba(110, 231, 183, 0.35) !important;
    border-color: #6ee7b7 !important;
    border-radius: 14px !important;
}}

/* ─ Hide sidebar toggle ──────────────────────────────────────────────── */
[data-testid="collapsedControl"] {{ display: none !important; }}
section[data-testid="stSidebar"] {{ display: none !important; }}

/* ─ Header — hidden ──────────────────────────────────────────────────── */
.stAppHeader {{
    display: none !important;
}}

/* ─ Main container — mobile first ───────────────────────────────────── */
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
        max-width: 860px !important;
    }}
}}

/* ─ Headings ─────────────────────────────────────────────────────────── */
h1 {{ color: {C.TEXT_MAIN}; font-weight: 700; letter-spacing: -0.4px; font-size: 1.5rem; }}
h2 {{ color: {C.TEXT_MAIN}; font-weight: 600; font-size: 1.15rem; }}
h3 {{ color: {C.TEXT_MAIN}; font-weight: 600; font-size: 1rem; }}

/* ─ Glass card ───────────────────────────────────────────────────────── */
.glass-card {{
    background: {C.GLASS_BG};
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-radius: 20px;
    border: 1px solid {C.GLASS_BORDER};
    box-shadow: {C.GLASS_SHADOW};
    padding: 1.1rem 1.1rem;
    margin-bottom: 0.85rem;
}}
@media (min-width: 640px) {{
    .glass-card {{
        padding: 1.4rem 1.5rem;
        margin-bottom: 1rem;
    }}
}}

/* ─ Stat cards ───────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {C.GLASS_BG} !important;
    backdrop-filter: blur(16px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
    border-radius: 16px !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    box-shadow: {C.GLASS_SHADOW} !important;
    padding: 0.85rem 1rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C.TEXT_MAIN} !important;
    font-weight: 700 !important;
    font-size: 1.5rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    color: {C.TEXT_MUTED} !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ─ Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {{
    background: {C.ACCENT_SOFT} !important;
    color: {C.ACCENT_PRIMARY} !important;
    border: 1px solid {C.ACCENT_BORDER} !important;
    border-radius: 14px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    min-height: 44px !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
}}
.stButton > button:hover {{
    background: rgba(123,156,244,0.22) !important;
    border-color: {C.ACCENT_PRIMARY} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(123,156,244,0.22) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* ─ Chat messages ────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {{
    background: rgba(255,255,255,0.65) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.90) !important;
    box-shadow: 0 2px 10px rgba(110,120,200,0.07) !important;
    margin-bottom: 0.5rem !important;
    padding: 0.7rem 0.9rem !important;
}}

/* ─ Chat input ───────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {{
    background: rgba(255,255,255,0.82) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.92) !important;
    box-shadow: 0 4px 20px rgba(110,120,200,0.10) !important;
}}
[data-testid="stChatInput"] textarea {{
    color: {C.TEXT_MAIN} !important;
    background: transparent !important;
    font-size: 0.95rem !important;
    min-height: 44px !important;
}}

/* ─ Text inputs ──────────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.78) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.88) !important;
    color: {C.TEXT_MAIN} !important;
    font-size: 0.95rem !important;
    min-height: 44px !important;
    box-shadow: 0 2px 8px rgba(110,120,200,0.06) !important;
}}

/* ─ Tabs ─────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {{
    background: rgba(255,255,255,0.55) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.85) !important;
    padding: 0.2rem !important;
    gap: 0.1rem !important;
    box-shadow: 0 2px 8px rgba(110,120,200,0.07) !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
}}
[data-baseweb="tab"] {{
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: {C.TEXT_MUTED} !important;
    padding: 0.45rem 0.85rem !important;
    min-height: 40px !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
}}
[aria-selected="true"][data-baseweb="tab"] {{
    background: rgba(255,255,255,0.92) !important;
    color: {C.TEXT_MAIN} !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(110,120,200,0.12) !important;
}}

/* ─ Expander ─────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: {C.GLASS_BG} !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
}}

/* ─ Bottom container ─────────────────────────────────────────────────── */
.stBottomBlockContainer {{
    background: rgba(230,238,255,0.88) !important;
    backdrop-filter: blur(20px) !important;
    border-top: 1px solid rgba(255,255,255,0.85) !important;
}}

/* ─ Divider ──────────────────────────────────────────────────────────── */
hr {{
    border: none;
    border-top: 1px solid rgba(110,120,200,0.10);
    margin: 0.85rem 0;
}}

/* ─ Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: rgba(110,120,200,0.18);
    border-radius: 2px;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ── Top nav header ─────────────────────────────────────────────────────────
st.markdown(
    f"""
<div style="display:flex; align-items:center; justify-content:space-between;
            margin-bottom:1.25rem;">
    <div>
        <div style="font-size:1.3rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.4px; line-height:1.2;">🔍 FakeShield</div>
        <div style="font-size:0.72rem; color:{C.TEXT_MUTED}; margin-top:1px;">
            Bluesky Intelligence Platform
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Top-level navigation (mobile-friendly tabs)
nav_tab1, nav_tab2 = st.tabs(["  Fact-Check  ", "  Analytics  "])


# ── Load data (cached) ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    df = get_posts()
    if df.empty:
        return df, None, None, None, None
    return (
        df,
        top_users_per_category(df),
        trending_keywords(df),
        posts_per_hour(df),
        emotion_distribution(df),
    )


df_posts, df_category, df_trend, df_hour, df_emotion = load_data()
has_data = df_posts is not None and not df_posts.empty


# ── Altair theme helper ────────────────────────────────────────────────────
def glass_chart(chart):
    return (
        chart.configure_view(strokeWidth=0, fill="transparent")
        .configure_axis(
            labelColor=C.TEXT_MUTED,
            titleColor=C.TEXT_MUTED,
            gridColor="rgba(110,120,200,0.08)",
            domainColor="rgba(110,120,200,0.15)",
            labelFont="Inter, sans-serif",
            titleFont="Inter, sans-serif",
        )
        .configure_legend(
            labelColor=C.TEXT_MUTED,
            titleColor=C.TEXT_MUTED,
            labelFont="Inter, sans-serif",
            titleFont="Inter, sans-serif",
        )
    )


# ══════════════════════════════════════════════════════════════════════════
# PAGE — FACT-CHECK CHATBOT
# ══════════════════════════════════════════════════════════════════════════
with nav_tab1:
    st.markdown(
        f"""
    <div class="glass-card">
        <div style="font-size:1.15rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.3px;">Fact-Check a Claim</div>
        <div style="font-size:0.85rem; color:{C.TEXT_MUTED}; margin-top:3px;
                    line-height:1.5;">
            Paste any post or headline — the model checks it against
            the Bluesky corpus and gives a verdict.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("is_html"):
                st.html(msg["content"])
            else:
                st.markdown(msg["content"])

    # Input
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
                "rag": "🔵 Bluesky corpus",
                "general_knowledge": "🟡 General knowledge",
                "error": "🔴 API error",
            }.get(source, f"· {source}")

            prob_bar = ""
            if prob is not None:
                pct = int(prob * 100)
                prob_bar = f"""
                <div style="margin:0.65rem 0 0.35rem;">
                    <div style="display:flex; justify-content:space-between;
                                font-size:0.75rem; color:{C.TEXT_MUTED};
                                margin-bottom:5px;">
                        <span>Confidence</span><span>{pct}%</span>
                    </div>
                    <div style="background:rgba(110,120,200,0.12); border-radius:99px;
                                height:6px; overflow:hidden;">
                        <div style="width:{pct}%; height:100%;
                                    background:{color};
                                    border-radius:99px;">
                        </div>
                    </div>
                </div>"""

            html = f"""
            <div style="background:rgba(255,255,255,0.60);
                        border:1px solid rgba(255,255,255,0.90);
                        border-radius:18px; padding:1rem 1.1rem;
                        backdrop-filter:blur(14px);
                        -webkit-backdrop-filter:blur(14px);">
                <div style="display:inline-block; background:{color}30;
                            border:1.5px solid {color}70; border-radius:99px;
                            padding:0.2rem 0.9rem; font-size:0.78rem;
                            font-weight:700; color:{C.TEXT_MAIN};
                            letter-spacing:0.04em; text-transform:uppercase;">
                    {verdict}
                </div>
                {prob_bar}
                <div style="font-size:0.9rem; color:{C.TEXT_MAIN};
                            line-height:1.65; margin-top:0.5rem;">
                    {expl}
                </div>
                <div style="font-size:0.72rem; color:{C.TEXT_SUBTLE};
                            margin-top:0.65rem; padding-top:0.55rem;
                            border-top:1px solid rgba(110,120,200,0.10);">
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
        <div style="text-align:center; padding:2.5rem 0 1rem;
                    color:{C.TEXT_SUBTLE}; font-size:0.88rem;">
            ↑ Enter a claim above to get started
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Reload button
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
    <div style="font-size:1.15rem; font-weight:700; color:{C.TEXT_MAIN};
                letter-spacing:-0.3px; margin-bottom:1rem;">
        Analytics
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not has_data:
        st.markdown(
            f"""
        <div class="glass-card" style="text-align:center; padding:2.5rem 1rem;">
            <div style="font-size:2rem;">📭</div>
            <div style="color:{C.TEXT_MUTED}; margin-top:0.5rem; font-size:0.9rem;">
                No data yet — run the ingestion pipeline first.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Stat cards — 2×2 on mobile, 4×1 on wider screens ─────────────────
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

    # ── Chart tabs ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Keywords", "Authors", "By Hour", "Emotions"]
    )

    # ── Tab 1: Keywords ───────────────────────────────────────────────────
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
                opacity=0.22,
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
            )
            + base.mark_point(filled=True, size=70, color=C.ACCENT_PRIMARY)
            + base.mark_rule(color=C.ACCENT_PRIMARY, opacity=0.35, strokeWidth=1.5)
        ).properties(height=380)
        st.altair_chart(glass_chart(chart), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 2: Top authors ────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        categories = df_category["category"].unique().tolist()
        for cat in categories:
            df_cat = df_category[df_category["category"] == cat].head(8)
            pie = (
                alt.Chart(df_cat)
                .mark_arc(innerRadius=45, outerRadius=90)
                .encode(
                    theta=alt.Theta("post_count:Q"),
                    color=alt.Color(
                        "username:N",
                        scale=alt.Scale(scheme="pastel1"),
                        legend=alt.Legend(orient="bottom", labelLimit=120, columns=2),
                    ),
                    tooltip=["username:N", "post_count:Q"],
                )
                .properties(title=cat, height=240)
            )
            st.altair_chart(glass_chart(pie), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3: Posts by hour ──────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        area = (
            alt.Chart(df_hour)
            .mark_area(
                color=C.ACCENT_PRIMARY,
                opacity=0.14,
                line={"color": C.ACCENT_PRIMARY, "strokeWidth": 2},
                point=alt.OverlayMarkDef(
                    color=C.ACCENT_PRIMARY, filled=True, size=55
                ),
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

    # ── Tab 4: Emotions ───────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if df_emotion is not None and not df_emotion.empty:
            EMOTION_COLORS = {
                "joy": "#86efac",
                "sadness": "#93c5fd",
                "anger": "#fca5a5",
                "fear": "#fdba74",
                "love": "#f9a8d4",
                "surprise": "#d8b4fe",
            }
            color_range = [
                EMOTION_COLORS.get(e, C.ACCENT_PRIMARY)
                for e in df_emotion["emotion"].tolist()
            ]
            bars = (
                alt.Chart(df_emotion)
                .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
                .encode(
                    y=alt.Y(
                        "emotion:N",
                        sort="-x",
                        title="",
                        axis=alt.Axis(labelLimit=110),
                    ),
                    x=alt.X("count:Q", title="Posts"),
                    color=alt.Color(
                        "emotion:N",
                        scale=alt.Scale(
                            domain=df_emotion["emotion"].tolist(),
                            range=color_range,
                        ),
                        legend=None,
                    ),
                    tooltip=["emotion:N", "count:Q"],
                )
                .properties(height=260)
            )
            st.altair_chart(glass_chart(bars), use_container_width=True)
        else:
            st.markdown(
                f"""
            <div style="text-align:center; padding:2rem; color:{C.TEXT_MUTED};
                        font-size:0.88rem;">
                No emotion data yet — run the NLP pipeline first.
            </div>
            """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
    <div style="text-align:center; margin-top:2rem;
                font-size:0.7rem; color:{C.TEXT_SUBTLE};">
        M1 Data Science · 2024
    </div>
    """,
        unsafe_allow_html=True,
    )
