<div align="center">
  <img src="assets/alice_face.png" width="120" alt="Alice" />

  # nanodesu 🐰📖

  <sub>An auto-updating trend report for anime & games, split across Global / Japan</sub>

  [![Update Trend Report](https://github.com/Chang-Jin-Lee/nanodesu/actions/workflows/update-report.yml/badge.svg)](https://github.com/Chang-Jin-Lee/nanodesu/actions/workflows/update-report.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

  <!--START_SECTION:last-updated-->
Last updated: 2026-08-07 14:14 UTC
<!--END_SECTION:last-updated-->
</div>

---

## 📖 What is this?

`nanodesu` is a repository that tracks anime & game ("subculture") trends automatically. Every Mon/Wed/Fri, GitHub Actions collects anime/game news, AniList trending data, and Japanese magazine & collab-cafe announcements, then refreshes **mention-based trending rankings (last 7 / 30 days)** and a **Japan collab-event calendar** — no manual work involved.

- 🌐 [Full Global report](reports/global.md)
- 🎌 [Full Japan report](reports/japan.md)

## 🌐 Global — Anime Buzz Top 5 (Last 7 Days)

<!--START_SECTION:global-anime-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | ONE PIECE | 5 | - | animecorner, ann |
| 2 | Bleach | 4 | ▲2 | animecorner, ann |
| 3 | Though I Am an Inept Villainess | 3 | ▲13 | animecorner, ann, reddit_anime |
| 4 | Chainsaw Man | 2 | ▲1 | animecorner |
| 5 | Chainsmoker Cat | 2 | ▼3 | ann, reddit_anime |

<!--END_SECTION:global-anime-top5-->

## 🌐 Global — Game Buzz Top 5 (Last 7 Days)

<!--START_SECTION:global-game-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | Blue Archive | 1 | NEW | automatonwest |
| 2 | Genshin Impact | 1 | ▼1 | rpgsite |
| 3 | Umamusume: Pretty Derby | 1 | ▼1 | animecorner |
| 4 | Wuthering Waves | 1 | NEW | gematsu |

<!--END_SECTION:global-game-top5-->

## 🎌 Japan — Anime Buzz Top 5 (Last 7 Days)

<!--START_SECTION:japan-anime-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | Bleach | 4 | - | animeanime |
| 2 | Jujutsu Kaisen | 4 | - | animeanime |
| 3 | Demon Slayer: Kimetsu no Yaiba | 3 | ▲2 | animeanime |
| 4 | Haikyu!! | 3 | ▼1 | animeanime |
| 5 | ONE PIECE | 3 | ▼1 | animeanime |

<!--END_SECTION:japan-anime-top5-->

## 🎌 Japan — Game Buzz Top 5 (Last 7 Days)

<!--START_SECTION:japan-game-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | Zenless Zone Zero | 2 | ▲3 | fourgamer |
| 2 | Genshin Impact | 1 | - | fourgamer |
| 3 | Wuthering Waves | 1 | NEW | fourgamer |

<!--END_SECTION:japan-game-top5-->

The full event calendar (collab cafes, pop-up stores, conventions) lives in [reports/japan.md](reports/japan.md).

## 🛠️ How it works

```
fetch_all.py → extract_mentions.py → rank_trends.py → build_events.py → render_reports.py
     │                │                    │                │                  │
  RSS / API /      match against       aggregate into     merge, dedupe    regenerate
  scraping         watchlist.yaml      7d/30d windows     & sort events    README/reports
```

Raw data is versioned per-day under `data/raw/`, aggregates under `data/trends/` and `data/events/`. Each step is a standalone module under `scripts/` with a matching test file under `tests/`.

## 🤝 Contributing

Love anime, manga, or games? You're already qualified — adding a missing title or alias to the watchlist takes one YAML entry and directly improves the rankings. See [CONTRIBUTING.md](CONTRIBUTING.md) for all the ways to help, no code required.

## 🐰 About Alice

<img src="assets/alice_upper.png" width="200" align="right" alt="Alice upper body" />

Meet **Alice**, this repository's mascot. She's always the first to check the news whenever a report refreshes.

<br clear="right"/>

## 📄 License

Code is released under the [MIT License](LICENSE). Alice is the author's original character created with VRoid Studio; her images (`assets/`) are **not** covered by the MIT license — please don't reuse them outside this repository.

Report data is aggregated from public RSS feeds and APIs; each table links back to its sources.
