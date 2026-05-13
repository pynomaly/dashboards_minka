import os

import config
import streamlit as st

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

# Now import the rest
from datetime import datetime, timedelta

import pandas as pd
import requests
from i18n import create_footer, init_i18n, t
from markdownlit import mdlit
from utils import get_last_obs, reindex

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
init_i18n(current_page="observations")


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


def show_last_species(df, provincia_name):
    """
    Display last species - not cached (renders UI with translations)
    """
    if df is None or df.empty:
        st.info(t("ui.no_species_available").replace("{province}", provincia_name))
        return

    try:
        df = df.reset_index(drop=True).copy()

        # Convert dates efficiently
        df["observed_on"] = pd.to_datetime(df["observed_on"], errors="coerce")
        df["observed_on"] = df["observed_on"].dt.strftime("%d-%m-%Y")
        df["obs_url"] = df["id"].apply(
            lambda x: f"{config.HOME_PATH}/observations/{int(x)}"
        )

        # Ensure we have enough data
        max_items = min(8, len(df))
        df_display = df.head(max_items)

        col1sp, col2sp, col3sp, col4sp = st.columns(4, gap="small")

        # Table in first column
        with col1sp:
            st.dataframe(
                df_display[["taxon_name", "observed_on", "obs_url"]].rename(
                    columns={
                        "taxon_name": t("table.species_name"),
                        "observed_on": t("table.observation_date"),
                    }
                ),
                column_config={
                    "obs_url": st.column_config.LinkColumn(
                        t("table.link"), display_text=t("ui.view")
                    )
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
                        f":link: [MINKA]({config.HOME_PATH}/observations/{int(row['id'])})"
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
                        f":link: [MINKA]({config.HOME_PATH}/observations/{row['id']})"
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
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":orange[{t('header.observations_title')}]")

    # Optimized image viewer with caching
    @st.cache_data(ttl=600, show_spinner="📷 Carregant darreres observacions...")
    def load_recent_observations(project_id):
        """Load and process recent observations with caching"""
        return get_last_obs(project_id)

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    # Excluye a Xavi y a mediambient_ajelprat en la función
    last_total = load_recent_observations(config.MAIN_PROJ)

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

    if results.empty:
        st.info(t("ui.no_observations_yet"))
    else:
        # Optimized gallery using direct URLs instead of fetching content
        c1, c2, c3, c4, c5 = st.columns(5)
        cols = [c1, c2, c3, c4, c5]
        col_idx = 0

        for index, row in results.iterrows():
            image_url = row["photos_medium_url"]
            id_obs = row["id"]
            taxon_name = row.taxon_name
            attribution = row.get("attribution", "")

            # Skip if no image URL
            if not image_url:
                continue

            with cols[col_idx]:
                st.markdown(
                    f":link: [MINKA]({config.HOME_PATH}/observations/{int(id_obs)})"
                )
                st.image(
                    image_url,
                    caption=f"{taxon_name} | Foto: {attribution}",
                    use_container_width=True,
                )

            col_idx = (col_idx + 1) % 5


st.divider()

# Últimas especies incorporadas
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":orange[{t('header.last_species_title')}]")

    # usuarios excluidos
    excluded = []
    # excluded = ["xasalva", "mediambient_ajelprat"]

    # Optimized province data loading without ThreadPoolExecutor to avoid ScriptRunContext warning
    @st.cache_data(ttl=1800, show_spinner="Carregant dades de províncies...")
    def load_all_province_data(directory_path, excluded_users):
        """Load all province species data with caching and sequential processing"""
        provinces = {
            k: v for k, v in config.PROJECTS_BY_NAME.items() if v != config.MAIN_PROJ
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
@st.cache_data(ttl=10, show_spinner="🌱 Carregant noves espècies...")
def load_new_species_data(directory_path):
    """Load and process new species data with caching"""
    try:
        df_species = pd.read_csv(f"{directory_path}/data/place_species.csv")

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
    st.header(t("header.new_species_title"))
    new_species_data = load_new_species_data(directory)
    show_last_species(new_species_data, "BioMARató")

# Footer with logos
create_footer()
