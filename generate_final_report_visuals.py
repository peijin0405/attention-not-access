#!/usr/bin/env python3
"""Generate the Blockchain Futurist 2025 final visual analysis report."""

from __future__ import annotations

import math
import os
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
MPL_CACHE = ROOT / "output" / ".matplotlib"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

try:
    import squarify
except Exception:  # pragma: no cover - optional dependency
    squarify = None


OUTPUT = ROOT / "output"
ENRICHED = OUTPUT / "enriched"
FINAL = OUTPUT / "final_report"
FIGURES = FINAL / "figures"
TABLES = FINAL / "tables"
INSIGHTS = FINAL / "insights"

TOTAL_SESSIONS = 152
TOTAL_SPEAKERS = 215
TOTAL_COMPANIES = 199

COLORS = {
    "ink": "#1f2933",
    "muted": "#64748b",
    "grid": "#e5e7eb",
    "blue": "#2563eb",
    "teal": "#0f766e",
    "green": "#16a34a",
    "amber": "#d97706",
    "red": "#dc2626",
    "violet": "#7c3aed",
    "slate": "#475569",
}


@dataclass
class Artifact:
    figure: str
    table: str
    question: str
    sources: list[str]
    how_to_read: str
    takeaway: str


@dataclass
class RunState:
    charts: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    skipped_charts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    top_topics: pd.DataFrame | None = None
    top_alpha: pd.DataFrame | None = None
    top_brokers: pd.DataFrame | None = None


def ensure_dirs() -> None:
    for path in [FINAL, FIGURES, TABLES, INSIGHTS]:
        path.mkdir(parents=True, exist_ok=True)


def load_csv(name: str, state: RunState, required: bool = True) -> pd.DataFrame:
    path = OUTPUT / name if not name.startswith("enriched/") else OUTPUT / name
    if not path.exists():
        msg = str(path.relative_to(ROOT))
        if required:
            state.missing_inputs.append(msg)
            state.warnings.append(f"Missing required input: {msg}")
        return pd.DataFrame()
    return pd.read_csv(path)


def validate_columns(df: pd.DataFrame, cols: list[str], label: str, state: RunState) -> bool:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        state.warnings.append(f"{label} missing columns: {', '.join(missing)}")
        return False
    return True


def save_table(df: pd.DataFrame, filename: str, state: RunState) -> str:
    path = TABLES / filename
    df.to_csv(path, index=False)
    state.tables.append(str(path.relative_to(ROOT)))
    return str(path.relative_to(FINAL))


def save_fig(fig: plt.Figure, filename: str, state: RunState) -> str:
    path = FIGURES / filename
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    state.charts.append(str(path.relative_to(ROOT)))
    return str(path.relative_to(FINAL))


def write_md(path: Path, body: str, state: RunState | None = None, insight: bool = False) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")
    if state and insight:
        state.insights.append(str(path.relative_to(ROOT)))


def md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "Not available"
    table = df.copy()
    table.columns = [str(c) for c in table.columns]
    rows = []
    rows.append("| " + " | ".join(table.columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(table.columns)) + " |")
    for _, row in table.iterrows():
        vals = [str(v).replace("|", "/") for v in row.tolist()]
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def clean_label(value: object, width: int = 24) -> str:
    if pd.isna(value):
        return ""
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False))


