# Stock Insight

Stock Insight is a comprehensive tool for analyzing stock data, calculating technical indicators, and evaluating option probabilities using the Black-Scholes model. It allows users to download stock data, calculate various technical indicators, and visualize the data with detailed plots.

## Features

- Download stock data using Yfinance package for one or more tickers within a given date range.
- Calculate technical indicators such as EMA, SMA, RSI, MFI, and Fibonacci retracement levels.
- Download option chain data and calculate the probability of options being in the money using the Black-Scholes model.
- Generate detailed plots with candlestick charts, indicators, and annotations.
- Save stock and option data to CSV files for further analysis.
- Download Important economic events and data in CSV.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/kcwtimothy/stock-insight.git
   cd stock-insight
   ```


2. Create virtual environment:
   ```
   python -m venv 'yourvenvname'
   ```
   Linux:
   ```
    source venv/bin/activate
   ```
   Windows:
   ```  
    venv\Scripts\activate
   ```

3. Install dependencies
   ```
    pip install -r requirements.txt
   ```

## Preparation

- You can edit the default text file 'tickers.txt' to add/remove tickers symbol for stock and option chain data.
- You can edit the default text tile 'eco_calendar_date.txt' to modify the range of events of data you want to capture as csv.
- The default start date of stock chart is set to '2023-06-01' for readability. You need to access and modify run_stockanalysis.py yourself to change this date.
- Stockanalyzer on default will always capture the most up to date stock data and 3rd friday of the current month.

## How to Use?

- After editing the 'tickers.txt' & 'eco_calendar_date.txt' for your own need, simply click & run 'run_all.bat' file.Then it will ask you whether to download current's month option information (Y/N)?
   - If 'Y', it will return the date of 3rd friday of current month.
   - If 'N', it will ask you to input  month & year for your desired option chain. 
- This is going to achieve a few things:
   - Download stock data up to the current date
   - Download option chain data on the third friday of the month(Opex date). ITM probability is calculated based on black scholes.
   - Automatically create stock data plot with technical indicators and labels.
   - Scrap the economic events data.
- The downloaded data will be automatically stored under 'data' folder.

## Known bugs

- Though there's logic to deal with the pop up ads, sometimes eco_calendar.py could still be blocked by the pop-up. Re-run it another time will solve this problem.


## Acknowledgements
    - yfinance for stock data retrieval.
    - ta for technical analysis indicators.
    - mplfinance for candlestick chart plotting.
