import urllib.request
import datetime
import json as js
import ssl

table = 'A'
start_date = (datetime.date.today() - datetime.timedelta(days=)).isoformat()
end_date = datetime.date.today().isoformat()
currency_code = 'USD'
url = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{currency_code}/{start_date}/{end_date}/?format=json"

context = ssl._create_unverified_context()

with urllib.request.urlopen(url, context=context) as response:

    res = response.read().decode("utf-8")  
 


data = js.loads(res)
save_path = "nbp_data.json"
with open(save_path, "w", encoding="utf-8") as f:
    js.dump(data, f, ensure_ascii=False, indent=4)
print(data)

#do zaliczenia analizujemy okres 5 lat
