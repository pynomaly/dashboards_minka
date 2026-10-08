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


def main_metrics_by_day(place_id: int) -> pd.DataFrame:
    """
    Saca métricas del place para cada día hasta el actual usando place_id y fechas.
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
                "place_id": place_id,
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


def _get_metrics_place(place_id: int, place_name: str) -> dict:
    """Get metrics for a place with date range."""
    observations = f"{config.API_PATH}/observations?"
    species = f"{config.API_PATH}/observations/species_counts?"
    observers = f"{config.API_PATH}/observations/observers?"

    params = {
        "place_id": place_id,
        "d1": config.START_DAY,
        "d2": config.END_DAY,
        "order": "desc",
        "order_by": "created_at",
    }
    session = requests.Session()
    total_species = session.get(species, params=params).json()["total_results"]
    total_participants = session.get(observers, params=params).json()["total_results"]
    total_obs = session.get(observations, params=params).json()["total_results"]

    result = {
        "place_id": place_id,
        "place": place_name,
        "observations": total_obs,
        "species": total_species,
        "participants": total_participants,
    }
    return result


def create_df_places(places: dict = None) -> pd.DataFrame:
    """Create dataframe with metrics for all places."""
    if places is None:
        places = config.PLACES

    place_metrics = []
    for place_id, place_name in places.items():
        results = _get_metrics_place(place_id, place_name)
        place_metrics.append(results)

    df_places = pd.DataFrame(place_metrics)
    return df_places


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


def _get_identifiers_by_place(place_id: int) -> pd.DataFrame:
    """Get identifiers for a place with date range."""
    url = f"{config.API_PATH}/observations/identifiers"
    params = {
        "place_id": place_id,
        "d1": config.START_DAY,
        "d2": config.END_DAY,
    }
    try:
        results = requests.get(url, params=params).json().get("results", [])
    except Exception:
        return pd.DataFrame()
    identifiers = []
    for result in results:
        identifier = {
            "user_id": result["user_id"],
            "user_login": result["user"]["login"],
            "number": result["count"],
        }
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
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
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


def get_participation_df_place(place_id: int) -> pd.DataFrame:
    """Generate users participation dataframe from place observations."""
    obs_path = f"{directory}/data/{place_id}_obs.csv"
    if not os.path.exists(obs_path):
        return pd.DataFrame()

    df_obs = pd.read_csv(obs_path)
    if len(df_obs) == 0:
        return pd.DataFrame()

    # Count observations per user
    pt_users = (
        df_obs["user_login"]
        .value_counts()
        .to_frame()
        .reset_index(drop=False)
        .rename(columns={"user_login": "participant", "count": "observacions"})
    )

    # Get identifications per user
    df_identifiers = _get_identifiers_by_place(place_id)
    pt_users["identificacions"] = pt_users["participant"].apply(
        lambda x: get_number_identifications(x, df_identifiers)
    )

    # Count unique species per user
    species_per_user = (
        df_obs.groupby("user_login")["taxon_name"]
        .nunique()
        .reset_index()
        .rename(columns={"user_login": "participant", "taxon_name": "espècies"})
    )

    pt_users = pt_users.merge(species_per_user, on="participant", how="left")
    pt_users["espècies"] = pt_users["espècies"].fillna(0).astype(int)

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

    # Actualiza main metrics por día para cada place
    for place_id in config.PLACES.keys():
        print(f"Actualizando métricas para place {place_id}: {config.PLACES[place_id]}")
        main_metrics_df = main_metrics_by_day(place_id)
        main_metrics_df.to_csv(
            f"{directory}/data/{place_id}_main_metrics.csv", index=False
        )
    print("Main metrics actualizada por día para todos los places")

    # Actualiza métricas de todos los places
    df_places = create_df_places(config.PLACES)
    df_places.to_csv(f"{directory}/data/all_places_metrics.csv", index=False)
    print("Main metrics of all places actualizado")

    # Actualiza df_obs y df_photos para cada place
    for place_id, place_name in config.PLACES.items():
        print(f"Descargando observaciones para {place_name} (place_id={place_id})")
        obs = get_obs(
            place_id=place_id, starts_on=config.START_DAY, ends_on=config.END_DAY
        )
        if len(obs) > 0:
            df_obs, df_photos = get_dfs(obs)

            df_obs.to_csv(f"{directory}/data/{place_id}_obs.csv", index=False)
            df_photos.to_csv(f"{directory}/data/{place_id}_photos.csv", index=False)

            print(f"Guardadas {len(df_obs)} observaciones para {place_name}")
        else:
            print(f"No hay observaciones para {place_name}")

    print("Todas las observaciones descargadas")

    # Genera CSV de usuarios para cada place
    for place_id, place_name in config.PLACES.items():
        print(f"Generando ranking de usuarios para {place_name}")
        users_df = get_participation_df_place(place_id)
        if len(users_df) > 0:
            users_df.to_csv(f"{directory}/data/{place_id}_users.csv", index=False)
            print(f"Guardados {len(users_df)} usuarios para {place_name}")
        else:
            print(f"No hay usuarios para {place_name}")

    print("Ranking de usuarios generado")

    # Agregar métricas diarias de todos los places para el proyecto
    print("Generando métricas diarias del proyecto...")
    all_metrics = []
    for place_id in config.PLACES.keys():
        metrics_path = f"{directory}/data/{place_id}_main_metrics.csv"
        if os.path.exists(metrics_path):
            df = pd.read_csv(metrics_path)
            all_metrics.append(df)

    if all_metrics:
        # Concatenar y agrupar por fecha
        combined = pd.concat(all_metrics, ignore_index=True)
        project_metrics = combined.groupby("date").agg({
            "observations": "sum",
            "species": "sum",
            "participants": "sum"
        }).reset_index()
        project_metrics.to_csv(f"{directory}/data/project_main_metrics.csv", index=False)
        print("Métricas diarias del proyecto generadas")
    else:
        print("No hay métricas de places para agregar")
