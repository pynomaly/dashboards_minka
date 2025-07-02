# Run as streamlit run app_biomarato.py --server.port 9003

import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    get_main_metrics,
)

st.set_page_config(
    layout="wide",
    page_icon="images/minka-logo.png",
    page_title="Dashboard BioDiverCiutat 2024",
)

bdc_colors = ["#4aae79", "#007d8a", "#00a3b4"]

try:
    directory = f"{os.environ['DASHBOARDS']}/biodiverciutat_24"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

exclude_users = [
    "xasalva",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "uri_domingo",
    "mimo_fecdas",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
]

API_PATH = "https://api.minka-sdg.org/v1"

main_project = 233

projects = {
    79: "Begues",
    80: "Viladecans",
    81: "Sant Climent de Llobregat",
    83: "Cervelló",
    85: "Sant Boi de Llobregat",
    86: "Santa Coloma de Cervelló",
    87: "Sant Vicenç dels Horts",
    88: "la Palma de Cervelló",
    89: "Corbera de Llobregat",
    91: "Sant Andreu de la Barca",
    92: "Castellbisbal",
    93: "el Papiol",
    94: "Molins de Rei",
    95: "Sant Feliu de Llobregat",
    97: "Cornellà de Llobregat",
    98: "l'Hospitalet de Llobregat",
    99: "Esplugues de Llobregat",
    100: "Sant Just Desvern",
    101: "Sant Cugat del Vallès",
    102: "Barberà del Vallès",
    103: "Ripollet",
    104: "Montcada i Reixac",
    106: "Sant Adrià de Besòs",
    107: "Badalona",
    108: "Tiana",
    109: "Montgat",
    224: "Barcelona",
    225: "el Prat de Llobregat",
    226: "Pallejà",
    227: "Torrelles de Llobregat",
    228: "Castelldefels",
    229: "Gavà",
    230: "Sant Joan Despí",
    231: "Santa Coloma de Gramenet",
    232: "Àrea marina Barcelona",
}


@st.cache_data(ttl=360)
def read_df(path: str) -> pd.DataFrame:
    df_obs = pd.read_csv(path)
    return df_obs


# columna izquierda

st.sidebar.markdown("# Què és BioDiverCiutat")
st.sidebar.markdown(
    """
És un esdeveniment de ciència ciutadana que forma part del City Nature Challenge, una competició internacional amistosa que destaca la importància de reportar la biodiversitat a les ciutats. Cada ciutat està "custodiada" per una entitat de recerca o naturalista. A Barcelona i tota l’àrea metropolitana, l’esdeveniment adopta el nom de BioDiverCiutat i l’organitza l'Institut de Ciències del Mar (ICM-CSIC).

Consisteix a registrar el màxim nombre d'espècies possible durant 4 dies consecutius: del 26 al 29 d’abril de 2024. És un bioblitz internacional, vol dir que ciutats de tot el món competeixen per reportar el major nombre d'observacions de biodiversitat en aquest període de temps.
"""
)


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image(f"{directory}/images/LOGO OFICIAL_biodiverciutat_marca_rgbpositiu.png")
    with col2:
        st.header(":green[Resultats BioDiverCiutat 2024]")
        st.markdown(":green[Repte Naturalista Urbà - City Nature Challenge]")
        st.markdown(":green[26 - 29 d'abril de 2024]")


try:
    total_species, total_participants, total_obs = get_main_metrics(main_project)
except:
    st.error("Error loading data")
    st.stop()

# Tarjetas Main metrics
with st.container():

    __, col1, col2, col3, _ = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric(
            "Observacions",
            # f"{total_obs:,}".replace(",", " "),
            "3 536",
        )
    with col2:
        st.metric(
            "Espècies",
            # f"{total_species:,}".replace(",", " "),
            "767",
        )
    with col3:
        st.metric(
            "Participants",
            # f"{total_participants:,}".replace(",", " "),
            "62",
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color="#007d8a",
        box_shadow=False,
    )

# Evolution lines
with st.container():
    main_metrics = pd.read_csv(f"{directory}/data/{main_project}_main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )

    col1_line, col2_line, col3_line = st.columns(3, gap="small")

    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics,
            field="observacions",
            title="Observacions per dia",
            color=bdc_colors[0],
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics,
            field="espècies",
            title="Espècies per dia",
            color=bdc_colors[1],
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics,
            field="participants",
            title="Participants per dia",
            color=bdc_colors[2],
        )
        st.plotly_chart(fig3, use_container_width=True)

st.divider()

# 7. Mapas (incluye todos los usuarios y todos los grados)

with st.container():
    st.header("Mapes")
    try:
        df_obs = read_df(f"{directory}/data/{main_project}_obs.csv")
        if len(df_obs) > 0:
            if "heatmap" not in st.session_state or st.session_state.heatmap is None:
                st.session_state.heatmap = create_heatmap(
                    df_obs, center=[41.36174441599461, 2.108076037807884]
                )
            if (
                "markermap" not in st.session_state
                or st.session_state.markermap is None
            ):
                st.session_state.markermap = create_markercluster(
                    df_obs, center=[41.36174441599461, 2.108076037807884]
                )
            map1, map2 = st.columns(2)
            with map1:
                map_html1 = st.session_state.heatmap._repr_html_()
                components.html(map_html1, height=600)

            with map2:
                map_html2 = st.session_state.markermap._repr_html_()
                components.html(map_html2, height=600)

    except FileNotFoundError:
        pass
