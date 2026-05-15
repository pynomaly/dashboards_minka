#!/usr/bin/env python3

import datetime
import math
import os
import time
from typing import List, Optional
import config
import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"

main_project = config.MAIN_PROJ
place_biomaratona = config.MAIN_PLACE
all_projects = [config.MAIN_PROJ]

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


def update_main_metrics(proj_id: int) -> pd.DataFrame:
    """
    Actualiza el df de las 3 métricas para cada día de la competición.
    Devuelve 0 para los días que no han llegado.
    """
    results = []

    # Define URLs once
    urls = {
        "observations": f"{API_PATH}/observations",
        "species": f"{API_PATH}/observations/species_counts",
        "observers": f"{API_PATH}/observations/observers",
    }

    # Fecha de inicio de la Biomarato: 2024/05/03 - 2024/10/15
    start = datetime.datetime.strptime(config.START_DAY, "%Y/%m/%d")
    end = datetime.datetime.strptime(config.END_DAY, "%Y/%m/%d")
    rango_temporal = (end - start).days
    today = datetime.date.today()

    with requests.Session() as session:
        current_day = start

        for _ in range(rango_temporal):
            if today >= current_day.date():
                st_day = current_day.strftime("%Y-%m-%d")

                params = {
                    "project_id": proj_id,
                    "d2": st_day,
                    "order": "desc",
                    "order_by": "created_at",
                }

                # Batch API calls with retry logic
                metrics = {}
                for key, url in urls.items():
                    retries = 3
                    for attempt in range(retries):
                        try:
                            response = session.get(url, params=params)
                            response.raise_for_status()
                            metrics[key] = response.json()["total_results"]
                            break
                        except (requests.RequestException, KeyError) as e:
                            if attempt < retries - 1:
                                print(
                                    f"Error fetching {key} for {st_day} (attempt {attempt + 1}): {e}. Retrying..."
                                )
                                time.sleep(2)  # Wait 2 seconds before retry
                            else:
                                print(
                                    f"Failed to fetch {key} for {st_day} after {retries} attempts: {e}"
                                )
                                raise  # Re-raise the exception after all retries failed

                result = {
                    "date": st_day,
                    "observations": metrics["observations"],
                    "species": metrics["species"],
                    "participants": metrics["observers"],
                }
            else:
                # Para el resto devuelve 0
                result = {
                    "date": current_day.strftime("%Y-%m-%d"),
                    "observations": 0,
                    "species": 0,
                    "participants": 0,
                }

            results.append(result)
            current_day = current_day + datetime.timedelta(days=1)

    result_df = pd.DataFrame(results)
    print("Updated main metrics")
    return result_df


def get_list_users(id_project):
    with requests.Session() as session:
        # Get observers data
        url_observers = f"{API_PATH}/observations/observers?project_id={id_project}"
        try:
            response = session.get(url_observers)
            response.raise_for_status()
            observers_results = response.json()["results"]
        except (requests.RequestException, KeyError) as e:
            print(f"Error fetching observers: {e}")
            return pd.DataFrame()

        # Process observers data more efficiently
        users_data = []
        for result in observers_results:
            try:
                user_data = {
                    "user_id": result["user_id"],
                    "participant": result["user"]["login"],
                    "observacions": result["observation_count"],
                    "espècies": result["species_count"],
                }
                users_data.append(user_data)
            except KeyError as e:
                print(f"Missing key in observers data: {e}")
                continue

        if not users_data:
            return pd.DataFrame()

        df_users = pd.DataFrame(users_data)

        # Get identifiers data
        url_identifiers = f"{API_PATH}/observations/identifiers?project_id={id_project}"
        try:
            response = session.get(url_identifiers)
            response.raise_for_status()
            identifiers_results = response.json()["results"]
        except (requests.RequestException, KeyError) as e:
            print(f"Error fetching identifiers: {e}")
            # Return users without identifiers data
            df_users["identificacions"] = 0
            return df_users[
                ["participant", "observacions", "espècies", "identificacions"]
            ]

        # Process identifiers data
        identifiers_data = []
        for result in identifiers_results:
            try:
                identifiers_data.append(
                    {"user_id": result["user_id"], "identificacions": result["count"]}
                )
            except KeyError as e:
                print(f"Missing key in identifiers data: {e}")
                continue

        if identifiers_data:
            df_identifiers = pd.DataFrame(identifiers_data)
            df_users = pd.merge(df_users, df_identifiers, how="left", on="user_id")

        df_users.fillna(0, inplace=True)
        return df_users[["participant", "observacions", "espècies", "identificacions"]]


