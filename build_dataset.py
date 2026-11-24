"""Build clean CSVs from the hand-collected raw_*.txt files and validate them.

Run:  python3 scripts/build_dataset.py
"""
import csv
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Season -> (first ep, last ep, episodes per Wikipedia overview, first release, last release)
SEASONS = {
    1: (1, 8, 8, "2015-03-12", "2015-10-22"), 2: (9, 48, 40, "2015-12-10", "2016-12-22"),
    3: (49, 72, 24, "2017-01-19", "2017-06-29"), 4: (73, 96, 24, "2017-07-20", "2017-12-28"),
    5: (97, 112, 16, "2018-01-18", "2018-05-03"), 6: (113, 125, 13, "2018-06-07", "2018-09-06"),
    7: (126, 137, 12, "2018-10-04", "2018-12-20"), 8: (138, 149, 12, "2019-01-24", "2019-04-11"),
    9: (150, 162, 13, "2019-05-30", "2019-09-05"), 10: (163, 174, 12, "2019-09-19", "2019-12-05"),
    11: (175, 183, 9, "2020-01-18", "2020-04-09"), 12: (184, 193, 10, "2020-06-25", "2020-08-27"),
    13: (194, 204, 11, "2020-10-01", "2020-12-10"), 14: (205, 216, 12, "2021-01-28", "2021-04-15"),
    15: (217, 228, 12, "2021-05-27", "2021-08-12"), 16: (229, 242, 14, "2021-09-23", "2021-12-23"),
    17: (243, 254, 12, "2022-01-20", "2022-04-07"), 18: (255, 266, 12, "2022-05-26", "2022-08-11"),
    19: (267, 278, 12, "2022-09-29", "2022-12-22"), 20: (279, 290, 12, "2023-01-26", "2023-04-13"),
    21: (291, 302, 12, "2023-05-25", "2023-08-10"), 22: (303, 314, 12, "2023-09-21", "2023-12-07"),
    23: (315, 327, 13, "2024-01-25", "2024-04-18"), 24: (328, 340, 13, "2024-05-23", "2024-08-23"),
    25: (341, 354, 14, "2024-09-19", "2024-12-05"), 26: (355, 367, 13, "2025-01-15", "2025-04-10"),
    27: (368, 380, 13, "2025-05-22", "2025-08-07"), 28: (381, 393, 12 + 1, "2025-09-18", "2025-12-04"),
    29: (394, 407, 13, "2026-01-22", "2026-04-13"), 30: (408, 423, 16, "2026-05-21", "2026-09-14"),
    31: (424, 428, None, "2026-09-24", None),
}
CATS = {"MU": "Music", "AC": "Actor", "CO": "Comedian", "AT": "Athlete", "WM": "Wrestling/MMA",
        "CH": "Chef/Food", "CR": "Creator", "ME": "Media/Host", "OT": "Other"}


def season_of(ep):
    for s, (a, b, *_rest) in SEASONS.items():
        if a <= ep <= b:
            return s
    raise ValueError(ep)


