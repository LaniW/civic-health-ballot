# 🗳️ Civic Health Alliance: Official Health Ballot

<img width="1317" height="836" alt="image" src="https://github.com/user-attachments/assets/ade2bb28-4449-4207-940b-81cf9cdf7480" />

An interactive, ballot-style web experience exploring the critical intersection of civic participation and healthcare outcomes in the United States. 

This project visualizes how voter turnout correlates with life expectancy and uninsured rates, taking the user on a journey from national state-level trends down to local New York City neighborhoods, and finally grounding the data in real human stories.

## About the Project

*“Civic engagement isn't abstract. It is the mechanism by which need becomes law, and law becomes care, and care becomes survival.”*

This visual investigation demonstrates that states and neighborhoods where residents vote more frequently tend to have lower uninsured rates and higher life expectancies. The experience is designed to mimic an official election ballot ([inspired by MIT Election Lab best practices](https://electionlab.mit.edu/research/ballot-design)) to emphasize that health policy is shaped directly at the ballot box.

## Key Features & Walkthrough

### 1. The National Picture (US Map)
<img width="1688" height="870" alt="image" src="https://github.com/user-attachments/assets/6e87099f-0647-4687-b7f2-375602bcc531" />

* Interactive hexagonal tile grid of the United States, laid out per NPR's convention (see Data Sources below).
* Displays 2020 voter turnout, uninsured rates, and life expectancy for each state.
* Highlights the correlation between high civic engagement and stronger health metrics.

### 2. The Local Picture (NYC Map)
<img width="1412" height="1293" alt="image" src="https://github.com/user-attachments/assets/74d251e8-90b0-4fd2-beb9-d5223c92a957" />

* Brings the national data down to a granular, local level using New York City neighborhoods.
* Shows the stark life expectancy gaps (e.g., the 12-year gap between adjacent neighborhoods) and how they map to local voter turnout.

### 3. Legislative Measures (Patient Stories)
<img width="1292" height="1091" alt="image" src="https://github.com/user-attachments/assets/fa839a12-0f13-4502-9156-8195c7314683" />

* Grounds the statistical data in real human experiences.
* Features interactive patient records documenting how civic failures (like Medicaid benefit limits or state-level housing policies) result in direct, often fatal, health outcomes.

## Data Sources

The data driving this visualization is sourced from official public health and electoral databases:

**National Data:**
* **Voter Turnout:** [UF Election Lab](https://election.lab.ufl.edu/voter-turnout/2020-general-election-turnout/), 2020 Voting-Eligible Population (VEP)
* **Uninsured Rates:** [Kaiser Family Foundation (KFF)](https://www.kff.org/state-health-policy-data/state-indicator/total-population/?currentTimeframe=0&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D) ACS estimates, 2022-2023
* **Life Expectancy:** [CDC National Vital Statistics Reports](https://www.cdc.gov/nchs/data/nvsr/nvsr74/nvsr74-12.pdf), Vol. 74 No. 12, 2022

**New York City Data:**
* **Voter Turnout:** [NYC Campaign Finance Board (CFB) Community Profiles](https://www.nyccfb.info/nyc-votes/community-profiles/), 2020
* **Life Expectancy:** [NYC DOHMH Community Health Profiles](https://a816-health.nyc.gov/hdi/profiles/), 2021 (2010-2019 average)

**Map Layout:**
* US state tile grid: hexagonal layout from [Danny DeBelius & Alyson Hurt, "Let's Tesselate: Hexagons for Tile Grid Maps"](https://blog.apps.npr.org/2015/05/11/hex-tile-maps.html) (NPR Visuals, May 2015). Per-state coordinates transcribed from the [`tilemapr`](https://github.com/EmilHvitfeldt/tilemapr) R package.

## Technologies Used

* **HTML5** (Semantic structure)
* **CSS3** (Custom properties, grid/flexbox layouts, CSS animations, 3D transforms for ballot flipping)
* **Vanilla JavaScript** (DOM manipulation, state management, SVG generation)
* **SVG** (Scalable Vector Graphics for the tile maps)

## Running the Project Locally

There is no build step and no npm install. The site is plain HTML/CSS/JS that loads its datasets from `data/*.json` at startup.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/civic-health-ballot.git
   cd civic-health-ballot
   ```

2. Serve the directory (any static server works):
   ```bash
   python3 -m http.server 8000
   ```

3. Open <http://localhost:8000/> in a browser.

Note: opening `index.html` directly via `file://` will fail because browsers block `fetch()` on file URLs. The page shows an in-app banner with these instructions if that happens.

### Refreshing the state dataset

The US state numbers can be regenerated from their upstream sources:

```bash
python3 scripts/build-data.py
```

This fetches the UF Election Lab turnout CSV and the Census ACS uninsured-rate API, merges them with the committed CDC life-expectancy extract in `data/raw/`, and writes `data/states.json` + `data/sources.json`. Python stdlib only — no dependencies to install.

NYC neighborhood data (`data/nyc.json`) and patient stories (`data/stories.json`) are hand-curated and are not touched by the script.
