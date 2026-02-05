import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
from markdownlit import mdlit
from utils import get_last_obs, reindex

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


@st.cache_data(ttl=1800, show_spinner="🔍 Processant espècies...")
def get_last_species_from_obs(df_obs, df_photos):
    """Optimized species processing with caching"""
    if df_obs.empty or df_photos.empty:
        return pd.DataFrame()

    try:
        # Filter species observations efficiently
        df_species = df_obs[df_obs["taxon_rank"] == "species"].copy()

        if df_species.empty:
            return pd.DataFrame()

        # Sort and get unique species (keep latest observation per species)
        df_species = (
            df_species.sort_values(
                by=["observed_on", "observed_on_time"], ascending=False
            )
            .drop_duplicates(subset=["taxon_id"], keep="first")
            .reset_index(drop=True)
        )

        # Merge with photos efficiently
        df_unique_photos = df_photos.drop_duplicates(subset=["id"], keep="first")
        df_result = pd.merge(
            df_species,
            df_unique_photos[["id", "photos_medium_url", "attribution"]],
            on="id",
            how="left",
        )

        return df_result

    except Exception as e:
        st.error(f"Error processing species data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=900)
def show_last_species(df, provincia_name):
    """
    Optimized display of last species with better error handling
    """
    if df is None or df.empty:
        st.info(f"No hi ha espècies disponibles per {provincia_name}")
        return

    try:
        df = df.reset_index(drop=True).copy()

        # Convert dates efficiently
        df["observed_on"] = pd.to_datetime(df["observed_on"], errors="coerce")
        df["observed_on"] = df["observed_on"].dt.strftime("%d-%m-%Y")
        df["obs_url"] = df["id"].apply(
            lambda x: f"https://minka-sdg.org/observations/{x}"
        )

        # Ensure we have enough data
        max_items = min(8, len(df))
        df_display = df.head(max_items)

        col1sp, col2sp, col3sp, col4sp = st.columns(4, gap="small")

        # Table in first column
        with col1sp:
            st.dataframe(
                df_display[["taxon_name", "observed_on", "obs_url"]].rename(
                    columns={"observed_on": "data"}
                ),
                column_config={
                    "obs_url": st.column_config.LinkColumn("link", display_text="Veure")
                },
                use_container_width=True,
                height=300,
                hide_index=True,
            )

        # Images in other columns - first row
        cols = [col2sp, col3sp, col4sp]
        for i, col in enumerate(cols, 0):
            if i < len(df_display):
                with col:
                    row = df_display.iloc[i]
                    photo_url = row.get("photos_medium_url")
                    taxon_name = row.get("taxon_name", "Unknown")
                    attribution = row.get("attribution", "Unknown")

                    st.markdown(
                        f":link: [MINKA](https://minka-sdg.org/observations/{int(row['id'])})"
                    )

                    if photo_url and pd.notna(photo_url):
                        st.image(
                            photo_url,
                            caption=f"{taxon_name} | Foto: {attribution}",
                            use_container_width=True,
                        )
                    else:
                        st.info(f"Sense foto\n{taxon_name}")

        # Images - second row
        for i, col in enumerate([col1sp, col2sp, col3sp, col4sp], 4):
            if i < len(df_display):
                with col:
                    row = df_display.iloc[i]
                    photo_url = row.get("photos_medium_url")
                    taxon_name = row.get("taxon_name", "Unknown")
                    attribution = row.get("attribution", "Unknown")

                    st.markdown(
                        f":link: [MINKA](https://minka-sdg.org/observations/{row['id']})"
                    )

                    if photo_url and pd.notna(photo_url):
                        st.image(
                            photo_url,
                            caption=f"{taxon_name} | Foto: {attribution}",
                            use_container_width=True,
                        )
                    else:
                        st.info(f"Sense foto\n{taxon_name}")

    except Exception as e:
        st.error(f"Error mostrant espècies de {provincia_name}: {e}")


# Carrusel de últimas observaciones,
# con grado research, excluidos xasalva y mediambient_ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes observacions publicades]")

    # Optimized image viewer with caching
    @st.cache_data(ttl=600, show_spinner="📷 Carregant darreres observacions...")
    def load_recent_observations(project_id):
        """Load and process recent observations with caching"""
        return get_last_obs(project_id)

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    # Excluye a Xavi y a mediambient_ajelprat en la función
    last_total = load_recent_observations(main_project)

    # Optimized results processing with vectorized operations
    @st.cache_data(ttl=300)
    def process_gallery_results(df_observations, max_per_user=3, total_limit=15):
        """Process gallery results with optimized operations"""
        if df_observations.empty:
            return pd.DataFrame()

        # Group by user and take top 3 observations per user
        results = df_observations.groupby("user_login").head(max_per_user)

        # Sort by id descending and limit total results
        results = results.sort_values(by="id", ascending=False).head(total_limit)

        return results.reset_index(drop=True)

    # convertimos el df para que sólo aparezcan 3 obs de cada usuario como máximo
    results = process_gallery_results(last_total, max_per_user=3, total_limit=15)

    # Optimized gallery using direct URLs instead of fetching content
    c1, c2, c3, c4, c5 = st.columns(5)
    col = 0

    for index, row in results.iterrows():
        image_url = row["photos_medium_url"]
        id_obs = row["id"]
        taxon_name = row.taxon_name

        # Skip if no image URL
        if not image_url:
            continue

        if col == 0:
            with c1:
                st.image(image_url, caption=taxon_name)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 1:
            with c2:
                st.image(image_url, caption=taxon_name)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 2:
            with c3:
                st.image(image_url, caption=taxon_name)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 3:
            with c4:
                st.image(image_url, caption=taxon_name)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 4:
            with c5:
                st.image(image_url, caption=taxon_name)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col = 0


st.divider()

# Últimas especies incorporadas
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes espècies registrades per província]")

    # usuarios excluidos
    excluded = []
    # excluded = ["xasalva", "mediambient_ajelprat"]

    # Optimized province data loading without ThreadPoolExecutor to avoid ScriptRunContext warning
    @st.cache_data(ttl=1800, show_spinner="Carregant dades de províncies...")
    def load_all_province_data(directory_path, excluded_users):
        """Load all province species data with caching and sequential processing"""
        provinces = {
            "Girona": project_id_gir,
            "Tarragona": project_id_tarr,
            "Barcelona": project_id_bcn,
        }

        results = {}

        for prov_name, prov_id in provinces.items():
            try:
                df_obs = pd.read_csv(f"{directory_path}/data/{prov_id}_df_obs.csv")
                df_photos = pd.read_csv(
                    f"{directory_path}/data/{prov_id}_df_photos.csv"
                )
                sp_data = get_last_species_from_obs(df_obs, df_photos)
                sp_data = sp_data[-sp_data.user_login.isin(excluded_users)]
                results[prov_name] = (
                    reindex(sp_data)
                    if sp_data is not None and not sp_data.empty
                    else None
                )
            except (FileNotFoundError, Exception):
                results[prov_name] = None

        return results

    # Load all province data with caching
    province_data = load_all_province_data(directory, excluded)
    sp_girona = province_data.get("Girona")
    sp_tarragona = province_data.get("Tarragona")
    sp_barcelona = province_data.get("Barcelona")

    # Display provinces with error handling
    provinces_display = [
        ("Girona", sp_girona),
        ("Tarragona", sp_tarragona),
        ("Barcelona", sp_barcelona),
    ]

    for prov_name, prov_data in provinces_display:
        st.header(prov_name)
        show_last_species(prov_data, prov_name)
        st.divider()


# Optimized new species section
@st.cache_data(ttl=1800, show_spinner="🌱 Carregant noves espècies...")
def load_new_species_data(directory_path):
    """Load and process new species data with caching"""
    try:
        df_species = pd.read_csv(f"{directory_path}/data/place_biomarato_species.csv")

        # Filter last 30 days
        last_month = datetime.now() - timedelta(days=30)
        df_species["first_date"] = pd.to_datetime(df_species["first_date"])
        df_filtered = df_species[df_species.first_date >= last_month]

        if df_filtered.empty:
            return pd.DataFrame()

        # Sort and rename columns efficiently
        df_filtered = df_filtered.sort_values(by="first_date", ascending=False)

        column_mapping = {
            "id": "taxon_id",
            "first_date": "observed_on",
            "name": "taxon_name",
            "photo_url": "photos_medium_url",
            "author": "attribution",
            "obs_id": "id",
        }

        return df_filtered.rename(columns=column_mapping)

    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error carregant noves espècies: {e}")
        return pd.DataFrame()


with st.container():
    st.header("Noves espècies a l'àrea Biomarató en els darrers 30 dies")
    new_species_data = load_new_species_data(directory)
    show_last_species(new_species_data, "BioMARató")

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
