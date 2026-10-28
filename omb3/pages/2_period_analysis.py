import os
import sys

import streamlit as st

# Set page config FIRST before any other Streamlit-related imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    directory = f"{os.environ['DASHBOARDS']}/omb3"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        /* Equal height for metric cards */
        [data-testid="stMetric"] {{
            min-height: 100px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Now import everything else (after set_page_config)
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from config import (
    API_PATH,
    COLORS,
    HEADER_LOGO,
    HEADER_TITLE,
    MAIN_PLACE,
)
from streamlit_extras.metric_cards import style_metric_cards

SESSION = requests.Session()


@st.cache_data(ttl=3600)
def load_observations():
    """Load observations CSV with caching"""
    return pd.read_csv(f"{directory}/data/df_obs_catalunya.csv")


def create_header():
    with st.container():
        # Título
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(f"{directory}/images/{HEADER_LOGO}")
        with col2:
            st.header(HEADER_TITLE)


def create_period_comparisson():
    """Create period selection form - returns (periods_dict, form_submitted)"""
    with st.form("comparison_form"):
        __, col1, __, col2, __ = st.columns([0.5, 3, 1, 3, 0.5])

        with col1:
            st.markdown("#### Period 1 to compare")
            col11, col12 = st.columns(2)
            with col11:
                year1 = st.text_input(
                    "Insert a year (YYYY)",
                    value="",
                    max_chars=4,
                )
            with col12:
                month1 = st.text_input(
                    "Insert a month (MM)",
                    value="",
                    max_chars=2,
                )

        with col2:
            st.markdown("#### Period 2 to compare")
            col21, col22 = st.columns(2)
            with col21:
                year2 = st.text_input(
                    "Insert a year",
                    value="",
                    max_chars=4,
                    key="year2_input",
                )
            with col22:
                month2 = st.text_input(
                    "Insert a month",
                    value="",
                    max_chars=2,
                    key="month2_input",
                )

        # Submit button centered
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submitted = st.form_submit_button(
                "🔍 Compare",
                type="primary",
                use_container_width=True,
            )

    # Parse values after form
    year1 = int(year1) if year1 != "" else None
    month1 = int(month1) if month1 != "" else None
    year2 = int(year2) if year2 != "" else None
    month2 = int(month2) if month2 != "" else None

    period_to_compare = {
        "year1": year1,
        "month1": month1,
        "year2": year2,
        "month2": month2,
    }

    return period_to_compare, submitted


@st.cache_data(ttl=3600)
def get_period_metrics(year, month):
    """Get metrics for a specific year-month period"""
    if year is None:
        return None

    # Build date range (d2 is exclusive in the API)
    if month:
        start_date = f"{year}-{month:02d}-01"
        # Calculate first day of next month
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
    else:
        # Full year - end is first day of next year
        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

    # Only include d2 if end_date is not in the future
    today = datetime.now().strftime("%Y-%m-%d")
    d2_param = f"&d2={end_date}" if end_date <= today else ""

    urls = {
        "observations": f"{API_PATH}/observations?place_id={MAIN_PLACE}&d1={start_date}{d2_param}&verifiable=true",
        "species": f"{API_PATH}/observations/species_counts?place_id={MAIN_PLACE}&d1={start_date}{d2_param}&verifiable=true",
        "observers": f"{API_PATH}/observations/observers?place_id={MAIN_PLACE}&d1={start_date}{d2_param}&verifiable=true",
        "identifiers": f"{API_PATH}/observations/identifiers?place_id={MAIN_PLACE}&d1={start_date}{d2_param}&verifiable=true",
    }

    results = {"period": f"{year}-{month:02d}" if month else str(year)}

    for key, url in urls.items():
        try:
            response = SESSION.get(url, timeout=10)
            data = response.json()
            results[key] = data.get("total_results", 0)

            # Sum identification counts from identifiers response
            if key == "identifiers" and "results" in data:
                total_identifications = sum(r.get("count", 0) for r in data["results"])
                results["identifications"] = total_identifications
        except Exception as e:
            results[key] = 0

    return results


@st.cache_data(ttl=3600)
def get_period_species_list(year, month):
    """Get list of species for a period"""
    if year is None:
        return set()

    if month:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

    # Filter local CSV for species
    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ]
    return set(df_filtered["taxon_name"].dropna().unique())


def show_comparison_metrics(metrics1, metrics2):
    """Display metrics comparison with deltas"""
    if not metrics1 or not metrics2:
        st.warning("Please enter both periods to compare")
        return

    st.markdown("### 📊 Main metrics comparison")

    col1, col2, col3, col4, col5 = st.columns(5)

    metric_keys = ["observations", "species", "observers", "identifiers"]
    metric_labels = ["Observations", "Species", "Observers", "Identifiers"]
    cols = [col1, col2, col3, col4]

    for col, key, label in zip(cols, metric_keys, metric_labels):
        with col:
            val1 = metrics1.get(key, 0)
            val2 = metrics2.get(key, 0)
            delta = val2 - val1
            delta_pct = (delta / val1 * 100) if val1 > 0 else 0

            st.metric(
                label=f"{label}",
                value=f"{val2:,}",
                delta=f"{delta:+,} ({delta_pct:+.1f}%)",
                delta_color="normal",
            )

    # Average identifications per observation (community engagement)
    with col5:
        obs1 = metrics1.get("observations", 0)
        obs2 = metrics2.get("observations", 0)
        ids1 = metrics1.get("identifications", 0)
        ids2 = metrics2.get("identifications", 0)

        avg1 = ids1 / obs1 if obs1 > 0 else 0
        avg2 = ids2 / obs2 if obs2 > 0 else 0
        delta = avg2 - avg1

        st.metric(
            label="Avg. IDs. per Obs.",
            value=f"{avg2:.2f}",
            delta=f"{delta:+.2f}",
            delta_color="normal",
            help="Community engagement: average identifications per observation (excl. self-identifications)",
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color=COLORS[3],
        box_shadow=False,
    )


@st.cache_data(ttl=3600)
def get_quality_grade_stats(year, month):
    """Get quality grade statistics for a period"""
    if year is None:
        return None

    if month:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ]

    if df_filtered.empty:
        return {
            "research": 0,
            "needs_id": 0,
            "casual": 0,
            "total": 0,
            "research_pct": 0,
        }

    total = len(df_filtered)
    research = len(df_filtered[df_filtered["quality_grade"] == "research"])
    needs_id = len(df_filtered[df_filtered["quality_grade"] == "needs_id"])
    casual = len(df_filtered[df_filtered["quality_grade"] == "casual"])

    return {
        "research": research,
        "needs_id": needs_id,
        "casual": casual,
        "total": total,
        "research_pct": round(research / total * 100, 1) if total > 0 else 0,
    }


