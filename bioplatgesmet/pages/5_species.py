import datetime
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import create_footer, init_i18n, t
from utils import (
    create_markercluster,
    fig_cols,
    fig_monthly_bars,
    get_photo_url_from_taxon,
)

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
init_i18n(current_page="species")

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

colors = ["#009DE0", "#0081B8", "#00567A"]
main_project = 264

grupos_especies = ["invasoras", "exoticas", "protegidas", "amenazadas"]
ciutats = [
    "Badalona",
    "Barcelona",
    "Castelldefels",
    "El Prat de Llobregat",
    "Gavà",
    "Montgat",
    "Sant Adrià del Besòs",
    "Viladecans",
]


# Cacheado de datos optimizado
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data(ttl=1800, show_spinner=False)
def load_main_observations():
    """Carga observaciones principales con cache"""
    df_obs = pd.read_csv(f"{directory}/data/264_obs.csv")
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])
    return df_obs


@st.cache_data(ttl=3600, show_spinner=False)
def process_species_group_data(grupo_especies_name):
    """Procesa datos de grupo de especies con cache"""
    df_especies = pd.read_csv(f"{directory}/data/species/{grupo_especies_name}.csv")
    df_obs = load_main_observations()

    obs_result = df_obs[
        df_obs.taxon_id.isin(df_especies.taxon_id.to_list())
    ].reset_index(drop=True)
    obs_result = pd.merge(
        obs_result, df_especies, on=["taxon_id", "taxon_name"], how="left"
    )

    # Calcular metricas
    end_date = datetime.datetime.now().replace(day=1)
    last_month_count = obs_result.loc[
        obs_result["observed_on"] < end_date, "taxon_name"
    ].nunique()

    # tabla de num. observaciones por especie
    count_species = obs_result.taxon_name.value_counts().to_frame().reset_index()
    count_species = pd.merge(
        count_species,
        obs_result.drop_duplicates(subset=["taxon_name"])[
            ["taxon_name", "taxon_id", "estat", "font", "link"]
        ],
        on=["taxon_name"],
        how="left",
    )

    # Fechas de observación
    for idx, row in count_species.iterrows():
        taxon_obs = obs_result[obs_result["taxon_name"] == row["taxon_name"]]
        count_species.loc[idx, "first_observed"] = taxon_obs["observed_on"].min()
        count_species.loc[idx, "last_observed"] = taxon_obs["observed_on"].max()

    count_species["taxon_url"] = count_species["taxon_name"].apply(
        lambda x: f"https://minka-sdg.org/taxa/{x}"
    )

    return obs_result, count_species, last_month_count


def get_obs_by_species_group(df_obs, grupo):
    df_grupo = load_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )
    return last_obs


def get_species_by_city(grupo_especie):
    resultados = []
    df_especies = load_csv(f"{directory}/data/species/{grupo_especie}.csv")
    for ciutat in ciutats:
        df_obs = load_csv(f"{directory}/data/obs_{ciutat}.csv")
        obs_result = df_obs[df_obs.taxon_id.isin(df_especies.taxon_id.to_list())]
        num_especies = obs_result.taxon_name.nunique()
        resultados.append([ciutat, num_especies])

    df_resultados = pd.DataFrame(resultados, columns=["ciutat", "num_especies"])
    df_resultados.sort_values(by=["num_especies"], ascending=False, inplace=True)
    return df_resultados


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# st.sidebar.markdown("# Espècies introduïdes amb espècies protegides")
# st.sidebar.markdown("Descripció")

# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.species_title')}]")