def norm(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce").fillna(0)
    low, high = vals.min(), vals.max()
    if math.isclose(high, low):
        return pd.Series(np.zeros(len(vals)), index=series.index)
    return (vals - low) / (high - low)


def setup_axes(ax: plt.Axes, title: str, subtitle: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", color=COLORS["ink"], pad=18)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10.5, color=COLORS["muted"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    ax.tick_params(colors=COLORS["ink"])


def barh(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    subtitle: str,
    filename: str,
    state: RunState,
    color: str = COLORS["blue"],
    top_n: int = 20,
) -> str:
    data = df.sort_values(value_col, ascending=True).tail(top_n)
    fig, ax = plt.subplots(figsize=(11, max(6, len(data) * 0.36)))
    ax.barh(data[label_col].map(lambda x: clean_label(x, 28)), data[value_col], color=color)
    setup_axes(ax, title, subtitle)
    ax.set_xlabel(value_col.replace("_", " ").title())
    for y, v in enumerate(data[value_col]):
        ax.text(v, y, f" {v:.2f}" if isinstance(v, float) and not float(v).is_integer() else f" {int(v)}", va="center", fontsize=9)
    return save_fig(fig, filename, state)


def add_artifact(state: RunState, figure: str, table: str, question: str, sources: list[str], how: str, takeaway: str) -> None:
    state.artifacts.append(Artifact(figure, table, question, sources, how, takeaway))


def load_inputs(state: RunState) -> dict[str, pd.DataFrame]:
    return {
        "sessions": load_csv("cleaned_sessions.csv", state),
        "speakers": load_csv("speakers.csv", state),
        "companies": load_csv("companies.csv", state),
        "speaker_company": load_csv("speaker_company_edges.csv", state),
        "speaker_topic": load_csv("speaker_topic_edges.csv", state),
        "company_topic": load_csv("company_topic_edges.csv", state),
        "top_speakers": load_csv("conference_top_speakers.csv", state),
        "top_companies": load_csv("conference_top_companies.csv", state),
        "cooccurrence": load_csv("topic_cooccurrence_matrix.csv", state),
        "identity": load_csv("enriched/company_identity_enrichment.csv", state),
        "market": load_csv("enriched/company_market_signals.csv", state),
        "alpha": load_csv("enriched/company_alpha_scores.csv", state),
        "topic_intel": load_csv("enriched/topic_intelligence.csv", state),
    }


def module_attention(data: dict[str, pd.DataFrame], state: RunState) -> dict[str, object]:
    topic = data["topic_intel"].copy()
    validate_columns(topic, ["topic_v2", "number_of_sessions", "number_of_companies", "number_of_speakers"], "topic_intelligence", state)
    topic["attention_share"] = topic["number_of_sessions"] / topic["number_of_sessions"].sum()
    topic = topic.sort_values("number_of_sessions", ascending=False)
    state.top_topics = topic[["topic_v2", "number_of_sessions"]].head(10)

    table1 = save_table(topic[["topic_v2", "number_of_sessions", "attention_share"]], "01_topic_attention_distribution.csv", state)
    fig1 = barh(topic, "topic_v2", "number_of_sessions", "Topic Attention Distribution", "Sessions per topic, using topic_intelligence session counts.", "01_topic_attention_distribution.png", state, COLORS["blue"], 24)
    add_artifact(state, fig1, table1, "What topics captured the most attention?", ["topic_intelligence.csv", "cleaned_sessions.csv"], "Longer bars indicate more agenda attention by session count.", f"{topic.iloc[0].topic_v2} is the largest bucket with {int(topic.iloc[0].number_of_sessions)} sessions.")

    fig, ax = plt.subplots(figsize=(12, 8))
    if squarify:
        sizes = topic["number_of_sessions"].clip(lower=0.1)
        colors = plt.cm.viridis(norm(topic["number_of_speakers"]).to_numpy() * 0.75 + 0.15)
        labels = [f"{r.topic_v2}\n{int(r.number_of_sessions)} sessions" for r in topic.itertuples()]
        squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.9, ax=ax, text_kwargs={"fontsize": 8})
        ax.axis("off")
    else:
        ax.pie(topic["number_of_sessions"], labels=topic["topic_v2"], startangle=90)
    ax.set_title("Topic Attention Treemap", loc="left", fontsize=16, fontweight="bold", color=COLORS["ink"])
    fig2 = save_fig(fig, "02_topic_attention_treemap.png", state)
    add_artifact(state, fig2, "", "How concentrated is attention across the topic map?", ["topic_intelligence.csv"], "Rectangle size shows session count; darker color indicates more speakers.", "The map shows a large residual Other bucket plus visible concentration around AI x Crypto, Ethereum, Infrastructure, DeFi, and RWA.")

    fig, ax = plt.subplots(figsize=(11, 8))
    sizes = 80 + topic["number_of_speakers"] * 12
    ax.scatter(topic["number_of_companies"], topic["number_of_sessions"], s=sizes, alpha=0.72, color=COLORS["teal"], edgecolor="white", linewidth=1.2)
    for r in topic.itertuples():
        ax.text(r.number_of_companies + 0.25, r.number_of_sessions + 0.1, r.topic_v2, fontsize=8.5, color=COLORS["ink"])
    setup_axes(ax, "Topic Attention Concentration", "Broad company participation vs session attention. Bubble size is speaker count.")
    ax.set_xlabel("Number Of Companies")
    ax.set_ylabel("Number Of Sessions")
    table3 = save_table(topic[["topic_v2", "number_of_companies", "number_of_sessions", "number_of_speakers", "attention_share"]], "03_topic_attention_concentration.csv", state)
    fig3 = save_fig(fig, "03_topic_attention_concentration.png", state)
    add_artifact(state, fig3, table3, "Which narratives are broad-based versus concentrated?", ["topic_intelligence.csv", "company_topic_edges.csv", "speaker_topic_edges.csv"], "Upper-right topics have both high attention and broad participation; upper-left topics are more expert-concentrated.", "AI x Crypto has high session count and broad participation, while some lower-company topics look more specialist.")

    broad = topic.sort_values(["number_of_companies", "number_of_sessions"], ascending=False).head(5)
    concentrated = topic.assign(sessions_per_company=topic["number_of_sessions"] / topic["number_of_companies"].replace(0, np.nan)).sort_values("sessions_per_company", ascending=False).head(5)
    crowded = topic.assign(companies_per_session=topic["number_of_companies"] / topic["number_of_sessions"].replace(0, np.nan)).sort_values("companies_per_session", ascending=False).head(5)
    insight = f"""
# Module 1: The Attention Economy Of Web3

## Research Question
What topics captured the most attention at Blockchain Futurist Conference 2025?

## Method
Topic attention is measured with `number_of_sessions` from `topic_intelligence.csv`, which sums to the 152-session conference base. Breadth is measured with company and speaker counts from the topic intelligence table and the topic edge files.

## Required Visualizations
- `figures/01_topic_attention_distribution.png`
- `figures/02_topic_attention_treemap.png`
- `figures/03_topic_attention_concentration.png`

## Written Insights
The data suggests that attention is highly uneven. `{topic.iloc[0].topic_v2}` is the largest category at {int(topic.iloc[0].number_of_sessions)} sessions, but it is also a catch-all bucket that should be interpreted carefully. Excluding that residual bucket, the strongest named topics are {", ".join(topic[topic.topic_v2 != "Other"].head(5).topic_v2.tolist())}.

Broad-based narratives are visible where both company count and session count are high. The broadest topics by company participation are {", ".join(broad.topic_v2.tolist())}. These look less like single-company messaging and more like ecosystem-level attention.

Crowded narratives are topics with many companies per session: {", ".join(crowded.topic_v2.tolist())}. A reasonable interpretation is that these topics have wide market participation but limited agenda slots, which can indicate competitive positioning pressure.

Concentrated expert narratives are topics with high sessions per company: {", ".join(concentrated.topic_v2.tolist())}. These may represent more specialized domains where a smaller set of actors carries the conversation.

Overall, the agenda suggests a maturing Web3 market: attention is moving beyond broad crypto education into AI, infrastructure, financialization, and institutional-market themes, while legacy consumer narratives are present but not dominant.

## Limitations
The `Other` category is large and dilutes precision. Session counts represent agenda attention, not market size, revenue, or investor conviction. OCR-derived agenda data may merge or split some session records.
"""
    write_md(INSIGHTS / "01_attention_economy.md", insight, state, True)
    return {"topic": topic}


def build_topic_graph(cooc: pd.DataFrame) -> tuple[nx.Graph, pd.DataFrame]:
    topics = [c for c in cooc.columns if c != "topic"]
    rows = []
    for _, row in cooc.iterrows():
        a = row["topic"]
        for b in topics:
            if a == b:
                continue
            w = float(row.get(b, 0) or 0)
            if w > 0 and str(a) < str(b):
                rows.append({"source": a, "target": b, "weight": w})
    edges = pd.DataFrame(rows).sort_values("weight", ascending=False)
    graph = nx.Graph()
    for topic in topics:
        graph.add_node(topic)
    for r in edges.itertuples():
        graph.add_edge(r.source, r.target, weight=r.weight)
    return graph, edges


def draw_network(graph: nx.Graph, title: str, filename: str, state: RunState, node_colors: dict[str, str] | None = None, top_labels: int = 40) -> str:
    fig, ax = plt.subplots(figsize=(13, 10))
    if graph.number_of_edges() == 0:
        ax.text(0.5, 0.5, "No edges available", ha="center", va="center")
        return save_fig(fig, filename, state)
    weights = np.array([d.get("weight", 1) for _, _, d in graph.edges(data=True)])
    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.9)
    degrees = dict(graph.degree(weight="weight"))
    node_size = [180 + degrees.get(n, 1) * 55 for n in graph.nodes()]
    colors = [node_colors.get(n, COLORS["blue"]) if node_colors else COLORS["blue"] for n in graph.nodes()]
    nx.draw_networkx_edges(graph, pos, ax=ax, width=0.6 + weights / max(weights.max(), 1) * 3.5, alpha=0.28, edge_color=COLORS["slate"])
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=node_size, node_color=colors, alpha=0.88, linewidths=1, edgecolors="white")
    ranked = sorted(degrees, key=degrees.get, reverse=True)[:top_labels]
    nx.draw_networkx_labels(graph.subgraph(ranked), pos, ax=ax, font_size=8, font_color=COLORS["ink"])
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", color=COLORS["ink"])
    ax.axis("off")
    return save_fig(fig, filename, state)


