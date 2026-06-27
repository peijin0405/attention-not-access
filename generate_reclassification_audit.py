#!/usr/bin/env python3
"""Audit and improve topic classification for Blockchain Futurist 2025 sessions."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
AUDIT = OUTPUT / "reclassification_audit"

TAXONOMY = [
    "AI x Crypto",
    "AI Agents",
    "AI Infrastructure",
    "AI Data",
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
    "Developer Ecosystem",
    "Enterprise Blockchain",
    "Supply Chain",
    "DAO / Governance",
    "Mining / Validators",
    "Wallets / Custody",
    "Compliance / Risk",
    "Media / Education",
    "Community / Events",
    "Women / Diversity",
    "Career / Talent",
    "Marketing / Growth",
    "Tokenomics",
    "Exchanges / Trading",
    "Research / Academia",
    "Other - Insufficient Information",
]

OLD_TO_NEW = {
    "Education": "Media / Education",
    "Social Impact": "Community / Events",
}


def txt(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def row_text(row: pd.Series) -> str:
    fields = [
        "clean_session_title",
        "session_title",
        "session_description",
        "speaker_title",
        "speaker_company",
        "stage_or_venue",
        "notes",
    ]
    return " ".join(txt(row.get(c)) for c in fields).lower()


def title_text(row: pd.Series) -> str:
    return " ".join([txt(row.get("clean_session_title")), txt(row.get("session_title"))]).lower()


def has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def clean_old_topic(value: object) -> str:
    old = txt(value).strip()
    return OLD_TO_NEW.get(old, old if old in TAXONOMY else "")


def classify(row: pd.Series) -> tuple[str, str, str, bool]:
    text = row_text(row)
    title = title_text(row)
    stage_company = " ".join([txt(row.get("speaker_company")), txt(row.get("stage_or_venue"))]).lower()
    old = clean_old_topic(row.get("topic_v2"))
    notes = txt(row.get("notes")).lower()

    broken = "missing session title" in notes or (not txt(row.get("clean_session_title")).strip() and not txt(row.get("session_title")).strip())
    if broken:
        return (
            "Other - Insufficient Information",
            "low",
            "Missing or unusable session title; OCR context does not provide enough topic signal.",
            True,
        )

    if re.fullmatch(r"\s*day\s+\d+(\s+1-1)?\s*", title.strip()):
        return (
            "Other - Insufficient Information",
            "low",
            "Day marker without session content; not enough information to infer a topic.",
            True,
        )
    if title.strip() in {"web3.", "web3"}:
        return (
            "Other - Insufficient Information",
            "low",
            "Title is too generic to classify safely despite surrounding OCR context.",
            True,
        )

    # High-confidence exact phrase and named-session overrides.
    exact_rules = [
        (["supply chain management"], "Supply Chain", "Title explicitly references blockchain in supply chain management."),
        (["blockchain for kids"], "Media / Education", "Title explicitly describes educational blockchain programming for children."),
        (["geopolitics of blockchain markets"], "Institutional Adoption", "Title frames blockchain adoption across geopolitical markets."),
        (["so you've got an app", "need distribution"], "Marketing / Growth", "Title focuses on app distribution and go-to-market."),
        (["daos decoded", "disruptor dao"], "DAO / Governance", "Title explicitly references DAOs."),
        (["hoodies into suits", "shaping tomorrow's finance"], "Women / Diversity", "AWIC session about finance and representation on the ETHWomen track."),
        (["power of women-led communities"], "Women / Diversity", "Title explicitly references women-led communities."),
        (["spotlight on success: cryptochicks"], "Women / Diversity", "CryptoChicks spotlight is a women-in-blockchain community session."),
        (["spotlight on success: femt3ch"], "Women / Diversity", "FEMT3CH spotlight is a women/diversity ecosystem session."),
        (["spotlight on success: createher"], "Women / Diversity", "CreateHER Fest spotlight is a women/diversity ecosystem session."),
        (["women in blockchain canada"], "Women / Diversity", "Title/company explicitly references Women in Blockchain Canada."),
        (["harness all possibilities"], "Women / Diversity", "ETHWomen spotlight for a women-focused community organization."),
        (["association for women in cryptocurrency"], "Women / Diversity", "Session is explicitly tied to Association for Women in Cryptocurrency."),
        (["from surviving to thriving", "opens doors for women"], "Women / Diversity", "Title explicitly focuses on blockchain opening doors for women."),
        (["architects of the future", "creating the next era of web3"], "Women / Diversity", "ETHWomen panel centered on women builders in Web3."),
        (["top industry women at the helm"], "Women / Diversity", "Title explicitly centers women leaders."),
        (["from idea to impact", "entrepreneurs driving web3 innovation"], "Women / Diversity", "ETHWomen panel centered on women entrepreneurs."),
        (["bridging worlds", "global trust in blockchain"], "Women / Diversity", "ETHWomen panel; trust/adoption topic is routed through women-in-blockchain programming."),
        (["barriers to breakthroughs"], "Women / Diversity", "ETHWomen panel on overcoming barriers to Web3 adoption."),
        (["crypto in your pocket", "tangem wallet"], "Wallets / Custody", "Title explicitly references Tangem wallet and pocket custody experience."),
        (["store, grow, spend", "personal finance"], "Consumer Crypto", "Title focuses on consumer personal-finance crypto use."),
        (["ip and blockchain"], "Institutional Adoption", "Title connects IP and blockchain to mainstream adoption."),
        (["data-driven crypto trading"], "Exchanges / Trading", "Title explicitly focuses on crypto trading."),
        (["trusted verifiable economic data"], "AI Data", "Title focuses on verifiable economic data infrastructure."),
        (["death of celebrity coins"], "Tokenomics", "Title focuses on celebrity/meme coin dynamics."),
        (["why $pengu"], "Tokenomics", "Title focuses on the $PENGU token/community asset."),
        (["programmable money", "bitcoin covenants"], "Bitcoin", "Title explicitly references Bitcoin covenants."),
        (["bitcoin miner", "digital reserve"], "Mining / Validators", "Title focuses on Bitcoin mining and reserve operations."),
        (["american the home of crypto innovation"], "Bitcoin", "American Bitcoin/Hut 8 session centered on Bitcoin and national crypto innovation."),
        (["make america the home of crypto innovation"], "Bitcoin", "American Bitcoin/Hut 8 session centered on Bitcoin and national crypto innovation."),
        (["quantum computers will steal your coins"], "Security", "Title focuses on post-quantum security risk for crypto assets."),
        (["trust by design", "data storage"], "AI Data", "Title focuses on trusted data storage for the internet."),
        (["aml, risk, and custody"], "Compliance / Risk", "Title explicitly mentions AML, risk, and custody compliance."),
        (["global compliance", "risk"], "Compliance / Risk", "Title explicitly frames global compliance and risk."),
        (["cayman's virtual asset ecosystem"], "Compliance / Risk", "Title emphasizes compliance and execution in a virtual asset jurisdiction."),
        (["from congress to compliance"], "Compliance / Risk", "Title explicitly connects policy with compliance."),
        (["global race to regulate"], "Regulation", "Title explicitly references global regulation of digital finance."),
        (["florida house", "state government"], "Regulation", "Title references blockchain policy and state government."),
        (["payments panel"], "Payments", "Title explicitly identifies a payments panel."),
        (["future payment hub for ai agents"], "AI Agents", "Title explicitly references payments for AI agents."),
        (["stablecoins panel"], "Stablecoins", "Title explicitly identifies stablecoins."),
        (["crypto banking revolution"], "Payments", "Title references crypto banking and rebuilding finance."),
        (["defi & staking"], "DeFi", "Title explicitly identifies DeFi and staking."),
        (["tradfi meets defi"], "DeFi", "Title explicitly connects TradFi and DeFi."),
        (["defi's social layer"], "DeFi", "Title explicitly references DeFi."),
        (["onchain financial services"], "DeFi", "Title focuses on onchain financial services and DeFi."),
        (["tokenized real estate"], "RWA", "Title explicitly references tokenized real estate."),
        (["tokenizing property"], "RWA", "Title explicitly references tokenizing property."),
        (["real world assets"], "RWA", "Title explicitly references RWAs."),
        (["digital assets to tokenized markets"], "RWA", "Title connects investing with tokenized markets."),
        (["building long-term value in digital assets"], "Venture Capital", "Investment panel focused on digital asset investing and long-term value."),
        (["wall street to web3", "capital markets"], "Venture Capital", "Title references Wall Street, Web3, and capital markets."),
        (["future of investing"], "Venture Capital", "Title explicitly focuses on investing."),
        (["coalition", "non-profits and brands embrace digital assets"], "Institutional Adoption", "Title focuses on brands and nonprofits adopting digital assets."),
        (["web3 in travel"], "Consumer Crypto", "Title describes consumer-facing Web3 travel use case."),
        (["quantum, a new era of web 3 gaming"], "Gaming", "Title explicitly references Web3 gaming."),
        (["beyond play", "web3 gaming"], "Gaming", "Title explicitly references Web3 gaming."),
        (["future of ai & gaming"], "Gaming", "Title explicitly combines AI and gaming."),
        (["nft panel"], "NFT", "Title explicitly identifies an NFT panel."),
        (["democratizing ip via nfts"], "NFT", "Title explicitly references NFTs, patents, and IP."),
        (["content creation", "building influence"], "Creator Economy", "Title explicitly focuses on content creation and influence."),
        (["ai and art"], "Creator Economy", "Title focuses on AI-assisted digital expression and art."),
        (["human creativity"], "Creator Economy", "Title focuses on AI and human creativity."),
        (["decentralized agi"], "AI Infrastructure", "Title explicitly references decentralized AGI."),
        (["infrastructure behind intelligence"], "AI Infrastructure", "Title explicitly focuses on AI infrastructure, privacy, and trust."),
        (["internet of ai"], "AI Infrastructure", "Title explicitly references AI network infrastructure."),
        (["ai legacy", "defai"], "AI x Crypto", "Title explicitly connects AI/DeFAI with inheritance."),
        (["agentic ai"], "AI Agents", "Title explicitly references agentic AI and autonomous systems."),
        (["smart money era", "ai and the evolution of digital finance"], "AI x Crypto", "Title explicitly connects AI and digital finance."),
        (["charting the web3 ai frontier"], "AI x Crypto", "Title explicitly frames Web3 AI innovation/risk/opportunity."),
        (["transhumanism", "on-chain"], "AI x Crypto", "Title connects transhumanism, on-chain systems, and Argentum AI."),
        (["peace through trade", "ai integrated"], "AI x Crypto", "Title explicitly mentions AI-integrated blockchain."),
        (["presentation by pavan agarwal from angel ai"], "AI x Crypto", "AI company keynote/presentation in crypto conference context."),
        (["grow your global impact", "secret network"], "Privacy", "Secret Network session likely focuses on privacy-enabled Web3 impact."),
        (["sovereignty protocol"], "Infrastructure", "Title references protocol-level infrastructure."),
        (["aws cloud infrastructure"], "Infrastructure", "Title explicitly references AWS cloud infrastructure."),
        (["infrastructure as opportunity"], "Infrastructure", "Title explicitly references infrastructure opportunity."),
        (["building privacy and communities in web3"], "Developer Ecosystem", "Developer panel on privacy and community building."),
        (["decentralized by design"], "Community / Events", "Title focuses on community in Web3."),
        (["great leap", "web3 will become a mainstream reality"], "Institutional Adoption", "Title focuses on mainstream Web3 adoption."),
        (["building for the greater good"], "Community / Events", "Title frames Web3/emerging tech for social good."),
        (["insights from 200 crypto ceos"], "Research / Academia", "Title indicates research/interview insights from crypto CEOs."),
        (["this time is different for crypto"], "Media / Education", "ZH Media session appears to be market commentary/media education."),
        (["pack your bags for the supercycle"], "Venture Capital", "Sarson Funds title implies investment-cycle market outlook."),
        (["from mania to maturity"], "Institutional Adoption", "Title frames crypto market maturation."),
        (["remarks from the mayor"], "Community / Events", "Civic conference remarks rather than a substantive topic session."),
        (["announcement by dustin stockton"], "Community / Events", "Generic announcement row with limited topic signal."),
        (["presentation by blaer technologies"], "Other - Insufficient Information", "Company presentation title lacks enough topic context to classify reliably."),
    ]
    for terms, topic, reason in exact_rules:
        if all(term in title for term in terms):
            confidence = "low" if topic == "Other - Insufficient Information" else "high"
            return (topic, confidence, reason, confidence == "low")

    if "shefi morning social" in title:
        return (
            "Women / Diversity",
            "medium",
            "SheFi-branded social event; likely women-focused community programming, but title is event-oriented.",
            True,
        )
    if "building the intelligent city" in title:
        return (
            "Institutional Adoption",
            "medium",
            "City of Miami welcome references intelligent-city collaboration and public-sector adoption.",
            False,
        )

    # Event logistics and conference-program rows. Raw OCR text is intentionally
    # excluded here because it often contains neighboring sessions from the same screenshot.
    event_terms = [
        "registration open",
        "doors open",
        "opening remarks",
        "welcoming",
        "closing remarks",
        "vip cabana",
        "rum bar",
        "happy hour",
        "networking",
        "book signing",
        "hard rock guitar",
        "afther hours",
        "nft gallery",
        "gallery",
    ]
    if has_any(title, event_terms):
        if "nft gallery" in title or "gallery by bitbasel" in title:
            return ("NFT", "high", "Title explicitly describes an NFT gallery.", False)
        if "ethwomen" in title or "ethwomen" in stage_company or "awic" in title or "createher" in title or "femt3ch" in title:
            return ("Women / Diversity", "high", "Event/session is explicitly tied to ETHWomen, AWIC, CreateHER, or FEMT3CH.", False)
        if "ai futurist" in title:
            return ("Community / Events", "medium", "AI Futurist opening/closing/logistics row; event context is clear but not a substantive AI session.", False)
        return ("Community / Events", "high", "Title describes conference logistics, networking, social programming, or remarks.", False)

    # Stage and community-track signals.
    if "ethwomen" in title or "ethwomen" in stage_company or "women" in title or "femt3ch" in title or "createher" in title or "cryptochicks" in title or "cryptochicks" in stage_company:
        return ("Women / Diversity", "medium", "Women/ETHWomen/community signal is present, but the title is not fully specific.", False)

    # General keyword fallbacks.
    keyword_rules = [
        (["ai agents", "agentic ai", "autonomous systems"], "AI Agents", "AI-agent keywords in title/text."),
        (["agi", "ai infrastructure", "intelligence", "hypercycle"], "AI Infrastructure", "AI infrastructure or AGI keywords in title/text."),
        (["ai", "artificial intelligence", "defai"], "AI x Crypto", "AI keywords in crypto/Web3 conference context."),
        (["data storage", "verifiable data", "economic data"], "AI Data", "Data infrastructure keywords in title/text."),
        (["defi", "staking", "lending"], "DeFi", "DeFi/staking/lending keywords in title/text."),
        (["real world asset", "rwa", "tokenized real estate", "tokenizing property"], "RWA", "RWA/tokenization keywords in title/text."),
        (["stablecoin"], "Stablecoins", "Stablecoin keyword in title/text."),
        (["payment", "transaction", "banking"], "Payments", "Payments/banking keywords in title/text."),
        (["bitcoin", "miner", "mining"], "Bitcoin", "Bitcoin/mining keywords in title/text."),
        (["ethereum", "ethwomen", "ethdenver"], "Ethereum", "Ethereum ecosystem keywords in title/text."),
        (["layer 1", "layer1"], "Layer1", "Layer1 keywords in title/text."),
        (["layer 2", "layer2", "scaling"], "Layer2", "Layer2/scaling keywords in title/text."),
        (["infrastructure", "protocol", "cloud"], "Infrastructure", "Infrastructure/protocol keywords in title/text."),
        (["depin"], "DePIN", "DePIN keyword in title/text."),
        (["security", "defense", "risk", "quantum"], "Security", "Security/risk keywords in title/text."),
        (["privacy"], "Privacy", "Privacy keyword in title/text."),
        (["identity"], "Identity", "Identity keyword in title/text."),
        (["regulat", "policy", "government", "congress"], "Regulation", "Regulation/policy/government keywords in title/text."),
        (["institutional", "mainstream adoption", "brands embrace", "enterprise"], "Institutional Adoption", "Institutional/mainstream adoption keywords in title/text."),
        (["venture", "fundraising", "capital markets", "investing", "investment"], "Venture Capital", "Capital/investment keywords in title/text."),
        (["consumer", "personal finance", "travel"], "Consumer Crypto", "Consumer-use-case keywords in title/text."),
        (["gaming", "gamefi", "play-to-earn"], "Gaming", "Gaming keywords in title/text."),
        (["nft"], "NFT", "NFT keyword in title/text."),
        (["creator", "content creation", "influence", "art"], "Creator Economy", "Creator/content/art keywords in title/text."),
        (["developer", "dev panel", "building"], "Developer Ecosystem", "Developer/builder keywords in title/text."),
        (["supply chain"], "Supply Chain", "Supply chain keyword in title/text."),
        (["dao", "governance"], "DAO / Governance", "DAO/governance keywords in title/text."),
        (["wallet", "custody"], "Wallets / Custody", "Wallet/custody keywords in title/text."),
        (["compliance", "aml"], "Compliance / Risk", "Compliance/AML keywords in title/text."),
        (["media", "education", "kids", "bootcamp"], "Media / Education", "Media/education/bootcamp keywords in title/text."),
        (["community", "events", "social"], "Community / Events", "Community/event keywords in title/text."),
        (["career", "talent"], "Career / Talent", "Career/talent keywords in title/text."),
        (["marketing", "growth", "distribution"], "Marketing / Growth", "Marketing/growth/distribution keywords in title/text."),
        (["tokenomics", "token", "coin"], "Tokenomics", "Token/coin keywords in title/text."),
        (["exchange", "trading"], "Exchanges / Trading", "Exchange/trading keywords in title/text."),
        (["research", "academia", "institute"], "Research / Academia", "Research/academia keywords in title/text."),
    ]
    for terms, topic, reason in keyword_rules:
        if has_any(title, terms):
            return (topic, "medium", reason, False)

    if "argentum ai stage" in stage_company and "ai" in stage_company and old == "":
        return (
            "AI x Crypto",
            "medium",
            "Generic presentation appears on the AI stage, but title lacks a specific AI subtopic.",
            True,
        )

    if old and old != "Other":
        return (old, "medium", f"Kept prior topic_v2 `{old}`; no stronger conflicting evidence found.", False)

    return (
        "Other - Insufficient Information",
        "low",
        "No reliable title, company, stage, or notes signal mapped to the updated taxonomy.",
        True,
    )


def build_report(df: pd.DataFrame, other_original: pd.DataFrame, other_reclassified: pd.DataFrame, manual: pd.DataFrame, comparison: pd.DataFrame) -> str:
    original_union = len(other_original)
    original_v2 = int((df["topic_v2"].fillna("") == "Other").sum())
    new_insufficient = int((df["topic_v3"] == "Other - Insufficient Information").sum())
    former_other = df["was_original_other_union"]
    former_other_success = int((former_other & (df["topic_v3"] != "Other - Insufficient Information")).sum())
    former_other_remaining = int((former_other & (df["topic_v3"] == "Other - Insufficient Information")).sum())
    reduction = (1 - new_insufficient / original_union) * 100 if original_union else 0
    former_cats = (
        df[former_other & (df["topic_v3"] != "Other - Insufficient Information")]["topic_v3"]
        .value_counts()
        .head(15)
        .reset_index()
    )
    former_cats.columns = ["topic_v3", "former_other_rows"]
    low_count = int((df["reclassification_confidence"] == "low").sum())
    manual_count = len(manual)

    def md_table(data: pd.DataFrame) -> str:
        if data.empty:
            return "None"
        rows = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
        for _, row in data.iterrows():
            rows.append("| " + " | ".join(str(v).replace("|", "/") for v in row.tolist()) + " |")
        return "\n".join(rows)

    manual_preview = manual[
        ["source_row_index", "clean_session_title", "speaker_company", "topic_v2", "topic_v3", "reclassification_confidence", "reclassification_reason"]
    ].head(30)
    distribution = df["topic_v3"].value_counts().head(20).reset_index()
    distribution.columns = ["topic_v3", "row_count"]

    return f"""# Topic Reclassification Audit

