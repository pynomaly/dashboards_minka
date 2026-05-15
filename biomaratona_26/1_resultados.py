# Run as streamlit run app_biomarato.py --server.port 9003

import os
import time
from datetime import datetime, timedelta
import config
import pandas as pd
import streamlit as st

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARatona 2025",
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

# Optimized CSS - apply once
if "css_applied" not in st.session_state:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                width: 300px !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: 300px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.css_applied = True

with st.sidebar:
    st.write(
        """Descobre a biodiversidade única das costas de Portugal de uma forma divertida e educativa! Na BioMaratona, tu e a tua família transformam-se em verdadeiros cientistas-cidadãos, explorando e registrando as incríveis espécies da região.
    Identifica a biodiversidade em saídas de campo emocionantes, contribui para um projeto nacional de ciência cidadã, conecta-te com a natureza, junta-te a nós nesta missão científica – cada observação conta!"""
    )

# Cache metrics in session state to avoid repeated API calls
if (
    "main_metrics_cache" not in st.session_state
    or st.session_state.get("cache_time", 0) < time.time() - 300
):  # 5 min cache
    try:
        total_species, total_participants, total_obs = get_main_metrics(
            config.MAIN_PROJ
        )
        lw_obs, lw_spe, lw_part = get_last_week_metrics(config.MAIN_PROJ)
        st.session_state.main_metrics_cache = {
            "total_species": total_species,
            "total_participants": total_participants,
            "total_obs": total_obs,
            "lw_obs": lw_obs,
            "lw_spe": lw_spe,
            "lw_part": lw_part,
        }
        st.session_state.cache_time = time.time()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()
else:
    # Use cached values
    cache = st.session_state.main_metrics_cache
    total_species = cache["total_species"]
    total_participants = cache["total_participants"]
    total_obs = cache["total_obs"]
    lw_obs = cache["lw_obs"]
    lw_spe = cache["lw_spe"]
    lw_part = cache["lw_part"]


# Main metrics (incluye todos los usuarios y todos los grados)
with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":orange[Resultados BioMARatona {config.YEAR}]")
        st.markdown(f":orange[{config.PROJ_DATES}]")

    __, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    with col1:
        st.metric(
            ":camera_with_flash: Observações",
            f"{total_obs:,}".replace(",", " "),
            f"+{total_obs - lw_obs:,} últimos 7 dias".replace(",", " "),
        )
    with col2:
        st.metric(
            ":ladybug: Espécies",
            f"{total_species:,}".replace(",", " "),
            f"+{total_species - lw_spe} últimos 7 dias",
        )
    with col3:
        st.metric(
            ":eyes: Participantes",
            f"{total_participants:,}".replace(",", " "),
            f"+{total_participants - lw_part} últimos 7 dias",
        )

    style_metric_cards(
        background_color="#fef7eb",
        border_left_color="#f9b853",
        box_shadow=False,
    )


@st.cache_data(ttl=300)
def load_and_process_main_metrics():
    main_metrics = pd.read_csv(f"{directory}/data/main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observações",
            "species": "espécies",
            "participants": "participantes",
        },
        inplace=True,
    )
    main_metrics["data"] = pd.to_datetime(main_metrics["data"])
    main_metrics_filtered = main_metrics[
        main_metrics["data"] <= datetime.today()
    ].reset_index(drop=True)
    return main_metrics_filtered


with st.container():
    # Evolution lines - use cached function
    main_metrics_filtered = load_and_process_main_metrics()

    col1_line, col2_line, col3_line = st.columns(3)

    # Create charts more efficiently with batch processing
    chart_configs = [
        ("observações", "Número de observações", config.COLORS[1]),
        ("espécies", "Número de espécies", config.COLORS[3]),
        ("participantes", "Número de participantes", config.COLORS[4]),
    ]

    columns = [col1_line, col2_line, col3_line]

    for i, (field, title, color) in enumerate(chart_configs):
        with columns[i]:
            fig = fig_area_evolution(
                df=main_metrics_filtered,
                field=field,
                title=title,
                color=color,
            )
            st.plotly_chart(fig, config=config_modebar, use_container_width=True)