def module_narrative(data: dict[str, pd.DataFrame], state: RunState) -> dict[str, object]:
    cooc = data["cooccurrence"].copy()
    topic = data["topic_intel"].copy()
    graph, edges = build_topic_graph(cooc)
    edge_table = save_table(edges, "04_narrative_network_edges.csv", state)
    fig4 = draw_network(graph, "Narrative Network Graph", "04_narrative_network_graph.png", state, top_labels=29)
    add_artifact(state, fig4, edge_table, "Which topics co-occur and form narrative clusters?", ["topic_cooccurrence_matrix.csv"], "Thicker edges show stronger topic co-occurrence; larger nodes have more weighted connections.", "AI x Crypto, Infrastructure, RWA, and Ethereum sit near multiple adjacent narratives.")

    deg = nx.degree_centrality(graph)
    bet = nx.betweenness_centrality(graph, weight="weight", normalized=True) if graph.number_of_edges() else {}
    try:
        eig = nx.eigenvector_centrality(graph, weight="weight", max_iter=2000) if graph.number_of_edges() else {}
    except Exception:
        eig = {n: 0 for n in graph.nodes()}
    centrality = pd.DataFrame({
        "topic_v2": list(graph.nodes()),
        "degree_centrality": [deg.get(n, 0) for n in graph.nodes()],
        "betweenness_centrality": [bet.get(n, 0) for n in graph.nodes()],
        "eigenvector_centrality": [eig.get(n, 0) for n in graph.nodes()],
    })
    centrality["composite_centrality"] = centrality[["degree_centrality", "betweenness_centrality", "eigenvector_centrality"]].mean(axis=1)
    centrality = centrality.sort_values("composite_centrality", ascending=False)
    cent_table = save_table(centrality, "05_narrative_centrality_ranking.csv", state)
    fig5 = barh(centrality, "topic_v2", "composite_centrality", "Narrative Centrality Ranking", "Composite of degree, betweenness, and eigenvector centrality.", "05_narrative_centrality_ranking.png", state, COLORS["violet"], 20)
    add_artifact(state, fig5, cent_table, "Which narratives act as bridges?", ["topic_cooccurrence_matrix.csv"], "Higher bars identify topics connected to more and stronger adjacent narratives.", f"{centrality.iloc[0].topic_v2} is the most central narrative by composite centrality.")

    groups = {
        "Legacy narratives": ["NFT", "Gaming", "Metaverse", "Creator Economy"],
        "Core infrastructure narratives": ["Infrastructure", "Layer1", "Layer2", "Security", "Privacy"],
        "Financialization narratives": ["RWA", "Stablecoins", "Payments", "Institutional Adoption"],
        "AI-native narratives": ["AI x Crypto", "AI Agents", "Identity", "DePIN"],
    }
    migration_rows = []
    for group, members in groups.items():
        subset = topic[topic["topic_v2"].isin(members)]
        migration_rows.append({
            "narrative_group": group,
            "topics_present": "; ".join(subset["topic_v2"].tolist()),
            "session_count": int(subset["number_of_sessions"].sum()),
            "company_count": int(subset["number_of_companies"].sum()),
            "speaker_count": int(subset["number_of_speakers"].sum()),
            "average_narrative_strength": round(float(subset["narrative_strength_score"].mean() if len(subset) else 0), 2),
        })
    migration = pd.DataFrame(migration_rows).sort_values("session_count", ascending=False)
    mig_table = save_table(migration, "06_narrative_migration_map.csv", state)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(migration))
    width = 0.26
    ax.bar(x - width, migration["session_count"], width, label="Sessions", color=COLORS["blue"])
    ax.bar(x, migration["company_count"], width, label="Companies", color=COLORS["teal"])
    ax.bar(x + width, migration["speaker_count"], width, label="Speakers", color=COLORS["amber"])
    ax.set_xticks(x)
    ax.set_xticklabels([clean_label(v, 20) for v in migration["narrative_group"]])
    setup_axes(ax, "Narrative Migration Map", "Legacy vs infrastructure, financialization, and AI-native agenda clusters.")
    ax.legend(frameon=False)
    fig6 = save_fig(fig, "06_narrative_migration_map.png", state)
    add_artifact(state, fig6, mig_table, "Is Web3 shifting toward AI, financialization, or infrastructure?", ["topic_intelligence.csv", "company_topic_edges.csv"], "Compare grouped session, company, and speaker counts across narrative families.", f"{migration.iloc[0].narrative_group} is the largest grouped cluster by session count.")

    less = migration[migration["narrative_group"].eq("Legacy narratives")].iloc[0]
    more = migration.head(2)
    bridges = centrality.head(6)
    insight = f"""
# Module 2: The Great Narrative Shift

## Research Question
What does the conference reveal about Web3's shift from older narratives toward AI, infrastructure, RWA, and stablecoins?

## Method
The module uses topic co-occurrence to build a narrative graph, then ranks topics by network centrality. A grouped migration view compares legacy, infrastructure, financialization, and AI-native topic families.

## Required Visualizations
- `figures/04_narrative_network_graph.png`
- `figures/05_narrative_centrality_ranking.png`
- `figures/06_narrative_migration_map.png`

## Written Insights
The data suggests that legacy consumer narratives are no longer the organizing center of the agenda. The legacy group totals {int(less.session_count)} sessions across the available topics, while the largest non-legacy groups are {more.iloc[0].narrative_group} ({int(more.iloc[0].session_count)} sessions) and {more.iloc[1].narrative_group} ({int(more.iloc[1].session_count)} sessions).

The most central bridge narratives by composite centrality are {", ".join(bridges.topic_v2.tolist())}. These topics matter because they connect otherwise separate conversations, making them more useful as indicators of where founder, investor, and enterprise attention may converge.

A reasonable interpretation is that Web3 in 2025 is becoming more infrastructure-driven and AI-aware, while financialization remains an important parallel axis through RWA, payments, stablecoins, and institutional adoption. The shift is not a full replacement of legacy narratives; it is a reprioritization toward domains with clearer enterprise utility, capital formation, and technical defensibility.

The most defensible narrative shift supported by this dataset is: conference attention appears to be moving away from NFT/GameFi-style cultural adoption narratives and toward AI, infrastructure, institutional finance, and real-world asset rails.

## Limitations
Co-occurrence reflects agenda tagging, not causal relationships. Some topics are absent from the cleaned taxonomy, including Metaverse and Data as standalone categories. Centrality can be inflated by broad topics that co-occur often because they are general.
"""
    write_md(INSIGHTS / "02_narrative_shift.md", insight, state, True)
    return {"centrality": centrality, "narrative_groups": migration, "narrative_edges": edges}


