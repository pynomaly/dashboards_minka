import os
import sys

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from utils import create_heatmap, create_markercluster, get_photo_url_from_taxon

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)

# Now import the rest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import create_footer, init_i18n, t

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 300px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 300px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize i18n
init_i18n(current_page="eada_contribution")
API_PATH = "https://api.minka-sdg.org/v1"
session = requests.Session()


# Funciones
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=3600, show_spinner=False)
def load_observations_data():
    """Carga datos de observaciones"""
    try:
        return pd.read_parquet(f"{directory}/data/eada/observations_eada.parquet")
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_total_metrics(df_accounts, proj_id, session=session):
    user_ids = df_accounts["user_id"].to_list()
    users_str = ",".join(user_ids)

    url1 = f"{API_PATH}/observations?project_id={proj_id}&user_id={users_str}&order=desc&order_by=created_at"
    url2 = f"{API_PATH}/observations/species_counts?project_id={proj_id}&user_id={users_str}"

    obs = session.get(url1).json()["total_results"]
    species = session.get(url2).json()["total_results"]
    ids = df_accounts["identifications_proj"].sum()

    return obs, species, ids


@st.cache_resource(ttl=3600, show_spinner=False)
def get_cached_maps(data_hash, _df):
    """Crea mapas con cache basado en hash de datos"""
    heatmap = create_heatmap(_df, center=[41.36174441599461, 2.108076037807884])
    markermap = create_markercluster(_df, center=[41.36174441599461, 2.108076037807884])
    return heatmap, markermap


# Load accounts data
@st.cache_data(ttl=3600, show_spinner=False)
def load_accounts_data():
    """Carga datos de cuentas EADA"""
    try:
        minka_accounts = pd.read_csv(f"{directory}/data/eada/minka_accounts.csv")
    except:
        minka_accounts = pd.DataFrame()
    return minka_accounts


# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.eada_title')}]")
        st.markdown("")
        st.markdown("")

# Total Contribution Metrics
with st.container():
    # Default values
    total_obs = 0
    total_species = 0
    total_ids = 0

    # Try to get metrics from API if accounts data is available
    accounts_df = load_accounts_data()
    if len(accounts_df) > 0 and "user_id" in accounts_df.columns:
        try:
            total_obs, total_species, total_ids = get_total_metrics(accounts_df, 264)
        except:
            pass

    __, col1, col2, col3, __ = st.columns(5)
    with col1:
        st.metric(label="**Total Observations**", value=total_obs)
    with col2:
        st.metric(label="**Total Species**", value=total_species)
    with col3:
        st.metric(label="**Total Identifications**", value=int(total_ids))

st.divider()

