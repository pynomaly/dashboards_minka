import datetime
import os

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_markercluster,
    fig_cols,
    fig_monthly_bars,
    get_photo_url_from_taxon,
)

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
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
            width: 220px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 220px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
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


# Cacheado de datos
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


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
        st.header(":blue[Espècies d'interès]")

i = 0
for tab in st.tabs(
    [
        "**Espècies invasores**",
        "**Espècies exòtiques**",
        "**Espècies protegides**",
        "**Espècies amenaçades**",
    ]
):
    with tab:
        # Cálculos generales
        df_especies = load_csv(f"{directory}/data/species/{grupos_especies[i]}.csv")
        df_obs = load_csv(f"{directory}/data/264_obs.csv")
        df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])
        obs_result = df_obs[
            df_obs.taxon_id.isin(df_especies.taxon_id.to_list())
        ].reset_index(drop=True)
        obs_result = pd.merge(
            obs_result, df_especies, on=["taxon_id", "taxon_name"], how="left"
        )

        end_date = datetime.datetime.now().replace(day=1)
        last_month_invasoras = obs_result.loc[
            obs_result["observed_on"] < end_date, "taxon_name"
        ].nunique()

        # tabla de num. observaciones por especie
        count_invasoras = obs_result.taxon_name.value_counts().to_frame().reset_index()
        count_invasoras = pd.merge(
            count_invasoras,
            obs_result.drop_duplicates(subset=["taxon_name"])[
                ["taxon_name", "taxon_id", "estat", "font", "link"]
            ],
            on=["taxon_name"],
            how="left",
        )
        count_invasoras["first_observed"] = count_invasoras["taxon_name"].apply(
            lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].min()
        )
        count_invasoras["last_observed"] = count_invasoras["taxon_name"].apply(
            lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].max()
        )
        count_invasoras["taxon_url"] = count_invasoras["taxon_name"].apply(
            lambda x: f"https://minka-sdg.org/taxa/{x}"
        )

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
                name = "invasores"
            elif grupos_especies[i] == "exoticas":
                name = "exòtiques"
            elif grupos_especies[i] == "amenazadas":
                name = "amenaçades"
            elif grupos_especies[i] == "protegidas":
                name = "protegides"
            st.metric(
                f":ladybug: Nombre d'espècies {name}",
                len(count_invasoras),
                f"+{len(count_invasoras) - last_month_invasoras} últim mes",
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
                title="Nombre d'espècies per ciutat",
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
                        "Nom de l'espècie",
                        display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                    ),
                    "photo": st.column_config.ImageColumn(
                        "Imatge (doble clic per ampliar)",
                        help="Previsualitza",
                        width=200,
                    ),
                    "count": st.column_config.NumberColumn("Nombre d'observacions"),
                    "first_observed": st.column_config.DateColumn(
                        "Primera observació", format="DD-MM-YYYY"
                    ),
                    "last_observed": st.column_config.DateColumn(
                        "Darrera observació", format="DD-MM-YYYY"
                    ),
                    "estat": st.column_config.TextColumn(
                        label="Estat d'amenaça", width="medium"
                    ),
                    "link": st.column_config.LinkColumn(
                        label="Font",
                        width="small",
                        display_text="enllaç",  # Texto fijo para todos los enlaces
                    ),
                },
                hide_index=False,
                height=600,
            )

        st.divider()
        st.subheader("Observacions dels darrers 12 mesos")
        col1, col2, col3 = st.columns([2, 2, 5])
        with col1:
            city = st.selectbox(
                "Filtre per municipi:",
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
                st.markdown("**Sumari d'espècies:**")
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
                            "Data d'observació", format="DD-MM-YYYY"
                        ),
                        "user_login": st.column_config.TextColumn(
                            label="Participant", width="medium"
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            label="Nom de l'espècie", width="medium"
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
                st.markdown("Cap observació registrada.")

        st.divider()

        # selectores de especies y places
        st.subheader("Observacions per espècie i municipi")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            lista_especies = ["Totes"]
            taxon_unique = obs_result.taxon_name.unique()
            lista_especies.extend(sorted(taxon_unique))
            especie = st.selectbox(
                "**Filtrar per nom d'espècie:**",
                lista_especies,
                key=f"select_especie{i}",
            )
        with col2:
            lista_places = ["Tots"]
            lista_places.extend(ciutats)
            place = st.selectbox(
                "**Filtrar per municipi:**", lista_places, key=f"select_place{i}"
            )
        with col3:
            st.markdown(
                "**NOTA**: Les espècies amenaçades no es mostren al mapa perquè les seves coordenades estan protegides."
            )

        # gráfico de observaciones por mes y mapa
        col1, col2 = st.columns(2)
        with col1:
            if especie != "Totes":
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

            if place != "Tots":
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
                st.markdown("Cap espècie en aquesta cerca")

            # Descarga de datos
            csv_invasoras = convert_df(obs_especie2)
            st.download_button(
                label="Descarrega les dades",
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
        especie = "Totes"
        place = "Tots"

st.container(height=50, border=False)

# Footer
with st.container(border=True):
    col1, __, col2 = st.columns([10, 1, 5], gap="small")
    with col1:
        st.markdown("##### Organitzadors")
        st.image(
            f"{directory}/images/organizadores_bioplatgesmet_logos2.png",
        )
    with col2:
        st.markdown("##### Amb el finançament dels projectes europeus")
        st.image(
            f"{directory}/images/financiadores_bioplatgesmet_logos.png",
        )
