import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib.request
import datetime
import json as js
import ssl

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5 * 365)
daty_full = pd.date_range(start=start_date, end=end_date, freq="D")

stock_files = [
    {"nazwa": "EUCO/20", "symbol": "EUC"},
    {"nazwa": "CDPROJECT", "symbol": "CDR"},
    {"nazwa": "PURE", "symbol": "PUR"},
]

stock_prices = {}
print("Wczytuję Twoje pliki CSV...")

for info in stock_files:
    nazwa = info["nazwa"]
    symbol = info["symbol"]
    plik = f"{symbol}.csv"

    if not os.path.exists(plik):
        print(
            f"BŁĄD: Nie ma pliku {plik}. Upewnij się, że jest w tym samym folderze co skrypt!"
        )
        continue

    try:
        df = pd.read_csv(plik)
        date_col = "Data"
        price_col = "Zamkniecie"

        df["daty"] = pd.to_datetime(df[date_col], format="%Y-%m-%d")
        df.set_index("daty", inplace=True)

        df_clean = pd.DataFrame()
        df_clean["Close"] = df[price_col]

        df_clean = df_clean.sort_index()

        df_clean = df_clean.reindex(daty_full)
        df_clean["Close"] = (
            df_clean["Close"].interpolate(method="linear").ffill().bfill()
        )

        df_clean.reset_index(inplace=True)
        df_clean.rename(columns={"index": "daty"}, inplace=True)

        rows_in_range = df_clean[df_clean["daty"].isin(daty_full)]

        nazwa_json = f"{info['symbol']}.json"
        df_json = df_clean.copy()
        df_json["daty"] = df_json["daty"].dt.strftime("%Y-%m-%d")
        df_json.to_json(nazwa_json, orient="records", force_ascii=False)

        stock_prices[nazwa] = df_clean
        print(f"-> {nazwa}: Wczytano poprawnie ({len(df_clean)} dni).")

    except Exception as e:
        print(f"Błąd przetwarzania pliku {plik}: {e}")

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


df_usd = pd.DataFrame(usd_history)
if not df_usd.empty:
    df_usd["effectiveDate"] = pd.to_datetime(df_usd["effectiveDate"])
    df_usd.set_index("effectiveDate", inplace=True)
    df_usd.sort_index(inplace=True)

df_gold = pd.DataFrame(gold_history)
if not df_gold.empty:
    df_gold["data"] = pd.to_datetime(df_gold["data"])
    df_gold.set_index("data", inplace=True)
    df_gold.sort_index(inplace=True)


# --- Prepare Historical Data for Plotting ---
if not df_usd.empty:
    print(f"DEBUG: USD data loaded. Rows: {len(df_usd)}")
    print(f"DEBUG: USD head:\n{df_usd.head()}")
    usd_series = df_usd["mid"].reindex(daty_full).ffill().bfill()
else:
    print("Warning: USD data empty, using 1.0 as rate")
    usd_series = pd.Series(1.0, index=daty_full)

if not df_gold.empty:
    print(f"DEBUG: Gold data loaded. Rows: {len(df_gold)}")
    gold_series = df_gold["cena"].reindex(daty_full).ffill().bfill()
else:
    print("Warning: Gold data empty, using 1.0 as rate")
    gold_series = pd.Series(1.0, index=daty_full)

# --- Plotting: 3 Subplots (PLN, USD, Gold) ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

ax1.set_title("Cena w PLN")
ax1.set_ylabel("Cena (PLN)")

ax2.set_title("Cena w USD")
ax2.set_ylabel("Cena (USD)")

ax3.set_title("Cena w Złocie")
ax3.set_ylabel("Cena (gramy złota)")

for nazwa, df_stock in stock_prices.items():
    if df_stock.empty:
        continue

    if "daty" in df_stock.columns:
        df_plot = df_stock.set_index("daty")
    else:
        df_plot = df_stock.copy()

    prices_pln = df_plot["Close"]

    prices_usd = prices_pln / usd_series
    prices_gold = prices_pln / gold_series

    ax1.plot(prices_pln.index, prices_pln, label=nazwa)
    ax2.plot(prices_usd.index, prices_usd, label=nazwa)
    ax3.plot(prices_gold.index, prices_gold, label=nazwa)

ax1.legend()
ax2.legend()
ax3.legend()

plt.tight_layout()
plt.show()
