import sys
import os
import numpy as np
import datetime as dt
import pandas as pd
from pandas_datareader import  data as web
from matplotlib import pyplot as plt

if len(sys.argv) == 2:
    ticker = sys.argv[1]
else:
    tickr = 'SPY'

start = dt.datetime(1999, 1, 2)
end = dt.datetime.today()

stock_csv = tickr + '.csv'

if os.path.isfile(stock_csv):
    stock = pd.read_csv(stock_csv)
    stock['Date'] = stock['Date'].map(lambda x: dt.datetime.strptime(str(x), "%Y-%m-%d"))
    stock.set_index('Date', inplace=True)
else:
    stock = web.DataReader(tickr, "yahoo", start, end)

stock.to_csv(stock_csv)

# stock.reset_index('Date', inplace=True)
price = stock['Adj Close'].tolist()
N = len(price)
pN = price[-1]

invprice = [1/x for x in price]
suminvprice = [sum(invprice[x:])/(N-x) for x in np.arange(0, N)]

onetimeinvestgrowth = [pN * x for x in invprice]
dollarcostavgrowth = [pN * x for x in suminvprice]

stock['onetimeinvestgrowth'] = onetimeinvestgrowth
stock['dollarcostavgrowth'] = dollarcostavgrowth

plt.plot(stock.index, stock['onetimeinvestgrowth'], label='One time investing')
plt.plot(stock.index, stock['dollarcostavgrowth'], label='Dollar Cost Avering')

# mng = plt.get_current_fig_manager()
# mng.full_screen_toggle()
plt.show()
