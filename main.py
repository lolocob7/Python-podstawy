import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib.request
import datetime
import json as js
import ssl

# -----------------------------
# 4. Wczytanie Twoich plików CSV (Format Polski)
# -----------------------------
# --- Setup Time Period ---
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5 * 365)
daty_full = pd.date_range(start=start_date, end=end_date, freq="D")

stock_files = [
    {"nazwa": "EUCO/20", "symbol": "EUC"},
    {"nazwa": "CDPROJECT", "symbol": "CDR"},
    {"nazwa": "PURE", "symbol": "PUR"},
]

notowania = {}
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

        # -> Tworzymy czystą tabelę tylko z ceną zamknięcia
        df_clean = pd.DataFrame()
        df_clean["Close"] = df[price_col]

        # -> Sortujemy datami (od 2021 do 2026), żeby wykres się nie pomieszał
        df_clean = df_clean.sort_index()

        # -> Wyrównanie do 5 lat (1826 dni). Dzięki temu możemy łatwo dzielić przez kurs dolara.
        df_clean = df_clean.reindex(daty_full)
        df_clean["Close"] = (
            df_clean["Close"].interpolate(method="linear").ffill().bfill()
        )

        df_clean.reset_index(inplace=True)
        df_clean.rename(columns={"index": "daty"}, inplace=True)

        # -> Zadanie (a): Zapis do JSON. Konwertujemy daty na tekst, bo JSON nie obsługuje obiektów datetime.
        nazwa_json = f"{info['symbol']}.json"
        df_json = df_clean.copy()
        df_json["daty"] = df_json["daty"].dt.strftime("%Y-%m-%d")
        df_json.to_json(nazwa_json, orient="records", force_ascii=False)

        notowania[nazwa] = df_clean
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


# --- Process NBP Data into DataFrames for lookup ---
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


# --- Fetch Security Data & Populate Main DataFrame ---
rows_list = []

for nazwa, df_stock in notowania.items():
    if df_stock.empty:
        continue

    # Get the last row (most recent date)
    last_row = df_stock.iloc[-1]
    # 'daty' column is datetime64[ns]
    last_date = last_row["daty"]
    last_close = float(last_row["Close"])

    # Lookup USD and Gold rates (nearest available date)
    usd_val = np.nan
    gold_val = np.nan

    if not df_usd.empty:
        idx_usd = df_usd.index.get_indexer([last_date], method="nearest")[0]
        usd_val = float(df_usd.iloc[idx_usd]["mid"])

    if not df_gold.empty:
        idx_gold = df_gold.index.get_indexer([last_date], method="nearest")[0]
        gold_val = float(df_gold.iloc[idx_gold]["cena"])

    rows_list.append(
        {
            "code": nazwa,
            "date": last_date.strftime("%Y-%m-%d"),
            "close": last_close,
            "usd_rate": usd_val,
            "gold_rate": gold_val,
        }
    )

# Create the main DataFrame
data = pd.DataFrame(rows_list)

# Calculate converted prices if data exists
if not data.empty:
    data["price_usd"] = data["close"] / data["usd_rate"]
    data["price_gold"] = data["close"] / data["gold_rate"]
    # Fill any NaNs if rates were missing
    data.fillna(0, inplace=True)


# --- Print conversions ---
for index, item in data.iterrows():
    print(f"{item['code']} ({item['date']})")
    print(f"PLN: {item['close']:.4f}")
    print(f"USD: {item['price_usd']:.4f}")
    print(f"Złoto (g): {item['price_gold']:.6f}")
    print("-" * 30)

# --- Prepare chart data ---
if not data.empty:
    codes = data["code"].tolist()
    prices_pln = data["close"].tolist()
    prices_usd = data["price_usd"].tolist()
    prices_gold = data["price_gold"].tolist()
else:
    codes, prices_pln, prices_usd, prices_gold = [], [], [], []


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
