import os
import yfinance as yf
import ta
import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import date, datetime 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
import calendar

class StockAnalyzer:
    def __init__(self, ticker, start_date, end_date=None, expiry=None):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date if end_date else date.today().isoformat()
        self.expiry = expiry if expiry else self._get_third_friday_of_current_month()
        self.stock_data = None
        self.option_chain = None
        self.indicators = {}
        # Create the directory for the ticker if it doesn't exist
        self.directory = f'data/{self.ticker}'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def _get_third_friday_of_current_month(self):
        today = date.today()
        month = today.month
        year = today.year
        c = calendar.Calendar(firstweekday=calendar.SUNDAY)

        monthcal = c.monthdatescalendar(year, month)
        third_friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]
        return third_friday.isoformat()

    # Calculate Probability of Profit (POP)
    def black_scholes(self, S, K, T, sigma, optionType, r=0.02):
        if sigma == 0 or T == 0:
            if optionType == 'call':
                return 1.0 if S > K else 0.0
            else:
                return 1.0 if S < K else 0.0
        
        try:
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            if optionType == 'call':
                return norm.cdf(d1)
            else:
                return norm.cdf(-d1)
        except Exception as e:
            print(f"Error in black_scholes calculation: {e}")
            return 0.0  # Return a default value or handle the exception as needed

    def download_data(self):
        self.stock_data = yf.download(self.ticker, start=self.start_date, end=self.end_date)
        self.close_price = self.stock_data['Close'].iloc[-1]

    def download_option(self):
        self.option_chain = yf.Ticker(self.ticker).option_chain(self.expiry)
        self.puts = self.option_chain.puts.drop(['lastPrice','change','percentChange','inTheMoney', 'contractSize', 'currency'], axis=1)
        self.puts['last_price'] = self.close_price
        # Want to filter out some deeply far ITM/OTM strikes to save token count.
        self.puts = self.puts[(self.puts['strike'] > self.close_price * 0.7) & (self.puts['strike'] < self.close_price * 1.5)]
        self.puts['expiry_date'] = pd.to_datetime(self.expiry)
        self.puts['InTheMoney_probability'] = self.puts.apply(lambda row: self.black_scholes(
            S = row['last_price'], 
            K = row['strike'], 
            T = (row['expiry_date'] - datetime.now()).days / 365,  
            sigma = row['impliedVolatility'], 
            optionType = 'put'
            ), axis = 1)
        self.calls = self.option_chain.calls.drop(['lastPrice','change','percentChange','inTheMoney', 'contractSize', 'currency'], axis=1)
        self.calls['last_price'] = self.close_price
        self.calls = self.calls[(self.calls['strike'] > self.close_price * 0.5) & (self.calls['strike'] < self.close_price * 1.8)]
        self.calls['expiry_date'] = pd.to_datetime(self.expiry)
        self.calls['InTheMoney_probability'] = self.calls.apply(lambda row: self.black_scholes(
            S = row['last_price'], 
            K = row['strike'], 
            T = (row['expiry_date'] - datetime.now()).days / 365, 
            sigma = row['impliedVolatility'], 
            optionType = 'call'
            ), axis=1)

    def calculate_indicators(self):
        if self.stock_data is not None:
            # Ensure that local maxima and minima are calculated over a meaningful window
            window_size = 30

            # Calculate the recent high and low over the specified window
            recent_max = self.stock_data['Close'][-window_size:].max()
            recent_min = self.stock_data['Close'][-window_size:].min()
            
            # Calculate Fibonacci retracement levels
            diff = recent_max - recent_min
            fib_ratios = [1.0, 0.786, 0.618, 0.5, 0.382, 0.236, 0]
            fib_levels = {f'Fib_{ratio}': recent_max - diff * ratio for ratio in fib_ratios}

            # Add Fibonacci levels to the dataframe
            for key, value in fib_levels.items():
                self.stock_data[key] = value

            # Calculate other indicators
            self.stock_data['EMA24'] = ta.trend.ema_indicator(self.stock_data['Close'], window=24)
            self.stock_data['SMA50'] = ta.trend.sma_indicator(self.stock_data['Close'], window=50)
            self.stock_data['SMA200'] = ta.trend.sma_indicator(self.stock_data['Close'], window=200)
            self.stock_data['RSI'] = ta.momentum.rsi(self.stock_data['Close'], window=14)
            self.stock_data['MFI'] = ta.volume.money_flow_index(self.stock_data['High'], self.stock_data['Low'], self.stock_data['Close'], self.stock_data['Volume'], window=14)
            
            # Store indicators in self.indicators dictionary
            self.indicators = {
                'EMA24' : self.stock_data['EMA24'],
                'SMA50': self.stock_data['SMA50'],
                'SMA200': self.stock_data['SMA200'],
                'RSI': self.stock_data['RSI'],
                'MFI': self.stock_data['MFI'],
                **{key: self.stock_data[key] for key in fib_levels.keys()},
            }
        else:
            raise ValueError("Stock data is not downloaded yet. Please call download_data() first.")
    
    def get_indicators(self):
        if not self.indicators:
            self.calculate_indicators()
        return self.indicators
    
    def get_stock_data(self):
        return self.stock_data
    
    def stock_to_csv(self, filename):
        if self.stock_data is not None:
            start_date = pd.to_datetime(self.start_date).strftime('%m%d%Y')
            end_date = pd.to_datetime(self.end_date).strftime('%m%d%Y')
            self.stock_data.to_csv(f'{self.directory}/{filename}_{start_date}_{end_date}.csv')
        else:
            raise ValueError("Stock data is not available. Please call download_data() first.")
    
    def option_to_csv(self, filename):
        if self.option_chain is not None:
            self.calls.to_csv(f'{self.directory}/{filename}_calls_{self.expiry}.csv')
            self.puts.to_csv(f'{self.directory}/{filename}_puts_{self.expiry}.csv')
        else:
            raise ValueError("Option chain data is not available. Please call download_option() first.")
        
    
    def plot_stock_data(self, filename):
        if self.stock_data is not None:
            # Create a copy of the stock data
            stock_data_copy = self.stock_data.copy()

            # Convert the index to datetime if it's not already
            if not isinstance(stock_data_copy.index, pd.DatetimeIndex):
                stock_data_copy.index = pd.to_datetime(stock_data_copy.index)

            # Reset the index to obtain integer indices
            stock_data_copy.reset_index(inplace=True)

            # Create the candlestick data
            ohlc = stock_data_copy[['Date', 'Open', 'High', 'Low', 'Close']].values

            # Convert dates to matplotlib format
            ohlc[:, 0] = mdates.date2num(ohlc[:, 0])

            # Create the candlestick plot with a larger figure size
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(40, 28), gridspec_kw={'height_ratios': [4, 1, 1]})

            candlestick_ohlc(ax1, ohlc, width=0.6, colorup='g', colordown='r')

            # Plot the indicators on the first subplot
            ax1.plot(stock_data_copy['Date'], self.stock_data['EMA24'], label='EMA24', linestyle='--')
            ax1.plot(stock_data_copy['Date'], self.stock_data['SMA50'], label='SMA50', linestyle='--')
            ax1.plot(stock_data_copy['Date'], self.stock_data['SMA200'], label='SMA200', linestyle='--')

            # Plot Fibonacci levels on the first subplot
            fib_colors = ['red', 'orange', 'olivedrab', 'green', 'blue', 'purple', 'brown']
            fib_ratios = [1.0, 0.786, 0.618, 0.5, 0.382, 0.236, 0]
            for i, ratio in enumerate(fib_ratios):
                fib_level = self.stock_data[f'Fib_{ratio}'].iloc[-1]
                ax1.axhline(y=fib_level, label=f'Fibonacci Retracement {ratio*100:.1f}%', color=fib_colors[i], linestyle=':')

                # Add price labels to Fibonacci levels on the first subplot
                ax1.text(stock_data_copy['Date'].iloc[-29], fib_level, f'{fib_level:.2f}', fontsize=16, color=fib_colors[i],
                        va='center', ha='right', bbox=dict(facecolor='white', edgecolor=fib_colors[i], boxstyle='round'))

            # Highlight the last data point on the first subplot
            first_date = self.stock_data.index[0]
            filename_fd = first_date.strftime('%m%d%Y')
            last_date = self.stock_data.index[-1]
            last_close = self.stock_data['Close'].iloc[-1]
            last_rsi = self.stock_data['RSI'].iloc[-1]
            last_vol = self.stock_data['Volume'].iloc[-1]
            formatted_date = last_date.strftime('%Y-%m-%d')
            filename_ld = last_date.strftime('%m%d%Y')
            ax1.plot(mdates.date2num(last_date), last_close, marker='o', markersize=8, color='red')
            ax1.annotate(f'Date: {formatted_date}\nLast Close: {last_close:.2f}', xy=(mdates.date2num(last_date), last_close),
                        xytext=(14, 20), textcoords='offset points',
                        fontsize=16, color='red',
                        bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

            # Set x-axis labels to display every month on the first subplot
            months = mdates.MonthLocator()
            months_fmt = mdates.DateFormatter('%m %Y')
            ax1.xaxis.set_major_locator(months)
            ax1.xaxis.set_major_formatter(months_fmt)

            # Customize the first subplot
            ax1.set_title(f'Stock Data and Indicators for {self.ticker}')
            ax1.set_ylabel('Price')
            ax1.legend(loc='upper left')
            ax1.grid(True)

            # Plot the RSI on the second subplot
            ax2.plot(stock_data_copy['Date'], self.stock_data['RSI'], label='RSI', color='purple')
            ax2.axhline(y=70, color='red', linestyle='--', label='Overbought')
            ax2.axhline(y=30, color='green', linestyle='--', label='Oversold')
            ax2.fill_between(stock_data_copy['Date'], self.stock_data['RSI'], 70, where=(self.stock_data['RSI'] >= 70), alpha=0.5, color='red')
            ax2.fill_between(stock_data_copy['Date'], self.stock_data['RSI'], 30, where=(self.stock_data['RSI'] <= 30), alpha=0.5, color='green')
            ax2.plot(mdates.date2num(last_date), last_rsi, marker='o', markersize=8, color='red')
            ax2.annotate(f'Date: {formatted_date}\nLast RSI: {last_rsi:.2f}', xy=(mdates.date2num(last_date), last_rsi),
                        xytext=(14, 20), textcoords='offset points',
                        fontsize=16, color='red',
                        bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))
            ax2.set_ylabel('RSI')
            ax2.legend(loc='upper left')
            ax2.grid(True)

            # Set x-axis labels to display every month on the second subplot
            ax2.xaxis.set_major_locator(months)
            ax2.xaxis.set_major_formatter(months_fmt)

            # Plot the volume on the third subplot
            ax3.bar(stock_data_copy['Date'], stock_data_copy['Volume'], width=0.6, color='gray')
            ax3.plot(stock_data_copy['Date'], stock_data_copy['Volume'], color='blue')
            ax3.plot(mdates.date2num(last_date), last_vol, marker='o', markersize=8, color='red')
            ax3.annotate(f'Date: {formatted_date}\nLast Volume: {last_vol:.2f}', xy=(mdates.date2num(last_date), last_vol),
                        xytext=(14, 20), textcoords='offset points',
                        fontsize=16, color='red',
                        bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))
            ax3.set_ylabel('Volume')
            ax3.grid(True)

            # Set x-axis labels to display every month on the third subplot
            ax3.xaxis.set_major_locator(months)
            ax3.xaxis.set_major_formatter(months_fmt)

            # Adjust the spacing between subplots
            plt.tight_layout()

            # Set the x-axis limits to show the entire date range
            ax1.set_xlim(stock_data_copy['Date'].iloc[0], stock_data_copy['Date'].iloc[-1])
            ax2.set_xlim(stock_data_copy['Date'].iloc[0], stock_data_copy['Date'].iloc[-1])
            ax3.set_xlim(stock_data_copy['Date'].iloc[0], stock_data_copy['Date'].iloc[-1])

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)

            plt.savefig(f'{self.directory}/{filename}_{filename_fd}_{filename_ld}', bbox_inches='tight')
            plt.close()
        else:
            raise ValueError("Stock data is not available. Please call download_data() first.")

    @classmethod
    def stockBatch(cls, tickers, start_date, end_date=None, expiry=None):
        for ticker in tickers:
            try:
                analyzer = cls(ticker, start_date, end_date, expiry)
                analyzer.download_data()
                analyzer.calculate_indicators()
                analyzer.stock_to_csv(f"{ticker}_stock_data")
                analyzer.plot_stock_data(f"{ticker}_stock_data_plot")
                analyzer.download_option()
                analyzer.option_to_csv(ticker)
                print(f"Analysis completed for {ticker}")
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")