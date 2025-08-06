import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils import create_heatmap, create_markercluster

# Performance constants
MAP_HEIGHT = 500  # Reduced from 600 for better performance
MAP_CACHE_TTL = 3600  # 1 hour cache
MAX_MAP_POINTS = 5000  # Limit points for better performance

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

# Optimize config - move to session state to avoid recreation
if "map_config_modebar" not in st.session_state:
    st.session_state.map_config_modebar = {
        "displayModeBar": True,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "pan2d",
            "lasso2d",
            "autoScale2d",
            "resetScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
            "zoomIn2d",
            "zoomOut2d",
        ],
        "displaylogo": False,
    }

# Remove unused variables for better performance
# exclude_users = []  # Commented out as unused

# Apply CSS only once per session for better performance
if "map_css_applied" not in st.session_state:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                width: 220px !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: 220px !important;
            }
            /* Optimize map rendering */
            .element-container {
                contain: layout style;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.map_css_applied = True

# Optimize constants (not needed for this page but kept for consistency)
BASE_URL = "https://minka-sdg.org"
API_PATH = "https://api.minka-sdg.org/v1"


# Optimize project data structure for faster lookup
PROJECTS = {"BioMARatona 2025": 424, "BioMARatona 2024": 452}
PROJECT_OPTIONS = tuple(PROJECTS.keys())  # Tuple is faster than list
MAIN_PROJECT = 424


with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Mapas]")

# Optimized project selection
project_name = st.selectbox(
    label="🗺️ Projecto a mostrar no mapa",
    options=PROJECT_OPTIONS,
    key="project_selector",
    help="Selecciona o projeto para visualizar no mapa",
)

# Efficient project ID lookup using dictionary
proj_id = PROJECTS.get(project_name)

if proj_id is None:
    st.error(f"⚠️ Project {project_name} not found")
    st.stop()

# Create a unique key for each project
map_key = f"maps_{proj_id}"


@st.cache_data(ttl=MAP_CACHE_TTL, max_entries=4, show_spinner="🗺️ Loading map data...")
def load_map_data_optimized(proj_id):
    """Ultra-optimized map data loading with sampling for large datasets"""
    try:
        # Load with optimized data types
        map_dtypes = {
            "latitude": "float32",  # Use float32 instead of float64 for memory efficiency
            "longitude": "float32",
            "taxon_name": "string",
            "user_login": "string",
            "id": "int32",
        }

        file_path = f"{directory}/data/{proj_id}_df_obs.csv"

        # Load data with optimizations
        df_map = pd.read_csv(
            file_path,
            usecols=list(map_dtypes.keys()),
            dtype=map_dtypes,
            engine="c",  # Use C engine for speed
        )

        if df_map.empty:
            return None

        # Clean data efficiently
        df_map = df_map.dropna(subset=["latitude", "longitude"])

        # Sample data if too large for better performance
        if len(df_map) > MAX_MAP_POINTS:
            df_map = df_map.sample(n=MAX_MAP_POINTS, random_state=42)
            st.info(
                f"📊 Showing sample of {MAX_MAP_POINTS:,} points for better performance"
            )

        return df_map

    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"⚠️ Error loading map data: {e}")
        return None


# Optimized map loading and creation
with st.spinner("🗺️ Preparing maps..."):
    df_map = load_map_data_optimized(proj_id)

# Create maps with better error handling and performance tracking
if df_map is not None:
    if map_key not in st.session_state:
        try:
            with st.spinner(f"🌍 Creating maps for {project_name}..."):
                # Create maps and store in session state
                heatmap = create_heatmap(df_map)
                markermap = create_markercluster(df_map)

                st.session_state[map_key] = {
                    "heatmap": heatmap,
                    "markermap": markermap,
                    "data_points": len(df_map),
                }

                st.success(f"✅ Maps created with {len(df_map):,} data points")

        except Exception as e:
            st.error(f"⚠️ Error creating maps for {project_name}: {e}")
            st.session_state[map_key] = None

else:
    st.warning(f"📊 No data found for {project_name}")

# Optimized map display with better organization
if map_key in st.session_state and st.session_state[map_key] is not None:

    # Add map type selector for better UX
    map_type = st.radio(
        "🗺️ Select map visualization:",
        ["Ambos os Mapas", "Apenas Mapa de Calor", "Apenas Marcadores"],
        horizontal=True,
        key="map_type_selector",
    )

    if map_type == "Ambos os Mapas":
        # Show both maps side by side
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔥 Heatmap")
            try:
                map_html1 = st.session_state[map_key]["heatmap"]._repr_html_()
                components.html(map_html1, height=MAP_HEIGHT, scrolling=False)
            except Exception as e:
                st.error(f"Erro ao exibir heatmap: {e}")

        with col2:
            st.subheader("📍 Marker Clusters")
            try:
                map_html2 = st.session_state[map_key]["markermap"]._repr_html_()
                components.html(map_html2, height=MAP_HEIGHT, scrolling=False)
            except Exception as e:
                st.error(f"Erro ao exibir marker map: {e}")

    elif map_type == "Apenas Mapa de Calor":
        st.subheader("🔥 Density Heatmap")
        try:
            map_html1 = st.session_state[map_key]["heatmap"]._repr_html_()
            components.html(map_html1, height=MAP_HEIGHT + 100, scrolling=False)
        except Exception as e:
            st.error(f"Erro ao exibir heatmap: {e}")

    else:  # Marker Clusters Only
        st.subheader("📍 Interactive Marker Clusters")
        try:
            map_html2 = st.session_state[map_key]["markermap"]._repr_html_()
            components.html(map_html2, height=MAP_HEIGHT + 100, scrolling=False)
        except Exception as e:
            st.error(f"Erro ao exibir marker map: {e}")

else:
    st.info("🗺️ No maps available to display")

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
