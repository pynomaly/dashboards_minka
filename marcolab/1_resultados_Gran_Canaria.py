# Run as streamlit run app_biomarato.py --server.port 9003

import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    fig_area_evolution,
    fig_bars_months,
    get_grouped_monthly,
    get_last_week_metrics,
    get_main_metrics,
)

# Variable de entorno para el directorio
try:
    DIRECTORY = f"{os.environ['DASHBOARDS']}/marcolab"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{DIRECTORY}/images/minka-logo.png",
    page_title="Dashboard MarCoLab",
)


# configuración de ModeBar
config_modebar = {
    "displayModeBar": True,  # Mostrar u ocultar la ModeBar
    "modeBarButtonsToRemove": [  # Lista de botones a remover
        "zoom2d",  # Eliminar el botón de zoom
        "pan2d",  # Eliminar el botón de paneo
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

colors = ["#012644", "#496cc0", "#43c0bb", "#de6719", "#fab954"]

exclude_users = [
    "xasalva",
    "jaume-piera",
    "elibonfill",
    "adrisoacha",
    "anonimousminkacontributor",
    "loreto_rodriguez",
]

parser_lang = {
    "date": "fecha",
    "observations": "observaciones",
    "species": "especies",
    "participants": "participantes",
}


BASE_URL = "https://minka-sdg.org"
API_PATH = "https://api.minka-sdg.org/v1"
PROJECT_LOGO = "PHAROS_White_Background.png"

MAIN_PROJECT = 580
MAIN_PROJECT_NAME = "MarCoLab Gran Canaria"

# Reducimos ancho de la barra lateral
st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 250px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 250px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Optimized data loading with caching
@st.cache_data(ttl=300, show_spinner="Cargando métricas principales...")
def load_main_dashboard_data(p_id):
    """Load and cache main dashboard data"""
    try:
        total_species, total_participants, total_obs = get_main_metrics(p_id)
        lw_obs, lw_spe, lw_part = get_last_week_metrics(p_id)
        return total_species, total_participants, total_obs, lw_obs, lw_spe, lw_part
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


# Load main metrics with caching
total_species, total_participants, total_obs, lw_obs, lw_spe, lw_part = (
    load_main_dashboard_data(MAIN_PROJECT)
)


# Main metrics (incluye todos los usuarios y todos los grados)
with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{DIRECTORY}/images/{PROJECT_LOGO}")
    with col2:
        st.header(f":orange[Resultados {MAIN_PROJECT_NAME}]")
        # st.markdown(":blue[31 enero 2026]")

    __, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    with col1:
        st.metric(
            f":camera_with_flash: {parser_lang['observations'].capitalize()}",
            f"{total_obs:,}".replace(",", " "),
        )
    with col2:
        st.metric(
            f":ladybug: {parser_lang['species'].capitalize()}",
            f"{total_species:,}".replace(",", " "),
        )
    with col3:
        st.metric(
            f":eyes: {parser_lang['species'].capitalize()}",
            f"{total_participants:,}".replace(",", " "),
        )

    style_metric_cards(
        background_color="#ffffff",
        border_left_color="#43c0bb",
        box_shadow=False,
    )


# Cached data loading for evolution charts
@st.cache_data(ttl=600, show_spinner="Preparando gráficos de evolución...")
def load_main_metrics_data(MAIN_PROJECT):
    """Load and process main metrics data with caching"""
    main_metrics = pd.read_csv(f"{DIRECTORY}/data/{MAIN_PROJECT}_main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": parser_lang["date"],
            "observations": parser_lang["observations"],
            "species": parser_lang["species"],
            "participants": parser_lang["participants"],
        },
        inplace=True,
    )
    main_metrics[parser_lang["date"]] = pd.to_datetime(
        main_metrics[parser_lang["date"]]
    )
    main_metrics_filtered = main_metrics[
        main_metrics[parser_lang["date"]] <= datetime.today()
    ].reset_index(drop=True)
    return main_metrics_filtered


with st.container():
    # Evolution lines with cached data
    main_metrics_filtered = load_main_metrics_data(MAIN_PROJECT)

    # Evolution charts in three parallel columns
    col1_line, col2_line, col3_line = st.columns(3)

    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics_filtered,
            field=parser_lang["observations"],
            title="Número de observaciones",
            color="#012644",
        )
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics_filtered,
            field=parser_lang["species"],
            title="Número de especies",
            color="#496cc0",
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics_filtered,
            field="participantes",
            title="Número de participantes",
            color="#43c0bb",
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)


