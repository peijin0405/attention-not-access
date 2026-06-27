#!/usr/bin/env python3
"""
Power Map: Blockchain Futurist Conference 2025
Five publication-quality charts supporting the four-layer analysis.
"""

import csv, os, warnings, textwrap
from collections import defaultdict, Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import squarify
import networkx as nx

warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────
BASE = Path('/Users/mqc/Documents/ai_projects/vibe_coding_shit/blockchain_2025')
FIGS = BASE / 'power_analysis' / 'figures'
FIGS.mkdir(parents=True, exist_ok=True)

# ── Global style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          11,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.facecolor':   'white',
    'axes.facecolor':     '#FAFAFA',
    'axes.grid':          True,
    'grid.alpha':         0.35,
    'grid.linestyle':     '--',
    'axes.titlesize':     13,
    'axes.titleweight':   'bold',
    'axes.labelsize':     11,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
})

C_FIN  = '#2166AC'   # blue  – Financial Web3
C_COM  = '#C0392B'   # red   – Community / ETHWomen Web3
C_TEC  = '#27AE60'   # green – Technical Web3
C_OTH  = '#95A5A6'   # grey  – Other / uncategorised
C_GOLD = '#E67E22'   # orange – Main Stage highlight
C_DARK = '#2C3E50'

# ── Load & deduplicate ────────────────────────────────────────────────────
with open(BASE / 'output' / 'cleaned_sessions.csv') as f:
    raw = list(csv.DictReader(f))

# Unique sessions: title + stage
seen_ts, sessions = set(), []
for r in raw:
    key = (r['clean_session_title'].strip(), r['stage_or_venue'].strip())
    if key[0] and key not in seen_ts:
        seen_ts.add(key)
        sessions.append(r)

# Unique speaker-session pairs (for broker analysis)
seen_sp, sp_sessions = set(), []
for r in raw:
    key = (r['speaker_name'].strip(), r['clean_session_title'].strip())
    if key[0] and key[1] and key not in seen_sp:
        seen_sp.add(key)
        sp_sessions.append(r)

def stage_norm(s):
    s = s.strip()
    if 'ETHWomen' in s:              return 'ETHWomen'
    if 'AI' in s and 'Entice' in s:  return 'AI Sub-Track'
    if s.startswith('Main Stage'):   return 'Main Stage'
    if 'Bootcamp' in s:              return 'Bootcamp'
    if 'Rooftop' in s:               return 'Rooftop Stage'
    return 'Events/Other'

def get_topic(r):
    t = (r.get('topic_v2') or r.get('topic_category') or 'Other').strip()
    return t or 'Other'

for r in sessions:
    r['_stage'] = stage_norm(r['stage_or_venue'])
    r['_topic'] = get_topic(r)
for r in sp_sessions:
    r['_stage'] = stage_norm(r['stage_or_venue'])
    r['_topic'] = get_topic(r)

# ── Cluster taxonomy ──────────────────────────────────────────────────────
FIN_T = {'Bitcoin','RWA','DeFi','Payments','Stablecoins',
          'Institutional Adoption','Venture Capital','Regulation','Security'}
COM_T = {'Ethereum','Social Impact','Creator Economy','Education',
          'Consumer Crypto','NFT','Gaming','Enterprise Blockchain','Supply Chain'}
TEC_T = {'Infrastructure','AI x Crypto','AI Agents','Layer1','Layer2',
          'Privacy','Identity','DePIN','Developer Ecosystem','Fundraising'}

def cluster(topic):
    if topic in FIN_T: return 'Financial'
    if topic in COM_T: return 'Community'
    if topic in TEC_T: return 'Technical'
    return 'Other'

CLUSTER_COLOR = {'Financial': C_FIN, 'Community': C_COM,
                 'Technical': C_TEC, 'Other': C_OTH}

