from flask import Flask, render_template, request, jsonify
import json
import sqlite3
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__)
CONFIG_FILE = "config.json"

def init_db():
    """データベースの初期化（インデックス追加）"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON sensor_data (timestamp DESC)
    ''')
    conn.commit()
    conn.close()
    
def get_temp_hum_data():
    """sensor_data.db から timestamp, temperature, humidity, battery を取得する"""
    conn = sqlite3.connect("sensor_data.db")
    query = "SELECT timestamp, temperature, humidity, battery FROM sensor_data ORDER BY timestamp"
    df = pd.read_sql(query, conn)
    conn.close()
    # timestamp を datetime 型に変換
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_latest_data():
    """最新のセンサーデータを取得"""
    try:
        conn = sqlite3.connect("sensor_data.db")
        query = """
            SELECT timestamp, mac_addr, temperature, humidity, battery 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict(orient="records")[0] if not df.empty else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    
def load_threshold():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("threshold_temperature", 25.0)
    except FileNotFoundError:
        return 25.0

def save_threshold(value):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"threshold_temperature": value}, f)

@app.route("/get_threshold")
def get_threshold():
    return jsonify({"threshold": load_threshold()})

@app.route("/set_threshold", methods=["POST"])
def set_threshold():
    data = request.json
    save_threshold(float(data["threshold"]))
    return jsonify({"status": "ok"})

@app.route("/get_latest_data")
def latest_data_endpoint():
    """最新のセンサーデータを JSON で返す API エンドポイント"""
    latest_data = get_latest_data()
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data available"}), 404

@app.route("/")
def index():
    """ホームページ（最新データ表示）"""
    latest_data = get_latest_data()
    return render_template("dashboard.html", latest_data=latest_data)

@app.route("/graph")
def graph():
    df = get_temp_hum_data()
    
    # それぞれのデータでトレースを作成
    trace_temp = go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines', name='Temperature')
    trace_hum = go.Scatter(x=df['timestamp'], y=df['humidity'], mode='lines', name='Humidity')
    trace_bat = go.Scatter(x=df['timestamp'], y=df['battery'], mode='lines', name='Battery')
    
    # 全トレースを含む Figure を作成（初期状態は「All」）
    fig = go.Figure(data=[trace_temp, trace_hum, trace_bat])
    
    # x軸に rangeslider と rangeselector を追加し、さらに updatemenus で表示項目を切り替え可能に設定
    fig.update_layout(
        title="Sensor Data Trend (All)",
        xaxis=dict(
            title="Time",
            rangeslider=dict(visible=True),
            rangeselector=dict(
                y=1.15,  # 上部に配置
                x=0,  # 左寄せ
                xanchor="left",
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=24, label="24h", step="hour", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            ),
            type="date"
        ),
        yaxis=dict(title="Value"),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1,  # 右寄せ
                y=1.15,  # 上部に配置
                xanchor="right",
                showactive=True,
                buttons=list([
                    dict(label="Temperature", method="update",
                        args=[{"visible": [True, False, False]},
                            {"title": "Temperature Trend",
                                "yaxis": {"title": "Temperature (°C)"}}]),
                    dict(label="Humidity", method="update",
                        args=[{"visible": [False, True, False]},
                            {"title": "Humidity Trend",
                                "yaxis": {"title": "Humidity (%)"}}]),
                    dict(label="Battery", method="update",
                        args=[{"visible": [False, False, True]},
                            {"title": "Battery Trend",
                                "yaxis": {"title": "Battery (%)"}}])
                ])
            )
        ]
    )
    
    # Figure を HTML 部分のみに変換
    graph_html = fig.to_html(full_html=False)
    return render_template("graph.html", graph_html=graph_html)


if __name__ == "__main__":
    init_db()  # データベースの初期化
    app.run(host='0.0.0.0', port=5000, debug=True)