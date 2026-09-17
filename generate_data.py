"""
Generate a synthetic (simulated) one-year hospital encounter dataset.
Patterns are modelled on published North-Indian tertiary care norms.
No real patient or hospital records are used.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(1947)

START = pd.Timestamp("2025-04-01")   # Indian financial year FY 2025-26
END = pd.Timestamp("2026-03-31")
days = pd.date_range(START, END, freq="D")

DEPTS = {
    # dept: (share of encounters, ip_rate, base_los, base_ip_bill, opd_bill)
    "Cardiology":            (0.135, 0.42, 4.6, 185000, 1400),
    "Orthopaedics":          (0.120, 0.38, 4.1, 132000, 1100),
    "General Medicine":      (0.165, 0.26, 3.4,  48000,  700),
    "Obstetrics & Gynae":    (0.105, 0.47, 3.0,  62000,   900),
    "Paediatrics":           (0.095, 0.30, 3.2,  41000,   650),
    "Oncology":              (0.062, 0.55, 5.2, 158000,  1600),
    "Nephrology":            (0.058, 0.44, 4.4,  96000,  1200),
    "Gastroenterology":      (0.060, 0.33, 3.6,  88000,  1150),
    "Neurology & Neurosurg": (0.055, 0.46, 6.1, 224000,  1500),
    "Pulmonology":           (0.050, 0.34, 4.0,  71000,   850),
    "ENT & Ophthalmology":   (0.055, 0.22, 1.8,  46000,   600),
    "Emergency & Trauma":    (0.040, 0.61, 3.8, 104000,  1000),
}

PAYERS = {
    "Ayushman Bharat / Sarbat Sehat": 0.29,
    "Private insurance (TPA)":        0.27,
    "Self-pay / cash":                0.31,
    "Corporate & CGHS/ECHS":          0.13,
}
PAYER_FACTOR = {  # realised revenue vs gross tariff
    "Ayushman Bharat / Sarbat Sehat": 0.62,
    "Private insurance (TPA)":        1.02,
    "Self-pay / cash":                0.94,
    "Corporate & CGHS/ECHS":          0.88,
}

CATCHMENT = {
    "Amritsar (urban)": 0.41, "Amritsar (rural)": 0.17, "Tarn Taran": 0.09,
    "Gurdaspur / Batala": 0.10, "Jalandhar / Kapurthala": 0.07,
    "Pathankot": 0.05, "Ferozepur / Fazilka": 0.04,
    "Jammu & HP": 0.04, "NRI / overseas": 0.03,
}

WARDS = {"General ward": 0.44, "Semi-private": 0.21, "Private room": 0.16,
         "ICU / HDU": 0.14, "Day-care": 0.05}

DIAG = {
    "Cardiology": ["Acute coronary syndrome", "Heart failure (CHF)", "Arrhythmia",
                   "Hypertensive crisis", "Angioplasty / PTCA"],
    "Orthopaedics": ["Fracture - lower limb", "Total knee replacement", "Lumbar disc disease",
                     "Road traffic injury", "Arthroscopy"],
    "General Medicine": ["Type 2 diabetes complication", "Enteric / viral fever", "Dengue",
                         "Anaemia workup", "Hypothyroidism"],
    "Obstetrics & Gynae": ["LSCS delivery", "Normal delivery", "Hysterectomy",
                           "Antenatal complication", "Fibroid / menorrhagia"],
    "Paediatrics": ["Bronchiolitis", "Neonatal jaundice", "Acute gastroenteritis",
                    "Febrile seizure", "Pneumonia (paediatric)"],
    "Oncology": ["Breast carcinoma", "Chemotherapy cycle", "Head & neck carcinoma",
                 "Haematologic malignancy", "Colorectal carcinoma"],
    "Nephrology": ["Maintenance haemodialysis", "Acute kidney injury", "CKD stage 4-5",
                   "Renal calculi", "Nephrotic syndrome"],
    "Gastroenterology": ["Acute pancreatitis", "Chronic liver disease", "Upper GI bleed",
                         "Gallstone disease", "Endoscopy / colonoscopy"],
    "Neurology & Neurosurg": ["Ischaemic stroke", "Head injury", "Epilepsy",
                              "Intracranial haemorrhage", "Spine surgery"],
    "Pulmonology": ["COPD exacerbation", "Asthma", "Pneumonia", "Tuberculosis", "Sleep apnoea"],
    "ENT & Ophthalmology": ["Cataract surgery", "Chronic otitis media", "Tonsillectomy",
                            "Nasal polyp / FESS", "Diabetic retinopathy"],
    "Emergency & Trauma": ["Polytrauma", "Poisoning", "Acute abdomen",
                           "Snake / dog bite", "Cardiac arrest"],
}

# procedures can only be coded against an admission / day-care episode, never an OPD consult
PROCEDURES = {
    "Angioplasty / PTCA", "Total knee replacement", "Arthroscopy", "LSCS delivery",
    "Normal delivery", "Hysterectomy", "Chemotherapy cycle", "Maintenance haemodialysis",
    "Endoscopy / colonoscopy", "Spine surgery", "Cataract surgery", "Tonsillectomy",
    "Nasal polyp / FESS", "Polytrauma", "Cardiac arrest",
}
OPD_DIAG = {d: [x for x in v if x not in PROCEDURES] for d, v in DIAG.items()}

dept_names = list(DEPTS)
dept_p = np.array([DEPTS[d][0] for d in dept_names]); dept_p = dept_p / dept_p.sum()


def day_multiplier(ts):
    m, dow, doy = ts.month, ts.dayofweek, ts.dayofyear
    seasonal = 1.0
    if m in (7, 8, 9):      seasonal = 1.18   # monsoon: dengue, GI, respiratory
    elif m in (12, 1):      seasonal = 1.14   # winter: cardiac, COPD, smog
    elif m in (5, 6):       seasonal = 0.93   # peak summer lull
    weekly = {0: 1.18, 1: 1.07, 2: 1.03, 3: 1.02, 4: 1.00, 5: 0.92, 6: 0.64}[dow]
    growth = 1 + 0.10 * (doy / 365.0)          # slow YoY growth through the year
    holidays = {(11, 5): 0.55, (10, 20): 0.6, (8, 15): 0.7, (1, 26): 0.7, (3, 14): 0.75}
    hol = holidays.get((ts.month, ts.day), 1.0)
    return seasonal * weekly * growth * hol


rows = []
eid = 100000
for ts in days:
    n = rng.poisson(238 * day_multiplier(ts))
    depts = rng.choice(dept_names, size=n, p=dept_p)
    for d in depts:
        eid += 1
        share, ip_rate, base_los, base_ip, opd_bill = DEPTS[d]
        ip_adj = ip_rate * 0.33 * (1.25 if ts.month in (7, 8, 9, 12, 1) else 1.0)
        is_ip = rng.random() < min(ip_adj, 0.85)

        if d == "Paediatrics":
            age = int(np.clip(rng.gamma(1.6, 4.5), 0, 17))
        elif d == "Obstetrics & Gynae":
            age = int(np.clip(rng.normal(28, 6), 16, 52))
        elif d in ("Cardiology", "Oncology", "Nephrology"):
            age = int(np.clip(rng.normal(58, 13), 19, 94))
        else:
            age = int(np.clip(rng.normal(44, 18), 1, 92))

        if d == "Obstetrics & Gynae":
            gender = "Female"
        else:
            gender = rng.choice(["Male", "Female"], p=[0.54, 0.46])

        payer = rng.choice(list(PAYERS), p=list(PAYERS.values()))
        district = rng.choice(list(CATCHMENT), p=list(CATCHMENT.values()))

        if is_ip:
            los = int(np.clip(round(rng.gamma(2.2, base_los / 2.2)), 1, 42))
            ward = rng.choice(list(WARDS), p=list(WARDS.values()))
            if d == "Emergency & Trauma" and rng.random() < 0.45:
                ward = "ICU / HDU"
            ward_mult = {"General ward": 0.82, "Semi-private": 1.0, "Private room": 1.28,
                         "ICU / HDU": 1.95, "Day-care": 0.5}[ward]
            gross = base_ip * ward_mult * (0.55 + 0.18 * los) / 1.9
            gross *= rng.lognormal(0, 0.28)
            revenue = gross * PAYER_FACTOR[payer]
            outcome = rng.choice(["Discharged", "Discharged", "Discharged", "Discharged",
                                  "Referred / LAMA", "Death"],
                                 p=[0.30, 0.30, 0.20, 0.157, 0.028, 0.015])
            if d in ("Emergency & Trauma", "Oncology", "Neurology & Neurosurg") and outcome == "Death":
                pass
            elif outcome == "Death" and rng.random() < 0.55:
                outcome = "Discharged"
            readmit = rng.random() < (0.11 if d in ("Nephrology", "Pulmonology", "Cardiology") else 0.055)
        else:
            los, ward = 0, "OPD"
            revenue = opd_bill * rng.lognormal(0, 0.45) * PAYER_FACTOR[payer]
            outcome = "OPD consult"
            readmit = False

        wait = int(np.clip(rng.gamma(2.0, 11 if ts.dayofweek == 0 else 8), 3, 150))
        sat = float(np.clip(rng.normal(4.25 - wait / 160, 0.55), 1, 5))

        rows.append((
            f"AMR{eid}", ts.date().isoformat(), d, "IP" if is_ip else "OPD",
            age, gender, district, payer, ward, los,
            rng.choice(DIAG[d] if is_ip else OPD_DIAG[d]), outcome,
            int(round(revenue)), wait, round(sat, 1),
            "Yes" if readmit else "No",
        ))

cols = ["encounter_id", "date", "department", "encounter_type", "age", "gender",
        "district", "payer", "ward_type", "length_of_stay_days", "primary_diagnosis",
        "outcome", "net_revenue_inr", "wait_time_min", "satisfaction_score", "readmit_30d"]
df = pd.DataFrame(rows, columns=cols)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
df.to_csv("/home/claude/apollo_amritsar_synthetic_encounters_FY2025_26.csv", index=False)

print(df.shape)
print(df.head())
print("\nIP share:", (df.encounter_type == "IP").mean().round(3))
print("ALOS:", df.loc[df.encounter_type == "IP", "length_of_stay_days"].mean().round(2))
print("Revenue (Cr):", (df.net_revenue_inr.sum() / 1e7).round(2))
print("Bed-days:", df.length_of_stay_days.sum())
