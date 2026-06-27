import requests
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

SHEET_NAME = "ボートレース予想"

print("=== 開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def fetch_and_update():
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    
    today = datetime.now().strftime("%Y/%m/%d")
    
    # 1. CSV（まわり足・一周・直線）
    try:
        csv_url = f"https://boatracecsv.github.io/data/previews/original_exhibition/{today}.csv"
        df_csv = pd.read_csv(csv_url)
        sheet_csv = spreadsheet.worksheet("CSV_まわり足など") if "CSV_まわり足など" in [ws.title for ws in spreadsheet.worksheets()] else spreadsheet.add_worksheet("CSV_まわり足など", 1000, 300)
        df_csv = df_csv.fillna('')
        sheet_csv.clear()
        sheet_csv.update([df_csv.columns.values.tolist()] + df_csv.values.tolist())
        print("✅ CSVタブ更新完了")
    except Exception as e:
        print("CSV取得失敗", str(e))
    
    # 2. API（展示・ST）
    try:
        p = requests.get("https://boatraceopenapi.github.io/previews/v3/today.json", timeout=10).json()
        df_api = pd.json_normalize(p.get('previews', p) if isinstance(p, dict) else p, sep='_')
        sheet_api = spreadsheet.worksheet("API_展示ST") if "API_展示ST" in [ws.title for ws in spreadsheet.worksheets()] else spreadsheet.add_worksheet("API_展示ST", 1000, 300)
        df_api = df_api.fillna('')
        sheet_api.clear()
        sheet_api.update([df_api.columns.values.tolist()] + df_api.values.tolist())
        print("✅ APIタブ更新完了")
    except Exception as e:
        print("API取得失敗", str(e))

fetch_and_update()
print("=== 完了 ===")
