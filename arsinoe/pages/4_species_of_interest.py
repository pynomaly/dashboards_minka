import datetime
import os

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards
from utils import create_markercluster, fig_cols, fig_monthly_bars

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

colors = ["#119239", "#562579", "#f4c812", "#f07d12", "#e61b1f", "#1e388d"]
main_project = 186

species_groups = ["invasive", "protected"]
schools = {
    252: "3ο ΓΥΜΝΑΣΙΟ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ",
    197: "2ο Γυμνάσιο Νέας Φιλαδέλφειας",
    247: "ΜΟΥΣΙΚΟ ΓΥΜΝΑΣΙΟ Λ.Τ. ΙΛΙΟΥ",
    257: "11ο Γυμνάσιο ΙΛΙΟΥ",
    196: "1ο ΓΕΛ ΑΧΑΡΝΩΝ",
    240: "ΒΑΡΒΑΚΕΙΟ ΠΡΟΤΥΠΟ ΓΥΜΝΑΣΙΟ",
    267: "1ο Γυμνάσιο ΑΣΠΡΟΠΥΡΓΟΥ",
    253: "6o ΓΕΛ ΑΘΗΝΩΝ",
    195: "7ο ΓΕΛ ΑΧΑΡΝΩΝ",
    211: "3ο ΓΕΛ ΖΩΓΡΑΦΟΥ",
    238: "5ο ΕΚ ΑΝΑΤΟΛΙΚΗΣ ΑΤΤΙΚΗΣ",
    354: "Γυμνάσιο-Λυκειακές Τάξεις Λαιμού Πρεσπών",
    241: "3ο ΕΠΑΛ Αθηνών",
    254: "4ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΑΜΑΡΟΥΣΙΟΥ",
    210: "ΠΡΟΤΥΠΟ ΓΕΛ ΑΓΙΩΝ ΑΝΑΡΓΥΡΩΝ",
    245: "5ο ΓΕΛ ΑΧΑΡΝΩΝ ΑΓΙΑ ΑΝΝΑ",
    237: "1ο Γυμνάσιο Καματερού",
    386: "1ο ΕΠΑΛ ΝΕΑΣ ΙΩΝΙΑΣ ΑΤΤΙΚΗΣ",
    384: "4ο Δημοτικό σχολείο Περάματος",
    208: "1ο ΓΕΛ ΚΕΡΑΤΣΙΝΙΟΥ",
    194: "3ο ΓΕΛ ΑΧΑΡΝΩΝ",
    382: "1ο ΓΕΛ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ",
    250: "ΓΕΛ ΛΑΥΡΙΟΥ",
    390: "5ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΚΕΡΑΤΣΙΝΙΟΥ",
    274: "1ο ΕΠΑΛ Αγίων Αναργύρων",
    244: "ΓΥΜΝΑΣΙΟ ΑΝΘΟΥΣΑΣ",
    246: "1ο ΓΥΜΝΑΣΙΟ ΠΕΥΚΗΣ",
    272: "2ο Γυμνάσιο Καισαριανής",
    389: "3 ΓΥΜΝΑΣΙΟ ΙΛΙΟΥ",
    188: "1ο Εσπερινό Γυμνάσιο ΑΘΗΝΩΝ",
    236: "ΣΧΟΛΗ ΜΩΡΑΪΤΗ-ΟΜΙΛΟΣ ΠΑΡΑΤΗΡΗΣΗΣ & ΕΡΜΗΝΕΙΑΣ ΤΗΣ ΦΥΣΗΣ",
    299: "6ο ΓΕΛ Περιστερίου",
    198: "6ο Γυμνάσιο Ζωγράφου",
    202: "10o ΓΕΛ ΠΕΡΙΣΤΕΡΙΟΥ",
    374: "11ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΑΜΑΡΟΥΣΙΟΥ",
    392: "1o ΓΥΜΝΑΣΙΟ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ",
    379: "1o ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΝΕΑΣ ΣΜΥΡΝΗΣ",
    388: "1ο ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΚΑΜΑΤΕΡΟΥ",
    260: "1ο Γυμνάσιο Κηφησιάς",
    376: "1ο Γυμνάσιο Ραφήνας",
    207: "26ο ΓΕΛ ΑΘΗΝΩΝ",
    393: "2ο ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΣΑΛΑΜΙΝΑΣ",
    387: "2ο Γενικό Λύκειο Χολαργού",
    397: "3o ΓΥΜΝΑΣΙΟ ΠΕΡΙΣΤΕΡΙΟΥ",
    251: "3ο Γυμνάσιο Γαλατσίου",
    235: "3ο Γυμνάσιο Χαϊδαρίου",
    380: "3ο ΔΗΜ.ΣΧ.ΑΡΓΥΡΟΥΠΟΛΗΣ",
    373: "49ο ΓΕ.Λ. Αθηνών",
    383: "4o ΓΥΜΝΑΣΙΟ ΑΙΓΑΛΕΩ",
    381: "4ο ΓΕΛ ΑΘΗΝΩΝ",
    391: "4ο Δημοτικό Σχολείο Αλίμου",
    375: "7o ΓΕΛ ΠΕΙΡΑΙΑ",
    378: "7ο ΗΜΕΡΗΣΙΟ ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΑΧΑΡΝΩΝ",
    377: "ΓΕΛ ΨΥΧΙΚΟΥ",
    385: "ΓΥΜΝΑΣΙΟ Ν. ΧΑΛΚΗΔΟΝΑΣ",
    199: "6ο ΓΕΛ Περιστερίου",
}


