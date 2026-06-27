#!/usr/bin/env python3
"""
Second-stage enrichment for the Blockchain Futurist agenda OCR dataset.

Input:
  output/structured_sessions.csv

Outputs:
  output/cleaned_sessions.csv
  output/speakers.csv
  output/companies.csv
  output/speaker_company_edges.csv
  output/speaker_topic_edges.csv
  output/company_topic_edges.csv
  output/conference_summary.md
  output/conference_network_analysis.md
  output/conference_top_speakers.csv
  output/conference_top_companies.csv
  output/topic_cooccurrence_matrix.csv
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
INPUT = OUTPUT / "structured_sessions.csv"

TOPIC_TAXONOMY = [
    "AI x Crypto",
    "AI Agents",
    "DeFi",
    "RWA",
    "Stablecoins",
    "Payments",
    "Bitcoin",
    "Ethereum",
    "Layer1",
    "Layer2",
    "Infrastructure",
    "DePIN",
    "Security",
    "Privacy",
    "Identity",
    "Regulation",
    "Institutional Adoption",
    "Venture Capital",
    "Fundraising",
    "Consumer Crypto",
    "Gaming",
    "NFT",
    "Creator Economy",
    "Education",
    "Developer Ecosystem",
    "Enterprise Blockchain",
    "Supply Chain",
    "Social Impact",
    "Other",
]

TOPIC_RULES = [
    ("AI Agents", ["ai agent", "agents", "autonomous agent", "eliza"]),
    ("AI x Crypto", [" ai ", "artificial intelligence", "machine learning", "digital expression", "ai and art", " ai panel", "argentum ai"]),
    ("DeFi", ["defi", "staking", "yield", "liquidity", "dex", "lending", "tradfi to defi"]),
    ("RWA", ["rwa", "tokeniz", "real estate", "property", "diamond", "mineral", "carbon credit"]),
    ("Stablecoins", ["stablecoin", "usdc", "usdt"]),
    ("Payments", ["payment", "transaction", "fintech", "merchant", "pay", "banking"]),
    ("Bitcoin", ["bitcoin", "btc", "miner", "mining", "digital reserve", "american bitcoin"]),
    ("Ethereum", ["ethereum", "ethwomen", "eth women", "ethdenver", " evm "]),
    ("Layer2", ["layer 2", "l2", "rollup", "scaling"]),
    ("Layer1", ["layer 1", "l1", "solana", "sui", "avalanche", "aptos", "network state"]),
    ("DePIN", ["depin", "physical infrastructure", "wireless", "sensor"]),
    ("Security", ["security", "custody", "risk", "hack", "audit", "trust by design", "data storage"]),
    ("Privacy", ["privacy", "secret network", "confidential"]),
    ("Identity", ["identity", "reputation", "did", "credential", "noid"]),
    ("Regulation", ["regulation", "regulate", "policy", "government", "legal", "compliance", "house of representatives", "borders"]),
    ("Institutional Adoption", ["institutional", "etf", "treasury", "public-markets", "public markets", "tradfi", "asset manager", "digital assets"]),
    ("Venture Capital", ["venture", "investor", "capital", "vc"]),
    ("Fundraising", ["fundraising", "funding", "raise", "pitch"]),
    ("Consumer Crypto", ["consumer", "travel", "social", "retail", "loyalty", "wallet", "hoodies into suits"]),
    ("Gaming", ["gaming", "game", "play-to-earn", "play to earn", "tcg"]),
    ("NFT", ["nft", "collectible", "bitbasel", "rarible"]),
    ("Creator Economy", ["creator", "artist", "art", "expression"]),
    ("Education", ["education", "bootcamp", "institute", "kids", "school", "academy", "learn"]),
    ("Developer Ecosystem", ["developer", "builder", "hackathon", "open source", "web3lab"]),
    ("Enterprise Blockchain", ["enterprise", "business", "supply chain management"]),
    ("Supply Chain", ["supply chain", "traceability", "transparency"]),
    ("Social Impact", ["social impact", "non-profit", "nonprofit", "women", "youth", "foundation", "ocean"]),
    ("Infrastructure", ["infrastructure", "protocol", "web3", "wallet", "node", "oracle", "data", "storage", "quantum"]),
]

TITLE_PREFIX_RE = re.compile(
    r"^\d{1,2}:\d{2}\s*(?:\d+\s*)?[A-Z\\/\s]*\b(?:all|wl)\b\s*>?\s*[€E]?\s*",
    re.IGNORECASE,
)
INVALID_SYMBOL_RE = re.compile(r"[\[\]{}<>€■□●]+")
MULTISPACE_RE = re.compile(r"\s+")

TITLE_PREFIXES = {
    "founder",
    "co-founder",
    "ceo",
    "cto",
    "cfo",
    "coo",
    "president",
    "partner",
    "managing partner",
    "board member",
    "author",
    "chair",
    "director",
    "senator",
}

KNOWN_COMPANY_FIXES = {
    "Blockchain Futurist ia Conference": "Blockchain Futurist Conference",
    "Blockchain FA Futurist Conference": "Blockchain Futurist Conference",
    "Argentum Al": "Argentum AI",
    "BTCS [4 Inc.": "BTCS Inc.",
    "One F Ocean Foundation": "One Ocean Foundation",
    "Bloxcross Inc": "Bloxcross Inc.",
    "NFT-vip.io": "NFT-VIP.io",
    "Women in A Blockchain Canada": "Women in Blockchain Canada",
    "BVI Financial FA Services Commission": "BVI Financial Services Commission",
}

KNOWN_NAME_FIXES = {
    "Samuel Armes Oj": "Samuel Armes",
    "Karen Hsu [4": "Karen Hsu",
    "Kishelle Blaize- [4 Cameron": "Kishelle Blaize-Cameron",
    "Anewbiz .": "Anewbiz",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def basic_clean(value: str) -> str:
    value = value or ""
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = INVALID_SYMBOL_RE.sub("", value)
    value = value.replace(" ,", ",").replace(" .", ".")
    value = re.sub(r"\s+([,.:;!?])", r"\1", value)
    value = re.sub(r"([,.:;!?]){2,}", r"\1", value)
    value = MULTISPACE_RE.sub(" ", value).strip(" \t\r\n-|")
    return value


def clean_title(value: str) -> str:
    value = basic_clean(value)
    value = TITLE_PREFIX_RE.sub("", value)
    value = re.sub(r"^\d{1,2}:\d{2}[A-Z\\/\s]*>\s*[€E]?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bAl\b", "AI", value)
    value = re.sub(r"\s+[A-Z]{1,3}$", "", value).strip()
    value = re.sub(r"^&\s*", "", value)
    return basic_clean(value)


def clean_stage(value: str) -> str:
    value = basic_clean(value)
    value = value.replace("Stagee", "Stage")
    value = value.replace("Argentum Al", "Argentum AI")
    value = value.replace(" | Al", " | AI")
    value = re.sub(r"\bEntic\b", "Entice", value)
    value = value.replace("Ev | nts", "Events")
    value = value.replace("ETHWom | n", "ETHWomen")
    value = re.sub(r"\bStag\b", "Stage", value)
    return basic_clean(value)


def clean_person_name(value: str) -> str:
    value = basic_clean(value)
    value = re.sub(r"\bOj\b$", "", value).strip()
    value = re.sub(r"\bPh\.?D\.?$", "", value).strip(" ,")
    value = re.sub(r"\s*\bFA\b\s*", " ", value).strip()
    value = re.sub(r"\s*\b4\b\s*", " ", value).strip()
    value = re.sub(r"Blaize-\s+Cameron", "Blaize-Cameron", value)
    value = KNOWN_NAME_FIXES.get(value, value)
    return basic_clean(value)


def split_title_company(speaker_title: str, speaker_company: str) -> tuple[str, str]:
    title = basic_clean(speaker_title)
    company = basic_clean(speaker_company)
    company = re.sub(r"\s*\bFA\b\s*", " ", company).strip()
    company = re.sub(r"\s*\b4\b\s*", " ", company).strip()
    company = company.replace("Women in A Blockchain Canada", "Women in Blockchain Canada")
    company = KNOWN_COMPANY_FIXES.get(company, company)
    if "," in company:
        left, right = [basic_clean(x) for x in company.split(",", 1)]
        if left.lower() in TITLE_PREFIXES and right:
            title = title or left
            company = right
    return title, basic_clean(KNOWN_COMPANY_FIXES.get(company, company))


def canonical_key(value: str) -> str:
    value = basic_clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def dedupe_mapping(values: list[str], threshold: float = 0.96) -> dict[str, str]:
    """Map similar cleaned values to one representative without aggressive merging."""
    reps: list[str] = []
    mapping: dict[str, str] = {}
    for value in sorted(set(v for v in values if v), key=lambda x: (canonical_key(x), x)):
        key = canonical_key(value)
        exact = next((rep for rep in reps if canonical_key(rep) == key), None)
        if exact:
            mapping[value] = exact
            continue
        close = None
        for rep in reps:
            if SequenceMatcher(None, key, canonical_key(rep)).ratio() >= threshold:
                close = rep
                break
        if close:
            mapping[value] = close
        else:
            reps.append(value)
            mapping[value] = value
    return mapping


def topic_hits(title: str, description: str = "") -> list[str]:
    text = f" {title} {description} ".lower()
    hits: list[str] = []
    for topic, keywords in TOPIC_RULES:
        if any(keyword in text for keyword in keywords):
            hits.append(topic)
    if not hits:
        hits.append("Other")
    # Infrastructure is broad; keep it secondary when a more specific category exists.
    if len(hits) > 1 and "Infrastructure" in hits:
        hits = [h for h in hits if h != "Infrastructure"] + ["Infrastructure"]
    return hits


def primary_topic(title: str, description: str = "") -> str:
    return topic_hits(title, description)[0]


def session_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("source_file", ""),
        row.get("start_time", ""),
        row.get("end_time", ""),
        row.get("clean_session_title", ""),
    )


def id_for(prefix: str, n: int) -> str:
    return f"{prefix}_{n:04d}"


def score_frequency(freq: int, topics: int, stages: int) -> float:
    return round(freq * 5.0 + topics * 3.0 + stages * 2.0, 2)


def score_company(speakers: int, sessions: int, topics: int) -> float:
    return round(speakers * 4.0 + sessions * 3.0 + topics * 3.0, 2)


def md_table(headers: list[str], rows: list[list[object]], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    out = ["| " + " | ".join(cell(h) for h in headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(cell(x) for x in row) + " |")
    return "\n".join(out)


def bar_lines(counter: Counter, limit: int = 12) -> list[str]:
    if not counter:
        return ["- No data"]
    max_count = max(counter.values())
    lines = []
    for label, count in counter.most_common(limit):
        bar = "#" * max(1, math.ceil(count / max_count * 28))
        lines.append(f"- `{label}` {count} {bar}")
    return lines


def main() -> int:
    OUTPUT.mkdir(exist_ok=True)
    rows = read_rows(INPUT)

    cleaned = []
    for row in rows:
        out = dict(row)
        out["clean_session_title"] = clean_title(row.get("session_title", ""))
        out["stage_or_venue"] = clean_stage(row.get("stage_or_venue", ""))
        out["speaker_name"] = clean_person_name(row.get("speaker_name", ""))
        title, company = split_title_company(row.get("speaker_title", ""), row.get("speaker_company", ""))
        out["speaker_title"] = title
        out["speaker_company"] = company
        out["topic_v2"] = primary_topic(out["clean_session_title"], row.get("session_description", ""))
        cleaned.append(out)

    speaker_map = dedupe_mapping([r["speaker_name"] for r in cleaned if r["speaker_name"]])
    company_map = dedupe_mapping([r["speaker_company"] for r in cleaned if r["speaker_company"]])
    for row in cleaned:
        if row["speaker_name"]:
            row["speaker_name"] = speaker_map.get(row["speaker_name"], row["speaker_name"])
        if row["speaker_company"]:
            row["speaker_company"] = company_map.get(row["speaker_company"], row["speaker_company"])

    clean_fields = list(rows[0].keys()) + ["clean_session_title", "topic_v2"]
    write_csv(OUTPUT / "cleaned_sessions.csv", cleaned, clean_fields)

    sessions_by_key = defaultdict(list)
    for row in cleaned:
        sessions_by_key[session_key(row)].append(row)

    speaker_stats = {}
    for row in cleaned:
        speaker = row["speaker_name"]
        if not speaker:
            continue
        stats = speaker_stats.setdefault(
            speaker,
            {"titles": Counter(), "companies": Counter(), "sessions": set(), "topics": set(), "stages": set()},
        )
        if row["speaker_title"]:
            stats["titles"][row["speaker_title"]] += 1
        if row["speaker_company"]:
            stats["companies"][row["speaker_company"]] += 1
        stats["sessions"].add(session_key(row))
        stats["topics"].add(row["topic_v2"])
        if row["stage_or_venue"]:
            stats["stages"].add(row["stage_or_venue"])

    speakers = []
    for i, (speaker, stats) in enumerate(sorted(speaker_stats.items()), start=1):
        sessions = len(stats["sessions"])
        topics = len(stats["topics"])
        stages = len(stats["stages"])
        speakers.append(
            {
                "speaker_id": id_for("speaker", i),
                "speaker_name": speaker,
                "speaker_title": stats["titles"].most_common(1)[0][0] if stats["titles"] else "",
                "speaker_company": stats["companies"].most_common(1)[0][0] if stats["companies"] else "",
                "number_of_sessions": sessions,
                "number_of_topics": topics,
                "number_of_stages": stages,
                "speaker_influence_score": score_frequency(sessions, topics, stages),
            }
        )

    company_stats = {}
    for row in cleaned:
        company = row["speaker_company"]
        if not company:
            continue
        stats = company_stats.setdefault(company, {"sessions": set(), "speakers": set(), "topics": set()})
        stats["sessions"].add(session_key(row))
        if row["speaker_name"]:
            stats["speakers"].add(row["speaker_name"])
        stats["topics"].add(row["topic_v2"])

    companies = []
    for i, (company, stats) in enumerate(sorted(company_stats.items()), start=1):
        sessions = len(stats["sessions"])
        speakers_n = len(stats["speakers"])
        topics = len(stats["topics"])
        companies.append(
            {
                "company_id": id_for("company", i),
                "company_name": company,
                "number_of_sessions": sessions,
                "number_of_speakers": speakers_n,
                "topic_diversity": topics,
                "company_influence_score": score_company(speakers_n, sessions, topics),
            }
        )

    speakers_sorted = sorted(speakers, key=lambda r: (-float(r["speaker_influence_score"]), r["speaker_name"]))
    companies_sorted = sorted(companies, key=lambda r: (-float(r["company_influence_score"]), r["company_name"]))

    write_csv(
        OUTPUT / "speakers.csv",
        speakers_sorted,
        ["speaker_id", "speaker_name", "speaker_title", "speaker_company", "number_of_sessions", "number_of_topics", "number_of_stages", "speaker_influence_score"],
    )
    write_csv(
        OUTPUT / "companies.csv",
        companies_sorted,
        ["company_id", "company_name", "number_of_sessions", "number_of_speakers", "topic_diversity", "company_influence_score"],
    )
    write_csv(OUTPUT / "conference_top_speakers.csv", speakers_sorted, list(speakers_sorted[0].keys()) if speakers_sorted else [])
    write_csv(OUTPUT / "conference_top_companies.csv", companies_sorted, list(companies_sorted[0].keys()) if companies_sorted else [])

    speaker_company_edges = sorted(
        {("speaker_name", "speaker_company") for _ in []}
        | {(r["speaker_name"], r["speaker_company"]) for r in cleaned if r["speaker_name"] and r["speaker_company"]}
    )
    speaker_topic_edges = sorted({(r["speaker_name"], r["topic_v2"]) for r in cleaned if r["speaker_name"] and r["topic_v2"]})
    company_topic_edges = sorted({(r["speaker_company"], r["topic_v2"]) for r in cleaned if r["speaker_company"] and r["topic_v2"]})
    write_csv(OUTPUT / "speaker_company_edges.csv", [{"speaker_name": a, "speaker_company": b} for a, b in speaker_company_edges], ["speaker_name", "speaker_company"])
    write_csv(OUTPUT / "speaker_topic_edges.csv", [{"speaker_name": a, "topic_v2": b} for a, b in speaker_topic_edges], ["speaker_name", "topic_v2"])
    write_csv(OUTPUT / "company_topic_edges.csv", [{"company_name": a, "topic_v2": b} for a, b in company_topic_edges], ["company_name", "topic_v2"])

    session_records = {}
    for key, group in sessions_by_key.items():
        first = group[0]
        session_records[key] = first

    topic_counts = Counter(r["topic_v2"] for r in session_records.values())
    company_counts = Counter()
    speaker_counts = Counter()
    stage_topic = defaultdict(Counter)
    for key, group in sessions_by_key.items():
        first = group[0]
        topic = first["topic_v2"]
        if first["stage_or_venue"]:
            stage_topic[first["stage_or_venue"]][topic] += 1
        seen_companies = {r["speaker_company"] for r in group if r["speaker_company"]}
        seen_speakers = {r["speaker_name"] for r in group if r["speaker_name"]}
        for company in seen_companies:
            company_counts[company] += 1
        for speaker in seen_speakers:
            speaker_counts[speaker] += 1

    co = {topic: Counter() for topic in TOPIC_TAXONOMY}
    for row in session_records.values():
        hits = topic_hits(row["clean_session_title"], row.get("session_description", ""))
        for a in hits:
            for b in hits:
                co[a][b] += 1
    matrix_rows = []
    for a in TOPIC_TAXONOMY:
        matrix_rows.append({"topic": a, **{b: co[a][b] for b in TOPIC_TAXONOMY}})
    write_csv(OUTPUT / "topic_cooccurrence_matrix.csv", matrix_rows, ["topic"] + TOPIC_TAXONOMY)

    top_stage_rows = []
    for stage, counts in sorted(stage_topic.items()):
        top = counts.most_common(5)
        top_stage_rows.append([stage, ", ".join(f"{topic} ({count})" for topic, count in top)])

    summary = [
        "# Conference Summary",
        "",
        "## Executive Summary",
        "",
        "The agenda data points to a conference narrative centered on AI-enabled Web3, infrastructure, DeFi, tokenization/RWA, regulation, and payments. AI is especially visible through the dedicated Argentum AI track, while Main Stage programming concentrates the broad market narratives: regulation, institutional adoption, Bitcoin, RWA, payments, and DeFi. Rooftop and Bootcamp sessions skew more educational and infrastructure-oriented.",
        "",
        "The strongest emerging trends before wider mainstream adoption were AI agents, AI-generated creator workflows, tokenized real-world assets, consumer wallets/payments, and institution-facing digital asset infrastructure. These appeared alongside more mature themes such as Bitcoin, regulation, and DeFi, suggesting the agenda blended adoption narratives with next-cycle experimentation.",
        "",
        "## Most Discussed Topics",
        "",
        *bar_lines(topic_counts, 15),
        "",
        "## Most Represented Companies",
        "",
        md_table(["Company", "Sessions"], [[k, v] for k, v in company_counts.most_common(15)]),
        "",
        "## Most Represented Speakers",
        "",
        md_table(["Speaker", "Sessions"], [[k, v] for k, v in speaker_counts.most_common(15)]),
        "",
        "## Topic Concentration By Stage",
        "",
        md_table(["Stage / Venue", "Top topics"], top_stage_rows),
        "",
        "## Manual Review Notes",
        "",
        "- OCR-derived titles and company names were normalized conservatively; uncertain missing fields remain blank.",
        "- Date and speaker-title coverage remains limited because the source screenshots generally did not expose those fields.",
        "- Rows marked low confidence in `cleaned_sessions.csv` should be reviewed before publication or quantitative claims.",
    ]
    (OUTPUT / "conference_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    network = [
        "# Conference Network Analysis",
        "",
        "## Network Sizes",
        "",
        f"- Unique speakers: {len(speakers_sorted)}",
        f"- Unique companies: {len(companies_sorted)}",
        f"- Speaker-company edges: {len(speaker_company_edges)}",
        f"- Speaker-topic edges: {len(speaker_topic_edges)}",
        f"- Company-topic edges: {len(company_topic_edges)}",
        "",
        "## Top Speaker Influence Scores",
        "",
        md_table(
            ["Speaker", "Company", "Sessions", "Topics", "Stages", "Score"],
            [[r["speaker_name"], r["speaker_company"], r["number_of_sessions"], r["number_of_topics"], r["number_of_stages"], r["speaker_influence_score"]] for r in speakers_sorted],
            20,
        ),
        "",
        "## Top Company Influence Scores",
        "",
        md_table(
            ["Company", "Sessions", "Speakers", "Topics", "Score"],
            [[r["company_name"], r["number_of_sessions"], r["number_of_speakers"], r["topic_diversity"], r["company_influence_score"]] for r in companies_sorted],
            20,
        ),
        "",
        "## Topic Co-occurrence",
        "",
        "The matrix in `topic_cooccurrence_matrix.csv` counts sessions whose title/description matched multiple taxonomy rules. High co-occurrence indicates overlapping narratives rather than separate agenda slots.",
        "",
        md_table(
            ["Topic", "Strongest overlaps"],
            [
                [
                    topic,
                    ", ".join(f"{other} ({count})" for other, count in counts.most_common(5) if other != topic and count > 0) or "None",
                ]
                for topic, counts in sorted(co.items())
                if counts[topic] > 0
            ],
        ),
    ]
    (OUTPUT / "conference_network_analysis.md").write_text("\n".join(network) + "\n", encoding="utf-8")

    print(f"Rows cleaned: {len(cleaned)}")
    print(f"Unique sessions: {len(session_records)}")
    print(f"Unique speakers: {len(speakers_sorted)}")
    print(f"Unique companies: {len(companies_sorted)}")
    print("\nTop topics:")
    for topic, count in topic_counts.most_common(12):
        print(f"{topic}: {count}")
    print("\nTop companies:")
    for company in companies_sorted[:10]:
        print(f"{company['company_name']}: score={company['company_influence_score']} sessions={company['number_of_sessions']} speakers={company['number_of_speakers']}")
    print("\nTop speakers:")
    for speaker in speakers_sorted[:10]:
        print(f"{speaker['speaker_name']}: score={speaker['speaker_influence_score']} sessions={speaker['number_of_sessions']} topics={speaker['number_of_topics']} stages={speaker['number_of_stages']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