# Participation and Contribution Metrics
with st.container():
    st.header("Participation and Contribution Metrics")

    accounts_df = load_accounts_data()

    # Prepare dataframe with user, observations, identifications and species
    required_cols = [
        "user_name",
        "observations_proj",
        "identifications_proj",
        "species_proj",
    ]
    if len(accounts_df) > 0 and all(
        col in accounts_df.columns for col in required_cols
    ):
        observations_df = accounts_df[required_cols].copy()
        observations_df.columns = ["User", "Observations", "Identifications", "Species"]
        mean_observations = observations_df["Observations"].mean()
        mean_identifications = observations_df["Identifications"].mean()
        mean_species = observations_df["Species"].mean()
    else:
        observations_df = pd.DataFrame(
            columns=["User", "Observations", "Identifications", "Species"]
        )
        mean_observations = 0
        mean_identifications = 0
        mean_species = 0

    col_left, __, col_right = st.columns([3, 1, 3])

    with col_left:
        if len(observations_df) > 0:
            st.dataframe(
                observations_df.sort_values(by="Observations", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(
                observations_df,
                use_container_width=True,
                hide_index=True,
            )

    with col_right:
        st.metric(
            label=" **Average Observations** per User", value=f"{mean_observations:.2f}"
        )
        st.metric(
            label="**Average Identifications** per User",
            value=f"{mean_identifications:.2f}",
        )
        st.metric(label="**Average Species** per User", value=f"{mean_species:.2f}")

st.divider()

# Data Quality and Validation Metrics
with st.container():
    st.header("Data Quality and Validation Metrics")

    # Load observations data for peer interaction calculation
    obs_df_quality = load_observations_data()

    # Prepare dataframe with quality metrics
    required_quality_cols = [
        "user_id",
        "user_name",
        "research_obs",
        "observations_proj",
    ]
    if len(accounts_df) > 0 and all(
        col in accounts_df.columns for col in required_quality_cols
    ):
        quality_df = accounts_df[required_quality_cols].copy()
    else:
        quality_df = pd.DataFrame(columns=required_quality_cols)

    if len(quality_df) > 0:
        # Calculate Quality Rate (handle division by zero)
        quality_df["Quality Rate"] = quality_df.apply(
            lambda row: (
                f"{round((row['research_obs'] / row['observations_proj']) * 100, 2)}%"
                if row["observations_proj"] > 0
                else 0
            ),
            axis=1,
        )

        # Calculate Peer Interaction Rate from identifiers_id field
        def count_peer_identifications(user_id):
            """Count observations where this user appears in identifiers_id"""
            if "identifiers_id" not in obs_df_quality.columns:
                return 0
            count = 0
            for ids_list in obs_df_quality["identifiers_id"].dropna():
                if ids_list is not None and user_id in ids_list:
                    count += 1
            return count

        quality_df["peer_identifications"] = quality_df["user_id"].apply(
            count_peer_identifications
        )
        quality_df["peer_interaction_rate"] = quality_df.apply(
            lambda row: (
                round(row["peer_identifications"] / row["observations_proj"], 2)
                if row["observations_proj"] > 0
                else 0
            ),
            axis=1,
        )

        # Select and rename columns for display
        quality_display_df = quality_df[
            [
                "user_name",
                "research_obs",
                "Quality Rate",
                "peer_identifications",
                "peer_interaction_rate",
            ]
        ].copy()
        quality_display_df.columns = [
            "User",
            "Research Grade Obs.",
            "Quality Rate",
            "Peer Identifications",
            "Peer Interaction Rate",
        ]

        avg_research_obs = quality_df["research_obs"].sum() / len(quality_df)
        avg_peer_interaction = round(
            quality_df["peer_identifications"].sum() / len(accounts_df),
            2,
        )
    else:
        quality_display_df = pd.DataFrame(
            columns=[
                "User",
                "Research Grade Obs.",
                "Quality Rate",
                "Peer Identifications",
                "Peer Interaction Rate",
            ]
        )
        avg_research_obs = 0
        avg_peer_interaction = 0

    col_left, __, col_right = st.columns([3, 1, 3])

    with col_left:
        st.dataframe(
            quality_display_df,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            """
            * **Research Grade Obs.**: Number of observations that have reached validated or research-grade status.
            * **Quality Rate**: Ratio of research-grade observations to total observations.
            * **Peer Identifications**: Number of observations from other users that this user has identified.
            * **Peer Interaction Rate**: Ratio of peer identifications to the user's own observations.
            """
        )

    with col_right:
        st.metric(
            label="**Average Research Observations** per User",
            value=f"{avg_research_obs:.2f}",
        )
        st.metric(
            label="**Average Peer Interaction** per User",
            value=f"{avg_peer_interaction:.2f}",
        )

st.divider()


# Taxonomic Coverage Metrics
with st.container():
    st.header("Taxonomic Coverage Metrics")

    # Taxonomic groups mapping: taxon_id -> name
    taxon_groups = {
        12: "Plants",
        8: "Mammalia",
        5: "Aves",
        15: "Mollusca",
        3: "Actinopterygii",
        11: "Insecta",
        325: "Lepidoptera",
        326: "Hymenoptera",
        9: "Arachnida",
        6: "Reptilia",
        13: "Fungi",
    }

    col_left, col_right = st.columns([5, 2], gap="medium")

    with col_left:
        # Dataframe with taxonomic groups per user
        taxonomic_columns = ["user_name"] + list(taxon_groups.values())
        # Filter only existing columns
        available_columns = [
            col for col in taxonomic_columns if col in accounts_df.columns
        ]
        if len(available_columns) > 1 and len(accounts_df) > 0:
            taxonomic_df = accounts_df[available_columns].copy()
            taxonomic_df.columns = ["User"] + available_columns[1:]
        else:
            # Show empty table with headers
            taxonomic_df = pd.DataFrame(columns=["User"] + list(taxon_groups.values()))

        st.dataframe(
            taxonomic_df,
            use_container_width=True,
            hide_index=True,
            height=600,
        )

    with col_right:
        st.markdown("**Total Observations by Group**")

        # Calculate total observations per taxonomic group
        taxon_totals = []
        for taxon_id, taxon_name in taxon_groups.items():
            if len(accounts_df) > 0 and taxon_name in accounts_df.columns:
                total = accounts_df[taxon_name].sum()
            else:
                total = 0
            taxon_totals.append(
                {
                    "taxon_id": taxon_id,
                    "taxon_name": taxon_name,
                    "total": total,
                }
            )

        # Sort by total observations descending
        taxon_totals_df = pd.DataFrame(taxon_totals)
        taxon_totals_df = taxon_totals_df.sort_values(by="total", ascending=False)

        # Display metrics with links
        for _, row in taxon_totals_df.iterrows():
            taxon_id = row["taxon_id"]
            taxon_name = row["taxon_name"]
            total = int(row["total"])
            if taxon_id > 0:
                link = f"https://minka-sdg.org/taxa/{taxon_id}"
                st.markdown(f"- [**{taxon_name}**]({link}): {total} observations")
            else:
                st.markdown(f"- **{taxon_name}**: {total} observations")


# Most Observed Species Gallery
with st.container():
    st.subheader("10 Most Observed Species")

    obs_eada_df = load_observations_data()

    if len(obs_eada_df) > 0 and "taxon.name" in obs_eada_df.columns:
        # Filter only species rank and count observations
        species_only_df = obs_eada_df[obs_eada_df["taxon.rank"] == "species"]
        species_counts = (
            species_only_df.groupby(["taxon.name", "taxon.id"])
            .size()
            .reset_index(name="count")
        )
        top_species = species_counts.sort_values(by="count", ascending=False).head(10)

        # First row (5 species)
        cols = st.columns(5)
        for idx, (_, row) in enumerate(top_species.head(5).iterrows()):
            taxon_name = row["taxon.name"]
            taxon_id = int(row["taxon.id"])
            obs_count = int(row["count"])
            taxon_link = f"https://minka-sdg.org/taxa/{taxon_id}"
            photo_url = get_photo_url_from_taxon(taxon_id)

            with cols[idx]:
                st.markdown(f"[**{taxon_name}**]({taxon_link}) ({obs_count} obs.)")
                st.image(photo_url, use_container_width=True)

        # Second row (next 5 species)
        cols = st.columns(5)
        for idx, (_, row) in enumerate(top_species.tail(5).iterrows()):
            taxon_name = row["taxon.name"]
            taxon_id = int(row["taxon.id"])
            obs_count = int(row["count"])
            taxon_link = f"https://minka-sdg.org/taxa/{taxon_id}"
            photo_url = get_photo_url_from_taxon(taxon_id)

            with cols[idx]:
                st.markdown(f"[**{taxon_name}**]({taxon_link}) ({obs_count} obs.)")
                st.image(photo_url, use_container_width=True)
    else:
        st.info("No observation data available.")

st.divider()

# Newly Recorded Species Gallery
with st.container():
    st.subheader("Newly Recorded Species")
    st.markdown("5 species most recently added to the EADA observations dataset")

    if len(obs_eada_df) > 0 and "observed_on_details.date" in obs_eada_df.columns:
        # Find the first observation of each species (when it was first recorded)
        first_records = obs_eada_df.sort_values(
            by="observed_on_details.date"
        ).drop_duplicates(subset=["taxon.name"], keep="first")
        # Sort by date descending to get the most recently added species
        new_species = first_records.sort_values(
            by="observed_on_details.date", ascending=False
        ).head(5)

        cols = st.columns(5)
        for idx, (_, row) in enumerate(new_species.iterrows()):
            taxon_name = row.get("taxon.name", "Unknown")
            obs_id = int(row["id"])
            obs_link = f"https://minka-sdg.org/observations/{obs_id}"

            # Extract photo URL and attribution from photos field
            photos = row.get("photos", None)
            if photos is not None and len(photos) > 0:
                photo_url = photos[0].get("url", "")
                # Use medium size instead of square
                photo_url = photo_url.replace("/square.", "/medium.")
                attribution = photos[0].get("attribution", "")
            else:
                photo_url = ""
                attribution = ""

            with cols[idx]:
                st.markdown(f"[**{taxon_name}**]({obs_link})")
                if photo_url:
                    st.image(photo_url, use_container_width=True)
                else:
                    st.markdown("*No photo available*")
                if attribution:
                    st.caption(attribution)
    else:
        st.info("No observation data available.")

st.divider()


# Temporal Distribution Metrics
with st.container():
    st.header("Temporal Distribution Metrics")

    if len(obs_eada_df) > 0 and "observed_on_details.date" in obs_eada_df.columns:
        # Prepare temporal data
        temporal_df = obs_eada_df.copy()
        temporal_df["date"] = pd.to_datetime(temporal_df["observed_on_details.date"])

        # Filter from 25/02/2026 to today
        start_date = pd.Timestamp("2026-02-25")
        end_date = pd.Timestamp.today()
        temporal_df = temporal_df[
            (temporal_df["date"] >= start_date) & (temporal_df["date"] <= end_date)
        ]

        if len(temporal_df) > 0:
            # Chart 1: Total observations over time with aggregation selector
            st.subheader("Total Observations Over Time")

            aggregation = st.selectbox(
                "Aggregation",
                options=["Daily", "Weekly", "Monthly"],
                index=0,
                key="aggregation_total",
            )

            # Aggregate data based on selection
            if aggregation == "Daily":
                obs_by_time = (
                    temporal_df.groupby(temporal_df["date"].dt.date)
                    .size()
                    .reset_index(name="observations")
                )
                obs_by_time.columns = ["date", "observations"]
            elif aggregation == "Weekly":
                temporal_df["week"] = (
                    temporal_df["date"].dt.to_period("W").dt.start_time
                )
                obs_by_time = (
                    temporal_df.groupby("week").size().reset_index(name="observations")
                )
                obs_by_time.columns = ["date", "observations"]
            else:  # Monthly
                temporal_df["month"] = (
                    temporal_df["date"].dt.to_period("M").dt.start_time
                )
                obs_by_time = (
                    temporal_df.groupby("month").size().reset_index(name="observations")
                )
                obs_by_time.columns = ["date", "observations"]

            fig1 = px.area(
                obs_by_time,
                x="date",
                y="observations",
                labels={"date": "Date", "observations": "Observations"},
            )
            fig1.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Observations",
                hovermode="x unified",
                yaxis=dict(rangemode="tozero"),
                xaxis=dict(range=[start_date, end_date]),
            )
            st.plotly_chart(fig1, use_container_width=True)

            st.divider()

            # Chart 2: Observations by user over time
            st.subheader("Observations by User Over Time")

            # Get unique users
            if "user.login" in temporal_df.columns:
                users = sorted(temporal_df["user.login"].dropna().unique().tolist())
                col_selector, _ = st.columns([1, 3])
                with col_selector:
                    selected_user = st.selectbox(
                        "Select User",
                        options=["All Users"] + users,
                        index=0,
                        key="user_selector",
                    )

                # Filter by user if selected
                if selected_user != "All Users":
                    user_temporal_df = temporal_df[
                        temporal_df["user.login"] == selected_user
                    ]
                else:
                    user_temporal_df = temporal_df

                # Group by date and user
                obs_by_user = (
                    user_temporal_df.groupby(
                        [user_temporal_df["date"].dt.date, "user.login"]
                    )
                    .size()
                    .reset_index(name="observations")
                )
                obs_by_user.columns = ["date", "user", "observations"]

                if selected_user == "All Users":
                    # Get top 10 users by total observations
                    user_totals = (
                        obs_by_user.groupby("user")["observations"]
                        .sum()
                        .sort_values(ascending=False)
                    )
                    top_users = user_totals.head(10).index.tolist()

                    # Filter data to include only top 10 users
                    obs_by_user_filtered = obs_by_user[
                        obs_by_user["user"].isin(top_users)
                    ]

                    # Calculate daily totals for hover title
                    daily_totals = (
                        obs_by_user_filtered.groupby("date")["observations"]
                        .sum()
                        .reset_index()
                    )
                    daily_totals.columns = ["date", "total"]

                    # Add total column to filtered data for hover
                    obs_by_user_filtered = obs_by_user_filtered.merge(
                        daily_totals, on="date", how="left"
                    )

                    # Stacked area chart for top users
                    fig2 = px.area(
                        obs_by_user_filtered,
                        x="date",
                        y="observations",
                        color="user",
                        category_orders={"user": top_users},
                        labels={
                            "date": "Date",
                            "observations": "Observations",
                            "user": "User",
                        },
                        custom_data=["total"],
                    )
                else:
                    # Fill missing dates with 0 for single user
                    all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
                    all_dates_df = pd.DataFrame({"date": all_dates.date})
                    obs_by_user = all_dates_df.merge(
                        obs_by_user[["date", "observations"]], on="date", how="left"
                    ).fillna(0)
                    obs_by_user["observations"] = obs_by_user["observations"].astype(
                        int
                    )

                    # Area chart for single user
                    fig2 = px.area(
                        obs_by_user,
                        x="date",
                        y="observations",
                        labels={"date": "Date", "observations": "Observations"},
                    )

                fig2.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Observations",
                    hovermode="x unified",
                    legend_title="User",
                )
                # Update hover to show user and observations, with total in header
                fig2.update_traces(
                    hovertemplate="%{fullData.name}: %{y}<extra></extra>"
                )
                # Update x-axis hover format to include total
                fig2.update_layout(
                    xaxis=dict(
                        hoverformat="%Y-%m-%d",
                    ),
                )
                # Add invisible trace for total that appears first in hover
                if selected_user == "All Users":
                    fig2.add_scatter(
                        x=daily_totals["date"],
                        y=[0] * len(daily_totals),
                        mode="markers",
                        marker=dict(size=0, opacity=0),
                        name="Total",
                        hovertemplate="Total: %{customdata[0]}<extra></extra>",
                        customdata=daily_totals[["total"]].values,
                        showlegend=False,
                    )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("User data not available.")
        else:
            st.info("No observations found in the selected date range.")
    else:
        st.info("No temporal data available.")

