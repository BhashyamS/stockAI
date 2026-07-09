import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
import joblib

INPUT_FILE = Path("data/processed/features_clean.csv")
MODEL_FILE = Path("models/random_forest_5d_model.pkl")
MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "Daily_Return",
    "MA_5",
    "MA_20",
    "MA_50",
    "MA_200",
    "Volatility_20",
    "Momentum_10",
    "Volume_Ratio",
    "RSI_14",
    "ATR_Ratio",
]

TARGET = "Target_5D_Up"


def main():
    df = pd.read_csv(INPUT_FILE)

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        shuffle=False
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    print("Accuracy:", accuracy_score(y_test, predictions))
    print("Precision:", precision_score(y_test, predictions))
    print("Recall:", recall_score(y_test, predictions))
    print("ROC AUC:", roc_auc_score(y_test, probabilities))

    joblib.dump(model, MODEL_FILE)
    print(f"Saved model to {MODEL_FILE}")


if __name__ == "__main__":
    main()