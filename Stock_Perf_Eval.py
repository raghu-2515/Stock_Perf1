import streamlit as st
from datetime import date
from datetime import datetime
import pandas as pd
import plotly.express as px
import numpy as np

import yfinance as yf
from plotly import graph_objs as go

st.set_page_config(layout='wide', initial_sidebar_state='expanded')

TODAY=date.today().strftime("%Y-%m-%d")

st.title("Stock Performance Evaulation")

st.sidebar.subheader('Load the Invest Tracker File')
uploaded_file=st.sidebar.file_uploader('Select the Folio Data File', type='xlsx')

@st.cache_data
def get_price_data(df):
    for i in range(len(df)):
        cp= yf.download(df.at[i,'Symbol'],period="1d",interval="1d")['Adj Close']
        df.loc[i,'Current_Price']=round(cp.sum(),2)
    return df

if uploaded_file:
    st.markdown('----')
    ddf=pd.read_excel(uploaded_file,engine='openpyxl')
    #df['Trade Date'] = pd.to_datetime(df['Trade Date'])
    
    folio_list=ddf["Folio"].unique().tolist()
    folio_list.insert(0,'All')
    select_folio=st.sidebar.selectbox('Select Folio',folio_list,index=0)

    if select_folio=='All':
        df=ddf
    else:
        df=(ddf.loc[ddf['Folio'] == select_folio])
    df.reset_index(drop=True, inplace=True)
    
    ticker_list=df["Symbol"].unique().tolist()
    #ticker_list.insert(0,'All')
    select_ticker=st.sidebar.selectbox('Select Ticker',ticker_list,index=0)

    purchase_date=df[df['Symbol'] == select_ticker]['Trade Date'].min()
    #st.write("Today =",TODAY,"Purchase_Date =",purchase_date)
    hold_time=round((date.today()-datetime.date(purchase_date)).days/365,1)
select_etf=st.sidebar.text_input("Enter ETF/Index Symbol to Compare",'SPY')

Time_Period=("Hold Period","1y","3y","5y")
Time_Frame=st.sidebar.selectbox("**Select Timeframe**",Time_Period,index=1)
Time_Interval="1d"

