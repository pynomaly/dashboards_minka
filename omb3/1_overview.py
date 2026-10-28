import os

import streamlit as st

# Set page config FIRST before any other Streamlit-related imports
try:
    directory = f"{os.environ['DASHBOARDS']}/omb3"
except KeyError:
    directory = os.path.dirname(os.path.abspath(__file__))

from config import PAGE_ICON, PAGE_TITLE, SIDEBAR_WIDTH

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/{PAGE_ICON}",
    page_title=PAGE_TITLE,
)
st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: {SIDEBAR_WIDTH}px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: {SIDEBAR_WIDTH}px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Now import everything else (after set_page_config)
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
from config import (
    API_PATH,
    CATEGORY_ORDER,
    CATEGORY_TRANSLATIONS,
    COLORS,
    HEADER_LOGO,
    HEADER_TITLE,
    HOME_PATH,
    MAIN_PLACE,
    OBSERVE_PATH,
    SPECIES_FILES,
    STARTING_DATE,
)
from dateutil.relativedelta import relativedelta
from streamlit_extras.metric_cards import style_metric_cards

SESSION = requests.Session()

# Simple in-memory cache for common names (avoids Streamlit context issues in threads)
_common_name_cache = {}


def _fetch_common_name_api(taxon_id: int, species_name: str) -> str:
    """Fetch English common name from MINKA API (internal, no Streamlit cache)"""
    cache_key = f"{taxon_id}_{species_name}"
    if cache_key in _common_name_cache:
        return _common_name_cache[cache_key]

    result = ""
    try:
        url = f"{OBSERVE_PATH}/taxa/{taxon_id}-{species_name.replace(' ', '-')}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            taxon_names = data.get("taxon_names", [])
            for name in taxon_names:
                if name.get("lexicon") == "English":
                    result = name.get("name", "")
                    break
    except Exception:
        pass

    _common_name_cache[cache_key] = result
    return result


@st.cache_data(ttl=86400)
def fetch_common_names(species_list: tuple, taxon_mapping_items: tuple) -> dict:
    """Fetch common names for all species in parallel (cached by species list)"""
    taxon_mapping = dict(taxon_mapping_items)
    common_names = {}

    def fetch_single(species_name):
        taxon_id = taxon_mapping.get(species_name)
        if taxon_id:
            return species_name, _fetch_common_name_api(int(taxon_id), species_name)
        return species_name, ""

    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_single, species_list)
        for species_name, common_name in results:
            common_names[species_name] = common_name

    return common_names


@st.cache_data(ttl=3600)
def load_main_observations():
    """Load main observations CSV with caching"""
    df = pd.read_csv(f"{directory}/data/df_obs_catalunya.csv")
    df["observed_on"] = pd.to_datetime(df["observed_on"])
    return df


@st.cache_data(ttl=3600)
def load_species_csv(filename):
    """Load species CSV with caching"""
    return pd.read_csv(f"{directory}/data/{filename}")


# Functions


def create_header():
    with st.container():
        # Título
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(f"{directory}/images/{HEADER_LOGO}")
        with col2:
            st.header(HEADER_TITLE)


@st.cache_data(ttl=3600)
def get_main_metrics(start_date=None, end_date=None):
    """Get main metrics with parallel API calls"""

    def fetch_url(url):
        return requests.get(url).json()["total_results"]

    urls = {
        "observations": f"{API_PATH}/observations?place_id={MAIN_PLACE}&d1={start_date}&d2={end_date}&verifiable=true",
        "species": f"{API_PATH}/observations/species_counts?place_id={MAIN_PLACE}&d1={start_date}&d2={end_date}&verifiable=true",
        "observers": f"{API_PATH}/observations/observers?place_id={MAIN_PLACE}&d1={start_date}&d2={end_date}&verifiable=true",
        "identifiers": f"{API_PATH}/observations/identifiers?place_id={MAIN_PLACE}&d1={start_date}&d2={end_date}&verifiable=true",
    }

    total_results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {key: executor.submit(fetch_url, url) for key, url in urls.items()}
        for key, future in futures.items():
            total_results[key] = future.result()

    return total_results