# update obs for projects
def get_new_data(project, grade=None):
    # Load existing data with better error handling
    obs_file = f"{directory}/data/{project}_df_obs.csv"
    photos_file = f"{directory}/data/{project}_df_photos.csv"

    try:
        df_obs = pd.read_csv(obs_file)
        max_id = df_obs["id"].max()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_obs = pd.DataFrame()
        max_id = 0

    try:
        df_photos = pd.read_csv(photos_file)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_photos = pd.DataFrame()

    # Check for new observations
    obs = get_obs(id_project=project, id_above=max_id, grade=grade)
    if len(obs) > 0:
        print(f"Add {len(obs)} obs in project {project}")
        df_obs_new, df_photos_new = get_dfs(obs)

        # Concatenate and save more efficiently
        df_obs_combined = pd.concat([df_obs, df_obs_new], ignore_index=True)
        df_photos_combined = pd.concat([df_photos, df_photos_new], ignore_index=True)

        # Save with error handling
        try:
            df_obs_combined.to_csv(obs_file, index=False)
            df_photos_combined.to_csv(photos_file, index=False)
        except Exception as e:
            print(f"Error saving files for project {project}: {e}")


def update_dfs_projects(
    project,
    day=(datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    grade=None,
):
    # Get updated observations
    obs_nuevas = get_obs(id_project=project, updated_since=day, grade=grade)

    if len(obs_nuevas) > 0:
        df_obs_new, df_photos_new = get_dfs(obs_nuevas)

        # Ensure photos_id is int with error handling
        try:
            df_photos_new["photos_id"] = df_photos_new["photos_id"].astype(int)
        except (ValueError, KeyError) as e:
            print(f"Error converting photos_id to int: {e}")

        # Load existing data with error handling
        try:
            df_obs = pd.read_csv(f"{directory}/data/{project}_df_obs.csv")
            df_photos = pd.read_csv(f"{directory}/data/{project}_df_photos.csv")
        except (FileNotFoundError, pd.errors.EmptyDataError) as e:
            print(f"Error loading existing data for project {project}: {e}")
            return None, None

        # More efficient filtering using sets for better performance
        new_obs_ids = set(df_obs_new["id"].tolist())
        new_photos_ids = set(df_photos_new["photos_id"].tolist())

        old_obs = df_obs[~df_obs["id"].isin(new_obs_ids)]
        old_photos = df_photos[~df_photos["photos_id"].isin(new_photos_ids)]

        # Combine old and updated data
        df_obs_updated = pd.concat(
            [old_obs, df_obs_new], ignore_index=True
        ).sort_values(by="id", ascending=False)

        df_photo_updated = pd.concat(
            [old_photos, df_photos_new], ignore_index=True
        ).sort_values(by="photos_id", ascending=False)
    else:
        df_obs_updated = None
        df_photo_updated = None

    # Remove casual observations
    obs_casual = get_obs(grade="casual", updated_since=day)
    if len(obs_casual) > 0 and df_obs_updated is not None:
        casual_ids = {
            ob_casual.id for ob_casual in obs_casual
        }  # Use set for faster lookup
        df_obs_updated = df_obs_updated[~df_obs_updated["id"].isin(casual_ids)]

        if df_photo_updated is not None:
            df_photo_updated = df_photo_updated[
                ~df_photo_updated["id"].isin(casual_ids)
            ]

    obs_count = len(df_obs_updated) if df_obs_updated is not None else 0
    print(f"Updated obs and photos for project {project}: {obs_count}")
    return df_obs_updated, df_photo_updated


def get_ranking_users(proj_id, grade=None):
    get_new_data(proj_id, grade)
    update_dfs_projects(proj_id, grade=grade)
    try:
        df_obs = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
        df_photos = pd.read_csv(f"{directory}/data/{proj_id}_df_photos.csv")
    except:
        df_obs = pd.DataFrame()
        df_photos = pd.DataFrame()

    if len(df_obs) == 0:
        df_obs = None
        df_photos = None

    # Sacamos pt_users
    if df_obs is not None:
        pt_users = get_list_users(proj_id)

    else:
        pt_users = None

    return df_obs, df_photos, pt_users


def get_list_species(proj_id: int, type="project") -> Optional[pd.DataFrame]:
    if type == "project":
        params = {"project_id": proj_id, "quality_grade": "research"}
    elif type == "place":
        params = {"place_id": proj_id, "quality_grade": "research"}
    else:
        raise ValueError("type must be 'project' or 'place'")

    url = f"{API_PATH}/observations/species_counts"

    with requests.Session() as session:
        try:
            # Get total count first
            response = session.get(url, params=params)
            response.raise_for_status()
            first_response = response.json()
            total_results = first_response["total_results"]

            if total_results == 0:
                return None

            results = first_response["results"]

            # If more than one page, fetch remaining pages
            if total_results > 500:
                num_pages = math.ceil(total_results / 500)
                for page in range(2, num_pages + 1):
                    params["page"] = page
                    try:
                        response = session.get(url, params=params)
                        response.raise_for_status()
                        results.extend(response.json()["results"])
                    except (requests.RequestException, KeyError) as e:
                        print(f"Error fetching page {page}: {e}")
                        break

        except (requests.RequestException, KeyError) as e:
            print(f"Error fetching species data: {e}")
            return None

    # Process results more efficiently
    if results:
        species_data = []
        for result in results:
            try:
                species_data.append(
                    {
                        "name": result["taxon"]["name"],
                        "count": result["count"],
                        "id": result["taxon"]["id"],
                    }
                )
            except KeyError as e:
                print(f"Missing key in species result: {e}")
                continue

        return pd.DataFrame(species_data) if species_data else None

    return None


def get_first_obs_taxon(taxon_id, proj_id, type="project", session=None):
    if session is None:
        session = requests.Session()

    url = f"{API_PATH}/observations"
    if type == "place":
        params = {
            "place_id": proj_id,
            "quality_grade": "research",
            "taxon_id": taxon_id,
            "order_by": "observed_on",
            "order": "asc",
        }
    else:
        params = {
            "place_id": 398,
            "quality_grade": "research",
            "taxon_id": taxon_id,
            "order_by": "observed_on",
            "order": "asc",
        }

    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        results = response.json()["results"]
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching first observation for taxon {taxon_id}: {e}")
        return [None, None, None, None]

    if not results:
        return [None, None, None, None]

    try:
        primera_observacion = results[0]
        date = primera_observacion["observed_on"]
        author = primera_observacion["user"]["login"]
        obs_id = primera_observacion["id"]
    except KeyError as e:
        print(f"Missing key in observation data: {e}")
        return [None, None, None, None]

    # Get photo with error handling
    try:
        response = session.get(url, params={"id": obs_id})
        response.raise_for_status()
        results_photos = response.json()["results"]

        if results_photos and results_photos[0].get("photos"):
            photo_url = results_photos[0]["photos"][0]["url"].replace(
                "/square", "/large"
            )
        else:
            photo_url = None
    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Error fetching photo for observation {obs_id}: {e}")
        photo_url = None

    return [date, author, obs_id, photo_url]


if __name__ == "__main__":
    # Get main_metrics.csv
    start_time = time.time()
    print("Updating main metrics")
    main_metrics_df = update_main_metrics(main_project)
    main_metrics_df.to_csv(f"{directory}/data/main_metrics.csv", index=False)
    print("Main metrics actualizada")

    # Update df de cada proyecto - optimized with better error handling
    if config.MAIN_PROJ:
        for proj_id in all_projects:
            print(f"Update df: {proj_id}")

            # Load existing data with better error handling
            try:
                downloaded_obs = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
            except (FileNotFoundError, pd.errors.EmptyDataError):
                downloaded_obs = pd.DataFrame()

            # Get current observations
            obs = get_obs(id_project=proj_id)
            pt_users = get_list_users(proj_id)

            # Check if there are new observations
            if len(obs) > 0 and len(obs) != len(downloaded_obs):
                print(f"Processing {len(obs)} observations for project {proj_id}")
                try:
                    df_obs, df_photos = get_dfs(obs)

                except Exception as e:
                    print(f"Error processing data for project {proj_id}: {e}")
                    continue

                # Save files with better error handling
                files_to_save = [
                    (
                        df_obs,
                        f"{directory}/data/{proj_id}_df_obs.csv",
                        f"df_obs_{proj_id}",
                    ),
                    (
                        df_photos,
                        f"{directory}/data/{proj_id}_df_photos.csv",
                        f"df_photos_{proj_id}",
                    ),
                    (
                        pt_users,
                        f"{directory}/data/{proj_id}_pt_users.csv",
                        f"pt_users_{proj_id}",
                    ),
                ]

                for data, filepath, name in files_to_save:
                    if data is not None and not data.empty:
                        try:
                            data.to_csv(filepath, index=False)
                            print(f"{name}.csv updated - {len(data)} records")
                        except Exception as e:
                            print(f"Error saving {name}: {e}")
                    else:
                        print(f"No data to save for {name}")
            else:
                print(f"No new observations for project {proj_id}")

    # Get listado de species - optimized processing
    if all_projects:
        for proj_id in all_projects:
            print(f"Get species for project {proj_id}")

            try:
                species = get_list_species(proj_id)
            except Exception as e:
                print(f"Error getting species for project {proj_id}: {e}")
                continue

            if species is None:
                print(f"No species data for project {proj_id}")
                continue

            # Load existing species data
            try:
                downloaded_species = pd.read_csv(
                    f"{directory}/data/{proj_id}_species.csv"
                )
            except (FileNotFoundError, pd.errors.EmptyDataError):
                downloaded_species = pd.DataFrame()

            # Check if update is needed
            if len(species) != len(downloaded_species):
                print(
                    f"Updating species data for project {proj_id}: {len(species)} species"
                )

                try:
                    with requests.Session() as session:
                        # More efficient apply with error handling
                        species_with_details = species.copy()
                        details_list = []

                        for _, row in species.iterrows():
                            try:
                                details = get_first_obs_taxon(
                                    row["id"], proj_id, session=session
                                )
                                details_list.append(details)
                            except Exception as e:
                                print(
                                    f"Error getting details for species {row['id']}: {e}"
                                )
                                details_list.append([None, None, None, None])

                        # Add details to dataframe
                        details_df = pd.DataFrame(
                            details_list,
                            columns=["first_date", "author", "obs_id", "photo_url"],
                        )
                        species_final = pd.concat(
                            [species_with_details, details_df], axis=1
                        )

                        # Sort and save
                        species_final = species_final.sort_values(
                            by=["first_date", "obs_id"],
                            ascending=False,
                            na_position="last",
                        ).reset_index(drop=True)

                        species_final.to_csv(
                            f"{directory}/data/{proj_id}_species.csv", index=False
                        )
                        print(f"Species updated for project {proj_id}")

                except Exception as e:
                    print(
                        f"Error processing species details for project {proj_id}: {e}"
                    )
            else:
                print(f"Species data up to date for project {proj_id}")

    # Get listado de species por lugar - optimized
    print("Get species for biomarato")

    try:
        species_biomarato = get_list_species(place_biomaratona, type="place")
    except Exception as e:
        print(f"Error getting biomarato species: {e}")
        species_biomarato = None

    if species_biomarato is not None:
        try:
            downloaded_species_biomarato = pd.read_csv(
                f"{directory}/data/place_biomaratona_species.csv"
            )
        except (FileNotFoundError, pd.errors.EmptyDataError):
            downloaded_species_biomarato = pd.DataFrame()

        if len(species_biomarato) != len(downloaded_species_biomarato):
            print(f"Updating biomarato species: {len(species_biomarato)} species")

            try:
                with requests.Session() as session:
                    details_list = []

                    for _, row in species_biomarato.iterrows():
                        try:
                            details = get_first_obs_taxon(
                                row["id"],
                                place_biomaratona,
                                type="place",
                                session=session,
                            )
                            details_list.append(details)
                        except Exception as e:
                            print(
                                f"Error getting biomarato species details for {row['id']}: {e}"
                            )
                            details_list.append([None, None, None, None])

                    # Add details to dataframe
                    details_df = pd.DataFrame(
                        details_list,
                        columns=["first_date", "author", "obs_id", "photo_url"],
                    )
                    species_biomarato_final = pd.concat(
                        [species_biomarato, details_df], axis=1
                    )

                    species_biomarato_final.to_csv(
                        f"{directory}/data/place_biomaratona_species.csv", index=False
                    )
                    print("Species updated for biomarato")

            except Exception as e:
                print(f"Error processing biomarato species details: {e}")
        else:
            print("Biomarato species data up to date")
    else:
        print("No biomarato species data available")

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