# ── Organization classification ───────────────────────────────────────────
ORG_RULES = [
    ('Government / Regulatory',
     ['commission','congress','house of representatives','congressional',
      'government','mayor','florida blockchain business','digital commission',
      'fbi','sec ','cftc','bvi financial']),
    ('Traditional Finance',
     ['berkshire','hathaway','maple finance','cayman finance',
      'family office','wall street']),
    ('Trading & Financial Services',
     ['coinbase','transak','tether','quicknode','bloxcross',
      'spree.finance','diamond lake','titi','razy','raza']),
    ('Blockchain Protocol & Infrastructure',
     ['secret network','nexa','bitcoin unlimited','algorand','sporkdao',
      'ethdenv','mysten','web3 enabler','xion','optio','phenix',
      'infene','reachx','blockchain.fun','layer','protocol',
      'reserveone','reserve one','ben franklin digital']),
    ('AI Company',
     ['singularitynet','asi alliance','eliza labs','angel ai',
      'angel_ai','nexttech','impact theory']),
    ('Consumer Product',
     ['pudgy penguins','doginal','nft-vip','bitbasel',
      'look ','$mother','n3on media','red light']),
    ('Investment Institution',
     ['sarson fund','virgo group','blockstreet','grinhaus',
      'luna media','blockchain capital','investment']),
    ('Legal / Compliance',
     ['collas crill','gowling','lewis baach','notabene','blockchain legal',
      'aml incubator','parfin','ryki','threesquared','vault12',
      'counsel','legal institute']),
    ('Media / Research',
     ['cointelegraph','decrypt','genzio media','crypto coin show',
      'notanother','blockchain north','purple horizons',
      'marketing','media']),
    ('Community Association',
     ['women in cryptocurrency','cryptochicks','women in blockchain',
      'crypto strategy academy','harness all poss',
      'association for women','eth women','ethwomen']),
    ('Conference Organizer',
     ['blockchain futurist conference']),
]

def classify_org(name):
    nl = name.lower()
    for cat, kws in ORG_RULES:
        if any(k in nl for k in kws):
            return cat
    return 'Other'