def show_main_metrics(start_date=None, end_date=None):
    total_results = get_main_metrics(start_date=start_date, end_date=end_date)

    # Cards
    __, col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        st.metric("Total Observations", f'{total_results["observations"]:,}')

        if st.button("Show details", key="btn_obs", use_container_width=True):
            if st.session_state.get("selected_metric") == "observations":
                st.session_state.selected_metric = None  # Close if already open
            else:
                st.session_state.selected_metric = "observations"

    with col2:
        st.metric(
            "Unique Species",
            f'{total_results["species"]:,}',
        )
        if st.button("Show details", key="btn_species", use_container_width=True):
            if st.session_state.get("selected_metric") == "species":
                st.session_state.selected_metric = None  # Close if already open
            else:
                st.session_state.selected_metric = "species"

    with col3:
        st.metric(
            "Unique Observers",
            f'{total_results["observers"]:,}',
        )
        if st.button("Show details", key="btn_observers", use_container_width=True):
            if st.session_state.get("selected_metric") == "observers":
                st.session_state.selected_metric = None  # Close if already open
            else:
                st.session_state.selected_metric = "observers"

    with col4:
        st.metric(
            "Unique Identifiers",
            f'{total_results["identifiers"]:,}',
        )
        if st.button("Show details", key="btn_identifiers", use_container_width=True):
            if st.session_state.get("selected_metric") == "identifiers":
                st.session_state.selected_metric = None  # Close if already open
            else:
                st.session_state.selected_metric = "identifiers"

    style_metric_cards(
        background_color="#fff",
        border_left_color=COLORS[3],
        box_shadow=False,
    )

    # Store date range in session_state for chart rendering
    st.session_state.chart_start_date = start_date
    st.session_state.chart_end_date = end_date

    # Mostrar el gráfico según la selección
    if "selected_metric" in st.session_state and st.session_state.selected_metric:
        metric = st.session_state.selected_metric

        titles = {
            "observations": "📊 Observations by Month",
            "species": "📊 Unique Species by Month",
            "observers": "📊 Unique Observers by Month",
            "identifiers": "📊 Identifiers Over Time",
        }

        st.write(f"### {titles.get(metric, '')}")

        # Calculate full date range for chart
        chart_begin = None
        chart_end = None
        if start_date and end_date:
            chart_begin = f"{start_date}-01"
            end_month = datetime.strptime(f"{end_date}-01", "%Y-%m-%d")
            chart_end = (
                end_month + relativedelta(months=1) - relativedelta(days=1)
            ).strftime("%Y-%m-%d")

        if metric in ["observations", "species", "observers"]:
            create_metric_chart(
                column=metric, begin_date=chart_begin, end_date=chart_end
            )
        elif metric == "identifiers":
            st.info("Identifiers chart coming soon")


@st.cache_data(ttl=3600)
def get_monthly_counts(column, begin_date: str = None, end_date: str = None):
    """Cache the data processing separately from chart rendering"""
    df_obs = load_main_observations()

    # Apply date filter if provided
    if begin_date and end_date:
        df_obs_filtered = df_obs[
            (df_obs["observed_on"] >= begin_date) & (df_obs["observed_on"] <= end_date)
        ].copy()
    else:
        df_obs_filtered = df_obs[df_obs["observed_on"] >= "2021-04-01"].copy()

    if column == "observations":
        monthly_counts = (
            df_obs_filtered.set_index("observed_on")
            .resample("ME")
            .size()
            .reset_index(name="observations")
        )
    elif column == "species":
        monthly_counts = (
            df_obs_filtered.set_index("observed_on")
            .resample("ME")["taxon_name"]
            .nunique()
            .reset_index(name="species")
        )
    elif column == "observers":
        monthly_counts = (
            df_obs_filtered.set_index("observed_on")
            .resample("ME")["user_login"]
            .nunique()
            .reset_index(name="observers")
        )
    else:
        return pd.DataFrame()

    monthly_counts["month"] = monthly_counts["observed_on"].dt.strftime("%Y-%m")
    return monthly_counts


def create_metric_chart(column, begin_date: str = None, end_date: str = None):
    """Create chart for any metric - data is cached separately"""
    monthly_counts = get_monthly_counts(column, begin_date, end_date)

    if monthly_counts.empty:
        st.info("No data available")
        return

    fig = px.bar(
        monthly_counts,
        x="month",
        y=column,
        title="",
        labels={"month": "Month", column: column.capitalize()},
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_tickangle=0,
        template="plotly_white",
        showlegend=False,
    )

    fig.update_traces(marker_color=COLORS[4])

    st.plotly_chart(fig, use_container_width=True)


