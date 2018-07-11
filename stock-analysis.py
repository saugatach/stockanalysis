import sys
import os
import tkinter as tk

import pandas as pd
import datetime as dt
import numpy as np

# import datatreader to import Yahoo Finance data
from pandas_datareader import data as web

# Import matplotlib
from matplotlib import pyplot as plt
# Seaborn for plotting and styling
import seaborn as sns

# make the plots nicer
from matplotlib import style
style.use('ggplot')

# print more columns of dataframes. Without this option python will wrap after 5 columns.
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)

# global variables that can be reused
now = dt.datetime.now()

# -------------------------------------------- FUNCTIONS --------------------------------------------

def createmetadatafile(tickr, start, end):

    # temp = pd.DataFrame([[tickr, start, end]])
    temp = pd.DataFrame([[tickr, start, end]], columns=['Stock', 'Start Date', 'End Date'])

    # set first column as index otherwise pandas will append an extra column as index
    temp.set_index('Stock', inplace=True)

    print(temp)


    temp.to_csv('metadata.csv')
    # -------------------------------------

def getdata_from_stock_dataframe(stock, start, end):

    startloc = stock.index[(stock.Date == start)]
    endloc =  stock.index[(stock.Date == end)]

    stock_part = stock.iloc[startloc:endloc]

    return stock_part


def getyahoodata(tickr, start, end):

    stock_csv = tickr + '.csv'
    dir_path = os.path.dirname(os.path.realpath(__file__))


    stock_csv = os.path.join(dir_path, 'data_stocks', stock_csv)

    # read metadata file first to see the timeframe before even opening tickr.csv file

    fetchdata = True

    if os.path.isfile(stock_csv):

        stock_csv_data = pd.read_csv(stock_csv)
        # only select relevant columns
        stock = stock_csv_data[['Date', 'Adj Close', 'Volume']]
        # release memory
        stock_csv_data = []

        csv_start_date, csv_end_date = dt.datetime.strptime(stock['Date'].iloc[0], "%Y-%m-%d"), \
                                       dt.datetime.strptime(stock['Date'].iloc[-1], "%Y-%m-%d")

        # print(csv_start_date, csv_end_date)

        if os.path.isfile('metadata.csv'):
            metadata = pd.read_csv('metadata.csv')
            tickrlocation = metadata['Stock'] == tickr

            # if the tickr symbol is found in metadata file then extract the start and end date from it
            if tickrlocation.sum():
                # if duplicate entries exist, then select the last one
                tickrdata = list(metadata[tickrlocation].iloc[-1][1:3])
                metadatastartdate, metadataenddate = map(lambda x: dt.datetime.strptime(x, "%Y-%m-%d"), tickrdata)
            else:
                metadatastartdate, metadataenddate = csv_start_date, csv_end_date
        else:
            # if the metadata file doesn't exist then create one
            metadatastartdate, metadataenddate = csv_start_date, csv_end_date
            createmetadatafile(tickr, metadatastartdate, metadataenddate)

        if start >= csv_start_date and end <= csv_end_date:
            # when the query is run during trading hours, the same day data needs to be updated
            # verify if now() is between 9.30 am and 4.00 pm EST
            stock = getdata_from_stock_dataframe(stock, start, end)
    else:
        fetchdata = True


    if fetchdata == True:
        # get Yahoo Data
        print("Getting data from Yahoo Finance .....")
        stock = web.DataReader(tickr, "yahoo", start, end)
        # u pdate metadata
        if os.path.isfile('metadata.csv'):
            metadata = pd.read_csv('metadata.csv', index_col='Stock')
            # strip out the time from datetime object before storing it in file
            metadata.loc[tickr] = (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
            metadata.to_csv('metadata.csv')
        else:
            # file doesn't exist, create one
            createmetadatafile(tickr, start, end)

    # export stock data to CSV file
    stock.to_csv(stock_csv)
    return stock

# -------------------------------------------- START OF CODE --------------------------------------------
# set defaults
# if no stock ticker has been passed as an argv then set SPY as the default ticker
if len(sys.argv) == 2:
        tickr = sys.argv[1]
        start = dt.datetime(2016, 1, 2)
        # now = dt.datetime.now()
        end = dt.datetime(now.year, now.month, now.day)
else:
        tickr = input('Enter stock ticker (default[SPY]): ')
        if tickr == '':
            tickr = "SPY"

        startq = input('Enter start date as mm/dd/yyyy (default 1/2/2016): ')
        if startq == '':
            start = dt.datetime(2016, 1, 2)
        else:
            try:
                start = dt.datetime.strptime(startq, "%m/%d/%Y")
            except:
                print("Error in format")
                exit(-1)


        endq = input('Enter end date as mm/dd/yyyy (default TODAY): ')
        if endq == '':
            now = dt.datetime.now()
            end = dt.datetime(now.year, now.month, now.day)
        else:
            try:
                end = dt.datetime.strptime(endq, "%m/%d/%Y")
            except:
                print("Error in format")
                exit(-1)

tickr = tickr.upper()

stock = getyahoodata(tickr, start, end)


# create SMA columns
# min_periods starts averaging from day-0 not day-200 so it is always continuous with no initial 200-day gap
stock['21SMA'] = stock['Adj Close'].rolling(window=21, min_periods=0).mean()
stock['200SMA'] = stock['Adj Close'].rolling(window=200, min_periods=0).mean()

# sd = stock['21SMA'].std()
tempstd = stock['Adj Close'].rolling(window=200, min_periods=0).std()

# Create Bollinger bands
stock['Bollinger1'] = stock['21SMA'] + tempstd
stock['Bollinger2'] = stock['21SMA'] - tempstd

sns.set_style('darkgrid')

# daily change (delta)
stock['delta'] = stock['Adj Close'].diff()

ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=5, colspan=1)
ax2 = plt.subplot2grid((7, 1), (5, 0), rowspan=2, colspan=1, sharex=ax1)

