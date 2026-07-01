import requests
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

SHEET_NAME = "ボートレース予想"
WORKSHEET_NAME = "特定日データ"   # タブ名
TARGET_DATE = "2026-07-01"        # ← ここを変更（YYYY-MM-DD）

print("=== 特定日取得開始 ===", TARGET_DATE)

creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def fetch_data():
    print("📡 データ取得...")
    date_obj = datetime.strptime(TARGET_DATE, "%Y-%m-%d")
    year = date_obj.strftime("%Y")
    ymd = date_obj.strftime("%Y%m%d")
    
    # OpenAPI
    preview_url = f"https://boatraceopenapi.github.io/previews/v3/{year}/{ymd}.json"
    program_url = f"https://boatraceopenapi.github.io/programs/v3/{year}/{ymd}.json"
    
    preview_df = pd.DataFrame()
    program_df = pd.DataFrame()
    
    try:
        p = requests.get(preview_url, timeout=10).json()
        preview_df = pd.json_normalize(p.get('previews', p) if isinstance(p, dict) else p, sep='_')
    except:
        print("Preview取得失敗")
    
    try:
        pr = requests.get(program_url, timeout=10).json()
        program_df = pd.json_normalize(pr.get('programs', pr) if isinstance(pr, dict) else pr, sep='_')
    except:
        print("Program取得失敗")
    
    df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
    print(f"✅ {len(df)}レース取得")
    return df

def update_sheet(df):
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        sheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 300)
    
    df = df.fillna('')
    df = df.replace([np.inf, -np.inf], '')
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レース")

df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
