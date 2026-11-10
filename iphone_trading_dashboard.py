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
