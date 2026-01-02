import json
import matplotlib.pyplot as plt
import numpy as np

file_names = ("PUR.json", "EUC.json", "CDR.json")

usd_price = 3.5963
gold_price = 500.84


def read_securities(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if "code" not in data:
        raise ValueError("Missing 'code'")
    if "quotes" not in data:
        raise ValueError("Missing 'quotes'")

    quote = data["quotes"]
    if "date" not in quote or "close" not in quote:
        raise ValueError("Quote must contain 'date' and 'close'")

    return {
        "code": data["code"],
        "currency": data.get("currency", "PLN"),
        "date": quote["date"],
        "close": float(quote["close"]),
    }


# --- Read all selected papers ---
data = [read_securities(file) for file in file_names]

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
