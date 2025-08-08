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

# Create session for image loading
session = requests.Session()

# Optimized data loading with caching - moved inside container to avoid ScriptRunContext warning

# Ranking by province (incluye todos los usuarios y todos los grados)
with st.container():
    # Optimized data loading functions
    @st.cache_data(ttl=600, show_spinner="Carregant mètriques per província...")
    def load_province_metrics():
        """Load and cache province metrics"""
        return get_metrics_province()

    @st.cache_data(ttl=600, show_spinner="Carregant rànquings de participants...")
    def load_province_rankings(directory_path, exclude_users_list):
        """Load and process all province rankings with caching"""
        provinces = {"Girona": 418, "Tarragona": 419, "Barcelona": 420}

        rankings = {}
        for prov_name, prov_id in provinces.items():
            try:
                df = pd.read_csv(f"{directory_path}/data/{prov_id}_pt_users.csv")
                df = df[~df.participant.isin(exclude_users_list)].reset_index(drop=True)
                df.index = range(df.index.start + 1, df.index.stop + 1)
                df["observacions"] = df["observacions"].apply(
                    lambda x: "{:,.0f}".format(x).replace(",", " ")
                )
                rankings[prov_name] = df
            except FileNotFoundError:
                rankings[prov_name] = pd.DataFrame()

        return rankings

    # Load data with caching
    main_metrics_prov = load_province_metrics()
    province_rankings = load_province_rankings(directory, exclude_users)

    # Cabecera
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Quina província ha estat la més activa?]")

    # Generate cached province charts
    @st.cache_data(ttl=900, show_spinner="Generant gràfics de províncies...")
    def generate_province_charts(metrics_df):
        """Generate all province charts with caching"""
        fig1 = fig_provinces(metrics_df, "observacions", "Nombre d'observacions")
        fig2 = fig_provinces(metrics_df, "espècies", "Espècies diferents")
        fig3 = fig_provinces(metrics_df, "participants", "Participants")
        return fig1, fig2, fig3

    fig1, fig2, fig3 = generate_province_charts(main_metrics_prov)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)
    with col3:
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    # Optimized trophy winners calculation
    @st.cache_data(ttl=900)
    def get_trophy_winners(metrics_df):
        """Calculate trophy winners with caching"""
        prov_sp = metrics_df.sort_values(by="espècies", ascending=False)[
            "provincia"
        ].iloc[0]
        prov_obs = metrics_df.sort_values(by="observacions", ascending=False)[
            "provincia"
        ].iloc[0]
        prov_part = metrics_df.sort_values(by="participants", ascending=False)[
            "provincia"
        ].iloc[0]
        return prov_obs, prov_sp, prov_part

    prov_obs, prov_sp, prov_part = get_trophy_winners(main_metrics_prov)
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

    # Ranking Girona
    with col1:
        provincia1 = "Girona"
        st.subheader(provincia1)

        # Use cached data
        girona_data = province_rankings.get("Girona", pd.DataFrame())

        if not girona_data.empty:
            st.dataframe(
                girona_data[["participant", "observacions", "espècies"]],
                use_container_width=True,
                height=210,
            )

            # Winner name and photo
            __, col1b, __ = st.columns([1, 10, 1])
            with col1b:
                if len(girona_data) > 0 and 1 in girona_data.index:
                    nombre = girona_data.loc[1, "participant"]
                    st.subheader(
                        f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                    )

                    # Load winner photo
                    try:
                        url = f"{base_url}/users/{nombre}.json"
                        foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                        response = session.get(foto)
                        st.image(response.content, caption=nombre, width=300)
                    except:
                        pass
        else:
            st.info("No hi ha dades disponibles per Girona")

        # Ranking Tarragona
        with col2:
            provincia2 = "Tarragona"
            st.subheader(provincia2)

            # Use cached data
            tarragona_data = province_rankings.get("Tarragona", pd.DataFrame())

            if not tarragona_data.empty:
                st.dataframe(
                    tarragona_data[["participant", "observacions", "espècies"]],
                    use_container_width=True,
                    height=210,
                )

                # Winner name and photo
                __, col1b, __ = st.columns([1, 10, 1])
                with col1b:
                    if len(tarragona_data) > 0 and 1 in tarragona_data.index:
                        nombre = tarragona_data.loc[1, "participant"]
                        st.subheader(
                            f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )

                        # Load winner photo
                        try:
                            url = f"{base_url}/users/{nombre}.json"
                            foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                            response = session.get(foto)
                            st.image(response.content, caption=nombre, width=300)
                        except:
                            pass
            else:
                st.info("No hi ha dades disponibles per Tarragona")

        # Ranking Barcelona
        with col3:
            provincia3 = "Barcelona"
            st.subheader(provincia3)

            # Use cached data
            barcelona_data = province_rankings.get("Barcelona", pd.DataFrame())

            if not barcelona_data.empty:
                st.dataframe(
                    barcelona_data[["participant", "observacions", "espècies"]],
                    use_container_width=True,
                    height=210,
                )

                # Winner name and photo
                __, col1b, __ = st.columns([1, 10, 1])
                with col1b:
                    if len(barcelona_data) > 0 and 1 in barcelona_data.index:
                        nombre = barcelona_data.loc[1, "participant"]
                        st.subheader(
                            f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                        )

                        # Load winner photo
                        try:
                            url = f"{base_url}/users/{nombre}.json"
                            foto = f"https://minka-sdg.org/{session.get(url).json()['medium_user_icon_url']}"
                            response = session.get(foto)
                            st.image(response.content, caption=nombre, width=300)
                        except:
                            pass
            else:
                st.info("No hi ha dades disponibles per Barcelona")

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
