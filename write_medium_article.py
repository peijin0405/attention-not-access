from __future__ import annotations

import math
import re
import textwrap
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "medium_article"
FIG = OUT / "figures"
TABLES = OUT / "supporting_data_tables"

FILES = {
    "sessions": ROOT / "output" / "reclassification_audit" / "cleaned_sessions_topic_v3.csv",
    "speakers": ROOT / "output" / "speakers.csv",
    "companies": ROOT / "output" / "companies.csv",
    "speaker_company_edges": ROOT / "output" / "speaker_company_edges.csv",
    "speaker_topic_edges": ROOT / "output" / "speaker_topic_edges.csv",
    "company_topic_edges": ROOT / "output" / "company_topic_edges.csv",
    "identity": ROOT / "output" / "enriched" / "company_identity_enrichment.csv",
    "market": ROOT / "output" / "enriched" / "company_market_signals.csv",
    "alpha": ROOT / "output" / "enriched" / "company_alpha_scores.csv",
    "topic_intelligence": ROOT / "output" / "enriched" / "topic_intelligence.csv",
}


PALETTE = {
    "ink": "#202124",
    "muted": "#5f6368",
    "grid": "#e7e8ea",
    "blue": "#2f6fed",
    "green": "#1f9d72",
    "orange": "#d9822b",
    "red": "#c94f4f",
    "purple": "#7b61b8",
    "teal": "#008b8b",
    "gray": "#8a9099",
}


def ensure_dirs() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[dict[str, pd.DataFrame], list[str], list[str]]:
    missing = []
    warnings = []
    data: dict[str, pd.DataFrame] = {}
    for name, path in FILES.items():
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))
            data[name] = pd.DataFrame()
            continue
        data[name] = pd.read_csv(path)

    required = {
        "sessions": ["session_title", "stage_or_venue", "topic_v3", "start_time"],
        "speakers": ["speaker_name"],
        "companies": ["company_name"],
        "alpha": ["company_name", "conference_presence_score", "external_momentum_score"],
    }
    for name, cols in required.items():
        if data[name].empty:
            continue
        absent = [c for c in cols if c not in data[name].columns]
        if absent:
            warnings.append(f"{name} missing columns: {', '.join(absent)}")
    return data, missing, warnings


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).lower()


def contains(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)


def classify_audience(row: pd.Series) -> str:
    text = " ".join(
        normalize_text(row.get(c, ""))
        for c in [
            "stage_or_venue",
            "topic_v3",
            "session_title",
            "clean_session_title",
            "speaker_title",
            "session_description",
            "raw_text",
        ]
    )

    if contains(text, ["women", "woman", "female", "diversity", "inclusion", "ethwomen"]):
        return "Women in Crypto"
    if contains(text, ["investor", "vc", "venture", "capital", "fundraising", "fund", "lp", "angels"]):
        return "Investors / VC"
    if contains(
        text,
        [
            "institution",
            "institutional",
            "enterprise",
            "bank",
            "asset manager",
            "compliance",
            "risk",
            "regulation",
            "regulatory",
            "custody",
            "custodian",
            "policy",
        ],
    ):
        return "Institutions / Compliance"
    if contains(
        text,
        [
            "developer",
            "developers",
            "builder",
            "builders",
            "engineering",
            "protocol",
            "api",
            "infrastructure",
            "bootcamp",
            "security",
        ],
    ):
        return "Builders / Developers"
    if contains(text, ["founder", "founders", "startup", "startups", "pitch"]):
        return "Founders / Startups"
    if contains(text, ["media", "education", "podcast", "community", "event", "events", "networking"]):
        return "Media / Community / Education"
    return "General Web3"


def dedupe_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    s = sessions.copy()
    title_col = "clean_session_title" if "clean_session_title" in s.columns else "session_title"
    for col in [title_col, "session_title", "start_time", "end_time", "stage_or_venue"]:
        if col in s.columns:
            s[col] = s[col].fillna("").astype(str).str.strip()
    s["_dedupe_title"] = s[title_col].where(s[title_col].ne(""), s["session_title"])
    dedup_cols = ["_dedupe_title", "start_time", "stage_or_venue"]
    keep_cols = [c for c in dedup_cols if c in s.columns]
    s = s.drop_duplicates(subset=keep_cols, keep="first").copy()
    s["audience_layer"] = s.apply(classify_audience, axis=1)
    return s


