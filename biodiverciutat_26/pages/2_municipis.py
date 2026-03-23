# Run as streamlit run app_biomarato.py --server.port XXXX

import os

import config
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import create_geo_df, fig_cities

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

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[Municipis participants a {config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

# Ranking by cities (incluye todos los usuarios y grado research)
metrics_path = f"{directory}/data/{config.MAIN_PROJ}_main_metrics_projects.csv"
if not os.path.exists(metrics_path):
    st.warning("Cap dada disponible")
else:
    with st.container():
        # Cabecera

        st.subheader("Quins municipis són els més actius?")
        if "main_metrics_cities" not in st.session_state:
            st.session_state.main_metrics_cities = pd.read_csv(metrics_path)

        # Gráfico de barras
        fig1 = fig_cities(
            st.session_state.main_metrics_cities, "observations", "Nombre d'observacions"
        )
        fig2 = fig_cities(
            st.session_state.main_metrics_cities, "species", "Nombre d'espècies diferents"
        )
        fig3 = fig_cities(
            st.session_state.main_metrics_cities,
            "participants",
            "Nombre de participants",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.plotly_chart(fig2, use_container_width=True)
        with col3:
            st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Mapas
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            color_option = st.selectbox(
                "Pintar el mapa per:", ("Observacions", "Espècies", "Participants")
            )

        # Especifica la ruta al archivo GeoJSON

        datos_mapa = create_geo_df(config.MAIN_PROJ)
        fig = px.choropleth_map(
            data_frame=datos_mapa,
            geojson=datos_mapa.geometry.__geo_interface__,
            locations=datos_mapa["Area"],
            color=color_option,
            color_continuous_scale="Viridis",
            zoom=9,
            center={"lat": 41.4, "lon": 2.05},
            opacity=0.7,
            hover_name="city",
            hover_data={color_option: True, "Area": False},
            height=600,
        )

        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>"
            + f"{color_option}: %{{z}}<extra></extra>"
        )
        # Muestra el mapa
        st.plotly_chart(fig, use_container_width=True)
