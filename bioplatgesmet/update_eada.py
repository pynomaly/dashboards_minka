import argparse
import math
import os

import pandas as pd
import requests

try:
    DIRECTORY = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

API_PATH = "https://api.minka-sdg.org/v1"
CODE_IN_EMAIL = "eada.edu"
PROJECT_ID = 264

taxon_groups = {
    12: "Plants",
    8: "Mammalia",
    5: "Aves",
    15: "Mollusca",
    3: "Actinopterygii",
    11: "Insecta",
    325: "Lepidoptera",  # Está en insecta
    326: "Hymenoptera",  # Está en insecta
    9: "Arachnida",
    6: "Reptilia",
    13: "Fungi",
}
session = requests.Session()

# Change every day
user_file = "get_user_list.csv"


# functions
def get_info_users(user_id, session=session) -> dict:
    user_url = f"{API_PATH}/users/{user_id}"
    try:
        response = session.get(user_url)

        if response.status_code != 200:
            return None

        json_data = response.json()

        if "results" not in json_data or not json_data["results"]:
            empty_count += 1  # Incrementar si el usuario no existe
        else:
            data = {
                "created_at": json_data["results"][0]["created_at"],
                "observations_count": json_data["results"][0]["observations_count"],
                "identifications_count": json_data["results"][0][
                    "identifications_count"
                ],
                "species_count": json_data["results"][0]["species_count"],
            }
            return data

    except requests.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return None


def get_user_info_in_project(user_id, proj_id=PROJECT_ID, session=session):
    url = f"https://api.minka-sdg.org/v1/observations/observers?project_id={proj_id}&user_id={user_id}"

    response = session.get(url).json()
    if len(response["results"]) > 0:
        results = {
            "observations_proj": response["results"][0]["observation_count"],
            # las identificaciones no pueden ser de un proyecto solo
            # "identifications": response['results'][0]['user']['identifications_count'],
            "species_proj": response["results"][0]["species_count"],
        }

    else:
        results = {"observations_proj": 0, "species_proj": 0}
    return results


def get_identifications_by_user(project_id) -> dict:
    url = (
        f"https://api.minka-sdg.org/v1/observations/identifiers?project_id={project_id}"
    )
    results = requests.get(url).json()["results"]
    dict_identifications = {}
    for result in results:
        dict_identifications[result["user_id"]] = result["count"]
    return dict_identifications


def get_taxon_group_by_user(user_id, taxon_groups=taxon_groups, session=session):
    observations = {}
    for k, v in taxon_groups.items():
        url = f"https://api.minka-sdg.org/v1/observations?project_id={PROJECT_ID}&taxon_id={k}&user_id={user_id}"
        try:
            observations[v] = session.get(url).json()["total_results"]
        except:
            observations[v] = 0
    return observations


def get_research_obs_in_project(user_id, proj_id=PROJECT_ID, session=session):

    url = f"https://api.minka-sdg.org/v1/observations/observers?project_id={proj_id}&user_id={user_id}&quality_grade=research"

    response = session.get(url).json()
    if len(response["results"]) > 0:
        research_obs = response["results"][0]["observation_count"]
        print(research_obs)
    else:
        research_obs = 0
    return research_obs


def fetch_observations(user_ids: list[int], proj_id, per_page: int = 200) -> list:
    results = []

    with requests.Session() as session:
        for user_id in user_ids:
            params = {
                "user_id": user_id,
                "project_id": proj_id,
                "order": "desc",
                "order_by": "created_at",
                "per_page": per_page,
            }

            # Primera página
            response = session.get(
                "https://api.minka-sdg.org/v1/observations", params=params
            )
            response.raise_for_status()
            data = response.json()
            results.extend(data["results"])

            # Páginas restantes
            total_pages = math.ceil(data["total_results"] / per_page)
            for page in range(2, total_pages + 1):
                response = session.get(
                    "https://api.minka-sdg.org/v1/observations",
                    params={**params, "page": page},
                )
                response.raise_for_status()
                results.extend(response.json()["results"])

    return results


def save_df_observations(results, file_path):
    df_results = pd.json_normalize(results)
    df_results = df_results.drop(
        columns=[
            "uuid",
            "site_id",
            "created_time_zone",
            "quality_metrics",
            "flags",
            "project_ids_with_curator_id",
            "outlinks",
            "ofvs",
            "map_scale",
            "project_ids",
            "owners_identification_from_vision",
            "spam",
            "project_ids_without_curator_id",
            "faves",
            "created_at_details.date",
            "created_at_details.week",
            "created_at_details.month",
            "created_at_details.hour",
            "created_at_details.year",
            "created_at_details.day",
            "taxon.photos_locked",
            "taxon.wikipedia_url",
            "taxon.universal_search_rank",
            "taxon.created_at",
            "taxon.taxon_changes_count",
            "taxon.flag_counts.resolved",
            "taxon.flag_counts.unresolved",
            "taxon.atlas_id",
            "taxon.default_photo.id",
            "taxon.default_photo.license_code",
            "taxon.default_photo.attribution",
            "taxon.default_photo.url",
            "taxon.default_photo.original_dimensions.height",
            "taxon.default_photo.original_dimensions.width",
            "taxon.default_photo.flags",
            "taxon.default_photo.square_url",
            "taxon.default_photo.medium_url",
            "user.site_id",
            "user.created_at",
            "user.spam",
            "user.suspended",
            "user.login_autocomplete",
            "user.login_exact",
            "user.name",
            "user.name_autocomplete",
            "user.orcid",
            "user.icon",
            "user.observations_count",
            "user.identifications_count",
            "user.journal_posts_count",
            "user.activity_count",
            "user.species_count",
            "user.universal_search_rank",
            "user.roles",
            "user.icon_url",
            "taxon",
            "taxon.default_photo",
        ]
    )
    df_results.to_parquet(file_path)
    return df_results