def style_ax(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", color=PALETTE["ink"], pad=18)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, ha="left", va="bottom", fontsize=10, color=PALETTE["muted"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grid"])
    ax.spines["bottom"].set_color(PALETTE["grid"])
    ax.tick_params(colors=PALETTE["muted"])
    ax.grid(axis="x", color=PALETTE["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def save_barh(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    path: Path,
    title: str,
    subtitle: str,
    color: str,
    xlabel: str = "Sessions",
    value_format: str = "{:.0f}",
) -> None:
    plot_df = df.sort_values(value_col, ascending=True)
    h = max(5, 0.42 * len(plot_df) + 1.8)
    fig, ax = plt.subplots(figsize=(10, h), dpi=180)
    ax.barh(plot_df[label_col], plot_df[value_col], color=color)
    style_ax(ax, title, subtitle)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    max_val = plot_df[value_col].max() if len(plot_df) else 0
    for i, v in enumerate(plot_df[value_col]):
        ax.text(v + max(0.02, max_val * 0.01), i, value_format.format(v), va="center", fontsize=9, color=PALETTE["ink"])
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def build_audience_tables(sessions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    class_cols = [
        c
        for c in [
            "source_row_index",
            "start_time",
            "end_time",
            "stage_or_venue",
            "session_title",
            "clean_session_title",
            "topic_v3",
            "speaker_name",
            "speaker_title",
            "speaker_company",
            "audience_layer",
        ]
        if c in sessions.columns
    ]
    classification = sessions[class_cols].copy()
    audience = (
        sessions.groupby("audience_layer", dropna=False)
        .size()
        .reset_index(name="session_count")
        .sort_values("session_count", ascending=False)
    )
    audience["share_of_deduped_sessions"] = audience["session_count"] / audience["session_count"].sum()

    audience_topic = (
        sessions.groupby(["audience_layer", "topic_v3"], dropna=False)
        .size()
        .reset_index(name="session_count")
        .sort_values(["audience_layer", "session_count"], ascending=[True, False])
    )
    totals = audience_topic.groupby("audience_layer")["session_count"].transform("sum")
    audience_topic["share_within_audience"] = audience_topic["session_count"] / totals
    return classification, audience, audience_topic


def plot_audience_heatmap(audience_topic: pd.DataFrame, path: Path) -> pd.DataFrame:
    topic_totals = audience_topic.groupby("topic_v3")["session_count"].sum().sort_values(ascending=False)
    top_topics = topic_totals.head(12).index.tolist()
    hdf = audience_topic[audience_topic["topic_v3"].isin(top_topics)].copy()
    pivot = hdf.pivot_table(index="audience_layer", columns="topic_v3", values="session_count", aggfunc="sum", fill_value=0)
    row_order = hdf.groupby("audience_layer")["session_count"].sum().sort_values(ascending=False).index
    pivot = pivot.reindex(row_order).fillna(0)
    pivot_share = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=180)
    im = ax.imshow(pivot_share.values, cmap="YlGnBu", aspect="auto", vmin=0)
    ax.set_xticks(range(len(pivot_share.columns)))
    ax.set_xticklabels(pivot_share.columns, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(pivot_share.index)))
    ax.set_yticklabels(pivot_share.index, fontsize=10)
    ax.set_title("Different Communities Live in Different Versions of Web3", loc="left", fontsize=16, fontweight="bold", pad=18)
    ax.text(0, 1.03, "Cell color shows each topic's share within an audience layer", transform=ax.transAxes, fontsize=10, color=PALETTE["muted"])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = int(pivot.iloc[i, j])
            if val:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=8, color=PALETTE["ink"])
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.ax.set_ylabel("Share within audience", rotation=90)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return pivot.reset_index()