# Cacheado de datos
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


def get_obs_by_species_group(df_obs, grupo):
    df_grupo = pd.read_csv(f"{directory}/data/species/arsinoe_interest_species.csv")

    if grupo == "protected":
        df_grupo = df_grupo[df_grupo["category"].str.contains("Protected")].reset_index(
            drop=True
        )
    elif grupo == "invasive":
        df_grupo = df_grupo[df_grupo["category"].str.contains("IAS")].reset_index(
            drop=True
        )

    species_ids = df_grupo.taxon_id.to_list()
    last_obs = (
        df_obs[df_obs.taxon_id.isin(species_ids)]
        .sort_values(by="observed_on", ascending=False)
        .reset_index(drop=True)
    )
    return last_obs


def get_species_by_school(grupo_especie, df_obs):
    resultados = []
    df_grupo = pd.read_csv(f"{directory}/data/species/arsinoe_interest_species.csv")

    if grupo_especie == "protected":
        df_grupo = df_grupo[df_grupo["category"].str.contains("Protected")].reset_index(
            drop=True
        )
    elif grupo_especie == "invasive":
        df_grupo = df_grupo[df_grupo["category"].str.contains("IAS")].reset_index(
            drop=True
        )

    for school in list(df_obs["address"].astype(int).unique()):
        df_obs = load_csv(f"{directory}/data/obs_{school}.csv")
        obs_result = df_obs[df_obs.taxon_id.isin(df_grupo.taxon_id.to_list())]
        num_especies = obs_result.taxon_name.nunique()
        resultados.append([schools[int(school)], num_especies])

    df_resultados = pd.DataFrame(resultados, columns=["school", "num_especies"])
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
        st.image(f"{directory}/images/ARSINOE.png")
    with col2:
        st.title(f"Species of interest")

