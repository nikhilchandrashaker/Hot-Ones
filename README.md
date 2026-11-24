# Hot Ones analytics, 2015–2026

A hand-built dataset, analysis, research paper and interactive dashboard on *Hot Ones* (First We Feast): who gets invited, how the heat ladder is built, and where guests tap out.

**Dashboard:** open `dashboard/hot_ones_dashboard.html` in any browser (self-contained, works offline, light/dark mode, table views, searchable guest table).
**Paper:** `paper/hot_ones_paper.pdf`

## Headline findings
- **Guest mix shifted to actors.** Actors went from 15.6% of 2015–2018 episodes to 46.9% of 2023–2026; comedians fell from 23.0% to 8.2% (chi-square(4) = 41.4, Cramér's V = 0.38). Actor odds rise about 22% per year (95% CI 1.15–1.30 odds ratio).
- **The heat ladder is a cliff.** Median SHU by wing runs 1,800 → 120,000 through wing 8, then 666,000 (wing 9) and 2,000,000 (wing 10). Median step ratios are 1.2–1.5× through the middle wings, then 5.4× into wing 9 and 3.4× into wing 10.
- **Middle wings got hotter; Da Bomb (wing 8) did not.** Mean log10 SHU of wings 2–7 rises with season (Spearman rho = 0.90).
- **Documented tap-outs cluster after wing 8.** 8 of 11 with a known stopping point (exact binomial test vs. uniform, p < 0.001). 18 documented non-finishers is a lower bound of 4.3% of episodes, not a completion rate.

## What's here
```
data/        CSVs (+ raw_*.txt hand-collected inputs, results.json)
scripts/     build_dataset.py -> analysis.py -> build_dashboard.py / build_paper.py
             fetch_views.py + views_model.py (optional, see "Views" below)
figures/     f1–f6 PNGs used in the paper
dashboard/   hot_ones_dashboard.html
paper/       hot_ones_paper.pdf
```
Reproduce: `python3 scripts/build_dataset.py && python3 scripts/analysis.py && python3 scripts/build_dashboard.py && python3 scripts/build_paper.py`
(needs pandas, numpy, scipy, scikit-learn, matplotlib, reportlab).

## Data dictionary
**episodes.csv** (427 rows): `episode` number; `season`; `air_date`; `year`; `guests` (`;`-separated); `n_guests`; `category` (analyst-coded: Music, Actor, Comedian, Athlete, Wrestling/MMA, Chef/Food, Creator, Media/Host, Other); `is_bonus`, `is_removed` (removed from YouTube), `is_holiday`, `is_character` (non-human guest); `episode_in_season`.
**seasons.csv**: per-season episode counts and date range, with the count Wikipedia's overview gives (season 28 has one extra row, the Keke Palmer opener).
**sauce_lineups.csv**: `season`, `wing` 1–10, `sauce`, `shu`, `log10_shu`. Seasons 1–21, 29, 30; blank SHU where unpublished.
**sauce_anchor_points_partial_seasons.csv**: published SHU for individual wings in seasons 22–28.
**documented_non_finishers.csv**: 18 guests with `last_wing_eaten`, `confidence`, `note`, `source`.
**specials.csv**: 22 off-format specials (late-night crossovers, reunions, promos, holiday); not included in episode counts.
**views_snapshots_not_comparable.csv**: nine one-off view numbers with different as-of dates. **Do not model these.**
**results.json**: every statistic cited in the paper.

## Limitations
- Episode 397 is missing from the source list I used (427 rows for episodes 1–428).
- Guest categories are my own judgment, one label per guest, no second rater.
- Tap-outs come from press coverage, not from the show. Early-era quitters were written about more, so era comparisons of tap-outs are not reliable.
- Seasons 22–28 lack full sauce lineups; wing 10 is unpublished for seasons 21, 29 and 30.
- SHU values are as published by the brand or fan sources.
- Era tests use 2015–2018 vs 2023–2026; other cut points were not explored.

## Views (not done, ready to run)
I could not collect comparable per-episode YouTube view counts, so the "what drives views" question is not answered. `scripts/fetch_views.py` (needs a YouTube Data API key and the playlist ID) writes `data/views_full.csv`, and `scripts/views_model.py` then fits log10(views) on category, episode age, multi-guest and holiday flags with bootstrap CIs. **fetch_views.py has never been run against the real API.** views_model.py was only smoke-tested on random synthetic numbers. Check the match report for unmatched episodes before trusting results.

## Sources
Wikipedia list of Hot Ones episodes and season overviews (retrieved 2026-11-22); Heatonist season pages; hotsaucehell.wordpress.com; press on tap-outs (Ranker, Mashed, BuzzFeed, Dexerto, Uproxx and others; per-row sources in `documented_non_finishers.csv`).
