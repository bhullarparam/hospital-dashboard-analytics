# Hospital Operations Review — Amritsar, FY 2025-26

An end-to-end healthcare analytics project: a synthetic one-year encounter dataset for a 190-bed
multi-specialty tertiary hospital in Amritsar, Punjab, and an interactive operations dashboard
built on top of it.

👉 [**View the interactive dashboard**](https://bhullarparam.github.io/hospital-dashboard-analytics)
> **All data in this project is simulated.** It was generated in Python to mirror the seasonality,
> payer mix, case profile and tariff structure typical of a private tertiary hospital in Punjab.
> No real patient records or hospital financials were used, and nothing here represents the actual
> performance of any named institution.

---

## What the project answers

Hospital management dashboards usually get built to answer four questions at once, and they pull in
different directions. This one is structured around that tension:

1. **Where does the workload sit?** — footfall, admissions and bed-days by specialty
2. **Where does the money actually come from?** — net revenue after scheme rates and TPA deductions
3. **Is capacity holding?** — monthly bed occupancy against a fixed 190-bed count
4. **Is care quality drifting?** — ALOS, 30-day readmissions, inpatient mortality, wait times

## Headline results

| Metric | FY 2025-26 |
|---|---|
| Total encounters | 94,122 |
| Inpatient admissions | 13,173 (14.0%) |
| Net revenue | ₹111 Cr |
| Average length of stay | 4.08 days |
| Bed occupancy | 77.2% |
| 30-day readmissions | 7.0% |
| Inpatient mortality | 0.88% |
| Mean OPD wait | 16.6 minutes |

## Findings

- **Revenue concentrates faster than volume.** Cardiology produces ~23% of net revenue from ~13% of
  encounters; General Medicine carries the largest footfall. Capacity planning and margin planning
  point at different departments.
- **Scheme patients fill beds but don't fund them.** Roughly 29% of encounters arrive through
  Ayushman Bharat / Sarbat Sehat, realising about two-thirds of the private-insurance rate per case.
- **Occupancy swings ~25 points across the year**, peaking in the monsoon months rather than winter —
  a staffing-roster problem before it is a bed problem.
- **A third of patients travel in from outside Amritsar district** (Gurdaspur, Tarn Taran, Pathankot,
  the Jammu belt), so referral relationships move volume more than local marketing does.
- **Readmissions cluster in nephrology, pulmonology and cardiology**, at roughly double the rate of
  surgical specialties.

## Dataset

`apollo_amritsar_synthetic_encounters_FY2025_26.csv` — 94,122 rows × 16 columns, one row per
encounter.

| Column | Description |
|---|---|
| `encounter_id` | Unique encounter reference |
| `date` | Encounter date (1 Apr 2025 – 31 Mar 2026) |
| `department` | One of 12 specialties |
| `encounter_type` | `OPD` or `IP` |
| `age`, `gender` | Patient demographics |
| `district` | Home district / catchment area |
| `payer` | Ayushman Bharat–Sarbat Sehat, private insurance (TPA), self-pay, corporate/CGHS-ECHS |
| `ward_type` | General, semi-private, private, ICU/HDU, day-care, OPD |
| `length_of_stay_days` | 0 for outpatients |
| `primary_diagnosis` | Presenting condition or procedure (procedures coded to admissions only) |
| `outcome` | Discharged, referred/LAMA, death, OPD consult |
| `net_revenue_inr` | Realised revenue after payer-specific deductions |
| `wait_time_min`, `satisfaction_score` | Experience measures |
| `readmit_30d` | Unplanned readmission within 30 days |

### How the data was generated

`generate_data.py` builds the dataset with:

- **Seasonality** — monsoon (Jul–Sep) and winter (Dec–Jan) surges, a summer lull, weekday/Sunday
  effects, and dips on major festival dates
- **Specialty-specific clinical profiles** — age distributions, admission rates, gamma-distributed
  length of stay, and an appropriate diagnosis vocabulary per department
- **Payer economics** — gross tariffs scaled by ward class and length of stay, then multiplied by a
  payer-specific realisation factor
- **Quality signals** — readmission risk weighted towards chronic-care specialties, and satisfaction
  modelled as a function of waiting time

`build_cube.py` aggregates 94k rows into a ~180 KB pre-computed cube (month × department time series,
department × quarter × dimension facts, and per-department daily series) so the dashboard filters
instantly in the browser without shipping the raw file.

## Dashboard

A single self-contained HTML file. Every chart is hand-built SVG — no charting library, no build
step, no dependencies.

- 365-day patient-flow trace with a 7-day rolling mean and peak annotation
- Eight operational KPIs that recompute against the active filter
- Monthly volume-and-revenue combination chart
- Bed capacity absorbed per month, with a 92% "elective scheduling breaks" threshold
- Specialty, payer, length-of-stay, diagnosis, age, catchment and weekday breakdowns
- Filters by specialty and by quarter; findings text rewrites itself to match
- Responsive, keyboard-accessible, light/dark aware, respects reduced-motion

## Stack

Python · pandas · NumPy · JavaScript · SVG

## Files

```
generate_data.py                                    synthetic data generator
build_cube.py                                       aggregation into the dashboard cube
apollo_amritsar_synthetic_encounters_FY2025_26.csv  the dataset (94,122 rows)
apollo-amritsar-hospital-dashboard.html             the dashboard
```

## Reproduce

```bash
pip install pandas numpy
python generate_data.py     # writes the CSV
python build_cube.py        # writes dashboard_data.json
```

The generator is seeded (`rng = np.random.default_rng(1947)`), so the output is identical on
every run.