def show_quality_comparison(year1, month1, year2, month2):
    """Show quality grade comparison between periods"""
    if year1 is None or year2 is None:
        return

    stats1 = get_quality_grade_stats(year1, month1)
    stats2 = get_quality_grade_stats(year2, month2)

    if not stats1 or not stats2:
        return

    st.markdown("### 🔬 Research grade comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        delta_pct = stats2["research_pct"] - stats1["research_pct"]
        st.metric(
            "Research Grade %",
            f"{stats2['research_pct']}%",
            f"{delta_pct:+.1f}%",
            delta_color="normal",
        )

    with col2:
        delta = stats2["research"] - stats1["research"]
        st.metric("Research Grade Obs", f"{stats2['research']:,}", f"{delta:+,}")

    with col3:
        delta = stats2["needs_id"] - stats1["needs_id"]
        st.metric(
            "Needs ID Obs",
            f"{stats2['needs_id']:,}",
            f"{delta:+,}",
            delta_color="inverse",
        )

    # Donut charts comparison
    col1, col2 = st.columns(2)

    # Explicit order: Research -> Needs ID -> Casual
    grade_labels = ["Research", "Needs ID", "Casual"]
    grade_colors = [COLORS[4], COLORS[3], COLORS[1]]  # #5953a5, #00b6c4, #FBD1A2

    with col1:
        period1_label = f"{year1}" + (f"-{month1:02d}" if month1 else "")
        values1 = [stats1["research"], stats1["needs_id"], stats1["casual"]]

        fig1 = go.Figure(
            data=[
                go.Pie(
                    labels=grade_labels,
                    values=values1,
                    hole=0.5,
                    marker=dict(colors=grade_colors),
                    textposition="auto",
                    textinfo="percent+label",
                    textfont=dict(size=16),
                    insidetextorientation="horizontal",
                    sort=False,
                    direction="clockwise",
                )
            ]
        )
        fig1.update_layout(
            title=f"Period: {period1_label}",
            showlegend=False,
            margin=dict(t=100, b=50, l=80, r=80),
            height=480,
            annotations=[
                dict(
                    text="Total observations:",
                    x=0.5,
                    y=0.55,
                    font_size=14,
                    showarrow=False,
                ),
                dict(
                    text=f"{stats1['total']:,}",
                    x=0.5,
                    y=0.45,
                    font_size=16,
                    font=dict(weight="bold"),
                    showarrow=False,
                ),
            ],
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        period2_label = f"{year2}" + (f"-{month2:02d}" if month2 else "")
        values2 = [stats2["research"], stats2["needs_id"], stats2["casual"]]

        fig2 = go.Figure(
            data=[
                go.Pie(
                    labels=grade_labels,
                    values=values2,
                    hole=0.5,
                    marker=dict(colors=grade_colors),
                    textposition="auto",
                    textinfo="percent+label",
                    textfont=dict(size=16),
                    insidetextorientation="horizontal",
                    sort=False,
                    direction="clockwise",
                )
            ]
        )
        fig2.update_layout(
            title=f"Period: {period2_label}",
            showlegend=False,
            margin=dict(t=100, b=50, l=80, r=80),
            height=480,
            annotations=[
                dict(
                    text="Total observations:",
                    x=0.5,
                    y=0.55,
                    font_size=14,
                    showarrow=False,
                ),
                dict(
                    text=f"{stats2['total']:,}",
                    x=0.5,
                    y=0.45,
                    font_size=16,
                    font=dict(weight="bold"),
                    showarrow=False,
                ),
            ],
        )
        st.plotly_chart(fig2, use_container_width=True)


def show_new_species(year1, month1, year2, month2):
    """Show species comparison between periods"""
    if year1 is None or year2 is None:
        return

    species1 = get_period_species_list(year1, month1)
    species2 = get_period_species_list(year2, month2)

    new_species = species2 - species1
    lost_species = species1 - species2
    common_species = species1 & species2

    st.markdown("### 🦋 Species analysis")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Species in Period 1", f"{len(species1):,}")
    with col2:
        st.metric("Species in Period 2", f"{len(species2):,}")
    with col3:
        st.metric("🆕 New in Period 2", f"{len(new_species):,}", delta_color="normal")
    with col4:
        st.metric("❌ Not in Period 2", f"{len(lost_species):,}", delta_color="inverse")

    # Download buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if new_species:
            df_new = pd.DataFrame({"Species": sorted(new_species)})
            st.download_button(
                "📥 Download new species list",
                df_new.to_csv(index=False),
                file_name="new_species.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col2:
        if lost_species:
            df_lost = pd.DataFrame({"Species": sorted(lost_species)})
            st.download_button(
                "📥 Download lost species list",
                df_lost.to_csv(index=False),
                file_name="lost_species.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col3:
        if common_species:
            df_common = pd.DataFrame({"Species": sorted(common_species)})
            st.download_button(
                "📥 Download common species list",
                df_common.to_csv(index=False),
                file_name="common_species.csv",
                mime="text/csv",
                use_container_width=True,
            )


@st.cache_data(ttl=3600)
def get_period_observers_list(year, month):
    """Get list of observer usernames for a period"""
    if year is None:
        return set()

    if month:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ]
    return set(df_filtered["user_login"].dropna().unique())


@st.cache_data(ttl=3600)
def get_top_contributors(year, month, limit=10):
    """Get top contributors with observation counts for a period"""
    if year is None:
        return pd.DataFrame()

    if month:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ]

    if df_filtered.empty:
        return pd.DataFrame()

    top = (
        df_filtered.groupby("user_login")
        .size()
        .reset_index(name="observations")
        .sort_values("observations", ascending=False)
        .head(limit)
    )
    top["rank"] = range(1, len(top) + 1)
    return top


def show_participation_comparison(year1, month1, year2, month2):
    """Show participation comparison between periods"""
    if year1 is None or year2 is None:
        return

    observers1 = get_period_observers_list(year1, month1)
    observers2 = get_period_observers_list(year2, month2)

    new_observers = observers2 - observers1
    recurring_observers = observers1 & observers2

    # Get observations for avg calculation
    df_obs = load_observations()

    # Period 1 stats
    if month1:
        start1 = f"{year1}-{month1:02d}-01"
        end1 = f"{year1}-{month1+1:02d}-01" if month1 < 12 else f"{year1+1}-01-01"
    else:
        start1 = f"{year1}-01-01"
        end1 = f"{year1+1}-01-01"

    # Period 2 stats
    if month2:
        start2 = f"{year2}-{month2:02d}-01"
        end2 = f"{year2}-{month2+1:02d}-01" if month2 < 12 else f"{year2+1}-01-01"
    else:
        start2 = f"{year2}-01-01"
        end2 = f"{year2+1}-01-01"

    df1 = df_obs[(df_obs["observed_on"] >= start1) & (df_obs["observed_on"] < end1)]
    df2 = df_obs[(df_obs["observed_on"] >= start2) & (df_obs["observed_on"] < end2)]

    obs_count1 = len(df1)
    obs_count2 = len(df2)
    observer_count1 = len(observers1)
    observer_count2 = len(observers2)

    avg_obs1 = obs_count1 / observer_count1 if observer_count1 > 0 else 0
    avg_obs2 = obs_count2 / observer_count2 if observer_count2 > 0 else 0

    st.markdown("### 🤝 Participation")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        delta_observers = observer_count2 - observer_count1
        st.metric(
            "Observers",
            f"{observer_count2:,}",
            delta=f"{delta_observers:+,}",
            delta_color="normal",
            help="Total unique observers in Period 2",
        )

    with col2:
        st.metric(
            "New Observers",
            f"{len(new_observers):,}",
            help="People who contributed in Period 2 but not in Period 1",
        )

    with col3:
        st.metric(
            "Recurring Observers",
            f"{len(recurring_observers):,}",
            help="People active in both periods",
        )

    with col4:
        delta = avg_obs2 - avg_obs1
        st.metric(
            "Avg. Obs. per Observer",
            f"{avg_obs2:.1f}",
            delta=f"{delta:+.1f}",
            delta_color="normal",
            help="Individual productivity: observations per observer",
        )

    with col5:
        retention = (
            len(recurring_observers) / len(observers1) * 100
            if len(observers1) > 0
            else 0
        )
        st.metric(
            "Observer Retention",
            f"{retention:.1f}%",
            help="Percentage of Period 1 observers who also contributed in Period 2",
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color=COLORS[3],
        box_shadow=False,
    )

    # Top contributors comparison
    st.markdown("#### Top 10 Contributors")

    top1 = get_top_contributors(year1, month1)
    top2 = get_top_contributors(year2, month2)

    period1_label = f"{year1}" + (f"-{month1:02d}" if month1 else "")
    period2_label = f"{year2}" + (f"-{month2:02d}" if month2 else "")

    col1, __, col2, __ = st.columns([3, 1, 3, 2])

    column_config = {
        "#": st.column_config.NumberColumn(width=50),
    }

    with col1:
        st.markdown(f"**Period: {period1_label}**")
        if not top1.empty:
            display_df1 = top1[["rank", "user_login", "observations"]].copy()
            display_df1.columns = ["#", "Observer", "Observations"]
            st.dataframe(
                display_df1,
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
            )
        else:
            st.info("No data available")

    with col2:
        st.markdown(f"**Period: {period2_label}**")
        if not top2.empty:
            display_df2 = top2[["rank", "user_login", "observations"]].copy()
            display_df2.columns = ["#", "Observer", "Observations"]
            st.dataframe(
                display_df2,
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
            )
        else:
            st.info("No data available")


def show_temporal_comparison(year1, month1, year2, month2):
    """Show temporal patterns comparison between periods"""
    if year1 is None or year2 is None:
        return

    df_obs = load_observations()
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])

    # Period 1 filter
    if month1:
        start1 = f"{year1}-{month1:02d}-01"
        end1 = f"{year1}-{month1+1:02d}-01" if month1 < 12 else f"{year1+1}-01-01"
    else:
        start1 = f"{year1}-01-01"
        end1 = f"{year1+1}-01-01"

    # Period 2 filter
    if month2:
        start2 = f"{year2}-{month2:02d}-01"
        end2 = f"{year2}-{month2+1:02d}-01" if month2 < 12 else f"{year2+1}-01-01"
    else:
        start2 = f"{year2}-01-01"
        end2 = f"{year2+1}-01-01"

    df1 = df_obs[
        (df_obs["observed_on"] >= start1) & (df_obs["observed_on"] < end1)
    ].copy()
    df2 = df_obs[
        (df_obs["observed_on"] >= start2) & (df_obs["observed_on"] < end2)
    ].copy()

    # Calculate days in each period
    days1 = (pd.to_datetime(end1) - pd.to_datetime(start1)).days
    days2 = (pd.to_datetime(end2) - pd.to_datetime(start2)).days

    # Average daily observations
    avg_daily1 = len(df1) / days1 if days1 > 0 else 0
    avg_daily2 = len(df2) / days2 if days2 > 0 else 0

    # Most active day of week
    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    if not df1.empty:
        df1["day_of_week"] = df1["observed_on"].dt.dayofweek
        day_counts1 = df1["day_of_week"].value_counts()
        most_active_day1 = day_names[day_counts1.idxmax()]
        most_active_count1 = day_counts1.max()
    else:
        most_active_day1 = "-"
        most_active_count1 = 0

    if not df2.empty:
        df2["day_of_week"] = df2["observed_on"].dt.dayofweek
        day_counts2 = df2["day_of_week"].value_counts()
        most_active_day2 = day_names[day_counts2.idxmax()]
        most_active_count2 = day_counts2.max()
    else:
        most_active_day2 = "-"
        most_active_count2 = 0

    st.markdown("### 📅 Temporal patterns")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_daily = avg_daily2 - avg_daily1
        st.metric(
            "Avg. Daily Obs.",
            f"{avg_daily2:.1f}",
            delta=f"{delta_daily:+.1f}",
            delta_color="normal",
            help="Sampling intensity: average observations per day",
        )

    with col2:
        st.metric(
            "Most Active Day (P2)",
            most_active_day2,
            help="Day of the week with most observations in Period 2",
        )

    with col3:
        st.metric(
            "Most Active Day (P1)",
            most_active_day1,
            help="Day of the week with most observations in Period 1",
        )

    with col4:
        # Active days (days with at least one observation)
        active_days1 = df1["observed_on"].dt.date.nunique() if not df1.empty else 0
        active_days2 = df2["observed_on"].dt.date.nunique() if not df2.empty else 0
        coverage1 = active_days1 / days1 * 100 if days1 > 0 else 0
        coverage2 = active_days2 / days2 * 100 if days2 > 0 else 0
        delta_coverage = coverage2 - coverage1
        st.metric(
            "Day Coverage",
            f"{coverage2:.1f}%",
            delta=f"{delta_coverage:+.1f}%",
            delta_color="normal",
            help="Percentage of days with at least one observation",
        )

    style_metric_cards(
        background_color="#fff",
        border_left_color=COLORS[3],
        box_shadow=False,
    )


