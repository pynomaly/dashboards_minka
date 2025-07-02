# Run as streamlit run app_biomarato.py --server.port 9003

import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/biomaratona_25"
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


base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 424, "name": "Biomaratona Norte"},
]

main_project = 424


# Reducimos ancho de la barra lateral
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

with st.sidebar:
    st.write(
        """Descobre a biodiversidade única das costas de Portugal de uma forma divertida e educativa! Na BioMaratona, tu e a tua família transformam-se em verdadeiros cientistas-cidadãos, explorando e registrando as incríveis espécies da região.
    Identifica a biodiversidade em saídas de campo emocionantes, contribui para um projeto nacional de ciência cidadã, conecta-te com a natureza, junta-te a nós nesta missão científica – cada observação conta!"""
    )

# Error si no responde la API
try:
    total_species, total_participants, total_obs = get_main_metrics(main_project)
    lw_obs, lw_spe, lw_part = get_last_week_metrics(main_project)
except:
    st.error("Error loading data")
    st.stop()


# Main metrics (incluye todos los usuarios y todos los grados)
with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Resultados BioMARatona 2025]")
        st.markdown(":orange[3 de maio - 15 de outubro de 2025]")

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


with st.container():
    # Evolution lines
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

    col1_line, col2_line, col3_line = st.columns(3)
    print(main_metrics_filtered.columns)
    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics_filtered,
            field="observações",
            title="Número de observações",
            color="#089aa2",
        )

        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics_filtered,
            field="espécies",
            title="Número de espécies",
            color="#dc6619",
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics_filtered,
            field="participantes",
            title="Número de participantes",
            color="#f9b853",
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

with st.container():
    # Resultados mensuales
    grouped = get_grouped_monthly(project_id=main_project, year="2025")
    # grouped["data"] = grouped["data"].astype(str)
    col1_month, col2_month, col3_month = st.columns(3)
    with col1_month:
        fig1b = fig_bars_months(
            grouped,
            field="observações",
            title="Observações por mês",
            color="#089aa2",
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with col2_month:
        fig2b = fig_bars_months(
            grouped,
            field="espécies",
            title="Espécies por mês",
            color="#dc6619",
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with col3_month:
        fig3b = fig_bars_months(
            grouped,
            field="participantes",
            title="Participantes por mês",
            color="#f9b853",
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)


with st.container():
    st.subheader(":orange[Comparação de resultados entre BioMARatonas (2024-2025)]")
    # Datos de años anteriores
    df_2024_filtered = get_previous_years(main_metrics_filtered)
    col1_comp, col2_comp, col3_comp = st.columns(3)

    with col1_comp:
        fig1_comp = fig_multi_year_comparison(
            df_list=[
                main_metrics_filtered,
                df_2024_filtered,
            ],
            years=["2025", "2024"],
            field="observações",  # Columna a comparar
            colors=[
                "#2CA02C",
                "#FF9E4A",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig1_comp, config=config_modebar, use_container_width=True)

    with col2_comp:
        fig2_comp = fig_multi_year_comparison(
            df_list=[
                main_metrics_filtered,
                df_2024_filtered,
            ],
            years=["2025", "2024"],
            field="espécies",  # Columna a comparar
            colors=[
                "#2CA02C",
                "#FF9E4A",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig2_comp, config=config_modebar, use_container_width=True)

    with col3_comp:
        fig3_comp = fig_multi_year_comparison(
            df_list=[
                main_metrics_filtered,
                df_2024_filtered,
            ],
            years=["2025", "2024"],
            field="participantes",  # Columna a comparar
            colors=[
                "#2CA02C",
                "#FF9E4A",
            ],  # Naranja, azul, verde, rojo
        )
        st.plotly_chart(fig3_comp, config=config_modebar, use_container_width=True)


with st.container():
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Classificação dos participantes]")
    st.markdown("Número de observações com o grau de investigação.")
    try:
        pd.read_csv(f"{directory}/data/{main_project}_pt_users.csv")
        col0, col1, col2, col3 = st.columns([4, 1, 4, 1])

        # Ranking general
        with col0:

            # Tabla
            if "pt_users0" not in st.session_state:
                st.session_state.pt_users0 = pd.read_csv(
                    f"{directory}/data/{main_project}_pt_users.csv"
                )
                st.session_state.pt_users0 = st.session_state.pt_users0[
                    -st.session_state.pt_users0.participant.isin(exclude_users)
                ].reset_index(drop=True)
                st.session_state.pt_users0.index = range(
                    st.session_state.pt_users0.index.start + 1,
                    st.session_state.pt_users0.index.stop + 1,
                )
                st.session_state.pt_users0["observacions"] = st.session_state.pt_users0[
                    "observacions"
                ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

            pt_users = st.session_state.pt_users0[
                ["participant", "observacions", "espècies"]
            ].rename(
                columns={
                    "participant": "participante",
                    "observacions": "observações",
                    "espècies": "espécies",
                }
            )
            st.dataframe(
                pt_users,
                use_container_width=True,
                height=210,
            )
        with col2:
            # Medallas
            col1b, __ = st.columns([10, 1])
            with col1b:
                if len(st.session_state.pt_users0) > 0:
                    medals = [
                        "first_place_medal",
                        "second_place_medal",
                        "third_place_medal",
                    ]
                    for i in range(1, 4):
                        nombre = st.session_state.pt_users0.loc[i, "participant"]
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
        st.header(":orange[Agradecimentos]")
    st.markdown("Participaram da Biomaratona Norte 2025:")
    try:
        df_total = pd.read_csv(f"{directory}/data/{main_project}_df_obs.csv")
        list_participants = df_total.user_login.unique()
        list_participants.sort()
        linked_list = []
        for p in list_participants:
            linked_list.append(f"[{p}](https://minka-sdg.org/users/{p})")
        agraiments = ", ".join(linked_list)
        st.markdown(f"{agraiments}")
    except FileNotFoundError:
        pass

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organizadores:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.markdown("##### Com o financiamento de projetos europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
