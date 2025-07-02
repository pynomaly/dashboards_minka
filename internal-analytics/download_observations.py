import os

import geopandas as gpd
import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs
from shapely.geometry import Point, Polygon

API_PATH = "https://api.minka-sdg.org/v1"
session = requests.Session()

try:
    directory = f"{os.environ['DASHBOARDS']}/internal-analytics"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


# Observaciones de Catalunya
def get_catalunya_column(df_obs, session=session):
    url = f"{API_PATH}/places/374"

    response = session.get(url).json()

    catalunya_geojson = response["results"][0]["geometry_geojson"]

    # Convertir el GeoJSON en un polígono de Shapely
    # polygon = Polygon(catalunya_geojson[0][0])  # Extraer la lista interna y crear un polígono
    polygon = Polygon(catalunya_geojson["coordinates"][0][0])

    # Crear un GeoDataFrame con el polígono
    gdf_catalunya = gpd.GeoDataFrame({"geometry": [polygon]}, crs="EPSG:4326")

    # Convertir las coordenadas en geometría de puntos
    df_obs["geometry"] = df_obs.apply(
        lambda row: Point(row["longitude"], row["latitude"]), axis=1
    )

    # Convertir df_obs en un GeoDataFrame con CRS WGS84 (EPSG:4326)
    gdf_obs = gpd.GeoDataFrame(df_obs, geometry=df_obs["geometry"], crs="EPSG:4326")

    # Crear una nueva columna 'in_catalunya' con valores True/False
    df_obs["catalunya"] = gdf_obs.within(gdf_catalunya.loc[0, "geometry"])

    return df_obs


# Importadas
def get_imported_column(df_obs):
    df_imported = pd.read_csv(f"{directory}/data/minka_obs_imported.csv")

    df_obs["imported"] = df_obs["id"].isin(df_imported["id"])

    return df_obs


# Proyectos
def get_projects(session=session):
    projects_data = []
    url = f"{API_PATH}/projects?order_by=created"
    total_results = session.get(url).json()["total_results"]
    for page in range(1, total_results // 300 + 2):
        url = f"{API_PATH}/projects?order_by=created&per_page=300&page={page}"
        results = session.get(url).json()["results"]
        for result in results:
            data = {}
            data["project_id"] = result["id"]
            data["project_name"] = result["title"]
            data["project_description"] = result["description"]
            data["created_at"] = result["created_at"]
            data["updated_at"] = result["updated_at"]
            data["project_type"] = result["project_type"]
            data["admin"] = result["admins"][0]["user"]["login"]
            projects_data.append(data)
    df_projects = pd.DataFrame(projects_data)
    df_projects["created_at"] = pd.to_datetime(
        df_projects["created_at"], utc=True
    ).dt.date
    df_projects["updated_at"] = pd.to_datetime(
        df_projects["updated_at"], utc=True
    ).dt.date

    df_projects["num_observations"] = df_projects["project_id"].apply(
        lambda x: _get_observations_by_project(x, session)
    )
    df_projects["num_observers"] = df_projects["project_id"].apply(
        lambda x: _get_observers_by_project(x, session)
    )
    df_projects["num_species"] = df_projects["project_id"].apply(
        lambda x: _get_species_by_project(x, session)
    )
    df_projects["last_observation"] = df_projects["project_id"].apply(
        lambda x: _get_last_observation_by_project(x, session)
    )

    return df_projects


def _get_observations_by_project(project_id, session):
    url = f"https://api.minka-sdg.org/v1/observations?project_id={project_id}&order=desc&order_by=created_at"
    try:
        return session.get(url).json()["total_results"]
    except:
        return 0


def _get_observers_by_project(project_id, session):
    url = f"https://api.minka-sdg.org/v1/observations/observers?project_id={project_id}"
    try:
        return session.get(url).json()["total_results"]
    except:
        return 0


def _get_species_by_project(project_id, session):
    url = f"https://api.minka-sdg.org/v1/observations/species_counts?project_id={project_id}"
    try:
        return session.get(url).json()["total_results"]
    except:
        return 0


def _get_last_observation_by_project(project_id, session):
    url = f"https://api.minka-sdg.org/v1/observations?project_id={project_id}&order=desc&order_by=created_at"
    try:
        return session.get(url).json()["results"][0]["created_at_details"]["date"]
    except:
        return None


# KPI: Number of unique users contributing to validation per year
def get_identifiers(session=session):
    url = f"{API_PATH}/observations/identifiers"

    response = session.get(url).json()

    total_identifiers = []

    for result in response["results"]:
        data = {}
        data["identifier_id"] = result["user_id"]
        data["identifier_name"] = result["user"]["login"]
        data["number_identifications"] = result["count"]
        data["species_count"] = result["user"]["species_count"]
        total_identifiers.append(data)

    df_identifiers = pd.DataFrame(total_identifiers)
    return df_identifiers


def get_users_created(session=session):
    try:
        print(f"{directory}/data/minka_accounts.csv")
        df_accounts = pd.read_csv(f"{directory}/data/minka_accounts.csv")
        i = df_accounts.user_id.max() + 1
    except:
        i = 1
        df_accounts = pd.DataFrame()

    max_empty = 100  # Máximo número de IDs consecutivos vacíos antes de detenerse
    empty_count = 0  # Contador de IDs vacíos consecutivos
    total = []

    while empty_count < max_empty:
        user_url = f"{API_PATH}/users/{i}"
        try:
            response = session.get(user_url)

            if response.status_code != 200:
                print(f"Error {response.status_code} en ID {i}, continuando...")
                empty_count += 1
                i += 1
                continue  # Saltar a la siguiente iteración

            json_data = response.json()

            if "results" not in json_data or not json_data["results"]:
                empty_count += 1  # Incrementar si el usuario no existe
            else:
                data = {
                    "user_id": i,
                    "user_name": json_data["results"][0]["login"],
                    "created_at": json_data["results"][0]["created_at"],
                    "observations_count": json_data["results"][0]["observations_count"],
                    "identifications_count": json_data["results"][0][
                        "identifications_count"
                    ],
                    "species_count": json_data["results"][0]["species_count"],
                }
                total.append(data)
                empty_count = (
                    0  # Reiniciar el contador si encontramos un usuario válido
                )

            i += 1  # Pasar al siguiente ID

        except requests.RequestException as e:
            print(f"Error en la solicitud: {e}")
            break  # Detener el bucle si hay un error grave de red

    df_accounts = pd.concat([df_accounts, pd.DataFrame(total)], ignore_index=True)

    return df_accounts


if __name__ == "__main__":

    # Actualización de usuarios
    print("Get users")
    session = requests.Session()
    df_accounts = get_users_created(session)
    df_accounts.to_csv(f"{directory}/data/minka_accounts.csv", index=False)

    # Descarga de observaciones
    print("Get observations")
    obs = get_obs()
    print("Get dfs for obs")
    df_obs, df_photos = get_dfs(obs)

    print("Get catalunya column")
    df_obs = get_catalunya_column(df_obs)

    print("Get imported column")
    df_obs = get_imported_column(df_obs)

    print("Guardando observaciones...")
    df_obs.to_csv(f"{directory}/data/minka_obs.csv", index=False)

    # Descarga de proyectos
    print("Get projects")
    df_projects = get_projects()

    print("Guardando proyectos...")
    df_projects.to_csv(f"{directory}/data/minka_projects.csv", index=False)