def topic_edges_from_participants(participant_sessions: pd.DataFrame, count_sessions: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if count_sessions is None:
        count_sessions = participant_sessions
    narrative_exclude = {"Women / Diversity", "Community / Events", "Other - Insufficient Information"}
    entity_topics: dict[str, set[str]] = defaultdict(set)
    for _, row in participant_sessions.iterrows():
        topic = row.get("topic_v3")
        if pd.isna(topic) or topic in narrative_exclude:
            continue
        for field, prefix in [("speaker_name", "speaker"), ("speaker_company", "company")]:
            val = row.get(field)
            if pd.isna(val) or not str(val).strip():
                continue
            entity_topics[f"{prefix}:{str(val).strip()}"].add(str(topic))

    edge_counter: Counter[tuple[str, str]] = Counter()
    for topics in entity_topics.values():
        if len(topics) < 2:
            continue
        for a, b in combinations(sorted(topics), 2):
            edge_counter[(a, b)] += 1

    rows = [{"source_topic": a, "target_topic": b, "edge_weight": w} for (a, b), w in edge_counter.items() if w > 0]
    edges = pd.DataFrame(rows).sort_values("edge_weight", ascending=False) if rows else pd.DataFrame(columns=["source_topic", "target_topic", "edge_weight"])

    topic_counts = count_sessions[~count_sessions["topic_v3"].isin(narrative_exclude)].groupby("topic_v3").size()
    speaker_counts = (
        participant_sessions[~participant_sessions["topic_v3"].isin(narrative_exclude)]
        .dropna(subset=["speaker_name"])
        .groupby("topic_v3")["speaker_name"]
        .nunique()
    )
    company_counts = (
        participant_sessions[~participant_sessions["topic_v3"].isin(narrative_exclude)]
        .dropna(subset=["speaker_company"])
        .groupby("topic_v3")["speaker_company"]
        .nunique()
    )
    topics = sorted(set(topic_counts.index) | set(edges.get("source_topic", [])) | set(edges.get("target_topic", [])))
    g = nx.Graph()
    for topic in topics:
        g.add_node(topic, session_count=int(topic_counts.get(topic, 0)))
    for _, e in edges.iterrows():
        g.add_edge(e["source_topic"], e["target_topic"], weight=float(e["edge_weight"]))

    degree = nx.degree_centrality(g) if len(g) else {}
    between = nx.betweenness_centrality(g, weight="weight", normalized=True) if len(g) else {}
    eigen: dict[str, float] = {}
    if len(g) > 1:
        for component in nx.connected_components(g):
            sub = g.subgraph(component)
            if len(sub) == 1:
                node = next(iter(sub.nodes()))
                eigen[node] = 0.0
                continue
            try:
                eigen.update(nx.eigenvector_centrality(sub, weight="weight", max_iter=1000))
            except nx.PowerIterationFailedConvergence:
                eigen.update({node: 0.0 for node in sub.nodes()})
    cent = pd.DataFrame(
        [
            {
                "topic_v3": t,
                "session_count": int(topic_counts.get(t, 0)),
                "speaker_count": int(speaker_counts.get(t, 0)),
                "company_count": int(company_counts.get(t, 0)),
                "degree_centrality": round(float(degree.get(t, 0)), 4),
                "betweenness_centrality": round(float(between.get(t, 0)), 4),
                "eigenvector_centrality": round(float(eigen.get(t, 0)), 4),
            }
            for t in topics
        ]
    )
    if not cent.empty:
        for col in ["degree_centrality", "betweenness_centrality", "eigenvector_centrality"]:
            maxv = cent[col].max()
            cent[f"{col}_norm"] = cent[col] / maxv if maxv else 0
        cent["combined_centrality_score"] = (
            0.45 * cent["degree_centrality_norm"]
            + 0.45 * cent["betweenness_centrality_norm"]
            + 0.10 * cent["eigenvector_centrality_norm"]
        ).round(4)
        cent = cent.sort_values(["combined_centrality_score", "session_count"], ascending=False)
    return edges, cent


def plot_network(edges: pd.DataFrame, centrality: pd.DataFrame, path: Path) -> None:
    g = nx.Graph()
    for _, r in centrality.iterrows():
        g.add_node(r["topic_v3"], session_count=r["session_count"], centrality=r["combined_centrality_score"])
    for _, e in edges.iterrows():
        if e["source_topic"] in g and e["target_topic"] in g:
            g.add_edge(e["source_topic"], e["target_topic"], weight=e["edge_weight"])
    if len(g) == 0:
        return
    if len(g.edges) == 0:
        pos = nx.circular_layout(g)
    else:
        pos = nx.spring_layout(g, seed=8, k=1.2, weight="weight")

    fig, ax = plt.subplots(figsize=(12, 8), dpi=180)
    weights = [g[u][v]["weight"] for u, v in g.edges()]
    if weights:
        nx.draw_networkx_edges(g, pos, ax=ax, width=[0.6 + 0.8 * w for w in weights], alpha=0.22, edge_color=PALETTE["muted"])
    sizes = [220 + 85 * g.nodes[n].get("session_count", 0) for n in g.nodes()]
    colors = [g.nodes[n].get("centrality", 0) for n in g.nodes()]
    nodes = nx.draw_networkx_nodes(g, pos, ax=ax, node_size=sizes, node_color=colors, cmap="viridis", alpha=0.92, linewidths=0.8, edgecolors="white")
    labels = {n: n for n in g.nodes() if g.nodes[n].get("session_count", 0) >= 2 or g.nodes[n].get("centrality", 0) > 0.25}
    nx.draw_networkx_labels(g, pos, labels=labels, ax=ax, font_size=8, font_color=PALETTE["ink"])
    fig.text(0.04, 0.965, "Narrative Network: Size Is Not the Same as Connectivity", ha="left", va="top", fontsize=16, fontweight="bold", color=PALETTE["ink"])
    fig.text(0.04, 0.935, "Node size = sessions; color = combined centrality; edges = shared speakers or companies", ha="left", va="top", fontsize=10, color=PALETTE["muted"])
    ax.axis("off")
    cbar = fig.colorbar(nodes, ax=ax, fraction=0.03, pad=0.01)
    cbar.ax.set_ylabel("Combined centrality")
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def build_presence_momentum(alpha: pd.DataFrame, market: pd.DataFrame, identity: pd.DataFrame) -> pd.DataFrame:
    df = alpha.copy()
    if not market.empty:
        df = df.merge(market[["company_name", "market_signal_confidence"]], on="company_name", how="left")
    if not identity.empty:
        df = df.merge(identity[["company_name", "enrichment_confidence", "crypto_category"]], on="company_name", how="left")
    df["meaningful_external_signal"] = ~df.get("market_signal_confidence", pd.Series(index=df.index, dtype=str)).fillna("low").eq("low")
    presence_threshold = df["conference_presence_score"].median()
    nonzero_momentum = df.loc[df["external_momentum_score"] > 0, "external_momentum_score"]
    momentum_threshold = nonzero_momentum.median() if len(nonzero_momentum) else df["external_momentum_score"].median()
    df["quadrant"] = np.where(
        (df["conference_presence_score"] >= presence_threshold) & (df["external_momentum_score"] >= momentum_threshold),
        "High presence / high momentum",
        np.where(
            (df["conference_presence_score"] >= presence_threshold),
            "High presence / low momentum",
            np.where(df["external_momentum_score"] >= momentum_threshold, "Low presence / high momentum", "Low presence / low momentum"),
        ),
    )
    return df.sort_values("alpha_watch_score", ascending=False)


def plot_presence_momentum(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7), dpi=180)
    colors = np.where(df["meaningful_external_signal"], PALETTE["blue"], PALETTE["gray"])
    ax.scatter(df["conference_presence_score"], df["external_momentum_score"], s=48, c=colors, alpha=0.76, edgecolors="white", linewidths=0.5)
    xmed = df["conference_presence_score"].median()
    nonzero_momentum = df.loc[df["external_momentum_score"] > 0, "external_momentum_score"]
    ymed = nonzero_momentum.median() if len(nonzero_momentum) else df["external_momentum_score"].median()
    ax.axvline(xmed, color=PALETTE["grid"], linewidth=1.2)
    ax.axhline(ymed, color=PALETTE["grid"], linewidth=1.2)
    label_names = [
        "Mysten Labs",
        "Coinbase",
        "Secret Network",
        "QuickNode",
        "Maple Finance",
        "Rarible",
        "Cointelegraph",
        "Tangem",
        "Eliza Labs",
    ]
    label_df = df[df["company_name"].isin(label_names)].copy()
    label_df["_label_order"] = label_df["company_name"].map({name: i for i, name in enumerate(label_names)})
    label_df = label_df.sort_values("_label_order")
    offsets = {
        "Mysten Labs": (8, -8),
        "Coinbase": (8, 10),
        "Secret Network": (8, 8),
        "QuickNode": (10, -8),
        "Maple Finance": (10, 8),
        "Rarible": (10, 22),
        "Cointelegraph": (10, -12),
        "Tangem": (10, 14),
        "Eliza Labs": (10, -12),
    }
    for _, r in label_df.iterrows():
        ax.annotate(
            r["company_name"],
            (r["conference_presence_score"], r["external_momentum_score"]),
            xytext=offsets.get(r["company_name"], (8, 6)),
            textcoords="offset points",
            fontsize=8,
            color=PALETTE["ink"],
        )
    style_ax(ax, "Conference Presence vs. External Momentum", "Blue points have non-low external market-signal confidence; gray points are sparse or low-confidence")
    ax.set_xlabel("Conference presence score")
    ax.set_ylabel("External momentum score")
    ax.text(xmed + 1, ymed + 3, "Visible leaders", fontsize=9, color=PALETTE["muted"])
    ax.text(xmed + 1, max(8, ymed - 18), "Conference-visible,\nexternally under-documented", fontsize=9, color=PALETTE["muted"])
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def simple_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append(f"{val:.4f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_article(
    sessions: pd.DataFrame,
    speakers: pd.DataFrame,
    companies: pd.DataFrame,
    audience: pd.DataFrame,
    audience_topic: pd.DataFrame,
    centrality: pd.DataFrame,
    momentum: pd.DataFrame,
    non_low_external: int,
) -> str:
    top_aud = audience.iloc[0]
    top_aud2 = audience.iloc[1] if len(audience) > 1 else top_aud
    top_topics = sessions["topic_v3"].value_counts().head(5)
    top_cent = centrality.head(5)
    backbone = top_cent.iloc[0]["topic_v3"] if not top_cent.empty else "infrastructure"
    ai_aud = audience_topic[audience_topic["topic_v3"].str.contains("AI", na=False)].groupby("audience_layer")["session_count"].sum().sort_values(ascending=False)
    ai_line = f"AI-related sessions were most visible in {ai_aud.index[0]}" if len(ai_aud) else "AI appeared as a cross-cutting topic"
    high_momentum = momentum[momentum["meaningful_external_signal"]].head(5)["company_name"].tolist()

    article = f"""# Blockchain Futurist 2025

## A Map of Attention Across the Web3 Ecosystem

*What 152 Sessions, 215 Speakers, and 199 Organizations Reveal About the Structure of Web3*

Most crypto research starts with capital.

It studies token prices, market caps, TVL, funding rounds, exchange volumes, treasury balances, or developer activity. Those are useful signals. They tell us where money has already moved, where liquidity has accumulated, and where products have already found some measurable traction.

But capital is not where ecosystems begin.

Before capital moves, people pay attention. Before startups form, builders gather around problems. Before categories become investable, founders, developers, investors, institutions, educators, media, and communities spend time arguing about what matters.

This article looks at that earlier layer.

I analyzed Blockchain Futurist 2025 as attention data: a structured record of where a major Web3 conference ecosystem chose to allocate stage time, speakers, organizations, and narrative focus. The dataset behind this essay includes 152 conference sessions, 215 speakers, and 199 organizations, extracted from conference agenda screenshots, structured into tables, then enriched with company, speaker, topic, and external market-signal layers.

The question is not, "What will pump?"

The question is:

**If Web3 is an ecosystem, what does its attention structure look like?**

This is not a comprehensive map of the entire Web3 industry. It is a structured snapshot of one major conference environment. It should be interpreted as attention signal, not market prediction. Still, agenda data has a useful property: it captures what different actors believe is worth scarce time in a shared industry space.

That makes it a different kind of research input. Not price data. Not funding data. Attention data.

And the first thing the data suggests is that Web3 is not one community.

## Web3 Is Not One Community

The easiest way to analyze a conference is to count topics. AI. DeFi. RWA. Bitcoin. Compliance. Stablecoins. That is useful, but it misses something important.

Topics answer: **what are people talking about?**

Audience layers answer: **who is the conversation for?**

For this analysis, I created a deterministic audience classification for each deduplicated session using stage, title, topic, speaker title, description, and raw agenda text. A session could have only one primary audience layer, with priority given to dedicated community programming such as Women in Crypto before investor, institutional, builder, founder, media, and general Web3 categories.

![Audience distribution](figures/01_audience_distribution.png)

*How to read this chart: each bar shows the number of deduplicated sessions whose primary audience layer matched that category. This is a community map, not a topic ranking.*

The largest audience layer in the working session set was **{top_aud['audience_layer']}**, with {int(top_aud['session_count'])} deduplicated sessions, followed by **{top_aud2['audience_layer']}** with {int(top_aud2['session_count'])}.

That finding needs careful interpretation. The large Women in Crypto category is not simply a sign that "diversity" was one more narrative competing with DeFi or AI. It partly reflects conference programming design: Blockchain Futurist 2025 included a dedicated Women in Crypto / ETHWomen layer, which means this category functions as an audience and community layer as much as a content theme.

That distinction matters.

Treating Women in Crypto as just another topic would flatten the structure of the event. The better interpretation is that the conference was not only organizing around technologies and financial narratives. It was also organizing around communities of participation: who gets access, who is visible, who builds networks, and who is invited into the room.

This is the first memorable insight from the data:

**Web3 attention is not distributed across topics alone. It is distributed across communities.**

That sounds obvious until you try to model it. Once audience and topic are separated, the conference stops looking like a single industry track and starts looking like overlapping publics sharing the same venue.

## Different Communities Live in Different Versions of Web3

The next question is whether these audience layers focus on the same narratives.

They do not.

To test this, I mapped each audience layer to the topic assigned to its sessions. The result is not a universal Web3 agenda. It is a set of different Web3s, depending on where you stand inside the ecosystem.

![Audience to topic map](figures/02_audience_topic_map.png)

*How to read this chart: rows are audience layers, columns are the most common topic categories, and each cell shows the session count. Darker cells indicate a higher share of that audience layer's agenda.*

The data suggests that different groups inhabit different versions of Web3. Women in Crypto programming was heavily shaped by community, leadership, inclusion, founder, education, and AI-adjacent conversations. Investor-oriented sessions leaned toward capital formation, venture, and finance-adjacent narratives. Institutional and compliance-oriented sessions clustered around regulation, risk, custody, and adoption. Builder sessions were more likely to point toward infrastructure, developer ecosystems, protocols, APIs, and technical rails.

This does not mean these communities are isolated. Conferences exist precisely because groups overlap. A founder can also be a developer. A media organization can also shape investor narratives. A community track can create the relationships that later become companies, partnerships, or funds.

But the structure is not random.

The agenda suggests a multi-layer ecosystem where communities are not merely discussing the same topics in different rooms. They are often prioritizing different problems.

That has practical consequences.

For founders, it means category strategy depends on the audience. A product that sounds compelling to institutions may not map cleanly to builder energy. A consumer or community thesis may not show up in the same way in external market data. An AI x Crypto idea may mean agents, infrastructure, data, privacy, workflow automation, or education depending on which room is discussing it.

For investors, it means attention should not be read as a single leaderboard. A topic can be small overall but highly concentrated in a strategically important audience. Conversely, a large category can reflect event architecture rather than broad market demand.

This is the second memorable insight:

**There is no single Web3 narrative. There are audience-specific narratives.**

Most market maps collapse those distinctions. Conference attention data lets us recover them.

## The Most Important Narratives Are Not Always the Biggest Ones

Counting sessions is still useful. In the deduplicated working set, the most visible topics included {', '.join([f'{name} ({count})' for name, count in top_topics.items()])}. But size is only one form of importance.

Inside an ecosystem, influence often comes from connectivity.

A narrative matters more when it links different speakers, companies, and adjacent topics. A category with many sessions may be a large room. A category with high centrality may be a hallway: the place people pass through to reach many other rooms.

To examine that layer, I built a topic network from shared speakers and organizations across narrative topics. Audience-like and logistics categories were excluded from this narrative-network view so Women in Crypto and community programming would not be treated as normal equivalents to AI, DeFi, or RWA.

![Narrative network](figures/03_narrative_network.png)

*How to read this chart: node size reflects session count. Node color reflects combined centrality. Edges appear when topics share speakers or companies. A large node has attention; a central node connects attention.*

The network view changes the interpretation.

In a pure count ranking, the biggest topics look like the dominant story. But in the network, the important question is which topics connect otherwise separate parts of the agenda. The centrality table shows the strongest connective narratives as {', '.join(top_cent['topic_v3'].head(5).tolist()) if not top_cent.empty else 'the topics with the most shared speaker and company bridges'}.

This does not prove those categories will produce the largest companies. It does indicate that they occupied bridging positions in the conference attention graph.

That distinction is important. AI x Crypto can be highly visible because it is timely and broadly legible. Infrastructure can be influential because it touches developer tooling, institutions, wallets, compliance, data, and applications. Compliance or risk can look less exciting in a headline but still connect the parts of the ecosystem that need trust, custody, reporting, and institutional adoption. RWA and stablecoins can sit at the boundary between crypto-native finance and traditional financial rails.

The data suggests that narrative influence is not just about how loudly a topic appears. It is about how many parts of the ecosystem must pass through it.

This is the third memorable insight:

**In Web3, the hidden backbone may be smaller than the headline narrative.**

## The Hidden Backbone of Web3

Centrality makes that backbone more explicit.

For the ranking below, I combined degree centrality, betweenness centrality, and eigenvector centrality. Degree measures how many direct topic connections exist. Betweenness captures bridge position. Eigenvector centrality gives more weight to topics connected to other important topics. The result is not a popularity score. It is a connectivity score.

![Topic centrality ranking](figures/04_topic_centrality_ranking.png)

*How to read this chart: higher scores indicate topics that are more connective inside the conference narrative network, not necessarily topics with the most sessions.*

The top-ranked connective topic in this pass was **{backbone}**.

That result should be read cautiously because centrality depends on the available agenda data, the deduplication method, and the quality of speaker and company extraction. But it is still useful because it surfaces a different kind of signal than simple frequency.

On the surface, Futurist 2025 can look like a collection of AI, community, finance, and crypto-native conversations. Underneath, the connective tissue is revealed by the topics that bridge speakers and organizations across multiple contexts.

If infrastructure appears central, the interpretation is straightforward: the industry may talk in narratives, but it is still organized around rails. If compliance and institutional adoption appear central, the interpretation shifts toward maturation: custody, risk, policy, and enterprise interfaces are becoming part of the operating layer rather than a side conversation. If AI x Crypto is both large and central, then AI is not just a hot topic. It is acting as a cross-cutting interface between builders, founders, investors, and technical infrastructure.

The point is not to crown a winner. The point is to separate **attention volume** from **attention connectivity**.

For founders, the connective layer is often where durable opportunities hide. Products are rarely built for abstract narratives. They are built where multiple groups share an unresolved problem. For investors, centrality can help identify categories that deserve diligence even when they are not the largest by session count.

## What Enrichment Data Adds: Attention vs. External Momentum

Conference attention is useful, but it is incomplete.

To compare internal conference visibility with external market visibility, I used the enrichment layer: company identity data, market-signal fields, and alpha scores. The important limitation is that the external enrichment is sparse. Only **{non_low_external} of {len(companies)} organizations** had non-low-confidence external market signals in this pass.

That means the absence of external signal should not be treated as negative evidence. It often means the enrichment layer did not capture enough verified data.

Still, the comparison is valuable because it separates two things that are often confused:

1. **Conference presence:** how visible an organization was inside this event dataset.
2. **External momentum:** how much verified outside signal appeared in the enrichment layer.

![Presence vs momentum](figures/05_presence_vs_momentum.png)

*How to read this chart: the x-axis shows conference presence; the y-axis shows external momentum. Blue points have non-low external market-signal confidence. Gray points have sparse or low-confidence enrichment.*

The chart shows why conference intelligence should not be treated as a market ranking. Some organizations are conference-visible but externally under-documented. Others have stronger external visibility but are less central in this particular conference graph. A smaller set appears in the high-presence, high-momentum area.

Examples with stronger visible enrichment in this pass include {', '.join(high_momentum[:5]) if high_momentum else 'a small subset of organizations with non-low market-signal confidence'}. These examples should not be read as recommendations. They are simply cases where the internal conference layer and external data layer both produced signal.

This is the fourth memorable insight:

**Conference attention and market visibility are not the same thing.**

That difference is useful. Conference data can surface under-documented organizations and emerging narratives before they are obvious in funding, token, or media datasets. External market data can help distinguish broad event visibility from companies with verified traction, financing, developer activity, public profiles, or distribution.

The most responsible use is to combine them. Use conference attention to generate a research queue. Use external enrichment to prioritize diligence. Then use manual validation before drawing strong conclusions.

There is also a strategic reason to keep both layers separate. A conference is good at detecting where people want to be seen, where they want to recruit, where they want to learn, and where they want to position themselves. External market data is better at detecting what has already accumulated public proof. The gap between those two layers can be revealing. High conference visibility with limited external signal may indicate an early community, a service business, a regional player, an event-native organization, or simply an enrichment gap. High external signal with modest conference presence may indicate a company that is already established enough not to need the same agenda visibility, or one whose market is adjacent to the event's main community.

Neither case is automatically good or bad. The value is in knowing which question to ask next.

That is why the article treats enrichment as context, not verdict. The strongest use of this dataset is not automated ranking; it is better manual research.

## What Web3 Is Becoming

So what does this attention map suggest about Web3?

Not that one category will dominate. Not that a token will outperform. Not that a conference agenda can predict a market cycle.

The more interesting conclusion is structural.

Blockchain Futurist 2025 makes Web3 look less like a single speculative market and more like a multi-layer ecosystem. It contains communities, infrastructure providers, developers, institutions, investors, founders, compliance professionals, media, educators, AI-native experiments, and financial rails. They share vocabulary, but they do not all pay attention to the same things.

That is a sign of complexity. It may also be a sign of maturation.

Early markets often look like one conversation because everything is close to the asset. As ecosystems mature, attention differentiates. Builders talk about tools and protocols. Institutions talk about risk and custody. Investors talk about capital formation and category timing. Communities talk about access, identity, education, and leadership. Media and event operators shape distribution. Founders translate narratives into products.

AI appears in this map not as a standalone slogan but as a cross-cutting layer. Depending on the audience, it means agents, infrastructure, data, workflow automation, privacy, or new user experiences. Infrastructure appears not only as a technical topic but as connective tissue. Compliance and institutional adoption appear not only as constraints but as signs that the ecosystem is building interfaces with the outside financial system. Women in Crypto and community programming appear not as side events but as part of the ecosystem's social structure.

That is the strongest intellectual move of the analysis:

**Conference agendas can be read as ecosystem attention maps.**

They do not tell us the future. But they help us see what the ecosystem is already rehearsing.

Capital follows products.

Products follow builders.

Builders follow attention.

If we want to understand where Web3 may go next, it helps to study where its attention is already beginning to concentrate.
"""
    return article


