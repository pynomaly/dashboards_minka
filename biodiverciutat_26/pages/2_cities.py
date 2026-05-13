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

from i18n import init_i18n, t

# Initialize i18n
init_i18n(current_page="municipalities")


@st.cache_data(ttl=300, show_spinner=False)
def load_metrics_cities(path):
    """Cache CSV loading for city metrics"""
    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_geo_df(main_proj):
    """Cache GeoDataFrame creation (expensive: reads GeoJSON + CSV + merge)"""
    return create_geo_df(main_proj)


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.municipalities_title')} {config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

# Ranking by cities
metrics_path = f"{directory}/data/{config.MAIN_PROJ}_main_metrics_projects.csv"
if not os.path.exists(metrics_path):
    st.warning(t("ui.no_data"))
else:
    main_metrics_cities = load_metrics_cities(metrics_path)

    with st.container():
        st.subheader(t("municipalities.most_active"))

        fig1 = fig_cities(
            main_metrics_cities,
            "observations",
            t("charts.observations_count"),
        )
        fig2 = fig_cities(
            main_metrics_cities,
            "species",
            t("charts.species_count"),
        )
        fig3 = fig_cities(
            main_metrics_cities,
            "participants",
            t("charts.participants_count"),
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
            options_map = {
                t("metrics.observations"): "Observacions",
                t("metrics.species"): "Espècies",
                t("metrics.participants"): "Participants",
            }
            color_label = st.selectbox(
                t("municipalities.paint_map"), list(options_map.keys())
            )
            color_option = options_map[color_label]

        datos_mapa = get_cached_geo_df(config.MAIN_PROJ)
        mask = datos_mapa["project"] != 499
        datos_mapa = datos_mapa[mask]
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
            + f"{color_label}: %{{z}}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer con fondo de color
image_footer = f"{directory}/images/footer.png"

st.markdown(
    f"""
    <div style="background-color: {config.COLORS[1]}; padding: 10px; margin-top: 10px; border-radius: 10px;">
        <img src="data:image/png;base64,{__import__('base64').b64encode(open(image_footer, 'rb').read()).decode()}"
             style="width: 100%; display: block;">
    </div>
    """,
    unsafe_allow_html=True,
)