# PLOT STOCK
ax1.plot(stock.index, stock['Adj Close'], label='Adj. Close', linewidth=1, color='blue')
ax1.plot(stock.index, stock['200SMA'], label='200day SMA', linewidth=1, color='darkred')
ax1.plot(stock.index, stock['21SMA'], label='21day SMA', linewidth=1, color='mediumseagreen')

# fill the Bollinger bands
ax1.plot(stock.index, stock['Bollinger1'], label='Bollinger bands', linewidth=1, color='darkkhaki')
ax1.plot(stock.index, stock['Bollinger2'], label='', linewidth=1, color='darkkhaki')
xfillcoord = stock['Bollinger1'].append(stock['Bollinger2'][::-1])
yfillcoord = stock.index.append(stock.index)

ax1.fill(xfillcoord, color='gold', alpha=0.1)

# position the legend to upper left corner of the plot
ax1.legend(loc='upper left', bbox_to_anchor=(0, 1.00),  shadow=True, ncol=1)

# add stock stats pulled from MorningStar or Yahoo Finance
stockstats = 'Current: $' + str(np.round(stock['Adj Close'][-1], 2)) + '\n' + '52wk hi: $' + \
             str(np.round(stock['Adj Close'][-260:-1].max(), 2)) + '\n' + '52wk lo: $' + \
             str(np.round(stock['Adj Close'][-260:-1].min(), 2))

ax1.text(0, 0.5, stockstats , fontsize=11, bbox=dict(facecolor='gold', alpha=0.1), horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)

ax2.plot(stock.index, stock['delta'])

plt.suptitle(tickr+": Price moves between "+start.strftime("%m/%d/%y")+" and "+end.strftime("%m/%d/%y"))

# show plot in a maximized window
mng = plt.get_current_fig_manager()
mng.full_screen_toggle()

plt.show()