@st.cache_data(ttl=3600)
def get_monthly_evolution(year):
    """Get monthly counts for a full year"""
    if year is None:
        return pd.DataFrame()

    start_date = f"{year}-01-01"
    end_date = f"{year+1}-01-01"

    # Filter observations for the year
    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ].copy()

    if df_filtered.empty:
        return pd.DataFrame()

    # Convert to datetime for resampling
    df_filtered["observed_on"] = pd.to_datetime(df_filtered["observed_on"])

    # Monthly aggregations
    monthly_obs = (
        df_filtered.set_index("observed_on")
        .resample("ME")
        .size()
        .reset_index(name="observations")
    )
    monthly_species = (
        df_filtered.set_index("observed_on")
        .resample("ME")["taxon_name"]
        .nunique()
        .reset_index(name="species")
    )
    monthly_observers = (
        df_filtered.set_index("observed_on")
        .resample("ME")["user_login"]
        .nunique()
        .reset_index(name="observers")
    )

    # Merge all
    monthly = monthly_obs.merge(monthly_species, on="observed_on").merge(
        monthly_observers, on="observed_on"
    )
    monthly["month"] = monthly["observed_on"].dt.month
    monthly["month_name"] = monthly["observed_on"].dt.strftime("%b")
    monthly["year"] = year

    return monthly


