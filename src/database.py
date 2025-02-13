import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    
    # センサーデータテーブル作成
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (timestamp DATETIME PRIMARY KEY,
                  mac_addr TEXT,
                  temperature REAL,
                  humidity REAL,
                  battery INTEGER)''')
                  
    # 最新データテーブル作成
    c.execute('''CREATE TABLE IF NOT EXISTS latest_data
                 (mac_addr TEXT PRIMARY KEY,
                  timestamp DATETIME,
                  temperature REAL,
                  humidity REAL,
                  battery INTEGER)''')
                  
    conn.commit()
    conn.close()

def log_data(mac_addr, temp, hum, batt):
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    ts = datetime.now().isoformat()
    
    # メインテーブルに挿入
    c.execute('''INSERT INTO sensor_data VALUES (?,?,?,?,?)''',
              (ts, mac_addr, temp, hum, batt))
    
    # 最新データを更新
    c.execute('''INSERT OR REPLACE INTO latest_data VALUES (?,?,?,?,?)''',
              (mac_addr, ts, temp, hum, batt))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
