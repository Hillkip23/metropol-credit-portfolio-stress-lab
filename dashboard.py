from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "demo"

st.set_page_config(
    page_title="Portfolio Resilience & Scenario Stress Module",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISCLAIMER = """
**Illustrative sandbox demonstrator.** The portfolio and scenario parameters
shown here are synthetic and are used only to demonstrate the workflow:
scenario design -> portfolio stress sensitivity -> concentration analysis ->
early-warning prioritisation -> management action.

A client implementation would be calibrated using governed, pseudonymized
lender and permitted credit-information-sharing data, Kenya-relevant
macroeconomic scenarios, and the institution's approved credit-risk and
IFRS 9 policies.
"""

PAGE_OVERVIEW = "Portfolio resilience overview"
PAGE_CONCENTRATION = "Risk exposure & concentration"
PAGE_MIGRATION = "Borrower risk migration"
PAGE_WATCHLIST = "Early-warning worklist"
PAGE_ACTIONS = "Recommended actions"
PAGE_METHOD = "Pilot design & governance"

SEVERE_SCENARIO = "Severe stress"
BASELINE_SCENARIO = "Baseline"
MODERATE_SCENARIO = "Moderate stress"


def read_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required dashboard input was not found: {path}"
        )

    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "kpis": read_csv("executive_kpis_by_scenario.csv"),
        "sector": read_csv(
            "executive_ecl_concentration_by_sector.csv"
        ),
        "product": read_csv(
            "executive_ecl_concentration_by_product.csv"
        ),
        "score_band": read_csv(
            "executive_ecl_concentration_by_score_band.csv"
        ),
        "region": read_csv(
            "executive_ecl_concentration_by_region.csv"
        ),
        "borrower_type": read_csv(
            "executive_ecl_concentration_by_borrower_type.csv"
        ),
        "migration": read_csv(
            "executive_stage_migration_severe.csv"
        ),
        "watchlist": read_csv(
            "executive_watchlist_top25.csv"
        ),
        "actions": read_csv(
            "executive_management_actions.csv"
        ),
        "scenarios": read_csv(
            "illustrative_credit_stress_scenarios.csv"
        ),
        "thresholds": read_csv(
            "illustrative_stress_percentile_thresholds.csv"
        ),
    }


def get_scenario_row(
    kpis: pd.DataFrame,
    scenario_name: str,
) -> pd.Series:
    matching_rows = kpis.loc[
        kpis["scenario"] == scenario_name
    ]

    if matching_rows.empty:
        raise ValueError(
            f"Scenario '{scenario_name}' was not found in KPI data."
        )

    return matching_rows.iloc[0]


def format_kes(value: float) -> str:
    if pd.isna(value):
        return "-"

    absolute_value = abs(value)

    if absolute_value >= 1_000_000_000:
        return f"KES {value / 1_000_000_000:,.2f}bn"

    if absolute_value >= 1_000_000:
        return f"KES {value / 1_000_000:,.2f}m"

    if absolute_value >= 1_000:
        return f"KES {value / 1_000:,.1f}k"

    return f"KES {value:,.0f}"


def format_percent(value: float) -> str:
    if pd.isna(value):
        return "-"

    return f"{value:,.1f}%"