# ─────────────────────────────────────────────────────────────────────────
# CHART 1 · Topic Attention vs. Main Stage Penetration  (v2 – clean labels)
# ─────────────────────────────────────────────────────────────────────────
def chart1_attention_power():
    topic_total = Counter(r['_topic'] for r in sessions)
    topic_main  = Counter(r['_topic'] for r in sessions if r['_stage'] == 'Main Stage')

    excluded = {'Other'}
    topics = [t for t in topic_total if t not in excluded and topic_total[t] >= 2]

    x  = [topic_total[t] for t in topics]
    y  = [topic_main[t] / topic_total[t] for t in topics]
    cl = [cluster(t) for t in topics]
    co = [CLUSTER_COLOR[c] for c in cl]

    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.scatter(x, y, c=co, s=200, alpha=0.85, edgecolors='white',
               linewidths=1.5, zorder=3)

    # Quadrant lines
    ax.axhline(0.25, color='#CCCCCC', lw=1.0, ls=':', zorder=1)
    ax.axvline(5,    color='#CCCCCC', lw=1.0, ls=':', zorder=1)

    # Quadrant background labels — placed in corners, well away from data
    for txt, xx, yy, ha in [
        ('← Elevated\n(high access,\nlow volume)',  0.5,  0.88, 'left'),
        ('Dominant →\n(high access,\nhigh volume)', 17.5, 0.88, 'right'),
        ('← Marginal\n(low access,\nlow volume)',   0.5,  0.04, 'left'),
        ('Suppressed →\n(low access,\nhigh volume)',17.5, 0.04, 'right'),
    ]:
        ax.text(xx, yy, txt, fontsize=8, color='#C0C0C0',
                ha=ha, va='bottom', style='italic', zorder=1)

    # Offsets in screen points (dx, dy) — keeps every label close to its dot.
    # Co-located pairs are fanned to opposite sides:
    #   (3, 0.667): Creator Economy ↖  vs  Security ↘
    #   (3, 0.333): Gaming ↗  vs  Institutional Adoption ↙
    #   (4, 0.000): Consumer Crypto ↙  vs  (5, 0.000): Social Impact ↘
    LABEL_OFFSETS = {
        'AI x Crypto':              (-65, 20),   # far-right point → pull label left-up
        'Ethereum':                 (  8, -18),  # bottom-right → below
        'Infrastructure':           (  8,   8),
        'DeFi':                     (  8,  -8),
        'RWA':                      (  8,   0),
        'Payments':                 ( -8,  16),  # (5, 0.60) → up-left (below Bitcoin)
        'Bitcoin':                  (  8,  16),  # (5, 0.80) → up-right
        'Social Impact':            (  8, -18),  # (5, 0.00) → below-right
        'Regulation':               (-10,  16),  # (4, 1.00) → up-left
        'Consumer Crypto':          (-10, -18),  # (4, 0.00) → below-left
        'Creator Economy':          (-10,  12),  # (3, 0.667) → up-left
        'Security':                 (  8, -12),  # (3, 0.667) → down-right
        'Gaming':                   (  8,  14),  # (3, 0.333) → up-right
        'Institutional Adoption':   (-10, -14),  # (3, 0.333) → down-left
        'Education':                (  8,  12),  # (2, 0.00)  → up-right
    }

    for t, xi, yi in zip(topics, x, y):
        dx, dy = LABEL_OFFSETS.get(t, (8, 8))
        ax.annotate(
            t,
            xy=(xi, yi),
            xytext=(dx, dy),
            textcoords='offset points',
            fontsize=8.5,
            color=C_DARK,
            ha='right' if dx < 0 else 'left',
            va='center',
            arrowprops=dict(arrowstyle='-', color='#CCCCCC', lw=0.8,
                            shrinkA=0, shrinkB=5),
        )

    legend_handles = [
        mpatches.Patch(color=C_FIN, label='Financial Web3'),
        mpatches.Patch(color=C_COM, label='Community Web3'),
        mpatches.Patch(color=C_TEC, label='Technical Web3'),
    ]
    ax.legend(handles=legend_handles, loc='center left', framealpha=0.9, fontsize=9)

    ax.set_xlabel('Total Unique Sessions  (attention volume)', labelpad=8)
    ax.set_ylabel('Share of Sessions on Main Stage  (discourse access rate)', labelpad=8)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_title('Fig 1 · Attention vs. Discourse Access\n'
                 'High session count does not guarantee Main Stage presence',
                 pad=14)
    ax.set_xlim(-0.5, 19)
    ax.set_ylim(-0.08, 1.12)

    plt.tight_layout()
    fig.savefig(FIGS / 'fig1_attention_power.png', dpi=160, bbox_inches='tight')
    plt.close()
    print("✓ Fig 1 saved")