i = 0
for tab in st.tabs(
    [
        "**Invasive species**",
        "**Protected species**",
    ]
):
    with tab:
        # Cálculos generales
        df_especies = load_csv(f"{directory}/data/species/arsinoe_interest_species.csv")

        df_obs = load_csv(f"{directory}/data/{main_project}_obs.csv")
        df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])
        print(tab)

        grupo = "invasive"
        if i == 0:
            grupo = "invasive"
            st.markdown(
                ":grey[*This list is continuously under revision. It includes species that are of Union concern (Regulation (EU) 1143/2014), as well as other species considered to be invasive in Greece by scientists.*]"
            )
        elif i == 1:
            grupo = "protected"

        obs_result = get_obs_by_species_group(df_obs, grupo)

        end_date = datetime.datetime.now().replace(day=1)
        last_month_invasoras = obs_result.loc[
            obs_result["observed_on"] < end_date, "taxon_name"
        ].nunique()

        # tabla de num. observaciones por especie
        count_invasoras = obs_result.taxon_name.value_counts().to_frame().reset_index()
        count_invasoras["first_observed"] = count_invasoras["taxon_name"].apply(
            lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].min()
        )
        count_invasoras["last_observed"] = count_invasoras["taxon_name"].apply(
            lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].max()
        )
        count_invasoras["taxon_url"] = count_invasoras["taxon_name"].apply(
            lambda x: f"https://minka-sdg.org/taxa/{x}"
        )

        col1, col3 = st.columns([7, 10])
        with col1:
            if species_groups[i] == "invasive":
                name = "invasive"
            elif species_groups[i] == "protected":
                name = "protected"
            st.metric(
                f":ladybug: Number of {name} species",
                len(count_invasoras),
                f"+{len(count_invasoras) - last_month_invasoras} last month",
            )
            style_metric_cards(
                background_color="#fff",
                # border_left_color="#C2C2C2",
                border_left_color=colors[1],
                box_shadow=False,
            )

            count_invasoras.index = np.arange(1, len(count_invasoras) + 1)
            st.dataframe(
                count_invasoras[
                    ["taxon_url", "count", "first_observed", "last_observed"]
                ],
                column_config={
                    "taxon_url": st.column_config.LinkColumn(
                        "Species name",
                        display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                    ),
                    "count": st.column_config.NumberColumn("Nombre d'observacions"),
                    "first_observed": st.column_config.DateColumn(
                        "First observed", format="DD-MM-YYYY"
                    ),
                    "last_observed": st.column_config.DateColumn(
                        "Last observed", format="DD-MM-YYYY"
                    ),
                },
                hide_index=False,
                height=340,
            )

        with col3:
            # gráfico de barras especies por ciudad
            df_resultados = get_species_by_school(species_groups[i], df_obs)
            df_resultados = df_resultados[
                df_resultados["num_especies"] > 0
            ].reset_index(drop=True)
            fig_species_by_city = fig_cols(
                df_resultados,
                "school",
                "num_especies",
                title="Number of species by school",
                color_code=colors[0],
            )
            st.plotly_chart(
                fig_species_by_city,
                config=config_modebar,
                use_container_width=True,
            )

        st.divider()
        # selectores de especies y places
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            lista_especies = ["All"]
            taxon_unique = obs_result.taxon_name.unique()
            lista_especies.extend(sorted(taxon_unique))
            especie = st.selectbox(
                "**Filter by species name:**",
                lista_especies,
                key=f"select_species{i}",
            )
        with col2:
            lista_places = ["All"]
            lista_places.extend(schools.values())
            place = st.selectbox(
                "**Filter by school:**", lista_places, key=f"select_place{i}"
            )

        col1, col2 = st.columns(2)
        with col1:
            if especie != "All":
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

            if place != "All":
                place_id = list(schools.keys())[list(schools.values()).index(place)]
                obs_place = load_csv(f"{directory}/data/obs_{place_id}.csv")
                list_obs_in_place = obs_place["id"].to_list()
                obs_especie2 = obs_especie[
                    obs_especie["id"].isin(list_obs_in_place)
                ].reset_index(drop=True)
            else:
                obs_especie2 = obs_especie

            # gráfico de observaciones por mes
            if len(obs_especie2) > 0:
                fig = fig_monthly_bars(obs_especie2)
                st.plotly_chart(
                    fig, config={"displayModeBar": False}, use_container_width=True
                )
            else:
                st.markdown("No species in this search")

            # Descarga de datos
            csv_interest_species = convert_df(obs_especie2)
            st.download_button(
                label="Download data",
                data=csv_interest_species,
                file_name=f"obs_{species_groups[i]}.csv",
                mime="text/csv",
                key=f"download{i}",
            )
        with col2:
            # mapa de observaciones
            markermap = create_markercluster(obs_especie2, zoom=10)
            map_html2 = markermap._repr_html_()
            components.html(map_html2, height=900)

        i += 1
        especie = "Totes"
        place = "Tots"

st.container(height=50, border=False)

# Footer
with st.container(border=True):
    col1, col2 = st.columns([15, 7], gap="small")
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
