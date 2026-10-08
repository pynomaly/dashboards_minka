# Run as streamlit run 1_results.py --server.port 9003
# Main page showing summary of all places

import os

import config
import pandas as pd
import streamlit as st

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

from i18n import create_sidebar_content, init_i18n, t
from streamlit_extras.metric_cards import style_metric_cards
from utils import fig_area_evolution, get_project_metrics

# Initialize i18n
init_i18n(current_page="main")
create_sidebar_content()


# Cached functions for performance
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_project_metrics(project_id):
    """Cache API calls for project metrics"""
    return get_project_metrics(project_id)


st.markdown(
    """
    <style>
        /* Forzar tema claro sobrescribiendo variables CSS de Streamlit */
        :root {
            --background-color: #FFFFFF !important;
            --secondary-background-color: #F1F9F5 !important;
            --text-color: #262730 !important;
            --font: "Source Sans Pro", sans-serif !important;
        }

        /* Sobrescribir colores del body y contenedor principal */
        .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stHeader"], .main, .block-container {
            background-color: #FFFFFF !important;
            color: #262730 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            width: 300px !important;
            background-color: #F1F9F5 !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 300px !important;
            background-color: #F1F9F5 !important;
        }
        [data-testid="stSidebarContent"] {
            background-color: #F1F9F5 !important;
        }

        /* Texto y elementos */
        p, span, label, .stMarkdown, h1, h2, h3, h4, h5, h6 {
            color: #262730 !important;
        }

        /* Widgets */
        [data-testid="stMetric"], [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
            color: #262730 !important;
        }

        /* Tablas */
        [data-testid="stDataFrame"], .dataframe {
            background-color: #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.main_title')} {config.PROJ_NAME}]")
        st.markdown(f":green[{t('header.subtitle')}]")
        st.markdown(f":green[{config.PROJ_DATES}]")


# Get project metrics from API
try:
    total_species, total_participants, total_obs = get_cached_project_metrics(
        config.PROJECT_ID
    )
except Exception:
    st.warning(t("ui.no_data"))
    total_species = total_participants = total_obs = 0

# Tarjetas Main metrics (totales de todos los places)
with st.container():
    __, col1, col2, col3, _ = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric(
            t("metrics.observations"),
            f"{total_obs:,}".replace(",", "."),
        )
    with col2:
        st.metric(
            t("metrics.species"),
            f"{total_species:,}".replace(",", "."),
        )
    with col3:
        st.metric(
            t("metrics.participants"),
            f"{total_participants:,}".replace(",", "."),
        )
    style_metric_cards(
        background_color="#fff",
        border_left_color=f"{config.COLORS[1]}",
        box_shadow=False,
    )

# Daily evolution charts
project_metrics_path = f"{directory}/data/project_main_metrics.csv"
if os.path.exists(project_metrics_path):
    with st.container():
        project_metrics = pd.read_csv(project_metrics_path)
        project_metrics.rename(
            columns={
                "date": "data",
                "observations": "observacions",
                "species": "espècies",
            },
            inplace=True,
        )

        col1_line, col2_line, col3_line = st.columns(3, gap="large")

        with col1_line:
            fig1 = fig_area_evolution(
                df=project_metrics,
                field="observacions",
                title=t("charts.observations_per_day"),
                color=f"{config.COLORS[0]}",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2_line:
            fig2 = fig_area_evolution(
                df=project_metrics,
                field="espècies",
                title=t("charts.species_per_day"),
                color=f"{config.COLORS[1]}",
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3_line:
            fig3 = fig_area_evolution(
                df=project_metrics,
                field="participants",
                title=t("charts.participants_per_day"),
                color=f"{config.COLORS[2]}",
            )
            st.plotly_chart(fig3, use_container_width=True)

# Footer con fondo de color
image_footer = f"{directory}/images/footer.png"

if os.path.exists(image_footer):
    st.markdown(
        f"""
        <div style="background-color: {config.COLORS[1]}; padding: 10px; margin-top: 10px; border-radius: 10px;">
            <img src="data:image/png;base64,{__import__('base64').b64encode(open(image_footer, 'rb').read()).decode()}"
                 style="width: 100%; display: block;">
        </div>
        """,
        unsafe_allow_html=True,
    )