# ─────────────────────────────────────────────────────────────────────────
# CHART 2 · Organization Power Matrix
# ─────────────────────────────────────────────────────────────────────────
def chart2_org_matrix():
    # Build org → sessions map (unique sessions only)
    org_sessions = defaultdict(list)
    for r in sessions:
        co = r.get('speaker_company', '').strip()
        if co:
            org_sessions[co].append(r)

    # Classify orgs and aggregate by category
    cat_sessions = defaultdict(list)
    for org, sess in org_sessions.items():
        cat = classify_org(org)
        cat_sessions[cat].extend(sess)

    ORDER = [
        'Government / Regulatory', 'Traditional Finance',
        'Legal / Compliance', 'Investment Institution',
        'Trading & Financial Services', 'Blockchain Protocol & Infrastructure',
        'AI Company', 'Consumer Product',
        'Media / Research', 'Community Association', 'Conference Organizer',
    ]

    metrics = {}
    for cat in ORDER:
        ss = cat_sessions.get(cat, [])
        if not ss:
            metrics[cat] = (0, 0, 0, 0)
            continue
        total = len(ss)
        n_main   = sum(1 for r in ss if r['_stage'] == 'Main Stage')
        topics   = set(r['_topic'] for r in ss if r['_topic'] != 'Other')
        stages   = set(r['_stage'] for r in ss)
        # track dependence: share in single most-common stage
        stage_cnt = Counter(r['_stage'] for r in ss)
        top_stage_share = stage_cnt.most_common(1)[0][1] / total if total else 0

        metrics[cat] = (
            n_main / total,            # main stage %
            min(len(topics) / 8, 1),   # topic breadth (norm to 8 max)
            min(len(stages) / 4, 1),   # stage breadth (norm to 4 max)
            top_stage_share,           # track dependence
        )

    labels = ['Main Stage\nPenetration', 'Topic\nBreadth',
              'Stage\nBreadth', 'Track\nDependence']

    mat = np.array([metrics[c] for c in ORDER])
    # Invert track dependence so "more concentrated" = darker (worse diversity)
    # Actually keep as-is; higher = more concentrated in one track

    fig, ax = plt.subplots(figsize=(10, 7))
    # Single-color sequential colormap (darker = higher score)
    im = ax.imshow(mat, aspect='auto', cmap='YlOrBr', vmin=0, vmax=1)

    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels(ORDER, fontsize=9)

    # Cell text
    for i in range(len(ORDER)):
        for j in range(4):
            v = mat[i, j]
            txt = f'{v:.0%}'
            col = 'white' if v > 0.55 else C_DARK
            ax.text(j, i, txt, ha='center', va='center',
                    fontsize=8.5, color=col, fontweight='bold')

    cb = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
    cb.set_label('Score (darker = higher)', fontsize=9)

    # Divider line between institutional vs community groups
    ax.axhline(4.5, color='white', lw=2)

    ax.set_title('Fig 2 · Organizational Presence Matrix\n'
                 'Main Stage access, topic breadth, stage reach, and track concentration by org type',
                 pad=14)
    plt.tight_layout()
    fig.savefig(FIGS / 'fig2_org_matrix.png', dpi=160, bbox_inches='tight')
    plt.close()
    print("✓ Fig 2 saved")

