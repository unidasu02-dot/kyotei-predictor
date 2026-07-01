import requests
import pandas as pd
import json
import os
from datetime import datetime
import sys

SHEET_NAME = "ボートレース予想"

print("=== 開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def parse_date(date_input):
    """柔軟に日付をパース"""
    if isinstance(date_input, datetime):
        return date_input
    
    if date_input is None:
        return datetime.now()
    
    date_str = str(date_input).replace('/', '').replace('-', '')
    if len(date_str) == 8:  # YYYYMMDD
        return datetime.strptime(date_str, "%Y%m%d")
    else:
        # その他の形式も試す
        for fmt in ("%Y%m%d", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(date_input), fmt)
            except ValueError:
                continue
    raise ValueError(f"日付の形式が認識できません: {date_input}")

def fetch_and_update(target_date=None):
    client = get_gspread_client()
    spreadsheet = client.open(SHEET_NAME)
    
    dt = parse_date(target_date)
    ymd_slash = dt.strftime("%Y/%m/%d")   # CSV用
    ymd_no_slash = dt.strftime("%Y%m%d")  # API用
    year = dt.strftime("%Y")
    
    print(f"対象日: {ymd_slash}")
    
    # 1. CSV（まわり足・一周・直線）
    try:
        csv_url = f"https://boatracecsv.github.io/data/previews/original_exhibition/{ymd_slash}.csv"
        print(f"CSV取得中: {csv_url}")
        df_csv = pd.read_csv(csv_url)
        sheet_name = "CSV_まわり足など"
        sheet_csv = spreadsheet.worksheet(sheet_name) if sheet_name in [ws.title for ws in spreadsheet.worksheets()] else spreadsheet.add_worksheet(sheet_name, 1000, 300)
        
        df_csv = df_csv.fillna('')
        sheet_csv.clear()
        sheet_csv.update([df_csv.columns.values.tolist()] + df_csv.values.tolist())
        print("✅ CSVタブ更新完了")
    except Exception as e:
        print("❌ CSV取得失敗", str(e))
    
    # 2. API（展示・ST）
    try:
        api_url = f"https://boatraceopenapi.github.io/previews/v3/{year}/{ymd_no_slash}.json"
        print(f"API取得中: {api_url}")
        p = requests.get(api_url, timeout=15).json()
        
        # データ構造に応じて正規化
        data = p.get('previews', p) if isinstance(p, dict) else p
        df_api = pd.json_normalize(data, sep='_')
        
        sheet_name = "API_展示ST"
        sheet_api = spreadsheet.worksheet(sheet_name) if sheet_name in [ws.title for ws in spreadsheet.worksheets()] else spreadsheet.add_worksheet(sheet_name, 1000, 300)
        
        df_api = df_api.fillna('')
        sheet_api.clear()
        sheet_api.update([df_api.columns.values.tolist()] + df_api.values.tolist())
        print("✅ APIタブ更新完了")
    except Exception as e:
        print("❌ API取得失敗", str(e))

# ====================== 実行例 ======================

if __name__ == "__main__":
    # コマンドライン引数で日付指定（例: python script.py 2026-07-01）
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = None  # 今日
    
    fetch_and_update(target)
    print("=== 完了 ===")