def module_signal(data: dict[str, pd.DataFrame], state: RunState) -> dict[str, object]:
    alpha = data["alpha"].copy()
    topic = data["topic_intel"].copy()
    company_topic = data["company_topic"].copy()
    validate_columns(alpha, ["company_name", "conference_presence_score", "external_momentum_score", "alpha_watch_score"], "company_alpha_scores", state)
    alpha = alpha.sort_values("alpha_watch_score", ascending=False)
    state.top_alpha = alpha[["company_name", "alpha_watch_score"]].head(10)

    x_med = alpha["conference_presence_score"].median()
    y_med = alpha["external_momentum_score"].median()
    def quadrant(row: pd.Series) -> str:
        if row["conference_presence_score"] >= x_med and row["external_momentum_score"] >= y_med:
            return "Validated leaders"
        if row["conference_presence_score"] >= x_med and row["external_momentum_score"] < y_med:
            return "Under-the-radar alpha"
        if row["conference_presence_score"] < x_med and row["external_momentum_score"] >= y_med:
            return "Market-known, less conference-central"
        return "Low signal"
    alpha["quadrant"] = alpha.apply(quadrant, axis=1)
    scatter_table = save_table(alpha, "07_presence_vs_external_momentum.csv", state)

    fig, ax = plt.subplots(figsize=(12, 8))
    qcolors = {
        "Validated leaders": COLORS["green"],
        "Under-the-radar alpha": COLORS["amber"],
        "Market-known, less conference-central": COLORS["blue"],
        "Low signal": COLORS["muted"],
    }
    for q, qdf in alpha.groupby("quadrant"):
        ax.scatter(qdf["conference_presence_score"], qdf["external_momentum_score"], s=70, label=q, alpha=0.75, color=qcolors[q], edgecolor="white", linewidth=0.8)
    ax.axvline(x_med, color=COLORS["grid"], linewidth=1.5)
    ax.axhline(y_med, color=COLORS["grid"], linewidth=1.5)
    for r in alpha.head(18).itertuples():
        ax.text(r.conference_presence_score + 0.6, r.external_momentum_score + 0.6, r.company_name, fontsize=8)
    setup_axes(ax, "Conference Presence vs External Momentum", "Quadrants use dataset medians; external coverage is directional and sparse.")
    ax.set_xlabel("Conference Presence Score")
    ax.set_ylabel("External Momentum Score")
    ax.legend(frameon=False, fontsize=8)
    fig7 = save_fig(fig, "07_presence_vs_external_momentum.png", state)
    add_artifact(state, fig7, scatter_table, "Which companies have conference attention before market visibility?", ["company_alpha_scores.csv", "company_market_signals.csv"], "Right side means stronger conference presence; upper side means stronger sourced external momentum.", "High-presence, low-momentum companies form the directional under-the-radar watchlist.")

    rank_table = save_table(alpha[["company_name", "conference_presence_score", "external_momentum_score", "alpha_watch_score", "dominant_topics", "quadrant"]], "08_company_alpha_watch_ranking.csv", state)
    fig8 = barh(alpha.head(25), "company_name", "alpha_watch_score", "Alpha Watch Ranking", "Companies ranked by alpha_watch_score from the enrichment pass.", "08_company_alpha_watch_ranking.png", state, COLORS["green"], 25)
    add_artifact(state, fig8, rank_table, "Which companies deserve an alpha watchlist?", ["company_alpha_scores.csv"], "Higher bars combine conference presence, emerging narrative exposure, and limited mainstream penalty.", f"{alpha.iloc[0].company_name} ranks highest by alpha_watch_score.")

    topic_alpha = company_topic.merge(alpha[["company_name", "alpha_watch_score"]], on="company_name", how="left")
    avg_alpha = topic_alpha.groupby("topic_v2", as_index=False)["alpha_watch_score"].mean().rename(columns={"alpha_watch_score": "edge_average_alpha_score"})
    opportunity = topic.merge(avg_alpha, on="topic_v2", how="left")
    opportunity["edge_average_alpha_score"] = opportunity["edge_average_alpha_score"].fillna(opportunity["average_company_alpha_score"])
    opportunity["topic_opportunity_score"] = (
        0.35 * norm(opportunity["narrative_strength_score"]) +
        0.30 * norm(opportunity["edge_average_alpha_score"]) +
        0.20 * norm(opportunity["number_of_companies"]) +
        0.15 * norm(opportunity["number_of_sessions"])
    ) * 100
    opportunity = opportunity.sort_values("topic_opportunity_score", ascending=False)
    opp_table = save_table(opportunity[["topic_v2", "topic_opportunity_score", "narrative_strength_score", "edge_average_alpha_score", "number_of_companies", "number_of_sessions"]], "09_topic_opportunity_ranking.csv", state)
    fig9 = barh(opportunity.head(20), "topic_v2", "topic_opportunity_score", "Topic Opportunity Ranking", "Composite of narrative strength, average company alpha, company count, and session count.", "09_topic_opportunity_ranking.png", state, COLORS["amber"], 20)
    add_artifact(state, fig9, opp_table, "Which topics look promising before broad market validation?", ["topic_intelligence.csv", "company_alpha_scores.csv", "company_topic_edges.csv"], "Higher scores combine narrative strength with company-level alpha and agenda breadth.", f"{opportunity.iloc[0].topic_v2} ranks highest by topic_opportunity_score.")

    market = data["market"]
    covered = int((market.get("market_signal_confidence", pd.Series(dtype=str)).fillna("low").str.lower() != "low").sum()) if not market.empty else 0
    validated = alpha[alpha["quadrant"].eq("Validated leaders")].head(8)
    under = alpha[alpha["quadrant"].eq("Under-the-radar alpha")].head(8)
    low_ext_high_presence = under["company_name"].tolist()
    insight = f"""
# Module 3: Finding Signal Before The Market

## Research Question
Which topics and companies appear to have strong conference attention but weaker external market visibility?

## Method
Company positioning is measured by `conference_presence_score` versus `external_momentum_score`. Quadrants are split by dataset medians. Topic opportunity combines narrative strength, average company alpha, number of companies, and session count.

## Required Visualizations
- `figures/07_presence_vs_external_momentum.png`
- `figures/08_company_alpha_watch_ranking.png`
- `figures/09_topic_opportunity_ranking.png`

## Written Insights
Validated leaders are companies with both high conference presence and high external momentum. In this dataset, the leading examples are {", ".join(validated.company_name.tolist())}.

Under-the-radar candidates are high-presence companies with weaker captured external momentum. The directional watchlist includes {", ".join(low_ext_high_presence)}. This does not mean these companies lack traction; it means the current enrichment pass did not capture strong external signals.

The strongest topic opportunity scores are {", ".join(opportunity.head(6).topic_v2.tolist())}. These topics combine agenda attention with company participation and alpha-weighted positioning.

Potentially overhyped topics are those with substantial participation but weak average alpha or low external validation. Given the limited external enrichment coverage, this should be treated as directional rather than definitive.

Only {covered} of {len(market)} companies have non-low external market signal confidence in the current enrichment file. This is the central caution for the module: the alpha watchlist is useful for prioritizing manual research, not for making definitive investment conclusions.

## Limitations
External signal coverage is sparse and seed-based. Blanks should not be interpreted as proof of no traction. The scoring model weights are heuristic and should be recalibrated after broader funding, token, developer, social, and hiring data is added.
"""
    write_md(INSIGHTS / "03_signal_before_market.md", insight, state, True)
    state.warnings.append(f"External market signal coverage is limited: {covered} of {len(market)} companies have non-low confidence.")
    return {"alpha": alpha, "opportunity": opportunity}


