import yfinance as yf
import os

data = yf.download(["BZ=F", "ZAR=X"], start="2016-01-01")
# 2. Keep only the closing prices and give the columns clear names
close = data["Close"]
close = close.rename(columns={"BZ=F": "oil_usd", "ZAR=X": "usd_zar"})
print(close.head())

# 3. Look at the days where oil has no price
print(close[close["oil_usd"].isna()].head(10))

# 4. Fill gaps by copying the previous day's price forward
close = close.ffill()
print(close.isna().sum())      # what is still missing?

# 5. Remove any rows that are still missing
close = close.dropna()
print(close.isna().sum())      # should now be all zeros

# 6. Convert daily prices to monthly averages
monthly = close.resample("MS").mean()
print(monthly.head())
print(monthly.shape)

# 7. Save the result
os.makedirs("data", exist_ok=True)
monthly.to_csv("data/monthly_oil_rand.csv")
print("Saved!")
