import os

import config
import pandas as pd
import streamlit as st
from utils import fig_cols, get_count_by_hour, get_count_per_day

# variables

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

exclude_users = []


# Columna izquierda
st.sidebar.markdown("# Com s’hi pot participar?")
st.sidebar.markdown(
    f"""
Qualsevol persona amb interès en la natura pot unir-se al repte. A través de la plataforma MINKA es poden pujar les observacions de flora i fauna, de qualsevol ecosistema urbà, en aquest cas de Barcelona i de tots els municipis metropolitans (boscos de Collserola, parcs, jardins, rius, aiguamolls, dunes, platges i mar).

Totes les observacions del perímetre dels municipis metropolitans que entrin a MINKA, del {config.PROJ_DATES} formaran part de l’esdeveniment.
"""
)

# Ranking de participantes por obs, identificaciones y especies

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

with st.container():
    st.markdown("## Usuaris per nombre d'observacions, identificacions i espècies")
    users_path = f"{directory}/data/{config.MAIN_PROJ}_users.csv"
    if not os.path.exists(users_path):
        st.warning("Cap dada disponible")
    else:
        users = pd.read_csv(users_path)
        users = users[-users.participant.isin(exclude_users)].reset_index(drop=True)
        users["link"] = "https://minka-sdg.org/users/" + users["participant"]
        users.drop(columns="participant", inplace=True)
        users = users[["link", "observacions", "identificacions", "espècies"]]
        users.index += 1

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
        )
st.divider()


# observaciones por día de la semana y hora del día
st.header("Distribució de participants per hora i dia")

obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
if not os.path.exists(obs_path):
    st.warning("Cap dada disponible")
else:
    df_obs = pd.read_csv(obs_path)
    counts_per_day = get_count_per_day(df_obs, mode="users")
    counts_per_hour = get_count_by_hour(df_obs, mode="users")

    fig_count_per_day = fig_cols(
        counts_per_day,
        x_field="day_of_week",
        y_field="count",
        title="Nombre de participants per dia",
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
