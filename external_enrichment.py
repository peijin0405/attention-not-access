#!/usr/bin/env python3
"""
Third-stage external enrichment for the Blockchain Futurist intelligence dataset.

This script does not overwrite prior stage files. It writes a new layer under:
  output/enriched/

External enrichment is intentionally conservative. For companies without a
high-confidence public identity match in the seed map, fields remain blank and
the row is marked low confidence for manual review.
"""

from __future__ import annotations

import csv
import html
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
ENRICHED = OUT / "enriched"
FIGURES = ENRICHED / "figures"


IDENTITY_FIELDS = [
    "company_name",
    "official_website",
    "company_description",
    "crypto_category",
    "token_symbol",
    "ecosystem",
    "headquarters",
    "founded_year",
    "source_url",
    "enrichment_confidence",
    "notes",
]

MARKET_FIELDS = [
    "company_name",
    "funding_status",
    "latest_funding_round",
    "total_funding",
    "investors",
    "token_market_cap",
    "token_price",
    "github_url",
    "github_stars",
    "github_recent_activity",
    "x_twitter_url",
    "x_twitter_followers",
    "linkedin_url",
    "linkedin_employee_count",
    "source_url",
    "market_signal_confidence",
    "notes",
]


# Sourced seed data for entities that can be matched confidently from the OCR
# company list. Volatile values such as token prices/followers are left blank
# unless they are stable enough for a static enrichment pass.
COMPANY_SEEDS = {
    "Coinbase": {
        "official_website": "https://www.coinbase.com/",
        "company_description": "Public crypto exchange and digital asset infrastructure company.",
        "crypto_category": "Exchange / Infrastructure",
        "token_symbol": "COIN",
        "ecosystem": "Multi-chain",
        "headquarters": "Remote-first; United States",
        "founded_year": "2012",
        "source_url": "https://www.coinbase.com/about",
        "enrichment_confidence": "high",
        "funding_status": "Public company",
        "github_url": "https://github.com/coinbase",
        "x_twitter_url": "https://x.com/coinbase",
        "linkedin_url": "https://www.linkedin.com/company/coinbase/",
        "market_signal_confidence": "medium",
    },
    "OKX": {
        "official_website": "https://www.okx.com/",
        "company_description": "Global crypto exchange and Web3 wallet platform.",
        "crypto_category": "Exchange / Wallet",
        "token_symbol": "OKB",
        "ecosystem": "Multi-chain",
        "source_url": "https://www.okx.com/about",
        "enrichment_confidence": "high",
        "x_twitter_url": "https://x.com/okx",
        "linkedin_url": "https://www.linkedin.com/company/okxofficial/",
        "market_signal_confidence": "medium",
    },
    "Secret Network": {
        "official_website": "https://scrt.network/",
        "company_description": "Privacy-preserving smart contract network.",
        "crypto_category": "Privacy / Layer1",
        "token_symbol": "SCRT",
        "ecosystem": "Cosmos",
        "source_url": "https://scrt.network/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/scrtlabs",
        "x_twitter_url": "https://x.com/SecretNetwork",
        "market_signal_confidence": "medium",
    },
    "Maple Finance": {
        "official_website": "https://maple.finance/",
        "company_description": "On-chain asset management and institutional lending marketplace.",
        "crypto_category": "DeFi / Institutional Credit",
        "token_symbol": "SYRUP",
        "ecosystem": "Ethereum / Solana",
        "source_url": "https://maple.finance/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/maple-labs",
        "x_twitter_url": "https://x.com/maplefinance",
        "linkedin_url": "https://www.linkedin.com/company/maple-finance/",
        "market_signal_confidence": "medium",
    },
    "Rarible": {
        "official_website": "https://rarible.com/",
        "company_description": "NFT marketplace and protocol tooling company.",
        "crypto_category": "NFT / Creator Economy",
        "token_symbol": "RARI",
        "ecosystem": "Multi-chain",
        "source_url": "https://rarible.com/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/rarible",
        "x_twitter_url": "https://x.com/rarible",
        "linkedin_url": "https://www.linkedin.com/company/rarible/",
        "market_signal_confidence": "medium",
    },
    "Mysten Labs": {
        "official_website": "https://mystenlabs.com/",
        "company_description": "Builder of Sui and Move-based Web3 infrastructure.",
        "crypto_category": "Layer1 / Infrastructure",
        "token_symbol": "SUI",
        "ecosystem": "Sui",
        "source_url": "https://mystenlabs.com/",
        "enrichment_confidence": "high",
        "funding_status": "Venture-backed",
        "github_url": "https://github.com/MystenLabs",
        "x_twitter_url": "https://x.com/Mysten_Labs",
        "linkedin_url": "https://www.linkedin.com/company/mysten-labs/",
        "market_signal_confidence": "medium",
    },
    "QuickNode": {
        "official_website": "https://www.quicknode.com/",
        "company_description": "Blockchain RPC, API, and developer infrastructure provider.",
        "crypto_category": "Infrastructure / Developer Ecosystem",
        "ecosystem": "Multi-chain",
        "headquarters": "Miami, Florida",
        "source_url": "https://www.quicknode.com/",
        "enrichment_confidence": "high",
        "funding_status": "Venture-backed",
        "github_url": "https://github.com/quiknode-labs",
        "x_twitter_url": "https://x.com/QuickNode",
        "linkedin_url": "https://www.linkedin.com/company/quicknode/",
        "market_signal_confidence": "medium",
    },
    "Transak": {
        "official_website": "https://transak.com/",
        "company_description": "Fiat-to-crypto on-ramp and payments infrastructure.",
        "crypto_category": "Payments / On-ramp",
        "ecosystem": "Multi-chain",
        "source_url": "https://transak.com/",
        "enrichment_confidence": "high",
        "funding_status": "Venture-backed",
        "x_twitter_url": "https://x.com/transak",
        "linkedin_url": "https://www.linkedin.com/company/transak/",
        "market_signal_confidence": "medium",
    },
    "Tangem": {
        "official_website": "https://tangem.com/",
        "company_description": "Hardware wallet and self-custody wallet company.",
        "crypto_category": "Wallet / Security",
        "ecosystem": "Multi-chain",
        "source_url": "https://tangem.com/",
        "enrichment_confidence": "high",
        "x_twitter_url": "https://x.com/tangem",
        "linkedin_url": "https://www.linkedin.com/company/tangem/",
        "market_signal_confidence": "medium",
    },
    "Sequence": {
        "official_website": "https://sequence.xyz/",
        "company_description": "Web3 game and app development stack.",
        "crypto_category": "Gaming / Developer Ecosystem",
        "ecosystem": "EVM",
        "source_url": "https://sequence.xyz/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/0xsequence",
        "x_twitter_url": "https://x.com/0xsequence",
        "linkedin_url": "https://www.linkedin.com/company/sequencehq/",
        "market_signal_confidence": "medium",
    },
    "Eliza Labs": {
        "official_website": "https://elizaos.ai/",
        "company_description": "Open-source AI agent framework and ecosystem.",
        "crypto_category": "AI Agents",
        "ecosystem": "AI x Crypto",
        "source_url": "https://elizaos.ai/",
        "enrichment_confidence": "medium",
        "github_url": "https://github.com/elizaOS/eliza",
        "x_twitter_url": "https://x.com/elizaOS",
        "market_signal_confidence": "medium",
    },
    "Filecoin Foundation": {
        "official_website": "https://fil.org/",
        "company_description": "Organization supporting Filecoin, decentralized storage, and open web infrastructure.",
        "crypto_category": "Infrastructure / Storage",
        "token_symbol": "FIL",
        "ecosystem": "Filecoin",
        "source_url": "https://fil.org/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/filecoin-project",
        "x_twitter_url": "https://x.com/FilFoundation",
        "linkedin_url": "https://www.linkedin.com/company/filecoin-foundation/",
        "market_signal_confidence": "medium",
    },
    "Algorand Foundation": {
        "official_website": "https://algorand.co/",
        "company_description": "Foundation supporting the Algorand Layer 1 blockchain ecosystem.",
        "crypto_category": "Layer1",
        "token_symbol": "ALGO",
        "ecosystem": "Algorand",
        "source_url": "https://algorand.co/",
        "enrichment_confidence": "high",
        "github_url": "https://github.com/algorand",
        "x_twitter_url": "https://x.com/AlgoFoundation",
        "linkedin_url": "https://www.linkedin.com/company/algorand-foundation/",
        "market_signal_confidence": "medium",
    },
    "Dune": {
        "official_website": "https://dune.com/",
        "company_description": "Crypto data analytics platform.",
        "crypto_category": "Data / Analytics",
        "ecosystem": "Multi-chain",
        "source_url": "https://dune.com/",
        "enrichment_confidence": "high",
        "funding_status": "Venture-backed",
        "github_url": "https://github.com/duneanalytics",
        "x_twitter_url": "https://x.com/Dune",
        "linkedin_url": "https://www.linkedin.com/company/duneanalytics/",
        "market_signal_confidence": "medium",
    },
    "A16z": {
        "official_website": "https://a16zcrypto.com/",
        "company_description": "Crypto venture capital platform from Andreessen Horowitz.",
        "crypto_category": "Venture Capital",
        "ecosystem": "Multi-chain",
        "source_url": "https://a16zcrypto.com/",
        "enrichment_confidence": "high",
        "funding_status": "Investor",
        "x_twitter_url": "https://x.com/a16zcrypto",
        "linkedin_url": "https://www.linkedin.com/company/andreessen-horowitz/",
        "market_signal_confidence": "medium",
    },
    "Figment Inc.": {
        "official_website": "https://figment.io/",
        "company_description": "Institutional staking infrastructure provider.",
        "crypto_category": "Infrastructure / Staking",
        "ecosystem": "Multi-chain",
        "source_url": "https://figment.io/",
        "enrichment_confidence": "high",
        "funding_status": "Venture-backed",
        "x_twitter_url": "https://x.com/Figment_io",
        "linkedin_url": "https://www.linkedin.com/company/figment-io/",
        "market_signal_confidence": "medium",
    },
    "Amazon Web Services": {
        "official_website": "https://aws.amazon.com/",
        "company_description": "Cloud infrastructure provider with blockchain and Web3 infrastructure services.",
        "crypto_category": "Cloud / Enterprise Infrastructure",
        "ecosystem": "Enterprise",
        "source_url": "https://aws.amazon.com/",
        "enrichment_confidence": "high",
        "funding_status": "Public company",
        "linkedin_url": "https://www.linkedin.com/company/amazon-web-services/",
        "market_signal_confidence": "medium",
    },
    "EY": {
        "official_website": "https://www.ey.com/",
        "company_description": "Global professional services firm with blockchain, digital asset, and assurance practices.",
        "crypto_category": "Enterprise Blockchain / Consulting",
        "ecosystem": "Enterprise",
        "source_url": "https://www.ey.com/",
        "enrichment_confidence": "high",
        "funding_status": "Private partnership",
        "linkedin_url": "https://www.linkedin.com/company/ernstandyoung/",
        "market_signal_confidence": "medium",
    },
    "Decrypt": {
        "official_website": "https://decrypt.co/",
        "company_description": "Crypto and Web3 media publication.",
        "crypto_category": "Media",
        "ecosystem": "Crypto media",
        "source_url": "https://decrypt.co/",
        "enrichment_confidence": "high",
        "x_twitter_url": "https://x.com/decryptmedia",
        "linkedin_url": "https://www.linkedin.com/company/decrypt-media/",
        "market_signal_confidence": "medium",
    },
    "Cointelegraph": {
        "official_website": "https://cointelegraph.com/",
        "company_description": "Crypto and blockchain media publication.",
        "crypto_category": "Media",
        "ecosystem": "Crypto media",
        "source_url": "https://cointelegraph.com/",
        "enrichment_confidence": "high",
        "x_twitter_url": "https://x.com/Cointelegraph",
        "linkedin_url": "https://www.linkedin.com/company/cointelegraph/",
        "market_signal_confidence": "medium",
    },
    "WonderFi": {
        "official_website": "https://www.wonder.fi/",
        "company_description": "Canadian digital asset and crypto trading platform company.",
        "crypto_category": "Exchange / Financial Services",
        "ecosystem": "Canada",
        "source_url": "https://www.wonder.fi/",
        "enrichment_confidence": "high",
        "funding_status": "Public company",
        "x_twitter_url": "https://x.com/WonderFi",
        "linkedin_url": "https://www.linkedin.com/company/wonderfi/",
        "market_signal_confidence": "medium",
    },
    "BTCS Inc.": {
        "official_website": "https://www.btcs.com/",
        "company_description": "Public blockchain infrastructure and digital asset company.",
        "crypto_category": "Infrastructure / Public Company",
        "ecosystem": "Multi-chain",
        "source_url": "https://www.btcs.com/",
        "enrichment_confidence": "high",
        "funding_status": "Public company",
        "token_symbol": "BTCS",
        "linkedin_url": "https://www.linkedin.com/company/btcs-inc/",
        "market_signal_confidence": "medium",
    },
    "American Bitcoin": {
        "official_website": "https://americanbitcoin.com/",
        "company_description": "Bitcoin mining and accumulation company.",
        "crypto_category": "Bitcoin / Mining",
        "token_symbol": "BTC",
        "ecosystem": "Bitcoin",
        "source_url": "https://americanbitcoin.com/",
        "enrichment_confidence": "medium",
        "x_twitter_url": "https://x.com/AmericanBTC",
        "market_signal_confidence": "low",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def as_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def norm_score(value: float, max_value: float, weight: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(weight, (value / max_value) * weight)


def session_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (row["source_file"], row["start_time"], row["end_time"], row["clean_session_title"])


def external_signal_score(seed: dict[str, str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    if seed.get("funding_status"):
        score += 18
        reasons.append("funding/public-company signal")
    if seed.get("token_symbol") and seed.get("token_symbol") not in {"COIN", "BTCS", "BTC"}:
        score += 16
        reasons.append("token/ecosystem signal")
    elif seed.get("token_symbol"):
        score += 8
        reasons.append("public ticker or crypto asset signal")
    if seed.get("github_url"):
        score += 18
        reasons.append("GitHub presence")
    if seed.get("x_twitter_url"):
        score += 12
        reasons.append("X presence")
    if seed.get("linkedin_url"):
        score += 12
        reasons.append("LinkedIn presence")
    if seed.get("official_website"):
        score += 14
        reasons.append("official website matched")
    return min(100.0, score), reasons


def svg_bar(path: Path, title: str, rows: list[tuple[str, float]], width: int = 1000, height: int = 650) -> None:
    rows = rows[:20]
    margin_l, margin_t, margin_b = 260, 60, 40
    plot_w = width - margin_l - 60
    row_h = max(22, (height - margin_t - margin_b) // max(1, len(rows)))
    max_v = max([v for _, v in rows] or [1])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="30" y="34" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = margin_t + i * row_h
        bw = 0 if max_v == 0 else (value / max_v) * plot_w
        parts.append(f'<text x="20" y="{y+16}" font-family="Arial" font-size="13">{html.escape(label[:34])}</text>')
        parts.append(f'<rect x="{margin_l}" y="{y}" width="{bw:.1f}" height="{row_h-6}" fill="#2563eb"/>')
        parts.append(f'<text x="{margin_l + bw + 8:.1f}" y="{y+16}" font-family="Arial" font-size="13">{value:.1f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_scatter(path: Path, rows: list[dict], width: int = 900, height: int = 650) -> None:
    max_x = max([as_float(r["conference_presence_score"]) for r in rows] or [1])
    max_y = max([as_float(r["external_momentum_score"]) for r in rows] or [1])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<text x="30" y="34" font-family="Arial" font-size="22" font-weight="700">Conference Presence vs External Momentum</text>',
        '<line x1="80" y1="570" x2="840" y2="570" stroke="#111"/>',
        '<line x1="80" y1="570" x2="80" y2="70" stroke="#111"/>',
        '<text x="360" y="620" font-family="Arial" font-size="14">conference_presence_score</text>',
        '<text x="12" y="330" font-family="Arial" font-size="14" transform="rotate(-90 12,330)">external_momentum_score</text>',
    ]
    for r in rows[:80]:
        x = 80 + (as_float(r["conference_presence_score"]) / max_x) * 760
        y = 570 - (as_float(r["external_momentum_score"]) / max_y) * 500
        alpha = as_float(r["alpha_watch_score"])
        radius = 4 + min(9, alpha / 12)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="#dc2626" opacity="0.62"><title>{html.escape(r["company_name"])} alpha={alpha:.1f}</title></circle>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_network(path: Path, edges: list[tuple[str, str]], title: str, width: int = 1100, height: int = 760) -> None:
    edges = edges[:45]
    left_nodes = sorted({a for a, _ in edges})
    right_nodes = sorted({b for _, b in edges})
    left_y = {n: 70 + i * ((height - 120) / max(1, len(left_nodes) - 1)) for i, n in enumerate(left_nodes)}
    right_y = {n: 70 + i * ((height - 120) / max(1, len(right_nodes) - 1)) for i, n in enumerate(right_nodes)}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="30" y="34" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
    ]
    for a, b in edges:
        parts.append(f'<line x1="280" y1="{left_y[a]:.1f}" x2="760" y2="{right_y[b]:.1f}" stroke="#94a3b8" stroke-width="1"/>')
    for n, y in left_y.items():
        parts.append(f'<circle cx="280" cy="{y:.1f}" r="4" fill="#2563eb"/>')
        parts.append(f'<text x="20" y="{y+4:.1f}" font-family="Arial" font-size="12">{html.escape(n[:34])}</text>')
    for n, y in right_y.items():
        parts.append(f'<circle cx="760" cy="{y:.1f}" r="4" fill="#16a34a"/>')
        parts.append(f'<text x="775" y="{y+4:.1f}" font-family="Arial" font-size="12">{html.escape(n[:36])}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    ENRICHED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    companies = read_csv(OUT / "companies.csv")
    sessions = read_csv(OUT / "cleaned_sessions.csv")
    speakers = read_csv(OUT / "speakers.csv")
    speaker_company_edges = read_csv(OUT / "speaker_company_edges.csv")
    company_topic_edges = read_csv(OUT / "company_topic_edges.csv")
    co_rows = read_csv(OUT / "topic_cooccurrence_matrix.csv")

    company_stage = defaultdict(set)
    company_topics = defaultdict(Counter)
    company_sessions = defaultdict(set)
    topic_companies = defaultdict(set)
    topic_speakers = defaultdict(set)
    topic_sessions = defaultdict(set)
    stage_topic = defaultdict(Counter)

    for row in sessions:
        company = row["speaker_company"]
        speaker = row["speaker_name"]
        topic = row["topic_v2"]
        skey = session_key(row)
        if row["stage_or_venue"]:
            stage_topic[row["stage_or_venue"]][topic] += 1
        topic_sessions[topic].add(skey)
        if speaker:
            topic_speakers[topic].add(speaker)
        if company:
            company_stage[company].add(row["stage_or_venue"])
            company_topics[company][topic] += 1
            company_sessions[company].add(skey)
            topic_companies[topic].add(company)

    identity_rows = []
    market_rows = []
    score_rows = []

    max_sessions = max(as_int(c["number_of_sessions"]) for c in companies) or 1
    max_speakers = max(as_int(c["number_of_speakers"]) for c in companies) or 1
    max_topics = max(as_int(c["topic_diversity"]) for c in companies) or 1
    max_stages = max(len(company_stage[c["company_name"]]) for c in companies) or 1

    for c in companies:
        name = c["company_name"]
        seed = COMPANY_SEEDS.get(name, {})
        notes = "" if seed else "No high-confidence external identity match in seed sources; manual review required."
        identity_rows.append({
            "company_name": name,
            "official_website": seed.get("official_website", ""),
            "company_description": seed.get("company_description", ""),
            "crypto_category": seed.get("crypto_category", ""),
            "token_symbol": seed.get("token_symbol", ""),
            "ecosystem": seed.get("ecosystem", ""),
            "headquarters": seed.get("headquarters", ""),
            "founded_year": seed.get("founded_year", ""),
            "source_url": seed.get("source_url", ""),
            "enrichment_confidence": seed.get("enrichment_confidence", "low"),
            "notes": notes,
        })
        ext_score, ext_reasons = external_signal_score(seed)
        market_rows.append({
            "company_name": name,
            "funding_status": seed.get("funding_status", ""),
            "latest_funding_round": seed.get("latest_funding_round", ""),
            "total_funding": seed.get("total_funding", ""),
            "investors": seed.get("investors", ""),
            "token_market_cap": seed.get("token_market_cap", ""),
            "token_price": seed.get("token_price", ""),
            "github_url": seed.get("github_url", ""),
            "github_stars": seed.get("github_stars", ""),
            "github_recent_activity": seed.get("github_recent_activity", ""),
            "x_twitter_url": seed.get("x_twitter_url", ""),
            "x_twitter_followers": seed.get("x_twitter_followers", ""),
            "linkedin_url": seed.get("linkedin_url", ""),
            "linkedin_employee_count": seed.get("linkedin_employee_count", ""),
            "source_url": seed.get("source_url", ""),
            "market_signal_confidence": seed.get("market_signal_confidence", "low"),
            "notes": "; ".join(ext_reasons) if ext_reasons else "No sourced external market signal captured.",
        })
        presence = (
            norm_score(as_int(c["number_of_sessions"]), max_sessions, 38)
            + norm_score(as_int(c["number_of_speakers"]), max_speakers, 27)
            + norm_score(as_int(c["topic_diversity"]), max_topics, 20)
            + norm_score(len(company_stage[name]), max_stages, 15)
        )
        dominant_topics = company_topics[name].most_common(3)
        emerging_bonus = 0
        for topic, _ in dominant_topics:
            if topic in {"AI Agents", "AI x Crypto", "RWA", "DePIN", "Identity", "Developer Ecosystem", "Creator Economy", "Privacy"}:
                emerging_bonus += 5
        mainstream_penalty = 0
        if name in {"Coinbase", "Amazon Web Services", "EY", "OKX", "A16z"}:
            mainstream_penalty = 10
        topic_signal = min(25, sum(count for _, count in dominant_topics) * 3 + emerging_bonus)
        alpha = round((presence * 0.42) + (ext_score * 0.33) + topic_signal - mainstream_penalty, 2)
        score_rows.append({
            "company_name": name,
            "conference_presence_score": round(presence, 2),
            "external_momentum_score": round(ext_score, 2),
            "dominant_topics": "; ".join(f"{t} ({n})" for t, n in dominant_topics),
            "stage_diversity": len(company_stage[name]),
            "emerging_narrative_bonus": emerging_bonus,
            "mainstream_penalty": mainstream_penalty,
            "alpha_watch_score": max(0, alpha),
            "score_notes": "External score uses sourced seed fields only; blanks mean no verified public signal captured in this pass.",
        })

    score_rows.sort(key=lambda r: (-as_float(r["alpha_watch_score"]), r["company_name"]))

    write_csv(ENRICHED / "company_identity_enrichment.csv", identity_rows, IDENTITY_FIELDS)
    write_csv(ENRICHED / "company_market_signals.csv", market_rows, MARKET_FIELDS)
    write_csv(ENRICHED / "company_alpha_scores.csv", score_rows, list(score_rows[0].keys()))

    topic_co = {}
    for row in co_rows:
        topic = row["topic"]
        topic_co[topic] = sum(as_int(v) for k, v in row.items() if k != "topic" and k != topic)
    max_topic_sessions = max(len(v) for v in topic_sessions.values()) or 1
    max_topic_companies = max(len(v) for v in topic_companies.values()) or 1
    max_topic_speakers = max(len(v) for v in topic_speakers.values()) or 1
    max_topic_co = max(topic_co.values()) or 1
    alpha_by_company = {r["company_name"]: as_float(r["alpha_watch_score"]) for r in score_rows}

    topic_rows = []
    for topic in sorted(topic_sessions):
        companies_for_topic = topic_companies[topic]
        speakers_for_topic = topic_speakers[topic]
        alpha_avg = (
            sum(alpha_by_company.get(c, 0) for c in companies_for_topic) / len(companies_for_topic)
            if companies_for_topic else 0.0
        )
        narrative_strength = (
            norm_score(len(topic_sessions[topic]), max_topic_sessions, 40)
            + norm_score(len(companies_for_topic), max_topic_companies, 25)
            + norm_score(len(speakers_for_topic), max_topic_speakers, 20)
            + norm_score(topic_co.get(topic, 0), max_topic_co, 15)
        )
        top_companies = Counter()
        top_speakers = Counter()
        for row in sessions:
            if row["topic_v2"] == topic:
                if row["speaker_company"]:
                    top_companies[row["speaker_company"]] += 1
                if row["speaker_name"]:
                    top_speakers[row["speaker_name"]] += 1
        if topic in {"AI Agents", "AI x Crypto", "RWA", "Privacy", "Identity", "Developer Ecosystem", "DePIN"}:
            investment = "High: emerging narrative with venture-scale whitespace if validated externally."
            founder = "Build narrow tools, compliance wrappers, data products, or workflow software around this narrative."
        elif topic in {"DeFi", "Payments", "Infrastructure", "Institutional Adoption", "Security"}:
            investment = "Medium-high: mature demand with room for specialized infrastructure and distribution."
            founder = "Compete through trust, integrations, compliance, and clear ROI rather than broad platforms."
        elif topic == "Other":
            investment = "Low as a category: requires manual splitting before investment conclusions."
            founder = "Reclassify broad/unclear sessions into sharper customer problems."
        else:
            investment = "Medium: relevant but needs company-level validation."
            founder = "Look for underserved verticals, tooling gaps, and repeated pain points in session titles."
        topic_rows.append({
            "topic_v2": topic,
            "number_of_sessions": len(topic_sessions[topic]),
            "number_of_companies": len(companies_for_topic),
            "number_of_speakers": len(speakers_for_topic),
            "top_companies": "; ".join(c for c, _ in top_companies.most_common(8)),
            "top_speakers": "; ".join(s for s, _ in top_speakers.most_common(8)),
            "average_company_alpha_score": round(alpha_avg, 2),
            "narrative_strength_score": round(narrative_strength, 2),
            "narrative_summary": f"{topic} appeared in {len(topic_sessions[topic])} sessions with {len(companies_for_topic)} companies and {len(speakers_for_topic)} speakers.",
            "investment_relevance": investment,
            "founder_opportunity": founder,
        })
    topic_rows.sort(key=lambda r: (-as_float(r["narrative_strength_score"]), r["topic_v2"]))
    write_csv(ENRICHED / "topic_intelligence.csv", topic_rows, list(topic_rows[0].keys()))

    topic_counts = [(r["topic_v2"], as_float(r["number_of_sessions"])) for r in topic_rows]
    alpha_chart = [(r["company_name"], as_float(r["alpha_watch_score"])) for r in score_rows]
    narrative_chart = [(r["topic_v2"], as_float(r["narrative_strength_score"])) for r in topic_rows]
    svg_bar(FIGURES / "topic_frequency_bar.svg", "Topic Frequency", topic_counts)
    svg_bar(FIGURES / "company_alpha_score_ranking.svg", "Company Alpha Score Ranking", alpha_chart)
    svg_scatter(FIGURES / "presence_vs_external_momentum.svg", score_rows)
    svg_bar(FIGURES / "topic_narrative_strength_ranking.svg", "Topic Narrative Strength", narrative_chart)
    company_topic_network = [(r["company_name"], r["topic_v2"]) for r in company_topic_edges if r["company_name"] in dict(alpha_chart[:35])]
    speaker_company_network = [(r["speaker_name"], r["speaker_company"]) for r in speaker_company_edges[:60]]
    svg_network(FIGURES / "company_topic_network.svg", company_topic_network, "Company-Topic Network")
    svg_network(FIGURES / "speaker_company_network.svg", speaker_company_network, "Speaker-Company Network")

    top_alpha = score_rows[:20]
    top_topics = topic_rows[:10]
    central_speakers = sorted(speakers, key=lambda r: -as_float(r["speaker_influence_score"]))[:15]
    overhyped = [r for r in topic_rows if as_float(r["narrative_strength_score"]) >= 35 and as_float(r["average_company_alpha_score"]) < 20]
    under_radar = [r for r in topic_rows if as_float(r["average_company_alpha_score"]) >= 25 and as_int(r["number_of_sessions"]) <= 6]

    report = [
        "# Web3 Conference Alpha Report",
        "",
        "## Method",
        "",
        "This third-stage layer combines conference-derived presence with conservative external identity signals. External fields are populated only for companies with a high-confidence public-source seed match; otherwise fields are blank and marked for manual review. Volatile metrics such as live token prices, market caps, social followers, and GitHub stars are intentionally left blank unless a reliable source was captured in this pass.",
        "",
        "## Dominant Narratives",
        "",
        "The strongest narratives by conference footprint were AI x Crypto, Ethereum/ETHWomen programming, DeFi, RWA/tokenization, regulation, infrastructure, institutional adoption, and payments. The conference looked less like a single-theme event and more like a market map: mature adoption rails on Main Stage, education and infrastructure on Rooftop/Bootcamp, and AI/ETHWomen tracks carrying newer ecosystem narratives.",
        "",
        "## Potentially Overhyped Narratives",
        "",
        *(f"- {r['topic_v2']}: strong conference narrative but weaker verified company alpha average in this pass." for r in overhyped[:8]),
        "",
        "## Under-The-Radar Narratives",
        "",
        *(f"- {r['topic_v2']}: fewer sessions but stronger average company alpha or emerging-theme bonus." for r in under_radar[:8]),
        "",
        "## Companies Deserving Closer Tracking",
        "",
        "| Company | Alpha | Presence | External Momentum | Dominant Topics |",
        "| --- | ---: | ---: | ---: | --- |",
        *(f"| {r['company_name']} | {r['alpha_watch_score']} | {r['conference_presence_score']} | {r['external_momentum_score']} | {r['dominant_topics']} |" for r in top_alpha),
        "",
        "## Most Central Speakers",
        "",
        "| Speaker | Company | Influence Score | Sessions | Topics | Stages |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
        *(f"| {r['speaker_name']} | {r['speaker_company']} | {r['speaker_influence_score']} | {r['number_of_sessions']} | {r['number_of_topics']} | {r['number_of_stages']} |" for r in central_speakers),
        "",
        "## Founder Opportunities",
        "",
        "- AI agent infrastructure for compliance-heavy crypto workflows, not generic chatbots.",
        "- RWA/tokenization tooling for issuer onboarding, investor reporting, and secondary-market compliance.",
        "- Wallet/payment UX that hides chain complexity while preserving self-custody and auditability.",
        "- Privacy and identity infrastructure for institutions that need selective disclosure rather than full transparency.",
        "- Vertical analytics products that convert conference narratives into investor, BD, and ecosystem-intelligence workflows.",
        "",
        "## LinkedIn / X Post Ideas",
        "",
        "- \"The loudest Blockchain Futurist 2025 story was not just AI x Crypto. It was AI plus Ethereum communities, RWA, DeFi, and institutional rails converging into one adoption stack.\"",
        "- \"Conference presence is not market momentum. The companies worth tracking are where high agenda visibility overlaps with GitHub/social/funding/token signals.\"",
        "- \"Under-the-radar founder idea: compliance-native AI agents for tokenized asset issuers and Web3 finance teams.\"",
        "- \"ETHWomen and AI-track programming show that ecosystem-building is becoming a market signal, not just a community side event.\"",
        "",
        "## Top Topic Scores",
        "",
        "| Topic | Narrative Strength | Sessions | Companies | Speakers | Avg Company Alpha |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *(f"| {r['topic_v2']} | {r['narrative_strength_score']} | {r['number_of_sessions']} | {r['number_of_companies']} | {r['number_of_speakers']} | {r['average_company_alpha_score']} |" for r in top_topics),
        "",
        "## Manual Review Priorities",
        "",
        "- Review all low-confidence company identity rows before using the external enrichment layer for investment decisions.",
        "- Validate OCR-derived company names that look like job titles, podcast names, agencies, or government departments.",
        "- Add API-backed live market data for token market cap, token price, GitHub stars/activity, social followers, and LinkedIn headcount if the dataset will be refreshed regularly.",
    ]
    if not overhyped:
        report.insert(report.index("## Under-The-Radar Narratives") - 1, "- No clear overhyped narrative under the current conservative scoring rules.")
    if not under_radar:
        report.insert(report.index("## Companies Deserving Closer Tracking") - 1, "- No clear under-the-radar narrative under the current conservative scoring rules.")
    (ENRICHED / "web3_conference_alpha_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    companies_with_signals = sum(1 for r in market_rows if r["market_signal_confidence"] != "low")
    missing_website = sum(1 for r in identity_rows if not r["official_website"])
    low_conf = [r for r in identity_rows if r["enrichment_confidence"] == "low"]

    print(f"number of companies enriched: {len(identity_rows)}")
    print(f"number of companies with external signals: {companies_with_signals}")
    print(f"number of companies with missing website: {missing_website}")
    print("\ntop 20 companies by alpha_watch_score:")
    for r in top_alpha:
        print(f"{r['company_name']}: {r['alpha_watch_score']} presence={r['conference_presence_score']} external={r['external_momentum_score']}")
    print("\ntop 10 topics by narrative_strength_score:")
    for r in top_topics:
        print(f"{r['topic_v2']}: {r['narrative_strength_score']} sessions={r['number_of_sessions']} companies={r['number_of_companies']}")
    print("\nlow-confidence enrichment rows for manual review:")
    for r in low_conf[:40]:
        print(f"{r['company_name']}: {r['notes']}")
    if len(low_conf) > 40:
        print(f"... {len(low_conf) - 40} additional low-confidence rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