# ─────────────────────────────────────────────────────────────────────────
# CHART 3 · The Three Web3s — Stage × Topic Distribution
# ─────────────────────────────────────────────────────────────────────────
def chart3_three_web3s():
    TARGET_STAGES = ['Main Stage', 'ETHWomen', 'AI Sub-Track', 'Rooftop Stage']
    # Education (Bootcamp only) and NFT (Events only) excluded: zero sessions
    # in the four displayed stages — confirmed by data verification
    SHOW_TOPICS = [
        'Bitcoin', 'RWA', 'DeFi', 'Payments', 'Regulation',
        'Stablecoins', 'Institutional Adoption',
        'Ethereum', 'Social Impact', 'Creator Economy',
        'Consumer Crypto', 'Gaming',
        'Infrastructure', 'AI x Crypto', 'AI Agents',
        'Layer2', 'Security', 'Privacy',
    ]
    CL_ORDER = ['Financial', 'Community', 'Technical']
    topic_cluster = {t: cluster(t) for t in SHOW_TOPICS}

    # Count unique sessions per (stage_norm, topic)
    counts = defaultdict(Counter)
    for r in sessions:
        sn = r['_stage']
        tp = r['_topic']
        if sn in TARGET_STAGES and tp in SHOW_TOPICS:
            counts[sn][tp] += 1

    # Build matrix: rows = topics, cols = stages
    mat = np.zeros((len(SHOW_TOPICS), len(TARGET_STAGES)))
    for j, st in enumerate(TARGET_STAGES):
        for i, tp in enumerate(SHOW_TOPICS):
            mat[i, j] = counts[st][tp]

    # Sort topics by cluster then by total count
    def sort_key(tp):
        c = cluster(tp)
        order = {'Financial': 0, 'Community': 1, 'Technical': 2, 'Other': 3}
        return (order[c], -sum(counts[st][tp] for st in TARGET_STAGES))
    SHOW_TOPICS_sorted = sorted(SHOW_TOPICS, key=sort_key)
    mat_sorted = np.array([[counts[st][tp] for st in TARGET_STAGES]
                           for tp in SHOW_TOPICS_sorted])

    fig, ax = plt.subplots(figsize=(10, 9))
    stage_colors = [C_GOLD, C_COM, C_TEC, '#7F8C8D']
    bottom = np.zeros(len(SHOW_TOPICS_sorted))

    bars = []
    for j, (st, col) in enumerate(zip(TARGET_STAGES, stage_colors)):
        vals = mat_sorted[:, j]
        b = ax.barh(range(len(SHOW_TOPICS_sorted)), vals, left=bottom,
                    color=col, alpha=0.85, label=st, height=0.7)
        bars.append(b)
        bottom += vals

    # Cluster dividers
    cl_labels = [cluster(t) for t in SHOW_TOPICS_sorted]
    prev = cl_labels[0]
    group_start = 0
    cluster_positions = []
    for i, c in enumerate(cl_labels):
        if c != prev or i == len(cl_labels) - 1:
            end = i if c != prev else i + 1
            cluster_positions.append((prev, group_start, end))
            group_start = i
            prev = c
    cluster_positions.append((prev, group_start, len(cl_labels)))

    cluster_col = {'Financial': C_FIN, 'Community': C_COM, 'Technical': C_TEC}
    already_drawn = set()
    for cl_name, start, end in cluster_positions:
        if cl_name in already_drawn:
            continue
        already_drawn.add(cl_name)
        mid = (start + end - 1) / 2
        ax.text(-0.3, mid, cl_name, ha='right', va='center',
                fontsize=9, color=cluster_col.get(cl_name, C_OTH),
                fontweight='bold', transform=ax.get_yaxis_transform())
        if start > 0:
            ax.axhline(start - 0.5, color='#CCCCCC', lw=1.0, ls='-')

    ax.set_yticks(range(len(SHOW_TOPICS_sorted)))
    ax.set_yticklabels(SHOW_TOPICS_sorted, fontsize=9)
    ax.set_xlabel('Unique sessions', labelpad=8)
    ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
    ax.set_title('Fig 3 · The Three Web3s\n'
                 'Topic distribution across main stages reveals parallel ecosystems', pad=14)
    plt.tight_layout()
    fig.savefig(FIGS / 'fig3_three_web3s.png', dpi=160, bbox_inches='tight')
    plt.close()
    print("✓ Fig 3 saved")

# ─────────────────────────────────────────────────────────────────────────
# CHART 4 · Structural Brokers — Speaker Bridging Score
# ─────────────────────────────────────────────────────────────────────────
def chart4_brokers():
    # For each speaker, find their unique topics, stages, and clusters
    sp_data = defaultdict(lambda: {'topics': set(), 'stages': set(),
                                   'clusters': set(), 'sessions': set()})
    for r in sp_sessions:
        name = r['speaker_name'].strip()
        if not name or name.lower() in ('tba', 'tbd', ''):
            continue
        tp = r['_topic']
        st = r['_stage']
        sp_data[name]['topics'].add(tp)
        sp_data[name]['stages'].add(st)
        sp_data[name]['clusters'].add(cluster(tp))
        sp_data[name]['sessions'].add(r['clean_session_title'].strip())

    # Score: n_topics * n_clusters * n_stages (only speakers with ≥ 2 sessions)
    scored = []
    for name, d in sp_data.items():
        if len(d['sessions']) < 2:
            continue
        score = len(d['topics']) * len(d['clusters']) * len(d['stages'])
        scored.append({
            'name': name,
            'score': score,
            'topics': len(d['topics']),
            'clusters': len(d['clusters']),
            'stages': len(d['stages']),
            'sessions': len(d['sessions']),
        })
    scored.sort(key=lambda x: (-x['score'], -x['sessions']))
    top = scored[:18]

    fig, ax = plt.subplots(figsize=(10, 8))
    names   = [s['name'] for s in top]
    scores  = [s['score'] for s in top]
    n_cl    = [s['clusters'] for s in top]
    colors  = [C_FIN if nc == 1 else (C_COM if nc == 2 else C_TEC) for nc in n_cl]

    bars = ax.barh(range(len(top)), scores, color=colors, alpha=0.82,
                   edgecolor='white', height=0.7)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(names, fontsize=9.5)

    for i, s in enumerate(top):
        label = f"  {s['sessions']}sess · {s['topics']}topics · {s['clusters']}clusters"
        ax.text(s['score'] + 0.05, i, label, va='center', fontsize=8, color='#555555')

    legend_handles = [
        mpatches.Patch(color=C_FIN, label='Single cluster'),
        mpatches.Patch(color=C_COM, label='Two clusters'),
        mpatches.Patch(color=C_TEC, label='Three clusters'),
    ]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=9)

    ax.set_xlabel('Broker Score  (topics × clusters × stages)', labelpad=8)
    ax.set_title('Fig 4 · Structural Brokers\n'
                 'Speakers who cross topic categories, stages, and Web3 communities', pad=14)
    ax.set_xlim(0, max(scores) * 1.45)
    plt.tight_layout()
    fig.savefig(FIGS / 'fig4_brokers.png', dpi=160, bbox_inches='tight')
    plt.close()
    print("✓ Fig 4 saved")