## Summary
The audit reclassified all {len(df)} rows in `output/cleaned_sessions.csv` into the expanded `topic_v3` taxonomy. It specifically targeted rows where `topic_v2 == "Other"` or `topic_category == "Other"`, while also correcting non-Other rows when the updated taxonomy provided a clearer category.

## Key Counts
- Original `topic_v2 == Other` rows: {original_v2}
- Original broad Other rows (`topic_v2 == Other` or `topic_category == Other`): {original_union}
- Former broad Other rows successfully reclassified: {former_other_success}
- Former broad Other rows remaining `Other - Insufficient Information`: {former_other_remaining}
- New total `Other - Insufficient Information` rows: {new_insufficient}
- Reduction versus broad original Other set: {reduction:.1f}%
- Low-confidence reclassifications: {low_count}
- Manual review rows: {manual_count}

## Most Common New Categories For Former Other Rows
{md_table(former_cats)}

## Top 20 Topic V3 Categories
{md_table(distribution)}

## Rows Still Needing Manual Review
Rows are flagged when confidence is low, the title is missing or unclear, OCR context is broken, or the classifier found insufficient topic evidence.

{md_table(manual_preview)}

## Did Reducing Other Improve Analytical Usefulness?
Yes. The original `Other` bucket was too large to support useful narrative analysis. Reclassifying event logistics into `Community / Events`, ETHWomen/AWIC/FEMT3CH programming into `Women / Diversity`, wallet sessions into `Wallets / Custody`, compliance sessions into `Compliance / Risk`, and AI infrastructure/data sessions into more specific AI subcategories makes the topic map more interpretable.