@st.cache_data(ttl=3600)
def get_daily_evolution(year, month):
    """Get daily counts for a specific month"""
    if year is None or month is None:
        return pd.DataFrame()

    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year}-12-31"
    else:
        end_date = f"{year}-{month+1:02d}-01"

    # Filter observations for the month
    df_obs = load_observations()
    df_filtered = df_obs[
        (df_obs["observed_on"] >= start_date) & (df_obs["observed_on"] < end_date)
    ].copy()

    if df_filtered.empty:
        return pd.DataFrame()

    # Convert to datetime for resampling
    df_filtered["observed_on"] = pd.to_datetime(df_filtered["observed_on"])

    # Daily aggregations
    daily_obs = (
        df_filtered.set_index("observed_on")
        .resample("D")
        .size()
        .reset_index(name="observations")
    )
    daily_species = (
        df_filtered.set_index("observed_on")
        .resample("D")["taxon_name"]
        .nunique()
        .reset_index(name="species")
    )
    daily_observers = (
        df_filtered.set_index("observed_on")
        .resample("D")["user_login"]
        .nunique()
        .reset_index(name="observers")
    )

    # Merge all
    daily = daily_obs.merge(daily_species, on="observed_on").merge(
        daily_observers, on="observed_on"
    )
    daily["day"] = daily["observed_on"].dt.day
    daily["day_label"] = daily["observed_on"].dt.strftime("%d")
    daily["period"] = f"{year}-{month:02d}"

    return daily


