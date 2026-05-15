import datetime
import os
import config
import numpy as np
import pandas as pd
import requests
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

# Performance constants
MAX_SPECIES_DISPLAY = 5  # Limit species images for better performance
MAX_OBS_DISPLAY = 50  # Limit observations shown
CACHE_TTL = 3600  # 1 hour cache
PHOTO_CACHE_TTL = 7200  # 2 hours for photos (more stable)

# Optimize constants
BASE_URL = "https://minka-sdg.org"
API_PATH = "https://api.minka-sdg.org/v1"


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
    page_title=f"Dashboard BioMARatona {config.YEAR}",
)

# Apply CSS only once per session for better performance
if "especies_css_applied" not in st.session_state:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                width: 220px !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: 220px !important;
            }
            /* Optimize tab performance */
            .stTabs [role="tablist"] {
                contain: layout;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.especies_css_applied = True

# Optimize config - move to session state to avoid recreation
if "especies_config_modebar" not in st.session_state:
    st.session_state.especies_config_modebar = {
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

# Optimize constants and data structures
COLORS = ("#5fbfbb", "#1e9ca3", "#0c6a83", "#de6719", "#fab954")  # Tuple is faster

PROJECTS = {
    config.MAIN_PROJ: config.PROJ_NAME,
    424: "BioMARatona 2025",
    452: "BioMARatona 2024",
}

MAIN_PROJECT = config.MAIN_PROJ
PROJECT_2024 = 452
PROJECT_2025 = 424

# Use tuple for immutable data
GRUPOS_ESPECIES = ("exoticas", "protegidas", "amenazadas")
SPECIES_NAMES = ("exóticas", "protegidas", "ameaçadas")


@st.cache_data(ttl=CACHE_TTL, max_entries=10, show_spinner=False)
def load_csv_optimized(file_path, dtype_dict=None):
    """Optimized CSV loading with data type specifications"""
    try:
        if dtype_dict:
            return pd.read_csv(file_path, dtype=dtype_dict, engine="c")
        return pd.read_csv(file_path, engine="c")
    except Exception as e:
        st.error(f"Erro ao carregar {file_path}: {e}")
        return pd.DataFrame()


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=CACHE_TTL, max_entries=20)
def get_obs_by_species_group_optimized(proj_id, grupo):
    """Ultra-optimized observations filtering with minimal data loading"""
    try:
        # Load species data with safer handling
        species_file = f"{directory}/data/species/{grupo}.csv"
        df_grupo = load_csv_optimized(species_file)

        # Clean and convert data types safely
        if not df_grupo.empty and "taxon_id" in df_grupo.columns:
            df_grupo = df_grupo.dropna(subset=["taxon_id"])
            df_grupo["taxon_id"] = df_grupo["taxon_id"].astype("int32")

        if df_grupo.empty:
            return pd.DataFrame()

        species_ids_set = set(df_grupo.taxon_id.tolist())

        # Load observations with safer data types (handle NA values properly)
        obs_file = f"{directory}/data/{proj_id}_df_obs.csv"
        required_cols = ["taxon_id", "id", "observed_on", "user_login", "taxon_name"]

        df_obs = pd.read_csv(obs_file, usecols=required_cols, engine="c")

        # Clean data before type conversion
        df_obs = df_obs.dropna(subset=["taxon_id", "id"])

        # Convert to optimized types after cleaning
        df_obs["taxon_id"] = df_obs["taxon_id"].astype("int32")
        df_obs["id"] = df_obs["id"].astype("int32")
        df_obs["observed_on"] = df_obs["observed_on"].astype("string")
        df_obs["user_login"] = df_obs["user_login"].astype("string")
        df_obs["taxon_name"] = df_obs["taxon_name"].astype("string")

        # Efficient filtering and sorting
        filtered_obs = (
            df_obs[df_obs.taxon_id.isin(species_ids_set)]
            .sort_values("observed_on", ascending=False)
            .head(MAX_OBS_DISPLAY)  # Limit for performance
            .reset_index(drop=True)
        )

        return filtered_obs

    except Exception as e:
        st.error(f"Erro ao processar observações para {grupo}: {e}")
        return pd.DataFrame()


@st.cache_data(
    ttl=CACHE_TTL, max_entries=15, show_spinner="🔄 Processando dados de espécies..."
)
def get_species_table_ultra(obs_file, especies_file):
    """Ultra-optimized species table generation with vectorized operations"""
    try:
        # Load species data safely
        df_especies = load_csv_optimized(especies_file)

        # Clean and convert data types safely
        if not df_especies.empty and "taxon_id" in df_especies.columns:
            df_especies = df_especies.dropna(subset=["taxon_id"])
            df_especies["taxon_id"] = df_especies["taxon_id"].astype("int32")

        if df_especies.empty:
            return pd.DataFrame(), 0

        # Load observations with minimal required columns
        required_cols = ["taxon_id", "observed_on", "taxon_name"]

        df_obs = pd.read_csv(
            obs_file, usecols=required_cols, engine="c", parse_dates=["observed_on"]
        )

        # Clean and convert data types safely
        df_obs = df_obs.dropna(subset=["taxon_id"])
        df_obs["taxon_id"] = df_obs["taxon_id"].astype("int32")
        df_obs["taxon_name"] = df_obs["taxon_name"].astype("string")

        # Vectorized filtering
        species_ids_set = set(df_especies.taxon_id.tolist())
        obs_filtered = df_obs[df_obs.taxon_id.isin(species_ids_set)]

        if obs_filtered.empty:
            return pd.DataFrame(), 0

        # Calculate last month count more efficiently
        end_date = datetime.datetime.now() - datetime.timedelta(days=30)
        last_month_species = obs_filtered[obs_filtered["observed_on"] < end_date][
            "taxon_name"
        ].nunique()

        # Ultra-efficient aggregation with vectorized operations
        species_stats = (
            obs_filtered.groupby("taxon_name", sort=False)["observed_on"]
            .agg(["count", "min", "max"])
            .reset_index()
            .rename(
                columns={
                    "count": "count",
                    "min": "first_observed",
                    "max": "last_observed",
                }
            )
            .sort_values("count", ascending=False)
        )

        # Vectorized URL creation
        species_stats["taxon_url"] = (
            BASE_URL + "/taxa/" + species_stats["taxon_name"].astype(str)
        )

        return species_stats, last_month_species

    except Exception as e:
        st.error(f"Erro ao processar tabela de espécies: {e}")
        return pd.DataFrame(), 0


@st.cache_data(ttl=PHOTO_CACHE_TTL, max_entries=50)
def get_photo_url_batch(obs_ids):
    """Batch photo URL retrieval for better performance"""
    photo_urls = {}

    try:
        with requests.Session() as session:
            for obs_id in obs_ids:
                try:
                    response = session.get(
                        f"{API_PATH}/observations?id={obs_id}", timeout=5  # Add timeout
                    )
                    response.raise_for_status()
                    results = response.json()["results"]

                    if results and results[0].get("photos"):
                        photo_url = results[0]["photos"][0]["url"].replace(
                            "/square.", "/large."
                        )
                        photo_urls[obs_id] = photo_url
                    else:
                        photo_urls[obs_id] = None

                except Exception:
                    photo_urls[obs_id] = None

    except Exception as e:
        st.warning(f"Erro ao buscar fotos: {e}")

    return photo_urls


def show_last_species_optimized(df, max_display=None):
    """Optimized species display with error handling and limits"""
    if df.empty:
        st.info("🔍 Nenhuma espécie para exibir")
        return

    try:
        # Limit display for performance
        display_count = min(max_display or MAX_SPECIES_DISPLAY, len(df), 5)

        if display_count <= 0:
            st.info("📷 Nenhuma imagem disponível")
            return

        # Create efficient layout
        cols = st.columns(display_count, gap="small")

        for i in range(display_count):
            with cols[i]:
                try:
                    row = df.iloc[i]
                    photo_url = row.get("photo_url")
                    taxon_name = str(row.get("taxon_name", "Unknown"))[
                        :30
                    ]  # Truncate for performance
                    obs_id = row.get("id")
                    user_login = str(row.get("user_login", "Unknown"))[
                        :15
                    ]  # Truncate for performance

                    # Display link above image
                    st.markdown(f"[:camera: Ver]({BASE_URL}/observations/{obs_id})")

                    if photo_url and pd.notna(photo_url):
                        st.image(
                            photo_url,
                            caption=f"{taxon_name}\n📷 {user_login}",
                            use_container_width=True,
                        )
                    else:
                        st.info(f"📷 {taxon_name}\nSem foto")

                except Exception as e:
                    st.info(f"⚠️ Erro na imagem {i+1}")
                    continue

    except Exception as e:
        st.error(f"Erro ao exibir espécies: {e}")


with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Espécies de interesse]")

