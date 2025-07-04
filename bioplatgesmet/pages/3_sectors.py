import os

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from branca.colormap import LinearColormap
from shapely.geometry import shape
from streamlit_folium import folium_static, st_folium

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)

# Reducimos ancho de la barra lateral
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


# Mapa de parcelas
def create_map(df_parcelas, field):
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
        location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap"
    )

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

    # Añadir capa GeoJson con estilo personalizado
    folium.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Name", "Sectors", field],
            aliases=["Nom:", "Sector:", "Observacions:"],
            style="background-color: white; color: #333333;",
        ),
    ).add_to(m)

    # Añadir leyenda (solo para valores > 0)
    colormap.caption = "Nombre d'observacions"
    colormap.add_to(m)

    # Guardar y mostrar
    return m


BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
main_project = 264
grupos_biologicos = {
    "Plantes": 12,
    "Mamífers": 8,
    "Ocells": 5,  # aves
    "Mol·luscs": 15,
    "Insectes": 11,
    "Lepidòpters": 325,  # mariposas
    "Himenòpter": 326,  # abejas
    "Aràcnid": 9,
    "Rèptils": 6,
    "Fongs i Líquens": 13,
}

# Header
with st.container():
    st.header("Nombre d'observacions per parcel·la")

with st.container():
    df_parcelas = pd.read_csv(f"{directory}/data/parcelas.csv")

    options = list(["Totes les observacions"]) + list(grupos_biologicos.keys())

    field = st.selectbox(
        "Selecciona observacions a mostrar al mapa",
        options,
    )

    if field == "Totes les observacions":
        field = "num_obs"

    places_map = create_map(df_parcelas, field)

    map_html1 = places_map._repr_html_()
    components.html(map_html1, height=2000)
