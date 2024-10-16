import random
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO


class Strategy:
  
  def __init__(self) -> None:
    self.capital : float = 100_000_000
    self.portfolio_value : float = 0

    self.start_date : datetime = datetime(2024, 1, 1)
    self.end_date : datetime = datetime(2024, 3, 30)
  
    self.options : pd.DataFrame = pd.read_csv("data/cleaned_options_data.csv")
    self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

    self.underlying = pd.read_csv("data/underlying_data_hour.csv")
    self.underlying.columns = self.underlying.columns.str.lower()

  def get_weekday_start(date) -> datetime:
    if date.weekday() == 6:  # Sunday
      return date + timedelta(days=1)
    elif date.weekday() == 5:  # Saturday
      return date + timedelta(days=2)
    else:
      return date

  def generate_orders(self) -> pd.DataFrame:
    tenDayAvg = []
    fiveDayAvg = []
    currDate = self.get_weekday_start(self.start_date)

    # GETTING AVGS LOADED
    for i in range(1,10):
      strDate = currDate.strftime("%Y-%m-%d")
      dailyData = self.underlying[self.underlying["date"] == strDate]
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
    allOrders = []

    while currDate >= self.end_date:
      fiveDayAvg.pop(0)
      tenDayAvg.pop(0)
      strDate = currDate.strftime("%Y-%m-%d")
      dailyData = self.underlying[self.underlying["date"] == strDate]
      if not dailyData.empty:
        avgPrice = dailyData["adj close"].mean()
        if i > 5:
          fiveDayAvg.append(avgPrice)
        tenDayAvg.append(avgPrice)
      
      # WE EXECUTE STRATEGY HERE!!
      if tenDayGreater and (tenDayAvg < fiveDayAvg):
        tenDayGreater = False
      elif not tenDayGreater and (tenDayAvg > fiveDayAvg):
        tenDayGreater = True


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