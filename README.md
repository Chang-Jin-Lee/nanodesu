<div align="center">
  <img src="assets/alice_face.png" width="120" alt="Alice" />

  # nanodesu 🐰📖

  <sub>An auto-updating trend report for anime & games, split across Global / Japan</sub>

  [![Update Trend Report](https://github.com/Chang-Jin-Lee/nanodesu/actions/workflows/update-report.yml/badge.svg)](https://github.com/Chang-Jin-Lee/nanodesu/actions/workflows/update-report.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

  <!--START_SECTION:last-updated-->
Last updated: 2026-07-19 05:32 UTC
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
| 1 | Bleach | 5 | ▲1 | animecorner, gematsu, noisypixel, reddit_gachagaming |
| 2 | Jaadugar: A Witch in Mongolia | 3 | NEW | ann, reddit_anime |
| 3 | ONE PIECE | 3 | ▼2 | animecorner, ann |
| 4 | The Frontier Lord Begins with Zero Subjects | 3 | ▼1 | animecorner, ann, reddit_anime |
| 5 | Chainsaw Man | 2 | ▼1 | ann, reddit_anime |

<!--END_SECTION:global-anime-top5-->

## 🌐 Global — Game Buzz Top 5 (Last 7 Days)

<!--START_SECTION:global-game-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | Zenless Zone Zero | 5 | - | gematsu, reddit_gachagaming, rpgsite, steam-4162040 |
| 2 | Wuthering Waves | 3 | NEW | animecorner, gematsu, noisypixel |
| 3 | Blue Archive | 1 | NEW | noisypixel |
| 4 | Honkai: Star Rail | 1 | ▼2 | reddit_gachagaming |
| 5 | Umamusume: Pretty Derby | 1 | ▼2 | animecorner |

<!--END_SECTION:global-game-top5-->

## 🎌 Japan — Anime Buzz Top 5 (Last 7 Days)

<!--START_SECTION:japan-anime-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | ONE PIECE | 3 | - | animeanime, shonenjump |
| 2 | Jujutsu Kaisen | 2 | ▲2 | animeanime |
| 3 | Demon Slayer: Kimetsu no Yaiba | 1 | ▼1 | animeanime |
| 4 | GTO | 1 | ▼1 | shonenmagazine |
| 5 | Haikyu!! | 1 | NEW | animeanime |

<!--END_SECTION:japan-anime-top5-->

## 🎌 Japan — Game Buzz Top 5 (Last 7 Days)

<!--START_SECTION:japan-game-top5-->
| # | Title | Mentions | Δ | Sources |
|---|---|---|---|---|
| 1 | Zenless Zone Zero | 2 | - | fourgamer |
| 2 | Honkai: Star Rail | 1 | - | fourgamer |

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
