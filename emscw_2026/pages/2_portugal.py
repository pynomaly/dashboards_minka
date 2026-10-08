# Page for Portugal (place_id: 79)

import os

import config
import pandas as pd
import streamlit as st

PLACE_ID = 825
PLACE_NAME = config.PLACES[PLACE_ID]

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"{PLACE_NAME} - {config.PROJ_NAME}",
)

import streamlit.components.v1 as components
from i18n import create_sidebar_content, init_i18n, t
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    fig_taxonomic_treemap,
    get_main_metrics,
    get_taxonomic_distribution,
)

# Initialize i18n
init_i18n(current_page="portugal")
create_sidebar_content("Portugal")


# Cached functions for performance
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_main_metrics(place_id):
    """Cache API calls for main metrics"""
    return get_main_metrics(place_id)


@st.cache_data(ttl=300, show_spinner=False)
def load_main_metrics(path):
    """Cache CSV loading and transformation"""
    df = pd.read_csv(path)
    df.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )
    return df


def load_observations(path):
    """Load observations CSV"""
    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def get_quality_grade_stats(path):
    """Get quality grade distribution stats"""
    df = pd.read_csv(path)
    total = len(df)
    if total == 0:
        return 0, 0, 0, 0, 0, 0
    research = len(df[df["quality_grade"] == "research"])
    needs_id = len(df[df["quality_grade"] == "needs_id"])
    casual = len(df[df["quality_grade"] == "casual"])
    research_pct = round(research / total * 100, 1)
    needs_id_pct = round(needs_id / total * 100, 1)
    casual_pct = round(casual / total * 100, 1)
    return research, needs_id, casual, research_pct, needs_id_pct, casual_pct


@st.cache_data(ttl=300, show_spinner=False)
def load_users(path, place_id):
    """Cache users CSV loading and transformation"""
    users = pd.read_csv(path)
    users["link"] = (
        f"{config.HOME_PATH}/observations?d1={config.START_DAY}&d2={config.END_DAY}&place_id={place_id}&subview=map&user_id="
        + users["participant"]
    )
    users.drop(columns="participant", inplace=True)
    users = users[["link", "observacions", "identificacions", "espècies"]]
    users.index += 1
    return users


def get_maps(df_obs, center, zoom):
    """Generate map HTML without caching"""
    heatmap = create_heatmap(df_obs.copy(), center=center, zoom=zoom)
    markermap = create_markercluster(df_obs.copy(), center=center, zoom=zoom)
    return heatmap._repr_html_(), markermap._repr_html_()


@st.cache_data(ttl=300, show_spinner=False)
def get_species_ranking(obs_path, photos_path, place_id):
    """Get species ranking with observation counts and images (research grade only)."""
    df_obs = pd.read_csv(obs_path)
    df_photos = pd.read_csv(photos_path)

    # Filter only research grade observations
    df_obs = df_obs[df_obs["quality_grade"] == "research"]

    # Count observations per species
    species_counts = (
        df_obs.groupby(["taxon_id", "taxon_name"])
        .size()
        .reset_index(name="num_observations")
    )
    species_counts = species_counts.sort_values("num_observations", ascending=False)

    # Add link to observations (with taxon_name as fragment for display)
    species_counts["link"] = species_counts.apply(
        lambda row: f"{config.HOME_PATH}/observations?d1={config.START_DAY}&d2={config.END_DAY}&place_id={place_id}&taxon_id={int(row['taxon_id'])}#{row['taxon_name'].replace(' ', '_')}"
        if pd.notna(row["taxon_id"]) and pd.notna(row["taxon_name"])
        else "",
        axis=1,
    )

    # Get last observation image for each species (top 10)
    top_species = species_counts.head(10)
    images = []
    for _, row in top_species.iterrows():
        taxon_name = row["taxon_name"]
        taxon_id = row["taxon_id"]
        # Get the last observation for this species
        species_obs = df_obs[df_obs["taxon_name"] == taxon_name].sort_values(
            "observed_on", ascending=False
        )
        if len(species_obs) > 0:
            obs_id = species_obs.iloc[0]["id"]
            # Find photo for this observation
            photo = df_photos[df_photos["id"] == obs_id]
            if len(photo) > 0:
                images.append(
                    {
                        "taxon_name": taxon_name,
                        "taxon_id": taxon_id,
                        "image_url": photo.iloc[0]["photos_medium_url"],
                        "num_observations": row["num_observations"],
                    }
                )
            else:
                images.append(
                    {"taxon_name": taxon_name, "taxon_id": taxon_id, "image_url": None, "num_observations": row["num_observations"]}
                )
        else:
            images.append(
                {"taxon_name": taxon_name, "taxon_id": taxon_id, "image_url": None, "num_observations": row["num_observations"]}
            )

    return species_counts, images


