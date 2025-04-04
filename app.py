import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objs as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="RSI 다이버전스 정신과 트레이딩", page_icon="💭")
st.title("💭 RSI 다이버전스 정신과 트레이디닝")

# 🧠 Sidebar 종목 명 및 기간 선택
symbol = st.sidebar.text_input("종목 코드 입력 (예: AAPL, 005930.KS, 012450.KQ)", value="AAPL")
start_date = st.sidebar.date_input("시작 날짜", value=pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료 날짜", value=pd.to_datetime("2024-04-01"))

# 📊 데이터 다운로드
data = yf.download(symbol, start=start_date, end=end_date)

if data.empty:
    st.error("❌ 선택한 종목의 데이터를 가지오지 못했습니다.")
    st.stop()

if 'Close' not in data.columns:
    st.error("❌ 종가(Close) 데이터가 없습니다.")
    st.stop()

close = data['Close'].squeeze()
if close.empty:
    st.error("❌ 종가 데이터가 비어있습니다.")
    st.stop()

# ✅ RSI 계산
try:
    data['RSI'] = ta.momentum.RSIIndicator(close=close.squeeze(), window=14).rsi()
    if data['RSI'].isnull().all():
        st.error("❌ RSI 계산 결과가 모두 결식치입니다.")
        st.stop()
except Exception as e:
    st.error(f"RSI 계산 중 오류 발생: {e}")
    st.stop()

# ✅ 번리저 방드 계산
try:
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    data['bb_bbm'] = bb.bollinger_mavg()
    data['bb_bbh'] = bb.bollinger_hband()
    data['bb_bbl'] = bb.bollinger_lband()
except Exception as e:
    st.warning(f"번리저 방드 계산 오류: {e}")

# 🧠 다이버전스 탐지 함수
def find_bullish_divergence(df):
    points = []
    for i in range(30, len(df)):
        price_now = float(df['Close'].iloc[i])
        price_prev = float(df['Close'].iloc[i-10:i].min())
        rsi_now = float(df['RSI'].iloc[i])
        rsi_prev = float(df['RSI'].iloc[i-10:i].min())
        if price_now < price_prev and rsi_now > rsi_prev:
            points.append(i)
    return points

def find_bearish_divergence(df):
    points = []
    for i in range(30, len(df)):
        price_now = float(df['Close'].iloc[i])
        price_prev = float(df['Close'].iloc[i-10:i].max())
        rsi_now = float(df['RSI'].iloc[i])
        rsi_prev = float(df['RSI'].iloc[i-10:i].max())
        if price_now > price_prev and rsi_now < rsi_prev:
            points.append(i)
    return points

bullish_points = find_bullish_divergence(data)
bearish_points = find_bearish_divergence(data)

# 🔍 통합 Plotly 체계 작성
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.7, 0.3],
    subplot_titles=(f"{symbol} 가격 + RSI 다이버전스 + 번리저 방드", "RSI")
)

fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="종가", line=dict(color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.iloc[bullish_points].index, y=data['Close'].iloc[bullish_points],
                         mode='markers', name='🟢 매수 다이버전스', marker=dict(color='green', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=data.iloc[bearish_points].index, y=data['Close'].iloc[bearish_points],
                         mode='markers', name='🔴 매도 다이버전스', marker=dict(color='red', size=10)), row=1, col=1)

if 'bb_bbm' in data.columns:
    fig.add_trace(go.Scatter(x=data.index, y=data['bb_bbh'], name='번리저 상단', line=dict(color='lightgray', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['bb_bbm'], name='번리저 중간', line=dict(color='gray', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['bb_bbl'], name='번리저 하단', line=dict(color='lightgray', dash='dot')), row=1, col=1)

fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line=dict(color='gray', dash='dot'), row=2, col=1)
fig.add_hline(y=30, line=dict(color='gray', dash='dot'), row=2, col=1)

fig.update_layout(
    height=700,
    showlegend=True,
    xaxis_title="날짜",
    yaxis_title="가격",
    xaxis2_title="날짜",
    yaxis2_title="RSI",
)

# ✔️ 시각화 보출
st.plotly_chart(fig, use_container_width=True)
