import random
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO


class Strategy:
  
  def __init__(self, start_date, end_date, options_data, underlying) -> None:
    self.capital : float = 100_000_000
    self.portfolio_value : float = 0

    self.start_date : datetime = start_date
    self.end_date : datetime = end_date
  
    self.options : pd.DataFrame = pd.read_csv(options_data)
    self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

    self.underlying = pd.read_csv(underlying)
    self.underlying.columns = self.underlying.columns.str.lower()

  def get_third_friday(year, month) -> datetime:
    # Create a date object for the first day of the month
    first_day = datetime.date(year, month, 1)
    
    # Calculate the first Friday of the month
    first_friday = first_day + datetime.timedelta(days=(4 - first_day.weekday() + 7) % 7)
    
    # The third Friday is two Fridays after the first
    third_friday = first_friday + datetime.timedelta(weeks=2)
    return third_friday

  def next_third_friday(self, input_date) -> datetime:
    # Extract year and month from the input datetime object
    year = input_date.year
    month = input_date.month

    # If the date is after the third Friday, move to the next month
    if input_date > self.get_third_friday(year, month):
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Find the next third Friday
    return self.get_third_friday(year, month)

  def get_weekday_start(date) -> datetime:
    if date.weekday() == 6:  # Sunday
      return date + timedelta(days=1)
    elif date.weekday() == 5:  # Saturday
      return date + timedelta(days=2)
    else:
      return date
    
  def calculate_mean(numbers):
    if not numbers:  # Check for an empty list
        return 0
    return sum(numbers) / len(numbers)

  def generate_orders(self) -> pd.DataFrame:
    tenDayAvg = []
    fiveDayAvg = []
    currDate = self.get_weekday_start(self.start_date)

    # GETTING AVGS LOADED
    for i in range(1,10):
      strDate = currDate.strftime("%Y-%m-%d")
      dailyData = self.underlying[strDate in self.underlying["date"]]
      if not dailyData.empty:
        avgPrice = dailyData["adj close"].mean()
        if i > 5:
          fiveDayAvg.append(avgPrice)
        tenDayAvg.append(avgPrice)
      currDate += timedelta(days=1)
      currDate = self.get_weekday_start(currDate)

    tenDayGreater = False
    if tenDayAvg > fiveDayAvg:
      tenDayGreater = True
    else: 
      tenDayGreater = False

    sellBear = [] # sell positions in this list if bearish signal
    sellBull = [] # sell positions in this list if bullish signal
    allOrders = [] # keep all orders here to submit at the end

    while currDate >= self.end_date:
      fiveDayAvg.pop(0)
      tenDayAvg.pop(0)
      strDate = currDate.strftime("%Y-%m-%d")
      dailyData = self.underlying[strDate in self.underlying["date"]]
      if not dailyData.empty:
        avgPrice = dailyData["adj close"].mean()
        if i > 5:
          fiveDayAvg.append(avgPrice)
        tenDayAvg.append(avgPrice)
      
      thirdFri = self.get_third_friday(self, currDate)
      optionExpiry = thirdFri.strftime("SPX   %y%m%d")
      dailyOptionsData = self.options[strDate in self.options["data"]]
      # WE EXECUTE STRATEGY HERE!!
      if tenDayGreater and (self.calculate_mean(tenDayAvg) < self.calculate_mean(fiveDayAvg)):
        tenDayGreater = False
        callExpiry = optionExpiry + "C"
        DesiredBuy = dailyOptionsData[(callExpiry in self.options["symbol"])]
        
        order_size = 0
        if DesiredBuy["ask_sz_00"] > 100:
          order_size = 100
        else:
          order_size = DesiredBuy["ask_sz_00"]
        order = {
          "datetime" : DesiredBuy["ts_recv"],
          "option_symbol" : DesiredBuy["symbol"],
          "action" : "B",
          "order_size" : order_size
        }
        allOrders.append(order)
        bullOrder = {
          "datetime" : DesiredBuy["ts_recv"],
          "option_symbol" : DesiredBuy["symbol"],
          "action" : "S",
          "order_size" : order_size
        }
        sellBull.append(bullOrder)

        if not len(sellBear) == 0:
          putExpiry = optionExpiry + "P"
          DesiredSell = dailyOptionsData[(putExpiry in self.options["symbol"])]
          newOrder = sellBear[0]
          newOrder["datetime"] = DesiredSell["ts_recv"]
          allOrders.append(sellBear[0])
          sellBear.pop(0)
          # SELL BEARISH SIGNAL
      elif not tenDayGreater and (self.calculate_mean(tenDayAvg) > self.calculate_mean(fiveDayAvg)):
        tenDayGreater = True
        putExpiry = optionExpiry + "P"
        DesiredBuy = dailyOptionsData[(putExpiry in self.options["symbol"])]
        
        order_size = 0
        if DesiredBuy["ask_sz_00"] > 100:
          order_size = 100
        else:
          order_size = DesiredBuy["ask_sz_00"]
        order = {
          "datetime" : DesiredBuy["ts_recv"],
          "option_symbol" : DesiredBuy["symbol"],
          "action" : "B",
          "order_size" : order_size
        }
        allOrders.append(order)
        bearOrder = {
          "datetime" : DesiredBuy["ts_recv"],
          "option_symbol" : DesiredBuy["symbol"],
          "action" : "S",
          "order_size" : order_size
        }
        sellBear.append(bearOrder)

        if not len(sellBull) == 0:
          callExpiry = optionExpiry + "C"
          DesiredSell = dailyOptionsData[(callExpiry in self.options["symbol"])]
          newOrder = sellBull[0]
          newOrder["datetime"] = DesiredSell["ts_recv"]
          allOrders.append(newOrder)
          sellBull.pop(0)
          # SELL BULLISH SIGNAL
          
      currDate += timedelta(days=1)
      currDate = self.get_weekday_start(currDate)

    return pd.DataFrame(allOrders)
    # orders = []
    # num_orders = 1000
    
    # for _ in range(num_orders):
    #   row = self.options.sample(n=1).iloc[0]
    #   action = random.choice(["B", "S"])
      
    #   if action == "B":
    #     order_size = random.randint(1, int(row["ask_sz_00"]))
    #   else:
    #     order_size = random.randint(1, int(row["bid_sz_00"]))

    #   assert order_size <= int(row["ask_sz_00"]) or order_size <= int(row["bid_sz_00"])
      
    #   order = {
    #     "datetime" : row["ts_recv"],
    #     "option_symbol" : row["symbol"],
    #     "action" : action,
    #     "order_size" : order_size
    #   }
    #   orders.append(order)
    
    # return pd.DataFrame(orders)