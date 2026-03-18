import streamlit as st
import altair as alt

from streamlit_logic import (
    send_message_api,
    get_posts,
    top_users_per_category,
    trending_keywords,
    posts_per_hour,
    emotion_distribution,
)
from streamlit_color_chart import ColorChart
from streamlit_config import StreamlitConfig

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fake News Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

C = ColorChart

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ─ Base ─────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
}}

.stApp {{
    background: {C.BG_GRADIENT};
    min-height: 100vh;
}}

/* ─ Header ───────────────────────────────────────────────────────────── */
.stAppHeader {{
    background: rgba(255,255,255,0.72) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border-bottom: 1px solid rgba(255,255,255,0.8) !important;
    box-shadow: 0 1px 0 rgba(0,0,0,0.06) !important;
}}

/* ─ Sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: rgba(255,255,255,0.60) !important;
    backdrop-filter: blur(28px) saturate(200%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(200%) !important;
    border-right: 1px solid rgba(255,255,255,0.80) !important;
    box-shadow: 2px 0 24px rgba(0,0,0,0.06) !important;
}}
section[data-testid="stSidebar"] * {{
    color: {C.TEXT_MAIN} !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    background: rgba(255,255,255,0.5);
    border: 1px solid rgba(255,255,255,0.8);
    border-radius: 12px;
    padding: 0.45rem 0.85rem;
    margin-bottom: 0.25rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: {C.TEXT_MAIN} !important;
    cursor: pointer;
    transition: all 0.18s ease;
    display: block;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(0,122,255,0.08);
    border-color: {C.ACCENT_BORDER};
    color: {C.ACCENT_PRIMARY} !important;
}}
section[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
section[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
    background: {C.ACCENT_SOFT};
    border-color: {C.ACCENT_BORDER};
    color: {C.ACCENT_PRIMARY} !important;
    font-weight: 600;
}}

/* ─ Main content padding ─────────────────────────────────────────────── */
.block-container {{
    padding: 2rem 2.5rem 2rem !important;
    max-width: 1200px;
}}

/* ─ Headings ─────────────────────────────────────────────────────────── */
h1 {{ color: {C.TEXT_MAIN}; font-weight: 700; letter-spacing: -0.5px; }}
h2 {{ color: {C.TEXT_MAIN}; font-weight: 600; letter-spacing: -0.3px; }}
h3 {{ color: {C.TEXT_MAIN}; font-weight: 600; }}

/* ─ Glass card ───────────────────────────────────────────────────────── */
.glass-card {{
    background: {C.GLASS_BG};
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-radius: 20px;
    border: 1px solid {C.GLASS_BORDER};
    box-shadow: {C.GLASS_SHADOW};
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}}
.glass-card-sm {{
    background: {C.GLASS_BG};
    backdrop-filter: blur(16px) saturate(160%);
    -webkit-backdrop-filter: blur(16px) saturate(160%);
    border-radius: 16px;
    border: 1px solid {C.GLASS_BORDER};
    box-shadow: 0 4px 16px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.03);
    padding: 1.25rem 1.5rem;
}}

/* ─ Stat cards ───────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {C.GLASS_BG} !important;
    backdrop-filter: blur(16px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
    border-radius: 16px !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
    padding: 1rem 1.25rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C.TEXT_MAIN} !important;
    font-weight: 700 !important;
    font-size: 1.9rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    color: {C.TEXT_MUTED} !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

/* ─ Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {{
    background: {C.ACCENT_SOFT} !important;
    color: {C.ACCENT_PRIMARY} !important;
    border: 1px solid {C.ACCENT_BORDER} !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}}
.stButton > button:hover {{
    background: rgba(0,122,255,0.18) !important;
    border-color: {C.ACCENT_PRIMARY} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,122,255,0.18) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* ─ Chat messages ────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {{
    background: rgba(255,255,255,0.62) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.85) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    margin-bottom: 0.6rem !important;
    padding: 0.75rem 1rem !important;
}}

/* ─ Chat input ───────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {{
    background: rgba(255,255,255,0.80) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.90) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07) !important;
}}
[data-testid="stChatInput"] textarea {{
    color: {C.TEXT_MAIN} !important;
    background: transparent !important;
}}

/* ─ Text inputs ──────────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.75) !important;
    backdrop-filter: blur(8px) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.85) !important;
    color: {C.TEXT_MAIN} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}}

/* ─ Tabs ─────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {{
    background: rgba(255,255,255,0.50) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.80) !important;
    padding: 0.25rem !important;
    gap: 0.15rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}}
[data-baseweb="tab"] {{
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: {C.TEXT_MUTED} !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
}}
[aria-selected="true"][data-baseweb="tab"] {{
    background: rgba(255,255,255,0.90) !important;
    color: {C.TEXT_MAIN} !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}}

/* ─ Divider ──────────────────────────────────────────────────────────── */
hr {{
    border: none;
    border-top: 1px solid rgba(0,0,0,0.07);
    margin: 1rem 0;
}}