st.divider()


# Learning and Engagement Indicators
with st.container():
    st.header("Learning and Engagement Indicators")

    if len(obs_eada_df) > 0 and "non_owner_ids" in obs_eada_df.columns:
        # Calculate response time for each observation
        response_times = []

        for _, row in obs_eada_df.iterrows():
            non_owner_ids = row.get("non_owner_ids", None)
            created_at = row.get("created_at", None)

            if (
                non_owner_ids is not None
                and len(non_owner_ids) > 0
                and created_at is not None
            ):
                # Get first identification timestamp
                first_id = non_owner_ids[0]
                if isinstance(first_id, dict) and "created_at" in first_id:
                    first_id_time = pd.to_datetime(first_id["created_at"])
                    obs_created = pd.to_datetime(created_at)

                    # Calculate time difference in hours
                    time_diff = (first_id_time - obs_created).total_seconds() / 3600
                    if (
                        time_diff >= 0
                    ):  # Only positive values (identification after creation)
                        response_times.append(
                            {
                                "observation_id": row.get("id", None),
                                "response_time_hours": time_diff,
                                "created_at": obs_created,
                            }
                        )

        if len(response_times) > 0:
            response_df = pd.DataFrame(response_times)

            # Calculate average response time
            avg_response_hours = response_df["response_time_hours"].mean()
            median_response_hours = response_df["response_time_hours"].median()

            # Convert to days/hours/minutes for display
            def format_time(hours):
                """Format hours as days/hours/minutes"""
                if hours >= 24:
                    days = int(hours // 24)
                    remaining_hours = int(hours % 24)
                    remaining_minutes = int((hours % 1) * 60)
                    if remaining_hours > 0:
                        return f"{days}d {remaining_hours}h {remaining_minutes}m"
                    else:
                        return f"{days}d {remaining_minutes}m"
                else:
                    h = int(hours)
                    m = int((hours - h) * 60)
                    return f"{h}h {m}m"

            avg_display = format_time(avg_response_hours)
            median_display = format_time(median_response_hours)

            # Calculate percentage of observations with IDs
            total_observations = len(obs_eada_df)
            obs_with_ids_pct = (
                (len(response_times) / total_observations * 100)
                if total_observations > 0
                else 0
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="**Average Response Time**",
                    value=avg_display,
                    help="Average time from observation upload to first identification",
                )
            with col2:
                st.metric(
                    label="**Median Response Time**",
                    value=median_display,
                    help="Median time from observation upload to first identification",
                )
            with col3:
                st.metric(
                    label="**Observations with IDs**",
                    value=f"{len(response_times)}",
                    help="Number of observations that received at least one identification",
                )
            with col4:
                st.metric(
                    label="**% Observations with IDs**",
                    value=f"{obs_with_ids_pct:.1f}%",
                    help="Percentage of observations that received at least one identification",
                )

            st.caption(
                """
                * **Response Time**: Time elapsed from when an observation is uploaded until it receives its first identification from another user.
                """
            )
        else:
            # Show 0 metrics when no identification data
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="**Average Response Time**", value="0 hours")
            with col2:
                st.metric(label="**Median Response Time**", value="0 hours")
            with col3:
                st.metric(label="**Observations with IDs**", value="0")
            with col4:
                st.metric(label="**% Observations with IDs**", value="0.0%")
    else:
        # Show 0 metrics when no data available
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="**Average Response Time**", value="0 hours")
        with col2:
            st.metric(label="**Median Response Time**", value="0 hours")
        with col3:
            st.metric(label="**Observations with IDs**", value="0")
        with col4:
            st.metric(label="**% Observations with IDs**", value="0.0%")