i = 0
counter = 0
for tab in st.tabs(
    [
        "**Espécies exóticas**",
        "**Espécies protegidas**",
        "**Espécies ameaçadas**",
    ]
):

    with tab:
        # Ultra-optimized calculations
        species_file = f"{directory}/data/species/{GRUPOS_ESPECIES[i]}.csv"
        obs_file = f"{directory}/data/{MAIN_PROJECT}_df_obs.csv"

        # Use spinner for better UX
        with st.spinner(f"📊 Carregando dados de espécies {SPECIES_NAMES[i]}..."):
            try:
                table_species, last_month_species = get_species_table_ultra(
                    obs_file, species_file
                )
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar dados: {str(e)[:50]}...")
                table_species = pd.DataFrame()
                last_month_species = 0

        col1, col2, col3 = st.columns([10, 1, 10])
        with col1:
            try:
                if not table_species.empty:
                    # Optimized metric display
                    species_type = SPECIES_NAMES[i]
                    species_count = len(table_species)
                    month_diff = species_count - last_month_species

                    st.metric(
                        f":ladybug: Espécies {species_type}",
                        species_count,
                        (
                            f"+{month_diff} último mês"
                            if month_diff > 0
                            else f"{month_diff} último mês"
                        ),
                    )

                    # Apply style only once per session
                    if f"style_applied_{i}" not in st.session_state:
                        style_metric_cards(
                            background_color="#fff",
                            border_left_color=COLORS[1],
                            box_shadow=False,
                        )
                        st.session_state[f"style_applied_{i}"] = True

                    # Dataframe para el listado de especies
                    table_species.index = np.arange(1, len(table_species) + 1)
                    st.dataframe(
                        table_species[
                            ["taxon_url", "count", "first_observed", "last_observed"]
                        ],
                        column_config={
                            "taxon_url": st.column_config.LinkColumn(
                                "Nome da espécie",
                                display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                            ),
                            "count": st.column_config.NumberColumn(
                                "Número de observações"
                            ),
                            "first_observed": st.column_config.DateColumn(
                                "Primeira observação", format="DD-MM-YYYY"
                            ),
                            "last_observed": st.column_config.DateColumn(
                                "Última observação", format="DD-MM-YYYY"
                            ),
                        },
                        hide_index=False,
                        height=340,
                    )

            except NameError:
                pass

        with col3:
            st.subheader("Observações por ano")
            project_name = st.selectbox(
                "Filtrar por ano:",
                PROJECTS.values(),
                key=f"provincia_{counter}",
            )
            counter += 1
            proj_id = next((k for k, v in PROJECTS.items() if v == project_name), None)

            # Optimized observation loading
            with st.spinner("🔄 Carregando observações..."):
                try:
                    last_obs = get_obs_by_species_group_optimized(
                        proj_id, GRUPOS_ESPECIES[i]
                    )
                except Exception as e:
                    st.warning(f"⚠️ Erro: {str(e)[:30]}...")
                    last_obs = pd.DataFrame()

            if len(last_obs) > 0:
                last_obs_formatted = last_obs[
                    ["observed_on", "user_login", "taxon_name", "id"]
                ].reset_index(drop=True)
                last_obs_formatted.index = np.arange(1, len(last_obs_formatted) + 1)
                last_obs_formatted["id"] = last_obs_formatted["id"].astype(str)
                last_obs_formatted["url"] = last_obs_formatted["id"].apply(
                    lambda x: f"https://minka-sdg.org/observations/{x}"
                )

                # Optimized summary generation
                species_counts = (
                    last_obs_formatted["taxon_name"].value_counts().head(10)
                )  # Limit for performance

                if not species_counts.empty:
                    summary_lines = [
                        f"- {name}: {count}" for name, count in species_counts.items()
                    ]
                    st.markdown("\n".join(summary_lines))
                else:
                    st.info("📊 Nenhum dado de resumo disponível")

            else:
                st.markdown("Nenhuma observação registrada.")

        st.divider()
        st.subheader(f"Imagens das últimas espécies registradas")

        # Ultra-optimized image processing
        if not last_obs.empty:
            try:
                # Get unique species efficiently
                unique_species = (
                    last_obs.drop_duplicates("taxon_id", keep="first")
                    .head(MAX_SPECIES_DISPLAY)
                    .reset_index(drop=True)
                )

                if not unique_species.empty:
                    # Batch photo URL retrieval
                    obs_ids = unique_species["id"].tolist()
                    photo_urls_dict = get_photo_url_batch(obs_ids)

                    # Add photo URLs to dataframe
                    unique_species["photo_url"] = [
                        photo_urls_dict.get(obs_id) for obs_id in obs_ids
                    ]

                    show_last_species_optimized(unique_species, MAX_SPECIES_DISPLAY)
                else:
                    st.info("📷 Nenhuma espécie única encontrada")

            except Exception as e:
                st.warning(f"⚠️ Erro ao processar imagens: {str(e)[:40]}...")
        else:
            st.info("📷 Nenhuma foto disponível para este grupo")

        i += 1

st.container(height=50, border=False)

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
