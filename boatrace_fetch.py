import requests
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os

# === 設定 ===
SHEET_NAME = "ボートレース予想"  # あなたのシート名
WORKSHEET_NAME = "今日の直前データ"  # 出力先タブ

# Google Sheets認証（サービスアカウントJSONをリポジトリsecretsに設定推奨）
def get_gspread_client():
    creds_dict = {
        "type": "service_account",
        # ... (GitHub Secretsから読み込み推奨。詳細後述)
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

# データ取得（Previews + Programsを組み合わせ）
def fetch_today_data():
    # Previews（直前情報：展示・一周・まわり足・直線・STなど）
    preview_url = "https://boatraceopenapi.github.io/previews/v3/today.json"
    # Programs（出走表・基本情報）
    program_url = "https://boatraceopenapi.github.io/programs/v3/today.json"
    
    try:
        previews = requests.get(preview_url).json()
        programs = requests.get(program_url).json()
    except:
        print("データ取得失敗（非開催日？）")
        return pd.DataFrame()
    
    # pandasで処理（実際のJSON構造に合わせて調整）
    preview_df = pd.json_normalize(previews.get('previews', [])) if isinstance(previews, dict) else pd.DataFrame(previews)
    program_df = pd.json_normalize(programs.get('programs', [])) if isinstance(programs, dict) else pd.DataFrame(programs)
    
    # 結合例（raceキーなどでマージ）
    df = pd.merge(program_df, preview_df, on=['stadium_number', 'number'], how='left')
    
    # 欲しいカラム例（実際のキー名はJSON確認後調整）
    key_columns = [
        'stadium_name', 'number', 'race_title',
        # 枠番別
        'boat_1_exhibition_time', 'boat_1_straight_time', 'boat_1_lap_time', 'boat_1_turn_time',  # まわり足など
        'boat_1_start_timing', 'boat_1_win_rate',  # 枠番別勝率・ST
        # 同様にboat_2 ~ boat_6
        # ... あなたのフィルタ追加ここ
    ]
    return df[key_columns] if all(col in df.columns for col in key_columns) else df

# Sheets書き込み
def update_sheet(df):
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"更新完了: {len(df)}レース")

if __name__ == "__main__":
    df = fetch_today_data()
    if not df.empty:
        # ここにあなたのフィルタ（3号艇条件など）を追加
        # df = df[df['some_condition'] == True]
        update_sheet(df)
