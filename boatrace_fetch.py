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
    p = requests.get("https://boatraceopenapi.github.io/previews/v3/today.json", timeout=10).json()
    pr = requests.get("https://boatraceopenapi.github.io/programs/v3/today.json", timeout=10).json()
    
    # ネストを広範囲にフラット化
    preview_df = pd.json_normalize(p.get('previews', p) if isinstance(p, dict) else p, sep='_')
    program_df = pd.json_normalize(pr.get('programs', pr) if isinstance(pr, dict) else pr, sep='_')
    
    df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
    
    # ★ 欲しい情報を幅広く検索・抽出
    important_keywords = ['exhibition', 'straight', 'turn', 'lap', 'start_timing', 'stadium', 'number', 'title']
    selected_cols = [col for col in df.columns if any(k in col.lower() for k in important_keywords)]
    
    df = df[['stadium_number', 'stadium_name', 'number', 'title'] + [c for c in selected_cols if c not in ['stadium_number', 'number', 'title']]]
    
    print("抽出された主な列:", list(df.columns))
    print(f"✅ {len(df)}レース")
    return df

def update_sheet(df):
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        sheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 200)
    
    df = df.fillna('')
    df = df.replace([np.inf, -np.inf], '')
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レース")

df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
