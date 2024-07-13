from stock_analyzer import StockAnalyzer

with open('tickers.txt', 'r') as f:
    tickers = [line.strip() for line in f if line.strip()]

StockAnalyzer.stockBatch(tickers, '2023-06-01')