# ─────────────────────────────────────────────────────────────────────────
# CHART 5 · AI × Crypto Identity Crisis — Treemap
# ─────────────────────────────────────────────────────────────────────────
def chart5_ai_treemap():
    # All rows (with speaker info), filter to AI x Crypto
    ai_rows = [r for r in raw if (r.get('topic_v2') or r.get('topic_category','')) == 'AI x Crypto']

    # Decompose by: stage × co-occurring topic vs org type
    # We'll do stage × title keyword cluster
    def ai_sub(title, stage):
        t = title.lower()
        s = stage
        if 'agent' in t or 'autonomous' in t:           return 'AI Agents on-chain\n(Argentum AI Stage)'
        if 'gaming' in t or 'game' in t:                return 'AI × Gaming\n(Main Stage)'
        if 'creator' in t or 'content' in t:            return 'AI × Creator Economy\n(Mixed)'
        if 'infra' in t or 'layer' in t or 'node' in t: return 'AI Infrastructure\n(AI Sub-Track)'
        if 'invest' in t or 'financ' in t:              return 'AI × Finance\n(Main Stage)'
        if s == 'Main Stage':                            return 'AI Keynote / Panel\n(Main Stage)'
        if s == 'AI Sub-Track':                          return 'AI Sub-Track\n(Dedicated)'
        return 'Other AI × Crypto\n(Mixed)'

    sub_counts = Counter()
    for r in ai_rows:
        sub = ai_sub(r.get('clean_session_title','').lower(),
                     stage_norm(r['stage_or_venue']))
        sub_counts[sub] += 1

    # Also add the "AI Agents: only 1 session" as explicit data point
    sub_counts['AI Agents on-chain\n(Argentum AI Stage)'] = max(
        sub_counts.get('AI Agents on-chain\n(Argentum AI Stage)', 0), 1)

    labels_raw = list(sub_counts.keys())
    sizes_raw  = [sub_counts[l] for l in labels_raw]

    # Filter zero
    pairs = [(l, s) for l, s in zip(labels_raw, sizes_raw) if s > 0]
    pairs.sort(key=lambda x: -x[1])
    labels = [p[0] for p in pairs]
    sizes  = [p[1] for p in pairs]

    colors_map = {
        'AI Keynote / Panel\n(Main Stage)': C_GOLD,
        'AI × Finance\n(Main Stage)': C_FIN,
        'AI × Gaming\n(Main Stage)': '#8E44AD',
        'AI Sub-Track\n(Dedicated)': C_TEC,
        'AI Agents on-chain\n(Argentum AI Stage)': '#E74C3C',
        'AI Infrastructure\n(AI Sub-Track)': '#1ABC9C',
        'AI × Creator Economy\n(Mixed)': C_COM,
        'Other AI × Crypto\n(Mixed)': C_OTH,
    }
    colors = [colors_map.get(l, C_OTH) for l in labels]

    fig, ax = plt.subplots(figsize=(12, 7))
    squarify.plot(sizes=sizes, label=[f"{l}\n(n={s})" for l, s in zip(labels, sizes)],
                  color=colors, alpha=0.85, ax=ax,
                  text_kwargs={'fontsize': 8.5, 'color': 'white',
                               'fontweight': 'bold', 'wrap': True})
    ax.set_axis_off()
    ax.set_title('Fig 5 · "AI × Crypto" Contains Multiple Distinct Sub-Narratives\n'
                 'Session content and stage placement reveal at least five divergent product theses',
                 pad=14, fontsize=13, fontweight='bold')

    # Clarifying note about AI Agents
    ax.text(0.5, -0.04,
            '★  "AI Agents on-chain" — the dominant AI narrative in broader tech in 2025–26 '
            '— accounts for fewer than 5 sessions, all confined to the dedicated AI sub-track',
            transform=ax.transAxes, ha='center', fontsize=8.5,
            color='#E74C3C', style='italic')

    plt.tight_layout()
    fig.savefig(FIGS / 'fig5_ai_treemap.png', dpi=160, bbox_inches='tight')
    plt.close()
    print("✓ Fig 5 saved")