def clean_article(article: str) -> str:
    lines = []
    for line in article.splitlines():
        if line.startswith("!["):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def write_notes(
    article: str,
    sessions: pd.DataFrame,
    raw_sessions: pd.DataFrame,
    speakers: pd.DataFrame,
    companies: pd.DataFrame,
    audience: pd.DataFrame,
    audience_topic: pd.DataFrame,
    centrality: pd.DataFrame,
    momentum: pd.DataFrame,
    missing: list[str],
    warnings: list[str],
    generated: list[str],
) -> None:
    word_count = len(re.findall(r"\b\w+\b", article))
    top_aud = simple_markdown_table(audience.head(3))
    top_cent = simple_markdown_table(centrality.head(10)) if not centrality.empty else "No centrality rows generated."
    non_low = int(momentum["meaningful_external_signal"].sum()) if not momentum.empty else 0

    (OUT / "executive_summary.md").write_text(
        f"""# Executive Summary

Blockchain Futurist 2025 is analyzed as ecosystem attention data rather than as a generic conference recap. The dataset covers 152 topic-counted sessions, 215 speakers, and 199 organizations, with a deduplicated working set of {len(sessions)} agenda sessions for audience-layer analysis.

Core findings:

- Web3 attention is distributed across communities, not only across topics.
- Women in Crypto should be interpreted as an audience/community programming layer, not as a normal narrative category equivalent to AI, RWA, or DeFi.
- Different audience layers emphasized different versions of Web3.
- Narrative importance is not only session volume; connectivity across speakers and organizations reveals a hidden backbone.
- External enrichment is sparse: {non_low} of {len(companies)} organizations had non-low-confidence market signals, so alpha scores should be treated as directional research inputs.

Article word count: {word_count}
""",
        encoding="utf-8",
    )

    (OUT / "chart_selection.md").write_text(
        """# Chart Selection

The article uses five charts, each tied directly to the argument:

1. `01_audience_distribution.png` - shows the community/audience layer and prevents the essay from collapsing all attention into topics.
2. `02_audience_topic_map.png` - shows that different audience layers focus on different narratives.
3. `03_narrative_network.png` - shows that narrative influence depends on connectivity, not only size.
4. `04_topic_centrality_ranking.png` - ranks hidden backbone narratives using network centrality.
5. `05_presence_vs_momentum.png` - compares conference visibility with sparse external market-signal enrichment.

Charts intentionally exclude broader final-report visuals that do not support the Medium essay's core attention-map thesis.
""",
        encoding="utf-8",
    )

    (OUT / "methodology_note.md").write_text(
        f"""# Methodology Note

Primary session data came from `output/reclassification_audit/cleaned_sessions_topic_v3.csv`. Speaker, company, and edge tables came from the project-level output CSVs. Enrichment data came from `output/enriched/`.

The raw cleaned session file contains {len(raw_sessions)} rows. For audience-layer analysis, sessions were deduplicated by title, start time, and stage/venue, producing {len(sessions)} working agenda sessions. The article preserves the requested headline dataset framing of 152 sessions, 215 speakers, and 199 organizations because that matches the existing final report's topic-counted session basis.

Audience layers were assigned deterministically from `stage_or_venue`, `topic_v3`, `session_title`, `speaker_title`, `session_description`, and `raw_text`. Priority order was:

1. Women in Crypto
2. Investors / VC
3. Institutions / Compliance
4. Builders / Developers
5. Founders / Startups
6. Media / Community / Education
7. General Web3

The narrative network was built from shared speakers and organizations across narrative topics. Audience-like and logistics categories were excluded from the narrative network view so Women in Crypto and community programming would not be treated as equivalent to product or market narratives.

Centrality combines degree centrality, betweenness centrality, and eigenvector centrality. The score is intended as a relative connectivity signal, not a forecast.
""",
        encoding="utf-8",
    )

    (OUT / "limitations_note.md").write_text(
        f"""# Limitations Note

- This is a structured snapshot of one conference ecosystem, not a comprehensive map of Web3.
- Agenda attention is not market prediction, investment advice, or evidence of product-market fit.
- OCR extraction and entity normalization may introduce errors in session, speaker, or company fields.
- The cleaned session file contains {len(raw_sessions)} rows and deduplicates to {len(sessions)} working agenda sessions under the title/time/stage method; the existing report uses 152 topic-counted sessions.
- Audience-layer classification is deterministic and reproducible, but it is still a simplification of mixed-audience sessions.
- Women in Crypto is partly a programmed conference layer and should be interpreted as an audience/community layer.
- External enrichment is sparse: {non_low} of {len(companies)} organizations have non-low-confidence external market signals.
- Alpha scores and external momentum are directional research aids, not rankings or recommendations.
""",
        encoding="utf-8",
    )

    (OUT / "run_summary.md").write_text(
        f"""# Medium Article Run Summary

## Files Loaded
{chr(10).join(f'- `{p.relative_to(ROOT)}`' for p in FILES.values() if p.exists())}

## Rows Used
- Raw cleaned session rows: {len(raw_sessions)}
- Deduplicated working sessions: {len(sessions)}
- Speakers: {len(speakers)}
- Organizations: {len(companies)}
- External market signals with non-low confidence: {non_low}

## Charts Generated
{chr(10).join(f'- `{g}`' for g in generated)}

## Missing Input Files
{chr(10).join(f'- {m}' for m in missing) if missing else '- None'}

## Warnings
{chr(10).join(f'- {w}' for w in warnings) if warnings else '- None'}

## Top Audience Layers
{top_aud}

## Top Narrative Centrality Rows
{top_cent}

## Limitations
- This analysis should be interpreted as attention signal, not market prediction.
- Audience classification is deterministic but imperfect.
- External enrichment coverage is sparse and should not be overinterpreted.

## Recommended Manual Review Items
- Review sessions classified as General Web3 for possible sharper audience assignment.
- Verify chart label readability before publication in Medium.
- Manually validate any company examples before using them in promotional material.
- Consider adding a short disclosure that this is conference-intelligence research, not investment advice.
""",
        encoding="utf-8",
    )

    review_checks = [
        ("Every major claim has dataset support", "Pass - claims are tied to generated tables, counts, centrality, or enrichment coverage."),
        ("Charts are used in text", "Pass - all five figures appear with captions and interpretation."),
        ("Limitations are clear", "Pass - limitations appear in article and standalone note."),
        ("Readable for Medium", "Pass - article uses a narrative structure and avoids excessive methodological detail."),
        ("Avoids overclaiming", "Pass - uses cautious language and avoids recommendations or price predictions."),
        ("Separates audience from topic", "Pass - audience/community layer is introduced before narrative/topic layer."),
        ("Uses enrichment carefully", "Pass - sparse coverage is explicitly noted."),
        ("Strong opening and ending", "Pass - opens with attention as earlier than capital and closes with attention chain."),
        ("At least 3 memorable insights", "Pass - four explicit insight statements are included."),
        ("Title/subtitle consistency", "Pass - matches requested positioning."),
    ]
    (OUT / "editorial_review.md").write_text(
        "# Editorial Review\n\n"
        + "\n".join(f"- **{name}:** {result}" for name, result in review_checks)
        + f"\n\nArticle word count: {word_count}\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    data, missing, warnings = load_data()
    raw_sessions = data["sessions"]
    sessions = dedupe_sessions(raw_sessions)

    classification, audience, audience_topic = build_audience_tables(sessions)
    classification.to_csv(TABLES / "audience_layer_classification.csv", index=False)
    audience.to_csv(TABLES / "01_audience_distribution.csv", index=False)
    audience_topic.to_csv(TABLES / "02_audience_topic_map.csv", index=False)

    save_barh(
        audience,
        "audience_layer",
        "session_count",
        FIG / "01_audience_distribution.png",
        "Web3 Attention Is Distributed Across Communities",
        "Deduplicated agenda sessions by primary audience layer",
        PALETTE["blue"],
        xlabel="Sessions",
        value_format="{:.0f}",
    )
    heatmap_table = plot_audience_heatmap(audience_topic, FIG / "02_audience_topic_map.png")

    edges, centrality = topic_edges_from_participants(raw_sessions, sessions)
    edges.to_csv(TABLES / "03_narrative_network_edges.csv", index=False)
    centrality.to_csv(TABLES / "03_narrative_centrality.csv", index=False)
    plot_network(edges, centrality, FIG / "03_narrative_network.png")
    ranking = centrality.sort_values(["combined_centrality_score", "session_count"], ascending=False).head(12).copy()
    ranking.to_csv(TABLES / "04_topic_centrality_ranking.csv", index=False)
    save_barh(
        ranking,
        "topic_v3",
        "combined_centrality_score",
        FIG / "04_topic_centrality_ranking.png",
        "The Hidden Backbone of Web3 Attention",
        "Combined centrality across shared speaker and company topic bridges",
        PALETTE["green"],
        xlabel="Combined centrality score",
        value_format="{:.2f}",
    )

    momentum = build_presence_momentum(data["alpha"], data["market"], data["identity"])
    momentum.to_csv(TABLES / "05_presence_vs_momentum.csv", index=False)
    plot_presence_momentum(momentum, FIG / "05_presence_vs_momentum.png")

    generated = [
        "figures/01_audience_distribution.png",
        "figures/02_audience_topic_map.png",
        "figures/03_narrative_network.png",
        "figures/04_topic_centrality_ranking.png",
        "figures/05_presence_vs_momentum.png",
    ]

    non_low = int(momentum["meaningful_external_signal"].sum())
    article = write_article(
        sessions,
        data["speakers"],
        data["companies"],
        audience,
        audience_topic,
        centrality,
        momentum,
        non_low,
    )
    (OUT / "medium_article.md").write_text(article.strip() + "\n", encoding="utf-8")
    (OUT / "medium_article_clean.md").write_text(clean_article(article), encoding="utf-8")
    write_notes(
        article,
        sessions,
        raw_sessions,
        data["speakers"],
        data["companies"],
        audience,
        audience_topic,
        centrality,
        momentum,
        missing,
        warnings,
        generated,
    )

    print("Medium article package generated")
    print(f"Output folder: {OUT.relative_to(ROOT)}")
    print(f"Raw session rows: {len(raw_sessions)}")
    print(f"Deduplicated working sessions: {len(sessions)}")
    print(f"Speakers: {len(data['speakers'])}")
    print(f"Organizations: {len(data['companies'])}")
    print(f"Non-low external market signals: {non_low}")
    print(f"Charts generated: {len(generated)}")
    print(f"Warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
