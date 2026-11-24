"""Hot Ones analytics: statistics, small models and figures.

Run after build_dataset.py:  python3 scripts/analysis.py
Outputs: figures/*.png and data/results.json (numbers quoted in the paper + dashboard).
"""
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
DATA, FIG = ROOT / "data", ROOT / "figures"
FIG.mkdir(exist_ok=True)

# Validated reference palette (light mode) from the dataviz skill
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GRAY, INK, INK2, MUTED, GRID = "#898781", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SURFACE = "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
    "legend.frameon": False,
})
HOSTS = {"Sean Evans (interviewed)", "Sean Evans (interviews himself)", "Jimmy Fallon", "Puss in Boots"}

eps = pd.read_csv(DATA / "episodes.csv")
sauces = pd.read_csv(DATA / "sauce_lineups.csv")
anch = pd.read_csv(DATA / "sauce_anchor_points_partial_seasons.csv")
nonf = pd.read_csv(DATA / "documented_non_finishers.csv")
spec = pd.read_csv(DATA / "specials.csv")
R = {}  # results


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


# ------------------------------------------------------------------ 1. catalogue
human = eps[(eps.is_character == 0) & (eps.is_removed == 0) & (eps.guests != "Holiday Special (various)")]
ex = human.assign(name=human.guests.str.split(";")).explode("name")
cnt = Counter(ex.name)
spec_cnt = Counter()
for g in spec.guests:
    for n in g.split(";"):
        if n not in HOSTS:
            spec_cnt[n] += 1
total_app = {n: cnt.get(n, 0) + spec_cnt.get(n, 0) for n in set(cnt) | set(spec_cnt)}
repeat = sorted(((n, c) for n, c in total_app.items() if c >= 2 and cnt.get(n, 0) >= 1), key=lambda x: (-x[1], x[0]))
R["n_numbered_episodes"] = int(len(eps))
R["n_seasons"] = int(eps.season.nunique())
R["n_human_episodes"] = int(len(human))
R["n_unique_guest_names"] = int(len(cnt))
R["n_repeat_guests"] = len(repeat)
R["repeat_guests"] = [{"guest": n, "appearances": c} for n, c in repeat]
R["first_date"], R["last_date"] = eps.air_date.min(), eps.air_date.max()
R["multi_guest_episodes"] = int((eps.n_guests > 1).sum())

# ------------------------------------------------------------------ 2. cadence
per_year = eps.groupby("year").size()
R["episodes_per_year"] = {int(k): int(v) for k, v in per_year.items()}
d = pd.to_datetime(eps.sort_values(["air_date", "episode"]).air_date)
gaps = d.diff().dt.days.dropna()
R["median_gap_days"] = float(gaps.median())
R["share_gaps_exactly_7_days"] = float((gaps == 7).mean())
R["share_gaps_over_14_days"] = float((gaps > 14).mean())
R["longest_gap_days"] = int(gaps.max())
R["post_2018_median_gap"] = float(d[d >= "2018-06-01"].diff().dt.days.dropna().median())

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(per_year.index.astype(str), per_year.values, color=BLUE, width=0.62)
for x, v in zip(per_year.index.astype(str), per_year.values):
    ax.text(x, v + 0.8, str(v), ha="center", fontsize=8, color=INK2)
