import os

import config
import streamlit as st

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

# Now import the rest
from functools import lru_cache

import pandas as pd
import streamlit.components.v1 as components
from i18n import create_footer, init_i18n, t
from utils import create_heatmap, create_markercluster

# configuracion de ModeBar
config_modebar = {
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

matomo_script = """
    <!-- Matomo -->
    <script>
    var _paq = window._paq = window._paq || [];
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
        var u="//matomo.quanta-labs.com/";
        _paq.push(['setTrackerUrl', u+'matomo.php']);
        _paq.push(['setSiteId', '8']);
        var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
        g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
    })();
    </script>
    <!-- End Matomo Code -->
"""

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 300px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 300px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize i18n
init_i18n(current_page="maps")

with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":orange[{t('header.maps_title')}]")

# Project selection with performance hints
project_options = {
    "Catalunya": "Catalunya",
    "Tarragona": "Tarragona",
    "Barcelona": "Barcelona",
    "Girona": "Girona",
}

project_name = st.selectbox(
    label=t("maps_page.project_select_label"),
    options=list(project_options.keys()),
    format_func=lambda x: project_options[x],
    key="project_selector",
    help=t("maps_page.project_select_help"),
)

# Map id mapping
proj_id = config.PROJECTS_BY_NAME[project_name]

# Create a unique key for each project
map_key = f"maps_{proj_id}"


# Optimized data loading with caching and loading indicators
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_project_data(proj_id):
    """Load and cache project data"""
    try:
        return pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None


# Load data with progress indication
df_map = load_project_data(proj_id)

if df_map is None:
    st.error(t("maps_page.no_data_for").replace("{project}", project_name))
    st.stop()

num_points = len(df_map)


# Enhanced caching system - maps persist across sessions
@st.cache_resource(ttl=7200, show_spinner="Generant mapes...")  # Cache for 2 hours
def create_cached_maps(proj_id, data_hash):
    """Create and cache both maps to avoid recreation"""
    try:
        # Load data fresh for map creation
        df_map = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")

        # Create both maps
        heatmap = create_heatmap(df_map)
        markermap = create_markercluster(df_map)

        return {
            "heatmap": heatmap,
            "markermap": markermap,
            "created_at": pd.Timestamp.now(),
            "num_points": len(df_map),
        }
    except Exception as e:
        st.error(f"Error creant mapes: {e}")
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
            t("maps_page.maps_loaded").replace("{project}", project_name).replace("{count}", f"{cached_maps['num_points']:,}")
        )
    else:
        st.error(t("maps_page.maps_error"))

# Display the maps with enhanced UX
if map_key in st.session_state:
    # Add map selection for better UX with large datasets
    if num_points > 10000:
        map_type = st.radio(
            t("maps_page.visualization_type"),
            options=[t("maps_page.both_maps"), t("maps_page.heatmap_only"), t("maps_page.markers_only")],
            horizontal=True,
        )
    else:
        map_type = t("maps_page.both_maps")

    if map_type == t("maps_page.both_maps"):
        map1, map2 = st.columns(2)

        with map1:
            st.subheader(t("maps_page.heatmap"))
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
            st.subheader(t("maps_page.markers"))
            markermap = st.session_state[map_key]["markermap"]
            if markermap:
                # Handle both HTML strings and folium objects
                if isinstance(markermap, str):
                    components.html(markermap, height=600, width=None, scrolling=False)
                else:
                    # Fallback for folium objects
                    map_html = markermap._repr_html_()
                    components.html(markermap, height=600, width=None, scrolling=False)

    elif map_type == t("maps_page.heatmap_only"):
        st.subheader(t("maps_page.heatmap"))
        heatmap = st.session_state[map_key]["heatmap"]
        if heatmap:
            if isinstance(heatmap, str):
                components.html(heatmap, height=600, width=None, scrolling=False)
            else:
                # Fallback for folium objects
                map_html = heatmap._repr_html_()
                components.html(map_html, height=600, width=None, scrolling=False)

    else:  # markers only
        st.subheader(t("maps_page.markers"))
        markermap = st.session_state[map_key]["markermap"]
        if markermap:
            if isinstance(markermap, str):
                components.html(markermap, height=600, width=None, scrolling=False)
            else:
                # Fallback for folium objects
                map_html = markermap._repr_html_()
                components.html(markermap, height=600, width=None, scrolling=False)

# Footer with logos
create_footer()
