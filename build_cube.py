import json
import numpy as np
import pandas as pd

BEDS = 190
df = pd.read_csv("/home/claude/apollo_amritsar_synthetic_encounters_FY2025_26.csv", parse_dates=["date"])

months = pd.date_range("2025-04-01", "2026-03-01", freq="MS")
mindex = {m.strftime("%Y-%m"): i for i, m in enumerate(months)}
df["ym"] = df.date.dt.strftime("%Y-%m")
df["mi"] = df.ym.map(mindex)
df["q"] = df.mi // 3            # 0 = Q1 (Apr-Jun) ... 3 = Q4 (Jan-Mar)
df["is_ip"] = (df.encounter_type == "IP").astype(int)

# ---------- time series cube: month x department ----------
ts = (df.groupby(["mi", "department"])
        .apply(lambda g: pd.Series({
            "opd": int((g.encounter_type == "OPD").sum()),
            "ip": int(g.is_ip.sum()),
            "rev": int(g.net_revenue_inr.sum()),
            "iprev": int(g.loc[g.is_ip == 1, "net_revenue_inr"].sum()),
            "bd": int(g.length_of_stay_days.sum()),
            "re": int(((g.readmit_30d == "Yes") & (g.is_ip == 1)).sum()),
            "dth": int((g.outcome == "Death").sum()),
            "lama": int((g.outcome == "Referred / LAMA").sum()),
            "sat": float(g.satisfaction_score.sum()),
            "wt": int(g.wait_time_min.sum()),
            "n": int(len(g)),
        }), include_groups=False)
        .reset_index())
ts_rec = [[int(r.mi), r.department, int(r.opd), int(r.ip), int(r.rev), int(r.bd),
           int(r.re), int(r.dth), int(r.lama), round(float(r.sat), 1), int(r.wt), int(r.n),
           int(r.iprev)]
          for r in ts.itertuples()]

# ---------- categorical cube: dept x quarter x dimension ----------
df["age_band"] = pd.cut(df.age, [-1, 12, 25, 40, 55, 70, 200],
                        labels=["0-12", "13-25", "26-40", "41-55", "56-70", "70+"]).astype(str)
df["los_band"] = pd.cut(df.length_of_stay_days, [-1, 0, 1, 3, 5, 7, 10, 100],
                        labels=["OPD", "1 day", "2-3 days", "4-5 days", "6-7 days",
                                "8-10 days", "10+ days"]).astype(str)
df["dow"] = df.date.dt.day_name().str.slice(0, 3)

cube = []
for dim in ["payer", "ward_type", "district", "primary_diagnosis", "age_band",
            "los_band", "dow", "outcome", "gender"]:
    g = df.groupby(["department", "q", dim], observed=True).agg(
        n=("encounter_id", "size"), ip=("is_ip", "sum"), rev=("net_revenue_inr", "sum"),
        bd=("length_of_stay_days", "sum")).reset_index()
    for r in g.itertuples():
        cube.append([dim, r.department, int(r.q), str(getattr(r, dim)),
                     int(r.n), int(r.ip), int(r.rev), int(r.bd)])

# ---------- daily series for the hero chart (per department) ----------
all_days = pd.date_range("2025-04-01", "2026-03-31", freq="D")
daily_dept = {}
for dept, g in df.groupby("department"):
    d = g.groupby(g.date.dt.normalize()).agg(n=("encounter_id", "size"),
                                             ip=("is_ip", "sum")).reindex(all_days, fill_value=0)
    daily_dept[dept] = {"n": [int(x) for x in d.n], "ip": [int(x) for x in d.ip]}
daily_dates = [d.strftime("%Y-%m-%d") for d in all_days]

out = {
    "meta": {
        "beds": BEDS,
        "period": "FY 2025-26 (1 Apr 2025 - 31 Mar 2026)",
        "months": [m.strftime("%b %y") for m in months],
        "rows": int(len(df)),
        "departments": sorted(df.department.unique().tolist()),
    },
    "ts": ts_rec,
    "cube": cube,
    "dailyDates": daily_dates,
    "dailyDept": daily_dept,
}
with open("/home/claude/dashboard_data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))

ip = df[df.is_ip == 1]
print("rows", len(df), "| ts", len(ts_rec), "| cube", len(cube))
print("occupancy %", round(df.length_of_stay_days.sum() / (BEDS * 365) * 100, 1))
print("ALOS", round(ip.length_of_stay_days.mean(), 2))
print("rev Cr", round(df.net_revenue_inr.sum() / 1e7, 1))
print("readmit %", round((ip.readmit_30d == "Yes").mean() * 100, 2))
print("mortality %", round((ip.outcome == "Death").mean() * 100, 2))
print("sat", round(df.satisfaction_score.mean(), 2), "| wait", round(df.wait_time_min.mean(), 1))
import os; print("json KB", round(os.path.getsize("/home/claude/dashboard_data.json")/1024, 1))