def module_power(data: dict[str, pd.DataFrame], state: RunState) -> dict[str, object]:
    speakers = data["speakers"].copy()
    companies = data["companies"].copy()
    sc = data["speaker_company"].dropna().drop_duplicates().copy()
    st = data["speaker_topic"].dropna().drop_duplicates().copy()
    ct = data["company_topic"].dropna().drop_duplicates().copy()

    top_speakers = set(speakers.sort_values("speaker_influence_score", ascending=False).head(70)["speaker_name"])
    top_companies = set(companies.sort_values("company_influence_score", ascending=False).head(55)["company_name"])
    sc_net = sc[sc["speaker_name"].isin(top_speakers) | sc["speaker_company"].isin(top_companies)].copy()
    sc_table = save_table(sc_net, "10_speaker_company_network_edges.csv", state)
    graph = nx.Graph()
    for r in sc_net.itertuples():
        graph.add_node(r.speaker_name, kind="speaker")
        graph.add_node(r.speaker_company, kind="company")
        graph.add_edge(r.speaker_name, r.speaker_company, weight=1)
    colors = {n: (COLORS["blue"] if d.get("kind") == "speaker" else COLORS["amber"]) for n, d in graph.nodes(data=True)}
    fig10 = draw_network(graph, "Speaker-Company Network", "10_speaker_company_network.png", state, colors, top_labels=55)
    add_artifact(state, fig10, sc_table, "Who connects people to institutional platforms?", ["speaker_company_edges.csv", "speakers.csv", "companies.csv"], "Blue nodes are speakers; amber nodes are companies. More connected nodes sit closer to the center.", "The network highlights repeat speakers and companies that anchor multiple people in the agenda.")

    top_topics = set(data["topic_intel"].sort_values("number_of_sessions", ascending=False).head(18)["topic_v2"])
    ct_counts = ct.merge(companies[["company_name", "company_influence_score"]], on="company_name", how="left")
    ct_net = ct_counts[(ct_counts["topic_v2"].isin(top_topics)) | (ct_counts["company_influence_score"].fillna(0) >= companies["company_influence_score"].quantile(0.75))].copy()
    ct_table = save_table(ct_net[["company_name", "topic_v2"]], "11_company_topic_network_edges.csv", state)
    graph2 = nx.Graph()
    for r in ct_net.itertuples():
        graph2.add_node(r.company_name, kind="company")
        graph2.add_node(r.topic_v2, kind="topic")
        graph2.add_edge(r.company_name, r.topic_v2, weight=1)
    colors2 = {n: (COLORS["teal"] if d.get("kind") == "company" else COLORS["violet"]) for n, d in graph2.nodes(data=True)}
    fig11 = draw_network(graph2, "Company-Topic Network", "11_company_topic_network.png", state, colors2, top_labels=70)
    add_artifact(state, fig11, ct_table, "Which companies connect the most narratives?", ["company_topic_edges.csv", "companies.csv"], "Teal nodes are companies; violet nodes are topics. Central companies touch multiple narratives.", "Multi-topic companies are better interpreted as ecosystem connectors than single-narrative participants.")

    broker = speakers[["speaker_name", "speaker_company", "number_of_sessions", "number_of_topics", "number_of_stages", "speaker_influence_score"]].copy()
    company_links = sc.groupby("speaker_name")["speaker_company"].nunique().rename("unique_companies_connected").reset_index()
    broker = broker.merge(company_links, on="speaker_name", how="left")
    broker["unique_companies_connected"] = broker["unique_companies_connected"].fillna(0)
    broker["narrative_broker_score"] = (
        0.35 * norm(broker["number_of_topics"]) +
        0.25 * norm(broker["unique_companies_connected"]) +
        0.25 * norm(broker["number_of_sessions"]) +
        0.15 * norm(broker["number_of_stages"])
    ) * 100
    broker = broker.sort_values("narrative_broker_score", ascending=False)
    state.top_brokers = broker[["speaker_name", "narrative_broker_score"]].head(10)

    top30 = broker.head(30)
    sankey = st.merge(sc, on="speaker_name", how="left")
    sankey = sankey[sankey["speaker_name"].isin(top30["speaker_name"])].dropna().drop_duplicates()
    sankey_table = save_table(sankey, "12_speaker_topic_sankey.csv", state)
    fig = draw_three_column_flow(sankey, "Speaker-Topic-Company Flow", "Top 30 narrative brokers by score")
    fig12 = save_fig(fig, "12_speaker_topic_sankey.png", state)
    add_artifact(state, fig12, sankey_table, "How do central speakers route attention across topics and companies?", ["speaker_topic_edges.csv", "speaker_company_edges.csv", "speakers.csv"], "Read left to right: speaker to topic to company. Line density shows repeated connections.", "The flow identifies people who translate between narrative categories and organizational platforms.")

    broker_table = save_table(broker, "13_top_narrative_brokers.csv", state)
    fig13 = barh(broker.head(25), "speaker_name", "narrative_broker_score", "Top Narrative Brokers", "Score combines topic breadth, company connections, sessions, and stages.", "13_top_narrative_brokers.png", state, COLORS["red"], 25)
    add_artifact(state, fig13, broker_table, "Who are the most valuable connectors to follow, interview, or reach out to?", ["speakers.csv", "speaker_company_edges.csv", "speaker_topic_edges.csv"], "Higher score means a speaker spans more topics, sessions, companies, and stages.", f"{broker.iloc[0].speaker_name} ranks highest as a narrative broker.")

    top_company_connectors = ct.groupby("company_name")["topic_v2"].nunique().sort_values(ascending=False).head(8)
    insight = f"""
# Module 4: Mapping The Web3 Power Network

## Research Question
Who are the most central speakers, companies, and connectors in the conference ecosystem?

## Method
The module combines speaker-company, speaker-topic, and company-topic edges. Narrative broker score weights topic breadth, company connections, number of sessions, and number of stages.

## Required Visualizations
- `figures/10_speaker_company_network.png`
- `figures/11_company_topic_network.png`
- `figures/12_speaker_topic_sankey.png`
- `figures/13_top_narrative_brokers.png`

## Written Insights
The most central speakers by narrative broker score are {", ".join(broker.head(10).speaker_name.tolist())}. These are the people most likely to connect separate agenda conversations.

The companies connecting the most distinct topics are {", ".join(top_company_connectors.index.tolist())}. These organizations appear less like single-product representatives and more like ecosystem infrastructure, media, association, or platform nodes.

The power network suggests that influence at this conference is not only about company size. It is also about cross-topic repeat participation. Speakers who appear across multiple stages and topics can act as narrative brokers, making them valuable for interviews, partnership discovery, and early signal collection.

The highest-value people to follow or reach out to are not necessarily the most famous names. They are the connectors whose agenda footprint spans multiple narratives, especially AI, infrastructure, finance, and institutional adoption.

## Limitations
Edges represent agenda associations, not formal employment verification or commercial partnerships. Some speaker-company relationships come from OCR parsing and may need manual review. Network centrality is sensitive to top-N filtering used to keep figures readable.
"""
    write_md(INSIGHTS / "04_power_network.md", insight, state, True)
    return {"broker": broker}