with st.container():
    # Resultados mensuales - cached
    grouped = get_grouped_monthly(project_id=config.MAIN_PROJ, year=config.YEAR)
    col1_month, col2_month, col3_month = st.columns(3)

    # Monthly charts with same config as evolution charts
    monthly_configs = [
        ("observações", "Observações por mês", config.COLORS[1]),
        ("espécies", "Espécies por mês", config.COLORS[3]),
        ("participantes", "Participantes por mês", config.COLORS[4]),
    ]

    monthly_columns = [col1_month, col2_month, col3_month]

    for i, (field, title, color) in enumerate(monthly_configs):
        with monthly_columns[i]:
            fig = fig_bars_months(grouped, field=field, title=title, color=color)
            st.plotly_chart(fig, config=config_modebar, use_container_width=True)


with st.container():
    st.subheader(":orange[Comparação de resultados entre BioMARatonas (2024-2026)]")
    # Datos de años anteriores
    df_2024_filtered = get_previous_years(main_metrics_filtered, 2024)
    df_2025_filtered = get_previous_years(main_metrics_filtered, 2025)
    col1_comp, col2_comp, col3_comp = st.columns(3)

    # Comparison charts with shared configuration
    comparison_configs = [("observações",), ("espécies",), ("participantes",)]

    comparison_columns = [col1_comp, col2_comp, col3_comp]

    # Shared data and configuration for all comparison charts
    df_list = [main_metrics_filtered, df_2025_filtered, df_2024_filtered]
    years = ["2026", "2025", "2024"]
    colors = ["#0c6a83", "#de6719", "#fab954"]

    for i, (field,) in enumerate(comparison_configs):
        with comparison_columns[i]:
            fig_comp = fig_multi_year_comparison(
                df_list=df_list, years=years, field=field, colors=colors
            )
            st.plotly_chart(fig_comp, config=config_modebar, use_container_width=True)


with st.container():
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(":orange[Classificação dos participantes]")
    # st.markdown("Número de observações com o grau de investigação.")

    @st.cache_data(ttl=3600)
    def load_and_process_users():
        try:
            pt_users_df = pd.read_csv(
                f"{directory}/data/{config.MAIN_PROJ}_pt_users.csv"
            )
            # Filter excluded users (exclude_users is already a set)
            pt_users_filtered = pt_users_df[
                ~pt_users_df.participant.isin(config.EXCLUDE_USERS)
            ].reset_index(drop=True)

            # Set index starting from 1
            pt_users_filtered.index = range(1, len(pt_users_filtered) + 1)

            # Format observations column
            pt_users_filtered["observacions_formatted"] = pt_users_filtered[
                "observacions"
            ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

            return pt_users_filtered
        except FileNotFoundError:
            return None

    pt_users_data = load_and_process_users()

    if pt_users_data is not None:
        col0, col1, col2, col3 = st.columns([4, 1, 4, 1])

        # Ranking general
        with col0:
            pt_users_display = pt_users_data[
                ["participant", "observacions_formatted", "espècies"]
            ].rename(
                columns={
                    "participant": "participante",
                    "observacions_formatted": "observações",
                    "espècies": "espécies",
                }
            )
            st.dataframe(
                pt_users_display,
                use_container_width=True,
                height=210,
            )
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
                        nombre = pt_users_data.loc[i, "participant"]
                        st.subheader(
                            f":{medals[i-1]}: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )
    else:
        st.markdown("Nenhum participante")

st.divider()

# Agradecimientos
with st.container():

    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(":orange[Agradecimentos]")
    st.markdown(f"Participaram da Biomaratona {config.YEAR}:")

    @st.cache_data(ttl=3600)
    def get_participants_list():
        try:
            df_total = pd.read_csv(
                f"{directory}/data/{config.MAIN_PROJ}_df_obs.csv",
                usecols=["user_login"],
            )
            list_participants = sorted(df_total.user_login.unique())
            linked_list = [
                f"[{p}](https://minka-sdg.org/users/{p})" for p in list_participants
            ]
            return ", ".join(linked_list)
        except FileNotFoundError:
            return None

    participants_text = get_participants_list()
    if participants_text:
        st.markdown(participants_text)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organizadores:")

        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

        col_21, col_22, __ = st.columns([2, 2, 1.5])
        with col_21:
            st.image(f"{directory}/images/logo_cibio2.jpeg")
        with col_22:
            st.image(f"{directory}/images/logo_biopolis_horizontal2.jpeg")

    with col_2:
        st.markdown("##### Com o financiamento de projetos europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
