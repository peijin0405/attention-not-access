# 注意力不等于话语权

**2025 Blockchain Futurist Conference 议程的叙事准入结构分析**

---

## 关于这个项目

本项目基于 2025 年 Blockchain Futurist Conference（多伦多，2025 年 8 月）的完整议程数据，通过「议题—舞台—演讲者—组织」四层分析框架，考察注意力分配（session 出现频率）与叙事准入机会（主舞台占比）之间的结构性关系。

**核心发现**：话题热度与主舞台准入率之间存在系统性解耦——Ethereum 作为全场第二大话题，主舞台出席场次为零；社区类组织议题覆盖最广但主舞台占比为零；会议空间内部存在三类相互独立的 Web3 议题社群。

## 文件结构

```
.
├── power_analysis/
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
| 原始数据行数 | 312 行（含同场多演讲者） |
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
