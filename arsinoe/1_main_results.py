# Contents of ~/my_app/main_page.py
import os
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    directory = f"{os.environ['DASHBOARDS']}/arsinoe"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard ARSINOE",
)

import streamlit.components.v1 as components

# from streamlit.components.v1 import html
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    fig_bars_months,
    get_main_metrics,
    get_month_week_metrics,
)

# variables
colors = ["#119239", "#562579", "#f4c812", "#f07d12", "#e61b1f", "#1e388d"]

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

base_url = "https://minka-sdg.org"
api_path = f"https://api.minka-sdg.org/v1"


main_project = 186

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

matomo_script = """
"""


# Cacheado de datos
@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


def create_sidebar():
    st.sidebar.markdown("# ARSINOE")
    st.sidebar.markdown(
        """
    Recording Athens Biodiversity.

    URL: [ARSINOE project in MINKA](https://minka-sdg.org/projects/arsinoe_educational-community)
    """
    )


def create_header():
    with st.container():
        # Título
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(f"{directory}/images/ARSINOE.png")
        with col2:
            st.header("")


if __name__ == "__main__":

    # components.html(matomo_script, height=0, width=0)

    # Columna izquierda
    create_sidebar()

    # Header

    create_header()

    # Error si no responde la API

    total_obs, total_species, total_observers, total_identifiers = get_main_metrics(
        main_project
    )
    lw_obs, lw_spe, lw_part, lw_ident = get_month_week_metrics(main_project)

    with st.container():
        # Tarjetas de totales
        __, col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 1, 1])
        with col1:
            st.metric(
                ":camera_with_flash: Observations",
                f"{total_obs:,}".replace(",", " "),
                f"+{total_obs - lw_obs} last month",
            )
        with col2:
            st.metric(
                ":ladybug: Species",
                total_species,
                f"+{total_species - lw_spe} last month",
            )
        with col3:
            st.metric(
                ":eyes: Observers",
                total_observers,
                f"+{total_observers - lw_part} last month",
            )
        with col4:
            st.metric(
                ":books: Identifiers",
                total_identifiers,
                f"+{total_identifiers - lw_ident} last month",
            )
        style_metric_cards(
            background_color="#fff",
            # border_left_color="#C2C2C2",
            border_left_color=colors[1],
            box_shadow=False,
        )

    # Gráfico de columnas, acumulado mensual
    with st.container():
        df_cumulative_monthly = load_csv(
            f"{directory}/data/cumulative_city_monthly_metrics.csv"
        )
        df_cum_monthly_general = df_cumulative_monthly[
            df_cumulative_monthly.city == "ARSINOE"
        ].copy()
        df_cum_monthly_general["month"] = df_cum_monthly_general["month"].astype(str)
        df_cum_monthly_general.rename(
            columns={
                "city": "school",
                "month": "date",
                "total_obs": "observations",
                "total_spe": "species",
                "total_part": "observers",
                "total_ident": "identifiers",
            },
            inplace=True,
        )

        # Resultados mensuales desde junio 2022

        fecha_actual = datetime.now()
        end_date = fecha_actual.strftime("%Y-%m")
        start_date = "2023-10"

        cum_monthly_result = df_cum_monthly_general.reset_index(drop=True)

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "\tObservations\t",
                "\tSpecies\t",
                "\tObservers\t",
                "\tIdentifiers\t",
            ]
        )

        with tab1:
            fig1b = fig_bars_months(
                cum_monthly_result,
                field="observations",
                title="Cumulative observations by month",
                color=colors[0],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

        with tab2:
            fig2b = fig_bars_months(
                cum_monthly_result,
                field="species",
                title="Cumulative species by month",
                color=colors[1],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

        with tab3:
            fig3b = fig_bars_months(
                cum_monthly_result,
                field="observers",
                title="Cumulative observers by month",
                color=colors[2],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)

        with tab4:
            fig4b = fig_bars_months(
                cum_monthly_result,
                field="identifiers",
                title="Cumulative identifiers by month",
                color=colors[3],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig4b, config=config_modebar, use_container_width=True)

        csv2 = convert_df(cum_monthly_result)

        st.download_button(
            label="Download data",
            data=csv2,
            file_name="cum_monthly_result.csv",
            mime="text/csv",
        )

    # Gráfico de área, evolución por días
    with st.container():
        main_metrics = load_csv(f"{directory}/data/{main_project}_main_metrics.csv")

        tab5, tab6, tab7, tab8 = st.tabs(
            [
                "\tObservations\t",
                "\tSpecies\t",
                "\tObservers\t",
                "\tIdentifiers\t",
            ]
        )

        with tab5:
            fig1 = fig_area_evolution(
                df=main_metrics,
                field="observations",
                title="Evolution of the number of observations",
                color=colors[0],
                start_date=start_date,
                end_date=end_date,
            )

            st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

            csv1 = convert_df(main_metrics)

            st.download_button(
                label="Download data",
                data=csv1,
                file_name="main_metrics_by_day.csv",
                mime="text/csv",
            )

        with tab6:
            fig2 = fig_area_evolution(
                df=main_metrics,
                field="species",
                title="Evolution of the number of species",
                color=colors[1],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

        with tab7:
            fig3 = fig_area_evolution(
                df=main_metrics,
                field="observers",
                title="Evolution of the number of observers",
                color=colors[2],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

        with tab8:
            fig4 = fig_area_evolution(
                df=main_metrics,
                field="identifiers",
                title="Evolution of the number of identifiers",
                color=colors[3],
                start_date=start_date,
                end_date=end_date,
            )
            st.plotly_chart(fig4, config=config_modebar, use_container_width=True)

    st.divider()

    with st.container():
        st.header("Observations in Athens")
        df = load_csv(f"{directory}/data/{main_project}_obs.csv")
        athens_center = [37.9795, 23.7162]

        map1, map2 = st.columns([10, 10], gap="small")

        if "heatmap" not in st.session_state or st.session_state.heatmap is None:
            st.session_state.heatmap = create_heatmap(df, center=athens_center)

        if "markermap" not in st.session_state or st.session_state.markermap is None:
            st.session_state.markermap = create_markercluster(df, center=athens_center)
        with map1:
            map_html1 = st.session_state.heatmap._repr_html_()
            components.html(map_html1, height=600)
        with map2:
            map_html2 = st.session_state.markermap._repr_html_()
            components.html(map_html2, height=600)

        csv3 = convert_df(df)

        st.download_button(
            label="Download data",
            data=csv3,
            file_name="observations_arsinoe.csv",
            mime="text/csv",
        )

    st.container(height=50, border=False)

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
