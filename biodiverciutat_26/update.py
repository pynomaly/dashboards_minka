import datetime
import math
import os

import config
import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


def get_marine(taxon_name: str) -> bool:
    """
    Devuelve True/False en base a un taxon_name
    """
    name_clean = taxon_name.replace(" ", "+")
    status = requests.get(
        f"https://www.marinespecies.org/rest/AphiaIDByName/{name_clean}?marine_only=true"
    ).status_code
    if (status == 200) or (status == 206):
        result = True
    else:
        result = False
    return result


def main_metrics_by_day(proj_id: int) -> pd.DataFrame:
    """
    Saca métricas del proyecto para cada día hasta el actual
    """
    results = []
    observations = f"{config.API_PATH}/observations"
    species = f"{config.API_PATH}/observations/species_counts"
    observers = f"{config.API_PATH}/observations/observers"

    session = requests.Session()

    start_day = datetime.date.fromisoformat(config.START_DAY)
    end_day = datetime.date.fromisoformat(config.END_DAY)
    today = datetime.date.today()

    current_day = start_day
    while current_day <= end_day:
        day_str = current_day.strftime("%Y-%m-%d")
        print(day_str)

        if current_day <= today:
            params = {
                "project_id": proj_id,
                "d1": day_str,
                "d2": day_str,
                "order": "desc",
                "order_by": "created_at",
            }
            try:
                total_species = session.get(species, params=params).json()[
                    "total_results"
                ]
                total_participants = session.get(observers, params=params).json()[
                    "total_results"
                ]
                total_obs = session.get(observations, params=params).json()[
                    "total_results"
                ]
            except (requests.RequestException, KeyError) as e:
                print(f"Error fetching data for {day_str}: {e}")
                total_species = total_participants = total_obs = 0
        else:
            total_species = total_participants = total_obs = 0

        results.append(
            {
                "date": day_str,
                "observations": total_obs,
                "species": total_species,
                "participants": total_participants,
            }
        )

        current_day += datetime.timedelta(days=1)

    print("Updated main metrics")
    return pd.DataFrame(results)


def _get_metrics_proj(proj_id: int, proj_city: str) -> dict:
    observations = f"{config.API_PATH}/observations?"
    species = f"{config.API_PATH}/observations/species_counts?"
    observers = f"{config.API_PATH}/observations/observers?"

    params = {
        "project_id": proj_id,
        "order": "desc",
        "order_by": "created_at",
    }
    # Crear una sesión de requests
    session = requests.Session()
    total_species = session.get(species, params=params).json()["total_results"]
    total_participants = session.get(observers, params=params).json()["total_results"]
    total_obs = session.get(observations, params=params).json()["total_results"]

    result = {
        "project": proj_id,
        "city": proj_city,
        "observations": total_obs,
        "species": total_species,
        "participants": total_participants,
    }
    return result


def create_df_projs(projects: dict) -> pd.DataFrame:
    proj_metrics = []

    for k, v in projects.items():
        results = _get_metrics_proj(k, v)
        proj_metrics.append(results)

    df_projs = pd.DataFrame(proj_metrics)

    return df_projs


def get_missing_taxon(taxon_id: int, rank: str):
    url = f"{config.API_PATH}/taxa/{taxon_id}"
    try:
        ancestors = requests.get(url).json()["results"][0]["ancestors"]
        for anc in ancestors:
            if anc["rank"] == rank:
                return anc["name"]
    except:
        return None


def _get_species(user_name: str, proj_id: int) -> int:
    species = f"{config.API_PATH}/observations/species_counts"
    params = {"project_id": proj_id, "user_login": user_name}
    return requests.get(species, params=params).json()["total_results"]


def _get_identifiers(proj_id: int) -> pd.DataFrame:
    url = f"{config.API_PATH}/observations/identifiers?project_id={proj_id}"
    results = requests.get(url).json()["results"]
    identifiers = []
    for result in results:
        identifier = {}
        identifier["user_id"] = result["user_id"]
        identifier["user_login"] = result["user"]["login"]
        identifier["number"] = result["count"]
        identifiers.append(identifier)
    return pd.DataFrame(identifiers)


def get_number_identifications(user_name, df_identifiers):
    try:
        number_id = df_identifiers.loc[
            df_identifiers.user_login == user_name, "number"
        ].item()
    except:
        number_id = 0
    return number_id


def get_participation_df(main_project: int) -> pd.DataFrame:
    df_obs = pd.read_csv(f"{config.DIRECTORY}/data/{main_project}_obs.csv")
    pt_users = (
        df_obs["user_login"]
        .value_counts()
        .to_frame()
        .reset_index(drop=False)
        .rename(columns={"user_login": "participant", "count": "observacions"})
    )
    df_identifiers = _get_identifiers(main_project)

    pt_users["identificacions"] = pt_users["participant"].apply(
        lambda x: get_number_identifications(x, df_identifiers)
    )
    pt_users["espècies"] = pt_users["participant"].apply(
        lambda x: _get_species(x, main_project)
    )
    return pt_users


