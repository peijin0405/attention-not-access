# Attention Is Not Access
### A Structural Analysis of the 2025 Blockchain Futurist Conference Agenda

---

## About This Project

This project analyzes the complete agenda of the 2025 Blockchain Futurist Conference (Miami, November 2025) using a four-layer framework — Topic, Stage, Speaker, and Organization — to examine the structural relationship between attention allocation (session frequency) and discursive access (Main Stage representation).

**Core findings**: Topic prominence and Main Stage access systematically decouple — Ethereum is the conference's second-largest topic yet holds zero Main Stage sessions; community organizations cover the widest thematic range yet have zero Main Stage presence; and three largely independent Web3 sub-communities coexist within the same conference space with near-zero topic overlap.

## File Structure

```
.
├── power_analysis/
│   ├── article_final_en.md    # Full analysis article (English)
│   ├── article_final.md       # Full analysis article (Chinese)
│   ├── generate_charts.py     # Chart generation script (Python / matplotlib)
│   └── figures/               # 6 analysis charts
│       ├── fig1_attention_power.png
│       ├── fig2_org_matrix.png
│       ├── fig3_three_web3s.png
│       ├── fig4_brokers.png
│       ├── fig5_ai_treemap.png
│       └── fig_bonus_stage_breakdown.png
├── output/
│   └── cleaned_sessions.csv   # Cleaned session data (140 unique sessions)
└── pic/                       # Raw agenda screenshots (33 images, source verification)
    └── IMG_3323–IMG_3357.PNG
```

## Dataset at a Glance

| Metric | Value |
|--------|-------|
| Data source | Official conference app screenshots (manual OCR) |
| Raw rows (incl. multi-speaker duplicates) | 312 |
| Unique sessions after deduplication | 140 |
| Total speakers | 215 |
| Total organizations | 199 |

## Reproduce the Charts

```bash
pip install matplotlib squarify networkx pandas
python power_analysis/generate_charts.py
```

Charts will be written to `power_analysis/figures/`.

## License

Source data is drawn from a public conference agenda. Analysis content is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

---

# 注意力不等于话语权
### 2025 Blockchain Futurist Conference 议程的叙事准入结构分析

---

## 关于这个项目

本项目基于 2025 年 Blockchain Futurist Conference（迈阿密，2025 年 11 月）的完整议程数据，通过「议题—舞台—演讲者—组织」四层分析框架，考察注意力分配（session 出现频率）与叙事准入机会（主舞台占比）之间的结构性关系。

**核心发现**：话题热度与主舞台准入率之间存在系统性解耦——Ethereum 作为全场第二大话题，主舞台出席场次为零；社区类组织议题覆盖最广但主舞台占比为零；会议空间内部存在三类相互独立的 Web3 议题社群。

## 文件结构

```
.
├── power_analysis/
│   ├── article_final_en.md    # 完整分析文章（英文）
│   ├── article_final.md       # 完整分析文章（中文）
│   ├── generate_charts.py     # 图表生成脚本（Python / matplotlib）
│   └── figures/               # 6 张分析图表
│       ├── fig1_attention_power.png
│       ├── fig2_org_matrix.png
│       ├── fig3_three_web3s.png
│       ├── fig4_brokers.png
│       ├── fig5_ai_treemap.png
│       └── fig_bonus_stage_breakdown.png
├── output/
│   └── cleaned_sessions.csv   # 清洗后的会议数据（140 个唯一 session）
└── pic/                       # 原始议程截图（33 张，数据溯源）
    └── IMG_3323–IMG_3357.PNG
```

## 数据说明

| 指标 | 数值 |
|------|------|
| 数据来源 | 官方议程 App 截图（手工 OCR） |
| 原始数据行数（含同场多演讲者重复） | 312 |
| 去重后唯一 session 数 | 140 |
| 参与演讲者总数 | 215 |
| 参与组织总数 | 199 |

## 复现图表

```bash
pip install matplotlib squarify networkx pandas
python power_analysis/generate_charts.py
```

图表将输出至 `power_analysis/figures/`。

## 许可

数据来源为公开会议议程，分析内容以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 协议发布。
