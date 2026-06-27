import requests
import pandas as pd
import json
import os
from datetime import datetime

print("=== スクリプト開始 ===", datetime.now())

# 環境変数確認
creds = os.getenv('GOOGLE_CREDENTIALS')
print("GOOGLE_CREDENTIALS 存在確認:", "Yes" if creds else "No")

try:
    # データ取得
    preview_url = "https://boatraceopenapi.github.io/previews/v3/today.json"
    program_url = "https://boatraceopenapi.github.io/programs/v3/today.json"
    
    print("Previews URL取得中...")
    preview_resp = requests.get(preview_url)
    print("Previews ステータス:", preview_resp.status_code)
    
    print("Programs URL取得中...")
    program_resp = requests.get(program_url)
    print("Programs ステータス:", program_resp.status_code)
    
    previews = preview_resp.json()
    programs = program_resp.json()
    
    print("Previews キー:", list(previews.keys()) if isinstance(previews, dict) else "list型")
    print("Programs キー:", list(programs.keys()) if isinstance(programs, dict) else "list型")
    
    # pandas変換（安全に）
    if isinstance(previews, list):
        preview_df = pd.DataFrame(previews)
    else:
        preview_df = pd.json_normalize(previews.get('previews', previews))
    
    if isinstance(programs, list):
        program_df = pd.DataFrame(programs)
    else:
        program_df = pd.json_normalize(programs.get('programs', programs))
    
    print("取得データ数 - Previews:", len(preview_df), "Programs:", len(program_df))
    
    if preview_df.empty and program_df.empty:
        print("データなし（非開催日？）")
    else:
        print("サンプル列:", list(preview_df.columns)[:10] if not preview_df.empty else "空")
        
        # 結合（実際のキー名に合わせて調整）
        df = pd.merge(program_df, preview_df, left_on=['stadium_number', 'number'], 
                      right_on=['stadium_number', 'number'], how='left', suffixes=('', '_preview'))
        
        print("結合後行数:", len(df))
        print(df.head(3).to_string())  # デバッグ表示

except Exception as e:
    print("エラー発生:", type(e).__name__, str(e))

print("=== スクリプト終了 ===")
