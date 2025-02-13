import sqlite3

# データベースファイルへの接続（存在しない場合は自動生成）
conn = sqlite3.connect('sensor_data.db')

cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = cursor.fetchall()

print("テーブル一覧:")
for table in tables:
    print(table[0])

# 特定のテーブルのカラム情報を取得
table_name = "sensor_data"  # 例: ログテーブル

cursor.execute(f"PRAGMA table_info({table_name})")
columns = cursor.fetchall()

print(f"\n{table_name}テーブルのカラム:")
for col in columns:
    print(f"ID: {col[0]}, 名前: {col[1]}, 型: {col[2]}")

# 特定のクエリを実行
cursor.execute("SELECT * FROM sensor_data")
# cursor.execute("SELECT * FROM latest_data")


print("\nデータサンプル:")
headers = [desc[0] for desc in cursor.description]
print(" | ".join(headers))

for row in cursor.fetchall():
    print(f" | ".join(str(item) for item in row))

# conn.commit()  # 必要な場合（更新操作）
conn.close()
