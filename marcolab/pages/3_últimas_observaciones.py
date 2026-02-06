import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from utils import get_last_obs, reindex

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

exclude_users = []

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"

colors = ["#012644", "#496cc0", "#43c0bb", "#de6719", "#fab954"]

PROJECT_LOGO = "PHAROS_White_Background.png"

MAIN_PROJECT = 547
MAIN_PROJECT_NAME = "MarCoLab"

project_ids = {
    "MarCoLab Lanzarote": 581,
    "MarCoLab Gran Canaria": 580,
}


parser_lang = {
    "date": "fecha",
    "observations": "observaciones",
    "species": "especies",
    "participants": "participantes",
}


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


@st.cache_data(ttl=1800, show_spinner="🔍 Procesando especies...")
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
        st.error(f"Error procesando datos de especies: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=900)
def show_last_species(df, p_name):
    """
    Optimized display of last species with better error handling
    """
    if df is None:
        st.info(f"No hay especies disponibles para {p_name}")
        return

    try:
        df = df.reset_index(drop=True).copy()

        # discrepancia en el nombre de la columna entre archivos
        if "id" not in df.columns:
            id_obs = "obs_id"
        else:
            id_obs = "id"

        # Convert dates efficiently
        df["observed_on"] = pd.to_datetime(df["observed_on"], errors="coerce")
        df["observed_on"] = df["observed_on"].dt.strftime("%d-%m-%Y")

        df["obs_url"] = df[id_obs].apply(
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
                    "obs_url": st.column_config.LinkColumn("link", display_text="MINKA")
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
                        f":link: [MINKA](https://minka-sdg.org/observations/{int(row[id_obs])})"
                    )

                    if photo_url and pd.notna(photo_url):
                        st.image(
                            photo_url,
                            caption=f"{taxon_name} | Foto: {attribution}",
                            use_container_width=True,
                        )
                    else:
                        st.info(f"Sin foto\n{taxon_name}")

        # Images - second row
        for i, col in enumerate([col1sp, col2sp, col3sp, col4sp], 4):
            if i < len(df_display):
                with col:
                    row = df_display.iloc[i]
                    photo_url = row.get("photos_medium_url")
                    taxon_name = row.get("taxon_name", "Unknown")
                    attribution = row.get("attribution", "Unknown")

                    st.markdown(
                        f":link: [MINKA](https://minka-sdg.org/observations/{row[id_obs]})"
                    )

                    if photo_url and pd.notna(photo_url):
                        st.image(
                            photo_url,
                            caption=f"{taxon_name} | Foto: {attribution}",
                            use_container_width=True,
                        )
                    else:
                        st.info(f"Sin foto\n{taxon_name}")

    except Exception as e:
        st.error(f"Error mostrando especies de {p_name}: {e}")


# Optimized image viewer with caching
@st.cache_data(ttl=600, show_spinner="📷 Cargando últimas observaciones...")
def load_recent_observations(project_id):
    """Load and process recent observations with caching"""
    return get_last_obs(project_id)


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


@st.cache_data(ttl=1800, show_spinner="Cargando datos por isla...")
def load_all_province_data(proj_id):
    """Load all province species data with caching and sequential processing"""
    try:
        df_obs = pd.read_csv(f"{DIRECTORY}/data/{proj_id}_df_obs.csv")
        df_photos = pd.read_csv(f"{DIRECTORY}/data/{proj_id}_df_photos.csv")
        sp_data = get_last_species_from_obs(df_obs, df_photos)
        sp_data = sp_data[-sp_data.user_login.isin(exclude_users)]
        sp_data = (
            reindex(sp_data) if sp_data is not None and not sp_data.empty else None
        )
    except (FileNotFoundError, Exception):
        sp_data = None

    return sp_data


# Optimized new species section
@st.cache_data(ttl=1800, show_spinner="🌱 Cargando nuevas especies...")
def load_new_species_data():
    """Load and process new species data with caching"""
    try:
        df_species = pd.read_csv(f"{DIRECTORY}/data/{MAIN_PROJECT}_species.csv")

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
        }

        return df_filtered.rename(columns=column_mapping)

    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando nuevas especies: {e}")
        return pd.DataFrame()


# Carrusel de últimas observaciones,
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{DIRECTORY}/images/{PROJECT_LOGO}")
    with col2:
        st.header(":orange[Últimas observaciones publicadas]")

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    last_total = load_recent_observations(MAIN_PROJECT)

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
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{int(id_obs)})"
                )
                st.image(image_url, caption=taxon_name)
            col += 1
        elif col == 1:
            with c2:
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{int(id_obs)})"
                )
                st.image(image_url, caption=taxon_name)
            col += 1
        elif col == 2:
            with c3:
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{int(id_obs)})"
                )
                st.image(image_url, caption=taxon_name)
            col += 1
        elif col == 3:
            with c4:
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{int(id_obs)})"
                )
                st.image(image_url, caption=taxon_name)
            col += 1
        elif col == 4:
            with c5:
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{int(id_obs)})"
                )
                st.image(image_url, caption=taxon_name)
            col = 0


st.divider()

# Últimas especies incorporadas
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{DIRECTORY}/images/{PROJECT_LOGO}")
    with col2:
        st.header(":orange[Últimas especies registradas por proyecto]")

    # usuarios excluidos
    excluded = []

    # Load all province data with caching
    for proj_name, proj_id in project_ids.items():
        st.header(proj_name)
        prov_data = load_all_province_data(proj_id)
        show_last_species(prov_data, proj_name)
        st.divider()


with st.container():
    st.header(":orange[Nuevas especies observadas en el área MarCoLab]")
    new_species_data = load_new_species_data()
    show_last_species(new_species_data, MAIN_PROJECT_NAME)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("### Organizadores:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{DIRECTORY}/images/footer_recortado_1.png")

    with col_2:
        st.markdown("### Con la financiación de los proyectos europeos:")
        st.image(f"{DIRECTORY}/images/footer_recortado_2.png")
