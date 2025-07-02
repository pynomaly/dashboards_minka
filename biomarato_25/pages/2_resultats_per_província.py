# Run as streamlit run app_biomarato.py --server.port 9003

import os

import pandas as pd
import requests
import streamlit as st
from utils import fig_provinces, get_metrics_province

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

colors = ["#5fbfbb", "#1e9ca3", "#0c6a83", "#de6719", "#fab954"]

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

session = requests.Session()

# Ranking by province (incluye todos los usuarios y todos los grados)
with st.container():
    # Cabecera
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Quina província ha estat la més activa?]")
    if "main_metrics_prov" not in st.session_state:
        st.session_state.main_metrics_prov = get_metrics_province()

    # Gráfico de barras
    fig1 = fig_provinces(
        st.session_state.main_metrics_prov, "observacions", "Nombre d’observacions"
    )
    fig2 = fig_provinces(
        st.session_state.main_metrics_prov, "espècies", "Espècies diferents"
    )
    fig3 = fig_provinces(
        st.session_state.main_metrics_prov, "participants", "Participants"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)
    with col3:
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    # Trofeos provincia en cabeza
    prov_sp = (
        st.session_state.main_metrics_prov.sort_values(by="espècies", ascending=False)[
            "provincia"
        ]
        .head(1)
        .values[0]
    )
    prov_obs = (
        st.session_state.main_metrics_prov.sort_values(
            by="observacions", ascending=False
        )["provincia"]
        .head(1)
        .values[0]
    )
    prov_part = (
        st.session_state.main_metrics_prov.sort_values(
            by="participants", ascending=False
        )["provincia"]
        .head(1)
        .values[0]
    )
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(
        [2, 1, 4, 2, 1, 4, 2, 1, 4], gap="small"
    )
    with col2:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col3:
        st.subheader(prov_obs)
    with col5:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col6:
        st.subheader(prov_sp)
    with col8:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col9:
        st.subheader(prov_part)

st.divider()

# Ranking users por provincia, excluidos los usuarios voluntarios
with st.container():
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Rànquing de participants]")
    st.markdown("Nombre d'observacions amb grau de recerca.")

    col1, col2, col3 = st.columns(3)
    try:
        # Ranking Girona
        with col1:
            try:
                provincia1 = "Girona"
                st.subheader(provincia1)

                # Dataframe
                if "pt_users1" not in st.session_state:
                    st.session_state.pt_users1 = pd.read_csv(
                        f"{directory}/data/{project_id_gir}_pt_users.csv"
                    )
                    st.session_state.pt_users1 = st.session_state.pt_users1[
                        -st.session_state.pt_users1.participant.isin(exclude_users)
                    ].reset_index(drop=True)

                    st.session_state.pt_users1.index = range(
                        st.session_state.pt_users1.index.start + 1,
                        st.session_state.pt_users1.index.stop + 1,
                    )
                    st.session_state.pt_users1["observacions"] = (
                        st.session_state.pt_users1["observacions"].apply(
                            lambda x: "{:,.0f}".format(x).replace(",", " ")
                        )
                    )

                st.dataframe(
                    st.session_state.pt_users1[
                        ["participant", "observacions", "espècies"]
                    ],
                    use_container_width=True,
                    height=210,
                )

                # Nombre
                __, col1b, __ = st.columns([1, 10, 1])
                with col1b:
                    if len(st.session_state.pt_users1) > 0:
                        nombre = st.session_state.pt_users1.loc[1, "participant"]
                        st.subheader(
                            f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )
                        # st.markdown(f":first_place_medal: **[{nombre}]('https://minka-sdg.org/users/{nombre}')**")

                        # Foto
                        try:
                            url = f"{base_url}/users/{nombre}.json"
                            foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                            response = session.get(foto)
                            st.image(response.content, caption=nombre, width=300)
                        except:
                            pass
            except FileNotFoundError:
                pass

        # Ranking Tarragona
        with col2:
            try:
                provincia2 = "Tarragona"
                st.subheader(provincia2)
                # Dataframe
                if "pt_users2" not in st.session_state:
                    st.session_state.pt_users2 = pd.read_csv(
                        f"{directory}/data/{project_id_tarr}_pt_users.csv"
                    )
                    st.session_state.pt_users2 = st.session_state.pt_users2[
                        -st.session_state.pt_users2.participant.isin(exclude_users)
                    ].reset_index(drop=True)
                    st.session_state.pt_users2.index = range(
                        st.session_state.pt_users2.index.start + 1,
                        st.session_state.pt_users2.index.stop + 1,
                    )
                    st.session_state.pt_users2["observacions"] = (
                        st.session_state.pt_users2["observacions"].apply(
                            lambda x: "{:,.0f}".format(x).replace(",", " ")
                        )
                    )

                st.dataframe(
                    st.session_state.pt_users2[
                        ["participant", "observacions", "espècies"]
                    ],
                    use_container_width=True,
                    height=210,
                )

                # Nombre
                __, col1b, __ = st.columns([1, 10, 1])
                with col1b:
                    if len(st.session_state.pt_users2) > 0:
                        nombre = st.session_state.pt_users2.loc[1, "participant"]
                        st.subheader(
                            f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )

                        # Foto
                        try:
                            url = f"{base_url}/users/{nombre}.json"
                            foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                            response = session.get(foto)
                            st.image(response.content, caption=nombre, width=300)
                        except:
                            pass
            except FileNotFoundError:
                pass

        # Ranking Barcelona
        with col3:
            try:
                provincia3 = "Barcelona"
                st.subheader(provincia3)

                # Dataframe
                if "pt_users3" not in st.session_state:
                    st.session_state.pt_users3 = pd.read_csv(
                        f"{directory}/data/{project_id_bcn}_pt_users.csv"
                    )
                    st.session_state.pt_users3 = st.session_state.pt_users3[
                        -st.session_state.pt_users3.participant.isin(exclude_users)
                    ].reset_index(drop=True)
                    st.session_state.pt_users3.index = range(
                        st.session_state.pt_users3.index.start + 1,
                        st.session_state.pt_users3.index.stop + 1,
                    )
                    st.session_state.pt_users3["observacions"] = (
                        st.session_state.pt_users3["observacions"].apply(
                            lambda x: "{:,.0f}".format(x).replace(",", " ")
                        )
                    )

                st.dataframe(
                    st.session_state.pt_users3[
                        ["participant", "observacions", "espècies"]
                    ],
                    use_container_width=True,
                    height=210,
                )

                # Nombre
                __, col1b, __ = st.columns([1, 10, 1])
                with col1b:
                    if len(st.session_state.pt_users3) > 0:
                        nombre = st.session_state.pt_users3.loc[1, "participant"]
                        st.subheader(
                            f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )

                        # Foto
                        try:
                            url = f"{base_url}/users/{nombre}.json"
                            foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                            response = session.get(foto)
                            st.image(response.content, caption=nombre, width=300)
                        except:
                            pass
            except FileNotFoundError:
                pass

    except FileNotFoundError:
        st.markdown("Cap participant")

st.divider()

# Logos
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
