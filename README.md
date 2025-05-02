# meta-ads-pipeline

A modular and extensible data pipeline for extracting, transforming, and loading Meta Ads (Facebook Ads) data into Google BigQuery.

🚀 Overview
This project automates the daily extraction of performance data, recommendations, and account structures from the Meta Ads API. The data is stored in BigQuery for further analysis, visualization, or AI-driven insights.

🧱 Tech Stack
Python 3.10+
Meta Ads API (Facebook Graph API)
Google Cloud Platform
BigQuery
Cloud Run (optional for deployment)
OpenAI API (optional, for AI Agents)
Logging via logging module
📁 Project Structure

```text
meta-ads/
├── clients/                  # Client-specific config
├── credentials/              # Global credentials (ignored via .gitignore)
│   ├── service_accounts/
│   └── meta_ads/
├── scripts/                  # Entrypoint scripts
│   ├── main.py               # FastAPI server for Cloud Run
│   ├── run_pipeline.py       # Wraps the pipeline
│   └── meta_ads_main.py      # Actual pipeline logic
├── utilities/                # Shared utility modules
│   ├── logger_setup.py
│   ├── load_credentials.py
│   ├── run_config.py
│   ├── run_for_client.py
│   └── bigquery_uploader.py
├── modules/                  # ETL modules
│   ├── settings/             # Ad accounts, campaigns, ad sets, creatives
│   ├── performance/
│   │   ├── main/             # Campaign performance
│   │   └── breakdowns/
│   ├── recommendations/
│   └── change_history/       # (future)
├── tests/                    # pytest-compatible unit tests
├── requirements.txt
└── README.md
```

⚙️ How It Works
1.Client Configuration\*\*
Define clients in configs/clients.json: [ { "slug": "GAMA", "business_id": "1234567890", "service_account": "path/to/creds.json" } ]

2. \*_Run Confign_
   Dates are generated dynamically via get_run_config().

{ "since_date": "2025-03-21", "yesterday": "2025-03-25", ... }

3. Pipeline Execution
   The main script runs the pipeline for each client: python scripts/meta_ads_main.py

Each step extracts: • Ad accounts • Campaigns / Ad Sets / Ads • Recommendations (account, adset, ad) • Performance (daily insights) • Performance by breakdowns (daily insights) • Change history (optional)

🐛 Logging

All logs are stored in meta_ads_pipeline.log and printed to the terminal:

2025-03-26 18:24:25 - INFO - meta_ads_pipeline - ✅ Client GAMA processed successfully.

🧪 Testing

You can run a test client using:

python scripts/meta_ads_main.py --client TEST

Unit testing not implemented yet – recommended libraries: • pytest • unittest.mock for mocking Meta API calls

⸻

📦 Deployment Suggestions

You can deploy this project to: • Cloud Run + Scheduler (daily execution) • Cloud Composer (managed Airflow) • Docker + cron + GCP SA

⸻

📄 License

MIT License. © 2025 be-luma.com

⸻

✨ Contact

For support or questions:
📬 mateo@be-luma.com
🌐 https://be-luma.com
