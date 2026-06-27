import requests
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

SHEET_NAME = "ボートレース予想"
WORKSHEET_NAME = "今日の直前データ"

print("=== 開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def fetch_data():
    print("📡 データ取得...")
    today = datetime.now().strftime("%Y/%m/%d")
    
    # CSV
    csv_url = f"https://boatracecsv.github.io/data/previews/original_exhibition/{today}.csv"
    csv_df = pd.DataFrame()
    try:
        csv_df = pd.read_csv(csv_url)
        print("✅ CSV取得成功", len(csv_df), "列:", list(csv_df.columns)[:10])
    except Exception as e:
        print("CSV取得失敗", str(e))
    
    # API
    api_df = pd.DataFrame()
    try:
        p = requests.get("https://boatraceopenapi.github.io/previews/v3/today.json", timeout=10).json()
        api_df = pd.json_normalize(p.get('previews', p) if isinstance(p, dict) else p, sep='_')
        print("✅ API取得成功", len(api_df))
    except Exception as e:
        print("API取得失敗", str(e))
    
    # 統合（キー名を柔軟に）
    if not csv_df.empty and not api_df.empty:
        merge_key = 'stadium_number' if 'stadium_number' in csv_df.columns and 'stadium_number' in api_df.columns else 'number'
        df = pd.merge(csv_df, api_df, on=merge_key, how='left', suffixes=('_csv', '_api'))
    elif not csv_df.empty:
        df = csv_df
    else:
        df = api_df
    
    print("最終列:", list(df.columns))
    print(f"✅ 統合 {len(df)}レース")
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
