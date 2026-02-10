import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# 1. 页面设置
st.set_page_config(page_title="我的投资热力图", layout="wide")
st.title("💰 极简版持仓热力图")

try:
    # 记得把下面这个链接换成你自己的 Raw 链接！
    url = "https://github.com/Dufuo/invest-dashboard/raw/refs/heads/main/portfolio.csv" 
    df = pd.read_csv(url)
except Exception as e:
    st.error(f"读取数据失败，详细错误：{e}")
    st.stop()

# 3. 获取实时汇率 (美元 -> 人民币)
usd_cny = yf.Ticker("CNY=X").history(period="1d")['Close'].iloc[-1]
st.sidebar.write(f"当前美元汇率: {usd_cny:.2f}")


# 4. 定义获取价格函数
def get_current_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if data.empty:
            return None, None
        current_price = data['Close'].iloc[-1]
        prev_close = data['Open'].iloc[0]  # 用开盘价近似前收盘做涨跌幅
        change_pct = (current_price - prev_close) / prev_close * 100
        return current_price, change_pct
    except:
        return None, None


# 5. 循环抓取数据 (加个进度条，因为 yfinance 会慢)
if st.button('🔄 刷新数据'):
    my_bar = st.progress(0)
    total_len = len(df)

    current_prices = []
    changes = []

    for i, row in df.iterrows():
        price, change = get_current_data(row['Ticker'])
        current_prices.append(price)
        changes.append(change)
        my_bar.progress((i + 1) / total_len)

    df['Current_Price'] = current_prices
    df['Change_Pct'] = changes

    # 6. 计算市值和盈亏
    # 如果是美股，价格要乘汇率
    df['Market_Value_RMB'] = df.apply(
        lambda x: x['Current_Price'] * x['Quantity'] * usd_cny if x['Market'] == 'US' else x['Current_Price'] * x[
            'Quantity'],
        axis=1
    )

    df['Total_Cost_RMB'] = df.apply(
        lambda x: x['Cost_Price'] * x['Quantity'] * usd_cny if x['Market'] == 'US' else x['Cost_Price'] * x['Quantity'],
        axis=1
    )

    df['Profit_RMB'] = df['Market_Value_RMB'] - df['Total_Cost_RMB']

    # 7. 能够展示的数据表
    st.dataframe(df)

    # 8. 画热力图
    # 颜色：A股习惯 红色涨(正)，美股习惯 绿色涨(正)。这里统一用 红色代表赚钱(Profit > 0)
    fig = px.treemap(
        df,
        path=[px.Constant("我的持仓"), 'Market', 'Ticker'],
        values='Market_Value_RMB',
        color='Profit_RMB',
        color_continuous_scale='RdYlGn',  # 红绿配色
        color_continuous_midpoint=0,
        hover_data=['Change_Pct', 'Current_Price']
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("点击上方按钮开始获取最新数据")
