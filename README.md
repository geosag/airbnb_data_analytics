# Airbnb Market Analytics

A data pipeline and Power BI dashboard for monitoring and analyzing the short-term rental market (Airbnb) performance in Athens, Greece. Listing and review data is extracted from the web, stored in Supabase, and visualized in a 3-page interactive dashboard.

📊 [**View the live dashboard**](https://app.powerbi.com/view?r=eyJrIjoiNWY4OTM4ODQtYzE4ZS00ZDQ1LWE5ZjgtMTIyNTQ0Y2M0Zjc4IiwidCI6IjIyMzk4NzFkLTBmNmItNDQ4NS04ZjIzLTM1NmE0MzJlYzNmYiJ9)

---

## Overview

The pipeline automates the fetching of the latest listings and reviews .csv files using Python (`requests`, `BeautifulSoup`, `pandas`). The data is cleaned, transformed, and loaded into a Supabase (PostgreSQL) database. A GitHub Actions workflow runs the script automatically, keeping the Power BI dashboard current with both macroeconomic market trends and granular, property-level pricing anomalies.

---

## Dashboard

**Page 1 - Market Overview**
*Macro Market Performance*

* **Global Filters:** Date, Neighbourhood, Room Type, and Host Tier slicers, plus a Reset button to clear all selections.
* **KPI Cards:** Estimated Market Revenue, Demand Velocity Index (total reviews as a proxy for booking volume), Average Daily Rate, and Market Compliance Ratio (% of active listings with a valid license). Each card includes period-over-period variance vs. the preceding 12-month baseline.
* **Geospatial Map:** Interactive map of Athens with dynamic bubble clustering (capped at the Top 1,000 listings by demand) to visualize property density and performance across neighbourhoods, with a grayscale basemap toggle.
* **Trend Analysis:** A 24-Month Demand Trend chart plotting monthly review volume against a trailing 12-month rolling average, to expose true market growth versus seasonal fluctuations (this visual is independent of the Date slicer).
* **Note:** Revenue and rate figures are modeled estimates derived from listing price, minimum stay requirements, and review activity — not confirmed booking transactions.

**Page 2 - Market Landscape & Acquisition Strategy**
*Market Landscape & Acquisition Strategy*

* **Top 10 Neighbourhoods (Pareto Chart):** Ranks neighbourhoods by total market share (review volume) with a cumulative percentage line to highlight where demand concentration falls off.
* **Acquisition Target Matrix (Bubble Chart):** Plots the Top 10 neighbourhoods by Price vs. Volume, with bubble size representing quality, to help identify high-value expansion targets.
* **Competitive Landscape (Treemap):** Visualizes the Top 10 host portfolios sized by total reviews, surfacing the most dominant multi-listing operators in the market.

**Page 3 - Risk & Compliance**
*Risk, Compliance & Market Integrity*

* **KPI Cards:** Regulatory Compliance (% of listings with an invalid or missing license, flagged for legal audit), Operational Decay (% of listings dormant/stagnant over the trailing 12 months, flagged for oversupply review), and Pricing Integrity (% of price outliers detected via IQR analysis, flagged for revenue model review).
* **Anomaly Detection Methodology:** Evaluates listing prices against mathematically derived upper/lower bounds using the Interquartile Range (IQR) method, tailored dynamically by room type.
* **Master Compliance & Outlier Audit Table:** Row-level drill-down listing Listing ID (linked to the live Airbnb page), Host Name, Price, Availability/365 (visualized as a bar, where a full bar = 12 months vacant), and License Status, with conditional icons flagging blank/zero-price errors, statistical pricing outliers, invalid/missing licenses, and manual exemption reviews.

---

## Data pipeline

### Source

Data is extracted using `requests` and `BeautifulSoup` to capture latest listings and reviews, which are then processed into structured dataframes using `pandas`.

### Supabase tables

The database consists of three tables: a listings metadata table, a review-level demand table linked by listing ID, and a single-row metadata table tracking the latest data refresh.

**`listings`** (Primary metadata and pricing table)

| Column | Type | Description |
|---|---|---|
| `id` | `BIGINT` | Unique Airbnb listing ID (Primary Key) |
| `host_id` | `TEXT` | Unique host identifier |
| `host_url` | `TEXT` | Link to the host's Airbnb profile |
| `host_name` | `TEXT` | Host's display name |
| `neighbourhood_cleansed` | `TEXT` | Standardized property location/district |
| `latitude` | `TEXT` | Property latitude |
| `longitude` | `TEXT` | Property longitude |
| `room_type` | `TEXT` | Entire home, private room, etc. |
| `minimum_nights` | `TEXT` | Minimum required stay length |
| `price` | `TEXT` | Nightly rate |
| `availability_365` | `TEXT` | Days available in the next year |
| `number_of_reviews` | `TEXT` | Total historical review count |
| `last_review` | `TEXT` | Date of most recent review |
| `review_scores_rating` | `TEXT` | Aggregate guest rating score |
| `license` | `TEXT` | Registration/license number |
| `calculated_host_listings_count` | `TEXT` | Number of listings managed by the host (used to derive Host Tier) |

**`reviews`** (Demand and historical volume table)

| Column | Type | Description |
|---|---|---|
| `listing_id` | `BIGINT` | Foreign Key mapping to `listings.id` |
| `date` | `DATE` | Date the review was left |

**`airbnb_data_latest_info`** (Data refresh metadata table)

| Column | Type | Description |
|---|---|---|
| `last_update` | `DATE` | Date of the most recent data load (Primary Key) |
| `row_number_listings` | `INTEGER` | Row count of the listings table as of last update |
| `row_number_reviews` | `INTEGER` | Row count of the reviews table as of last update |

### Automation

The pipeline runs on a scheduled basis via GitHub Actions (`.github/workflows/scheduler.yml`). Supabase connection credentials and database keys are securely stored as repository secrets.

---

## Project structure

```text
airbnb_data_analytics/
├── .github/
│   └── workflows/
│       └── scheduler.yml
├── supabase/
│   └── roles_permissions_policies.sql
│   └── select_queries.sql
│   └── tables_creation.sql
├── .gitignore
├── get_airbnb_data.py
├── requirements.txt
└── README.md

```

---

## Tech stack

* **Python** - Data extraction and pipeline (`BeautifulSoup`, `requests`, `pandas`)
* **Supabase (PostgreSQL)** - Relational data storage
* **GitHub Actions** - Scheduled automation
* **Power BI** - Dashboard, DAX modeling, and visualization

---

*Built by [Georgios Sagris*](https://www.linkedin.com/in/georgesagris/)
