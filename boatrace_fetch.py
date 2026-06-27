import requests
import pandas as pd
import json
import os
from datetime import datetime

# ================== 設定 ==================
SHEET_NAME = "ボートレース予想"
WORKSHEET_NAME = "今日の直前データ"
# =========================================

print("=== ボートレース自動更新開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

creds_json = os.getenv('GOOGLE_CREDENTIALS')
if not creds_json:
    print("❌ GOOGLE_CREDENTIALS がありません")
    exit(1)

try:
    creds_dict = json.loads(creds_json)
    print("✅ 認証JSON成功 -", creds_dict.get('client_email'))
except Exception as e:
    print("❌ JSONエラー:", str(e))
    exit(1)

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    # ★ スコープを拡張（これが重要！）
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"   # ← 追加
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def fetch_data():
    print("📡 データ取得中...")
    try:
        previews = requests.get("https://boatraceopenapi.github.io/previews/v3/today.json", timeout=10).json()
        programs = requests.get("https://boatraceopenapi.github.io/programs/v3/today.json", timeout=10).json()
        
        preview_df = pd.json_normalize(previews.get('previews', previews) if isinstance(previews, dict) else previews)
        program_df = pd.json_normalize(programs.get('programs', programs) if isinstance(programs, dict) else programs)
        
        print(f"✅ 取得成功 - {len(preview_df)}レース")
        df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
        return df
    except Exception as e:
        print("❌ データ取得失敗:", str(e))
        return pd.DataFrame()

def update_sheet(df):
    if df.empty:
        print("⚠️ データ空")
        return
    client = get_gspread_client()
    try:
        spreadsheet = client.open(SHEET_NAME)
        print(f"✅ シート発見")
    except Exception:
        print("新規シート作成")
        spreadsheet = client.create(SHEET_NAME)
    
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except Exception:
        sheet = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=50)
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レース")

df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
