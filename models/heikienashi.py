import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Fetch Historical Data
symbol = 'SPY'
df = yf.download(symbol, start='2022-01-01', end='2026-01-01')

# 2. Calculate Heikin Ashi Candlesticks
ha_df = pd.DataFrame(index=df.index)
ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4.0

ha_open = []
for i in range(len(df)):
    if i == 0:
        ha_open.append((df['Open'].iloc[0] + df['Close'].iloc[0]) / 2.0)
    else:
        ha_open.append((ha_open[-1] + ha_df['HA_Close'].iloc[i-1]) / 2.0)

ha_df['HA_Open'] = ha_open
ha_df['HA_High'] = np.maximum(df['High'], np.maximum(ha_df['HA_Open'], ha_df['HA_Close']))
ha_df['HA_Low'] = np.minimum(df['Low'], np.minimum(ha_df['HA_Open'], ha_df['HA_Close']))

# 3. Create Features (e.g., HA Candle Direction and Color Streak)
ha_df['HA_Color'] = np.where(ha_df['HA_Close'] > ha_df['HA_Open'], 1, -1)
ha_df['HA_Streak'] = ha_df['HA_Color'] * (ha_df['HA_Color'].groupby((ha_df['HA_Color'] != ha_df['HA_Color'].shift()).cumsum()).cumcount() + 1)

# 4. Target Label: Predict if the next day's Heikin Ashi close will be higher than today's
ha_df['Target'] = np.where(ha_df['HA_Close'].shift(-1) > ha_df['HA_Close'], 1, 0)
ha_df = ha_df.dropna()

# 5. Machine Learning Pipeline
X = ha_df[['HA_Close', 'HA_Open', 'HA_High', 'HA_Low', 'HA_Streak']]
y = ha_df['Target']

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Train the Random Forest Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
predictions = model.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, predictions):.2%}")

# 6. Generate Strategy Signals based on Predictions
# Buy when ML predicts price goes up (1) & HA close is above open
ha_df['Signal'] = 0
ha_df.loc[(predictions == 1) & (ha_df['HA_Close'] > ha_df['HA_Open']), 'Signal'] = 1
# Sell/Exit when ML predicts price goes down (0)
ha_df.loc[(predictions == 0), 'Signal'] = -1

# Calculate Strategy Returns
ha_df['Strategy_Returns'] = ha_df['Signal'].shift(1) * (df['Close'].pct_change())
cumulative_returns = (ha_df['Strategy_Returns'] + 1).cumprod()

print(f"Strategy Cumulative Return: {cumulative_returns.iloc[-1]:.2f}")
