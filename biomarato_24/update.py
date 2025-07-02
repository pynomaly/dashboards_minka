#!/usr/bin/env python3

import datetime
import math
import os
import time
from typing import List, Optional

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"

main_project = 283
all_projects = [280, 281, 282, 283]

# main_project = 124
# all_projects = [121, 122, 123, 124]

try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_24"
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
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
    "anomalia",
    "amaliacardenas",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "monyant",
    "ura4dive",
    "lauracoro",
    "pirotte_",
    "oceanicos",
    "abril",
    "alba_barrera",
    "amb_platges",
    "daniel_palacios",
    "davidpiquer",
    "laiamanyer",
    "rogerpuig",
    "guillemdavila",
    # vanessa,
    # teresa,
]


def update_main_metrics(proj_id: int) -> pd.DataFrame:
    """
    Actualiza el df de las 3 métricas para cada día de la competición.
    Devuelve 0 para los días que no han llegado.
    """
    results = []
    observations = f"{API_PATH}/observations?"
    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"

    # Crear una sesión de requests
    session = requests.Session()

    # Fecha de inicio de la Biomarato: 2024/05/06 - 2024/10/15
    day = datetime.date(year=2024, month=5, day=6)
    rango_temporal = (datetime.date(year=2024, month=10, day=16) - day).days

    for i in range(rango_temporal):
        print(i)
        if datetime.datetime.today().date() >= day:
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
        # Para el resto devuelve 0
        else:
            result = {
                "date": day.strftime("%Y-%m-%d"),
                "observations": 0,
                "species": 0,
                "participants": 0,
            }

        results.append(result)
        day = day + datetime.timedelta(days=1)

    result_df = pd.DataFrame(results)
    print("Updated main metrics")
    return result_df


def get_list_users(id_project):
    users = []
    session = requests.Session()

    url1 = f"https://api.minka-sdg.org/v1/observations/observers?project_id={id_project}&quality_grade=research"
    results = session.get(url1).json()["results"]
    for result in results:
        datos = {}
        datos["user_id"] = result["user_id"]
        datos["participant"] = result["user"]["login"]
        datos["observacions"] = result["observation_count"]
        datos["espècies"] = result["species_count"]
        users.append(datos)
    df_users = pd.DataFrame(users)

    identifiers = []
    url = f"https://api.minka-sdg.org/v1/observations/identifiers?project_id={id_project}&quality_grade=research"
    results = session.get(url).json()["results"]
    for result in results:
        datos = {}
        datos["user_id"] = result["user_id"]
        datos["identificacions"] = result["count"]
        identifiers.append(datos)
    df_identifiers = pd.DataFrame(identifiers)

    df_users = pd.merge(df_users, df_identifiers, how="left", on="user_id")
    df_users.fillna(0, inplace=True)

    return df_users[["participant", "observacions", "espècies", "identificacions"]]


# update obs for projects
def get_new_data(project, grade=None):
    df_obs = pd.read_csv(f"{directory}/data/{project}_df_obs.csv")
    df_photos = pd.read_csv(f"{directory}/data/{project}_df_photos.csv")
    max_id = df_obs["id"].max()

    # Comprueba si hay observaciones nuevas
    obs = get_obs(id_project=project, id_above=max_id, grade=grade)
    if len(obs) > 0:
        print(f"Add {len(obs)} obs in project {project}")
        df_obs2, df_photos2 = get_dfs(obs)
        df_obs = pd.concat([df_obs, df_obs2], ignore_index=True)
        df_obs.to_csv(f"{directory}/data/{project}_df_obs.csv", index=False)
        df_photos = pd.concat([df_photos, df_photos2], ignore_index=True)
        df_photos.to_csv(f"{directory}/data/{project}_df_photos.csv", index=False)


