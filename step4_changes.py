import pandas as pd
import matplotlib.pyplot as plt

# Load and drop the partial month, as before
monthly = pd.read_csv("data/monthly_oil_rand.csv", index_col=0, parse_dates=True)
LAST_COMPLETE_MONTH = "2026-09-01"   # October 2026 was incomplete when the data was downloaded
monthly = monthly.loc[:LAST_COMPLETE_MONTH]

# Monthly percentage change for each series
changes = monthly.pct_change().dropna() * 100
changes.columns = ["oil_change_pct", "rand_change_pct"]
print(changes.head())
print(changes.describe())

# Correlation of the changes
print(changes.corr())

# Biggest moves
print("Biggest oil fall:", changes["oil_change_pct"].idxmin(), changes["oil_change_pct"].min())
print("Biggest oil rise:", changes["oil_change_pct"].idxmax(), changes["oil_change_pct"].max())

# Scatter plot of changes
plt.figure(figsize=(7, 5))
plt.scatter(changes["oil_change_pct"], changes["rand_change_pct"], alpha=0.6)
plt.axhline(0, color="grey", linewidth=0.5)
plt.axvline(0, color="grey", linewidth=0.5)
plt.xlabel("Oil price change in the month (%)")
plt.ylabel("Rand per dollar change in the month (%)")
plt.title("Monthly changes: oil vs rand")
plt.savefig("charts/changes_scatter.png")
plt.show()

# Rolling 24-month correlation
rolling = changes["oil_change_pct"].rolling(24).corr(changes["rand_change_pct"])
plt.figure(figsize=(10, 4))
plt.plot(rolling.index, rolling, color="purple")
plt.axhline(0, color="grey", linewidth=0.5)
plt.ylabel("Correlation")
plt.title("24-month rolling correlation of monthly changes")
plt.savefig("charts/rolling_correlation.png")
plt.show()
print(changes.loc["2020-03-01"])
print(changes.loc["2026-03-01"])

no2020 = changes[changes.index.year != 2020]
print(no2020.corr())
# 1. Remove only the two worst months of the crash
subset = changes.drop(pd.to_datetime(["2020-03-01", "2020-04-01"]))
print(subset.corr())

# 2. Only the period after 2020
after = changes[changes.index >= "2021-01-01"]
print(len(after))
print(after.corr())

# 3. Rank correlation, which is less affected by extreme months
print(changes.corr(method="spearman"))


