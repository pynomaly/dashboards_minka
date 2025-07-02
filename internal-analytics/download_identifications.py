import ast
import math
import os
import time

import pandas as pd
import requests

API_PATH = "https://api.minka-sdg.org/v1"
EXCLUDE_USERS = [
    "xasalva",
    "bertinhaco",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "irodero",
    "anomalia",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "verificador_1",
    "loreto_rodriguez",
    "minkatutor",
    "minkatest",
    "anonimousminkacontributor",
    "minkauser10",
    "test_minka_athens",
    "infominka",
    "admin",
]

session = requests.Session()


try:
    directory = f"{os.environ['DASHBOARDS']}/internal-analytics"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


def download_identifications():
    # Obtener el ID más alto disponible en MINKA
    batch_size = 10000
    page_max = 200
    df_identifications = pd.DataFrame()

    # Obtener el ID más alto disponible en la API
    url = f"{API_PATH}/identifications?own_observation=false&per_page=1"
    try:
        max_id = session.get(url).json()["results"][0]["id"]
        print(f"Max ID en la API: {max_id}")
    except Exception as e:
        print(f"Error al obtener el ID máximo: {str(e)}")
        return None

    print("Iniciando descarga...")

    for i in range(6, math.ceil(max_id / batch_size) + 2):
        print(f"Lote {i}...")
        for page in range(1, math.ceil(batch_size / page_max) + 1):
            url = f"{API_PATH}/identifications?own_observation=false&id_above={(i-1)*batch_size}&id_below={(i*batch_size) +1}&per_page={page_max}&page={page}"
            try:
                response = session.get(url).json()

                if "results" in response and response["results"]:
                    results = pd.json_normalize(response["results"])[
                        [
                            "id",
                            "user.id",
                            "user.login",
                            "created_at",
                            "taxon_id",
                            "taxon.ancestor_ids",
                            "observation.id",
                        ]
                    ]

                    # Filtrar usuarios excluidos
                    results = results[
                        ~results["user.login"].isin(EXCLUDE_USERS)
                    ].reset_index(drop=True)

                    if not results.empty:
                        df_identifications = pd.concat(
                            [df_identifications, results], ignore_index=True
                        )
                        print(f"Total registros: {len(df_identifications)}")
                else:
                    print(f"No hay más resultados en lote {i}, página {page}")
                    break  # Salir del bucle interno si no hay más datos

            except Exception as e:
                print(f"Error en lote {i}, página {page}: {str(e)}")
                time.sleep(
                    2
                )  # Pequeña pausa en caso de error para evitar bloqueos de API

    # Guardar el DataFrame en CSV
    file_path = f"{directory}/data/minka_identifications.csv"
    df_identifications.to_csv(file_path, index=False)
    print(f"Datos guardados en {file_path}")

    return df_identifications


# Identificadores
def get_identifiers():
    url = f"{API_PATH}/observations/identifiers"

    response = requests.get(url).json()

    total_identifiers = []

    for result in response["results"]:
        data = {}
        data["identifier_id"] = result["user_id"]
        data["identifier_name"] = result["user"]["login"]
        data["number_identifications"] = result["count"]
        data["created_at"] = result["user"]["created_at"]
        total_identifiers.append(data)

    df_identifiers = pd.DataFrame(total_identifiers)
    df_identifiers = df_identifiers.sort_values(
        by="number_identifications", ascending=False
    )
    df_identifiers["created_at"] = pd.to_datetime(df_identifiers["created_at"]).dt.date

    return df_identifiers[
        df_identifiers["identifier_name"].isin(EXCLUDE_USERS) == False
    ].reset_index(drop=True)


def get_last_identification(user_id, df_identifications):
    last_id = df_identifications.loc[
        df_identifications["user.id"] == user_id, "created_at"
    ].max()
    return last_id


def get_most_freq_taxon(user_id, column_name, df_identifications):
    df_identifications["kingdom"] = df_identifications["taxon.ancestor_ids"].apply(
        lambda x: x[0] if len(x) > 1 else None
    )
    df_identifications["phylum"] = df_identifications["taxon.ancestor_ids"].apply(
        lambda x: x[1] if len(x) > 1 else None
    )

    filtered_values = df_identifications.loc[
        df_identifications["user.id"] == user_id, column_name
    ].dropna()  # Elimina valores NaN
    most_freq = filtered_values.mode()
    taxon_id = most_freq.iloc[0] if not most_freq.empty else None
    if taxon_id is not None:
        url_taxon = f"https://minka-sdg.org/taxa/{int(taxon_id)}.json"
        taxon_name = session.get(url_taxon).json()["name"]
    else:
        taxon_name = None
    return taxon_name


if __name__ == "__main__":
    df_identifications = download_identifications()
    # df_identifications = pd.read_csv(f"{directory}/data/minka_identifications.csv")

    print("Get identifiers")
    df_identifiers = get_identifiers()

    print("Get last identification")
    df_identifiers["last_identification"] = df_identifiers["identifier_id"].apply(
        lambda x: get_last_identification(x, df_identifications)
    )
    df_identifiers["last_identification"] = pd.to_datetime(
        df_identifiers["last_identification"], utc=True
    )
    df_identifiers["last_identification"] = df_identifiers[
        "last_identification"
    ].dt.date

    print("Get most frequent taxons")
    df_identifications["taxon.ancestor_ids"] = df_identifications[
        "taxon.ancestor_ids"
    ].apply(ast.literal_eval)
    df_identifiers["most_kingdom"] = df_identifiers["identifier_id"].apply(
        lambda x: get_most_freq_taxon(x, "kingdom", df_identifications)
    )
    df_identifiers["most_phylum"] = df_identifiers["identifier_id"].apply(
        lambda x: get_most_freq_taxon(x, "phylum", df_identifications)
    )
    df_identifiers["most_taxon"] = df_identifiers["identifier_id"].apply(
        lambda x: get_most_freq_taxon(x, "taxon_id", df_identifications)
    )

    print("Save df_identifiers")
    df_identifiers.to_csv(f"{directory}/data/minka_identifiers.csv", index=False)
