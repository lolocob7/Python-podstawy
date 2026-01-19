import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib.request
import datetime
import json as js
import ssl
import yfinance as yf

selected_securities = [
    {"nazwa": "AUTOPARTN", "symbol": "APR.WA"},
    {"nazwa": "ASMGROUP", "symbol": "ASM.WA"},
    {"nazwa": "RENDER", "symbol": "RND.WA"},
    {"nazwa": "XTPL", "symbol": "XTP.WA"},
]


end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5 * 365)


def fetch_nbp_period(url_template, start_date, end_date):
    data_list = []
    current_start = start_date

    context = ssl._create_unverified_context()

    while current_start < end_date:
        current_end = current_start + datetime.timedelta(days=365)
        if current_end > end_date:
            current_end = end_date

        url = url_template.format(
            start_date=current_start.isoformat(), end_date=current_end.isoformat()
        )

        try:
            with urllib.request.urlopen(url, context=context) as response:
                res = response.read().decode("utf-8")
                chunk = js.loads(res)

                if isinstance(chunk, dict) and "rates" in chunk:
                    data_list.extend(chunk["rates"])
                elif isinstance(chunk, list):
                    data_list.extend(chunk)

        except urllib.error.HTTPError as e:
            print(
                f"Warning: Could not fetch data for {current_start} - {current_end}: {e}"
            )

        current_start = current_end + datetime.timedelta(days=1)

    return data_list


def get_usd_history(start_date, end_date):
    print("Fetching USD data...")
    url_usd_template = "https://api.nbp.pl/api/exchangerates/rates/A/USD/{start_date}/{end_date}/?format=json"
    usd_history = fetch_nbp_period(url_usd_template, start_date, end_date)
    return usd_history


def get_gold_history(start_date, end_date):
    print("Fetching Gold data...")
    url_gold_template = (
        "https://api.nbp.pl/api/cenyzlota/{start_date}/{end_date}/?format=json"
    )
    gold_history = fetch_nbp_period(url_gold_template, start_date, end_date)
    return gold_history


usd_history = get_usd_history(start_date, end_date)
gold_history = get_gold_history(start_date, end_date)

with open("nbp_data_usd.json", "w", encoding="utf-8") as f:
    js.dump(usd_history, f, ensure_ascii=False, indent=4)
with open("nbp_data_gold.json", "w", encoding="utf-8") as f:
    js.dump(gold_history, f, ensure_ascii=False, indent=4)


def get_securities_data(selected_securities, start_date, end_date):
    for papier in selected_securities:
        ticker = papier["symbol"]

        df = yf.download(ticker, start=str(start_date), end=str(end_date))
        df.reset_index(inplace=True)
        df.rename(columns={"index": "daty"}, inplace=True)

        # zapis JSON
        df.to_json(
            f"{ticker.replace('.WA','')}.json",
            orient="records",
            date_format="iso",
            force_ascii=False,
        )


# --- Read all selected papers ---
data = pd.DataFrame({})

# --- Print conversions ---
for item in data:
    price_usd = item["close"] / usd_price
    price_gold = item["close"] / gold_price

    print(f"{item['code']} ({item['date']})")
    print(f"PLN: {item['close']:.4f}")
    print(f"USD: {price_usd:.4f}")
    print(f"Złoto (g): {price_gold:.6f}")
    print("-" * 30)

# --- Prepare chart data ---
codes = [item["code"] for item in data]
prices_pln = [item["close"] for item in data]
prices_usd = [item["close"] / usd_price for item in data]
prices_gold = [item["close"] / gold_price for item in data]

# --- Chart 1: PLN ---
plt.figure()
plt.bar(codes, prices_pln)
plt.title("Ceny akcji (PLN)")
plt.xlabel("Papier wartościowy")
plt.ylabel("Cena [PLN]")
plt.grid(axis="y")
plt.show()

# --- Chart 2: USD ---
plt.figure()
plt.bar(codes, prices_usd)
plt.title("Ceny akcji (USD)")
plt.xlabel("Papier wartościowy")
plt.ylabel("Cena [USD]")
plt.grid(axis="y")
plt.show()

# --- Chart 3: Gold (grams) ---
plt.figure()
plt.bar(codes, prices_gold)
plt.title("Ceny akcji (w gramach złota)")
plt.xlabel("Papier wartościowy")
plt.ylabel("Złoto [g]")
plt.grid(axis="y")
plt.show()

# --- Optional: One combined comparison chart ---
x = np.arange(len(codes))
width = 0.25

plt.figure()
plt.bar(x - width, prices_pln, width, label="PLN")
plt.bar(x, prices_usd, width, label="USD")
plt.bar(x + width, prices_gold, width, label="Złoto (g)")
plt.xticks(x, codes)
plt.xlabel("Papier wartościowy")
plt.ylabel("Wartość")
plt.title("Porównanie cen akcji (PLN / USD / złoto)")
plt.legend()
plt.grid(axis="y")
plt.show()
