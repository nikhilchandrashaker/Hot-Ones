"""Build paper/hot_ones_paper.pdf with reportlab from results.json + figures."""
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "data/results.json").read_text())
F = ROOT / "figures"
ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Times-Roman", fontSize=10.5, leading=14.2, spaceAfter=7, alignment=4)
H1 = ParagraphStyle("H1", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=13, spaceBefore=12, spaceAfter=5)
T = ParagraphStyle("T", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=4)
SUB = ParagraphStyle("SUB", parent=B, alignment=1, fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#52514e"))
CAP = ParagraphStyle("CAP", parent=B, fontName="Helvetica-Oblique", fontSize=8.5, leading=11, alignment=0, textColor=colors.HexColor("#52514e"))
ABS = ParagraphStyle("ABS", parent=B, leftIndent=24, rightIndent=24, fontSize=10)
SM = ParagraphStyle("SM", parent=B, fontSize=9, leading=12, alignment=0)

def fig(name, cap, w=6.3):
    ir = ImageReader(str(F / name)); iw, ih = ir.getSize()
    return KeepTogether([Image(str(F / name), width=w * inch, height=w * inch * ih / iw), Paragraph(cap, CAP), Spacer(1, 8)])

def page(c, d):
    c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#898781"))
    c.drawString(inch, 0.6 * inch, "Hot Ones analytics, 2015-2026"); c.drawRightString(letter[0] - inch, 0.6 * inch, f"{d.page}")
    c.restoreState()

m = R["median_shu_by_wing"]; s = R["step_ratio_by_wing"]; e = R["era_test"]; lg = R["category_year_trend_logit"]
S = []
S += [Paragraph("Who Taps Out, What Gets Hotter, and Who Gets Asked", T),
      Paragraph("An analytics history of <i>Hot Ones</i>, 2015&ndash;2026", SUB),
      Paragraph("Nikhil Chandrashaker &middot; analysis dated 2026-11-23", SUB), Spacer(1, 10)]
S += [Paragraph("<b>Abstract.</b> I assembled a hand-built dataset of every numbered <i>Hot Ones</i> episode "
      f"({R['n_numbered_episodes']} episodes across {R['n_seasons']} seasons, March 2015 to October 2026), the published Scoville "
      f"(SHU) lineup for {R['n_full_lineup_seasons']} seasons with a full lineup, and 18 press-documented guests who did not finish the "
      "wing ladder. Three findings stand out. (1) The guest mix changed sharply: actors rose from "
      f"{e['early_share']['Actor']*100:.0f}% of 2015&ndash;2018 episodes to {e['recent_share']['Actor']*100:.0f}% of 2023&ndash;2026 episodes "
      f"(chi-square({e['dof']}) = {e['chi2']:.1f}, Cram&eacute;r's V = {e['cramers_v']}), while comedians fell from "
      f"{e['early_share']['Comedian']*100:.0f}% to {e['recent_share']['Comedian']*100:.0f}%. (2) The ladder has a cliff, not a slope: the median "
      f"jump from wing 8 to wing 9 is {s['8']['median_ratio']}&times;, bigger than any earlier step, and the middle wings rise by only 1.2&times; to 1.5&times; per step. "
      " (3) Documented tap-outs cluster after wing 8: 8 of the 11 with a known stopping point. Because completion is not published, "
      "the tap-out analysis is a lower bound, not a completion model. I also state plainly what I could not do: there are no comparable per-episode view counts.", ABS)]

S += [Paragraph("1. Question and scope", H1),
      Paragraph("<i>Hot Ones</i> (First We Feast) interviews a guest while they eat ten chicken wings, each coated in a hotter sauce. "
      "Three questions are answerable from public information: how has the guest list changed, how is the heat ladder constructed and has it drifted, and where do guests "
      "stop when they stop? A fourth question, what drives episode views, needs per-episode view counts that I could not collect in comparable form, so I ship a ready-to-run model "
      "script and fetch script rather than a result.", B)]

S += [Paragraph("2. Data and methods", H1),
      Paragraph("<b>Episodes.</b> Numbered episodes 1&ndash;428 from the Wikipedia list of episodes (episode 397 is absent from the source list, so the dataset has 427 rows). "
      "Season episode counts match the Wikipedia season overview for every season; season 28 has 13 rows because the Keke Palmer opener is listed separately. "
      "Each episode is assigned one primary guest category (actor, music, comedian, athlete, wrestling/MMA, chef/food, creator, media/host, other) by me, "
      "from the guest's best-known public role. These codes are judgment calls; a guest who is both an actor and a musician has one label. Category analyses exclude the two character episodes (Donald Duck, Peter Griffin), the one episode removed from YouTube and the holiday compilation episode(s), "
      "leaving 422 episodes.", B),
      Paragraph("<b>Sauces.</b> Published SHU for each wing, from Heatonist and fan-maintained season pages, for seasons 1&ndash;21, 29 and 30. "
      "Seasons 22&ndash;28 have only partial anchor points (the wings with a published number), so they are excluded from ramp statistics. Wing 10 is blank in seasons 21, 29 and 30. "
      f"Ramp statistics use the {R['n_full_lineup_seasons']} seasons with a full lineup. SHU values are marketing or lab figures as published and are not comparable to a standard lab measurement.", B),
      Paragraph("<b>Tap-outs.</b> Eighteen guests documented in press coverage (Ranker, Mashed, BuzzFeed, Dexerto, Uproxx and similar) as not finishing, each with a last wing eaten where reported and a confidence rating. "
      "This is a convenience list, not a census.", B),
      Paragraph("<b>Statistics.</b> Wilson intervals for proportions; chi-square with Cram&eacute;r's V for the guest mix across two eras (2015&ndash;2018 vs 2023&ndash;2026); "
      "logistic regressions of each category on year with bootstrap 95% intervals; Spearman correlations; log<sub>10</sub> SHU ramp slopes; an exact binomial test and a Fisher exact test for tap-out patterns.", B)]

S += [Paragraph("3. Results", H1), Paragraph("3.1 A weekly show, mostly", ParagraphStyle("h", parent=B, fontName="Helvetica-Bold")),
      Paragraph(f"The show averages about 38 episodes a year after 2016. The median gap between episodes is {R['median_gap_days']:.0f} days and "
      f"{R['share_gaps_exactly_7_days']*100:.0f}% of gaps are exactly 7 days; {R['share_gaps_over_14_days']*100:.0f}% exceed two weeks, with a longest gap of {R['longest_gap_days']} days. "
      f"Sixteen episodes have more than one guest.", B), fig("f1_episodes_per_year.png", "Figure 1. Episodes per year. 2015 and 2026 are partial.", 5.4)]

S += [Paragraph("3.2 The guest list moved toward actors", ParagraphStyle("h", parent=B, fontName="Helvetica-Bold")),
      Paragraph(f"Comparing 2015&ndash;2018 (n = {e['early_n']}) with 2023&ndash;2026 (n = {e['recent_n']}): actors {e['early_share']['Actor']*100:.1f}% &rarr; {e['recent_share']['Actor']*100:.1f}%, "
      f"comedians {e['early_share']['Comedian']*100:.1f}% &rarr; {e['recent_share']['Comedian']*100:.1f}%, music {e['early_share']['Music']*100:.1f}% &rarr; {e['recent_share']['Music']*100:.1f}%, "
      f"athletes {e['early_share']['Athlete']*100:.1f}% &rarr; {e['recent_share']['Athlete']*100:.1f}%. The era difference is large (chi-square = {e['chi2']:.1f}, p &lt; 0.001, V = {e['cramers_v']}). "
      f"In a year-trend logistic model, the odds that an episode features an actor rise {(lg['Actor']['odds_ratio_per_year']-1)*100:.0f}% per year "
      f"(95% CI {lg['Actor']['ci95'][0]}&ndash;{lg['Actor']['ci95'][1]}) and the odds of a comedian fall {(1-lg['Comedian']['odds_ratio_per_year'])*100:.0f}% per year "
      f"(CI {lg['Comedian']['ci95'][0]}&ndash;{lg['Comedian']['ci95'][1]}). Music ({lg['Music']['ci95'][0]}&ndash;{lg['Music']['ci95'][1]}) and athletes "
      f"({lg['Athlete']['ci95'][0]}&ndash;{lg['Athlete']['ci95'][1]}) show no clear trend. Since the category codes are mine, a reader who codes crossover guests differently could shift the "
      "levels, but a change of this size is unlikely to be a coding artifact. Thirty-eight guests have appeared more than once; Keke Palmer and T-Pain lead with three each.", B),
      fig("f2_category_share_by_year.png", "Figure 2. Guest category share of episodes by year."),
      fig("f3_repeat_guests.png", "Figure 3. Guests with repeat appearances.", 5.2)]

S += [Paragraph("3.3 The heat ladder is a cliff", ParagraphStyle("h", parent=B, fontName="Helvetica-Bold")),
      Paragraph(f"Median SHU by wing across full-lineup seasons: " + ", ".join(f"{k}: {v:,}" for k, v in m.items()) + ". "
      f"The median wing 8 sauce is {R['wing8_to_wing1_ratio_median']:.0f}&times; hotter than wing 1, and wing 10 is a further {R['wing10_to_wing8_ratio_median']:.1f}&times; above wing 8. "
      f"Step ratios between consecutive wings are small in the middle (wings 4 to 7: {s['4']['median_ratio']}&times;, {s['5']['median_ratio']}&times;, {s['6']['median_ratio']}&times;, {s['7']['median_ratio']}&times;), "
      f"then jump {s['8']['median_ratio']}&times; into wing 9 and {s['9']['median_ratio']}&times; into wing 10. Wing 8 has been Da Bomb since season 2, at 120,000 to 135,600 SHU depending on the published figure.", B),
      Paragraph(f"The ladder has drifted in an interesting way. The average log<sub>10</sub> SHU of wings 2&ndash;7 rises with season (Spearman &rho; = {R['mean_log10_wings2to7_vs_season_spearman']['rho']:.2f}), "
      f"while the fixed wing 8 means the overall slope per wing flattens (&rho; = {R['slope_vs_season_spearman']['rho']:.2f}). In plain terms, the early and middle wings got hotter and the Da Bomb wall did not move. "
      "Season 1 has non-monotonic published values in two places, which I keep as published.", B),
      fig("f4_heat_ramp.png", "Figure 4. SHU by wing, one line per full-lineup season (log scale)."),
      fig("f5_anchor_wings_by_season.png", "Figure 5. Selected anchor wings by season, including partial-lineup seasons where a value is published.")]

S += [Paragraph("3.4 Where guests stop", ParagraphStyle("h", parent=B, fontName="Helvetica-Bold")),
      Paragraph(f"I documented 18 non-finishers. Against {R['n_human_episodes']} human episodes, that is at least {R['documented_non_finisher_rate_lower_bound']*100:.1f}% of episodes; the Wilson 95% interval for 18 of "
      f"{R['n_human_episodes']} is {R['documented_non_finisher_rate_wilson95_of_documented'][0]*100:.1f}%&ndash;{R['documented_non_finisher_rate_wilson95_of_documented'][1]*100:.1f}%, but this is a floor, since quiet tap-outs may never have made the press. "
      "For the 11 with a known last wing, 8 stopped after wing 8 (the last wing before the steep jump), 1 after wing 9, 1 after wing 3 and 1 after wing 2. "
      f"An exact binomial test against a uniform one-in-eight chance gives p = {R['binomial_test_wing8_vs_uniform']['p_value']:.1e}. The cliff in Figure 4 and the cluster in Figure 6 line up, which is consistent with the 8&rarr;9 jump being where the difficulty step is. "
      "It does not prove it: guests who reach wing 9 may be more committed to finishing, and the Wall of Shame framing may make wing-8 quits more newsworthy.", B),
      Paragraph(f"By category, music accounts for {R['non_finishers_by_category']['Music']} of the 18 ({R['non_finisher_share_music_vs_music_in_catalogue']['among_non_finishers']*100:.0f}%) against "
      f"{R['non_finisher_share_music_vs_music_in_catalogue']['among_all_episodes']*100:.0f}% of the catalogue, but Fisher's exact test is inconclusive (OR = {R['fisher_music_vs_rest']['odds_ratio']}, p = {R['fisher_music_vs_rest']['p']:.2f}). "
      "By era, 12 of the documented tap-outs are from 2015&ndash;2018 and only 2 from 2023&ndash;2026. I would not read that as guests getting tougher: early quitters were widely written about as a novelty, and coverage "
      "of the later years is thinner.", B),
      fig("f6_non_finishers_by_wing.png", "Figure 6. Last wing eaten among documented non-finishers with a known stopping point.", 5.4)]

S += [Paragraph("4. Limitations", H1),
      Paragraph("&bull; <b>No completion labels.</b> The show does not publish who finished. A model predicting completion from guest traits would be fitting press attention, so I report counts and tests only.<br/>"
      "&bull; <b>No comparable view counts.</b> Per-episode views were not retrievable. A small snapshot table ships but is explicitly marked as not comparable; <font face='Courier'>fetch_views.py</font> and <font face='Courier'>views_model.py</font> are written for you to run with a YouTube API key. They are untested against real data; "
      "the model script was only smoke-tested on synthetic random numbers (which correctly returned near-zero effects).<br/>"
      "&bull; <b>Analyst-coded categories.</b> One label per guest; no inter-rater check.<br/>"
      "&bull; <b>Partial sauce data.</b> Seasons 22&ndash;28 have anchor points only; wing 10 is unpublished for some recent seasons.<br/>"
      "&bull; <b>Source fidelity.</b> Dates and counts were validated against Wikipedia season totals, but all inputs were collected from public web pages and not independently re-verified against the videos.", B)]

S += [Paragraph("5. Conclusion", H1),
      Paragraph("The show kept its format and changed its guests: weekly cadence, a ten-wing ladder whose difficulty is concentrated in the last three wings, and an invited list that has moved decisively toward actors. "
      "The most reliable fact about tapping out is where it happens: after Da Bomb. The natural next step is a proper views model, which needs only the scraped counts to be dropped into the pipeline.", B)]

S += [Paragraph("Data and code", H1),
      Paragraph("All CSVs, scripts, figures, the interactive dashboard and a README with a data dictionary accompany this paper. Reproduce with "
      "<font face='Courier'>python3 scripts/build_dataset.py &amp;&amp; python3 scripts/analysis.py</font>.", B),
      Paragraph("Sources", H1),
      Paragraph("Wikipedia, &ldquo;List of Hot Ones episodes&rdquo; and season overviews (retrieved 2026-11-22); Heatonist season sauce pages; hotsaucehell.wordpress.com sauce lineups; "
      "Ranker, Mashed, BuzzFeed, Dexerto, Uproxx and related press coverage of tap-outs (per-row sources in <font face='Courier'>documented_non_finishers.csv</font>).", SM)]

SimpleDocTemplate(str(ROOT / "paper/hot_ones_paper.pdf"), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                  title="Who Taps Out, What Gets Hotter, and Who Gets Asked", author="Nikhil Chandrashaker").build(S, onFirstPage=page, onLaterPages=page)
print("ok")
