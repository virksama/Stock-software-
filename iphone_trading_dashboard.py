"""Historical research dashboard. NOT live, no order execution or alerts.
Install: pip install streamlit yfinance pandas
Run: streamlit run iphone_trading_dashboard.py
"""
import streamlit as st
import pandas as pd
import yfinance as yf

SYMBOLS = ['NVDA','MSFT','AAPL','META','AMZN','GOOGL','TSLA','SPY','QQQ','DELL','AMD','MRVL','NOW']
st.set_page_config(page_title='Trading Scanner Research', page_icon='📈', layout='centered')
st.title('Trading Scanner')
st.warning('HISTORICAL RESEARCH ONLY. Not live prices, options quotes, news, or trade recommendations.')
st.caption('Robinhood orders are manual. No brokerage login or API keys required.')
risk = st.slider('Simulated risk budget per trade ($)', 5, 100, 20, 5)
st.metric('Simulated account', '$2,000')
st.metric('Planned risk budget', f'${risk}')
@st.cache_data(ttl=900)
def load(symbol):
    df = yf.download(symbol, period='6mo', interval='1d', auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def evaluate(symbol):
    df=load(symbol)
    if len(df)<35: return {'Symbol':symbol,'Signal':'Insufficient history','RSI':None,'Last bar':'—'}
    c=df['Close'].astype(float)
    a=c.ewm(span=9,adjust=False).mean(); b=c.ewm(span=21,adjust=False).mean()
    delta=c.diff(); up=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    down=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    r=100-100/(1+up/down.replace(0,float('nan')))
    bull=a.iloc[-2]<=b.iloc[-2] and a.iloc[-1]>b.iloc[-1] and r.iloc[-1]>50
    bear=a.iloc[-2]>=b.iloc[-2] and a.iloc[-1]<b.iloc[-1] and r.iloc[-1]<50
    return {'Symbol':symbol,'Signal':'Bullish watch' if bull else 'Bearish watch' if bear else 'No crossover', 'RSI':round(float(r.iloc[-1]),1) if pd.notna(r.iloc[-1]) else None,'Last bar':str(df.index[-1].date())}

if st.button('Refresh historical signals',type='primary'):
    st.cache_data.clear()
rows=[]
with st.spinner('Loading historical daily bars...'):
    for symbol in SYMBOLS:
        try: rows.append(evaluate(symbol))
        except Exception: rows.append({'Symbol':symbol,'Signal':'Data unavailable','RSI':None,'Last bar':'—'})
st.subheader('Combined watchlist')
st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
st.info('VWAP needs intraday bars. Option strikes, expirations, bid/ask, live news, and iPhone notifications require additional verified services. Do not trade 0DTE based on these daily historical signals.')
st.subheader('Next build milestones')
st.write('1. Verify real-time stocks AND OPRA options data, including API licensing and monthly costs.')
st.write('2. Add options contract screening and intraday session VWAP.')
st.write('3. Deploy on a cloud host and connect an iPhone notification channel.')
st.write('4. Backtest, then paper-test alerts before considering real trades.')

# 5-minute intraday research scanner
st.subheader("5-Minute Intraday Scanner")
st.caption("Yahoo Finance data may be delayed or unavailable. Not live trading signals.")

@st.cache_data(ttl=300)
def intraday_scan(symbol):
    df = yf.download(
        symbol, period="5d", interval="5m",
        auto_adjust=True, progress=False
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty or len(df) < 30:
        return {"Symbol": symbol, "Status": "No data"}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()

    change = close.diff()
    gain = change.clip(lower=0).ewm(
        alpha=1/14, adjust=False
    ).mean()
    loss = (-change.clip(upper=0)).ewm(
        alpha=1/14, adjust=False
    ).mean()
    rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] > 0 else float("inf")
    rsi = 100 - 100 / (1 + rs)

    typical = (high + low + close) / 3
    session = df.index.tz_convert(
        "America/New_York"
    ).date if df.index.tz is not None else df.index.date
    session_key = pd.Series(session, index=df.index)
    vwap = (typical * volume).groupby(
        session_key
    ).cumsum() / volume.groupby(
        session_key
    ).cumsum().replace(0, float("nan"))

    trend = "Bullish" if ema9.iloc[-1] > ema21.iloc[-1] else "Bearish"

    return {
        "Symbol": symbol,
        "Price": round(float(close.iloc[-1]), 2),
        "EMA 9": round(float(ema9.iloc[-1]), 2),
        "EMA 21": round(float(ema21.iloc[-1]), 2),
        "RSI": round(float(rsi), 1),
        "VWAP": round(float(vwap.iloc[-1]), 2),
        "Trend": trend,
        "Last bar": str(df.index[-1])
    }

if st.button("Refresh 5-minute scanner"):
    intraday_scan.clear()

intraday_rows = []
with st.spinner("Scanning 5-minute bars..."):
    for symbol in SYMBOLS:
        try:
            intraday_rows.append(intraday_scan(symbol))
        except Exception as e:
            intraday_rows.append({
                "Symbol": symbol,
                "Status": "Data unavailable"
            })

st.dataframe(
    pd.DataFrame(intraday_rows),
    hide_index=True,
    use_container_width=True
)
