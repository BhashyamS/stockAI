import subprocess
import sys

commands = [
    ["-m", "src.agents.technical_agent"],
    ["-m", "src.models.predict_ml_signals"],
    ["-m", "src.agents.ml_agent"],
    ["-m", "src.agents.risk_agent"],
    ["-m", "src.agents.executive_agent"],
]

for cmd in commands:
    print("\nRunning:", "python", " ".join(cmd))
    result = subprocess.run([sys.executable] + cmd)

    if result.returncode != 0:
        print("Failed:", "python", " ".join(cmd))
        sys.exit(result.returncode)

print("\nAll agents completed successfully.")