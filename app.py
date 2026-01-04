import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 設定網頁標題 ---
st.title('靜玫的投資儀表板 (雲端連線版) 🚀')

# --- 1. 連線到 Google Sheet ---
# 這是新的魔法，直接跟 Google 要資料
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 讀取資料，ttl=0 代表不快取，每次都抓最新的
    df_portfolio = conn.read(ttl=0)
    
    # 把資料轉成我們習慣的字典格式
    portfolio = df_portfolio.to_dict('records')
    
    if not portfolio:
        st.warning("Google Sheet 裡好像沒資料？請確認有 symbol, cost, shares 欄位")
        st.stop()
        
except Exception as e:
    st.error(f"連線失敗，請檢查 Secrets 設定: {e}")
    st.stop()

# --- 2. 抓取股價的邏輯函數 (跟之前一樣) ---
def get_data(portfolio):
    data_list = []
    total_cost_twd = 0
    total_value_twd = 0
    usd_to_twd = 32.5 

    progress_bar = st.progress(0)
    
    for i, item in enumerate(portfolio):
        ticker = item["symbol"]
        cost = float(item["cost"])     # 確保是數字
        shares = float(item["shares"]) # 確保是數字
        
        stock = yf.Ticker(ticker)
        try:
            current_price = stock.basic_info.last_price
        except:
            current_price = stock.history(period='1d')['Close'].iloc[-1]

        currency = "TWD"
        if ".TW" not in ticker:
            currency = "USD"
            market_value_twd = current_price * shares * usd_to_twd
            cost_twd = cost * shares * usd_to_twd
        else:
            market_value_twd = current_price * shares
            cost_twd = cost * shares

        profit = market_value_twd - cost_twd
        profit_pct = (profit / cost_twd) * 100 if cost_twd > 0 else 0

        total_cost_twd += cost_twd
        total_value_twd += market_value_twd

        data_list.append({
            "代號": ticker,
            "現價": round(current_price, 2),
            "成本": cost,
            "持有股數": shares,
            "幣別": currency,
            "市值(TWD)": round(market_value_twd, 0),
            "損益(TWD)": round(profit, 0),
            "報酬率%": round(profit_pct, 2)
        })
        progress_bar.progress((i + 1) / len(portfolio))

    return pd.DataFrame(data_list), total_cost_twd, total_value_twd

# --- 3. 顯示結果 ---
if st.button('更新股價'):
    st.caption("正在從 Google Sheet 讀取最新庫存...")
    df, total_cost, total_value = get_data(portfolio)
    
    total_profit = total_value - total_cost
    total_roi = (total_profit / total_cost) * 100 if total_cost > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("總市值 (TWD)", f"${total_value:,.0f}")
    col2.metric("總獲利 (TWD)", f"${total_profit:,.0f}", f"{total_roi:.1f}%")
    col3.metric("總成本", f"${total_cost:,.0f}")

    st.dataframe(df.sort_values(by="報酬率%", ascending=False))
    st.bar_chart(df.set_index("代號")["市值(TWD)"])
else:
    st.info('點擊按鈕，程式會去讀取妳的 Google Sheet 並計算獲利')
