# Run as streamlit run app_biomarato.py --server.port XXXX

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from utils import create_geo_df, fig_cities

st.set_page_config(layout="wide")

try:
    directory = f"{os.environ['DASHBOARDS']}/biodiverciutat_24"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

colors = ["#4aae79", "#007d8a", "#00a3b4"]

api_path = "https://api.minka-sdg.org/v1"

main_proj = 233

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


# Columna izquierda
st.sidebar.markdown("# Quins municipis hi participen?")
st.sidebar.markdown(
    """
* [Badalona](https://minka-sdg.org/projects/biodiverciutat-2024-badalona-repte-naturalista-urba)
* [Barberà del Vallès](https://minka-sdg.org/projects/biodiverciutat-2024-barbera-del-valles-repte-naturalista-urba)
* [Barcelona](https://minka-sdg.org/projects/biodiverciutat-2024-barcelona-repte-naturalista-urba)
* [Begues](https://minka-sdg.org/projects/biodiverciutat-2024-begues-repte-naturalista-urba)
* [Castellbisbal](https://minka-sdg.org/projects/biodiverciutat-2024-castellbisbal-repte-naturalista-urba)
* [Castelldefels](https://minka-sdg.org/projects/biodiverciutat-2024-castelldefels-repte-naturalista-urba)
* [Cervelló](https://minka-sdg.org/projects/biodiverciutat-2024-cervello-repte-naturalista-urba)
* [Corbera de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-corbera-de-llobregat-repte-naturalista-urba)
* [Cornellà de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-cornella-de-llobregat-repte-naturalista-urba)
* [El Papiol](https://minka-sdg.org/projects/biodiverciutat-2024-el-papiol-repte-naturalista-urba)
* [El Prat de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-el-prat-de-llobregat-repte-naturalista-urba)
* [Esplugues de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-esplugues-de-llobregat-repte-naturalista-urba)
* [Gavà](https://minka-sdg.org/projects/biodiverciutat-2024-gava-repte-naturalista-urba)
* [Hospitalet de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-hospitalet-de-llobregat-repte-naturalista-urba)
* [Molins de Rei](https://minka-sdg.org/projects/biodiverciutat-2024-molins-de-rei-repte-naturalista-urba)
* [Montcada i Reixac](https://minka-sdg.org/projects/biodiverciutat-2024-montcada-i-reixac-repte-naturalista-urba)
* [Montgat](https://minka-sdg.org/projects/biodiverciutat-2024-montgat-repte-naturalista-urba)
* [Pallejà](https://minka-sdg.org/projects/biodiverciutat-2024-palleja-repte-naturalista-urba)
* [Palma de Cervelló](https://minka-sdg.org/projects/biodiverciutat-2024-palma-de-cervello-repte-naturalista-urba)
* [Ripollet](https://minka-sdg.org/projects/biodiverciutat-2024-ripollet-repte-naturalista-urba)
* [Sant Adrià del Besós](https://minka-sdg.org/projects/biodiverciutat-2024-sant-adria-del-besos-repte-naturalista-urba)
* [Sant Andreu de la Barca](https://minka-sdg.org/projects/biodiverciutat-2024-sant-andreu-de-la-barca-repte-naturalista-urba)
* [Sant Boi de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-sant-boi-de-llobregat-repte-naturalista-urba)
* [Sant Climent de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-sant-climent-de-llobregat-repte-naturalista-urba)
* [Sant Cugat del Vallès](https://minka-sdg.org/projects/biodiverciutat-2024-sant-cugat-del-valles-repte-naturalista-urba)
* [Sant Feliu de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-sant-feliu-de-llobregat-repte-naturalista-urba)
* [Sant Joan Despí](https://minka-sdg.org/projects/biodiverciutat-2024-sant-joan-despi-repte-naturalista-urba)
* [Sant Just Desvern](https://minka-sdg.org/projects/biodiverciutat-2024-sant-just-desvern-repte-naturalista-urba)
* [Sant Vicenç dels Horts](https://minka-sdg.org/projects/biodiverciutat-2024-sant-vicenc-dels-horts-repte-naturalista-urba)
* [Santa Coloma de Cervelló](https://minka-sdg.org/projects/biodiverciutat-2024-santa-coloma-de-cervello-repte-naturalista-urba)
* [Santa Coloma de Gramenet](https://minka-sdg.org/projects/biodiverciutat-2024-santa-coloma-de-gramenet-repte-naturalista-urba)
* [Tiana](https://minka-sdg.org/projects/biodiverciutat-2024-tiana-repte-naturalista-urba)
* [Torrelles de Llobregat](https://minka-sdg.org/projects/biodiverciutat-2024-torrelles-de-llobregat-repte-naturalista-urba)
* [Viladecans](https://minka-sdg.org/projects/biodiverciutat-2024-viladecans-repte-naturalista-urba)
* [Àrea marina Barcelona](https://minka-sdg.org/projects/biodiverciutat-2024-area-marina-barcelona)
"""
)

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/LOGO OFICIAL_biodiverciutat_marca_rgbpositiu.png")
    with col2:
        st.header(":green[Municipis participants a BioDiverCiutat 2024]")
        st.markdown(":green[26 - 29 d'abril de 2024]")

# Ranking by cities (incluye todos los usuarios y grado research)
with st.container():
    # Cabecera

    st.subheader("Quins municipis són els més actius?")
    if "main_metrics_cities" not in st.session_state:
        st.session_state.main_metrics_cities = pd.read_csv(
            f"{directory}/data/{main_proj}_main_metrics_projects.csv"
        )

    # Gráfico de barras
    fig1 = fig_cities(
        st.session_state.main_metrics_cities, "observations", "Nombre d’observacions"
    )
    fig2 = fig_cities(
        st.session_state.main_metrics_cities, "species", "Nombre d’espècies diferents"
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
    datos_mapa = create_geo_df()
    fig = px.choropleth_map(
        data_frame=datos_mapa,
        geojson=datos_mapa.geometry.__geo_interface__,
        locations=datos_mapa[
            "Area"
        ],  # Otra opción puede ser 'NOMMUNI' si es único por municipio
        color=color_option,
        color_continuous_scale="Viridis",
        zoom=9,
        center={"lat": 41.4, "lon": 2.05},
        opacity=0.7,
        hover_name="city",  # Nombre que aparece al pasar el mouse sobre el municipio
        hover_data={"Area": False},
        height=600,
    )

    # Muestra el mapa
    st.plotly_chart(fig, use_container_width=True)
