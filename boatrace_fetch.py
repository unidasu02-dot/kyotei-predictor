import requests
import pandas as pd
import json
import os
from datetime import datetime

# ================== 設定 ==================
SHEET_NAME = "ボートレース予想"          # ← シートのタイトルに完全に一致させる
WORKSHEET_NAME = "今日の直前データ"     # ← タブ名に完全に一致させる
# =========================================

print("=== ボートレース自動更新開始 ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 認証テスト
creds_json = os.getenv('GOOGLE_CREDENTIALS')
if not creds_json:
    print("エラー: GOOGLE_CREDENTIALS が設定されていません")
    exit(1)

try:
    creds_dict = json.loads(creds_json)
    print("✅ 認証JSON読み込み成功 -", creds_dict.get('client_email'))
except Exception as e:
    print("❌ JSONパース失敗:", str(e))
    exit(1)

# Google Sheetsクライアント
def get_gspread_client():
    from google.oauth2.service_account import Credentials
    import gspread
    creds = Credentials.from_service_account_info(creds_dict, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

# データ取得
def fetch_data():
    print("📡 データ取得中...")
    preview_url = "https://boatraceopenapi.github.io/previews/v3/today.json"
    program_url = "https://boatraceopenapi.github.io/programs/v3/today.json"
    
    try:
        previews = requests.get(preview_url, timeout=10).json()
        programs = requests.get(program_url, timeout=10).json()
        
        # 柔軟にDataFrame化
        if isinstance(previews, list):
            preview_df = pd.DataFrame(previews)
        else:
            preview_df = pd.json_normalize(previews.get('previews', previews))
            
        if isinstance(programs, list):
            program_df = pd.DataFrame(programs)
        else:
            program_df = pd.json_normalize(programs.get('programs', programs))
        
        print(f"✅ 取得成功 - Previews: {len(preview_df)}件, Programs: {len(program_df)}件")
        
        # 結合（キー名は実際のJSONに合わせて調整可能）
        df = pd.merge(program_df, preview_df, 
                      left_on=['stadium_number', 'number'], 
                      right_on=['stadium_number', 'number'], 
                      how='left', suffixes=('', '_preview'))
        
        # 欲しい列を優先表示（実際のカラム名に合わせて後で追加）
        print("主な列:", list(df.columns)[:20])
        return df
        
    except Exception as e:
        print("❌ データ取得エラー:", str(e))
        return pd.DataFrame()

# Sheets更新
def update_sheet(df):
    if df.empty:
        print("⚠️ データが空です（非開催日？）")
        return
    
    client = get_gspread_client()
    try:
        spreadsheet = client.open(SHEET_NAME)
        print(f"✅ シート '{SHEET_NAME}' 発見")
    except Exception:
        print(f"シート '{SHEET_NAME}' がないので新規作成")
        spreadsheet = client.create(SHEET_NAME)
    
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except Exception:
        print(f"タブ '{WORKSHEET_NAME}' がないので新規作成")
        sheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=50)
    
    # ヘッダー＋データ書き込み
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"🎉 更新完了！ {len(df)}レースを '{WORKSHEET_NAME}' タブに書き込みました")

# メイン実行
df = fetch_data()
update_sheet(df)
print("=== 完了 ===")
