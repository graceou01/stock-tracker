import streamlit as st
import yfinance as yf
import pandas as pd

# --- 設定網頁標題 ---
st.title('靜玫的投資儀表板 📈')
st.caption('上次更新時間：即時 (依照 Yahoo Finance)')

# --- 1. 定義妳的投資組合 (這是妳的秘密帳本) ---
# 邏輯挑戰：未來我們可以把這個寫在外部檔案，不用每次改程式碼
portfolio = [
    {"symbol": "2330.TW", "cost": 600, "shares": 2000},  # 台積電
    {"symbol": "NVDA", "cost": 120, "shares": 50},       # 輝達
    {"symbol": "TSLA", "cost": 250, "shares": 30},       # 特斯拉
    {"symbol": "0050.TW", "cost": 130, "shares": 1000}   # 0050
]

# --- 2. 抓取股價的邏輯函數 ---
def get_data(portfolio):
    data_list = []
    total_cost_twd = 0
    total_value_twd = 0
    
    # 假設匯率 (如果要精準，這裡也可以寫爬蟲抓即時匯率)
    usd_to_twd = 32.5 

    progress_bar = st.progress(0) # 進度條
    
    for i, item in enumerate(portfolio):
        ticker = item["symbol"]
        cost = item["cost"]
        shares = item["shares"]
        
        # 抓取即時股價
        stock = yf.Ticker(ticker)
        # 用 'fast_info' 抓最新價格通常比較快
        try:
            current_price = stock.basic_info.last_price
        except:
            # 如果失敗，改用歷史數據抓
            current_price = stock.history(period='1d')['Close'].iloc[-1]

        # 判斷幣別邏輯
        currency = "TWD"
        if ".TW" not in ticker:
            currency = "USD"
            market_value_twd = current_price * shares * usd_to_twd
            cost_twd = cost * shares * usd_to_twd
        else:
            market_value_twd = current_price * shares
            cost_twd = cost * shares

        # 計算單檔損益
        profit = market_value_twd - cost_twd
        profit_pct = (profit / cost_twd) * 100

        # 累積總數
        total_cost_twd += cost_twd
        total_value_twd += market_value_twd

        # 整理數據格式
        data_list.append({
            "代號": ticker,
            "現價": round(current_price, 2),
            "成本": cost,
            "持有股數": shares,
            "幣別": currency,
            "市值(約台幣)": round(market_value_twd, 0),
            "損益(約台幣)": round(profit, 0),
            "報酬率%": round(profit_pct, 2)
        })
        
        progress_bar.progress((i + 1) / len(portfolio)) # 更新進度條

    return pd.DataFrame(data_list), total_cost_twd, total_value_twd

# --- 3. 執行運算並顯示 ---
if st.button('更新股價'):
    df, total_cost, total_value = get_data(portfolio)
    
    # 總體指標卡片
    total_profit = total_value - total_cost
    total_roi = (total_profit / total_cost) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("總市值 (TWD)", f"${total_value:,.0f}")
    col2.metric("總獲利 (TWD)", f"${total_profit:,.0f}", f"{total_roi:.1f}%")
    col3.metric("原始總成本", f"${total_cost:,.0f}")

    # 顯示詳細表格 (依照報酬率排序，厲害的放上面)
    st.dataframe(df.sort_values(by="報酬率%", ascending=False))
    
    # 畫個簡單的圖：市值分佈
    st.subheader("資產分佈餅圖")
    st.bar_chart(df.set_index("代號")["市值(約台幣)"])

else:
    st.info('請點擊上方按鈕開始抓取資料')