def update_dfs_projects(
    project,
    day=(datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    grade=None,
):

    # updated today
    obs_nuevas = get_obs(id_project=project, updated_since=day, grade=grade)
    if len(obs_nuevas) > 0:
        df_obs_new, df_photos_new = get_dfs(obs_nuevas)
        df_photos_new["photos_id"] = df_photos_new["photos_id"].astype(int)

        # get downloaded
        df_obs = pd.read_csv(f"{directory}/data/{project}_df_obs.csv")
        df_photos = pd.read_csv(f"{directory}/data/{project}_df_photos.csv")
        old_obs = df_obs[-df_obs["id"].isin(df_obs_new["id"].to_list())]
        old_photos = df_photos[
            -df_photos["photos_id"].isin(df_photos_new["photos_id"].to_list())
        ]

        # join old and updated
        df_obs_updated = pd.concat(
            [old_obs, df_obs_new], ignore_index=True
        ).sort_values(by="id", ascending=False)
        df_photo_updated = pd.concat(
            [old_photos, df_photos_new], ignore_index=True
        ).sort_values(by="photos_id", ascending=False)
    else:
        df_obs_updated = None
        df_photo_updated = None
    # remove casuals
    obs_casual = get_obs(grade="casual", updated_since=day)
    if len(obs_casual) > 0:
        casual_ids = [ob_casual.id for ob_casual in obs_casual]
        df_obs_updated = df_obs_updated[-df_obs_updated["id"].isin(casual_ids)]
        df_photo_updated = df_photo_updated[-df_photo_updated["id"].isin(casual_ids)]

    print(f"Updated obs and photos for project {project}: {len(df_obs_updated)}")
    return df_obs_updated, df_photo_updated


def get_ranking_users(proj_id, grade=None):
    get_new_data(proj_id, grade)
    update_dfs_projects(proj_id, grade=grade)
    df_obs = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
    df_photos = pd.read_csv(f"{directory}/data/{proj_id}_df_photos.csv")

    if len(df_obs) == 0:
        df_obs = None
        df_photos = None

    # Sacamos pt_users
    if df_obs is not None:
        pt_users = get_list_users(proj_id)

    else:
        pt_users = None

    return df_obs, df_photos, pt_users


def get_list_species(proj_id: int) -> Optional[pd.DataFrame]:
    session = requests.Session()
    params = {"project_id": proj_id, "quality_grade": "research"}
    url = f"{API_PATH}/observations/species_counts"
    results = []

    # Extrae todas las páginas de los resultados, si hay más de una
    total_results = session.get(url, params=params).json()["total_results"]
    if total_results > 500:
        num = math.ceil(total_results / 500)
        for i in range(1, num + 1):
            params["page"] = i
            results.extend(session.get(url, params=params).json()["results"])
    else:
        results = session.get(url, params=params).json()["results"]

    # Crea la tabla name-count de especies
    if len(results) > 0:
        total = []

        for result in results:
            species_count = {
                "name": result["taxon"]["name"],
                "count": result["count"],
                "id": result["taxon"]["id"],
            }
            total.append(species_count)
        species_count = pd.DataFrame(total)
    else:
        species_count = None

    return species_count


def get_first_obs_taxon(taxon_id, proj_id, session=None):
    if session is None:
        session = requests.Session()

    url = f"{API_PATH}/observations"
    params = {"project_id": proj_id, "quality_grade": "research", "taxon_id": taxon_id}

    results = session.get(url, params=params).json()["results"]

    if not results:
        return [None, None, None, None]

    primera_observacion = results[-1]

    date = primera_observacion["observed_on"]
    author = primera_observacion["user"]["login"]
    obs_id = primera_observacion["id"]

    results_photos = session.get(url, params={"id": obs_id}).json()["results"]
    try:
        photo_url = results_photos[0]["photos"][0]["url"].replace("/square", "/large")
    except:
        photo_url = None

    return [date, author, obs_id, photo_url]


def get_first_obs_taxon_original(taxon_id, proj_id):

    session = requests.Session()

    url = f"{API_PATH}/observations"

    params = {"project_id": proj_id, "quality_grade": "research", "taxon_id": taxon_id}

    results = session.get(url, params=params).json()["results"]

    primera_observacion = results[-1]

    date = primera_observacion["observed_on"]
    author = primera_observacion["user"]["login"]
    obs_id = primera_observacion["id"]

    results_photos = session.get(url, params={"id": obs_id}).json()["results"]
    try:
        photo_url = results_photos[0]["photos"][0]["url"].replace("/square", "/large")
    except:
        photo_url = None

    return [date, author, obs_id, photo_url]


if __name__ == "__main__":
    # Get main_metrics.csv
    start_time = time.time()

    main_metrics_df = update_main_metrics(main_project)
    main_metrics_df.to_csv(f"{directory}/data/main_metrics.csv", index=False)
    print("Main metrics actualizada")

    # Update df de cada proyecto
    for proj_id in all_projects:
        print("Update df:", proj_id)
        obs = get_obs(id_project=proj_id, grade="research")
        df_obs, df_photos = get_dfs(obs)
        pt_users = get_list_users(proj_id)
        # df_obs, df_photos, pt_users = get_ranking_users(proj_id, grade="research")
        try:
            df_obs.to_csv(f"{directory}/data/{proj_id}_df_obs.csv", index=False)
            print(f"df_obs_{proj_id}.csv updated")
        except:
            print("No se ha actualizado los df_obs")
            pass
        try:
            df_photos.to_csv(f"{directory}/data/{proj_id}_df_photos.csv", index=False)
            print(f"df_photos_{proj_id}.csv updated")
        except:
            print("No se han actualizado los df_photos")
            pass
        try:
            pt_users.to_csv(f"{directory}/data/{proj_id}_pt_users.csv", index=False)
            print(f"pt_users_{proj_id}.csv updated")
        except:
            print("No se han actualizado los pt_users")
            pass

    # Get listado de species
    for proj_id in all_projects:
        print(f"Get species for project {proj_id}")
        species = get_list_species(proj_id)
        if species is not None:
            with requests.Session() as session:
                species[["first_date", "author", "obs_id", "photo_url"]] = (
                    species.apply(
                        lambda x: get_first_obs_taxon(x["id"], proj_id, session), axis=1
                    ).to_list()
                )
            species = species[species.author != "xasalva"]
            species = species.sort_values(
                by=["first_date", "obs_id"], ascending=False
            ).reset_index(drop=True)
            species.to_csv(f"{directory}/data/{proj_id}_species.csv", index=False)
            print(f"Species updated for {proj_id}")

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