st.divider()


# Spatial Distribution Metrics
with st.container():
    st.header("Spatial Distribution Metrics")

    if len(obs_eada_df) == 0:
        st.info("No observation data available for mapping.")
    elif "geojson.coordinates" in obs_eada_df.columns:
        # Prepare dataframe with latitude and longitude from geojson.coordinates
        map_df = obs_eada_df.copy()
        # Extract latitude and longitude from geojson.coordinates [lon, lat]
        map_df["longitude"] = map_df["geojson.coordinates"].apply(
            lambda x: x[0] if x is not None and len(x) >= 2 else None
        )
        map_df["latitude"] = map_df["geojson.coordinates"].apply(
            lambda x: x[1] if x is not None and len(x) >= 2 else None
        )
        map_df = map_df.dropna(subset=["latitude", "longitude"])

        # Rename columns to match expected format for create_markercluster
        if "taxon.name" in map_df.columns:
            map_df["taxon_name"] = map_df["taxon.name"]
        if "user.login" in map_df.columns:
            map_df["user_login"] = map_df["user.login"]

        if len(map_df) > 0:
            map1, map2 = st.columns([10, 10], gap="small")

            # Calculate center from actual data
            center_lat = map_df["latitude"].mean()
            center_lon = map_df["longitude"].mean()

            data_hash = hash(
                str(map_df.shape) + str(map_df["id"].iloc[0] if len(map_df) > 0 else "")
            )
            heatmap = create_heatmap(map_df, center=[center_lat, center_lon])
            markermap = create_markercluster(map_df, center=[center_lat, center_lon])

            with map1:
                st.markdown("**Heatmap**")
                map_html1 = heatmap._repr_html_()
                components.html(map_html1, height=600)

            with map2:
                st.markdown("**Marker Map**")
                map_html2 = markermap._repr_html_()
                components.html(map_html2, height=600)

        else:
            st.info("No location data available for mapping.")
    else:
        st.info("Geolocation data not available.")

# Footer
create_footer()