ax.set_title("Episodes per calendar year")
ax.set_ylabel("Numbered episodes")
ax.text(0.99, 0.95, "2026 is partial (data through Oct 22)", transform=ax.transAxes, ha="right", va="top", fontsize=8, color=MUTED)
ax.grid(axis="x", visible=False)
fig.tight_layout()
fig.savefig(FIG / "f1_episodes_per_year.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ 3. who gets booked
cat_order = ["Actor", "Music", "Comedian", "Athlete"]
h = human.copy()
h["cat5"] = h.category.where(h.category.isin(cat_order), "Other")
tab = pd.crosstab(h.year, h.cat5)
share = tab.div(tab.sum(axis=1), axis=0)
R["category_share_by_year"] = {int(y): {c: round(float(share.loc[y, c]), 3) for c in share.columns} for y in share.index}
R["category_counts_overall"] = {c: int(v) for c, v in h.category.value_counts().items()}

early, recent = h[h.year <= 2018], h[h.year >= 2023]
ct = pd.crosstab(pd.concat([early.assign(era="2015-2018"), recent.assign(era="2023-2026")]).era,
                 pd.concat([early, recent]).cat5.values)
chi2, p, dof, _ = stats.chi2_contingency(ct)
cramers_v = math.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
R["era_test"] = {"early_n": int(len(early)), "recent_n": int(len(recent)), "chi2": round(float(chi2), 2),
                 "dof": int(dof), "p": float(p), "cramers_v": round(cramers_v, 3),
                 "early_share": {c: round(float((early.cat5 == c).mean()), 3) for c in cat_order + ["Other"]},
                 "recent_share": {c: round(float((recent.cat5 == c).mean()), 3) for c in cat_order + ["Other"]}}

rng = np.random.default_rng(7)
yrs = (h.year.values - 2020).reshape(-1, 1).astype(float)
trend = {}
for c in cat_order:
    y = (h.category.values == c).astype(int)
    m = LogisticRegression(C=1e6, max_iter=1000).fit(yrs, y)
    boots = []
    for _ in range(600):
        i = rng.integers(0, len(y), len(y))
        if y[i].sum() in (0, len(y)):
            continue
        boots.append(LogisticRegression(C=1e6, max_iter=1000).fit(yrs[i], y[i]).coef_[0][0])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    trend[c] = {"odds_ratio_per_year": round(math.exp(m.coef_[0][0]), 3),
                "ci95": [round(math.exp(lo), 3), round(math.exp(hi), 3)]}
R["category_year_trend_logit"] = trend

cols = [BLUE, ORANGE, AQUA, YELLOW, GRAY]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
bottom = np.zeros(len(share))
for col, c in zip(cols, cat_order + ["Other"]):
    ax.bar(share.index.astype(str), share[c], bottom=bottom, color=col, label=c, width=0.7,
           edgecolor=SURFACE, linewidth=1.5)
    bottom += share[c].values
ax.set_title("Guest mix by year (share of episodes)")
ax.set_ylim(0, 1)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
ax.grid(axis="x", visible=False)
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.08), fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "f2_category_share_by_year.png", dpi=200)
plt.close(fig)

