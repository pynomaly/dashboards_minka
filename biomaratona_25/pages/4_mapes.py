import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils import create_heatmap, create_markercluster

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/biomaratona_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )
# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARatona 2025",
)

# configuración de ModeBar
config_modebar = {
    "displayModeBar": True,  # Mostrar u ocultar la ModeBar
    "modeBarButtonsToRemove": [  # Lista de botones a remover
        "zoom2d",  # Eliminar el botón de zoom
        "pan2d",  # Eliminar el botón de paneo
        "lasso2d",  # Eliminar el botón de lazo
        "autoScale2d",  # Eliminar el botón de autoescalar
        "resetScale2d",  # Eliminar el botón de resetear escala
        "hoverClosestCartesian",  # Eliminar el botón de acercar el hover
        "hoverCompareCartesian",  # Eliminar el botón de comparar en hover
        "zoomIn2d",  # Eliminar el botón de zoom +
        "zoomOut2d",  # Eliminar el botón de zoom -
    ],
    "displaylogo": False,  # Ocultar el logo de Plotly
}

exclude_users = []

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 220px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 220px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 424, "name": "BioMARatona 2025"},
    {"id": 452, "name": "BioMARatona 2024"},
]

main_project = 424


with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Mapes]")

# Project selection
project_name = st.selectbox(
    label="Projecto a mostrar no mapa",
    options=("BioMARatona 2025", "BioMARatona 2024"),
    key="project_selector",  # Add a key for the selectbox
)

# Get the correct project ID
proj_id = next((p["id"] for p in projects if p["name"] == project_name), None)

# Create a unique key for each project
print(proj_id)
map_key = f"maps_{proj_id}"


# Only load maps if they don't exist in session_state or if project changed
if map_key not in st.session_state:
    try:
        df_map = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
        # Store both maps in a dictionary with this project's key
        st.session_state[map_key] = {
            "heatmap": create_heatmap(df_map),
            "markermap": create_markercluster(df_map),
        }
    except FileNotFoundError:
        st.error(f"No s'han trobat dades per {project_name}")

# Display the maps (from cache if available)
if map_key in st.session_state:
    map1, map2 = st.columns(2)

    with map1:
        map_html1 = st.session_state[map_key]["heatmap"]._repr_html_()
        components.html(map_html1, height=600)

    with map2:
        map_html2 = st.session_state[map_key]["markermap"]._repr_html_()
        components.html(map_html2, height=600)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organitzadors:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.markdown("##### Amb el finançament dels projectes europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
