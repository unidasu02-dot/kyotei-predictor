import requests
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

# ================== 設定 ==================
SHEET_NAME = "ボートレース予想"
WORKSHEET_NAME = "今日の直前データ"
# =========================================

print("=== 開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

creds_json = os.getenv('GOOGLE_CREDENTIALS')
creds_dict = json.loads(creds_json)
print("✅ 認証成功 -", creds_dict.get('client_email'))

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def fetch_data():
    print("📡 データ取得中...")
    previews = requests.get("https://boatraceopenapi.github.io/previews/v3/today.json", timeout=10).json()
    programs = requests.get("https://boatraceopenapi.github.io/programs/v3/today.json", timeout=10).json()
    
    preview_df = pd.json_normalize(previews.get('previews', previews) if isinstance(previews, dict) else previews)
    program_df = pd.json_normalize(programs.get('programs', programs) if isinstance(programs, dict) else programs)
    
    df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
    print(f"✅ 取得 {len(df)}レース")
    return df

def update_sheet(df):
    if df.empty:
        print("データ空")
        return
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        sheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 50)
    
    # ★ NaN/inf対策（これでエラー回避）
    df = df.fillna('')
    df = df.replace([np.inf, -np.inf], '')
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レース")

df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
