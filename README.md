# HSLU.MSCDAI_CD01.TeamProject

Group project for the module Customer Data Analytics (HSLU, HS26) on the YAPEAL card data.
Stakeholder: YAPEAL. Topic: share of wallet turned around, how much of the customer's financial wallet stays at YAPEAL ("wallet leakage") and what that means for churn. The work is tracked in the GitHub issues, one issue per deliverable.

## Setup

### 1. Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .CDA
source .CDA/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .CDA
.CDA\Scripts\Activate.ps1
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Strip notebook outputs on commit

The data is under NDA. `.gitattributes` declares the `nbstripout` filter for every notebook, each team member activates it once per clone:

```bash
nbstripout --install
```

After that, `git commit` removes all cell outputs automatically. Run all cells locally when you want to see them.

### 4. Put the data in place

Copy the five CSV files into `data/raw/` (the whole `data/` folder is gitignored):

```
data/raw/customer_data.csv
data/raw/customer_data_labels.csv
data/raw/customer_data_predict.csv
data/raw/sow_category.csv
data/raw/sow_category_counterpart.csv
```

Then run the cleaning script once, it writes the cleaned copies to `data/processed/`:

```bash
python src/clean_data.py
```

### 5. Deactivating

```bash
deactivate
```

## Project structure

```
.
├── data/
│   ├── raw/                # original CSVs, never edited, gitignored
│   └── processed/          # output of src/clean_data.py, gitignored
├── doc/                    # course briefs (PDF)
├── docs/                   # our written deliverables (research questions, findings, recommendations)
├── example_code/           # starter notebook provided by the course
├── notebooks/
│   ├── 00_ideation.ipynb   # first look at the data and the wallet-leakage case
│   └── 02_eda_first_look.ipynb
├── src/
│   └── clean_data.py       # cleans data/raw -> data/processed
├── dashboard/              # Streamlit app (issue 12)
├── figures/                # exported charts for the presentation
├── results/                # model outputs with customer ids, gitignored
├── tests/
└── requirements.txt
```

Notebooks live in `notebooks/` and resolve the repo root themselves, so they run from the root or from `notebooks/`. Anything with customer ids (`data/`, `results/`, `*.parquet`) stays out of git.

## Workflow

- one branch per issue, named `<issue-number>-<short-name>` (e.g. `01-data-prep`), merged into `main` via pull request
- small commits that each do one thing
- no raw rows, customer ids or data files in commits, slides or screenshots

## Deadlines

| Date | What |
|---|---|
| 25.09 | stakeholder and premise confirmed with the coaches |
| 09.10 | coaching session, book the presentation slot |
| 14.10 | submission on ILIAS: slides, notebooks, churn prediction file, dashboard screenshots |
| 16.10 / 23.10 | final presentations, presence on both days required |
