#!/usr/bin/env python3

import datetime
import math
import os
import time
from functools import lru_cache
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from mecoda_minka import get_dfs, get_obs
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://minka-sdg.org"
API_PATH = f"https://api.minka-sdg.org/v1"

main_project = 417
all_projects = [417, 418, 419, 420]


# Optimized session configuration
def _create_optimized_session():
    """Create a session with connection pooling and retry strategy"""
    session = requests.Session()

    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=0.5,
        respect_retry_after_header=True,
    )

    # Connection pool adapter
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry_strategy,
        pool_block=False,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {"Connection": "keep-alive", "Keep-Alive": "timeout=30, max=100"}
    )

    return session


try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_25"
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


def _fetch_daily_metrics_batch(session, proj_id, day_batches, urls):
    """Fetch metrics for multiple days with parallel processing"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    headers = {"Authorization": f"Bearer {access_token}"}

    def fetch_day_metrics(day_str):
        """Fetch all metrics for a single day"""
        params = {
            "project_id": proj_id,
            "created_d2": day_str,
            "order": "desc",
            "order_by": "created_at",
        }

        def fetch_metric(url_metric_pair):
            url, metric = url_metric_pair
            retries = 3
            for attempt in range(retries):
                try:
                    response = session.get(
                        url, headers=headers, params=params, timeout=10
                    )
                    response.raise_for_status()
                    return metric, response.json()["total_results"]
                except Exception as e:
                    if attempt < retries - 1:
                        print(
                            f"Error fetching {metric} for {day_str} (attempt {attempt + 1}): {e}. Retrying..."
                        )
                        time.sleep(2)
                    else:
                        print(
                            f"Failed to fetch {metric} for {day_str} after {retries} attempts: {e}"
                        )
                        return metric, 0

        # Fetch all metrics for this day in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            metric_futures = {
                executor.submit(fetch_metric, (url, metric)): (url, metric)
                for url, metric in zip(
                    urls, ["species", "participants", "observations"]
                )
            }

            metrics = {}
            for future in as_completed(metric_futures):
                metric_name, value = future.result()
                metrics[metric_name] = value

        return {
            "date": day_str,
            "observations": metrics.get("observations", 0),
            "species": metrics.get("species", 0),
            "participants": metrics.get("participants", 0),
        }

    # Process all days in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        day_futures = {
            executor.submit(fetch_day_metrics, day_str): day_str
            for day_str in day_batches
        }

        results = []
        for future in as_completed(day_futures):
            results.append(future.result())

    # Sort results by date to maintain order
    return sorted(results, key=lambda x: x["date"])


def update_main_metrics(proj_id: int) -> pd.DataFrame:
    """
    Actualiza el df de las 3 métricas para cada día de la competición.
    Devuelve 0 para los días que no han llegado.
    """
    urls = [
        f"{API_PATH}/observations/species_counts?",
        f"{API_PATH}/observations/observers?",
        f"{API_PATH}/observations?",
    ]

    session = _get_global_session()

    # Fecha de inicio de la Biomarato: 2024/05/03 - 2024/10/15
    day = datetime.date(year=2025, month=5, day=3)
    rango_temporal = (datetime.date(year=2025, month=10, day=16) - day).days
    today = datetime.datetime.today().date()

    # Generar días válidos y futuros
    valid_days = []
    future_results = []

    current_day = day
    for _ in range(rango_temporal):
        day_str = current_day.strftime("%Y-%m-%d")
        if today >= current_day:
            valid_days.append(day_str)
        else:
            future_results.append(
                {
                    "date": day_str,
                    "observations": 0,
                    "species": 0,
                    "participants": 0,
                }
            )
        current_day = current_day + datetime.timedelta(days=1)

    # Fetch valid days in optimized batches
    valid_results = _fetch_daily_metrics_batch(session, proj_id, valid_days, urls)

    # Combine results
    all_results = valid_results + future_results
    result_df = pd.DataFrame(all_results).sort_values("date").reset_index(drop=True)

    print("Updated main metrics")
    return result_df


def get_list_users(id_project):
    """Parallelized version using concurrent API calls"""
    from concurrent.futures import ThreadPoolExecutor

    session = _get_global_session()
    headers = {"Authorization": f"Bearer {access_token}"}

    url1 = f"https://api.minka-sdg.org/v1/observations/observers?project_id={id_project}&quality_grade=research"
    url2 = f"https://api.minka-sdg.org/v1/observations/identifiers?project_id={id_project}&quality_grade=research"

    def fetch_url(url):
        try:
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()["results"]
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    try:
        # Fetch both URLs concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_users = executor.submit(fetch_url, url1)
            future_identifiers = executor.submit(fetch_url, url2)

            users_results = future_users.result()
            identifiers_results = future_identifiers.result()

    except Exception as e:
        print(f"Error fetching user data for project {id_project}: {e}")
        return pd.DataFrame(
            columns=["participant", "observacions", "espècies", "identificacions"]
        )

    if not users_results:
        return pd.DataFrame(
            columns=["participant", "observacions", "espècies", "identificacions"]
        )

    # Convert to DataFrame directly for better performance
    df_users = pd.DataFrame(
        [
            {
                "user_id": result["user_id"],
                "participant": result["user"]["login"],
                "observacions": result["observation_count"],
                "espècies": result["species_count"],
            }
            for result in users_results
        ]
    )

    if identifiers_results:
        df_identifiers = pd.DataFrame(
            [
                {"user_id": result["user_id"], "identificacions": result["count"]}
                for result in identifiers_results
            ]
        )

        # Use merge with better performance
        df_users = df_users.merge(df_identifiers, on="user_id", how="left")
    else:
        df_users["identificacions"] = 0

    df_users["identificacions"] = df_users["identificacions"].fillna(0)

    # Filter excluded users early to reduce data size
    if exclude_users:
        df_users = df_users[~df_users["participant"].isin(exclude_users)]

    return df_users[["participant", "observacions", "espècies", "identificacions"]]


# Session and data caching
_session_cache = None


def _get_global_session():
    """Get or create a global optimized session"""
    global _session_cache
    if _session_cache is None:
        _session_cache = _create_optimized_session()
    return _session_cache


@lru_cache(maxsize=32)
def _get_cached_csv(file_path):
    """Cache CSV files to avoid repeated disk reads with LRU cache"""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        return None


# Memory-optimized data processing
def get_new_data(project, grade=None):
    """Optimized new data retrieval with chunked processing"""
    obs_file = f"{directory}/data/{project}_df_obs.csv"
    photos_file = f"{directory}/data/{project}_df_photos.csv"

    try:
        # Read only necessary columns initially to save memory
        df_obs = pd.read_csv(
            obs_file, usecols=["id"] if os.path.exists(obs_file) else None
        )
        if df_obs is None or df_obs.empty:
            print(f"No existing data for project {project}")
            return

        max_id = df_obs["id"].max()
        del df_obs  # Free memory immediately

        # Get new observations
        obs = get_obs(id_project=project, id_above=max_id, grade=grade)
        if len(obs) > 0:
            print(f"Add {len(obs)} obs in project {project}")
            df_obs2, df_photos2 = get_dfs(obs)

            # Read full data only when needed
            df_obs_full = pd.read_csv(obs_file)
            df_photos_full = pd.read_csv(photos_file)

            # Concatenate efficiently
            df_obs_updated = pd.concat([df_obs_full, df_obs2], ignore_index=True)
            df_photos_updated = pd.concat(
                [df_photos_full, df_photos2], ignore_index=True
            )

            # Save with compression to reduce I/O time
            df_obs_updated.to_csv(
                obs_file,
                index=False,
                compression="gzip" if obs_file.endswith(".gz") else None,
            )
            df_photos_updated.to_csv(
                photos_file,
                index=False,
                compression="gzip" if photos_file.endswith(".gz") else None,
            )

            # Clear cache to free memory
            _get_cached_csv.cache_clear()

    except Exception as e:
        print(f"Error in get_new_data for project {project}: {e}")


def update_dfs_projects(
    project,
    day=(datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    grade=None,
):
    obs_file = f"{directory}/data/{project}_df_obs.csv"
    photos_file = f"{directory}/data/{project}_df_photos.csv"

    # updated today
    obs_nuevas = get_obs(id_project=project, updated_since=day, grade=grade)
    if len(obs_nuevas) > 0:
        df_obs_new, df_photos_new = get_dfs(obs_nuevas)
        df_photos_new["photos_id"] = df_photos_new["photos_id"].astype(int)

        # get downloaded with cache
        df_obs = _get_cached_csv(obs_file)
        df_photos = _get_cached_csv(photos_file)

        if df_obs is None or df_photos is None:
            return None, None

        # Optimized filtering using isin with sets for better performance
        new_ids = set(df_obs_new["id"].tolist())
        new_photo_ids = set(df_photos_new["photos_id"].tolist())

        old_obs = df_obs[~df_obs["id"].isin(new_ids)]
        old_photos = df_photos[~df_photos["photos_id"].isin(new_photo_ids)]

        # join old and updated with better memory management
        df_obs_updated = pd.concat([old_obs, df_obs_new], ignore_index=True)
        df_photo_updated = pd.concat([old_photos, df_photos_new], ignore_index=True)

        # Sort only once after concatenation
        df_obs_updated.sort_values(by="id", ascending=False, inplace=True)
        df_photo_updated.sort_values(by="photos_id", ascending=False, inplace=True)
    else:
        df_obs_updated = None
        df_photo_updated = None

    # remove casuals
    obs_casual = get_obs(grade="casual", updated_since=day)
    if len(obs_casual) > 0 and df_obs_updated is not None:
        casual_ids = {
            ob_casual.id for ob_casual in obs_casual
        }  # Use set for faster lookup
        df_obs_updated = df_obs_updated[~df_obs_updated["id"].isin(casual_ids)]
        df_photo_updated = df_photo_updated[~df_photo_updated["id"].isin(casual_ids)]

    result_len = len(df_obs_updated) if df_obs_updated is not None else 0
    print(f"Updated obs and photos for project {project}: {result_len}")
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


def get_list_species(proj_id: int, type="project") -> Optional[pd.DataFrame]:
    """Optimized version with global session and chunked processing"""
    headers = {"Authorization": f"Bearer {access_token}"}
    session = _get_global_session()

    if type == "project":
        params = {"project_id": proj_id, "quality_grade": "research"}
    elif type == "place":
        params = {"place_id": proj_id, "quality_grade": "research"}

    url = f"{API_PATH}/observations/species_counts"

    try:
        # Get total results first
        initial_response = session.get(url, headers=headers, params=params, timeout=15)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        total_results = initial_data["total_results"]

        if total_results == 0:
            return None

        if total_results > 500:
            # Sequential page fetching
            num_pages = math.ceil(total_results / 500)
            all_results = []

            for page in range(1, num_pages + 1):
                page_params = params.copy()
                page_params["page"] = page

                try:
                    response = session.get(
                        url, headers=headers, params=page_params, timeout=15
                    )
                    response.raise_for_status()
                    all_results.extend(response.json()["results"])
                except Exception as e:
                    print(f"Error fetching page {page}: {e}")
                    continue

            results = all_results
        else:
            results = initial_data["results"]

        # Create DataFrame more efficiently
        if results:
            return pd.DataFrame(
                [
                    {
                        "name": result["taxon"]["name"],
                        "count": result["count"],
                        "id": result["taxon"]["id"],
                    }
                    for result in results
                ]
            )

    except Exception as e:
        print(f"Error fetching species for {type} {proj_id}: {e}")

    return None


def get_first_obs_taxon(taxon_id, proj_id, type="project", session=None):
    if session is None:
        session = requests.Session()

    headers = {"Authorization": f"Bearer {access_token}"}
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
            "place_id": 244,
            "quality_grade": "research",
            "taxon_id": taxon_id,
            "order_by": "observed_on",
            "order": "asc",
        }

    results = session.get(url, headers=headers, params=params).json()["results"]

    if not results:
        return [None, None, None, None]

    primera_observacion = results[0]

    date = primera_observacion["observed_on"]
    author = primera_observacion["user"]["login"]
    obs_id = primera_observacion["id"]

    results_photos = session.get(url, headers=headers, params={"id": obs_id}).json()[
        "results"
    ]
    try:
        photo_url = results_photos[0]["photos"][0]["url"].replace("/square", "/large")
    except:
        photo_url = None

    return [date, author, obs_id, photo_url]


def _process_project(proj_id):
    """Process a single project with optimized operations"""
    print("Update df:", proj_id)
    try:
        downloaded_obs = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
        obs = get_obs(id_project=proj_id, grade="research")

        if len(obs) > 0 and len(obs) != len(downloaded_obs):
            df_obs, df_photos = get_dfs(obs)
            pt_users = get_list_users(proj_id)

            # Save files
            df_obs.to_csv(f"{directory}/data/{proj_id}_df_obs.csv", index=False)
            df_photos.to_csv(f"{directory}/data/{proj_id}_df_photos.csv", index=False)
            pt_users.to_csv(f"{directory}/data/{proj_id}_pt_users.csv", index=False)

            print(f"Updated files for project {proj_id}")
            return True
    except Exception as e:
        print(f"Error processing project {proj_id}: {e}")
        return False
    return False


def _process_species_with_obs(species_df, proj_id, session, type="project"):
    """Sequential species processing"""
    if species_df is None or len(species_df) == 0:
        return species_df

    species_copy = species_df.copy()

    for idx, row in species_copy.iterrows():
        try:
            result = get_first_obs_taxon(row["id"], proj_id, type, session)
            species_copy.loc[idx, ["first_date", "author", "obs_id", "photo_url"]] = (
                result
            )
        except Exception as e:
            print(f"Error fetching observation for taxon at index {idx}: {e}")
            species_copy.loc[idx, ["first_date", "author", "obs_id", "photo_url"]] = [
                None,
                None,
                None,
                None,
            ]

        # Small delay to avoid overwhelming the API
        time.sleep(0.1)

    return species_copy.sort_values(
        by=["first_date", "obs_id"], ascending=False, na_position="last"
    ).reset_index(drop=True)


def _process_species_with_obs_concurrent(species_df, proj_id, session, type="project"):
    """Concurrent species processing for better performance"""
    if species_df is None or len(species_df) == 0:
        return species_df

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch_single_observation(idx_row_tuple):
        idx, row = idx_row_tuple
        try:
            result = get_first_obs_taxon(row["id"], proj_id, type, session)
            return idx, result
        except Exception as e:
            print(f"Error fetching observation for taxon at index {idx}: {e}")
            return idx, [None, None, None, None]

    species_copy = species_df.copy()

    # Process observations concurrently with a reasonable thread limit
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_idx = {
            executor.submit(fetch_single_observation, (idx, row)): idx
            for idx, row in species_copy.iterrows()
        }

        for future in as_completed(future_to_idx):
            idx, result = future.result()
            species_copy.loc[idx, ["first_date", "author", "obs_id", "photo_url"]] = (
                result
            )

    return species_copy.sort_values(
        by=["first_date", "obs_id"], ascending=False, na_position="last"
    ).reset_index(drop=True)


def get_access_token():
    url = "https://www.minka-sdg.org/oauth/token"

    payload = {
        "client_id": os.getenv("MINKA_CLIENT_ID"),
        "client_secret": os.getenv("MINKA_CLIENT_SECRET"),
        "grant_type": "password",
        "username": os.getenv("MINKA_USER_EMAIL"),
        "password": os.getenv("MINKA_USER_PASSWORD"),
    }

    response = requests.post(url, data=payload)

    if response.ok:
        token = response.json().get("access_token")
        print("Token obtained")
    else:
        print("Error:", response.status_code, response.text)
        token = None
    return token


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()

    # api_token = get_admin_token()
    access_token = get_access_token()

    # Get main_metrics.csv
    main_metrics_df = update_main_metrics(main_project)
    main_metrics_df.to_csv(f"{directory}/data/main_metrics.csv", index=False)
    print("Main metrics actualizada")

    # Process projects sequentially
    for proj_id in all_projects:
        _process_project(proj_id)

    # Process species data with optimization
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_project_species(proj_id):
        """Process species for a single project"""
        try:
            print(f"Get species for project {proj_id}")
            species = get_list_species(proj_id)
            downloaded_species = pd.read_csv(f"{directory}/data/{proj_id}_species.csv")

            if species is not None and len(species) != len(downloaded_species):
                with requests.Session() as session:
                    session.headers.update({"Connection": "keep-alive"})
                    species = _process_species_with_obs_concurrent(
                        species, proj_id, session
                    )
                species.to_csv(f"{directory}/data/{proj_id}_species.csv", index=False)
                print(f"Species updated for {proj_id}")
                return f"Success: {proj_id}"
            return f"No update needed: {proj_id}"
        except Exception as e:
            error_msg = f"Error processing species for project {proj_id}: {e}"
            print(error_msg)
            return error_msg

    # Process project species concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_proj = {
            executor.submit(process_project_species, proj_id): proj_id
            for proj_id in all_projects
        }

        for future in as_completed(future_to_proj):
            result = future.result()

        # Process biomarato place species
        print("Get species for biomarato")
        place_biomarato = 244
        try:
            species_biomarato = get_list_species(place_biomarato, type="place")
            downloaded_species_biomarato = pd.read_csv(
                f"{directory}/data/place_biomarato_species.csv"
            )

            if species_biomarato is not None and len(species_biomarato) != len(
                downloaded_species_biomarato
            ):
                with requests.Session() as biomarato_session:
                    biomarato_session.headers.update({"Connection": "keep-alive"})
                    species_biomarato = _process_species_with_obs_concurrent(
                        species_biomarato, place_biomarato, biomarato_session, "place"
                    )
                species_biomarato.to_csv(
                    f"{directory}/data/place_biomarato_species.csv", index=False
                )
                print("Species updated for biomarato")
        except Exception as e:
            print(f"Error processing biomarato species: {e}")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
