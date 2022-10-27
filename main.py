import numpy as np
import pandas as pd
import time
import gzip
import plotly.graph_objects as go
import plotly.subplots as ms
import mymodule as mm

startcode = time.time()
    
candle = pd.DataFrame(columns =['time','open','high','low','close','volume'])
Wallet = {'time':[],'balance':[100]}
history = {
    'long':{'buy':{'time':[],'price':[]},'sell':{'time':[],'price':[]}},
    'short':{'buy':{'time':[],'price':[]},'sell':{'time':[],'price':[]}},
    'profitcut':0, 'losscut':0
}
localextrema = {
    'maximum':{'time':[],'price':[],'length':[]},
    'minimum':{'time':[],'price':[],'length':[]},
}
localextrema_ohlc = {
    'maximum':{'time':[],'price':[],'length':[]},
    'minimum':{'time':[],'price':[],'length':[]},
}
position = {'side':0,'size':100,'entry_price':100}
#indi(0time,1ma1,2ma2,3macd,4macd_sig,5macd_osc)

lin = {'time':[],'mid':[],'top':[],'bot':[]} 

permit_long = 0
permit_short= 0
start = 0
last = 1
for h in range(start,last):
    with gzip.open('/Users/jun/btcusd/%03d.gz' % h, 'rb') as f:
        data = f.readlines()

    daytics = []
    for row in data:
        daytics.append(row.decode('utf-8').split(','))
    
    del daytics[0]
    daytics.reverse()

    if h == start:
        price = float(daytics[1][4])
        tictime = float(daytics[1][0])
        minute = tictime//60
        k = 0
        ohlc_list = []
        volume = 0
        ohlc = np.array([[minute,price,price,price,price,price]])
        ohlc = np.delete(ohlc,0, axis=0)
        indicators = {
            'time':np.empty([0]),
            'ma1':np.empty([0]),
            'ma2':np.empty([0]),
            'macd':np.empty([0]),
            'macd_sig':np.empty([0]),
            'macd_osc':np.empty([0])
        }
    
    print(daytics[0])

    for i, row in enumerate(daytics):
        ohlc_list.append(float(row[4]))
        volume += (float(row[3]))

        if tictime == float(row[0]): continue
        else: 
            tictime = float(row[0])
            price = ohlc_list[-1]

        # i min canlde =========================
        if minute != tictime//60:
            k+=1 
            minute=tictime//60
            ohlc=mm.addcandle(ohlc,ohlc_list,volume,tictime)
            volume = 0
            ohlc_list = []
        # i min canlde =========================
        
            if k < 50: continue 
            mm.makingindi(ohlc,indicators,tictime)
            mm.minmax_macd(indicators,localextrema,10)
            volindi = mm.vol_vol(ohlc)
            mm.linearfit(ohlc,lin)
            #mm.minmax_ohlc(indicators,localextrema_ohlc,5)

            if not position['side'] and len(indicators['macd_osc'])>1:
                if indicators['macd_osc'][-1] < -70 and indicators['macd_osc'][-2] < indicators['macd_osc'][-1]:
                    targetprice = price - 1
                    permit_long = 1
                if indicators['macd_osc'][-1] > 700:
                    permit_short= 1
                    targetprice = price + 1

                

        if k < 50: continue 

        if position['side']:
            if position['side'] == 1:
                if price < position['losscut'] or price > position['profitcut']:  
                    mm.Order_Reduceonly(Wallet,position,history,price,tictime)
                    
            else:
                print('something wrong')
                if price > position['losscut'] or price < position['profitcut']:
                    mm.Order_Reduceonly(Wallet,position,history,price,tictime)
        else:
            if permit_long and price <= targetprice:
                mm.Order_Limit('long',position,history,targetprice,tictime)
                permit_long = 0
            elif permit_short and price > targetprice:
                mm.Order_Limit('short',position,history,targetprice,tictime)
                permit_short=0




        
        

                
df, candle = mm.candle_go(ohlc)
fig = ms.make_subplots(rows=2,cols=1,shared_xaxes=True,shared_yaxes=False,vertical_spacing=0.02)
ma10=go.Scatter(x=indicators['time'],y=indicators['ma1'],line=dict(color='blue',width=0.8),name='ma10')
#lin =go.Scatter(x=lin['time'],y=lin['mid'],line=dict(color='blue',width=0.8),name='lin')
lin_top =go.Scatter(x=lin['time'],y=lin['top'],line=dict(color='red',width=0.8),name='lintop')
lin_mid=go.Scatter(x=lin['time'],y=lin['mid'],line=dict(color='red',width=0.8),name='lintop')
lin_bot=go.Scatter(x=lin['time'],y=lin['bot'],line=dict(color='red',width=0.8),name='lintop')
history_SL = go.Scatter(x=history['long']['sell']['time'], y=history['long']['sell']['price'], mode ="markers", marker=dict(color='green',symbol= '6'), name='Sell long')
history_BL = go.Scatter(x=history['long']['buy']['time'], y=history['long']['buy']['price'], mode ="markers", marker=dict(color='red',symbol= '6'), name='buy long')
MACD_Oscil = go.Bar(x=indicators['time'], y=indicators['macd_osc'], marker_color='red', name='MACD_Oscil')
volume= go.Bar(x=df.index, y=df['volume'], marker_color='black', name='Volume')

fig.update_layout(title='BTCUSD', xaxis1_rangeslider_visible=False)
fig.add_trace(lin_top,row=1,col=1)
fig.add_trace(lin_mid,row=1,col=1)
fig.add_trace(lin_bot,row=1,col=1)
fig.add_trace(candle, row=1,col=1)
fig.add_trace(history_SL,row=1,col=1)
fig.add_trace(history_BL,row=1,col=1)
fig.add_trace(MACD_Oscil,row=2,col=1)
fig.show()


print("time :",time.time()-startcode)