def read_pipe(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append(line.split("|"))
    return rows


def build_episodes():
    out = []
    for r in read_pipe(DATA / "raw_episodes.txt"):
        ep, date, guests, cat, flag = int(r[0]), r[1], r[2], r[3], (r[4] if len(r) > 4 else "")
        s = season_of(ep)
        names = [g.strip() for g in guests.split(";")]
        out.append({
            "episode": ep, "season": s, "air_date": date, "year": int(date[:4]),
            "guests": ";".join(names), "n_guests": len(names), "category": CATS[cat],
            "is_bonus": int("B" in flag), "is_removed": int("R" in flag),
            "is_holiday": int("H" in flag), "is_character": int("C" in flag),
        })
    df = pd.DataFrame(out)
    df["episode_in_season"] = df.groupby("season").cumcount() + 1
    return df


def build_seasons(eps):
    rows = []
    for s, (a, b, n_expected, first, last) in SEASONS.items():
        sub = eps[eps.season == s]
        rows.append({
            "season": s, "first_episode": int(sub.episode.min()), "last_episode": int(sub.episode.max()),
            "n_episodes_in_dataset": len(sub), "n_episodes_wikipedia_overview": n_expected,
            "first_air_date": sub.air_date.min(), "last_air_date": sub.air_date.max(),
        })
    return pd.DataFrame(rows)


def build_sauces():
    rows = []
    for r in read_pipe(DATA / "raw_sauces.txt"):
        s = int(r[0])
        for pos, item in enumerate(r[1].split(";"), start=1):
            name, shu = item.rsplit("~", 1)
            rows.append({"season": s, "wing": pos, "sauce": name.strip(),
                         "shu": int(shu) if shu.strip() else None})
    df = pd.DataFrame(rows)
    df["log10_shu"] = df.shu.map(lambda x: math.log10(x) if pd.notna(x) else None)
    return df


def build_anchors():
    rows = []
    for r in read_pipe(DATA / "raw_sauce_anchors.txt"):
        rows.append({"season": int(r[0]), "wing": int(r[1]), "sauce": r[2], "shu": int(r[3]),
                     "note": r[4] if len(r) > 4 else ""})
    return pd.DataFrame(rows)


def build_nonfinishers(eps):
    rows = []
    for r in read_pipe(DATA / "raw_nonfinishers.txt"):
        ep = int(r[1])
        e = eps[eps.episode == ep].iloc[0]
        rows.append({"guest": r[0], "episode": ep, "season": int(e.season), "air_date": e.air_date,
                     "category": e.category, "last_wing_eaten": int(r[2]) if r[2] else None,
                     "confidence": r[3], "note": r[4], "source": r[5]})
    return pd.DataFrame(rows)


def build_specials():
    rows = []
    for r in read_pipe(DATA / "raw_specials.txt"):
        rows.append({"air_date": r[0], "guests": r[1], "kind": r[2], "note": r[3]})
    return pd.DataFrame(rows)


def build_views():
    rows = []
    for r in read_pipe(DATA / "raw_views_snapshots.txt"):
        rows.append({"episode": int(r[0]), "guest": r[1], "views": int(r[2]), "as_of": r[3],
                     "precision": r[4], "source": r[5]})
    return pd.DataFrame(rows)


def validate(eps, seasons):
    problems = []
    if eps.episode.duplicated().any():
        problems.append("duplicate episode numbers")
    for _, r in seasons.iterrows():
        exp = r.n_episodes_wikipedia_overview
        if exp is not None and not pd.isna(exp) and r.season != 28 and r.n_episodes_in_dataset != exp:
            problems.append(f"S{r.season}: dataset has {r.n_episodes_in_dataset}, overview says {int(exp)}")
    # season 28: overview lists 12 episodes + Keke Palmer (15 Sep) opener counted separately
    s28 = seasons[seasons.season == 28].iloc[0]
    if s28.n_episodes_in_dataset != 13:
        problems.append(f"S28: expected 13 rows, got {s28.n_episodes_in_dataset}")
    gaps = sorted(set(range(1, int(eps.episode.max()) + 1)) - set(eps.episode))
    return problems, gaps


if __name__ == "__main__":
    eps = build_episodes()
    seasons = build_seasons(eps)
    problems, gaps = validate(eps, seasons)
    sauces = build_sauces()
    anchors = build_anchors()
    nonf = build_nonfinishers(eps)
    specials = build_specials()
    views = build_views()

    eps.to_csv(DATA / "episodes.csv", index=False)
    seasons.to_csv(DATA / "seasons.csv", index=False)
    sauces.to_csv(DATA / "sauce_lineups.csv", index=False)
    anchors.to_csv(DATA / "sauce_anchor_points_partial_seasons.csv", index=False)
    nonf.to_csv(DATA / "documented_non_finishers.csv", index=False)
    specials.to_csv(DATA / "specials.csv", index=False)
    views.to_csv(DATA / "views_snapshots_not_comparable.csv", index=False)

    print(f"episodes: {len(eps)}  seasons: {eps.season.nunique()}  sauces rows: {len(sauces)}")
    print(f"non-finishers documented: {len(nonf)}  specials: {len(specials)}")
    print("validation problems:", problems or "none")
    print("episode-number gaps in source list:", gaps or "none")
