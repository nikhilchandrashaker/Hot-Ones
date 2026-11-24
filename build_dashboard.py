"""Build dashboard/hot_ones_dashboard.html (self-contained) from the CSVs + results.json."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
eps = pd.read_csv(D / "episodes.csv")
sauces = pd.read_csv(D / "sauce_lineups.csv")
anch = pd.read_csv(D / "sauce_anchor_points_partial_seasons.csv")
nonf = pd.read_csv(D / "documented_non_finishers.csv")
res = json.loads((D / "results.json").read_text())

def clean(df):
    df = df.astype(object).where(df.notna(), None)
    return [{k: (int(v) if hasattr(v, "item") and isinstance(v.item(), int) else v) for k, v in r.items()} for r in df.to_dict("records")]


top4 = ["Actor", "Music", "Comedian", "Athlete"]
eps["cat4"] = eps.category.where(eps.category.isin(top4), "Other")
data = {
    "episodes": eps[eps.is_character == 0][["episode", "season", "air_date", "year", "guests", "category", "cat4", "is_bonus", "is_removed", "is_holiday"]].to_dict("records"),
    "all_episodes": eps[["episode", "season", "air_date", "guests", "category", "is_bonus", "is_removed", "is_holiday", "is_character"]].to_dict("records"),
    "sauces": clean(sauces),
    "anchors": clean(anch),
    "nonf": clean(nonf),
    "res": {k: res[k] for k in ["median_shu_by_wing", "step_ratio_by_wing", "mean_log10_wings2to7_by_season",
                                "repeat_guests", "era_test", "category_year_trend_logit", "last_wing_counts",
                                "documented_non_finisher_rate_lower_bound", "episodes_per_year", "n_human_episodes", "n_numbered_episodes",
                                "n_unique_guest_names", "n_repeat_guests", "wing_anchor_series"]},
}
html = (ROOT / "scripts" / "dashboard_template.html").read_text(encoding="utf-8")
out = ROOT / "dashboard" / "hot_ones_dashboard.html"
out.write_text(html.replace("__DATA__", json.dumps(data, allow_nan=False, default=lambda o: None)), encoding="utf-8")
print("wrote", out, out.stat().st_size // 1024, "KB")
