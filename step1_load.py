import yfinance as yf

data = yf.download(["BZ=F", "ZAR=X"], start="2016-01-01")

print(data.head())
print(data.shape)
print(data.columns)
print(data.index.min())
print(data.index.max())
print(data.isna().sum())