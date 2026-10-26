import os
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the file you saved in step 2
monthly = pd.read_csv("data/monthly_oil_rand.csv", index_col=0, parse_dates=True)

# 2. Drop the partial month (October 2026). Remove this line if you decided to keep it.
monthly = monthly.iloc[:-1]

print(monthly.shape)
print(monthly.tail(3))

os.makedirs("charts", exist_ok=True)

# 3. Chart 1: oil and rand over time, one above the other
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
axes[0].plot(monthly.index, monthly["oil_usd"], color="black")
axes[0].set_title("Brent crude oil, monthly average (USD per barrel)")
axes[1].plot(monthly.index, monthly["usd_zar"], color="green")
axes[1].set_title("US dollar to rand, monthly average")
plt.tight_layout()
plt.savefig("charts/oil_and_rand.png")
plt.show()
# 4. How closely do the two move together?
print(monthly.corr())

# 5. Chart 2: scatter plot of oil against rand
plt.figure(figsize=(7, 5))
plt.scatter(monthly["oil_usd"], monthly["usd_zar"], alpha=0.6)
plt.xlabel("Oil price (USD per barrel)")
plt.ylabel("Rand per US dollar")
plt.title("Oil price vs rand exchange rate")
plt.savefig("charts/oil_vs_rand_scatter.png")
plt.show()

# 6. The oil price in rand terms (closer to what South Africa actually pays)
monthly["oil_zar"] = monthly["oil_usd"] * monthly["usd_zar"]

plt.figure(figsize=(10, 4))
plt.plot(monthly.index, monthly["oil_zar"], color="darkred")
plt.title("Brent crude oil in rand per barrel (monthly average)")
plt.savefig("charts/oil_in_rand.png")
plt.show()

# 7. Highest and lowest months
print("Highest oil month:", monthly["oil_usd"].idxmax(), monthly["oil_usd"].max())
print("Lowest oil month:", monthly["oil_usd"].idxmin(), monthly["oil_usd"].min())
print("Weakest rand month:", monthly["usd_zar"].idxmax(), monthly["usd_zar"].max())
