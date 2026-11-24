"""Views model (runs only when data/views_full.csv exists; see fetch_views.py).

Model: log10(views) ~ log10(age in days) + category dummies + multi-guest flag + holiday flag.
Reports coefficients with bootstrap 95% CIs, so category effects are read as % differences in views
at the same episode age. Episodes are NOT independent draws (the show's audience grew), so treat as descriptive.

Usage: python3 scripts/views_model.py [path/to/views_full.csv]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

DATA = Path(__file__).resolve().parent.parent / "data"
path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "views_full.csv"
if not path.exists():
    sys.exit(f"{path} not found - run scripts/fetch_views.py first")

eps = pd.read_csv(DATA / "episodes.csv")
v = pd.read_csv(path).merge(eps, on="episode")
v = v[(v.is_character == 0) & (v.is_removed == 0) & v.views.notna() & (v.views > 0)].copy()
v["age_days"] = (pd.to_datetime(v.as_of_date) - pd.to_datetime(v.air_date)).dt.days.clip(lower=1)
X = pd.get_dummies(v.category, prefix="cat", drop_first=False).astype(float)
X = X.drop(columns=["cat_Actor"])  # Actor = reference level
X["log_age"] = np.log10(v.age_days)
X["multi_guest"] = (v.n_guests > 1).astype(float)
X["holiday"] = v.is_holiday.astype(float)
y = np.log10(v.views.values)
m = LinearRegression().fit(X, y)
rng = np.random.default_rng(1)
boots = np.array([LinearRegression().fit(X.iloc[i], y[i]).coef_
                  for i in (rng.integers(0, len(y), len(y)) for _ in range(1000))])
lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
out = pd.DataFrame({"term": X.columns, "coef_log10": m.coef_, "pct_vs_actor_or_per_unit": (10 ** m.coef_ - 1) * 100,
                    "ci_low_pct": (10 ** lo - 1) * 100, "ci_high_pct": (10 ** hi - 1) * 100})
print(f"n = {len(v)}  R^2 = {m.score(X, y):.3f}")
print(out.round(2).to_string(index=False))
out.to_csv(DATA / "views_model_results.csv", index=False)
