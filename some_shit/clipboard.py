import pyperclip
import time
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from win10toast import ToastNotifier

# Determine the path to the .env file
# If running as a frozen executable (PyInstaller), look in sys._MEIPASS
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=env_path)

toaster = ToastNotifier()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = "Działasz jako asysent analizujący pytania i odpowiedzi abcd. Wybierz jedną odpowiedź bez uzasadnienia."

def show_notification(text: str):
    toaster.show_toast(
        "🤖 OpenAI",
        text[:300],   # Windows ma limit długości
        duration=6,
        threaded=False
    )

def send_to_openai(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
    )
    return response.choices[0].message.content


def monitor_clipboard():
    last_text = None
    print("📋 Clipboard → OpenAI (Ctrl+C to stop)")

    while True:
        try:
            text = pyperclip.paste()

            if text and text != last_text:
                last_text = text
                print("\n➡️ Skopiowano:")
                print(text[:200])

                print("\n🤖 OpenAI analizuje...")
                answer = send_to_openai(text)
                show_notification(answer)
                print("\n✅ Odpowiedź OpenAI:")
                print(answer)

        except Exception as e:
            print("❌ Błąd:", e)

        time.sleep(0.2)


if __name__ == "__main__":
    monitor_clipboard()