def style_currency_table(
    frame: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    currency_columns = [
        column
        for column in frame.columns
        if column.endswith("_kes")
    ]

    percentage_columns = [
        column
        for column in frame.columns
        if column.endswith("_pct")
        or column in {
            "mean_baseline_pd",
            "mean_stressed_pd",
            "mean_baseline_lgd",
            "mean_stressed_lgd",
        }
    ]

    formatting: dict[str, str] = {}

    for column in currency_columns:
        formatting[column] = "KES {:,.0f}"

    for column in percentage_columns:
        formatting[column] = "{:,.1f}%"

    return frame.style.format(
        formatting,
        na_rep="-",
    )


def render_header() -> None:
    st.title("Portfolio Resilience & Scenario Stress Module")

    st.caption(
        "Illustrative extension for portfolio monitoring, early warning, "
        "risk exposure and collections prioritisation"
    )

    st.caption(
        "Demonstrator: synthetic portfolio and illustrative assumptions only | "
        "Designed to show a potential future module for governed lender and "
        "credit-information-sharing data"
    )

    st.warning(DISCLAIMER)


def render_overview(data: dict[str, pd.DataFrame]) -> None:
    st.header("Portfolio resilience overview")

    st.info(
        "Meeting demonstrator: this module is designed as a possible "
        "forward-looking extension to existing portfolio monitoring. "
        "It does not replace credit reports, credit scores, lender "
        "scorecards, or approved IFRS 9 processes."
    )

    kpis = data["kpis"].copy()

    baseline = get_scenario_row(
        kpis,
        BASELINE_SCENARIO,
    )

    moderate = get_scenario_row(
        kpis,
        MODERATE_SCENARIO,
    )

    severe = get_scenario_row(
        kpis,
        SEVERE_SCENARIO,
    )

    st.subheader("Illustrative scenario impact")

    first_row = st.columns(4)

    first_row[0].metric(
        "Baseline ECL",
        format_kes(baseline["baseline_ecl_kes"]),
    )

    first_row[1].metric(
        "Severe-scenario ECL",
        format_kes(severe["stressed_ecl_kes"]),
        delta=format_kes(severe["incremental_ecl_kes"]),
        delta_color="inverse",
    )

    first_row[2].metric(
        "ECL sensitivity",
        format_percent(severe["ecl_uplift_pct"]),
        delta="vs baseline",
        delta_color="inverse",
    )

    first_row[3].metric(
        "Accounts with risk deterioration",
        f"{int(severe['deteriorated_accounts']):,}",
        delta=format_percent(
            severe["deteriorated_account_pct"]
        ),
        delta_color="inverse",
    )

    second_row = st.columns(4)

    second_row[0].metric(
        "Baseline portfolio EAD",
        format_kes(baseline["baseline_ead_kes"]),
    )

    second_row[1].metric(
        "Severe-scenario EAD",
        format_kes(severe["stressed_ead_kes"]),
    )

    second_row[2].metric(
        "Stage 2 accounts",
        f"{int(severe['stage_2_accounts']):,}",
        delta=(
            f"{int(severe['stage_2_accounts'] - baseline['stage_2_accounts']):,} "
            "vs baseline"
        ),
        delta_color="inverse",
    )

    second_row[3].metric(
        "Stage 3 accounts",
        f"{int(severe['stage_3_accounts']):,}",
        delta=(
            f"{int(severe['stage_3_accounts'] - baseline['stage_3_accounts']):,} "
            "vs baseline"
        ),
        delta_color="inverse",
    )

    st.divider()
    st.subheader("Scenario comparison")

    chart_data = kpis[
        [
            "scenario",
            "baseline_ecl_kes",
            "stressed_ecl_kes",
            "incremental_ecl_kes",
        ]
    ].melt(
        id_vars="scenario",
        var_name="metric",
        value_name="ecl_kes",
    )

    chart_labels = {
        "baseline_ecl_kes": "Baseline ECL",
        "stressed_ecl_kes": "Scenario ECL",
        "incremental_ecl_kes": "Incremental ECL",
    }

    chart_data["metric"] = chart_data["metric"].map(
        chart_labels
    )

    scenario_chart = px.bar(
        chart_data,
        x="scenario",
        y="ecl_kes",
        color="metric",
        barmode="group",
        labels={
            "scenario": "Scenario",
            "ecl_kes": "Expected credit loss (KES)",
            "metric": "Measure",
        },
        color_discrete_map={
            "Baseline ECL": "#2F80ED",
            "Scenario ECL": "#C0392B",
            "Incremental ECL": "#F2994A",
        },
    )

    scenario_chart.update_yaxes(
        tickprefix="KES ",
        tickformat=",.0f",
    )

    scenario_chart.update_layout(
        legend_title_text="",
        height=440,
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(
        scenario_chart,
        use_container_width=True,
    )

    st.subheader("Scenario KPI table")

    display_columns = [
        "scenario",
        "baseline_ead_kes",
        "stressed_ead_kes",
        "baseline_ecl_kes",
        "stressed_ecl_kes",
        "incremental_ecl_kes",
        "ecl_uplift_pct",
        "deteriorated_accounts",
        "deteriorated_account_pct",
        "stage_2_accounts",
        "stage_3_accounts",
    ]

    st.dataframe(
        style_currency_table(
            kpis[display_columns]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Illustrative interpretation")

    st.markdown(
        f"""
- Under the illustrative severe scenario, ECL changes from
  **{format_kes(baseline["baseline_ecl_kes"])}** to
  **{format_kes(severe["stressed_ecl_kes"])}**.
- The illustrative incremental impact is
  **{format_kes(severe["incremental_ecl_kes"])}**, or
  **{format_percent(severe["ecl_uplift_pct"])}** above the baseline case.
- The purpose is to make vulnerability, loss concentration, borrower
  migration and intervention priorities visible before realised defaults
  accumulate.
- Scenario parameters and account data in this demonstrator are synthetic;
  they are not a forecast for a lender or Metropol client.
"""
    )

    st.caption(
        "Moderate scenario reference: "
        f"{format_kes(moderate['incremental_ecl_kes'])} incremental ECL "
        f"and {int(moderate['deteriorated_accounts']):,} accounts with "
        "illustrative deterioration."
    )


def render_concentration(
    data: dict[str, pd.DataFrame],
) -> None:
    st.header("Risk exposure & concentration")

    st.caption(
        "Illustrative severe-scenario concentration analysis. The purpose is "
        "to identify where a lender may need deeper portfolio review, "
        "policy attention or early intervention."
    )

    dimension = st.selectbox(
        "View risk exposure by",
        options=[
            "Sector",
            "Product",
            "Score band",
            "Region",
            "Borrower type",
        ],
    )

    dimension_data = {
        "Sector": (
            data["sector"].copy(),
            "sector",
            "Sector",
        ),
        "Product": (
            data["product"].copy(),
            "product_type",
            "Product",
        ),
        "Score band": (
            data["score_band"].copy(),
            "bureau_score_band",
            "Score band",
        ),
        "Region": (
            data["region"].copy(),
            "region",
            "Region",
        ),
        "Borrower type": (
            data["borrower_type"].copy(),
            "borrower_type",
            "Borrower type",
        ),
    }

    frame, category_column, category_label = dimension_data[
        dimension
    ]

    top_n = st.slider(
        "Number of segments to show",
        min_value=3,
        max_value=min(15, len(frame)),
        value=min(10, len(frame)),
    )

    selected = frame.head(top_n).copy()

    left_column, right_column = st.columns(2)

    incremental_chart = px.bar(
        selected,
        x="incremental_ecl_kes",
        y=category_column,
        orientation="h",
        text="incremental_ecl_share_pct",
        labels={
            category_column: category_label,
            "incremental_ecl_kes": "Incremental ECL (KES)",
        },
        color="incremental_ecl_kes",
        color_continuous_scale="Reds",
    )

    incremental_chart.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    incremental_chart.update_layout(
        title="Incremental ECL concentration",
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
        height=500,
        margin=dict(l=20, r=20, t=55, b=20),
    )

    left_column.plotly_chart(
        incremental_chart,
        use_container_width=True,
    )

    risk_chart = px.scatter(
        selected,
        x="deteriorated_account_pct",
        y="ecl_uplift_pct",
        size="stressed_ead_kes",
        color=category_column,
        hover_name=category_column,
        labels={
            "deteriorated_account_pct": "Accounts deteriorating (%)",
            "ecl_uplift_pct": "ECL sensitivity (%)",
            category_column: category_label,
        },
        size_max=55,
    )

    risk_chart.update_layout(
        title="Relative segment sensitivity",
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=55, b=20),
    )

    right_column.plotly_chart(
        risk_chart,
        use_container_width=True,
    )

    st.subheader(f"{category_label} detail")

    table_columns = [
        category_column,
        "accounts",
        "stressed_ead_kes",
        "baseline_ecl_kes",
        "stressed_ecl_kes",
        "incremental_ecl_kes",
        "incremental_ecl_share_pct",
        "ecl_uplift_pct",
        "deteriorated_accounts",
        "deteriorated_account_pct",
        "stage_2_accounts",
        "stage_3_accounts",
    ]

    st.dataframe(
        style_currency_table(
            frame[table_columns]
        ),
        use_container_width=True,
        hide_index=True,
    )

    top_segment = frame.iloc[0]

    st.info(
        f"In this illustrative severe scenario, **{top_segment[category_column]}** "
        "is the largest incremental-ECL contributor in the selected view: "
        f"{format_kes(top_segment['incremental_ecl_kes'])}, representing "
        f"{top_segment['incremental_ecl_share_pct']:.1f}% of total "
        "incremental ECL."
    )


def render_migration(
    data: dict[str, pd.DataFrame],
) -> None:
    st.header("Borrower risk migration")

    st.caption(
        "Illustrative migration from baseline risk stage to severe-scenario "
        "stage. A production implementation would use the lender's approved "
        "staging, significant-increase-in-credit-risk and default policies."
    )

    migration = data["migration"].copy()

    stage_order = {
        "Stage 1": 1,
        "Stage 2": 2,
        "Stage 3": 3,
    }

    migration["baseline_order"] = migration[
        "baseline_stage"
    ].map(stage_order)

    migration["stressed_order"] = migration[
        "stressed_stage"
    ].map(stage_order)

    migration = migration.sort_values(
        ["baseline_order", "stressed_order"]
    )

    matrix = migration.pivot(
        index="baseline_stage",
        columns="stressed_stage",
        values="accounts",
    ).reindex(
        index=["Stage 1", "Stage 2", "Stage 3"],
        columns=["Stage 1", "Stage 2", "Stage 3"],
    ).fillna(0)

    heatmap = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale="Reds",
            text=matrix.values.astype(int),
            texttemplate="%{text:,}",
            hovertemplate=(
                "Baseline stage: %{y}<br>"
                "Scenario stage: %{x}<br>"
                "Accounts: %{z:,}<extra></extra>"
            ),
        )
    )

    heatmap.update_layout(
        title="Illustrative account migration matrix",
        xaxis_title="Scenario stage",
        yaxis_title="Baseline stage",
        height=460,
        margin=dict(l=20, r=20, t=55, b=20),
    )

    left_column, right_column = st.columns([1.15, 1])

    left_column.plotly_chart(
        heatmap,
        use_container_width=True,
    )

    migration_chart = px.bar(
        migration,
        x="baseline_stage",
        y="incremental_ecl_kes",
        color="stressed_stage",
        barmode="stack",
        text="incremental_ecl_share_pct",
        category_orders={
            "baseline_stage": [
                "Stage 1",
                "Stage 2",
                "Stage 3",
            ],
            "stressed_stage": [
                "Stage 1",
                "Stage 2",
                "Stage 3",
            ],
        },
        labels={
            "baseline_stage": "Baseline stage",
            "incremental_ecl_kes": "Incremental ECL (KES)",
            "stressed_stage": "Scenario stage",
        },
        color_discrete_map={
            "Stage 1": "#27AE60",
            "Stage 2": "#F2994A",
            "Stage 3": "#C0392B",
        },
    )

    migration_chart.update_layout(
        title="Incremental ECL by migration route",
        legend_title_text="Scenario stage",
        height=460,
        margin=dict(l=20, r=20, t=55, b=20),
    )

    right_column.plotly_chart(
        migration_chart,
        use_container_width=True,
    )

    st.subheader("Migration detail")

    display_columns = [
        "baseline_stage",
        "stressed_stage",
        "migration_direction",
        "accounts",
        "account_share_pct",
        "baseline_ead_kes",
        "baseline_ecl_kes",
        "stressed_ecl_kes",
        "incremental_ecl_kes",
        "incremental_ecl_share_pct",
    ]

    st.dataframe(
        style_currency_table(
            migration[display_columns]
        ),
        use_container_width=True,
        hide_index=True,
    )

    stage_1_to_3 = migration.loc[
        (migration["baseline_stage"] == "Stage 1")
        & (migration["stressed_stage"] == "Stage 3")
    ].iloc[0]

    stage_2_to_3 = migration.loc[
        (migration["baseline_stage"] == "Stage 2")
        & (migration["stressed_stage"] == "Stage 3")
    ].iloc[0]

    combined_share = (
        stage_1_to_3["incremental_ecl_share_pct"]
        + stage_2_to_3["incremental_ecl_share_pct"]
    )

    st.info(
        "Illustrative Stage 1 -> Stage 3 and Stage 2 -> Stage 3 migration "
        f"together account for {combined_share:.1f}% of incremental ECL. "
        "This is why scenario analysis can complement static delinquency "
        "monitoring and current-state reporting."
    )


def render_watchlist(
    data: dict[str, pd.DataFrame],
) -> None:
    st.header("Early-warning worklist")

    st.caption(
        "Illustrative prioritisation of synthetic accounts by scenario "
        "vulnerability and incremental ECL. In a controlled pilot, "
        "pseudonymous records and human review would be used."
    )

    watchlist = data["watchlist"].copy()

    filter_column_1, filter_column_2, filter_column_3 = st.columns(3)

    sectors = ["All"] + sorted(
        watchlist["sector"].dropna().unique().tolist()
    )

    products = ["All"] + sorted(
        watchlist["product_type"].dropna().unique().tolist()
    )

    score_bands = ["All"] + sorted(
        watchlist["bureau_score_band"].dropna().unique().tolist()
    )

    selected_sector = filter_column_1.selectbox(
        "Sector",
        sectors,
    )

    selected_product = filter_column_2.selectbox(
        "Product",
        products,
    )

    selected_score_band = filter_column_3.selectbox(
        "Score band",
        score_bands,
    )

    rate_filter = st.radio(
        "Interest-rate structure",
        options=["All", "Variable", "Fixed"],
        horizontal=True,
    )

    filtered = watchlist.copy()

    if selected_sector != "All":
        filtered = filtered.loc[
            filtered["sector"] == selected_sector
        ]

    if selected_product != "All":
        filtered = filtered.loc[
            filtered["product_type"] == selected_product
        ]

    if selected_score_band != "All":
        filtered = filtered.loc[
            filtered["bureau_score_band"] == selected_score_band
        ]

    if rate_filter != "All":
        filtered = filtered.loc[
            filtered["interest_rate_type"] == rate_filter
        ]

    metric_row = st.columns(4)

    metric_row[0].metric(
        "Visible synthetic accounts",
        f"{len(filtered):,}",
    )

    metric_row[1].metric(
        "Visible incremental ECL",
        format_kes(filtered["incremental_ecl_kes"].sum()),
    )

    metric_row[2].metric(
        "Variable-rate share",
        (
            format_percent(
                100.0
                * (
                    filtered["interest_rate_type"]
                    == "Variable"
                ).mean()
            )
            if not filtered.empty
            else "-"
        ),
    )

    metric_row[3].metric(
        "FX-exposed share",
        (
            format_percent(
                100.0
                * filtered["fx_exposed"].astype(bool).mean()
            )
            if not filtered.empty
            else "-"
        ),
    )

    if filtered.empty:
        st.info(
            "No synthetic worklist accounts match the selected filters."
        )
        return

    worklist_chart = px.bar(
        filtered.sort_values(
            "incremental_ecl_kes",
            ascending=True,
        ),
        x="incremental_ecl_kes",
        y="account_id",
        orientation="h",
        color="stressed_stage",
        hover_data=[
            "product_type",
            "sector",
            "bureau_score_band",
            "dpd_band",
            "interest_rate_type",
            "fx_exposed",
            "combined_pd_multiplier",
        ],
        labels={
            "incremental_ecl_kes": "Incremental ECL (KES)",
            "account_id": "Synthetic account",
            "stressed_stage": "Scenario stage",
        },
        color_discrete_map={
            "Stage 1": "#27AE60",
            "Stage 2": "#F2994A",
            "Stage 3": "#C0392B",
        },
    )

    worklist_chart.update_layout(
        height=max(420, 34 * len(filtered)),
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(
        worklist_chart,
        use_container_width=True,
    )

    display_columns = [
        "watchlist_rank",
        "account_id",
        "borrower_type",
        "product_type",
        "sector",
        "region",
        "bureau_score_band",
        "dpd_band",
        "interest_rate_type",
        "fx_exposed",
        "ead_kes",
        "baseline_pd",
        "stressed_pd",
        "baseline_stage",
        "stressed_stage",
        "baseline_ecl_kes",
        "stressed_ecl_kes",
        "incremental_ecl_kes",
        "ecl_uplift_pct",
        "combined_pd_multiplier",
    ]

    display = filtered[display_columns].copy()

    for column in [
        "baseline_pd",
        "stressed_pd",
        "ecl_uplift_pct",
    ]:
        display[column] = 100.0 * display[column]

    st.dataframe(
        display.style.format(
            {
                "ead_kes": "KES {:,.0f}",
                "baseline_ecl_kes": "KES {:,.0f}",
                "stressed_ecl_kes": "KES {:,.0f}",
                "incremental_ecl_kes": "KES {:,.0f}",
                "baseline_pd": "{:,.1f}%",
                "stressed_pd": "{:,.1f}%",
                "ecl_uplift_pct": "{:,.1f}%",
                "combined_pd_multiplier": "{:,.2f}x",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "In a Metropol or lender sandbox, this view would be a "
        "pseudonymized worklist. It would support human review and "
        "prioritisation - not automated decisions about any borrower."
    )


def render_actions(
    data: dict[str, pd.DataFrame],
) -> None:
    st.header("Recommended actions")

    st.caption(
        "Illustrative actions generated from concentration analysis, "
        "risk migration and the synthetic early-warning worklist."
    )

    actions = data["actions"].copy().sort_values("priority")

    for _, action in actions.iterrows():
        with st.expander(
            f"{int(action['priority'])}. {action['risk_signal']}",
            expanded=True,
        ):
            st.markdown(
                f"**Recommended action:** {action['recommended_action']}"
            )

            st.markdown(
                f"**Primary owner:** {action['primary_owner']}"
            )

    st.divider()
    st.subheader("Operating-model implication")

    st.markdown(
        """
A production deployment would turn scenario outputs into a governed,
recurring portfolio-management workflow:

1. Refresh permitted portfolio, credit-information-sharing, macroeconomic
   and market-risk inputs.
2. Recalculate scenario sensitivity, concentration and early-warning
   outputs on an agreed frequency.
3. Review material risk migration, portfolio concentration and worklist
   exceptions.
4. Assign accountable actions to credit, collections, product, treasury,
   finance and relationship teams.
5. Track action completion, effectiveness, model performance and overrides
   through relevant risk and model-governance forums.
"""
    )


def render_methodology(
    data: dict[str, pd.DataFrame],
) -> None:
    st.header("Pilot design & governance")

    st.subheader("Illustrative stress-to-credit workflow")

    st.markdown(
        """
```text
Global and domestic market / macroeconomic stress signals
  - Uncertainty and downside-risk indicators
  - Interest-rate, FX, inflation and sector conditions
  - Portfolio score movement and payment behaviour
  - Delinquency, utilisation and borrower-change signals

          |
          v

Scenario severity and governance

          |
          v

Portfolio sensitivity analysis
  - PD, roll-rate and stage-migration sensitivity
  - ECL and exposure sensitivity
  - Sector, product, region and score-band concentration

          |
          v

Early-warning worklist and accountable management actions
```
"""
    )

    st.caption(
        "The demonstrator uses an external forward-looking market-stress "
        "methodology to show the architecture. A Kenyan deployment would "
        "use locally appropriate macroeconomic, sector and portfolio "
        "performance inputs."
    )

    thresholds = data["thresholds"].copy()

    with st.expander(
        "Demonstrator stress-threshold reference",
        expanded=False,
    ):
        st.dataframe(
            thresholds.style.format(
                {
                    "p50": "{:,.4f}",
                    "p75": "{:,.4f}",
                    "p90": "{:,.4f}",
                    "p95": "{:,.4f}",
                    "p99": "{:,.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Illustrative scenario assumptions")

    scenarios = data["scenarios"].copy()

    scenario_columns = [
        "scenario",
        "market_stress_band",
        "market_stress_score_range",
        "illustrative_pd_multiplier",
        "illustrative_lgd_multiplier",
        "illustrative_ead_multiplier",
        "illustrative_stage_2_threshold_pd",
        "illustrative_stage_3_threshold_pd",
        "purpose",
    ]

    available_columns = [
        column
        for column in scenario_columns
        if column in scenarios.columns
    ]

    st.dataframe(
        scenarios[available_columns].style.format(
            {
                "illustrative_pd_multiplier": "{:,.2f}x",
                "illustrative_lgd_multiplier": "{:,.2f}x",
                "illustrative_ead_multiplier": "{:,.2f}x",
                "illustrative_stage_2_threshold_pd": "{:,.1%}",
                "illustrative_stage_3_threshold_pd": "{:,.1%}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("What a controlled pilot would need")

    st.markdown(
        """
- A narrowly scoped pilot portfolio: for example, one SACCO, SME lender,
  digital-credit portfolio, trade-credit segment or lender portfolio.
- Pseudonymized account-level or approved segment-level data; no customer
  names, national IDs, phone numbers or direct identifiers.
- Agreed definitions for delinquency, default, cure, write-off, exposure,
  score movement and portfolio segments.
- Existing permitted signals: score bands and changes, delinquency flags,
  repayment patterns, new-facility or inquiry indicators, and relevant
  portfolio-monitoring fields.
- Kenya-relevant scenario inputs: interest rates, KES movement, inflation,
  activity/income conditions and sector-specific stress assumptions.
- A shadow-mode workflow: outputs reviewed by credit and collections teams,
  with no automated lending, pricing or customer decisioning.
- Joint success criteria: data quality, concentration visibility, usefulness
  of early-warning outputs and validation against subsequent outcomes.
"""
    )

    st.subheader("Proposed pilot conversation")

    pilot_columns = st.columns(3)

    pilot_columns[0].markdown(
        """
**1. Select a use case**

- SACCO or SME portfolio
- Trade-credit portfolio
- Digital-credit early warning
- Lender portfolio monitoring
"""
    )

    pilot_columns[1].markdown(
        """
**2. Run a controlled sandbox**

- Pseudonymized data
- Approved scenario paths
- Monthly or weekly refresh
- Human review; no automated action
"""
    )

    pilot_columns[2].markdown(
        """
**3. Measure value**

- Loss-concentration visibility
- Earlier risk escalation
- Better collections prioritisation
- Practical action adoption
"""
    )

    st.warning(DISCLAIMER)


def render_sidebar() -> str:
    with st.sidebar:
        st.header("Navigation")

        page = st.radio(
            "Select view",
            options=[
                PAGE_OVERVIEW,
                PAGE_CONCENTRATION,
                PAGE_MIGRATION,
                PAGE_WATCHLIST,
                PAGE_ACTIONS,
                PAGE_METHOD,
            ],
        )

        st.divider()

        st.caption("Demonstrator status")
        st.success("Synthetic portfolio loaded")
        st.success("Illustrative scenarios loaded")
        st.success("Executive outputs loaded")

        st.divider()

        st.caption(
            "Portfolio Resilience & Scenario Stress Module\n\n"
            "Illustrative sandbox demonstrator"
        )

    return page


def main() -> None:
    try:
        data = load_data()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()
    except ValueError as error:
        st.error(
            "Dashboard data could not be interpreted. "
            f"Details: {error}"
        )
        st.stop()

    render_header()
    page = render_sidebar()

    if page == PAGE_OVERVIEW:
        render_overview(data)
    elif page == PAGE_CONCENTRATION:
        render_concentration(data)
    elif page == PAGE_MIGRATION:
        render_migration(data)
    elif page == PAGE_WATCHLIST:
        render_watchlist(data)
    elif page == PAGE_ACTIONS:
        render_actions(data)
    elif page == PAGE_METHOD:
        render_methodology(data)


if __name__ == "__main__":
    main()