/* ─ Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: rgba(0,0,0,0.15);
    border-radius: 3px;
}}

/* ─ Expander ─────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: {C.GLASS_BG} !important;
    border: 1px solid {C.GLASS_BORDER} !important;
    border-radius: 14px !important;
    backdrop-filter: blur(12px) !important;
}}

/* ─ Bottom container ─────────────────────────────────────────────────── */
.stBottomBlockContainer {{
    background: rgba(238,242,255,0.85) !important;
    backdrop-filter: blur(16px) !important;
    border-top: 1px solid rgba(255,255,255,0.80) !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0.5rem 0 1.5rem;">
        <div style="font-size:1.5rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.5px;">🔍 FakeShield</div>
        <div style="font-size:0.78rem; color:{C.TEXT_MUTED}; margin-top:2px;">
            Bluesky Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", ["Fact-Check", "Analytics"], label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↺  Reload data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div style="position:absolute; bottom:1.5rem; left:1.5rem; right:1.5rem;
                font-size:0.72rem; color:{C.TEXT_SUBTLE}; text-align:center;">
        M1 Data Science · 2024
    </div>
    """, unsafe_allow_html=True)


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
        chart
        .configure_view(strokeWidth=0, fill="transparent")
        .configure_axis(
            labelColor=C.TEXT_MUTED, titleColor=C.TEXT_MUTED,
            gridColor="rgba(0,0,0,0.06)", domainColor="rgba(0,0,0,0.1)",
            labelFont="Inter, sans-serif", titleFont="Inter, sans-serif",
        )
        .configure_legend(
            labelColor=C.TEXT_MUTED, titleColor=C.TEXT_MUTED,
            labelFont="Inter, sans-serif", titleFont="Inter, sans-serif",
        )
    )


# ══════════════════════════════════════════════════════════════════════════
# PAGE — FACT-CHECK CHATBOT
# ══════════════════════════════════════════════════════════════════════════
if page == "Fact-Check":

    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:1.5rem;">
        <div style="font-size:1.6rem; font-weight:700; color:{C.TEXT_MAIN};
                    letter-spacing:-0.4px;">Fact-Check a Claim</div>
        <div style="font-size:0.9rem; color:{C.TEXT_MUTED}; margin-top:4px;">
            Paste any post or article excerpt — the model checks it against
            the Bluesky corpus and responds with a verdict.
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    user_input = st.chat_input("Paste a claim, post, or headline to verify…")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Checking…"):
                result = send_message_api(user_input)

            verdict   = result["verdict"]
            color     = result["color"]
            expl      = result["explanation"]
            prob      = result["probability"]
            source    = result["based_on"]

            source_label = {
                "rag": "🔵 Based on Bluesky corpus",
                "general_knowledge": "🟡 Based on general knowledge",
                "error": "🔴 API error",
            }.get(source, f"· {source}")

            prob_bar = ""
            if prob is not None:
                pct = int(prob * 100)
                prob_bar = f"""
                <div style="margin:0.6rem 0 0.4rem;">
                    <div style="display:flex; justify-content:space-between;
                                font-size:0.78rem; color:{C.TEXT_MUTED};
                                margin-bottom:4px;">
                        <span>Confidence</span><span>{pct}%</span>
                    </div>
                    <div style="background:rgba(0,0,0,0.08); border-radius:99px;
                                height:5px; overflow:hidden;">
                        <div style="width:{pct}%; height:100%;
                                    background:{color};
                                    border-radius:99px;
                                    transition:width 0.4s ease;">
                        </div>
                    </div>
                </div>"""

            html = f"""
            <div style="background:rgba(255,255,255,0.55);
                        border:1px solid rgba(255,255,255,0.85);
                        border-radius:16px; padding:1.1rem 1.3rem;
                        backdrop-filter:blur(12px);">
                <div style="display:inline-block; background:{color}22;
                            border:1px solid {color}55; border-radius:99px;
                            padding:0.2rem 0.85rem; font-size:0.82rem;
                            font-weight:700; color:{color};
                            letter-spacing:0.03em; text-transform:uppercase;">
                    {verdict}
                </div>
                {prob_bar}
                <div style="font-size:0.92rem; color:{C.TEXT_MAIN};
                            line-height:1.6; margin-top:0.5rem;">
                    {expl}
                </div>
                <div style="font-size:0.75rem; color:{C.TEXT_SUBTLE};
                            margin-top:0.75rem; padding-top:0.6rem;
                            border-top:1px solid rgba(0,0,0,0.07);">
                    {source_label}
                </div>
            </div>"""

            st.html(html)
            st.session_state.messages.append({"role": "assistant", "content": html, "is_html": True})

    if not st.session_state.messages:
        st.markdown(f"""
        <div style="text-align:center; padding:3rem 0; color:{C.TEXT_SUBTLE};
                    font-size:0.9rem;">
            ↑  Enter a claim above to get started
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE — ANALYTICS
# ══════════════════════════════════════════════════════════════════════════
elif page == "Analytics":

    st.markdown(f"""
    <div style="font-size:1.6rem; font-weight:700; color:{C.TEXT_MAIN};
                letter-spacing:-0.4px; margin-bottom:1.5rem;">
        Analytics
    </div>
    """, unsafe_allow_html=True)

    if not has_data:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:2rem;">📭</div>
            <div style="color:{C.TEXT_MUTED}; margin-top:0.5rem;">
                No data yet — run the ingestion pipeline first.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Stat row ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Posts",     f"{len(df_posts):,}")
    c2.metric("Unique Authors",  f"{df_posts['username'].nunique():,}")
    c3.metric("Categories",      f"{df_posts['category'].nunique():,}")
    top_kw = df_trend.iloc[0]["keyword"] if not df_trend.empty else "—"
    c4.metric("Top Keyword",     top_kw)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chart tabs ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "  Keywords  ", "  Top Authors  ", "  Posts by Hour  ", "  Emotions  "
    ])

    # ── Tab 1: Keywords ───────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        base = alt.Chart(df_trend).encode(
            y=alt.Y("keyword:N", sort="-x", title="", axis=alt.Axis(labelLimit=160)),
            x=alt.X("count:Q", title="Occurrences"),
            tooltip=["keyword:N", "count:Q"],
        )
        chart = (
            base.mark_bar(
                color=C.ACCENT_PRIMARY,
                opacity=0.18,
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
            )
            + base.mark_point(filled=True, size=80, color=C.ACCENT_PRIMARY)
            + base.mark_rule(color=C.ACCENT_PRIMARY, opacity=0.35, strokeWidth=1.5)
        ).properties(height=420)

        st.altair_chart(glass_chart(chart), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 2: Top authors ────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        categories = df_category["category"].unique().tolist()
        cols = st.columns(min(len(categories), 2))
        for i, cat in enumerate(categories):
            df_cat = df_category[df_category["category"] == cat].head(8)
            pie = (
                alt.Chart(df_cat)
                .mark_arc(innerRadius=50, outerRadius=100)
                .encode(
                    theta=alt.Theta("post_count:Q"),
                    color=alt.Color(
                        "username:N",
                        scale=alt.Scale(scheme="blues"),
                        legend=alt.Legend(orient="right", labelLimit=120),
                    ),
                    tooltip=["username:N", "post_count:Q"],
                )
                .properties(title=cat, height=260)
            )
            cols[i % 2].altair_chart(glass_chart(pie), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3: Posts by hour ──────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        area = (
            alt.Chart(df_hour)
            .mark_area(
                color=C.ACCENT_PRIMARY,
                opacity=0.12,
                line={"color": C.ACCENT_PRIMARY, "strokeWidth": 2},
                point=alt.OverlayMarkDef(
                    color=C.ACCENT_PRIMARY, filled=True, size=60
                ),
            )
            .encode(
                x=alt.X("hour:Q", title="Hour of day",
                         axis=alt.Axis(tickCount=24, format="d")),
                y=alt.Y("count:Q", title="Posts"),
                tooltip=["hour:Q", "count:Q"],
            )
            .properties(height=300)
        )

        st.altair_chart(glass_chart(area), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 4: Emotions ───────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        if df_emotion is not None and not df_emotion.empty:
            EMOTION_COLORS = {
                "joy":     "#34C759",
                "sadness": "#007AFF",
                "anger":   "#FF3B30",
                "fear":    "#FF9F0A",
                "love":    "#FF2D55",
                "surprise":"#AF52DE",
            }
            color_range = [
                EMOTION_COLORS.get(e, C.ACCENT_PRIMARY)
                for e in df_emotion["emotion"].tolist()
            ]

            bars = (
                alt.Chart(df_emotion)
                .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
                .encode(
                    y=alt.Y("emotion:N", sort="-x", title="",
                             axis=alt.Axis(labelLimit=120)),
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
                .properties(height=300)
            )
            st.altair_chart(glass_chart(bars), use_container_width=True)
        else:
            st.markdown(f"""
            <div style="text-align:center; padding:2rem; color:{C.TEXT_MUTED};">
                No emotion data yet — run the NLP pipeline first.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