st.markdown(
    """
    <style>
        :root {
            --background-color: #FFFFFF !important;
            --secondary-background-color: #F1F9F5 !important;
            --text-color: #262730 !important;
            --font: "Source Sans Pro", sans-serif !important;
        }
        .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stHeader"], .main, .block-container {
            background-color: #FFFFFF !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] {
            width: 300px !important;
            background-color: #F1F9F5 !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 300px !important;
            background-color: #F1F9F5 !important;
        }
        [data-testid="stSidebarContent"] {
            background-color: #F1F9F5 !important;
        }
        p, span, label, .stMarkdown, h1, h2, h3, h4, h5, h6 {
            color: #262730 !important;
        }
        [data-testid="stMetric"], [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
            color: #262730 !important;
        }
        [data-testid="stDataFrame"], .dataframe {
            background-color: #FFFFFF !important;
        }
        [data-testid="stDownloadButton"] button[kind="primary"] {
            background-color: #48b8cc !important;
            border-color: #48b8cc !important;
        }
        [data-testid="stDownloadButton"] button[kind="primary"]:hover {
            background-color: #3a9fb0 !important;
            border-color: #3a9fb0 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":blue[{PLACE_NAME}]")
        st.markdown(f":blue[{config.PROJ_NAME}]")
        st.markdown(f":blue[{config.PROJ_DATES}]")


# Main metrics from API (cached)
try:
    total_species, total_participants, total_obs = get_cached_main_metrics(PLACE_ID)
except Exception:
    st.warning(t("ui.no_data"))
    total_species = total_participants = total_obs = 0

# Tarjetas Main metrics
with st.container():
    __, col1, col2, col3, _ = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric(
            t("metrics.observations"),
            f"{total_obs:,}".replace(",", "."),
        )
    with col2:
        st.metric(
            t("metrics.species"),
            f"{total_species:,}".replace(",", "."),
        )
    with col3:
        st.metric(
            t("metrics.participants"),
            f"{total_participants:,}".replace(",", "."),
        )
    style_metric_cards(
        background_color="#fff",
        border_left_color=f"{config.COLORS[1]}",
        box_shadow=False,
    )

# Evolution bars (cached CSV)
with st.container():
    metrics_path = f"{directory}/data/{PLACE_ID}_main_metrics.csv"
    if not os.path.exists(metrics_path):
        st.warning(t("ui.no_data"))
    else:
        main_metrics = load_main_metrics(metrics_path)

        col1_line, col2_line, col3_line = st.columns(3, gap="large")

        with col1_line:
            fig1 = fig_area_evolution(
                df=main_metrics,
                field="observacions",
                title=t("charts.observations_per_day"),
                color=f"{config.COLORS[0]}",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2_line:
            fig2 = fig_area_evolution(
                df=main_metrics,
                field="espècies",
                title=t("charts.species_per_day"),
                color=f"{config.COLORS[1]}",
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3_line:
            fig3 = fig_area_evolution(
                df=main_metrics,
                field="participants",
                title=t("charts.participants_per_day"),
                color=f"{config.COLORS[2]}",
            )
            st.plotly_chart(fig3, use_container_width=True)

# Download button
with st.container():
    obs_path = f"{directory}/data/{PLACE_ID}_obs.csv"
    if os.path.exists(obs_path):
        df_download = load_observations(obs_path)
        csv_data = df_download.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=t("ui.download_dataset"),
            data=csv_data,
            file_name=f"{PLACE_NAME.lower().replace(' ', '_')}_observations.csv",
            mime="text/csv",
            type="primary",
        )

# Data quality section
with st.container():
    obs_path = f"{directory}/data/{PLACE_ID}_obs.csv"
    if os.path.exists(obs_path):
        research, needs_id, casual, research_pct, needs_id_pct, casual_pct = get_quality_grade_stats(obs_path)
        st.markdown(f"### {t('metrics.data_quality')}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t("metrics.research_grade"), f"{research} ({research_pct}%)")
        with col2:
            st.metric(t("metrics.needs_id"), f"{needs_id} ({needs_id_pct}%)")
        with col3:
            st.metric(t("metrics.casual"), f"{casual} ({casual_pct}%)")
        # Stacked progress bar
        st.markdown(f'''
        <div style="display: flex; width: 100%; height: 20px; border-radius: 5px; overflow: hidden; background-color: #e0e0e0;">
            <div style="width: {research_pct}%; background-color: #28a745;" title="{t("metrics.research_grade")}: {research_pct}%"></div>
            <div style="width: {needs_id_pct}%; background-color: #ffc107;" title="{t("metrics.needs_id")}: {needs_id_pct}%"></div>
            <div style="width: {casual_pct}%; background-color: #dc3545;" title="{t("metrics.casual")}: {casual_pct}%"></div>
        </div>
        ''', unsafe_allow_html=True)
        if casual > 0:
            st.caption(t("metrics.casual_explanation"))

st.divider()

# Users ranking
with st.container():
    st.markdown(f"## {t('participants_page.users_by_observations')}")
    users_path = f"{directory}/data/{PLACE_ID}_users.csv"
    if os.path.exists(users_path):
        users = load_users(users_path, PLACE_ID)
        st.data_editor(
            users,
            column_config={
                "link": st.column_config.LinkColumn(
                    t("participants_page.username"),
                    display_text=r"user_id=(.+)$",
                    width="medium",
                ),
                "observacions": st.column_config.NumberColumn(
                    t("metrics.observations"), width=100
                ),
                "identificacions": st.column_config.NumberColumn(width=100),
                "espècies": st.column_config.NumberColumn(
                    t("metrics.species"), width=100
                ),
            },
            hide_index=False,
            disabled=True,
        )
    else:
        st.warning(t("ui.no_data"))

st.divider()

# Species ranking
with st.container():
    obs_path = f"{directory}/data/{PLACE_ID}_obs.csv"
    photos_path = f"{directory}/data/{PLACE_ID}_photos.csv"

    if os.path.exists(obs_path) and os.path.exists(photos_path):
        species_df, top_images = get_species_ranking(obs_path, photos_path, PLACE_ID)

        if len(species_df) > 0:
            # Two columns: table (1/3) on left, treemap (2/3) on right
            col_table, col_treemap = st.columns([1, 2])

            with col_table:
                st.markdown(f"### {t('species_page.species_ranking')}")
                display_species = species_df[["link", "num_observations"]].copy()
                display_species.index = range(1, len(display_species) + 1)

                st.data_editor(
                    display_species,
                    column_config={
                        "link": st.column_config.LinkColumn(
                            t("species_page.species_name"),
                            display_text=r"#(.+)$",
                            width="medium",
                        ),
                        "num_observations": st.column_config.NumberColumn(
                            t("species_page.num_observations"), width=120
                        ),
                    },
                    hide_index=False,
                    disabled=True,
                )

            with col_treemap:
                st.markdown(f"### {t('species_page.taxonomic_groups')}")
                df_obs_treemap = load_observations(obs_path)
                tax_counts = get_taxonomic_distribution(df_obs_treemap)
                if len(tax_counts) > 0:
                    fig_treemap = fig_taxonomic_treemap(
                        tax_counts,
                        title="",
                        color_scheme=None
                    )
                    st.plotly_chart(fig_treemap, use_container_width=True)

            # Species images below both columns
            st.markdown(f"### {t('species_page.most_observed')}")
            cols = st.columns(5)
            for i, img_data in enumerate(top_images):
                with cols[i % 5]:
                    if img_data.get("taxon_id"):
                        obs_link = f"{config.HOME_PATH}/observations?d1={config.START_DAY}&d2={config.END_DAY}&place_id={PLACE_ID}&taxon_id={int(img_data['taxon_id'])}"
                        st.markdown(f"[🔗 MINKA]({obs_link})")
                    if img_data["image_url"]:
                        st.image(img_data["image_url"], caption=f"{img_data['taxon_name']} ({img_data['num_observations']})")
                    else:
                        st.write(f"{img_data['taxon_name']} ({img_data['num_observations']})")
        else:
            st.warning(t("ui.no_data"))
    else:
        st.warning(t("ui.no_data"))

st.divider()

# Mapas
with st.container():
    st.header(t("ui.maps"))
    obs_path = f"{directory}/data/{PLACE_ID}_obs.csv"

    if not os.path.exists(obs_path):
        st.warning(t("ui.no_observation"))
    else:
        try:
            df_obs = load_observations(obs_path)
            if len(df_obs) > 0:
                center = config.PLACE_CENTERS.get(PLACE_ID, [40.0, -3.0])
                zoom = config.PLACE_ZOOM.get(PLACE_ID, 6)
                map_html1, map_html2 = get_maps(df_obs, center, zoom)

                map1, map2 = st.columns(2)
                with map1:
                    components.html(map_html1, height=600)
                with map2:
                    components.html(map_html2, height=600)
            else:
                st.warning(t("ui.no_observation"))
        except Exception:
            st.warning(t("ui.no_observation"))

# Footer con fondo de color
image_footer = f"{directory}/images/footer.png"

if os.path.exists(image_footer):
    st.markdown(
        f"""
        <div style="background-color: {config.COLORS[1]}; padding: 10px; margin-top: 10px; border-radius: 10px;">
            <img src="data:image/png;base64,{__import__('base64').b64encode(open(image_footer, 'rb').read()).decode()}"
                 style="width: 100%; display: block;">
        </div>
        """,
        unsafe_allow_html=True,
    )