def show_evolution_chart(year1, year2):
    """Show line chart comparing monthly evolution of both periods"""
    if year1 is None or year2 is None:
        return

    st.markdown("### 📈 Monthly Evolution Comparison")

    # Get monthly data for both years
    monthly1 = get_monthly_evolution(year1)
    monthly2 = get_monthly_evolution(year2)

    if monthly1.empty and monthly2.empty:
        st.info("No data available for monthly comparison")
        return

    # Metric selector
    metric = st.selectbox(
        "Select metric to compare:",
        ["observations", "species", "observers"],
        format_func=lambda x: x.capitalize(),
    )

    # Prepare data for chart
    chart_data = []

    if not monthly1.empty:
        for _, row in monthly1.iterrows():
            chart_data.append(
                {
                    "Month": row["month_name"],
                    "Month_num": row["month"],
                    "Value": row[metric],
                    "Period": str(year1),
                }
            )

    if not monthly2.empty:
        for _, row in monthly2.iterrows():
            chart_data.append(
                {
                    "Month": row["month_name"],
                    "Month_num": row["month"],
                    "Value": row[metric],
                    "Period": str(year2),
                }
            )

    df_chart = pd.DataFrame(chart_data)

    if df_chart.empty:
        st.info("No data available")
        return

    # Sort by month number
    df_chart = df_chart.sort_values("Month_num")

    # Create line chart
    fig = px.line(
        df_chart,
        x="Month",
        y="Value",
        color="Period",
        markers=True,
        color_discrete_sequence=[COLORS[3], COLORS[4]],
        labels={"Value": metric.capitalize(), "Month": ""},
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            categoryorder="array",
            categoryarray=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
        ),
        yaxis=dict(rangemode="tozero", tickformat=",d"),
    )

    fig.update_traces(line=dict(width=3), marker=dict(size=8))

    st.plotly_chart(fig, use_container_width=True)


