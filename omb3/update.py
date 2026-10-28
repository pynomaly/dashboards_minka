import argparse
import os

import config
import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

# Directorio base del script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variable for taxon mapping
taxon_mapping = {}


def get_identifiers(place_id: int = None, d1: str = None):
    """Get identifiers from the API, optionally filtered by place_id and start date."""
    url = f"{config.API_PATH}/observations/identifiers"
    params = []
    if place_id:
        params.append(f"place_id={place_id}")
    if d1:
        params.append(f"d1={d1}")
    if params:
        url += "?" + "&".join(params)

    response = requests.get(url).json()

    total_identifiers = []
    for result in response["results"]:
        data = {
            "identifier_id": result["user_id"],
            "identifier_name": result["user"]["login"],
            "number_identifications": result["count"],
            "created_at": result["user"]["created_at"],
        }
        total_identifiers.append(data)

    df_identifiers = pd.DataFrame(total_identifiers)
    df_identifiers = df_identifiers.sort_values(
        by="number_identifications", ascending=False
    )
    df_identifiers["created_at"] = pd.to_datetime(df_identifiers["created_at"]).dt.date

    return df_identifiers.reset_index(drop=True)


def download_observations():
    """Download observations from MINKA API."""
    global taxon_mapping

    print("Downloading observations...")
    obs = get_obs(place_id=config.MAIN_PLACE, starts_on=config.STARTING_DATE)
    df_obs, __ = get_dfs(obs)
    df_obs.to_csv(f"{SCRIPT_DIR}/{config.DF_PATH}", index=False)
    print(f"Saved {len(df_obs)} observations to {config.DF_PATH}")

    # Crear mapeo de taxon_name -> taxon_id desde las observaciones
    taxon_mapping = df_obs.groupby("taxon_name")["taxon_id"].first().to_dict()

    return df_obs


def load_taxon_mapping():
    """Load taxon mapping from existing observations file."""
    global taxon_mapping

    df_obs = pd.read_csv(f"{SCRIPT_DIR}/{config.DF_PATH}")
    taxon_mapping = df_obs.groupby("taxon_name")["taxon_id"].first().to_dict()
    print(f"Loaded taxon mapping from {config.DF_PATH} ({len(taxon_mapping)} species)")


def update_species_file(filepath: str):
    """Update species file with taxon_ids from observations."""
    print(f"\nUpdating {filepath}...")
    df = pd.read_csv(f"{SCRIPT_DIR}/{filepath}")

    # Convert taxon_id to nullable Int64 to avoid dtype warnings
    df["taxon_id"] = df["taxon_id"].astype("Int64")

    # Actualizar taxon_id desde el mapeo de observaciones
    updated = 0
    for idx, row in df.iterrows():
        species_name = row["taxon_name"]
        if species_name in taxon_mapping:
            new_id = int(taxon_mapping[species_name])
            if pd.isna(row.get("taxon_id")) or row.get("taxon_id") != new_id:
                df.at[idx, "taxon_id"] = new_id
                updated += 1

    # Guardar archivo actualizado
    df.to_csv(f"{SCRIPT_DIR}/{filepath}", index=False)

    # Estadísticas
    total = len(df)
    with_id = df["taxon_id"].notna().sum()
    print(f"  Total species: {total}")
    print(f"  With taxon_id: {with_id} ({100*with_id/total:.1f}%)")
    print(f"  Updated: {updated}")

    return df


def update_species_files():
    """Update all species files."""
    for species_type, cfg in config.SPECIES_FILES.items():
        update_species_file(cfg["file"])


def download_identifiers():
    """Download identifiers from MINKA API."""
    print("\nDownloading identifiers...")
    df_identifiers = get_identifiers(place_id=config.MAIN_PLACE, d1=config.STARTING_DATE)
    df_identifiers.to_csv(f"{SCRIPT_DIR}/data/identifiers.csv", index=False)
    print(f"Saved {len(df_identifiers)} identifiers to data/identifiers.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update OMB3 dashboard data")
    parser.add_argument(
        "--no-observations",
        action="store_true",
        help="Skip downloading observations",
    )
    parser.add_argument(
        "--no-species",
        action="store_true",
        help="Skip updating species files",
    )
    parser.add_argument(
        "--no-identifiers",
        action="store_true",
        help="Skip downloading identifiers",
    )
    parser.add_argument(
        "--only",
        choices=["observations", "species", "identifiers"],
        help="Run only the specified task",
    )

    args = parser.parse_args()

    # Handle --only flag
    if args.only:
        if args.only == "observations":
            download_observations()
        elif args.only == "species":
            load_taxon_mapping()
            update_species_files()
        elif args.only == "identifiers":
            download_identifiers()
    else:
        # Run selected tasks
        if not args.no_observations:
            download_observations()
        else:
            # Need to load mapping for species update
            if not args.no_species:
                load_taxon_mapping()

        if not args.no_species:
            update_species_files()

        if not args.no_identifiers:
            download_identifiers()