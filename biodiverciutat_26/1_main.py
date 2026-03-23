# Run as streamlit run 1_main.py --server.port 9003

import os

import config
import pandas as pd
import streamlit as st

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

import streamlit.components.v1 as components
from i18n import create_sidebar_content, init_i18n, t
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    get_main_metrics,
)

# Initialize i18n
init_i18n(current_page="main")
create_sidebar_content()


# Cached functions for performance
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_main_metrics(proj_id):
    """Cache API calls for main metrics"""
    return get_main_metrics(proj_id)


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


@st.cache_data(ttl=300, show_spinner=False)
def load_observations(path):
    """Cache observations CSV"""
    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_maps(_df_obs):
    """Cache map HTML generation (underscore prefix tells Streamlit not to hash)"""
    heatmap = create_heatmap(_df_obs, center=[41.36174441599461, 2.108076037807884])
    markermap = create_markercluster(
        _df_obs, center=[41.36174441599461, 2.108076037807884]
    )
    return heatmap._repr_html_(), markermap._repr_html_()


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.main_title')} {config.PROJ_NAME}]")
        st.markdown(f":green[{t('header.subtitle')}]")
        st.markdown(f":green[{config.PROJ_DATES}]")


# Main metrics from API (cached)
try:
    total_species, total_participants, total_obs = get_cached_main_metrics(
        config.MAIN_PROJ
    )
except Exception:
    st.warning(t("ui.no_data"))
    total_species = total_participants = total_obs = 0

# Tarjetas Main metrics
with st.container():
    __, col1, col2, col3, _ = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric(
            t("metrics.observations"),
            f"{total_obs:,}".replace(",", " "),
        )
    with col2:
        st.metric(
            t("metrics.species"),
            f"{total_species:,}".replace(",", " "),
        )
    with col3:
        st.metric(
            t("metrics.participants"),
            f"{total_participants:,}".replace(",", " "),
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color=f"{config.COLORS[1]}",
        box_shadow=False,
    )

# Evolution lines (cached CSV)
with st.container():
    metrics_path = f"{directory}/data/{config.MAIN_PROJ}_main_metrics.csv"
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

st.divider()

# Mapas (cached)
with st.container():
    st.header(t("ui.maps"))
    obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"

    if not os.path.exists(obs_path):
        st.warning(t("ui.no_observation"))
    else:
        try:
            df_obs = load_observations(obs_path)
            if len(df_obs) > 0:
                map_html1, map_html2 = get_cached_maps(df_obs)

                map1, map2 = st.columns(2)
                with map1:
                    components.html(map_html1, height=600)
                with map2:
                    components.html(map_html2, height=600)
            else:
                st.warning(t("ui.no_observation"))
        except Exception:
            st.warning(t("ui.no_observation"))
