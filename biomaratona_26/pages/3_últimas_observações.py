import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
from markdownlit import mdlit
from utils import get_last_obs
import config

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

# Optimized config - move to session state to avoid recreation
if "config_modebar" not in st.session_state:
    st.session_state.config_modebar = {
        "displayModeBar": True,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "pan2d",
            "lasso2d",
            "autoScale2d",
            "resetScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
            "zoomIn2d",
            "zoomOut2d",
        ],
        "displaylogo": False,
    }

exclude_users = []


base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 424, "name": "BioMARatona 2025"},
]

main_project = 424


# Apply CSS only once per session
if "page3_css_applied" not in st.session_state:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                width: 220px !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: 220px !important;
            }
            /* Optimize image loading */
            img {
                loading: lazy;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.page3_css_applied = True


@st.cache_data(ttl=1800, show_spinner="Processing species data...")
def get_last_species_from_obs(df_obs_path, df_photos_path):
    """Optimized function to get last species with file paths for better caching"""
    # Load data inside cached function for better performance
    df_obs = pd.read_csv(
        df_obs_path,
        usecols=["taxon_rank", "observed_on", "observed_on_time", "taxon_id", "id"],
    )
    df_photos = pd.read_csv(
        df_photos_path, usecols=["id", "photos_medium_url", "attribution"]
    )

    # More efficient chaining with early filtering
    species_obs = df_obs[df_obs["taxon_rank"] == "species"].copy()

    if species_obs.empty:
        return pd.DataFrame()

    # Sort and deduplicate efficiently
    df_result = (
        species_obs.sort_values(by=["observed_on", "observed_on_time"])
        .drop_duplicates(subset=["taxon_id"], keep="first")
        .sort_values(by=["observed_on", "observed_on_time"], ascending=False)
        .reset_index(drop=True)
    )

    # Use unique photos only
    df_unique_photos = df_photos.drop_duplicates(subset=["id"], keep="first")

    # Efficient merge with inner join to reduce data
    df_merged = pd.merge(df_result, df_unique_photos, on="id", how="inner")

    return df_merged


@st.cache_data(ttl=1800)
def prepare_species_display_data(df):
    """Prepare species data for display with caching"""
    if df.empty:
        return pd.DataFrame()

    df_display = df.copy()
    df_display["observed_on"] = pd.to_datetime(df_display["observed_on"]).dt.strftime(
        "%d-%m-%Y"
    )
    df_display["obs_url"] = (
        df_display["id"]
        .astype(str)
        .apply(lambda x: f"https://minka-sdg.org/observations/{x}")
    )
    return df_display


def show_last_species(df, provincia_name):
    """
    Optimized function to show the last species added to the list.
    """
    if df.empty:
        st.info("No species data available")
        return

    try:
        # Use cached data preparation
        df_display = prepare_species_display_data(df)

        if len(df_display) == 0:
            st.info("No species to display")
            return

        col1sp, col2sp, col3sp, col4sp = st.columns(4, gap="small")

        # Display dataframe
        with col1sp:
            display_df = df_display[["taxon_name", "observed_on", "obs_url"]].rename(
                columns={"observed_on": "data"}
            )
            st.dataframe(
                display_df,
                column_config={
                    "obs_url": st.column_config.LinkColumn("link", display_text="Ver")
                },
                use_container_width=True,
                height=300,
                hide_index=True,
            )

        # Display images more efficiently
        columns = [col2sp, col3sp, col4sp, col1sp, col2sp, col3sp, col4sp]

        max_display = min(7, len(df_display))  # Limit to available data

        for i in range(max_display):
            if i >= len(df_display):
                break

            with columns[i]:
                try:
                    row = df_display.iloc[i]
                    photo_url = row["photos_medium_url"]
                    taxon_name = row["taxon_name"]
                    obs_id = row["id"]
                    attribution = row["attribution"]

                    st.markdown(
                        f":link: [MINKA](https://minka-sdg.org/observations/{obs_id})"
                    )
                    st.image(
                        photo_url,
                        caption=f"{taxon_name} | Foto: {attribution}",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"Erro ao exibir espécie {i}: {e}")
                    continue

    except Exception as e:
        st.error(f"Erro ao mostrar espécies: {e}")


# Carrusel de últimas observaciones,
# con grado research, excluidos xasalva y mediambient_ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimas observações publicadas]")

    # Highly optimized last observations processing
    @st.cache_data(ttl=900, show_spinner="Loading recent observations...")
    def process_last_observations():
        try:
            last_total = get_last_obs(main_project)

            if last_total.empty:
                return pd.DataFrame()

            # More efficient groupby approach
            user_limited = (
                last_total.groupby("user_login", group_keys=False)
                .apply(lambda x: x.head(3), include_groups=False)
                .reset_index(drop=True)
            )

            # Get top 15 sorted by id
            results = (
                user_limited.sort_values(by="id", ascending=False)
                .head(15)
                .reset_index(drop=True)
            )

            return results

        except Exception as e:
            st.error(f"Erro ao processar observações: {e}")
            return pd.DataFrame()

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    results = process_last_observations()

    # Optimized image display with better error handling and lazy loading
    if not results.empty:
        # Create columns once
        columns = st.columns(5)

        # Process in batches for better performance
        max_images = min(15, len(results))

        # Prepare image data efficiently
        image_data = [
            {
                "url": row["photos_medium_url"],
                "obs_id": row["id"],
                "taxon": row.get("taxon_name", "Unknown"),
            }
            for _, row in results.head(max_images).iterrows()
            if pd.notna(row.get("photos_medium_url"))
        ]

        # Display images efficiently
        for i, img_data in enumerate(image_data):
            col_idx = i % 5
            with columns[col_idx]:
                try:
                    # More efficient markdown link above image
                    st.markdown(
                        f"[:link: Ver observação](https://minka-sdg.org/observations/{img_data['obs_id']})"
                    )
                    # Lazy loading with better caching
                    st.image(
                        img_data["url"],
                        use_container_width=True,
                        caption=img_data["taxon"][:30]
                        + ("..." if len(img_data["taxon"]) > 30 else ""),
                    )
                except Exception as e:
                    st.info(f"Image {i+1} unavailable")
                    continue
    else:
        st.info("No recent observations to display")


st.divider()


@st.cache_data(ttl=1800, show_spinner="Loading recent species...")
def load_and_filter_species():
    """Optimized species loading with better error handling"""
    try:
        species_file = f"{directory}/data/place_biomaratona_species.csv"

        # Load only required columns for better performance
        required_cols = ["id", "first_date", "name", "photo_url", "author", "obs_id"]

        try:
            df_species = pd.read_csv(species_file, usecols=required_cols)
        except ValueError:
            # Fallback to loading all columns if specific columns don't exist
            df_species = pd.read_csv(species_file)

        if df_species.empty:
            return pd.DataFrame()

        # Efficient date filtering
        last_month = datetime.now() - timedelta(days=30)
        df_species["first_date"] = pd.to_datetime(
            df_species["first_date"], errors="coerce"
        )

        # Filter and sort in one operation
        df_species_filtered = (
            df_species[df_species.first_date >= last_month]
            .sort_values(by="first_date", ascending=False)
            .reset_index(drop=True)
        )

        if df_species_filtered.empty:
            return pd.DataFrame()

        # Efficient column renaming
        column_mapping = {
            "id": "taxon_id",
            "first_date": "observed_on",
            "name": "taxon_name",
            "photo_url": "photos_medium_url",
            "author": "attribution",
            "obs_id": "id",
        }

        df_species_filtered = df_species_filtered.rename(columns=column_mapping)

        return df_species_filtered

    except FileNotFoundError:
        st.warning("Species data file not found")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados de espécies: {e}")
        return pd.DataFrame()


# New species section with better organization
with st.container():
    st.header("Novas espécies na área da BioMARatona nos últimos 30 dias")

    # Load data with progress indicator
    with st.spinner("Loading recent species data..."):
        df_species_filtered = load_and_filter_species()

    if not df_species_filtered.empty:
        st.success(
            f"Encontradas {len(df_species_filtered)} espécies novas nos últimos 30 dias"
        )
        show_last_species(df_species_filtered, "BioMARatona 2025")
    else:
        st.info("Nenhuma espécie nova encontrada nos últimos 30 dias")

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
