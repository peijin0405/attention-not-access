# Attention Is Not Access
## A Four-Layer Structural Analysis of the 2025 Blockchain Futurist Conference Agenda

*2025 Blockchain Futurist Conference · Agenda Data Analysis*

---

**Abstract**

This paper analyzes the complete agenda dataset of the 2025 Blockchain Futurist Conference using a four-layer framework — Topic, Stage, Speaker, and Organization — to examine the structural relationship between attention allocation (session frequency) and discursive access (Main Stage representation). Core findings include: a systematic decoupling between topic prominence and Main Stage access rates; an inverse relationship between an organization type's topic breadth and its access to the central stage; three largely isolated Web3 topic communities coexisting within the same conference space with minimal cross-pollination; and significant internal fragmentation within the "AI × Crypto" label, with the Main Stage and dedicated sub-track serving distinct audiences operating under different product assumptions. The findings demonstrate that Main Stage access is shaped by topic framing, institutional identity, and sponsorship capital — not by topic frequency alone.

---

> A Web3 conference agenda is not merely a ranked list of trending topics. It is a map of structural access to narrative space. In this map, attention (session count) and discursive access (Main Stage share) systematically decouple: the most frequently appearing topics don't necessarily reach the main stage; the organizations with the broadest community reach don't necessarily occupy the center of the discourse; and the ability to bridge topic boundaries, stage tiers, and community divides is concentrated in a remarkably small number of speakers.

---

## I. The Agenda as a Readable Text

A conference agenda is not simply the logistical output of scheduling decisions. It is a statement of content priorities — which topics deserve the most visibility, which voices should occupy the most prominent positions, which organizations are granted the opportunity to define the narrative. These choices compose a structure that can be measured.

When an agenda determines which topics appear on the main stage, which organizations are given speaking slots, and which speakers can appear across three different tracks in a single day, it is doing something more fundamental: it is distributing the opportunity to be heard at the center of the conversation.

Attention (the number of sessions per topic) is easily quantified. Discursive access is harder to see — it hides in stage hierarchies, in organizational credentials, and in speakers' ability to cross community boundaries.

This paper analyzes the complete agenda of the 2025 Blockchain Futurist Conference, covering **140 unique sessions, 215 speakers, and 199 participating organizations** after deduplication. Building on cleaned data cross-verified against original app screenshots, the analysis proceeds through four layers:

| Layer | Analytical Dimension |
|-------|----------------------|
| **Topic** | What is the content, and which category does it belong to? |
| **Stage** | At which tier of the stage hierarchy is attention allocated? |
| **Speaker** | Who receives a platform, and which boundaries do they cross? |
| **Organization** | Who stands behind each voice, and what interests do they represent? |

---

## II. The Systematic Decoupling of Attention and Access

The first question: which topics appear most frequently across the full program, and which topics actually reach the main stage?

Mapping each topic's total session count (attention volume) against its share of Main Stage appearances (discourse access rate) produces a tension map with two structurally distinct regions (Figure 1).

![Attention vs. Discourse Access](figures/fig1_attention_power.png)

*Figure 1 · Attention volume vs. Main Stage access rate. X-axis: total unique sessions per topic (attention). Y-axis: share of sessions on the Main Stage (discourse access rate). Colors distinguish Financial, Community, and Technical topic clusters. The upper-right quadrant represents high-frequency, high-access "dominant" topics; the lower-right quadrant represents high-frequency, low-access "suppressed" topics.*

The chart reveals two structurally divergent zones:

**The high-access zone (upper right): the priority lane for institutional narratives.** RWA (real-world asset tokenization), Regulation, and Bitcoin post the highest Main Stage access rates — even if their overall session counts are not always the largest. What they share: audiences clearly oriented toward institutional investors, traditional financial institutions, or policymakers.

**The suppressed zone (lower right): topics routed away from the main stage.** Ethereum is the conference's second-largest topic (12 unique sessions), yet its **Main Stage access rate is zero**. AI × Crypto is the most heavily branded dedicated track in the program, yet fewer than 25% of its sessions appear on the Main Stage — the bulk are routed into a dedicated AI sub-track.

**An apparently anomalous data point**: DeFi actually posts four Main Stage sessions, on par with RWA and Bitcoin. But the session titles reveal what that access requires:

> *"TradFi Meets DeFi: Building Bridges in Blockchain"*
> *"Onchain Financial Services: Blending DeFi with Traditional Banking"*
> *"DeFi & Staking: How DeFi is Changing the Financial Landscape"*
> *"DeFi's Social Layer: Storytelling, Sentiment & Collective Power"*

