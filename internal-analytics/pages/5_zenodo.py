import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

try:
    directory = f"{os.environ['DASHBOARDS']}/internal-analytics"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Internal KPIs MINKA",
)


# funciones
def get_zenodo_stats():
    url = "https://zenodo.org/api/records"
    params = {
        "q": "communities:embimos",
        "size": 100,  # Número máximo de resultados por página
        "page": 1,  # Comenzar desde la página 1
    }

    records = []

    while True:
        response = requests.get(url, params=params)
        data = response.json()

        if "hits" not in data or "hits" not in data["hits"]:
            print("No se encontraron resultados.")
            break

        # Extraer los datos y agregarlos a la lista
        for record in data["hits"]["hits"]:
            records.append(
                {
                    "id": record["id"],
                    "created": record["created"].split("T")[0],
                    "title": record["metadata"]["title"],
                    "url": record["doi_url"],
                    "views": record["stats"]["unique_views"],
                    "downloads": record["stats"]["unique_downloads"],
                }
            )

        # Verificar si hay más páginas
        if params["page"] * params["size"] >= data["hits"]["total"]:
            break  # Si ya hemos obtenido todos los registros, salir del bucle

        params["page"] += 1  # Pasar a la siguiente página

    # Convertir la lista en un DataFrame
    df_zenodo = pd.DataFrame(records)

    # Mostrar los primeros registros
    df_zenodo.sort_values(by="downloads", ascending=False, inplace=True)

    return df_zenodo


if __name__ == "__main__":
    if "df_zenodo" not in st.session_state or st.session_state.df_zenodo is None:
        st.session_state.df_zenodo = get_zenodo_stats()

    st.title("Stats of Zenodo publications in EMBIMOS community")
    st.markdown("**Number of resources:** " + str(len(st.session_state.df_zenodo)))
    col1, col2 = st.columns([1, 3])
    with col1:
        search = st.text_input("Search in title", "")
        df_filtered = st.session_state.df_zenodo[
            st.session_state.df_zenodo["title"].str.contains(search, case=False)
        ]

    st.dataframe(
        df_filtered,
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("url"),
            "id": st.column_config.TextColumn("id"),
        },
        height=600,
    )