def get_taxonomy(identifications):
    if len(identifications) == 0:
        return {}
    current = [i for i in identifications if i.get("current")]
    ids = current[-1] if current else identifications[-1]
    ancestors = ids.get("taxon", {}).get("ancestors", [])
    return {a["rank"]: a["name"] for a in ancestors}


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Update EADA data from Minka API")
    parser.add_argument(
        "--mode",
        choices=["update_users", "test", "default"],
        default="default",
        help="Execution mode: 'update_users' to filter by email, 'test' for test users, 'default' to skip user update",
    )
    args = parser.parse_args()

    try:
        df_users = pd.read_csv(f"data/eada/{user_file}", sep=";")

    except:
        print(f"No file found {user_file}. Exiting without creating files.")
        exit(0)

    # Eliminamos última fila, que incluye los totales
    df_users = df_users[:-1]

    # seleccionamos estudiantes
    if args.mode == "update_users":
        df_accounts = df_users.loc[
            df_users["email"].str.contains(CODE_IN_EMAIL), ["id", "login"]
        ].reset_index(drop=True)

        # Check if there are users that meet the condition
        if len(df_accounts) == 0:
            print(
                f"No users found with email containing '{CODE_IN_EMAIL}'. Exiting without creating files."
            )
            exit(0)

        df_accounts.columns = ["user_id", "user_name"]

        # Dejamos las columnas útiles, eliminamos los emails por privacidad
        df_accounts[["user_id", "user_name"]].to_csv(
            "data/eada/get_user_list.csv", index=False
        )

    elif args.mode == "test":
        # Para pruebas
        df_accounts = df_users.loc[
            df_users["login"].isin(
                [
                    "xasalva",
                    "jaume-piera",
                    "carlosrodero",
                    "mediambient_ajelprat",
                    "bertinhaco",
                ]
            ),
            ["id", "login"],
        ].reset_index(drop=True)

    else:
        print("Not updating new users.")

    # convertir columna user_id, por verificación
    df_accounts["user_id"] = df_accounts["user_id"].astype(int)

    # crea columnas del diccionario
    print("get_info_users")
    df_accounts = df_accounts.join(
        df_accounts["user_id"].apply(get_info_users).apply(pd.Series)
    )

    # participation

    # Eliminar columnas si existen
    nuevas_cols = ["observations_proj", "identifications_proj", "species_proj"]
    df_accounts = df_accounts.drop(columns=nuevas_cols, errors="ignore")

    info = df_accounts["user_id"].apply(get_user_info_in_project).apply(pd.Series)
    df_accounts = pd.concat([df_accounts, info], axis=1)

    # extraemos diccionario de identificaciones
    dict_identifications = get_identifications_by_user(PROJECT_ID)
    df_accounts["identifications_proj"] = df_accounts["user_id"].apply(
        lambda x: dict_identifications[x] if x in dict_identifications.keys() else 0
    )

    # taxonomy
    result = df_accounts["user_id"].apply(get_taxon_group_by_user).apply(pd.Series)
    df_accounts = pd.concat([df_accounts, result], axis=1)

    # research obs
    df_accounts["research_obs"] = df_accounts["user_id"].apply(
        get_research_obs_in_project
    )

    # download obs in project
    print("Fetch observations")
    results = fetch_observations(
        user_ids=df_accounts["user_id"].to_list(), proj_id=PROJECT_ID
    )
    parquet_file = f"{DIRECTORY}/data/eada/observations_eada.parquet"
    df_obs = save_df_observations(results, parquet_file)

    # Extraer identifiers dentro de la lista
    print("Get identifiers")
    df_obs["identifiers_login"] = df_obs["non_owner_ids"].apply(
        lambda lst: [d["user"]["login"] for d in lst] if lst else []
    )
    df_obs["identifiers_id"] = df_obs["non_owner_ids"].apply(
        lambda lst: [d["user"]["id"] for d in lst] if lst else []
    )

    # True si ALGÚN id de la celda es una cuenta de EADA student
    df_obs["eada_identifier"] = df_obs["identifiers_id"].apply(
        lambda x: bool(set(x) & set())
    )

    # get_taxonomy
    print("Get taxonomy")
    taxonomy = df_obs["identifications"].apply(get_taxonomy).apply(pd.Series)
    df_obs = pd.concat([df_obs, taxonomy], axis=1)

    # save results
    df_obs.to_parquet(parquet_file)
    df_accounts.to_csv(f"{DIRECTORY}/data/eada/minka_accounts.csv", index=False)