The improvement is especially meaningful for conference-intelligence use cases because it separates substantive narratives from event logistics and community programming. This prevents a large residual bucket from dominating attention analysis.

## Risks Of Forcing Non-Other Classification
The main risk is false precision. Some agenda rows are logistical, incomplete, or OCR-damaged. Forcing those rows into substantive categories would inflate narratives that the source data does not actually support.

The audit therefore preserves `Other - Insufficient Information` for rows with missing titles or generic company presentations. It also flags low-confidence rows for manual review. This is preferable to eliminating `Other` at the expense of analytical quality.

## Recommended Next Steps
- Manually inspect `manual_review_rows.csv` before using topic_v3 for final investment or market conclusions.
- Rebuild topic intelligence and topic edge files from `cleaned_sessions_topic_v3.csv` if topic_v3 is adopted.
- Consider splitting `Community / Events` into logistics versus community programming in a later pass if event rows should be excluded from narrative analysis.
"""


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    sessions = pd.read_csv(OUTPUT / "cleaned_sessions.csv")
    sessions = sessions.reset_index().rename(columns={"index": "source_row_index"})

    other_mask = (sessions["topic_v2"].fillna("") == "Other") | (sessions["topic_category"].fillna("") == "Other")
    other_original = sessions.loc[other_mask].copy()
    other_original.to_csv(AUDIT / "other_rows_original.csv", index=False)

    classified = sessions.copy()
    classified["was_original_other_union"] = other_mask
    classified["was_topic_v2_other"] = classified["topic_v2"].fillna("") == "Other"

    results = classified.apply(classify, axis=1, result_type="expand")
    results.columns = ["topic_v3", "reclassification_confidence", "reclassification_reason", "needs_manual_review"]
    classified = pd.concat([classified, results], axis=1)

    # Validate taxonomy and boolean fields.
    invalid = sorted(set(classified["topic_v3"]) - set(TAXONOMY))
    if invalid:
        raise ValueError(f"Invalid topic_v3 values: {invalid}")
    classified["needs_manual_review"] = classified["needs_manual_review"].astype(bool)

    classified.to_csv(AUDIT / "cleaned_sessions_topic_v3.csv", index=False)

    other_reclassified = classified.loc[classified["was_original_other_union"]].copy()
    other_reclassified.to_csv(AUDIT / "other_reclassified_rows.csv", index=False)

    manual = classified.loc[classified["needs_manual_review"]].copy()
    manual.to_csv(AUDIT / "manual_review_rows.csv", index=False)

    comparison = (
        classified.groupby(["topic_v2", "topic_v3"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["topic_v2", "row_count"], ascending=[True, False])
    )
    comparison.to_csv(AUDIT / "topic_v2_vs_topic_v3_comparison.csv", index=False)

    distribution = classified["topic_v3"].value_counts().rename_axis("topic_v3").reset_index(name="row_count")
    distribution["row_share"] = distribution["row_count"] / len(classified)
    distribution.to_csv(AUDIT / "topic_v3_distribution.csv", index=False)

    report = build_report(classified, other_original, other_reclassified, manual, comparison)
    (AUDIT / "reclassification_report.md").write_text(report, encoding="utf-8")

    original_other_count = len(other_original)
    new_other_count = int((classified["topic_v3"] == "Other - Insufficient Information").sum())
    reduction = (1 - new_other_count / original_other_count) * 100 if original_other_count else 0
    low_count = int((classified["reclassification_confidence"] == "low").sum())
    manual_count = int(classified["needs_manual_review"].sum())

    print("Reclassification Validation")
    print("===========================")
    print(f"original Other count: {original_other_count}")
    print(f"new Other - Insufficient Information count: {new_other_count}")
    print(f"percentage reduction in Other: {reduction:.1f}%")
    print("\ntop 20 topic_v3 categories:")
    print(distribution.head(20).to_string(index=False))
    print(f"\ncount of low-confidence reclassifications: {low_count}")
    print(f"count of manual review rows: {manual_count}")


if __name__ == "__main__":
    main()
