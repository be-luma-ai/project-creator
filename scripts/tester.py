import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import pandas as pd
from utilities.logger_setup import setup_logger
from utilities.load_credentials import load_meta_access_token, load_clients_config
from utilities.run_config import get_run_config
from utilities.run_for_client import run_for_client

logger = setup_logger("test_runner")

def choose_client(clients):
    print("\n📌 Available Clients:")
    for idx, c in enumerate(clients):
        print(f"{idx + 1}. {c['slug']}")
    selected = int(input("👉 Select client number: ")) - 1
    return clients[selected]

def build_flags():
    print("\n📦 Toggle which datasets to extract (Y/n):")
    flags = {}
    modules = [
        "account_performance", "campaign_performance", "adset_performance", "ad_performance",
        "account_recommendations", "adset_recommendations", "ad_recommendations",
        "accounts", "campaigns", "adsets", "ads", "ad_creatives", "activities"
    ]
    for mod in modules:
        choice = input(f"  - {mod.replace('_', ' ').title()}? (Y/n): ").strip().lower()
        flags[mod] = (choice != 'n')
    return flags

def show_menu(result: dict):
    df_keys = [k for k, v in result.items() if isinstance(v, pd.DataFrame)]

    if not df_keys:
        print("⚠️ No DataFrames to show.")
        return

    while True:
        print("\n📊 Available DataFrames:")
        for idx, key in enumerate(df_keys):
            rows = len(result[key])
            print(f"{idx + 1}. {key} ({rows} rows)")
        print("0. Exit viewer")
        print("99. 💾 Save all DataFrames as CSV")

        try:
            selection = int(input("🔍 Select option: "))
            if selection == 0:
                break
            elif selection == 99:
                for key in df_keys:
                    result[key].to_csv(f"{key}.csv", index=False)
                print("✅ All DataFrames saved as CSV.")
            else:
                selected_key = df_keys[selection - 1]
                print(f"\n🧾 Preview of '{selected_key}':")
                print(result[selected_key].head(10))
        except Exception as e:
            print(f"❌ Invalid selection: {e}")

def main():
    access_token = load_meta_access_token()
    clients = load_clients_config()
    run_config = get_run_config()

    client = choose_client(clients)
    data_flags = build_flags()

    print("\n🚀 Running data extraction...")
    try:
        result = run_for_client(client, access_token, run_config, data_flags)
        print(f"\n✅ Data extraction completed. Keys returned: {list(result.keys())}")
        show_menu(result)
    except Exception as e:
        logger.error(f"❌ Error in extraction: {e}", exc_info=True)

if __name__ == "__main__":
    main()