def create_observations_chart(column, begin_date: str = None, end_date: str = None):
    """Wrapper for backwards compatibility"""
    create_metric_chart(column, begin_date, end_date)


@st.fragment
def create_table_map(df_taxa, taxa_group, df_obs, show_title=True, begin_date=None):
    """Fragment to handle table/map interaction without full page rerun."""
    # Tu dataframe de especies
    df_species = (
        df_taxa.groupby("taxon_name")
        .agg(
            {
                "id": "count",
                "latitude": "mean",
                "longitude": "mean",
                "taxon_id": "first",
            }
        )
        .sort_values(by="id", ascending=False)
        .reset_index()
    )
    df_species.columns = ["Species", "Observations", "Lat", "Lon", "taxon_id"]

    if show_title:
        st.subheader(f"{taxa_group.capitalize()} species reported: {len(df_species)}")
    else:
        st.caption(f"**{len(df_species)} species** with **{len(df_taxa):,} observations**")

    # Crear dos columnas: tabla a la izquierda, mapa a la derecha
    col_table, col_map = st.columns([1, 1.5])

    # Session state keys unique per taxa_group (definidos antes de los bloques)
    key_species = f"selected_species_{taxa_group}"
    key_lat = f"selected_lat_{taxa_group}"
    key_lon = f"selected_lon_{taxa_group}"

    with col_table:
        # Get taxon_id mapping for species
        taxon_mapping = df_taxa.groupby("taxon_name")["taxon_id"].first().to_dict()
        # Fetch common names (use tuples for caching)
        species_list = tuple(df_species["Species"].tolist())
        taxon_mapping_items = tuple(taxon_mapping.items())
        common_names = fetch_common_names(species_list, taxon_mapping_items)

        # Añadir columna de checkbox con link en Species
        df_display = df_species[["Species", "Observations"]].copy()
        # Store original species names for later use
        species_names = df_display["Species"].copy()
        # Add common name column
        df_display["Common Name"] = df_display["Species"].map(common_names)
        # Create URL for observations filtered by place_id, taxon_name and d1
        d1_param = f"&d1={begin_date}" if begin_date else ""
        df_display["Species"] = df_display["Species"].apply(
            lambda x: f"{OBSERVE_PATH}/observations?place_id={MAIN_PLACE}&taxon_name={x.replace(' ', '%20')}{d1_param}"
        )

        # Initialize Select column - mark only the previously selected species
        prev_selected = st.session_state.get(key_species)
        df_display["Select"] = species_names == prev_selected

        # Usar data_editor para permitir interacción
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "Species": st.column_config.LinkColumn(
                    "Species",
                    help="Click to view observations on MINKA",
                    display_text=r"taxon_name=([^&]+)",
                    width="medium",
                ),
                "Common Name": st.column_config.TextColumn(
                    "Common Name",
                    width="medium",
                ),
                "Select": st.column_config.CheckboxColumn(
                    "Map",
                    help="Select to view distribution",
                    default=False,
                ),
            },
            disabled=["Species", "Observations", "Common Name"],
            key=f"species_editor_{taxa_group}",
        )

        # Restore original species names for selection logic
        edited_df["Species"] = species_names.values

        # Find selected rows and determine if there's a new selection
        selected_rows = edited_df[edited_df["Select"] == True]
        selected_species_list = selected_rows["Species"].tolist()

        # Determine the newly selected species (single selection logic)
        new_selection = None
        if len(selected_species_list) == 0:
            # User deselected everything
            new_selection = None
        elif len(selected_species_list) == 1:
            # Single selection
            new_selection = selected_species_list[0]
        else:
            # Multiple selected - find the NEW one (not the previous selection)
            for species in selected_species_list:
                if species != prev_selected:
                    new_selection = species
                    break
            # If all selected were already selected (shouldn't happen), keep first
            if new_selection is None:
                new_selection = selected_species_list[0]

        # Update session state with the new selection
        selection_changed = new_selection != prev_selected

        if new_selection:
            selected_species = df_species[
                df_species["Species"] == new_selection
            ].iloc[0]

            # Guardar en session_state con key único
            st.session_state[key_species] = selected_species["Species"]
            st.session_state[key_lat] = selected_species["Lat"]
            st.session_state[key_lon] = selected_species["Lon"]
        else:
            st.session_state[key_species] = None

        # If selection changed, rerun fragment to update checkboxes
        if selection_changed:
            st.rerun(scope="fragment")

    with col_map:
        # Mostrar mapa si hay una especie seleccionada (usando key único)
        selected_species_name = st.session_state.get(key_species)
        selected_lat = st.session_state.get(key_lat)
        selected_lon = st.session_state.get(key_lon)

        if selected_species_name:
            st.markdown(f"#### Distribution of *{selected_species_name}*")

            # Filtrar observaciones de esa especie
            species_obs = df_taxa[
                df_taxa["taxon_name"] == selected_species_name
            ].dropna(subset=["latitude", "longitude"])

            st.caption(f"Total observations: {len(species_obs):,}")

            if len(species_obs) > 0:
                # Preparar datos para JavaScript (vectorizado)
                markers_data = species_obs[
                    [
                        "id",
                        "latitude",
                        "longitude",
                        "taxon_name",
                        "observed_on",
                        "user_login",
                    ]
                ].copy()
                markers_data.columns = ["id", "lat", "lng", "taxon", "date", "user"]
                markers_data["id"] = markers_data["id"].astype(int)
                markers_data["taxon"] = markers_data["taxon"].astype(str).str[:50]
                markers_data["date"] = markers_data["date"].astype(str)
                markers_data["user"] = markers_data["user"].fillna("N/A").astype(str)
                markers_data = markers_data.to_dict("records")

                # Crear mapa HTML con JavaScript
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                    <style>
                        html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
                        #map {{ height: 500px; width: 100%; }}
                    </style>
                </head>
                <body>
                    <div id="map"></div>
                    
                    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                    
                    <script>
                        var map = L.map('map').setView([{selected_lat}, {selected_lon}], 8);
                        
                        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '&copy; OpenStreetMap contributors',
                            maxZoom: 18
                        }}).addTo(map);
                        
                        var markerData = {json.dumps(markers_data)};
                        
                        // Añadir marcadores
                        markerData.forEach(function(point) {{
                            var marker = L.circleMarker([point.lat, point.lng], {{
                                radius: 5,
                                fillColor: "#00b6c4",
                                color: "#5953a5",
                                weight: 1,
                                opacity: 1,
                                fillOpacity: 0.8
                            }});
                            
                            marker.bindPopup(
                                '<b>Taxon:</b> ' + point.taxon +
                                '<br><b>Date:</b> ' + point.date +
                                '<br><b>Observer:</b> ' + point.user +
                                '<br><a href="{HOME_PATH}/observations/' + point.id + '" target="_blank">🔗 MINKA</a>'
                            );
                            
                            marker.addTo(map);
                        }});
                        
                        // Ajustar vista para mostrar todos los puntos
                        if (markerData.length > 0) {{
                            var bounds = L.latLngBounds(markerData.map(p => [p.lat, p.lng]));
                            map.fitBounds(bounds, {{ padding: [20, 20] }});
                        }}
                    </script>
                </body>
                </html>
                """

                # Mostrar mapa usando components.html
                st.components.v1.html(html_content, height=520)
            else:
                st.warning("No observations found")
        else:
            st.info("👈 Check a row to see the species distribution")


def create_slider(starting_date):
    # Resultados mensuales desde enero 2021
    fecha_actual = datetime.now()
    month_year = fecha_actual.strftime("%Y-%m")
    months = (
        pd.date_range(start=starting_date, end=datetime.now(), freq="MS")
        .strftime("%Y-%m")
        .tolist()
    )

    # Initialize session state for applied dates (only first time)
    # Usar formato "YYYY-MM" para el slider
    starting_month = STARTING_DATE[:7]  # "2021-01-01" -> "2021-01"
    if "applied_start_date" not in st.session_state:
        st.session_state.applied_start_date = starting_month
        st.session_state.applied_end_date = month_year

    # Use form to prevent reruns on slider change
    with st.form(key="date_filter_form"):
        col1, col2 = st.columns([5, 1])

        with col1:
            start_date, end_date = st.select_slider(
                "**Select temporal range to modify results (month included):**",
                options=months,
                value=(
                    st.session_state.applied_start_date,
                    st.session_state.applied_end_date,
                ),
            )

        with col2:
            st.write("")  # Spacing
            submitted = st.form_submit_button(
                "Apply", type="primary", use_container_width=True
            )

        if submitted:
            st.session_state.applied_start_date = start_date
            st.session_state.applied_end_date = end_date

    margin_dates = [
        st.session_state.applied_start_date,
        st.session_state.applied_end_date,
    ]
    return margin_dates


# Cached function for filtered observations
@st.cache_data(ttl=3600)
def get_filtered_observations(begin_date: str = None, end_date: str = None):
    """Get observations filtered by date range"""
    df = load_main_observations()
    if begin_date and end_date:
        df = df[
            (df["observed_on"] >= begin_date) & (df["observed_on"] <= end_date)
        ].reset_index(drop=True)
    return df


@st.cache_data(ttl=3600)
def get_species_filtered(begin_date: str, end_date: str, species_type: str):
    """Get protected or alien species filtered by date"""
    df_obs = get_filtered_observations(begin_date, end_date)
    df_csv = load_species_csv(f"species_{species_type}.csv")
    taxon_ids = set(df_csv.loc[df_csv.taxon_id.notnull(), "taxon_id"].unique())
    return df_obs[df_obs.taxon_id.isin(taxon_ids)].reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_species_by_category(begin_date: str, end_date: str, species_type: str):
    """Get species observations grouped by category"""
    df_obs = get_filtered_observations(begin_date, end_date)
    config = SPECIES_FILES[species_type]
    df_csv = load_species_csv(config["file"].replace("data/", ""))
    category_col = config["category_col"]

    # Get unique categories and their taxon_ids
    categories = {}
    for category in df_csv[category_col].dropna().unique():
        cat_taxon_ids = set(
            df_csv.loc[
                (df_csv[category_col] == category) & df_csv.taxon_id.notnull(),
                "taxon_id"
            ].unique()
        )
        # Filter observations for this category
        df_cat = df_obs[df_obs.taxon_id.isin(cat_taxon_ids)].reset_index(drop=True)
        if len(df_cat) > 0:
            # Translate category name
            translated = CATEGORY_TRANSLATIONS.get(category, category)
            categories[translated] = df_cat

    return categories


def create_species_section(species_type: str, begin_date: str, end_date: str, df_obs):
    """Create species section with tabs for each category"""
    config = SPECIES_FILES[species_type]

    st.subheader(f"🔍 {config['title']}")

    with st.spinner(f"Loading {config['title'].lower()}..."):
        categories = get_species_by_category(begin_date, end_date, species_type)

    if not categories:
        st.info(f"No {config['title'].lower()} observations found in this period.")
        return

    # Sort categories according to CATEGORY_ORDER
    order = CATEGORY_ORDER.get(species_type, [])
    sorted_categories = []
    for cat in order:
        if cat in categories:
            sorted_categories.append((cat, categories[cat]))
    # Add any categories not in the order list at the end
    for cat in categories:
        if cat not in order:
            sorted_categories.append((cat, categories[cat]))

    # Create tabs for each category
    tab_names = [cat for cat, _ in sorted_categories]
    tabs = st.tabs(tab_names)

    for tab, (category_name, df_category) in zip(tabs, sorted_categories):
        with tab:
            create_table_map(
                df_category,
                f"{species_type}_{category_name.lower().replace(' ', '_')}",
                df_obs=df_obs,
                show_title=False,
                begin_date=begin_date,
            )


# Main body

create_header()

margin_dates = create_slider(STARTING_DATE)

# Calculate date range
# Comparar con formato "YYYY-MM" del slider
starting_month = STARTING_DATE[:7]  # "2021-01-01" -> "2021-01"
if margin_dates[0] == starting_month and margin_dates[1] == datetime.now().strftime(
    "%Y-%m"
):
    show_main_metrics()
    begin_date = None
    end_date = None
else:
    # Convertir fechas de "YYYY-MM" a "YYYY-MM-DD" para la API
    begin_date = f"{margin_dates[0]}-01"
    end_month_date = datetime.strptime(f"{margin_dates[1]}-01", "%Y-%m-%d")
    end_date = (
        end_month_date + relativedelta(months=1) - relativedelta(days=1)
    ).strftime("%Y-%m-%d")
    show_main_metrics(start_date=begin_date, end_date=end_date)

# Get filtered data (cached)
df_obs = get_filtered_observations(begin_date, end_date)

# Sensitive species section (with tabs by category)
create_species_section("protected", begin_date, end_date, df_obs)

# Non-indigenous species section (with tabs by category)
create_species_section("exotic", begin_date, end_date, df_obs)
