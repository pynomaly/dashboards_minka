# Contents of ~/my_app/pages/page_3.py
import os

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import folium_static
from utils import create_markercluster, get_number_species, get_photo_from_ob

try:
    directory = f"{os.environ['DASHBOARDS']}/arsinoe"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.markdown(
    """
    <style>
        body {
            background-color: white !important;
            color: black !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"
main_project = 186
colors = ["#119239", "#562579", "#f4c812", "#f07d12", "#e61b1f", "#1e388d"]
athens_center = [37.9795, 23.7162]


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Cacheado de datos
@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/ARSINOE.png")
    with col2:
        st.title("Taxonomy of species observed")
        st.markdown("###### (observations with research grade)")

# Cargamos observaciones del proyecto principal
try:
    df_obs = load_csv(f"{directory}/data/{main_project}_obs.csv")
    df_photos = load_csv(f"{directory}/data/{main_project}_photos.csv")
except:
    df_obs = pd.DataFrame()

try:
    # sunburst: número de especies observadas por rango taxonómico
    df_research = df_obs[df_obs.quality_grade == "research"].reset_index(drop=True)

    if len(df_research) == 0:
        st.markdown("No observation with research grade yet")
    else:
        # preparación de los rangos taxonómicos vacíos
        df_research.loc[df_research["class"].isnull(), "class"] = df_research["phylum"]
        df_research.loc[df_research["order"].isnull(), "order"] = df_research["class"]
        df_research.loc[df_research["family"].isnull(), "family"] = df_research["order"]
        df_research.loc[df_research["taxon_rank"] == "genus", "genus"] = df_research[
            "taxon_name"
        ]

        # df de taxonomías agrupdas con ["name", "parent", "number"]
        df_total = get_number_species(df_research)

        rank_order = ["Life", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus"]
        df_total = df_total[df_total["rank"].isin(rank_order)]

        df_total.drop_duplicates(subset="name", keep="first", inplace=True)

        life_row = pd.DataFrame(
            [{"name": "Life", "number": len(df_research), "parent": ""}]
        )

        df_total = pd.concat([life_row, df_total])

        # Fix Ammophila duplicity taxon name: change by Plant Ammophila
        df_total.loc[df_total.name == "Ammophila arenaria", "parent"] = (
            "Plant Ammophila"
        )
        try:
            number = df_total.loc[
                df_total.name == "Ammophila arenaria", "number"
            ].item()
            df2 = pd.DataFrame(
                [{"name": "Plant Ammophila", "number": number, "parent": "Poaceae"}]
            )
            df_total = pd.concat([df_total, df2], ignore_index=True)
        except:
            pass

        fig_sunburst = px.sunburst(
            df_total,
            names="name",
            parents="parent",
            values="number",
            branchvalues="total",
            color_discrete_sequence=colors,
        )

        fig_sunburst.update_layout(width=800, height=800)

        st.plotly_chart(fig_sunburst, use_container_width=True)

        csv10 = convert_df(df_total)

        st.download_button(
            label="Download data",
            data=csv10,
            file_name="num_species_taxonomy.csv",
            mime="text/csv",
        )
except AttributeError:
    st.markdown("No observation with research grade yet")
st.divider()

with st.container():
    st.subheader("Taxonomy search")
    col1, col2 = st.columns([1, 3], gap="large")
    with col1:
        taxon_name = st.text_input("Taxon name:", "")

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
                df_result, center=athens_center, zoom=10
            )

        # Convertir el mapa a HTML
        map_html = st.session_state[cluster_map_key]._repr_html_()

        # Renderizar el mapa en Streamlit
        components.html(map_html, height=600)

    csv3 = convert_df(df_result)

    st.download_button(
        label="Download data",
        data=csv3,
        file_name="observacions_species_filtered.csv",
        mime="text/csv",
    )

st.divider()
# últimas especies incorporadas
if len(df_obs) > 0:
    col1, col2 = st.columns([5, 14], gap="large")
    with col1:
        # Últimes espècies registrades
        df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
        first_observed = df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")[
            ["id", "taxon_name", "observed_on"]
        ].sort_values(by=["observed_on"], ascending=False)

        st.markdown("#### Date of first observation")
        st.dataframe(
            first_observed[["taxon_name", "observed_on"]],
            column_config={
                "taxon_name": st.column_config.TextColumn(
                    "Species name", width="medium"
                ),
                "observed_on": st.column_config.DateColumn(
                    "First observation", format="DD-MM-YYYY"
                ),
            },
            hide_index=True,
            height=500,
        )
        csv9 = convert_df(first_observed)

        st.download_button(
            label="Download data",
            data=csv9,
            file_name="first_observed_species.csv",
            mime="text/csv",
        )

    with col2:
        # Extraemos una foto de cada una de las últimas especies
        ids_obs = first_observed["id"].to_list()[:3]
        st.markdown("#### Latest species added")
        c1, c2, c3 = st.columns(3)
        with c1:
            get_photo_from_ob(df_photos, ids_obs[0])
        with c2:
            get_photo_from_ob(df_photos, ids_obs[1])
        with c3:
            get_photo_from_ob(df_photos, ids_obs[2])


st.container(height=50, border=False)

with st.container(border=True):
    col1, __, col2 = st.columns([10, 1, 5], gap="small")
    with col1:
        st.markdown("##### Organizers")
        st.image(
            f"{directory}/images/organizers_arsinoe.png",
        )
    with col2:
        st.markdown("##### With the funding of European projects")
        st.image(
            f"{directory}/images/funders_arsinoe.png",
        )
