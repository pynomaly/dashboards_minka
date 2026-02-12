# Contents of ~/my_app/pages/page_3.py
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import create_footer, init_i18n, t
from utils import create_markercluster, get_number_species, get_photo_from_ob

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet_new"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)
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
init_i18n(current_page="taxonomy")

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
main_project = 264


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Cacheado de datos optimizado
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data(ttl=1800, show_spinner=False)  # Cache más corto para datos dinámicos
def load_observations_and_photos():
    """Carga observaciones y fotos con cache"""
    try:
        df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
        df_photos = pd.read_csv(f"{directory}/data/{main_project}_photos.csv")
        return df_obs, df_photos
    except:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def process_taxonomy_data(df_obs_hash):
    """Procesa datos taxonómicos con cache"""
    df_obs, _ = load_observations_and_photos()

    if len(df_obs) == 0:
        return pd.DataFrame(), pd.DataFrame()

    df_research = df_obs[df_obs.quality_grade == "research"].reset_index(drop=True)

    if len(df_research) == 0:
        return pd.DataFrame(), pd.DataFrame()

    # preparación de los rangos taxonómicos vacíos
    df_research.loc[df_research["class"].isnull(), "class"] = df_research["phylum"]
    df_research.loc[df_research["order"].isnull(), "order"] = df_research["class"]
    df_research.loc[df_research["family"].isnull(), "family"] = df_research["order"]
    df_research.loc[df_research["taxon_rank"] == "genus", "genus"] = df_research[
        "taxon_name"
    ]

    # df de taxonomías agrupdas con ["name", "parent", "number"]
    df_total = get_number_species(df_research)
    df_total.drop_duplicates(subset="name", keep="first", inplace=True)

    life_row = pd.DataFrame(
        [{"name": "Life", "number": len(df_research), "parent": ""}]
    )

    df_total = pd.concat([life_row, df_total])

    # Fix Ammophila duplicity taxon name: change by Plant Ammophila
    df_total.loc[df_total.name == "Ammophila arenaria", "parent"] = "Plant Ammophila"
    try:
        number = df_total.loc[df_total.name == "Ammophila arenaria", "number"].item()
        df2 = pd.DataFrame(
            [{"name": "Plant Ammophila", "number": number, "parent": "Poaceae"}]
        )
        df_total = pd.concat([df_total, df2], ignore_index=True)
    except:
        pass

    # Datos de primera observación
    df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
    first_observed = df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")[
        ["id", "taxon_name", "observed_on"]
    ].sort_values(by=["observed_on"], ascending=False)

    return df_total, first_observed


# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.taxonomy_title')}]")

# Cargamos observaciones del proyecto principal
df_obs, df_photos = load_observations_and_photos()

# Crear hash para cache de procesamiento taxonómico
data_hash = hash(
    str(df_obs.shape) + str(df_obs["id"].iloc[0] if len(df_obs) > 0 else "")
)
df_total, first_observed = process_taxonomy_data(data_hash)

if len(df_total) == 0:
    st.markdown(t("taxonomy.no_research_obs"))
else:

    # df_total = pd.concat([df_total, df2], ignore_index=True)
    # selector de rango
    col1, col2 = st.columns([1, 4], gap="large")

    with col1:
        cols = [
            t("ui.all_levels"),
            "kingdom | 1",
            "phylum | 2",
            "class | 3",
            "order | 4",
            "family | 5",
            "genus | 6",
        ]
        option = st.selectbox(t("ui.level"), cols)

        if option == t("ui.all_levels"):
            display_level = None
        else:
            display_level = cols.index(option) + 1

    st.markdown(f"{t('taxonomy.click_to_expand')} :point_right:")

    fig_sunburst = px.sunburst(
        df_total,
        names="name",
        parents="parent",
        values="number",
        branchvalues="total",
        color_discrete_sequence=[
            "#4aae79",
            "#f0c579",
            "#ec9e7b",
            "#426a5a",
            "#007d8a",
        ],
        maxdepth=display_level,
    )

    fig_sunburst.update_layout(width=800, height=800)

    st.plotly_chart(fig_sunburst, use_container_width=True)

    # Cache CSV conversion
    if "csv10" not in st.session_state:
        st.session_state.csv10 = convert_df(df_total)

    st.download_button(
        label=t("ui.download_data"),
        data=st.session_state.csv10,
        file_name="num_species_taxonomy.csv",
        mime="text/csv",
    )
st.divider()

with st.container():
    st.subheader(t("taxonomy.taxon_search"))
    col1, col2 = st.columns([1, 3], gap="large")
    with col1:
        taxon_name = st.text_input(t("taxonomy.taxon_name"), "")

    with col2:

        # Si el taxon_name es este o si es descendiente de ese taxon_name
        df_result = (
            df_obs[
                (df_obs["taxon_name"].str.lower() == taxon_name.lower())
                | df_obs[["kingdom", "phylum", "class", "order", "family", "genus"]]
                .map(lambda x: str(x).lower())
                .eq(taxon_name.lower())
                .any(axis=1)
            ]
            .reset_index(drop=True)
            .copy()
        )

        # Clave única en session_state basada en el taxón
        cluster_map_key = f"clustermap_{taxon_name.lower()}"

        # Crear el mapa solo si no existe para este taxón
        if cluster_map_key not in st.session_state:
            st.session_state[cluster_map_key] = create_markercluster(
                df_result, center=[41.36174441599461, 2.108076037807884], zoom=10
            )

        # Convertir el mapa a HTML
        map_html = st.session_state[cluster_map_key]._repr_html_()

        # Renderizar el mapa en Streamlit
        components.html(map_html, height=600)

    # Cache CSV conversion per taxon
    csv_key = f"csv3_{taxon_name.lower()}"
    if csv_key not in st.session_state:
        st.session_state[csv_key] = convert_df(df_result)

    st.download_button(
        label=t("ui.download_data"),
        data=st.session_state[csv_key],
        file_name="observacions_species_filtered.csv",
        mime="text/csv",
    )

st.divider()
# últimas especies incorporadas
if len(df_obs) > 0:
    col1, col2 = st.columns([5, 14], gap="large")
    with col1:
        # Usar datos ya procesados y cacheados

        st.markdown(f"#### {t('taxonomy.first_observation_date')}")
        st.dataframe(
            first_observed[["taxon_name", "observed_on"]],
            column_config={
                "taxon_name": st.column_config.TextColumn(
                    t("taxonomy.species_name"), width="medium"
                ),
                "observed_on": st.column_config.DateColumn(
                    t("taxonomy.first_observation"), format="DD-MM-YYYY"
                ),
            },
            hide_index=True,
            height=500,
        )
        # Cache CSV conversion
        if "csv9" not in st.session_state:
            st.session_state.csv9 = convert_df(first_observed)

        st.download_button(
            label=t("ui.download_data"),
            data=st.session_state.csv9,
            file_name="first_observed_species.csv",
            mime="text/csv",
        )

    with col2:
        # Extraemos una foto de cada una de las últimas especies
        ids_obs = first_observed["id"].to_list()[:3]
        st.markdown(f"#### {t('taxonomy.last_species_added')}")
        c1, c2, c3 = st.columns(3)
        with c1:
            get_photo_from_ob(df_photos, ids_obs[0])
        with c2:
            get_photo_from_ob(df_photos, ids_obs[1])
        with c3:
            get_photo_from_ob(df_photos, ids_obs[2])


# Footer
create_footer()
