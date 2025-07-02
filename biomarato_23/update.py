#!/usr/bin/env python3

import datetime
import math
import os

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"

try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_23"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


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


def update_main_metrics(proj_id):
    results = []
    observations = f"{API_PATH}/observations?"
    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"

    # Crear una sesión de requests
    session = requests.Session()

    # Fecha de inicio de la Biomarato
    day = datetime.date(year=2023, month=4, day=28)
    rango_temporal = (datetime.date(year=2023, month=10, day=16) - day).days

    for i in range(rango_temporal):
        print(i)
        st_day = day.strftime("%Y-%m-%d")

        params = {
            "project_id": proj_id,
            "created_d2": st_day,
            "order": "desc",
            "order_by": "created_at",
        }

        # Utilizar la sesión para realizar las solicitudes
        total_species = session.get(species, params=params).json()["total_results"]
        total_participants = session.get(observers, params=params).json()[
            "total_results"
        ]
        total_obs = session.get(observations, params=params).json()["total_results"]

        result = {
            "date": st_day,
            "observations": total_obs,
            "species": total_species,
            "participants": total_participants,
        }

        results.append(result)

        day = day + datetime.timedelta(days=1)

    result_df = pd.DataFrame(results)
    print("Updated main metrics")
    return result_df


def update_main_metrics_original():
    proj_id = 124
    results = []
    observations = f"{API_PATH}/observations?"
    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"
    # Fecha de inicio de la Biomarato
    day = datetime.date(year=2023, month=4, day=28)
    rango_temporal = (datetime.date.today() - day).days

    for i in range(rango_temporal):
        st_day = day.strftime("%Y-%m-%d")

        params = {
            "project_id": proj_id,
            "created_d2": st_day,
            "order": "desc",
            "order_by": "created_at",
        }
        total_species = requests.get(species, params=params).json()["total_results"]
        total_participants = requests.get(observers, params=params).json()[
            "total_results"
        ]
        total_obs = requests.get(observations, params=params).json()["total_results"]

        result = {
            "date": st_day,
            "observations": total_obs,
            "species": total_species,
            "participants": total_participants,
        }

        results.append(result)

        day = day + datetime.timedelta(days=1)

    result_df = pd.DataFrame(results)
    print("Updated main metrics")
    return result_df


def _get_species(user_name, proj_id):
    species = f"{API_PATH}/observations/species_counts"
    params = {"project_id": proj_id, "user_login": user_name}
    return requests.get(species, params=params).json()["total_results"]


def get_ranking_users(proj_id, max_id=300000, batch_size=10000):
    total_obs = []
    for limit in range(1, int(max_id / 10000)):
        obs = get_obs(
            id_above=(limit - 1) * batch_size,
            id_below=limit * batch_size,
            id_project=proj_id,
            grade="research",
        )
        total_obs.extend(obs)

    df_obs, df_photos = get_dfs(total_obs)
    df_obs = df_obs.drop_duplicates()
    df_photos = df_photos.drop_duplicates()

    pt_users = (
        df_obs["user_login"]
        .value_counts()
        .to_frame()
        .reset_index(drop=False)
        .rename(columns={"user_login": "participant", "count": "observacions"})
    )
    pt_users = pt_users[-pt_users["participant"].isin(exclude_users)].reset_index(
        drop=True
    )
    # pt_users.index = range(pt_users.index.start + 1, pt_users.index.stop + 1)
    pt_users["espècies"] = pt_users["participant"].apply(
        lambda x: _get_species(x, proj_id)
    )
    return df_obs, df_photos, pt_users


def get_list_species(proj_id):
    params = {"project_id": proj_id, "quality_grade": "research"}
    url = f"{API_PATH}/observations/species_counts"
    results = []

    # Extrae todas las páginas de los resultados, si hay más de una
    total_results = requests.get(url, params=params).json()["total_results"]
    if total_results > 500:
        num = math.ceil(total_results / 500)
        for i in range(1, num + 1):
            params["page"] = i
            results.extend(requests.get(url, params=params).json()["results"])
    else:
        results = requests.get(url, params=params).json()["results"]

    # Crea la tabla name-count de especies
    total = []

    for result in results:
        species_count = {
            "name": result["taxon"]["name"],
            "count": result["count"],
            "id": result["taxon"]["id"],
        }
        total.append(species_count)
    species_count = pd.DataFrame(total)

    return species_count


def get_date_taxon(taxon_id):
    first = get_obs(id_project=proj_id, taxon_id=taxon_id)[-1]
    date = first.observed_on.strftime("%Y-%m-%d")
    author = first.user_login
    obs_id = first.id
    photo_url = first.photos[0].large_url
    return [date, author, obs_id, photo_url]


if __name__ == "__main__":
    # Get main_metrics.csv
    main_metrics_df = update_main_metrics(124)
    print("Main metrics actualizada")
    main_metrics_df.to_csv(f"{directory}/data/main_metrics.csv", index=False)

    # Update df de cada proyecto
    for proj_id in [121, 122, 123, 124]:
        df_obs, df_photos, pt_users = get_ranking_users(proj_id)
        df_obs.to_csv(f"{directory}/data/{proj_id}_df_obs.csv", index=False)
        print(f"df_obs_{proj_id}.csv updated")
        df_photos.to_csv(f"{directory}/data/{proj_id}_df_photos.csv", index=False)
        print(f"df_photos_{proj_id}.csv updated")
        pt_users.to_csv(f"{directory}/data/{proj_id}_pt_users.csv", index=False)
        print(f"pt_users_{proj_id}.csv updated")

    # Get listado de species
    for proj_id in [121, 122, 123, 124]:
        species = get_list_species(proj_id)
        species[["first_date", "author", "obs_id", "photo_url"]] = (
            species["id"].apply(get_date_taxon).to_list()
        )
        species = species[species.author != "xasalva"]
        species = species.sort_values(
            by=["first_date", "obs_id"], ascending=False
        ).reset_index(drop=True)
        species.to_csv(f"{directory}/data/{proj_id}_species.csv", index=False)