# Cached monthly data loading
@st.cache_data(ttl=1800, show_spinner="Cargando datos...")
def load_monthly_data(project_id):
    """Load monthly grouped data with caching"""
    return get_grouped_monthly(project_id=project_id)


with st.container():
    # Resultados mensuales with caching
    grouped = load_monthly_data(MAIN_PROJECT)
    # Monthly charts - always visible
    col1_month, col2_month, col3_month = st.columns(3)
    with col1_month:
        fig1b = fig_bars_months(
            grouped,
            field=parser_lang["observations"],
            title="Observaciones por mes",
            color="#012644",
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with col2_month:
        fig2b = fig_bars_months(
            grouped,
            field=parser_lang["species"],
            title="Especies por mes",
            color="#496cc0",
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with col3_month:
        fig3b = fig_bars_months(
            grouped,
            field="participantes",
            title="Participantes por mes",
            color="#43c0bb",
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)

with st.container():
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{DIRECTORY}/images/PHAROS_White_Background.png")
    with col2:
        st.header(":orange[Ranking de participantes]")
    st.markdown("Número de observaciones con grado de investigación.")
    try:
        pd.read_csv(f"{DIRECTORY}/data/{MAIN_PROJECT}_pt_users.csv")
        col0, col1, col2, col3 = st.columns([4, 1, 4, 1])

        # Optimized ranking with better caching
        with col0:
            # Cached user ranking processing
            @st.cache_data(ttl=600, show_spinner="Cargando ranking de participantes...")
            def load_user_ranking(project_id, exclude_users_list):
                """Load and process user ranking data with caching"""
                try:
                    pt_users = pd.read_csv(
                        f"{DIRECTORY}/data/{project_id}_pt_users.csv"
                    )
                    pt_users = pt_users[
                        ~pt_users.participant.isin(exclude_users_list)
                    ].reset_index(drop=True)
                    pt_users.index = range(
                        pt_users.index.start + 1,
                        pt_users.index.stop + 1,
                    )
                    pt_users["observacions"] = pt_users["observacions"].apply(
                        lambda x: "{:,.0f}".format(x).replace(",", " ")
                    )
                    return pt_users
                except Exception as e:
                    st.error(f"Error loading user rankings: {e}")
                    return pd.DataFrame()

            # Load ranking data
            pt_users_data = load_user_ranking(MAIN_PROJECT, exclude_users)

            # Tabla

            if not pt_users_data.empty:
                st.dataframe(
                    pt_users_data[["participant", "observacions", "espècies"]],
                    use_container_width=True,
                    height=210,
                )
            else:
                st.info("No hay datos de participantes disponibles")
        with col2:
            # Medallas
            col1b, __ = st.columns([10, 1])
            with col1b:
                if len(pt_users_data) > 0:
                    medals = [
                        "first_place_medal",
                        "second_place_medal",
                        "third_place_medal",
                    ]
                    for i in range(1, min(4, len(pt_users_data) + 1)):
                        if i in pt_users_data.index:
                            nombre = pt_users_data.loc[i, "participant"]
                            st.subheader(
                                f":{medals[i-1]}: [{nombre}](https://minka-sdg.org/users/{nombre})"
                            )
    except FileNotFoundError:
        st.markdown("Cap participant")

st.divider()

# Agradecimientos
with st.container():

    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{DIRECTORY}/images/PHAROS_White_Background.png")
    with col2:
        st.header(":orange[Agradecimientos]")

    # Cached participants list loading
    @st.cache_data(ttl=1800, show_spinner="Cargando lista de participantes...")
    def load_participants_list(project_id):
        """Load and process participants list with caching"""
        try:
            df_total = pd.read_csv(
                f"{DIRECTORY}/data/{project_id}_df_obs.csv", usecols=["user_login"]
            )
            list_participants = df_total.user_login.unique()
            list_participants.sort()
            linked_list = [
                f"[{p}](https://minka-sdg.org/users/{p})" for p in list_participants
            ]
            return ", ".join(linked_list)
        except FileNotFoundError:
            return "No hay datos de participantes disponibles"
        except Exception as e:
            return f"Error cargando participantes: {e}"

    st.markdown(f"En {MAIN_PROJECT_NAME} han participado:")
    participants_text = load_participants_list(MAIN_PROJECT)
    st.markdown(participants_text)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organizadores:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{DIRECTORY}/images/footer_recortado_1.png")

    with col_2:
        st.markdown("##### Con la financiación de los proyectos europeos:")
        st.image(f"{DIRECTORY}/images/footer_recortado_2.png")