def show_daily_evolution_chart(year1, month1, year2, month2):
    """Show line chart comparing daily evolution of both periods (months)"""
    if year1 is None or month1 is None or year2 is None or month2 is None:
        return

    st.markdown("### 📈 Daily evolution analysis")

    # Get daily data for both months
    daily1 = get_daily_evolution(year1, month1)
    daily2 = get_daily_evolution(year2, month2)

    if daily1.empty and daily2.empty:
        st.info("No data available for daily comparison")
        return

    # Metric selector
    metric = st.selectbox(
        "Select metric to compare:",
        ["observations", "species", "observers"],
        format_func=lambda x: x.capitalize(),
        key="daily_metric",
    )

    # Prepare data for chart
    chart_data = []

    if not daily1.empty:
        for _, row in daily1.iterrows():
            chart_data.append(
                {
                    "Day": row["day"],
                    "Day_label": row["day_label"],
                    "Value": row[metric],
                    "Period": f"{year1}-{month1:02d}",
                }
            )

    if not daily2.empty:
        for _, row in daily2.iterrows():
            chart_data.append(
                {
                    "Day": row["day"],
                    "Day_label": row["day_label"],
                    "Value": row[metric],
                    "Period": f"{year2}-{month2:02d}",
                }
            )

    df_chart = pd.DataFrame(chart_data)

    if df_chart.empty:
        st.info("No data available")
        return

    # Sort by day
    df_chart = df_chart.sort_values("Day")

    # Create line chart
    fig = px.line(
        df_chart,
        x="Day",
        y="Value",
        color="Period",
        markers=True,
        color_discrete_sequence=[COLORS[3], COLORS[4]],
        labels={"Value": metric.capitalize(), "Day": "Day of month"},
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            tickmode="linear",
            tick0=1,
            dtick=1,
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
        ),
        yaxis=dict(rangemode="tozero", tickformat=",d"),
    )

    fig.update_traces(line=dict(width=3), marker=dict(size=8))

    st.plotly_chart(fig, use_container_width=True)


