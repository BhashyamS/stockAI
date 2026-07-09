import subprocess
import sys


COMMANDS = [
    ["src/data/download_prices.py"],
    ["src/data/combine_prices.py"],
    ["src/features/build_features.py"],
    ["src/features/clean_features.py"],
    ["src/models/predict_ml_signals.py"],
    ["-m", "src.committee.run_structured_committee"],
    ["-m", "src.committee.build_cio_package"],
]


def run_step(command):
    print("\n" + "=" * 70)
    print("Running:", "python", " ".join(command))
    print("=" * 70)

    result = subprocess.run([sys.executable] + command)

    if result.returncode != 0:
        print("\nPipeline stopped because this step failed:")
        print("python", " ".join(command))
        sys.exit(result.returncode)


def main():
    print("Starting StockAI committee pipeline...")

    for command in COMMANDS:
        run_step(command)

    print("\nCommittee pipeline completed successfully.")
    print("Next: run Streamlit dashboard:")
    print("streamlit run dashboard/investment_committee.py")


if __name__ == "__main__":
    main()