# Run as streamlit run app_biomarato.py --server.port 9003

import os

import config
import pandas as pd
import requests
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
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    get_main_metrics,
)

session = requests.Session()


@st.cache_data(ttl=60)
def read_df(path: str) -> pd.DataFrame:
    df_obs = pd.read_csv(path)
    return df_obs


# columna izquierda

st.sidebar.markdown("# Què és BioDiverCiutat")
st.sidebar.markdown(
    f"""
És un esdeveniment de ciència ciutadana que forma part del City Nature Challenge, una competició internacional amistosa que destaca la importància de reportar la biodiversitat a les ciutats. Cada ciutat està "custodiada" per una entitat de recerca o naturalista. A Barcelona i tota l’àrea metropolitana, l’esdeveniment adopta el nom de BioDiverCiutat i l’organitza l'Institut de Ciències del Mar (ICM-CSIC).

Consisteix a registrar el màxim nombre d'espècies possible durant 4 dies consecutius: del {config.PROJ_DATES}. És un bioblitz internacional, vol dir que ciutats de tot el món competeixen per reportar el major nombre d'observacions de biodiversitat en aquest període de temps.
"""
)


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[Resultats {config.PROJ_NAME}]")
        st.markdown(":green[Repte Naturalista Urbà - City Nature Challenge]")
        st.markdown(f":green[{config.PROJ_DATES}]")


try:
    total_species, total_participants, total_obs = get_main_metrics(
        config.MAIN_PROJ, session=session
    )
except Exception:
    st.warning("Cap dada disponible")
    total_species = total_participants = total_obs = 0

# Tarjetas Main metrics
with st.container():

    __, col1, col2, col3, _ = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric(
            "Observacions",
            f"{total_obs:,}".replace(",", " "),
        )
    with col2:
        st.metric(
            "Espècies",
            f"{total_species:,}".replace(",", " "),
        )
    with col3:
        st.metric(
            "Participants",
            f"{total_participants:,}".replace(",", " "),
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color=f"{config.COLORS[1]}",
        box_shadow=False,
    )

# Evolution lines
with st.container():
    metrics_path = f"{directory}/data/{config.MAIN_PROJ}_main_metrics.csv"
    if not os.path.exists(metrics_path):
        st.warning("Cap dada disponible")
    else:
        main_metrics = pd.read_csv(metrics_path)
        main_metrics.rename(
            columns={
                "date": "data",
                "observations": "observacions",
                "species": "espècies",
            },
            inplace=True,
        )

        col1_line, col2_line, col3_line = st.columns(3, gap="large")

        with col1_line:
            fig1 = fig_area_evolution(
                df=main_metrics,
                field="observacions",
                title="Observacions per dia",
                color=f"{config.COLORS[0]}",
            )

            st.plotly_chart(fig1, use_container_width=True)

        with col2_line:
            fig2 = fig_area_evolution(
                df=main_metrics,
                field="espècies",
                title="Espècies per dia",
                color=f"{config.COLORS[1]}",
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3_line:
            fig3 = fig_area_evolution(
                df=main_metrics,
                field="participants",
                title="Participants per dia",
                color=f"{config.COLORS[2]}",
            )
            st.plotly_chart(fig3, use_container_width=True)

st.divider()

# 7. Mapas (incluye todos los usuarios y todos los grados)

with st.container():
    st.header("Mapes")
    try:
        df_obs = read_df(f"{directory}/data/{config.MAIN_PROJ}_obs.csv")
        if len(df_obs) > 0:
            heatmap = create_heatmap(
                df_obs, center=[41.36174441599461, 2.108076037807884]
            )
            markermap = create_markercluster(
                df_obs, center=[41.36174441599461, 2.108076037807884]
            )
            map1, map2 = st.columns(2)
            with map1:
                map_html1 = heatmap._repr_html_()
                components.html(map_html1, height=600)

            with map2:
                map_html2 = markermap._repr_html_()
                components.html(map_html2, height=600)

    except FileNotFoundError:
        st.markdown("Cap observació")
        pass