Not one session is a pure protocol-layer DeFi discussion. DeFi's entry ticket to the main stage is repackaging itself within a traditional finance bridging narrative. **The framing of a topic determines whether it can be received by the audience structure the main stage is designed to serve.**

---

## III. Organizational Type and Main Stage Access: A Structural Matrix

The second question concerns the organizational forces behind the narratives. Classifying 199 participating organizations into 11 types and computing four metrics for each reveals the structural participation pattern (Figure 2):

- **Main Stage penetration**: share of an organization type's sessions on the Main Stage
- **Topic breadth**: number of distinct topic categories covered (normalized to a maximum of 8), reflecting the range of the narrative spectrum
- **Stage breadth**: number of distinct stage types appeared in
- **Track concentration**: degree to which sessions cluster in a single sub-track

![Organizational Presence Matrix](figures/fig2_org_matrix.png)

*Figure 2 · Organizational presence matrix (11 org types × 4 metrics). Color intensity represents normalized score — darker cells indicate higher scores. Topic breadth = number of topic categories covered ÷ 8; a full score indicates coverage across 8 or more distinct topic categories.*

The matrix reveals a consistent structural contrast:

**The organization types with the highest Main Stage access rates** are not those with the richest content or the broadest thematic reach. They are:

- **Legal / Compliance firms**: Main Stage penetration of roughly 50%, but topic breadth of only 25%. These organizations concentrate their activity within the regulatory narrative domain and, within that domain, maintain stable access to the central stage.
- **Traditional financial institutions**: similarly centered on Main Stage appearances, with near-zero topic breadth.

**The organization type with the widest topic coverage and lowest Main Stage access**:

