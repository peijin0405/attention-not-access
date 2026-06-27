#!/usr/bin/env python3
import csv, re
from pathlib import Path
from collections import Counter
from wordcloud import WordCloud, STOPWORDS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE = Path('/Users/mqc/Documents/ai_projects/vibe_coding_shit/blockchain_2025')
FIGS = BASE / 'power_analysis' / 'figures'

# ── Load session titles (deduplicated) ────────────────────────────────────
with open(BASE / 'output' / 'cleaned_sessions.csv') as f:
    raw = list(csv.DictReader(f))

seen, titles, topics = set(), [], []
for r in raw:
    t = r['clean_session_title'].strip()
    if t and t not in seen:
        seen.add(t)
        titles.append(t)
    topics.append((r.get('topic_v2') or r.get('topic_category', '')).strip())

# ── Build weighted frequency dict ─────────────────────────────────────────
EXTRA_STOP = {
    'registration', 'open', 'welcoming', 'remarks', 'doors', 'virtual',
    'welcome', 'opening', 'closing', 'session', 'panel', 'keynote',
    'fireside', 'chat', 'talk', 'workshop', 'lunch', 'break', 'networking',
    'presented', 'brought', 'featuring', 'discussion', 'will', 'can',
    'new', 'need', 'using', 'use', 'used', 'get', 'make', 'good',
    'like', 'one', 'two', 'also', 'way', 'ways', 'vs', 'meet',
    'building', 'build', 'built',
}
stopwords = STOPWORDS | EXTRA_STOP

word_freq: Counter = Counter()

# Session title words
for title in titles:
    words = re.findall(r"[A-Za-z][A-Za-z0-9&+'\-]*", title)
    for w in words:
        w_clean = w.strip("'-")
        if len(w_clean) >= 3 and w_clean.lower() not in stopwords:
            word_freq[w_clean] += 1

# Boost topic-level terms (they appear as labeled categories — give extra weight)
TOPIC_BOOSTS = {
    'Bitcoin': 12, 'Ethereum': 10, 'DeFi': 10, 'RWA': 9,
    'AI': 14, 'Crypto': 8, 'Blockchain': 6, 'Web3': 6,
    'Stablecoins': 5, 'Regulation': 7, 'Payments': 5,
    'NFT': 4, 'Privacy': 5, 'Infrastructure': 6, 'Layer2': 4,
    'Gaming': 4, 'Identity': 4, 'DePIN': 4, 'ZK': 4,
    'DAO': 4, 'DEX': 3, 'MEV': 3, 'EVM': 3,
    'TradFi': 6, 'Tokenization': 7, 'Agents': 5,
    'Decentralized': 5, 'Onchain': 5, 'Protocol': 4,
}
for word, boost in TOPIC_BOOSTS.items():
    word_freq[word] += boost

# ── Color function: map words to Financial / Community / Technical palette ─
FIN_WORDS  = {'Bitcoin','RWA','DeFi','Payments','Stablecoins','Regulation',
              'TradFi','Finance','Financial','Tokenization','Institutional',
              'Trading','Investment','Asset','Treasury','Bank','ETF',
              'Compliance','Legal','Capital','Fund','Macro','Onchain'}
COM_WORDS  = {'Ethereum','ETH','Social','Impact','Women','Community',
              'Creator','Education','NFT','Gaming','Culture','DAO',
              'Inclusion','Equity','Consumer','Decentralized'}
TEC_WORDS  = {'AI','Agents','Infrastructure','Layer','Layer2','Privacy',
              'ZK','Identity','Protocol','DePIN','EVM','MEV','DEX',
              'Node','Network','Compute','Data','Model','Proof','Chain',
              'Oracle','Bridge','Interoperability','Security','Cryptography'}

def color_func(word, font_size, position, orientation, random_state=None, **kw):
    w = word.strip("'-")
    if w in FIN_WORDS:
        # Blue family
        shades = ['#2166AC', '#4292C6', '#6BAED6', '#2196F3', '#1565C0']
    elif w in COM_WORDS:
        # Red/pink family
        shades = ['#C0392B', '#E74C3C', '#E53935', '#AD1457', '#D81B60']
    elif w in TEC_WORDS:
        # Green family
        shades = ['#27AE60', '#2ECC71', '#388E3C', '#00897B', '#1B5E20']
    else:
        # Neutral grey-white
        shades = ['#B0BEC5', '#CFD8DC', '#ECEFF1', '#90A4AE', '#78909C']
    return shades[hash(word) % len(shades)]

# ── Generate word cloud ────────────────────────────────────────────────────
wc = WordCloud(
    width=1400,
    height=700,
    background_color='#0D1117',   # GitHub dark background
    color_func=color_func,
    max_words=120,
    prefer_horizontal=0.75,
    min_font_size=11,
    max_font_size=140,
    collocations=False,
    random_state=42,
).generate_from_frequencies(word_freq)

fig, ax = plt.subplots(figsize=(14, 7), facecolor='#0D1117')
ax.imshow(wc, interpolation='bilinear')
ax.set_axis_off()

# Subtle legend strips at the bottom
legend_x = [0.18, 0.50, 0.82]
legend_labels = ['Financial Web3', 'Community Web3', 'Technical Web3']
legend_colors = ['#4292C6', '#E74C3C', '#27AE60']
for lx, lbl, lc in zip(legend_x, legend_labels, legend_colors):
    ax.text(lx, -0.03, f'■  {lbl}', transform=ax.transAxes,
            ha='center', va='top', fontsize=9, color=lc,
            fontfamily='DejaVu Sans')

plt.tight_layout(pad=0)
out = FIGS / 'wordcloud.png'
fig.savefig(out, dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print(f"✓ Word cloud saved → {out}")
