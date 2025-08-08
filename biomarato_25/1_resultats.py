# Run as streamlit run app_biomarato.py --server.port 9003

import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARató 2025",
)

import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    fig_area_evolution,
    fig_bars_months,
    fig_multi_year_comparison,
    get_grouped_monthly,
    get_last_week_metrics,
    get_main_metrics,
    get_previous_years,
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

colors = ["#5fbfbb", "#1e9ca3", "#0c6a83", "#de6719", "#fab954"]

exclude_users = [
    "xasalva",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
    "anomalia",
    "amaliacardenas",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "monyant",
    "ura4dive",
    "lauracoro",
    "pirotte_",
    "oceanicos",
    "abril",
    "alba_barrera",
    "amb_platges",
    "daniel_palacios",
    "davidpiquer",
    "laiamanyer",
    "rogerpuig",
    "guillemdavila",
    # vanessa,
    # teresa,
]
matomo_script = """
    <!-- Matomo -->
    <script>
    var _paq = window._paq = window._paq || [];
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
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

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 418, "name": "Girona"},
    {"id": 419, "name": "Tarragona"},
    {"id": 420, "name": "Barcelona"},
    {"id": 417, "name": "Catalunya"},
]

main_project = 417
project_id_gir = next((p["id"] for p in projects if p["name"] == "Girona"), None)
project_id_tarr = next((p["id"] for p in projects if p["name"] == "Tarragona"), None)
project_id_bcn = next((p["id"] for p in projects if p["name"] == "Barcelona"), None)


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


# Optimized data loading with caching
@st.cache_data(ttl=300, show_spinner="Carregant mètriques principals...")
def load_main_dashboard_data(project_id):
    """Load and cache main dashboard data"""
    try:
        total_species, total_participants, total_obs = get_main_metrics(project_id)
        lw_obs, lw_spe, lw_part = get_last_week_metrics(project_id)
        return total_species, total_participants, total_obs, lw_obs, lw_spe, lw_part
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


# Load main metrics with caching
total_species, total_participants, total_obs, lw_obs, lw_spe, lw_part = (
    load_main_dashboard_data(main_project)
)

# Load Matomo tracking asynchronously
if "matomo_loaded" not in st.session_state:
    components.html(matomo_script, height=0, width=0)
    st.session_state.matomo_loaded = True


# Main metrics (incluye todos los usuarios y todos los grados)
with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Resultats BioMARató 2025]")
        st.markdown(":orange[May 3, 2025 - Oct 15, 2025]")

    __, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    with col1:
        st.metric(
            ":camera_with_flash: Observacions",
            f"{total_obs:,}".replace(",", " "),
            f"+{total_obs - lw_obs:,} última setmana".replace(",", " "),
        )
    with col2:
        st.metric(
            ":ladybug: Espècies",
            f"{total_species:,}".replace(",", " "),
            f"+{total_species - lw_spe} última setmana",
        )
    with col3:
        st.metric(
            ":eyes: Participants",
            f"{total_participants:,}".replace(",", " "),
            f"+{total_participants - lw_part} última setmana",
        )

    style_metric_cards(
        background_color="#fef7eb",
        border_left_color="#f9b853",
        box_shadow=False,
    )


# Cached data loading for evolution charts
@st.cache_data(ttl=600, show_spinner="Preparant gràfics d'evolució...")
def load_main_metrics_data(directory_path):
    """Load and process main metrics data with caching"""
    main_metrics = pd.read_csv(f"{directory_path}/data/main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )
    main_metrics["data"] = pd.to_datetime(main_metrics["data"])
    main_metrics_filtered = main_metrics[
        main_metrics["data"] <= datetime.today()
    ].reset_index(drop=True)
    return main_metrics_filtered


with st.container():
    # Evolution lines with cached data
    main_metrics_filtered = load_main_metrics_data(directory)

    # Evolution charts in three parallel columns
    col1_line, col2_line, col3_line = st.columns(3)

    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics_filtered,
            field="observacions",
            title="Nombre d'observacions",
            color="#089aa2",
        )
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics_filtered,
            field="espècies",
            title="Nombre d'espècies",
            color="#dc6619",
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics_filtered,
            field="participants",
            title="Nombre de participants",
            color="#f9b853",
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)


# Cached monthly data loading
@st.cache_data(ttl=1800, show_spinner="Carregant dades mensuals...")
def load_monthly_data(project_id, year):
    """Load monthly grouped data with caching"""
    return get_grouped_monthly(project_id=project_id, year=year)


with st.container():
    # Resultados mensuales with caching
    grouped = load_monthly_data(main_project, "2025")
    # Monthly charts - always visible
    col1_month, col2_month, col3_month = st.columns(3)
    with col1_month:
        fig1b = fig_bars_months(
            grouped,
            field="observacions",
            title="Observacions per mes",
            color="#089aa2",
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with col2_month:
        fig2b = fig_bars_months(
            grouped,
            field="espècies",
            title="Espècies per mes",
            color="#dc6619",
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with col3_month:
        fig3b = fig_bars_months(
            grouped,
            field="participants",
            title="Participants per mes",
            color="#f9b853",
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)


# Cached previous years data
@st.cache_data(ttl=3600, show_spinner="Carregant comparatives d'anys anteriors...")
def load_comparison_data(main_metrics_filtered):
    """Load previous years data for comparison with caching"""
    return get_previous_years(main_metrics_filtered)


with st.container():
    st.subheader(":orange[Comparativa de resultats entre BioMARatons (2022-2025)]")
    # Datos de años anteriores with caching
    df_2022_filtered, df_2023_filtered, df_2024_filtered = load_comparison_data(
        main_metrics_filtered
    )
    # Comparison charts - always visible
    col1_comp, col2_comp, col3_comp = st.columns(3)

    with col1_comp:
        fig1_comp = fig_multi_year_comparison(
            df_list=[
                df_2022_filtered,
                df_2023_filtered,
                df_2024_filtered,
                main_metrics_filtered,
            ],
            years=["2022", "2023", "2024", "2025"],
            field="observacions",  # Columna a comparar
            colors=[
                "#FF9E4A",
                "#1F77B4",
                "#2CA02C",
                "#D62728",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig1_comp, config=config_modebar, use_container_width=True)

    with col2_comp:
        fig2_comp = fig_multi_year_comparison(
            df_list=[
                df_2022_filtered,
                df_2023_filtered,
                df_2024_filtered,
                main_metrics_filtered,
            ],
            years=["2022", "2023", "2024", "2025"],
            field="espècies",  # Columna a comparar
            colors=[
                "#FF9E4A",
                "#1F77B4",
                "#2CA02C",
                "#D62728",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig2_comp, config=config_modebar, use_container_width=True)

    with col3_comp:
        fig3_comp = fig_multi_year_comparison(
            df_list=[
                df_2022_filtered,
                df_2023_filtered,
                df_2024_filtered,
                main_metrics_filtered,
            ],
            years=["2022", "2023", "2024", "2025"],
            field="participants",  # Columna a comparar
            colors=[
                "#FF9E4A",
                "#1F77B4",
                "#2CA02C",
                "#D62728",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig3_comp, config=config_modebar, use_container_width=True)


with st.container():
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Rànquing de participants]")
    st.markdown("Nombre d'observacions amb grau de recerca.")
    try:
        pd.read_csv(f"{directory}/data/{main_project}_pt_users.csv")
        col0, col1, col2, col3 = st.columns([4, 1, 4, 1])

        # Optimized ranking with better caching
        with col0:
            # Cached user ranking processing
            @st.cache_data(
                ttl=600, show_spinner="Carregant rànquing de participants..."
            )
            def load_user_ranking(directory_path, project_id, exclude_users_list):
                """Load and process user ranking data with caching"""
                try:
                    pt_users = pd.read_csv(
                        f"{directory_path}/data/{project_id}_pt_users.csv"
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
            pt_users_data = load_user_ranking(directory, main_project, exclude_users)

            # Tabla

            if not pt_users_data.empty:
                st.dataframe(
                    pt_users_data[["participant", "observacions", "espècies"]],
                    use_container_width=True,
                    height=210,
                )
            else:
                st.info("No hi ha dades de participants disponibles")
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
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Agraïments]")

    # Cached participants list loading
    @st.cache_data(ttl=1800, show_spinner="Carregant llista de participants...")
    def load_participants_list(directory_path, project_id):
        """Load and process participants list with caching"""
        try:
            df_total = pd.read_csv(
                f"{directory_path}/data/{project_id}_df_obs.csv", usecols=["user_login"]
            )
            list_participants = df_total.user_login.unique()
            list_participants.sort()
            linked_list = [
                f"[{p}](https://minka-sdg.org/users/{p})" for p in list_participants
            ]
            return ", ".join(linked_list)
        except FileNotFoundError:
            return "No hi ha dades de participants disponibles"
        except Exception as e:
            return f"Error carregant participants: {e}"

    st.markdown("A la Biomarató 2025 de Catalunya han participat:")
    participants_text = load_participants_list(directory, main_project)
    st.markdown(participants_text)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organitzadors:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.markdown("##### Amb el finançament dels projectes europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