- **Community associations** (primarily women's crypto communities and ETHWomen-affiliated organizations): topic breadth of 62%, spanning Social Impact, Education, Creator Economy, Ethereum, and more — but a Main Stage penetration rate of **0%**. This is the matrix's most striking structural inversion: the category covering the widest narrative spectrum has no presence at the center of the discourse.
- **Blockchain protocol and infrastructure companies**: track concentration approaching 100% (sessions heavily clustered in dedicated technical sub-tracks), with a Main Stage penetration of only around 33%.

**The structural pattern**: in this conference, thematic breadth and access to the discursive center do not positively correlate. Organization types maintaining high focus on institutionally legible topics show a much stronger positive relationship with Main Stage access.

---

## IV. Three Parallel Communities Under One Roof

Mapping all sessions across stage type and topic reveals something more fundamental: this is not a conference presenting a single, unified industry narrative. It is three largely self-contained topic communities — each internally coherent, with minimal cross-topic overlap — sharing the same conference space (Figure 3).

![The Three Web3s](figures/fig3_three_web3s.png)

*Figure 3 · Topic-stage distribution across the three topic communities. Orange = Main Stage, red = ETHWomen track, green = AI sub-track, grey = Rooftop Stage. The color composition of each bar shows the cross-stage distribution pattern for that topic.*

**Financial Web3** (centered on the Main Stage): RWA, DeFi (TradFi-framed), Bitcoin, Regulation, and Payments form the thematic backbone. Participating organizations are primarily investment institutions, legal and compliance firms, and traditional financial institutions. Core narrative logic: *Web3 is the next generation of financial infrastructure.*

**Community Web3** (centered on the ETHWomen dedicated track, 19 unique sessions): all 12 Ethereum sessions are in this track, as are more than 75% of Social Impact sessions. The organizational core includes the Association for Women in Cryptocurrency, CryptoChicks & Metis, and Women in Blockchain Canada. Core narrative logic: *Web3 is a tool for equalizing access to social participation.*

**Technical Web3** (AI sub-track + Rooftop Stage, approximately 35 sessions): the main body of AI × Crypto content sits in the AI-dedicated track; Infrastructure, Privacy, and Layer2 topics appear on the Rooftop Stage. Participating organizations are primarily blockchain protocol companies and AI startups. Core narrative logic: *Web3 is the technology stack for decentralized computation.*

**The degree of topic isolation across the three communities is unmistakable in co-occurrence data**:

Ethereum co-occurs with Social Impact 12 times, with DeFi 0 times, with RWA 0 times, with Regulation 0 times. Bitcoin co-occurs with Social Impact 0 times.

This is not data noise. It is the near-complete structural separation of three topic communities. **Within the same physical conference space, they each operate an independent topic framework and a distinct discursive community.**

---

## V. The Few Speakers Who Bridge the Divide

Given the sharp topic boundaries separating these three communities, the data simultaneously reveals a small number of speakers who perform a bridging function across them.

Scoring each speaker on the number of topic categories, community clusters, and stage types crossed — with a composite bridging score of (topics × clusters × stages) — produces the ranking in Figure 4.

![Structural Brokers](figures/fig4_brokers.png)

*Figure 4 · Structural bridging score ranking (speakers with 2+ sessions only). Color indicates the number of topic communities crossed: blue = 1 community, red = 2 communities, green = 3 communities.*

**Amanda Wick** (Association for Women in Cryptocurrency) tops the ranking: 5 sessions, spanning 4 distinct topic categories, touching at least two of the three community clusters, and appearing on both the Main Stage and the ETHWomen sub-track.

The runners-up — **Julie Lamb** (NFT-VIP.io) and **Elena Sinelnikova** (CryptoChicks & Metis) — represent a different bridging type. Sinelnikova's organization carries both a technical identity (Metis is an L2 infrastructure project) and a community identity (CryptoChicks), making her one of the rare two-way interfaces between the Technical and Community Web3 clusters.

A structural pattern also emerges among the top-ranked speakers: **journalists (Sam Bourgi / Cointelegraph, André Beganski / Decrypt) are natural cross-community conduits.** Media practitioners belong to no single narrative camp and can move freely across tracks as a result.

By contrast, the vast majority of speakers in the sample appear exclusively within their home community, with little to no topic overlap with other clusters. **The scarcity of speakers capable of simultaneously crossing topic domains, discursive communities, and stage tiers reflects the relative absence of structural integration mechanisms between the distinct sub-ecosystems of the current Web3 landscape.**

---

## VI. "AI × Crypto": A Highly Fragmented Agenda Label

The final question targets the conference's most prominently branded dedicated track.

"AI × Crypto" registers as many as 37 appearances in aggregate session counts, positioned as a unified topic. But disaggregating those sessions by content direction and stage placement reveals internal complexity far exceeding what the label suggests (Figure 5).

![AI × Crypto Treemap](figures/fig5_ai_treemap.png)

*Figure 5 · Distinct sub-narratives within the "AI × Crypto" label (differentiated by stage and content direction). Block area reflects session count. Note: the annotation at the bottom of the chart highlights that "AI Agents on-chain" — one of the most discussed AI directions in the broader tech industry in 2025–26 — accounts for very few sessions, all confined to the dedicated AI sub-track, indicating a significant lag relative to broader industry attention.*

At least five independent sub-narratives coexist beneath this single label:

| Sub-narrative | Stage | Sessions | Characteristics |
|---------------|-------|----------|-----------------|
| AI Keynote / Panel | Main Stage | 7 | Macro-level AI vision for a mainstream audience; representative session: Ben Goertzel (SingularityNet) AGI keynote, with limited specific intersection with crypto technology |
| AI × Finance | Main Stage | 5 | AI-driven on-chain analytics, trading decisions, and asset management |
| AI Infrastructure | AI Sub-Track | 5 | Decentralized AI compute, data markets, model verification |
| AI Agents on-chain | AI Sub-Track | 5 | Autonomous AI agents executing on-chain transactions |
| AI × Gaming | Main Stage | 2 | AI-generated content combined with on-chain game assets |

**The critical gap**: AI Agents is the most discussed technical direction in the broader AI industry in 2025–26, yet in this conference, the topic accounts for very few sessions — all confined to the dedicated AI sub-track, never reaching the Main Stage.

**What "AI × Crypto" looks like on the main stage is the AI that institutional audiences can understand: high-level vision statements and AI applied to traditional finance. AI-native applications that presuppose crypto infrastructure — on-chain agents, decentralized models — are contained within the dedicated sub-track.** A single label aggregates multiple sub-narratives aimed at different audiences, built on different technical assumptions, and corresponding to different product logics and ecosystem positions.

---

## VII. Note: Three Pathways to the Main Stage

Cross-verification of raw agenda screenshots revealed a structural dimension not fully captured in the digitized agenda records: **sponsored placements**.

Combining all available evidence, three distinct pathways to a Main Stage session can be identified:

**Pathway A · Topic relevance**: a topic is recognized as central to the current industry narrative and receives a Main Stage slot organically. RWA, Regulation, and Bitcoin are typical examples.

**Pathway B · Institutional identity**: the speaker or organization's institutional profile confers Main Stage eligibility. The presence of legal and compliance firms and traditional financial institutions strongly correlates with this pathway.

**Pathway C · Sponsorship purchase**: multiple Main Stage sessions visible in original app screenshots carry explicit "Presented by" or "Brought to you by" markers, including:

- *WHY $PENGU. Presented by Pudgy Penguins*
- *Cayman's Virtual Asset Ecosystem: Brought to you by Cayman Finance*
- *Pack Your Bags for the Supercycle. Presented by Sarson Funds*

These sponsored sessions are classified in the agenda taxonomy as "Regulation" (Cayman Finance) or "Other" (Pudgy Penguins), artificially inflating the Main Stage penetration rates of the corresponding topic categories. Cayman Finance, categorized as regulatory content, functions in practice as brand promotion for an offshore financial center.

The raw screenshots also surface one Main Stage session — classified as "Other" — that warrants separate attention:

> *Fireside Chat with Eric Trump and Asher Genoot: The Plan To Make America a Crypto Nation*

This session is the conference's most direct mainstream political legitimacy signal — the participation of a political figure lending visibility to the industry's policy normalization narrative.

**The coexistence of three pathways makes "who gets the main stage" a far more layered question than a topic frequency ranking can answer. Topic relevance, institutional identity, and sponsorship capital together constitute the structural gates to the Main Stage's narrative space.**

---

## VIII. Conclusions

Taken together, the five analytical dimensions reveal a structure that a simple topic frequency ranking cannot surface:

**Finding 1: Attention volume and Main Stage narrative access systematically decouple.** Ethereum, with zero Main Stage sessions, is the clearest case of high frequency paired with zero access. DeFi can reach the main stage, but only by adopting a TradFi bridging narrative framework.

**Finding 2: Organizational topic breadth and Main Stage access rate exhibit an inverse relationship.** Legal and compliance firms and traditional financial institutions trade narrow topic coverage for high Main Stage access; community associations trade the widest topic coverage for complete exclusion from the dedicated sub-track. Content breadth and centrality in the discourse do not positively correlate.

**Finding 3: Three largely independent topic communities coexist within the same conference space.** Financial Web3 (Main Stage), Community Web3 (ETHWomen track), and Technical Web3 (AI sub-track + Rooftop Stage) produce virtually no structural topic, speaker, or organizational overlap.

**Finding 4: Speakers capable of bridging across communities are exceedingly rare.** Those with cross-community bridging capacity tend to come from media or from organizations holding simultaneous technical and community identities. The scarcity of this capability reflects the relative absence of integrative interaction mechanisms across the distinct sub-ecosystems of the Web3 landscape.

**Finding 5: "AI × Crypto" presents a highly fragmented internal structure at the agenda level.** AI content on the Main Stage is predominantly the macro-narrative legible to institutional audiences; AI-native applications built on crypto infrastructure (on-chain agents, decentralized models) are confined to the dedicated sub-track, lagging the broader AI industry's technical conversation by a meaningful margin.

---

A conference agenda is an industry's attention snapshot at a given moment — and the negotiated outcome of competing pressures to define narrative priority. Whether the internal coherence of each of the three Web3 communities, alongside their near-complete structural separation from one another, signals deep specialization across distinct directions — or an early-stage deficit in the industry's capacity for integrative storytelling — may require agenda data from multiple conference cycles to answer fully.

---

## Data Notes

**Data source**: Official 2025 Blockchain Futurist Conference agenda app screenshots (33 raw screenshots)

**Data processing**: OCR extraction from raw screenshots, structured into session records; deduplicated using (session title + stage) as the composite key to eliminate duplicate rows caused by multi-speaker sessions; final dataset contains 140 unique sessions.

**Verification**: Key findings (Ethereum's Main Stage absence, DeFi's narrative framing requirement, identification of sponsored sessions) were directly verified through cross-comparison of original screenshots against structured data.

**Classification note**: Education-category sessions are entirely within the Bootcamp sub-track; NFT-category sessions are entirely within Events venues — neither falls within the four main stages (Main Stage, ETHWomen, AI Sub-Track, Rooftop Stage) covered by this analysis. Both categories are excluded from Figure 3.

| Metric | Value |
|--------|-------|
| Raw data rows (including multi-speaker duplicates) | 312 |
| Unique sessions after deduplication | 140 |
| Main Stage unique sessions | 51 |
| ETHWomen track unique sessions | 19 |
| AI sub-track unique sessions | 15 |
| Rooftop Stage unique sessions | 20 |
| Total speakers | 215 |
| Total organizations | 199 |
| Ethereum Main Stage sessions | 0 (of 12 total, 0%) |
| Bitcoin Main Stage sessions | 4 (of 4 total, 100%) |
| AI × Crypto Main Stage sessions | 4 (of 16 total, 25%) |
| Highest structural bridging score | Amanda Wick (5 sessions × 4 topic categories × 3 communities) |

**Charts**: All figures generated in Python (matplotlib 3.11, squarify) from the dataset described above. All normalization is computed within organization categories.
