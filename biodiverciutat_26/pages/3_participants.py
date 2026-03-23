import os

import config
import pandas as pd
import streamlit as st
from utils import fig_cols, get_count_by_hour, get_count_per_day

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

from i18n import init_i18n, t

# Initialize i18n
init_i18n(current_page="participants")

exclude_users = []


@st.cache_data(ttl=300, show_spinner=False)
def load_users(path, exclude_list):
    """Cache users CSV loading and transformation"""
    users = pd.read_csv(path)
    users = users[~users.participant.isin(exclude_list)].reset_index(drop=True)
    users["link"] = "https://minka-sdg.org/users/" + users["participant"]
    users.drop(columns="participant", inplace=True)
    users = users[["link", "observacions", "identificacions", "espècies"]]
    users.index += 1
    return users


@st.cache_data(ttl=300, show_spinner=False)
def load_observations(path):
    """Cache observations CSV"""
    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_counts(_df_obs, mode):
    """Cache count calculations"""
    counts_per_day = get_count_per_day(_df_obs, mode=mode)
    counts_per_hour = get_count_by_hour(_df_obs, mode=mode)
    return counts_per_day, counts_per_hour

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.participants_title')} - {config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

with st.container():
    st.markdown(f"## {t('participants_page.users_by_observations')}")
    users_path = f"{directory}/data/{config.MAIN_PROJ}_users.csv"
    if not os.path.exists(users_path):
        st.warning(t("ui.no_data"))
    else:
        users = load_users(users_path, tuple(exclude_users))

        st.data_editor(
            users,
            column_config={
                "link": st.column_config.LinkColumn(
                    t("participants_page.username"),
                    validate="^https://minka-sdg\.org/users/[a-z]+$",
                    display_text=r"https://minka-sdg\.org/users/([^/]+)",
                    width="medium",
                ),
                "observacions": st.column_config.NumberColumn(
                    t("metrics.observations"), width=100
                ),
                "identificacions": st.column_config.NumberColumn(width=100),
                "espècies": st.column_config.NumberColumn(
                    t("metrics.species"), width=100
                ),
            },
            hide_index=False,
            disabled=True,
        )
st.divider()


# Distribución por hora y día
st.header(t("participants_page.distribution_by_hour_day"))

obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
if not os.path.exists(obs_path):
    st.warning(t("ui.no_data"))
else:
    df_obs = load_observations(obs_path)
    counts_per_day, counts_per_hour = get_cached_counts(df_obs, mode="users")

    fig_count_per_day = fig_cols(
        counts_per_day,
        x_field="day_of_week",
        y_field="count",
        title=t("participants_page.participants_per_day"),
        color_field="count",
    )

    fig_count_per_hour = fig_cols(
        counts_per_hour,
        x_field="hour_of_day",
        y_field="count",
        title=t("participants_page.participants_per_hour"),
        color_field="count",
    )

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.plotly_chart(fig_count_per_day, use_container_width=True)

    with col2:
        st.plotly_chart(fig_count_per_hour, use_container_width=True)
