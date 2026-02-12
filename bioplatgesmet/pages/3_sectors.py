import os
import sys

import streamlit as st

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)

# Now import the rest
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from branca.colormap import LinearColormap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import create_footer, init_i18n, t

# Reducimos ancho de la barra lateral
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
init_i18n(current_page="sectors")


# Cache para mapas por parcelas
@st.cache_resource(ttl=3600, show_spinner=False)
def create_map(df_hash, field, caption_text, tooltip_aliases):
    """Crea mapa de parcelas con cache"""
    df_parcelas = pd.read_csv(f"{directory}/data/parcelas.csv")

    # Convertimos a GeoDataFrame (CRS WGS84)
    gdf = gpd.GeoDataFrame(
        df_parcelas,
        geometry=gpd.GeoSeries.from_wkt(df_parcelas["geometry"]),
        crs="EPSG:4326",
    )

    # Calcular centroide del conjunto de datos
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon], zoom_start=12, tiles="OpenStreetMap"
    )

    # Verificar si hay datos para colorear
    if gdf[field].sum() == 0:
        # Todos los valores son 0, usar color gris uniforme
        def style_function(feature):
            return {
                "fillColor": "#3d3d3d",
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.7,
            }

    else:
        # Escala de colores para valores > 0 (YlOrRd)
        colormap = LinearColormap(
            colors=[
                "#ffffcc",
                "#ffeda0",
                "#fed976",
                "#feb24c",
                "#fd8d3c",
                "#fc4e2a",
                "#e31a1c",
            ],
            vmin=gdf[field][gdf[field] > 0].min(),  # Mínimo excluyendo ceros
            vmax=gdf[field].max(),
        )

        # Función de estilo condicional
        def style_function(feature):
            num_obs = feature["properties"][field]
            return {
                "fillColor": "#3d3d3d" if num_obs == 0 else colormap(num_obs),
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.7,
            }

        # Añadir leyenda (solo para valores > 0)
        colormap.caption = caption_text
        colormap.add_to(m)

    # Añadir capa GeoJson con estilo personalizado
    folium.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Name", "Sectors", field],
            aliases=tooltip_aliases,
            style="background-color: white; color: #333333;",
        ),
    ).add_to(m)

    return m


# Cache para datos de parcelas
@st.cache_data(ttl=3600, show_spinner=False)
def load_parcelas_data():
    """Carga datos de parcelas con cache"""
    return pd.read_csv(f"{directory}/data/parcelas.csv")


BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
main_project = 264

# Mapeo de claves de traducción a nombres de columna en el CSV
grupos_biologicos_keys = [
    "plants",
    "mammals",
    "birds",
    "molluscs",
    "insects",
    "lepidoptera",
    "hymenoptera",
    "arachnids",
    "reptiles",
    "fungi_lichens",
]
grupos_biologicos_columns = [
    "Plantes",
    "Mamífers",
    "Ocells",
    "Mol·luscs",
    "Insectes",
    "Lepidòpters",
    "Himenòpter",
    "Aràcnid",
    "Rèptils",
    "Fongs i Líquens",
]

# Header
with st.container():
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.sectors_title')}]")

with st.container():
    df_parcelas = load_parcelas_data()

    # Crear opciones traducidas
    translated_groups = [t(f"sectors.{key}") for key in grupos_biologicos_keys]
    options = [t("ui.all_observations")] + translated_groups

    # Mapeo de nombre traducido a columna del CSV
    translation_to_column = dict(zip(translated_groups, grupos_biologicos_columns))

    field_display = st.selectbox(
        t("ui.select_observations"),
        options,
    )

    # Convertir selección a nombre de columna
    if field_display == t("ui.all_observations"):
        field = "num_obs"
    else:
        field = translation_to_column.get(field_display, "num_obs")

    # Textos traducidos para el mapa
    caption_text = t("charts.observations_count")
    tooltip_aliases = [
        t("sectors.name"),
        t("sectors.sector"),
        t("sectors.observations"),
    ]

    # Crear hash para cache del mapa (incluye idioma)
    lang = st.session_state.get("language", "ca")
    data_hash = hash(f"{field}_{df_parcelas.shape}_{df_parcelas[field].sum()}_{lang}")
    places_map = create_map(data_hash, field, caption_text, tooltip_aliases)

    map_html1 = places_map._repr_html_()
    components.html(map_html1, height=2000)

# Footer
create_footer()
