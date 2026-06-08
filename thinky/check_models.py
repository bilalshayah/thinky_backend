import requests
import json

# ضعي مفتاحك هنا للتجربة
API_KEY = "AIzaSyA-zGEwY1jpNTFQBU3S282n466pI2ouKMk"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(url)
    models = response.json()
    if 'models' in models:
        print("--- الموديلات المتاحة لكِ يا ريري ---")
        for m in models['models']:
            print(f"- {m['name']}")
    else:
        print("خطأ في الاستجابة:", models)
except Exception as e:
    print(f"حدث خطأ أثناء الاتصال: {e}")