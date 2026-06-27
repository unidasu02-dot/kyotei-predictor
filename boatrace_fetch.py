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
    
    preview_df = pd.json_normalize(p.get('previews', p) if isinstance(p, dict) else p, 
                                   sep='_')
    program_df = pd.json_normalize(pr.get('programs', pr) if isinstance(pr, dict) else pr, 
                                   sep='_')
    
    df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
    
    # ★ あなたの欲しい列を優先抽出
    key_cols = [
        'stadium_number', 'stadium_name', 'number', 'title',
        # 1号艇〜6号艇のタイム情報
        'boats_1_racer_exhibition_time', 'boats_2_racer_exhibition_time', 
        'boats_3_racer_exhibition_time', 'boats_4_racer_exhibition_time',
        'boats_5_racer_exhibition_time', 'boats_6_racer_exhibition_time',
        
        'boats_1_racer_straight_time', 'boats_2_racer_straight_time', 
        'boats_3_racer_straight_time', 'boats_4_racer_straight_time',
        'boats_5_racer_straight_time', 'boats_6_racer_straight_time',
        
        'boats_1_racer_turn_time', 'boats_2_racer_turn_time', 
        'boats_3_racer_turn_time', 'boats_4_racer_turn_time',
        'boats_5_racer_turn_time', 'boats_6_racer_turn_time',
        
        'boats_1_racer_lap_time', 'boats_2_racer_lap_time', 
        'boats_3_racer_lap_time', 'boats_4_racer_lap_time',
        'boats_5_racer_lap_time', 'boats_6_racer_lap_time',
        
        'boats_1_racer_start_timing', 'boats_2_racer_start_timing', 
        'boats_3_racer_start_timing', 'boats_4_racer_start_timing',
        'boats_5_racer_start_timing', 'boats_6_racer_start_timing',
    ]
    
    available = [c for c in key_cols if c in df.columns]
    df = df[available]
    
    print(f"✅ 抽出完了 {len(df)}レース")
    return df

def update_sheet(df):
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        sheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 100)
    
    df = df.fillna('')
    df = df.replace([np.inf, -np.inf], '')
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レース")

df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