if select_ticker:
    
    #@st.cache

    def load_data(ticker):
        if Time_Frame== "Hold Period":
            data=yf.download(ticker,start=purchase_date,end=TODAY,interval=Time_Interval)
        else:
            data=yf.download(ticker,period=Time_Frame,interval=Time_Interval)
        #data_growth=(data.pct_change().fillna(0)+1).cumprod()
        data.reset_index(inplace=True)
        return data

    data_load_state=st.text("Load data...")
    data=load_data(select_ticker)
    data = data.rename(columns = {'index':'Date'})
    data['Date'] = pd.to_datetime(data['Date'])
    data['Year']=data['Date'].dt.year
    data['Qtr']=data['Date'].dt.quarter
    data['YQ']="Q"+data['Qtr'].astype(str)+"/"+data['Year'].astype(str)
    data1=load_data(select_etf)
    data_load_state.text("Loading data...done!")

    ticker_quantity = df[df['Symbol'] == select_ticker]['Quantity'].sum()
    invest_value= df[df['Symbol'] == select_ticker]['Investment'].sum()
    purchase_price=invest_value/ticker_quantity
    
    current_price = data['Adj Close'].iloc[-1]
    target_price=df[df['Symbol'] == select_ticker]['Target Price'].mean()
    

    stock_growth=(data["Adj Close"].pct_change().fillna(0)+1).cumprod()
    index_growth=(data1["Adj Close"].pct_change().fillna(0)+1).cumprod()

    def plot_raw_data():
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'],y=data['Adj Close'],name=select_ticker))
        if select_etf:
            fig.add_trace(go.Scatter(x=data1['Date'],y=data1['Adj Close'],name=select_etf,yaxis='y2'))
        fig.layout.update(title_text="Time Series Data",xaxis_rangeslider_visible=False)
        fig.update_layout(yaxis2=dict(overlaying='y',side='right'))
        corr_coeff=data["Adj Close"].corr(data1["Adj Close"])
        fig.add_annotation(
        x=min(data['Date']),  # x position where the reference value is
        y=max(data['Adj Close']),  # y position of the reference value
        text=f"Corr. Coeff : {round(corr_coeff,2)}")

        st.plotly_chart(fig,use_container_width=True)

    def plot_growth_data():
        fig=go.Figure()
        fig.add_trace(go.Line(x=data.index,y=stock_growth,name=select_ticker))
        fig.add_trace(go.Line(x=data1.index,y=index_growth,name=select_etf))
        fig.layout.update(title_text="Growth Comparison",xaxis_rangeslider_visible=False)
        st.plotly_chart(fig,use_container_width=True)

    def plot_box_plot():
        fig = px.box(data_frame=data, x='YQ', y='Adj Close', title=select_ticker+'- Adj Close')
        
            
        fig.add_shape(type="line",
        x0=0,  # Start at the left edge of the plot
        y0=purchase_price,  # Y position of the reference line
        x1=1,  # End at the right edge of the plot
        y1=purchase_price,
        xref="paper",  # Use "paper" to cover the entire x-axis range
        yref="y",
        line=dict(color="Red",width=2,dash="dash"),name="Purchase")

        fig.add_shape(type="line",
        x0=0,  # Start at the left edge of the plot
        y0=current_price,  # Y position of the reference line
        x1=1,  # End at the right edge of the plot
        y1=current_price,
        xref="paper",  # Use "paper" to cover the entire x-axis range
        yref="y",
        line=dict(color="Orange",width=2,dash="dash"),name="Current")

        fig.add_shape(type="line", x0=0, y0=target_price, x1=1, y1=target_price, xref="paper", yref="y",
        line=dict(color="green",width=2,dash="dash"),name="Target")

        fig.add_trace(go.Scatter(
        x=[0,0,0],
        y=[purchase_price, current_price,target_price],
        text=["Purchase", "Current","Target"],
        mode="text",showlegend=False
        ))
        
        st.plotly_chart(fig,use_container_width=True)
 
    def CAGR(data):
        df = data.copy()
        df['daily_returns'] = df['Adj Close'].pct_change()
        df['cumulative_returns'] = (1 + df['daily_returns']).cumprod()
        trading_days = 252
        n = len(df)/ trading_days
        cagr = (df['cumulative_returns'].iloc[-1])**(1/n) - 1
        return cagr

    def volatility(data):
        df = data.copy()
        df['daily_returns'] = df['Adj Close'].pct_change()
        trading_days = 252
        vol = df['daily_returns'].std() * np.sqrt(trading_days)
        return vol

    def sharpe_ratio(data, rf):
        df = data.copy()
        sharpe = (CAGR(df) - rf)/ volatility(df)
        return sharpe 
        
    stock_name=f"**Selected Ticker =** **{select_ticker}**"
    hold_time=f"Hold Time = {hold_time} Yrs"

    st.markdown(stock_name)
    col1,col2,col3,col4,col5=st.columns(5)
    with col1:
        st.markdown("Holdings")
        st.subheader(round(ticker_quantity,0))
        st.markdown(hold_time)
               
    with col2:
        st.markdown("Purchase Cost ($)")
        st.subheader(round(purchase_price,2))
        st.markdown(round(purchase_price*ticker_quantity,2))   
    with col3:
        st.markdown("Curr. Price ($)")
        st.subheader(round(current_price,2))
        st.markdown(round(current_price*ticker_quantity,2))
    with col4:
        st.markdown("Tgt. Price ($)")
        st.subheader(round(target_price,2))
        st.markdown(round(target_price*ticker_quantity,2))
    with col5:
        st.markdown("Gain/Loss (%)")
        st.subheader(f"Act. : {round((current_price-purchase_price)/purchase_price*100,2)}")
        st.markdown(f"Tgt. : {round((target_price-purchase_price)/purchase_price*100,2)}")

    st.markdown("------")
    col1,col2,col3=st.columns(3)
    with col1:
        st.markdown("CAGR")
        st.subheader(f'{round(CAGR(data)*100,1)}%')
        
        st.markdown("Index CAGR")
        st.subheader(f'{round(CAGR(data1)*100,1)}%')
    with col2:
        st.markdown("Volatility")
        st.subheader(f'{round(volatility(data) * 100,1)}%')
        
        st.markdown("Index Volatility")
        st.subheader(f'{round(volatility(data1) * 100,1)}%')
    with col3:
        st.markdown("SHRP Ratio")
        st.subheader(round(sharpe_ratio(data,0.06) * 100,1))
        
        st.markdown("Index SHRP")
        st.subheader(round(sharpe_ratio(data1,0.06) * 100,1))
    st.markdown("------")
    col1,col2=st.columns(2)
    with col1:
        plot_growth_data()
    
    with col2:
        plot_box_plot()