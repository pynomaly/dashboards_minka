import os

import pandas as pd
import streamlit as st
from utils import fig_cols, get_count_by_hour, get_count_per_day

st.set_page_config(layout="wide")

# variables
colors = ["#4aae79", "#00a3b4", "#265769"]

try:
    directory = f"{os.environ['DASHBOARDS']}/biodiverciutat_24"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

api_path = "https://api.minka-sdg.org/v1"

main_project = 233

projects = {
    79: "Begues",
    80: "Viladecans",
    81: "Sant Climent de Llobregat",
    83: "Cervelló",
    85: "Sant Boi de Llobregat",
    86: "Santa Coloma de Cervelló",
    87: "Sant Vicenç dels Horts",
    88: "la Palma de Cervelló",
    89: "Corbera de Llobregat",
    91: "Sant Andreu de la Barca",
    92: "Castellbisbal",
    93: "el Papiol",
    94: "Molins de Rei",
    95: "Sant Feliu de Llobregat",
    97: "Cornellà de Llobregat",
    98: "l'Hospitalet de Llobregat",
    99: "Esplugues de Llobregat",
    100: "Sant Just Desvern",
    101: "Sant Cugat del Vallès",
    102: "Barberà del Vallès",
    103: "Ripollet",
    104: "Montcada i Reixac",
    106: "Sant Adrià de Besòs",
    107: "Badalona",
    108: "Tiana",
    109: "Montgat",
    224: "Barcelona",
    225: "el Prat de Llobregat",
    226: "Pallejà",
    227: "Torrelles de Llobregat",
    228: "Castelldefels",
    229: "Gavà",
    230: "Sant Joan Despí",
    231: "Santa Coloma de Gramenet",
    232: "Àrea marina Barcelona",
}

exclude_users = [
    "xasalva",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "uri_domingo",
    "mimo_fecdas",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
]


# Columna izquierda
st.sidebar.markdown("# Com s’hi pot participar?")
st.sidebar.markdown(
    """
Qualsevol persona amb interès en la natura pot unir-se al repte. A través de la plataforma MINKA es poden pujar les observacions de flora i fauna, de qualsevol ecosistema urbà, en aquest cas de Barcelona i de tots els municipis metropolitans (boscos de Collserola, parcs, jardins, rius, aiguamolls, dunes, platges i mar).

Totes les observacions del perímetre dels municipis metropolitans que entrin a MINKA, del 26 d’abril a les 00:01 h al 29 d’abril a les 23:59 h formaran part de l’esdeveniment.
"""
)

# Ranking de participantes por obs, identificaciones y especies
try:
    users = pd.read_csv(f"{directory}/data/{main_project}_users.csv")
    users = users[-users.participant.isin(exclude_users)].reset_index(drop=True)
    users["link"] = "https://minka-sdg.org/users/" + users["participant"]
    users.drop(columns="participant", inplace=True)
    users = users[["link", "observacions", "identificacions", "espècies"]]
    users.index += 1

    # Cabecera
    with st.container():
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(
                f"{directory}/images/LOGO OFICIAL_biodiverciutat_marca_rgbpositiu.png"
            )
        with col2:
            st.header(":green[BioDiverCiutat 2024]")
            st.markdown(":green[26 - 29 d'abril de 2024]")

    with st.container():
        st.markdown("## Usuaris per nombre d'observacions, identificacions i espècies")
        st.data_editor(
            users,
            column_config={
                "link": st.column_config.LinkColumn(
                    "Nom d'usuari",
                    validate="^https://minka-sdg\.org/users/[a-z]+$",
                    display_text=r"https://minka-sdg\.org/users/([^/]+)",
                    width="medium",
                ),
                "observacions": st.column_config.NumberColumn(width=100),
                "identificacions": st.column_config.NumberColumn(width=100),
                "espècies": st.column_config.NumberColumn(width=100),
            },
            hide_index=False,
            disabled=True,
            # height=590,
        )
except FileNotFoundError:
    pass
st.divider()


# observaciones por día de la semana y hora del día
st.header("Distribució de participants per hora i dia")

try:
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
    counts_per_day = get_count_per_day(df_obs, mode="users")
    counts_per_hour = get_count_by_hour(df_obs, mode="users")

    fig_count_per_day = fig_cols(
        counts_per_day,
        x_field="day_of_week",
        y_field="count",
        title="Nombre de participants per dia del BioDiverCiutat",
        color_field="count",
    )

    fig_count_per_hour = fig_cols(
        counts_per_hour,
        x_field="hour_of_day",
        y_field="count",
        title="Nombre de participants per hora del dia",
        color_field="count",
    )

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.plotly_chart(fig_count_per_day, use_container_width=True)
    with col2:
        st.plotly_chart(fig_count_per_hour, use_container_width=True)
except FileNotFoundError:
    pass