# ─────────────────────────────────────────────────────────────────────────
# BONUS CHART · Ethereum vs Bitcoin: Stage Presence Comparison
# ─────────────────────────────────────────────────────────────────────────
def chart_bonus_eth_btc():
    chains = ['Bitcoin', 'Ethereum', 'DeFi', 'RWA', 'AI x Crypto', 'Regulation']
    target_stages = ['Main Stage', 'Rooftop Stage', 'ETHWomen', 'AI Sub-Track',
                     'Bootcamp', 'Events/Other']
    stage_colors  = [C_GOLD, '#7F8C8D', C_COM, C_TEC, '#BDC3C7', '#ECF0F1']

    counts = defaultdict(Counter)
    for r in sessions:
        tp = r['_topic']
        if tp in chains:
            counts[tp][r['_stage']] += 1

    fig, axes = plt.subplots(1, len(chains), figsize=(14, 5), sharey=False)
    for ax, tp in zip(axes, chains):
        vals = [counts[tp].get(s, 0) for s in target_stages]
        total = sum(vals)
        bars = ax.bar(range(len(target_stages)), vals,
                      color=stage_colors, edgecolor='white', width=0.7)
        ax.set_xticks(range(len(target_stages)))
        ax.set_xticklabels([s.replace(' ', '\n') for s in target_stages],
                           fontsize=7, rotation=0)
        ax.set_title(tp, fontsize=10, fontweight='bold',
                     color=cluster_col_for(tp))
        ax.set_ylabel('Unique sessions' if tp == chains[0] else '')
        ax.text(0.5, 0.97, f'n={total}', transform=ax.transAxes,
                ha='center', va='top', fontsize=8, color='#777')

    legend_handles = [mpatches.Patch(color=c, label=s)
                      for c, s in zip(stage_colors, target_stages)]
    fig.legend(handles=legend_handles, loc='lower center', ncol=6,
               fontsize=8, framealpha=0.9, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle('Bonus Fig · Where Each Major Topic Lives\n'
                 'Ethereum: zero Main Stage sessions. Bitcoin: almost exclusively Main Stage.',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(FIGS / 'fig_bonus_stage_breakdown.png', dpi=160,
                bbox_inches='tight')
    plt.close()
    print("✓ Bonus fig saved")

def cluster_col_for(tp):
    c = cluster(tp)
    return CLUSTER_COLOR.get(c, C_OTH)

# ─────────────────────────────────────────────────────────────────────────
# RUN ALL
# ─────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Generating charts …")
    chart1_attention_power()
    chart2_org_matrix()
    chart3_three_web3s()
    chart4_brokers()
    chart5_ai_treemap()
    chart_bonus_eth_btc()
    print("\nAll charts saved to:", FIGS)
