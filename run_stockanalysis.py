import argparse
from stock_analyzer import StockAnalyzer
import calendar
from datetime import date

def get_third_friday(year=None, month=None):
    if year is None or month is None:
        # If no specific date is provided, use the current month
        today = date.today()
        year = today.year
        month = today.month
    else:
        # Ensure year and month are integers
        year = int(year)
        month = int(month)

    # Create a calendar object
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)

    # Get all the days in the month
    month_days = c.itermonthdates(year, month)

    # Find all Fridays in the month
    fridays = [day for day in month_days if day.weekday() == calendar.FRIDAY and day.month == month]

    # Get the third Friday
    third_friday = fridays[2] if len(fridays) >= 3 else None

    if third_friday:
        return third_friday.isoformat()
    else:
        return None

def get_user_input():
    use_current_month = input("Do you want to use the current month for option expiry? (Y/N): ").strip().lower()
    
    if use_current_month == 'y':
        return None, None
    else:
        while True:
            try:
                month = int(input("Enter desired month (MM): "))
                year = int(input("Enter desired year (YYYY): "))
                if 1 <= month <= 12 and 2000 <= year <= 2100:
                    return month, year
                else:
                    print("Invalid month or year. Please try again.")
            except ValueError:
                print("Invalid input. Please enter numbers only.")

def main():
    with open('tickers.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]

    month, year = get_user_input()

    if month and year:
        expiry = get_third_friday(year, month)
        print(f"Using custom expiry date: {expiry}")
    else:
        expiry = get_third_friday()
        print(f"Using current month's expiry date: {expiry}")

    StockAnalyzer.stockBatch(tickers, '2023-06-01', expiry=expiry)

if __name__ == "__main__":
    main()