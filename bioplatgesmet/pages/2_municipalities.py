# Contents of ~/my_app/pages/page_2.py
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
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from streamlit_folium import folium_static, st_folium

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from i18n import create_footer, init_i18n, t
from utils import (
    create_heatmap,
    create_markercluster,
    fig_provinces,
    get_best_observers,
    get_last_species,
    get_num_species_by_city,
)
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
init_i18n(current_page="municipalities")

# configuracion de ModeBar
config_modebar = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "select2d",
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

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
places = {
    "Montgat": [357],
    "Castelldefels": [349],
    "Gava": [350],
    "El Prat de Llobregat": [351],
    "Sant Adria": [352],
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


# Cacheado de datos optimizado
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_city_metrics():
    """Carga metricas totales por ciudad"""
    return pd.read_csv(f"{directory}/data/city_total_metrics.csv")


@st.cache_data(ttl=900, show_spinner=False)
def load_city_observations(city_name):
    """Carga observaciones por ciudad"""
    return pd.read_csv(f"{directory}/data/obs_{city_name}.csv")


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_city_data(city_name):
    """Obtiene todos los datos de una ciudad de forma cacheada"""
    last_species = get_last_species(city_name)
    species_count = get_num_species_by_city(city_name)
    best_observers = get_best_observers(city_name)

    # Procesar datos de especies
    species_count["taxon_name"] = (
        f"https://minka-sdg.org/taxa/" + species_count["taxon_name"]
    )
    species_count.index = np.arange(1, len(species_count) + 1)

    # Procesar datos de observadores
    best_observers["nom"] = f"https://minka-sdg.org/users/" + best_observers["nom"]
    best_observers.index = np.arange(1, len(best_observers) + 1)

    return last_species, species_count, best_observers


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


# Header
with st.container():
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.municipalities_title')}]")


with st.container():
    # Ranking de ciudades, metricas totales
    city_total_metrics = load_city_metrics()

    fig1 = fig_provinces(
        city_total_metrics, "observacions", t("charts.observations_count"), "#00567A"
    )
    fig2 = fig_provinces(
        city_total_metrics, "espècies", t("charts.species_count"), "#0081B8"
    )
    fig3 = fig_provinces(
        city_total_metrics, "participants", t("charts.participants_count"), "#009DE0"
    )

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
        if "csv4" not in st.session_state:
            st.session_state.csv4 = convert_df(city_total_metrics)

        st.download_button(
            label=t("ui.download_data"),
            data=st.session_state.csv4,
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
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{t('municipalities.last_species')}**")
            results, _, _ = get_cached_city_data(ciutats[i])
            st.dataframe(
                results[["taxon_name", "url", "image"]],
                column_config={
                    "image": st.column_config.ImageColumn(
                        t("municipalities.image_column"),
                        help="Preview",
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
            st.markdown(f"**{t('municipalities.most_observed_species')}**")
            _, df_species, _ = get_cached_city_data(ciutats[i])
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
            st.markdown(f"**{t('municipalities.top_participants')}**")
            _, _, df_observers = get_cached_city_data(ciutats[i])
            st.dataframe(
                df_observers,
                column_config={
                    "nom": st.column_config.LinkColumn(
                        "nom", display_text=r"https://minka-sdg.org/users/(.*?)$"
                    ),
                    "observacions": st.column_config.NumberColumn(),
                },
                hide_index=False,
                height=210,
            )

        with st.container():
            st.header(f"{t('ui.observations_by_city')}: {ciutats[i]}")
            city_name = ciutats[i]
            df = load_city_observations(ciutats[i])

            map1, map2 = st.columns([10, 10], gap="small")

            center = [41.36174441599461, 2.108076037807884]

            heatmap_key = f"heatmap_city_{city_name}"
            markermap_key = f"markermap_city_{city_name}"

            if heatmap_key not in st.session_state:
                st.session_state[heatmap_key] = create_heatmap(df, center=center)

            if markermap_key not in st.session_state:
                st.session_state[markermap_key] = create_markercluster(
                    df, center=center
                )

            with map1:
                map_html1 = st.session_state[heatmap_key]._repr_html_()
                components.html(map_html1, height=600)

            with map2:
                map_html2 = st.session_state[markermap_key]._repr_html_()
                components.html(map_html2, height=600)

            csv_key = f"csv5_{ciutats[i]}"
            if csv_key not in st.session_state:
                st.session_state[csv_key] = convert_df(df)

            st.download_button(
                label=t("ui.download_data"),
                data=st.session_state[csv_key],
                file_name=f"observacions_{ciutats[i]}.csv",
                mime="text/csv",
            )

        i += 1

# Footer
create_footer()