top = repeat[:14]
fig, ax = plt.subplots(figsize=(7, 4.6))
ax.barh([n for n, _ in top][::-1], [c for _, c in top][::-1], color=BLUE, height=0.62)
ax.set_title("Most frequent guests (numbered episodes + reunion/holiday specials)")
ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
ax.grid(axis="y", visible=False)
fig.tight_layout()
fig.savefig(FIG / "f3_repeat_guests.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ 4. the heat ramp
piv = sauces.pivot(index="season", columns="wing", values="shu")
lp = np.log10(piv)
R["n_full_lineup_seasons"] = int(len(piv))
med = lp.median()
R["median_shu_by_wing"] = {int(w): int(round(10 ** med[w])) for w in med.index}
steps = {}
for w in range(1, 10):
    r = (piv[w + 1] / piv[w]).dropna()
    steps[w] = {"median_ratio": round(float(r.median()), 2), "n": int(len(r))}
R["step_ratio_by_wing"] = steps

slopes, mean27 = {}, {}
for s, row in lp.iterrows():
    pts = row.loc[1:8].dropna()
    slopes[s] = float(np.polyfit(pts.index.values, pts.values, 1)[0])
    mean27[s] = float(row.loc[2:7].mean())
sl = pd.Series(slopes)
R["ramp_slope_log10_per_wing_median"] = round(float(sl.median()), 3)
R["ramp_slope_implied_multiplier_per_wing"] = round(float(10 ** sl.median()), 2)
rho, pv = stats.spearmanr(sl.index, sl.values)
R["slope_vs_season_spearman"] = {"rho": round(float(rho), 3), "p": float(pv)}
m27 = pd.Series(mean27)
rho2, pv2 = stats.spearmanr(m27.index, m27.values)
R["mean_log10_wings2to7_vs_season_spearman"] = {"rho": round(float(rho2), 3), "p": float(pv2)}
R["mean_log10_wings2to7_by_season"] = {int(k): round(float(v), 3) for k, v in m27.items()}
# S1 monotonicity check on published SHU
mono_viol = {int(s): int((piv.loc[s].dropna().diff().dropna() < 0).sum()) for s in piv.index}
R["seasons_with_nonmonotonic_published_shu"] = {s: v for s, v in mono_viol.items() if v}
# wing 8 = Da Bomb
w8 = piv[8]
R["da_bomb_wing8_shu_range_S2_onward"] = [int(w8.loc[2:].min()), int(w8.loc[2:].max())]
R["wing8_to_wing1_ratio_median"] = round(float((piv[8] / piv[1]).median()), 1)
R["wing10_to_wing8_ratio_median"] = round(float((piv[10] / piv[8]).median()), 1)
R["wing9_to_wing8_ratio_median"] = round(float((piv[9] / piv[8]).median()), 2)

fig, ax = plt.subplots(figsize=(8, 4.8))
for s, row in piv.iterrows():
    ax.plot(row.index, row.values, color="#c3c2b7", lw=1.0, zorder=1)
ax.plot(med.index, 10 ** med.values, color=ORANGE, lw=2.4, marker="o", ms=5, label="Median across seasons", zorder=3)
ax.axvline(8, color=MUTED, lw=0.8, ls=(0, (3, 3)))
ax.text(8.08, 700, "Wing 8:\nDa Bomb", fontsize=8, color=INK2, va="bottom")
ax.set_yscale("log")
ax.set_xticks(range(1, 11))
ax.set_xlabel("Wing")
ax.set_ylabel("Published Scoville (log scale)")
ax.set_title(f"The heat ramp, {len(piv)} seasons with full published lineups")
ax.legend(loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "f4_heat_ramp.png", dpi=200)
plt.close(fig)

# anchors across all 31 seasons for wing 1 / 8 / 10
allpts = pd.concat([sauces[["season", "wing", "shu"]], anch[["season", "wing", "shu"]]]).dropna()
anchor_lines = {w: allpts[allpts.wing == w].drop_duplicates(["season", "wing"]).set_index("season").shu.sort_index()
                for w in (1, 8, 10)}
R["wing_anchor_series"] = {int(w): {int(s): int(v) for s, v in ser.items()} for w, ser in anchor_lines.items()}
fig, ax = plt.subplots(figsize=(8.4, 4.6))
for w, col, lab in [(10, ORANGE, "Wing 10 (The Last Dab)"), (8, AQUA, "Wing 8"), (1, BLUE, "Wing 1")]:
    ser = anchor_lines[w]
    ax.plot(ser.index, ser.values, color=col, lw=1.8, marker="o", ms=4, label=lab)
ax.set_yscale("log")
ax.set_xlabel("Season")
ax.set_ylabel("Published Scoville (log scale)")
ax.set_title("Where the show anchors its ramp: wings 1, 8 and 10")
ax.legend(fontsize=8, loc="center right")
ax.text(0.01, 0.02, "Wing 10 is unpublished for several recent seasons (shown only where a source gave a value).",
        transform=ax.transAxes, fontsize=7.5, color=MUTED)
fig.tight_layout()
fig.savefig(FIG / "f5_anchor_wings_by_season.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ 5. who taps out
n_h = len(human)
k = len(nonf)
lo, hi = wilson(k, n_h)
R["documented_non_finishers"] = int(k)
R["documented_non_finisher_rate_lower_bound"] = round(k / n_h, 4)
R["documented_non_finisher_rate_wilson95_of_documented"] = [round(lo, 4), round(hi, 4)]
known = nonf.dropna(subset=["last_wing_eaten"])
lw = known.last_wing_eaten.astype(int)
R["non_finishers_with_known_wing"] = int(len(known))
R["last_wing_counts"] = {int(a): int(b) for a, b in Counter(lw).items()}
k8 = int((lw == 8).sum())
R["share_stopping_after_wing8"] = round(k8 / len(lw), 3)
# null: uniform over wings 2..9 (8 values)
bt = stats.binomtest(k8, len(lw), p=1 / 8, alternative="greater")
R["binomial_test_wing8_vs_uniform"] = {"k": k8, "n": int(len(lw)), "null_p": 0.125, "p_value": float(bt.pvalue)}
R["non_finishers_by_category"] = {c: int(v) for c, v in nonf.category.value_counts().items()}
R["non_finishers_by_era"] = {"2015-2018": int((nonf.air_date < "2019-01-01").sum()),
                             "2019-2022": int(((nonf.air_date >= "2019-01-01") & (nonf.air_date < "2023-01-01")).sum()),
                             "2023-2026": int((nonf.air_date >= "2023-01-01").sum())}
R["non_finisher_share_music_vs_music_in_catalogue"] = {
    "among_non_finishers": round(float((nonf.category == "Music").mean()), 3),
    "among_all_episodes": round(float((human.category == "Music").mean()), 3)}
mu_k, mu_n = int((nonf.category == "Music").sum()), int((human.category == "Music").sum())
tbl = [[mu_k, k - mu_k], [mu_n - mu_k, (n_h - mu_n) - (k - mu_k)]]
R["fisher_music_vs_rest"] = {"odds_ratio": round(float(stats.fisher_exact(tbl)[0]), 2), "p": float(stats.fisher_exact(tbl)[1])}

counts = Counter(lw)
xs = list(range(2, 10))
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.bar([str(x) for x in xs], [counts.get(x, 0) for x in xs], color=BLUE, width=0.62)
for i, x in enumerate(xs):
    v = counts.get(x, 0)
    if v:
        ax.text(i, v + 0.1, str(v), ha="center", fontsize=9, color=INK2)
ax.set_title("Documented non-finishers: last wing eaten")
ax.set_xlabel("Last wing eaten before tapping out")
ax.set_ylabel("Guests")
ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
ax.grid(axis="x", visible=False)
ax.text(0.01, 0.97, f"n = {len(lw)} with a documented wing count ({k - len(lw)} more documented without one)",
        transform=ax.transAxes, fontsize=8, color=MUTED, va="top")
fig.tight_layout()
fig.savefig(FIG / "f6_non_finishers_by_wing.png", dpi=200)
plt.close(fig)

(DATA / "results.json").write_text(json.dumps(R, indent=2, default=str), encoding="utf-8")
print(json.dumps({k: R[k] for k in [
    "n_numbered_episodes", "n_human_episodes", "n_unique_guest_names", "n_repeat_guests", "median_gap_days",
    "share_gaps_exactly_7_days", "era_test", "category_year_trend_logit", "median_shu_by_wing",
    "step_ratio_by_wing", "ramp_slope_implied_multiplier_per_wing", "slope_vs_season_spearman",
    "mean_log10_wings2to7_vs_season_spearman", "seasons_with_nonmonotonic_published_shu",
    "documented_non_finishers", "documented_non_finisher_rate_lower_bound", "last_wing_counts",
    "share_stopping_after_wing8", "binomial_test_wing8_vs_uniform", "non_finishers_by_category",
    "fisher_music_vs_rest", "wing9_to_wing8_ratio_median", "wing10_to_wing8_ratio_median"]}, indent=1, default=str))
