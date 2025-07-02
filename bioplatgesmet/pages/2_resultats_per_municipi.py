# Contents of ~/my_app/pages/page_2.py
import os

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import folium_static, st_folium
from utils import (
    create_heatmap,
    create_markercluster,
    fig_provinces,
    get_best_observers,
    get_last_species,
    get_num_species_by_city,
)

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
st.markdown(
    """
    <style>
        body {
            background-color: white !important;
            color: black !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
# configuración de ModeBar
config_modebar = {
    "displayModeBar": True,  # Mostrar u ocultar la ModeBar
    "modeBarButtonsToRemove": [  # Lista de botones a remover
        "zoom2d",  # Eliminar el botón de zoom
        "pan2d",  # Eliminar el botón de paneo
        "select2d",  # Eliminar el botón de selección
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

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
places = {
    "Montgat": [357],
    "Castelldefels": [349],
    "Gavà": [350],
    "El Prat de Llobregat": [351],
    "Sant Adrià": [352],
    "Viladecans": [354],
    "Barcelona": [355, 356],
    "Badalona": [347, 348],
}

ciutats = [
    "Badalona",
    "Barcelona",
    "Castelldefels",
    "El Prat de Llobregat",
    "Gavà",
    "Montgat",
    "Sant Adrià del Besòs",
    "Viladecans",
]

main_project = 264


# Cacheado de datos
@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Columna izquierda
st.sidebar.markdown("# Municipis participants en aquest projecte:")
st.sidebar.markdown(
    """
* Badalona
* Barcelona
* Castelldefels
* El Prat de Llobregat
* Gavà
* Montgat
* Sant Adrià del Besòs
* Viladecans
"""
)

# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(":blue[Resultats per municipi]")


with st.container():

    # Ranking de ciudades, métricas totales
    city_total_metrics = load_csv(f"{directory}/data/city_total_metrics.csv")

    fig1 = fig_provinces(
        city_total_metrics, "observacions", "Nombre d’observacions", "#00567A"
    )
    fig2 = fig_provinces(
        city_total_metrics, "espècies", "Nombre d’espècies diferents", "#0081B8"
    )
    fig3 = fig_provinces(
        city_total_metrics, "participants", "Nombre de participants", "#009DE0"
    )

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
        csv4 = convert_df(city_total_metrics)

        st.download_button(
            label="Descarrega les dades",
            data=csv4,
            file_name="city_total_metrics.csv",
            mime="text/csv",
        )
    with col2:
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)
    with col3:
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

st.divider()

i = 0
for tab in st.tabs(
    [
        "\tBadalona\t",
        "\tBarcelona\t",
        "\tCastelldefels\t",
        "\tEl Prat de Llobregat\t",
        "\tGavà\t",
        "\tMontgat\t",
        "\tSant Adrià del Besòs\t",
        "\tViladecans\t",
    ]
):
    with tab:
        # st.header(ciutats[i])

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("**Últimes espècies registrades:**")
            results = get_last_species(ciutats[i])
            st.dataframe(
                results[["taxon_name", "url", "image"]],
                column_config={
                    "image": st.column_config.ImageColumn(
                        "Imatge (doble clic per ampliar)",
                        help="Previsualitza",
                        width=200,
                    ),
                    "url": st.column_config.LinkColumn(
                        "url",
                        width=275,
                    ),
                },
                hide_index=True,
            )

        with col2:
            st.markdown("**Espècies amb més observacions:**")
            df_species = get_num_species_by_city(ciutats[i])
            df_species["taxon_name"] = (
                f"https://minka-sdg.org/taxa/" + df_species["taxon_name"]
            )
            df_species.index = np.arange(1, len(df_species) + 1)
            st.data_editor(
                df_species,
                column_config={
                    "taxon_name": st.column_config.LinkColumn(
                        "nom", display_text=r"https://minka-sdg.org/taxa/(.*?)$"
                    ),
                    "observacions": st.column_config.NumberColumn(),
                },
                hide_index=False,
                height=210,
            )

        with col3:
            st.markdown("**Participants amb més observacions:**")
            df_observers = get_best_observers(ciutats[i])
            df_observers["nom"] = f"https://minka-sdg.org/users/" + df_observers["nom"]
            df_observers.index = np.arange(1, len(df_observers) + 1)
            st.dataframe(
                df_observers,
                column_config={
                    # "nom": st.column_config.TextColumn(width="medium"),
                    "nom": st.column_config.LinkColumn(
                        "nom", display_text=r"https://minka-sdg.org/users/(.*?)$"
                    ),
                    "observacions": st.column_config.NumberColumn(),
                },
                hide_index=False,
                height=210,
            )

        with st.container():
            st.header(f"Observacions per ciutat: {ciutats[i]}")
            city_name = ciutats[i]
            df = load_csv(f"{directory}/data/obs_{ciutats[i]}.csv")

            map1, map2 = st.columns([10, 10], gap="small")

            # Definir el centro del mapa
            center = [41.36174441599461, 2.108076037807884]

            # Usar claves únicas en session_state para cada ciudad
            heatmap_key = f"heatmap_city_{city_name}"
            markermap_key = f"markermap_city_{city_name}"

            # Guardar el mapa en session_state para evitar que desaparezca

            if heatmap_key not in st.session_state:
                st.session_state[heatmap_key] = create_heatmap(df, center=center)

            if markermap_key not in st.session_state:
                st.session_state[markermap_key] = create_markercluster(
                    df, center=center
                )

            # Renderizar los mapas con _repr_html_()
            with map1:
                map_html1 = st.session_state[heatmap_key]._repr_html_()
                components.html(map_html1, height=600)

            with map2:
                map_html2 = st.session_state[markermap_key]._repr_html_()
                components.html(map_html2, height=600)

            # Convertir dataframe y agregar botón de descarga
            csv5 = convert_df(df)

            st.download_button(
                label="Descarrega les dades",
                data=csv5,
                file_name=f"observacions_{ciutats[i]}.csv",
                mime="text/csv",
            )

        i += 1

st.container(height=50, border=False)

with st.container(border=True):
    col1, __, col2 = st.columns([10, 1, 5], gap="small")
    with col1:
        st.markdown("##### Organitzadors")
        st.image(
            f"{directory}/images/organizadores_bioplatgesmet_logos2.png",
        )
    with col2:
        st.markdown("##### Amb el finançament dels projectes europeus")
        st.image(
            f"{directory}/images/financiadores_bioplatgesmet_logos.png",
        )
