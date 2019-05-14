# this is a class file to grab Yahoo Finance data. This file is not executable
# ver 3.0

import os
import pandas as pd
import datetime as dt
import pytz
# import datatreader to import Yahoo Finance data
from pandas_datareader import data as web


# global variables that can be reused
tz = pytz.timezone('America/New_York')
now = dt.datetime.now(tz=tz)
today = dt.datetime(now.year, now.month, now.day)

# -------------------------------------------- CLASS --------------------------------------------
class GetStockData:

    def __init__(self, tickr='SPY', path='./data_stocks/'):

        self.tickr = tickr

        self.csvfile = path + tickr + '.csv'

        if os.path.isfile(self.csvfile):
            self.df, self.start = self.loadcsv(self.csvfile)
        else:
            self.df = pd.DataFrame()
            self.start = dt.datetime(1975, 1, 2)

        if self.start < today:
            print("Getting from yahoo finance the date range ... " + str(self.start) + " to " + str(today) )
            self.df_yahoo = web.DataReader(tickr, "yahoo", self.start, today)
        else:
            self.df_yahoo = pd.DataFrame()

        self.stockdata = self.mergedb(self.df, self.df_yahoo)

        # export stock data to CSV file
        self.stockdata.to_csv(self.csvfile)

    def loadcsv(self, csvfile):

        data = pd.read_csv(csvfile)
        # get the first and last values of the Date column - these are the csv_start_date, csv_end_date
        startdate, enddate = data['Date'].iloc[0], data['Date'].iloc[-1]
        # Date column not Datetime object. Either convert each row to datetime individually or use pd.to_datetime()
        # data['Date'] = data['Date'].map(lambda x: dt.datetime.strptime(str(x), "%Y-%m-%d"))
        data['Date'] = pd.to_datetime(data['Date'])
        csvdata = data.set_index('Date')

        return csvdata, self.dateformat(enddate)


    def mergedb(self, left, right):
        df = pd.concat([left[:-1], right])
        df = df.drop_duplicates()
        return df

    def getdata(self, startdate, enddate):
        return self.extractpartofdf(self.stockdata, startdate, enddate)

    def extractpartofdf(self, stock, start, end):

        # market might be closed on the dates. So we have to find the closest dates
        afterstartdate = stock.index >= start
        beforeenddate = stock.index <= end

        selectstockrange = afterstartdate * beforeenddate
        stock_part = stock[selectstockrange]

        return stock_part

    def dateformat(self, date):
        # Checks if date is in mm/dd/yyy format"""
        if not (isinstance(date, dt.date) or isinstance(date, dt.datetime)):
            try:
                date = dt.datetime.strptime(date, "%Y-%m-%d")
            except:
                print("Error in date format")
                exit(-1)
        return date

    def isstockexchangeopen(self):
        # today is already defined as global variable
        if 9 < now.hour < 16:
            return True
        else:
            return False