################


# Main body

create_header()

period_to_compare, form_submitted = create_period_comparisson()

# Check if both periods are valid
both_periods_valid = (
    period_to_compare["year1"] is not None and period_to_compare["year2"] is not None
)

# Check if period types match (both years or both months)
month1 = period_to_compare["month1"]
month2 = period_to_compare["month2"]
periods_match = (month1 is None and month2 is None) or (
    month1 is not None and month2 is not None
)

# Handle form submission
if form_submitted:
    if not both_periods_valid:
        st.warning("⚠️ Please enter at least a year for both periods")
    elif not periods_match:
        st.warning(
            "⚠️ Both periods must be of the same type: either both years or both year-months"
        )
    else:
        st.session_state.comparison_done = True
        st.session_state.compared_periods = period_to_compare.copy()

if not st.session_state.get("comparison_done"):
    st.info("👆 Enter both periods (at least year) and click Compare")
else:
    # Use stored periods for comparison
    periods = st.session_state.get("compared_periods", period_to_compare)

    # Get metrics for both periods
    with st.spinner("Loading comparison data..."):
        metrics1 = get_period_metrics(periods["year1"], periods["month1"])
        metrics2 = get_period_metrics(periods["year2"], periods["month2"])

    st.write("")
    st.write("")

    # Show comparison
    show_comparison_metrics(metrics1, metrics2)

    st.write("")
    st.write("")
    st.write("")

    # Show quality grade comparison
    show_quality_comparison(
        periods["year1"], periods["month1"], periods["year2"], periods["month2"]
    )

    st.write("")
    st.write("")

    show_new_species(
        periods["year1"], periods["month1"], periods["year2"], periods["month2"]
    )

    st.write("")
    st.write("")
    st.write("")

    # Show participation comparison
    show_participation_comparison(
        periods["year1"], periods["month1"], periods["year2"], periods["month2"]
    )

    st.write("")
    st.write("")
    st.write("")
    st.write("")

    # Show evolution chart based on period type
    if periods["month1"] is None and periods["month2"] is None:
        # Both are full years → monthly evolution
        show_evolution_chart(periods["year1"], periods["year2"])
    elif periods["month1"] is not None and periods["month2"] is not None:
        # Both are specific months → daily evolution
        show_daily_evolution_chart(
            periods["year1"], periods["month1"], periods["year2"], periods["month2"]
        )
    else:
        st.info(
            "📈 Evolution chart requires both periods to be of the same type (both years or both months)"
        )

    st.write("")

    # Show temporal patterns comparison
    show_temporal_comparison(
        periods["year1"], periods["month1"], periods["year2"], periods["month2"]
    )