i = 0
for tab in st.tabs(
    [
        f"**{t('species_page.invasive_species')}**",
        f"**{t('species_page.exotic_species')}**",
        f"**{t('species_page.protected_species')}**",
        f"**{t('species_page.threatened_species')}**",
    ]
):
    with tab:
        # Usar datos cacheados y procesados
        obs_result, count_invasoras, last_month_invasoras = process_species_group_data(
            grupos_especies[i]
        )
        df_obs = load_main_observations()  # Necesario para uso posterior

        # mostrar tabla de especies
        if grupos_especies[i] == "amenazadas":
            count_invasoras = load_csv(f"{directory}/amenazadas.csv")
            count_invasoras = count_invasoras[count_invasoras["count"] > 0].sort_values(
                by="count", ascending=False
            )
            count_invasoras["taxon_url"] = count_invasoras["taxon_name"].apply(
                lambda x: f"https://minka-sdg.org/taxa/{x}"
            )
            df_amenazadas = pd.read_csv(f"{directory}/data/species/amenazadas.csv")
            count_invasoras = pd.merge(
                count_invasoras,
                df_amenazadas,
                on=["taxon_name", "taxon_id"],
                how="left",
            )

        col1, col2 = st.columns([6, 10], gap="medium")
        with col1:
            if grupos_especies[i] == "invasoras":
                name = t("species_page.invasive")
            elif grupos_especies[i] == "exoticas":
                name = t("species_page.exotic")
            elif grupos_especies[i] == "amenazadas":
                name = t("species_page.threatened")
            elif grupos_especies[i] == "protegidas":
                name = t("species_page.protected")
            st.metric(
                f":ladybug: {t('species_page.num_species')} {name}",
                len(count_invasoras),
                f"+{len(count_invasoras) - last_month_invasoras} {t('metrics.last_month')}",
            )
            style_metric_cards(
                background_color="#fff",
                # border_left_color="#C2C2C2",
                border_left_color=colors[1],
                box_shadow=False,
            )

            # gráfico de barras especies por ciudad
            df_resultados = get_species_by_city(grupos_especies[i])
            fig_species_by_city = fig_cols(
                df_resultados,
                "ciutat",
                "num_especies",
                title=t("charts.species_by_city"),
                color_code="#0081B8",
            )
            st.plotly_chart(
                fig_species_by_city,
                config=config_modebar,
                use_container_width=True,
            )

        with col2:
            # tabla de especies
            count_invasoras.index = np.arange(1, len(count_invasoras) + 1)
            count_invasoras["photo"] = count_invasoras["taxon_id"].apply(
                get_photo_url_from_taxon
            )

            st.dataframe(
                count_invasoras[
                    [
                        "taxon_url",
                        "photo",
                        "count",
                        "first_observed",
                        "last_observed",
                        "estat",
                        # "font",
                        "link",
                    ]
                ],
                column_config={
                    "taxon_url": st.column_config.LinkColumn(
                        t("species_page.species_name_col"),
                        display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                    ),
                    "photo": st.column_config.ImageColumn(
                        t("municipalities.image_column"),
                        help="Preview",
                        width=200,
                    ),
                    "count": st.column_config.NumberColumn(
                        t("species_page.observations_count_col")
                    ),
                    "first_observed": st.column_config.DateColumn(
                        t("species_page.first_observation_col"), format="DD-MM-YYYY"
                    ),
                    "last_observed": st.column_config.DateColumn(
                        t("species_page.last_observation_col"), format="DD-MM-YYYY"
                    ),
                    "estat": st.column_config.TextColumn(
                        label=t("species_page.threat_status"), width="medium"
                    ),
                    "link": st.column_config.LinkColumn(
                        label=t("species_page.source"),
                        width="small",
                        display_text=t("species_page.link"),
                    ),
                },
                hide_index=False,
                height=600,
            )

        st.divider()
        st.subheader(t("species_page.last_12_months"))
        col1, col2, col3 = st.columns([2, 2, 5])
        with col1:
            city = st.selectbox(
                t("ui.filter_by_municipality"),
                ciutats,
                key=f"city_{i}",
            )
            last_obs = get_obs_by_species_group(df_obs, grupos_especies[i])
            fecha_limite = pd.Timestamp.today() - pd.DateOffset(months=12)

        with col2:
            if city == "":
                six_month = last_obs.loc[(last_obs.observed_on > fecha_limite)]

            else:
                six_month = last_obs.loc[
                    (last_obs.observed_on > fecha_limite) & (last_obs.address == city)
                ]
            if len(six_month) > 0:
                six_month_formatted = six_month[
                    ["observed_on", "user_login", "taxon_name", "id"]
                ].reset_index(drop=True)
                six_month_formatted.index = np.arange(1, len(six_month_formatted) + 1)
                six_month_formatted["id"] = six_month_formatted["id"].astype(str)

                # bloque sumario
                st.markdown(f"**{t('species_page.species_summary')}**")
                sumari = ""
                for idx, row in (
                    six_month_formatted["taxon_name"]
                    .value_counts()
                    .to_frame()
                    .reset_index()
                    .iterrows()
                ):
                    sumari += f"- {row.taxon_name}: {row['count']}\n"

                st.markdown(sumari)

        with col3:
            if len(six_month) > 0:
                # bloque tabla
                if len(six_month_formatted) == 1:
                    height = 40
                elif len(six_month_formatted) == 2:
                    height = 105
                elif len(six_month_formatted) == 3:
                    height = 142
                elif len(six_month_formatted) == 4:
                    height = 180
                elif len(six_month_formatted) == 5:
                    height = 210
                else:
                    height = 500
                st.dataframe(
                    six_month_formatted,
                    column_config={
                        "observed_on": st.column_config.DateColumn(
                            t("species_page.observation_date"), format="DD-MM-YYYY"
                        ),
                        "user_login": st.column_config.TextColumn(
                            label=t("species_page.participant"), width="medium"
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            label=t("species_page.species_name_col"), width="medium"
                        ),
                        "id": st.column_config.LinkColumn(
                            "Link",
                            width="small",
                            display_text=r"https://minka-sdg.org/observations/(.*?)",
                        ),
                    },
                    hide_index=True,
                    height=height,
                )

            else:
                st.markdown(t("species_page.no_observations"))

        st.divider()

        # selectores de especies y places
        st.subheader(t("species_page.observations_by_species_municipality"))
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            lista_especies = [t("ui.all")]
            taxon_unique = obs_result.taxon_name.unique()
            lista_especies.extend(sorted(taxon_unique))
            especie = st.selectbox(
                f"**{t('ui.filter_by_species')}**",
                lista_especies,
                key=f"select_especie{i}",
            )
        with col2:
            lista_places = [t("ui.all_places")]
            lista_places.extend(ciutats)
            place = st.selectbox(
                f"**{t('ui.filter_by_place')}**", lista_places, key=f"select_place{i}"
            )
        with col3:
            st.markdown(f"**{t('species_page.threatened_note')}**")

        # gráfico de observaciones por mes y mapa
        col1, col2 = st.columns(2)
        with col1:
            if especie != t("ui.all"):
                obs_especie = (
                    df_obs[
                        (df_obs["taxon_name"].str.lower() == especie.lower())
                        | df_obs[
                            ["kingdom", "phylum", "class", "order", "family", "genus"]
                        ]
                        .map(lambda x: str(x).lower())
                        .eq(especie.lower())
                        .any(axis=1)
                    ]
                    .reset_index(drop=True)
                    .copy()
                )
            else:
                obs_especie = obs_result

            if place != t("ui.all_places"):
                obs_place = load_csv(f"{directory}/data/obs_{place}.csv")
                list_obs_in_place = obs_place["id"].to_list()
                obs_especie2 = obs_especie[
                    obs_especie["id"].isin(list_obs_in_place)
                ].reset_index(drop=True)
            else:
                obs_especie2 = obs_especie

            if len(obs_especie2) > 0:
                fig = fig_monthly_bars(obs_especie2)
                st.plotly_chart(
                    fig, config={"displayModeBar": False}, use_container_width=True
                )
            else:
                st.markdown(t("species_page.no_species_search"))

            # Descarga de datos
            csv_invasoras = convert_df(obs_especie2)
            st.download_button(
                label=t("ui.download_data"),
                data=csv_invasoras,
                file_name=f"obs_{grupos_especies[i]}.csv",
                mime="text/csv",
                key=f"download{i}",
            )
        with col2:
            # mapa de observaciones

            markermap3 = create_markercluster(
                obs_especie2, zoom=10, center=[41.36174441599461, 2.108076037807884]
            )
            map_html3 = markermap3._repr_html_()
            components.html(map_html3, height=600)

        i += 1
        especie = t("ui.all")
        place = t("ui.all_places")

# Footer
create_footer()
