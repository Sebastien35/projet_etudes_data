import streamlit as st
import altair as alt

from streamlit_logic import load_posts, fake_news_model,  get_posts, top_users_per_category, trending_keywords, posts_per_hour
from streamlit_color_chart import ColorChart

# =====================================================
# COLOR PALETTE
# =====================================================
BG_MAIN        = ColorChart.get_bg_main()
BG_SIDEBAR     = ColorChart.get_bg_sidebar()
BG_CARD        = ColorChart.get_bg_card()
ACCENT_PRIMARY = ColorChart.get_accent_primary()
ACCENT_SOFT    = ColorChart.get_accent_soft()
TEXT_MAIN      = ColorChart.get_text_main()
TEXT_MUTED     = ColorChart.get_text_muted()
SUCCESS_COLOR  = ColorChart.get_success_color()
WARNING_COLOR  = ColorChart.get_warning_color()


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Fake News Intelligence",
    layout="wide",
)

# =====================================================
# GLOBAL CSS
# =====================================================
st.markdown(
    f"""
    <style>
    /* Header background */
    .stAppHeader {{
        background-color: {BG_MAIN};
        color: {TEXT_MAIN};
    }}

    /* App background */
    .stApp {{
        background-color: {BG_MAIN};
        color: {TEXT_MAIN};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {BG_SIDEBAR};
        border-right: 1px solid #1F2A28;
    }}

    /* Sidebar radio labels */
    section[data-testid="stSidebar"] label {{
        color: {TEXT_MUTED};
        font-weight: 500;
    }}

    section[data-testid="stSidebar"] label:hover {{
        color: {TEXT_MAIN};
    }}

    /* Sidebar radio button */
    section[data-testid="stSidebar"] input[type="radio"] {{
        accent-color: {ACCENT_PRIMARY};
    }}

    /* Titles */
    h1, h2, h3 {{
        color: {TEXT_MAIN};
    }}

    /* Chat card */
    .chat-card {{
        background-color: {BG_CARD};
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 0 0 1px rgba(47,79,75,0.25);
    }}

    /* Chat input */
    textarea {{
        color: {TEXT_MAIN} !important;
    }}

    /* Footer background */
    .stBottomBlockContainer {{
        background-color: {BG_MAIN};
        color: {TEXT_MAIN};
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# TITLE
# =====================================================
st.title("Dashboard Bluesky")

# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
st.sidebar.title("Navigation")

st.sidebar.button("Reload Data", on_click=lambda: st.session_state.update(reload=True))

main_section = st.sidebar.radio(
    "Section",
    ["Chatbot", "Graphes"],
)

if main_section == "Graphes":
    graph_type = st.sidebar.radio(
        "Type de graphe",
        [
            "Top utilisateurs par categorie",
            "Keywords en tendances",
            "Nombre de posts par heure",
        ],
    )

# =====================================================
# Logic functions
# =====================================================
    
df_posts = get_posts()

df_category = top_users_per_category(df_posts)
df_trend = trending_keywords(df_posts)
df_hour = posts_per_hour(df_posts)

# =====================================================
# CHATBOT PAGE
# =====================================================
if main_section == "Chatbot":

    st.markdown('<div class="chat-card">', unsafe_allow_html=True)

    st.subheader("Fake News Analyzer")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    user_input = st.chat_input("Paste a post or article to analyze...")

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        verdict, color, explanation = fake_news_model(user_input)

        response = f"""
        **Verdict:** <span style="color:{color}; font-weight:700">{verdict}</span>

        <span style="color:{TEXT_MUTED}">{explanation}</span>
        """

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        with st.chat_message("assistant"):
            st.markdown(response, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# GRAPHES PAGE
# =====================================================
elif main_section == "Graphes":

    # -------- Posts per publisher --------
    if graph_type == "Top utilisateurs par categorie":
        st.subheader("Top utilisateurs par categorie")

        cols = st.columns(2)
        # --- Generate a pie chart per category ---
        for i, category in enumerate(df_category['category'].unique()):

            df_cat = df_category[df_category['category'] == category]

            pie_chart = alt.Chart(df_cat).mark_arc().encode(
                theta=alt.Theta(field="post_count", type="quantitative"),
                color=alt.Color(field="username", type="nominal"),
                tooltip=['username', 'post_count']
            )
            
            # Place chart in left or right column
            col = cols[i % 2]
            col.subheader(f"Categorie: {category}")
            col.altair_chart(pie_chart, use_container_width=True)
            
            # Create a new row after 2 charts
            if i % 2 == 1:
                cols = st.columns(2)

    # -------- Trending keywords --------
    elif graph_type == "Keywords en tendances":
        st.subheader("Mots-clés en tendances")

        # Barres pleines
        #chart = (
        #    alt.Chart(df_trend)
        #    .mark_bar(
        #        color=ACCENT_PRIMARY,
        #        cornerRadiusTopRight=6,
        #        cornerRadiusBottomRight=6
        #    )
        #    .encode(
        #        y=alt.Y(
        #            "keyword:N",
        #            sort="-x",
        #            title=""
        #        ),
        #        x=alt.X("count:Q", title=""),
        #        tooltip=["keyword", "count"]
        #    )
        #)
        #st.altair_chart(chart, width='stretch')


        # Barres fines avec points

        base = alt.Chart(df_trend).encode(
            y=alt.Y("keyword:N", sort="-x", title=""),
            x=alt.X("count:Q", title="")
        )

        chart2 = (
            base.mark_rule(color="#444")
            + base.mark_point(
                size=100,
                filled=True,
                color=ACCENT_PRIMARY
            )
        )
        st.altair_chart(chart2, width='stretch')

        ##############################################


    # -------- Posts over time --------
    elif graph_type == "Nombre de posts (heure / jour)":
        st.subheader("Nombre de posts par heure")
        chart = (
            alt.Chart(df_hour)
            .mark_line(
                color=ACCENT_PRIMARY,
                point=alt.OverlayMarkDef(color=ACCENT_SOFT, size=60)
            )
            .encode(
                x=alt.X("hour:Q", title="Hour"),
                y=alt.Y("count:Q", title="Posts"),
                tooltip=["hour", "count"]
            )
        )

        st.altair_chart(chart, width='stretch')