def get_marine_count(df_obs: pd.DataFrame) -> pd.DataFrame:
    # Número de observaciones, marines y terrestres
    df_marines = (
        df_obs.groupby("marine")
        .size()
        .reset_index()
        .rename(columns={"marine": "entorn", 0: "observacions"})
    )
    # Número de especies marinas y terrestres
    df_spe = df_obs.groupby("marine")["taxon_name"].nunique().reset_index()
    especies_terrestres = df_spe.loc[df_spe.marine == False, "taxon_name"].item()
    especies_marinas = df_spe.loc[df_spe.marine == True, "taxon_name"].item()

    df_marines["entorn"] = df_marines["entorn"].map({False: "terrestre", True: "marí"})
    df_marines.loc[df_marines.entorn == "marí", "espècies"] = especies_marinas
    df_marines.loc[df_marines.entorn == "terrestre", "espècies"] = especies_terrestres

    df_marines = df_marines.sort_values(by="observacions", ascending=False).reset_index(
        drop=True
    )
    return df_marines


def get_main_metrics(proj_id):
    session = requests.Session()

    species = f"{config.API_PATH}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}"
    total_species = session.get(url1).json()["total_results"]

    observers = f"{config.API_PATH}/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}"
    total_participants = session.get(url2).json()["total_results"]

    observations = f"{config.API_PATH}/observations?"
    url3 = f"{observations}&project_id={proj_id}"
    total_obs = session.get(url3).json()["total_results"]

    return total_species, total_participants, total_obs


def get_marine_species(proj_id):
    session = requests.Session()
    total_sp = []

    species = f"{config.API_PATH}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}"

    total_num = session.get(url1).json()["total_results"]

    pages = math.ceil(total_num / 500)

    for i in range(pages):
        especie = {}
        page = i + 1
        url = f"{species}&project_id={proj_id}&page={page}"
        results = session.get(url).json()["results"]
        for result in results:
            especie = {}
            especie["taxon_id"] = result["taxon"]["id"]
            especie["taxon_name"] = result["taxon"]["name"]
            especie["rank"] = result["taxon"]["rank"]
            especie["ancestry"] = result["taxon"]["ancestry"]
            total_sp.append(especie)

    df_species = pd.DataFrame(total_sp)
    taxon_url = "https://raw.githubusercontent.com/eosc-cos4cloud/mecoda-orange/master/mecoda_orange/data/taxon_tree_with_marines.csv"
    taxon_tree = pd.read_csv(taxon_url)

    df_species = pd.merge(
        df_species,
        taxon_tree[["taxon_id", "marine"]],
        on="taxon_id",
        how="left",
    )
    return df_species


if __name__ == "__main__":

    # Actualiza main metrics
    main_metrics_df = main_metrics_by_day(config.MAIN_PROJ)
    main_metrics_df.to_csv(
        f"{directory}/data/{config.MAIN_PROJ}_main_metrics.csv", index=False
    )
    print("Main metrics actualizada por día")

    # Actualiza métricas de los proyectos
    df_projs = create_df_projs(config.PROJECTS)
    df_projs.to_csv(
        f"{directory}/data/{config.MAIN_PROJ}_main_metrics_projects.csv", index=False
    )
    print("Main metrics of city projects actualizado")

    # Actualiza df_obs y df_photos totales
    obs = get_obs(id_project=config.MAIN_PROJ)
    if len(obs) > 0:
        df_obs, df_photos = get_dfs(obs)
        # Completar campos de taxonomías
        cols = ["class", "order", "family", "genus"]

        df_obs.to_csv(f"{directory}/data/{config.MAIN_PROJ}_obs.csv", index=False)
        df_photos.to_csv(f"{directory}/data/{config.MAIN_PROJ}_photos.csv", index=False)

        print("Sacando columna marine")
        df_obs["taxon_id"] = df_obs["taxon_id"].replace("nan", None)
        df_filtered = df_obs[df_obs["taxon_id"].notnull()].copy()
        df_filtered["taxon_id"] = df_filtered["taxon_id"].astype(int)

        # sacamos listado de especies incluidas en el proyecto con col marina
        print("Aplicando get_marine_species")
        df_species = get_marine_species(config.MAIN_PROJ)

        # Sacar columna marino
        df_filtered = pd.merge(
            df_filtered,
            df_species[["taxon_id", "marine"]],
            on="taxon_id",
            how="left",
        )

        # Dataframe de participantes
        print("Dataframe de participantes")
        df_users = get_participation_df(config.MAIN_PROJ)
        df_users.to_csv(f"{directory}/data/{config.MAIN_PROJ}_users.csv", index=False)

        # Cuenta de marino/terrestre
        print("Cuenta de marinos/terrestres")
        try:
            df_marine = get_marine_count(df_filtered)
            df_marine.to_csv(
                f"{directory}/data/{config.MAIN_PROJ}_marines.csv", index=False
            )
        except:
            df_obs["marine"] = None
            df_obs.to_csv(
                f"{directory}/data/{config.MAIN_PROJ}_marines.csv", index=False
            )

    # Dataframe métricas totales
    print("Dataframe métricas tiempo real")
    total_species, total_participants, total_obs = get_main_metrics(config.MAIN_PROJ)
    df = pd.DataFrame(
        {
            "metrics": ["observacions", "espècies", "participants"],
            "values": [total_obs, total_species, total_participants],
        }
    )
    df.to_csv(
        f"{directory}/data/{config.MAIN_PROJ}_metrics_tiempo_real.csv", index=False
    )
