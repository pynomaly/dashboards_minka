# Contents of ~/my_app/pages/page_2.py
import os

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import folium_static, st_folium
from utils import (
    create_heatmap,
    create_markercluster,
    fig_provinces,
    get_best_observers,
    get_last_species,
    get_num_species_by_city,
)

try:
    directory = f"{os.environ['DASHBOARDS']}/arsinoe"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


# variables
colors = ["#119239", "#562579", "#f4c812", "#f07d12", "#e61b1f", "#1e388d"]

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
        "select2d",  # Eliminar el botón de selección
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

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"

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

main_project = 186


# Cacheado de datos
@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


if __name__ == "__main__":
    # Columna izquierda
    st.sidebar.markdown("# Schools:")
    for school_id, school_name in schools.items():
        st.sidebar.markdown(
            f"* [{school_name}](https://minka-sdg.org/projects/{school_id})"
        )

    # Header
    with st.container():
        # Título
        col1, col2 = st.columns([1, 15])
        with col1:
            st.image(f"{directory}/images/ARSINOE.png")
        with col2:
            top_number = 7
            st.title(f"Top {top_number} schools in number of observations")

    with st.container():

        # Ranking de ciudades, métricas totales
        city_total_metrics = load_csv(f"{directory}/data/city_total_metrics.csv")

        fig1 = fig_provinces(
            top_number,
            city_total_metrics,
            "observations",
            "Number of observations",
            colors,
        )
        fig2 = fig_provinces(
            top_number,
            city_total_metrics,
            "species",
            "Number of different species",
            colors,
        )
        fig3 = fig_provinces(
            top_number, city_total_metrics, "observers", "Number of observers", colors
        )

        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
            csv4 = convert_df(city_total_metrics)

            st.download_button(
                label="Download data",
                data=csv4,
                file_name="city_total_metrics.csv",
                mime="text/csv",
            )
        with col2:
            st.plotly_chart(fig2, config=config_modebar, use_container_width=True)
        with col3:
            st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    i = 0
    ciutats = city_total_metrics["city"].to_list()[:top_number]
    for tab in st.tabs(
        # Se muestran las 5 con más observaciones
        ciutats
    ):
        with tab:
            # st.header(ciutats[i])
            school_id = next((k for k, v in schools.items() if v == ciutats[i]), None)
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown("**Last species uploaded:**")

                results = get_last_species(school_id, main_project)
                st.dataframe(
                    results[["taxon_name", "url", "image"]],
                    column_config={
                        "image": st.column_config.ImageColumn(
                            "Image (double click to enlarge)",
                            help="Preview",
                            width=200,
                        ),
                        "url": st.column_config.LinkColumn(
                            "url",
                            width=275,
                        ),
                    },
                    hide_index=True,
                )

            with col2:
                st.markdown("**Most observed species:**")
                df_species = get_num_species_by_city(school_id)
                df_species["taxon_name"] = (
                    f"https://minka-sdg.org/taxa/" + df_species["taxon_name"]
                )
                df_species.index = np.arange(1, len(df_species) + 1)
                st.data_editor(
                    df_species,
                    column_config={
                        "taxon_name": st.column_config.LinkColumn(
                            "nom", display_text=r"https://minka-sdg.org/taxa/(.*?)$"
                        ),
                        "observacions": st.column_config.NumberColumn(),
                    },
                    hide_index=False,
                    height=210,
                )

            with col3:
                st.markdown("**Participants with the most observations:**")
                df_observers = get_best_observers(school_id)
                df_observers["nom"] = (
                    f"https://minka-sdg.org/users/" + df_observers["nom"]
                )
                df_observers.index = np.arange(1, len(df_observers) + 1)
                st.dataframe(
                    df_observers,
                    column_config={
                        # "nom": st.column_config.TextColumn(width="medium"),
                        "nom": st.column_config.LinkColumn(
                            "name", display_text=r"https://minka-sdg.org/users/(.*?)$"
                        ),
                        "observations": st.column_config.NumberColumn(),
                    },
                    hide_index=False,
                    height=210,
                )

            with st.container():
                st.header(f"Observations by school: {ciutats[i]}")
                city_name = ciutats[i]
                df = load_csv(f"{directory}/data/obs_{school_id}.csv")

                map1, map2 = st.columns([10, 10], gap="small")

                # Definir el centro del mapa
                athens_center = [37.9795, 23.7162]

                # Usar claves únicas en session_state para cada ciudad
                heatmap_key = f"heatmap_city_{school_id}"
                markermap_key = f"markermap_city_{school_id}"

                # Guardar el mapa en session_state para evitar que desaparezca

                if heatmap_key not in st.session_state:
                    st.session_state[heatmap_key] = create_heatmap(
                        df, center=athens_center
                    )

                if markermap_key not in st.session_state:
                    st.session_state[markermap_key] = create_markercluster(
                        df, center=athens_center
                    )

                # Renderizar los mapas con _repr_html_()
                with map1:
                    map_html1 = st.session_state[heatmap_key]._repr_html_()
                    components.html(map_html1, height=600)

                with map2:
                    map_html2 = st.session_state[markermap_key]._repr_html_()
                    components.html(map_html2, height=600)

                # Convertir dataframe y agregar botón de descarga
                csv5 = convert_df(df)

                st.download_button(
                    label="Download data",
                    data=csv5,
                    file_name=f"observacions_{ciutats[i]}.csv",
                    mime="text/csv",
                )

            i += 1

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