def draw_three_column_flow(df: pd.DataFrame, title: str, subtitle: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", color=COLORS["ink"], pad=18)
    ax.text(0, 1.01, subtitle, transform=ax.transAxes, fontsize=10.5, color=COLORS["muted"])
    if df.empty:
        ax.text(0.5, 0.5, "No flow records available", ha="center", va="center")
        return fig
    speakers = df["speaker_name"].value_counts().head(22).index.tolist()
    topics = df["topic_v2"].value_counts().head(16).index.tolist()
    companies = df["speaker_company"].value_counts().head(22).index.tolist()
    df = df[df["speaker_name"].isin(speakers) & df["topic_v2"].isin(topics) & df["speaker_company"].isin(companies)]

    def positions(items: list[str]) -> dict[str, float]:
        if len(items) == 1:
            return {items[0]: 0.5}
        return {item: 0.92 - i * (0.84 / (len(items) - 1)) for i, item in enumerate(items)}

    sp, tp, cp = positions(speakers), positions(topics), positions(companies)
    for _, r in df.iterrows():
        if r.speaker_name in sp and r.topic_v2 in tp:
            ax.plot([0.12, 0.5], [sp[r.speaker_name], tp[r.topic_v2]], color=COLORS["blue"], alpha=0.12, linewidth=1.0)
        if r.topic_v2 in tp and r.speaker_company in cp:
            ax.plot([0.5, 0.88], [tp[r.topic_v2], cp[r.speaker_company]], color=COLORS["amber"], alpha=0.12, linewidth=1.0)
    for label, y in sp.items():
        ax.text(0.02, y, clean_label(label, 21), va="center", fontsize=8, color=COLORS["ink"])
    for label, y in tp.items():
        ax.text(0.43, y, clean_label(label, 18), va="center", fontsize=8.5, color="white", bbox=dict(boxstyle="round,pad=0.22", fc=COLORS["violet"], ec="none"))
    for label, y in cp.items():
        ax.text(0.91, y, clean_label(label, 21), va="center", fontsize=8, color=COLORS["ink"])
    ax.text(0.02, 0.965, "Speakers", fontsize=10, fontweight="bold", color=COLORS["muted"])
    ax.text(0.43, 0.965, "Topics", fontsize=10, fontweight="bold", color=COLORS["muted"])
    ax.text(0.91, 0.965, "Companies", fontsize=10, fontweight="bold", color=COLORS["muted"])
    return fig


def module_ai(data: dict[str, pd.DataFrame], state: RunState) -> dict[str, object]:
    topic = data["topic_intel"].copy()
    ct = data["company_topic"].copy()
    alpha = data["alpha"].copy()
    cooc = data["cooccurrence"].copy()
    ai_terms = ["AI x Crypto", "AI Agents", "DePIN", "Infrastructure", "Identity", "Privacy", "Data", "Developer Ecosystem"]
    ai_topic = topic[topic["topic_v2"].apply(lambda x: any(term.lower() in str(x).lower() for term in ai_terms))].copy()
    if ai_topic.empty:
        state.skipped_charts.append("AI module charts skipped: no AI-related topics found.")
        return {"ai_topic": ai_topic}

    graph = nx.Graph()
    center = "AI x Crypto"
    graph.add_node(center)
    available = ai_topic["topic_v2"].tolist()
    graph_edges = []
    for t in available:
        if t == center:
            continue
        weight = cooc_weight(cooc, center, t)
        if weight <= 0:
            weight = max(1, int(ai_topic.loc[ai_topic["topic_v2"].eq(t), "number_of_sessions"].iloc[0] // 2))
        graph.add_edge(center, t, weight=weight)
        graph_edges.append({"source": center, "target": t, "relationship_strength": weight})
    ai_sub = pd.DataFrame(graph_edges)
    ai_sub_table = save_table(ai_sub, "14_ai_sub_narrative_map.csv", state)
    colors = {n: (COLORS["red"] if n == center else COLORS["teal"]) for n in graph.nodes()}
    fig14 = draw_network(graph, "AI Sub-Narrative Map", "14_ai_sub_narrative_map.png", state, colors, top_labels=20)
    add_artifact(state, fig14, ai_sub_table, "How does AI appear inside the Web3 ecosystem?", ["topic_intelligence.csv", "topic_cooccurrence_matrix.csv"], "AI x Crypto is centered; surrounding nodes show adjacent AI-related narratives.", "AI x Crypto connects most clearly to infrastructure, privacy, DePIN, identity, and agent-related themes in the available taxonomy.")

    ai_ct = ct[ct["topic_v2"].isin(available)].drop_duplicates().copy()
    ai_ct = ai_ct.merge(alpha[["company_name", "alpha_watch_score"]], on="company_name", how="left")
    ai_ct = ai_ct.sort_values("alpha_watch_score", ascending=False)
    ai_eco_table = save_table(ai_ct, "15_ai_company_ecosystem.csv", state)
    graph2 = nx.Graph()
    selected_companies = ai_ct["company_name"].dropna().drop_duplicates().head(55).tolist()
    ai_ct_net = ai_ct[ai_ct["company_name"].isin(selected_companies)]
    for r in ai_ct_net.itertuples():
        graph2.add_node(r.company_name, kind="company")
        graph2.add_node(r.topic_v2, kind="topic")
        graph2.add_edge(r.company_name, r.topic_v2, weight=1)
    colors2 = {n: (COLORS["blue"] if d.get("kind") == "company" else COLORS["red"]) for n, d in graph2.nodes(data=True)}
    fig15 = draw_network(graph2, "AI Company Ecosystem", "15_ai_company_ecosystem.png", state, colors2, top_labels=65)
    add_artifact(state, fig15, ai_eco_table, "Which companies are positioned around AI x Crypto and adjacent sub-narratives?", ["company_topic_edges.csv", "company_alpha_scores.csv"], "Blue nodes are companies; red nodes are AI-adjacent topics.", "The ecosystem is broadest around AI x Crypto and Infrastructure, with privacy and identity acting as deeper technical adjacencies.")

    complex_weights = {
        "Infrastructure": 1.0,
        "Security": 0.95,
        "Privacy": 0.95,
        "Developer Ecosystem": 0.9,
        "DePIN": 0.85,
        "Identity": 0.75,
        "AI Agents": 0.55,
        "AI x Crypto": 0.65,
    }
    matrix = ai_topic.copy()
    matrix["technical_complexity_proxy"] = matrix["topic_v2"].map(complex_weights).fillna(0.45) * 100
    matrix["market_demand_proxy"] = (
        0.45 * norm(matrix["number_of_sessions"]) +
        0.30 * norm(matrix["number_of_companies"]) +
        0.25 * norm(matrix["number_of_speakers"])
    ) * 100
    x_med = matrix["technical_complexity_proxy"].median()
    y_med = matrix["market_demand_proxy"].median()
    def ai_quad(row: pd.Series) -> str:
        if row["market_demand_proxy"] >= y_med and row["technical_complexity_proxy"] >= x_med:
            return "Deep-tech infrastructure opportunity"
        if row["market_demand_proxy"] >= y_med and row["technical_complexity_proxy"] < x_med:
            return "GTM/application opportunity"
        if row["market_demand_proxy"] < y_med and row["technical_complexity_proxy"] >= x_med:
            return "Research-heavy niche"
        return "Weak signal"
    matrix["quadrant"] = matrix.apply(ai_quad, axis=1)
    matrix_table = save_table(matrix[["topic_v2", "technical_complexity_proxy", "market_demand_proxy", "quadrant", "number_of_sessions", "number_of_companies", "number_of_speakers"]], "16_ai_crypto_opportunity_matrix.csv", state)
    fig, ax = plt.subplots(figsize=(10, 8))
    color_map = {
        "Deep-tech infrastructure opportunity": COLORS["green"],
        "GTM/application opportunity": COLORS["blue"],
        "Research-heavy niche": COLORS["amber"],
        "Weak signal": COLORS["muted"],
    }
    for q, qdf in matrix.groupby("quadrant"):
        ax.scatter(qdf["technical_complexity_proxy"], qdf["market_demand_proxy"], s=130, label=q, color=color_map[q], alpha=0.8, edgecolor="white")
    ax.axvline(x_med, color=COLORS["grid"], linewidth=1.5)
    ax.axhline(y_med, color=COLORS["grid"], linewidth=1.5)
    for r in matrix.itertuples():
        ax.text(r.technical_complexity_proxy + 1, r.market_demand_proxy + 1, r.topic_v2, fontsize=9)
    setup_axes(ax, "AI x Crypto Opportunity Matrix", "Technical complexity proxy vs market demand proxy.")
    ax.set_xlabel("Technical Complexity Proxy")
    ax.set_ylabel("Market Demand Proxy")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig16 = save_fig(fig, "16_ai_crypto_opportunity_matrix.png", state)
    add_artifact(state, fig16, matrix_table, "Is AI in Web3 infrastructure, application, data, identity, or investment narrative?", ["topic_intelligence.csv", "company_alpha_scores.csv"], "Upper-right topics combine demand and technical depth; upper-left topics are more GTM/application-oriented.", "AI x Crypto has the strongest demand signal, while Infrastructure and Privacy represent deeper technical opportunity spaces.")

    ai_companies = ai_ct.dropna(subset=["company_name"]).head(12)["company_name"].tolist()
    insight = f"""
# Module 5: Where AI Meets Crypto

## Research Question
How exactly does AI appear inside the Web3 ecosystem?

## Method
The module filters for AI x Crypto, AI Agents, DePIN, Infrastructure, Identity, Privacy, Data, and Developer Ecosystem topics. It maps AI-adjacent topic relationships, company-topic participation, and a 2x2 opportunity matrix.

## Required Visualizations
- `figures/14_ai_sub_narrative_map.png`
- `figures/15_ai_company_ecosystem.png`
- `figures/16_ai_crypto_opportunity_matrix.png`

## Written Insights
AI in this agenda appears less like a single product category and more like a cross-stack narrative. The strongest AI-related topics by session count are {", ".join(ai_topic.sort_values("number_of_sessions", ascending=False).head(6).topic_v2.tolist())}.

The data suggests AI is both an application narrative and an infrastructure narrative. AI x Crypto carries broad demand, while infrastructure, privacy, identity, and DePIN represent deeper technical layers where defensibility may come from compute, security, coordination, and data rights.

Companies positioned around AI-adjacent topics include {", ".join(ai_companies)}. This list should be treated as an ecosystem map, not a ranked investment recommendation.

Potential founder opportunities appear strongest where demand and technical depth overlap: AI infrastructure, privacy-preserving AI workflows, identity/data verification, agent tooling, and compliance-aware AI products for crypto-native markets.

This connects directly to the broader conference shift: AI is not replacing crypto narratives; it is becoming a new organizing layer across infrastructure, consumer workflow, identity, and capital allocation.

## Limitations
The taxonomy does not include standalone AI Data, AI Compute, or AI Governance labels, so those sub-narratives are inferred through adjacent topics. Opportunity proxies are heuristic and should be validated with product, customer, and funding data.
"""
    write_md(INSIGHTS / "05_ai_meets_crypto.md", insight, state, True)
    return {"ai_matrix": matrix, "ai_topic": ai_topic}


def cooc_weight(cooc: pd.DataFrame, a: str, b: str) -> float:
    if cooc.empty or "topic" not in cooc.columns:
        return 0
    row = cooc[cooc["topic"].eq(a)]
    if not row.empty and b in row.columns:
        return float(row.iloc[0][b])
    row = cooc[cooc["topic"].eq(b)]
    if not row.empty and a in row.columns:
        return float(row.iloc[0][a])
    return 0


def generate_outline(state: RunState) -> None:
    figure_list = "\n".join([f"- `{a.figure}`" for a in state.artifacts])
    table_list = "\n".join([f"- `{a.table}`" for a in state.artifacts if a.table])
    body = f"""
# Blockchain Futurist 2025: A Data-Driven Map of Where Web3 Is Heading Next

## Subtitle
What {TOTAL_SESSIONS} sessions, {TOTAL_SPEAKERS} speakers, and {TOTAL_COMPANIES} companies reveal about the next cycle of crypto, AI, and digital infrastructure.

## Executive Thesis
Conference agenda data is not just event data. It is attention data. By analyzing Blockchain Futurist Conference 2025, we can infer where Web3 attention, capital, talent, and product energy may move next.

## Section Structure
1. Executive Summary
2. Data & Methodology
3. Module 1: The Attention Economy of Web3
4. Module 2: The Great Narrative Shift
5. Module 3: Finding Signal Before the Market
6. Module 4: Mapping the Web3 Power Network
7. Module 5: Where AI Meets Crypto
8. Limitations
9. Future Work
10. Appendix

## Figure List
{figure_list}

## Table List
{table_list}
"""
    write_md(FINAL / "report_outline.md", body)


def generate_visualization_index(state: RunState) -> None:
    lines = ["# Visualization Index"]
    for i, art in enumerate(state.artifacts, 1):
        lines.append(f"""
## {i}. `{art.figure}`
**Research question answered:** {art.question}

**Data source used:** {", ".join(art.sources)}

**How to read it:** {art.how_to_read}

**Key takeaway:** {art.takeaway}

**Table:** `{art.table or "not applicable"}`
""")
    write_md(FINAL / "visualization_index.md", "\n".join(lines))


def generate_key_insights(results: dict[str, object]) -> None:
    topic = results["attention"]["topic"]
    centrality = results["narrative"]["centrality"]
    migration = results["narrative"]["narrative_groups"]
    alpha = results["signal"]["alpha"]
    opportunity = results["signal"]["opportunity"]
    broker = results["power"]["broker"]
    ai_topic = results["ai"].get("ai_topic", pd.DataFrame())
    insights = [
        ("Attention is concentrated, not evenly distributed.", f"`{topic.iloc[0].topic_v2}` accounts for {int(topic.iloc[0].number_of_sessions)} of {TOTAL_SESSIONS} topic-counted sessions.", "The agenda is organized around a few large attention pools rather than a flat taxonomy.", "Founders and investors should separate broad attention from investable specificity, especially inside the large residual bucket."),
        ("AI x Crypto is a primary named narrative.", f"AI x Crypto has {int(topic[topic.topic_v2.eq('AI x Crypto')].iloc[0].number_of_sessions)} sessions, {int(topic[topic.topic_v2.eq('AI x Crypto')].iloc[0].number_of_companies)} companies, and {int(topic[topic.topic_v2.eq('AI x Crypto')].iloc[0].number_of_speakers)} speakers.", "AI is not a side topic; it is a major cross-stack theme.", "AI-native crypto tooling deserves deeper diligence across infrastructure, agents, data, privacy, and workflow software."),
        ("Narrative power comes from bridges.", f"The top central topics are {', '.join(centrality.head(5).topic_v2.tolist())}.", "Topics that bridge multiple agenda clusters are more useful signal than isolated high-frequency topics.", "Track bridge narratives as early indicators of where capital and talent may converge."),
        ("The agenda points toward infrastructure and institutionalization.", f"The largest narrative groups include {migration.iloc[0].narrative_group} and {migration.iloc[1].narrative_group}.", "The conference is less centered on pure consumer-cycle narratives than on rails, financial markets, and enterprise-grade utility.", "Infrastructure and institutional workflows may offer more durable demand than broad cultural narratives."),
        ("Under-the-radar alpha is a research queue, not a conclusion.", f"High-presence/low-momentum companies include {', '.join(alpha[alpha.quadrant.eq('Under-the-radar alpha')].head(5).company_name.tolist())}.", "Conference attention can surface companies before external enrichment captures market visibility.", "Use this list for manual diligence, not as a definitive ranking."),
        ("External enrichment coverage is the biggest scoring constraint.", "Only a minority of companies have non-low market signal confidence in the current enrichment file.", "Sparse external data makes negative signals especially unreliable.", "The next analysis pass should expand funding, token, developer, hiring, social, and customer datasets."),
        ("Topic opportunity is strongest where attention and alpha overlap.", f"The top topic opportunity scores are {', '.join(opportunity.head(5).topic_v2.tolist())}.", "A topic becomes more interesting when narrative strength aligns with company-level alpha and participation breadth.", "Prioritize these topics for founder landscape mapping and investor pipeline review."),
        ("Narrative brokers are a practical relationship map.", f"The top broker candidates are {', '.join(broker.head(5).speaker_name.tolist())}.", "Cross-topic speakers are likely to see weak signals earlier than single-topic participants.", "These people are high-value interview, partnership, and expert-network targets."),
        ("Companies with topic diversity look like ecosystem nodes.", "Company-topic edges identify organizations spanning multiple themes.", "Topic breadth can signal platform role, media/association role, or infrastructure relevance.", "Multi-topic companies should be evaluated as network connectors, not only as product vendors."),
        ("AI in Web3 is both application and infrastructure.", f"AI-related topics present include {', '.join(ai_topic.topic_v2.tolist()) if not ai_topic.empty else 'no AI topics found'}.", "The data does not support a single AI lane; it appears across agents, infrastructure, privacy, identity, and DePIN.", "Founder opportunities may sit at the boundary of AI workflows and crypto-native trust infrastructure."),
        ("Legacy narratives remain present but less agenda-defining.", "NFT, Gaming, and Creator Economy appear in the taxonomy but do not dominate centrality or grouped attention.", "The consumer-cycle story is not absent, but it is no longer the strongest organizing frame.", "Consumer crypto ideas need sharper utility, distribution, or AI/finance adjacency."),
        ("The report should be read as attention intelligence.", f"The dataset covers {TOTAL_SESSIONS} sessions, {TOTAL_SPEAKERS} speakers, and {TOTAL_COMPANIES} companies.", "Agenda prominence suggests where industry actors are spending scarce conference attention.", "It is a directional map for research prioritization, not proof of market outcomes."),
    ]
    lines = ["# Key Insights"]
    for i, (title, evidence, interpretation, implication) in enumerate(insights, 1):
        lines.append(f"""
## {i}. {title}
**Evidence from dataset:** {evidence}

**Interpretation:** {interpretation}

**Implication:** {implication}
""")
    write_md(FINAL / "key_insights.md", "\n".join(lines))


def generate_final_report(state: RunState, results: dict[str, object]) -> None:
    insight_files = [
        INSIGHTS / "01_attention_economy.md",
        INSIGHTS / "02_narrative_shift.md",
        INSIGHTS / "03_signal_before_market.md",
        INSIGHTS / "04_power_network.md",
        INSIGHTS / "05_ai_meets_crypto.md",
    ]
    modules = "\n\n".join(path.read_text(encoding="utf-8") for path in insight_files if path.exists())
    top_topics = results["attention"]["topic"].head(8)
    body = f"""
# Blockchain Futurist 2025: A Data-Driven Map of Where Web3 Is Heading Next

## Executive Summary
Conference agenda data is not just event data. It is attention data. By analyzing {TOTAL_SESSIONS} sessions, {TOTAL_SPEAKERS} speakers, and {TOTAL_COMPANIES} companies from Blockchain Futurist Conference 2025, this report maps where Web3 attention, capital, talent, and product energy may move next.

The data suggests that the next Web3 cycle is being organized around AI x Crypto, infrastructure, financialization, institutional adoption, and ecosystem power networks. Legacy narratives such as NFT and Gaming remain visible, but they do not appear to be the strongest organizing center of the agenda.

The clearest finding is not that any single topic will win. It is that the industry attention stack is changing: AI, infrastructure, privacy, identity, RWA, payments, and institutional rails increasingly operate as connected narratives rather than isolated categories.

## Data & Methodology
The analysis uses the current project CSVs in `output/` and `output/enriched/`. Topic session counts come primarily from `topic_intelligence.csv`, which sums to the 152-session conference base. Speaker, company, and network views use edge files derived from the cleaned agenda.

Methods include frequency analysis, participation breadth analysis, topic co-occurrence networks, centrality scoring, quadrant analysis, composite opportunity scoring, bipartite network mapping, and AI-adjacent sub-narrative filtering.

Key caveat: this is attention intelligence, not market proof. Agenda prominence can suggest where industry energy is moving, but it does not directly measure revenue, user adoption, token performance, or fundraising outcomes.

## Top Topic Snapshot
{md_table(top_topics[["topic_v2", "number_of_sessions", "number_of_companies", "number_of_speakers"]])}

{modules}

## Limitations
The largest limitation is the large `Other` category, which contains {int(results["attention"]["topic"].iloc[0].number_of_sessions)} sessions and should be manually split before making sharper investment conclusions.

External enrichment coverage is limited. Given the limited external enrichment coverage, company alpha scores should be treated as directional rather than definitive.

Agenda data can identify attention, not causality. It cannot prove market demand, revenue traction, technical quality, or investment returns.

Some source data is OCR-derived, so speaker-company and session-topic associations may require manual review before publication.

## Future Work
Future versions should add funding databases, token data, GitHub activity, social growth, hiring signals, customer announcements, sponsor tiers, stage prominence, session attendance, and historical conference comparisons.

The next analytical upgrade should split `Other` into more precise categories and compare Blockchain Futurist 2025 against prior-year conference agendas to quantify narrative migration over time.

## Appendix
See `visualization_index.md` for the full chart inventory and `tables/` for exported chart data.
"""
    write_md(FINAL / "blockchain_futurist_2025_data_report.md", body)


def generate_run_summary(state: RunState) -> None:
    warnings = "\n".join(f"- {w}" for w in state.warnings) or "- None"
    skipped = "\n".join(f"- {s}" for s in state.skipped_charts) or "- None"
    missing = "\n".join(f"- {m}" for m in state.missing_inputs) or "- None"
    review = "\n".join([
        "- Manually review the large `Other` topic bucket before publishing investment conclusions.",
        "- Verify speaker-company relationships for high-priority outreach lists.",
        "- Expand external enrichment beyond the current seed coverage before treating alpha scores as more than directional.",
        "- Review dense network charts for label readability if the report is converted to slides.",
    ])
    top_topics = md_table(state.top_topics) if state.top_topics is not None else "Not available"
    top_alpha = md_table(state.top_alpha) if state.top_alpha is not None else "Not available"
    top_brokers = md_table(state.top_brokers) if state.top_brokers is not None else "Not available"
    body = f"""
# Final Report Run Summary

## Counts
- Visualizations generated: {len(state.charts)}
- Tables generated: {len(state.tables)}
- Insight files generated: {len(state.insights)}

## Missing Input Files
{missing}

## Skipped Charts
{skipped}

## Data Quality Warnings
{warnings}

## Top 10 Topics By Session Count
{top_topics}

## Top 10 Companies By Alpha Watch Score
{top_alpha}

## Top 10 Speakers By Narrative Broker Score
{top_brokers}

## Recommended Manual Review Items
{review}
"""
    write_md(FINAL / "run_summary.md", body)


def main() -> None:
    ensure_dirs()
    state = RunState()
    data = load_inputs(state)

    results: dict[str, object] = {}
    if not state.missing_inputs:
        results["attention"] = module_attention(data, state)
        results["narrative"] = module_narrative(data, state)
        results["signal"] = module_signal(data, state)
        results["power"] = module_power(data, state)
        results["ai"] = module_ai(data, state)
        generate_outline(state)
        generate_visualization_index(state)
        generate_key_insights(results)
        generate_final_report(state, results)
    else:
        state.skipped_charts.append("All charts skipped because required inputs were missing.")

    generate_run_summary(state)

    print("Validation Summary")
    print("==================")
    print(f"Total charts generated: {len(state.charts)}")
    print(f"Total tables generated: {len(state.tables)}")
    print(f"Total insight files generated: {len(state.insights)}")
    print("\nTop 10 topics by session count:")
    print(state.top_topics.to_string(index=False) if state.top_topics is not None else "Not available")
    print("\nTop 10 companies by alpha_watch_score:")
    print(state.top_alpha.to_string(index=False) if state.top_alpha is not None else "Not available")
    print("\nTop 10 speakers by narrative_broker_score:")
    print(state.top_brokers.to_string(index=False) if state.top_brokers is not None else "Not available")
    print("\nCharts skipped and why:")
    print("\n".join(state.skipped_charts) if state.skipped_charts else "None")
    print("\nData quality warnings:")
    print("\n".join(state.warnings) if state.warnings else "None")


if __name__ == "__main__":
    main()
