import os
from functools import lru_cache

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils import create_heatmap, create_markercluster

# Variable de entorno para el directorio
try:
    DIRECTORY = f"{os.environ['DASHBOARDS']}/marcolab"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{DIRECTORY}/images/minka-logo.png",
    page_title="Dashboard MarCoLab",
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
            width: 250px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 250px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_URL = "https://minka-sdg.org"
API_PATH = "https://api.minka-sdg.org/v1"
PROJECT_LOGO = "PHAROS_White_Background.png"


projects = [
    {"id": 547, "name": "MarCoLab"},
    {"id": 581, "name": "MarCoLab Gran Canaria"},
    {"id": 580, "name": "MarCoLab Lanzarote"},
]

MAIN_PROJECT = 547


with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{DIRECTORY}/images/{PROJECT_LOGO}")
    with col2:
        st.header(":orange[Mapas]")

# Project selection with performance hints
project_options = {
    "MarCoLab": "MarCoLab",
    "Lanzarote": "MarCoLab Lanzarote",
    "Gran Canaria": "MarCoLab Gran Canaria",
}

project_name = st.selectbox(
    label="Área para mostrar en el mapa",
    options=list(project_options.keys()),
    format_func=lambda x: project_options[x],
    key="project_selector",
)

# Map id mapping
project_ids = {"MarCoLab": 547, "Lanzarote": 580, "Gran Canaria": 581}
proj_id = project_ids[project_name]

# Create a unique key for each project
map_key = f"maps_{proj_id}"


# Optimized data loading with caching and loading indicators
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_project_data(proj_id):
    """Load and cache project data"""
    try:
        return pd.read_csv(f"{DIRECTORY}/data/{proj_id}_df_obs.csv")
    except FileNotFoundError:
        return None


# Load data with progress indication
df_map = load_project_data(proj_id)

if df_map is None:
    st.error(f"No se han encontrado datos para {project_name}")
    st.stop()

num_points = len(df_map)


# Enhanced caching system - maps persist across sessions
@st.cache_resource(ttl=7200, show_spinner="Generando mapes...")  # Cache for 2 hours
def create_cached_maps(proj_id, data_hash):
    """Create and cache both maps to avoid recreation"""
    try:
        # Load data fresh for map creation
        df_map = pd.read_csv(f"{DIRECTORY}/data/{proj_id}_df_obs.csv")

        # Create both maps
        if proj_id in [581, 580]:
            zoom = 9
        else:
            zoom = 8
        heatmap = create_heatmap(df_map, zoom=zoom)
        markermap = create_markercluster(df_map, zoom=zoom)
        return {
            "heatmap": heatmap,
            "markermap": markermap,
            "created_at": pd.Timestamp.now(),
            "num_points": len(df_map),
        }
    except Exception as e:
        st.error(f"Error creando mapas: {e}")
        return None


# Generate a hash of the data to detect changes
data_hash = hash(df_map.shape[0])  # Simple hash based on row count

# Check if we need to create maps or force refresh due to new implementation
needs_refresh = (
    map_key not in st.session_state
    or
    # Force refresh if old heatmap is folium object instead of HTML string
    (
        map_key in st.session_state
        and not isinstance(st.session_state[map_key].get("heatmap"), str)
    )
    or
    # Check if data changed
    (
        map_key in st.session_state
        and st.session_state[map_key].get("num_points", 0) != num_points
    )
    or
    # Force refresh for JavaScript markercluster fix (always refresh for now)
    True  # Force refresh to apply JavaScript fixes
)

if needs_refresh:
    # Clear existing cache and create new maps
    create_cached_maps.clear()  # Clear the cache function
    cached_maps = create_cached_maps(proj_id, data_hash)

    if cached_maps:
        st.session_state[map_key] = cached_maps
        st.success(
            f"✅ Mapas cargados para {project_name} ({cached_maps['num_points']:,} observacions)"
        )
    else:
        st.error("No se ha podido cargar los mapas")

# Display the maps with enhanced UX
if map_key in st.session_state:
    # Add map selection for better UX with large datasets
    if num_points > 10000:
        map_type = st.radio(
            "Tipos de visualización:",
            options=["Ambos mapas", "Solo mapa de calor", "Solo mapa de marcadore"],
            horizontal=True,
        )
    else:
        map_type = "Ambos mapas"

    if map_type == "Ambos mapas":
        map1, map2 = st.columns(2)

        with map1:
            st.subheader("Mapa de calor")
            heatmap = st.session_state[map_key]["heatmap"]
            if heatmap:
                # Handle both HTML strings and folium objects
                if isinstance(heatmap, str):
                    components.html(heatmap, height=600, width=None, scrolling=False)
                else:
                    # Fallback for folium objects
                    map_html = heatmap._repr_html_()
                    components.html(map_html, height=600, width=None, scrolling=False)

        with map2:
            st.subheader("Mapa de marcadores")
            markermap = st.session_state[map_key]["markermap"]
            if markermap:
                # Handle both HTML strings and folium objects
                if isinstance(markermap, str):
                    components.html(markermap, height=600, width=None, scrolling=False)
                else:
                    # Fallback for folium objects
                    map_html = markermap._repr_html_()
                    components.html(markermap, height=600, width=None, scrolling=False)

    elif map_type == "Solo mapa de calor":
        st.subheader("Mapa de calor")
        heatmap = st.session_state[map_key]["heatmap"]
        if heatmap:
            if isinstance(heatmap, str):
                components.html(heatmap, height=600, width=None, scrolling=False)
            else:
                # Fallback for folium objects
                map_html = heatmap._repr_html_()
                components.html(map_html, height=600, width=None, scrolling=False)

    else:  # Només mapa de marcadors
        st.subheader("Mapa de marcadores")
        markermap = st.session_state[map_key]["markermap"]
        if markermap:
            if isinstance(markermap, str):
                components.html(markermap, height=600, width=None, scrolling=False)
            else:
                # Fallback for folium objects
                map_html = markermap._repr_html_()
                components.html(markermap, height=600, width=None, scrolling=False)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organizadores:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{DIRECTORY}/images/footer_recortado_1.png")

    with col_2:
        st.markdown("##### Con la financiación de los proyectos europeos:")
        st.image(f"{DIRECTORY}/images/footer_recortado_2.png")
