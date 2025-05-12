import pandas as pd
import numpy as np
from random import choices, randint, uniform
from pathlib import Path

# Define the path to save the training data
TRAINING_DATA_PATH = Path(__file__).parent / 'data' / 'training_data.csv'
TRAINING_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)  # Create 'data' directory if it doesn't exist

def generate_training_data(num_samples=10000000):
    data = []
    for _ in range(num_samples):
        # Generate features
        os_type = choices([1, 2, 3, 4], weights=[0.6, 0.2, 0.15, 0.05])[0]
        device_type = choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        days_since = randint(0, 180)
        num_software = randint(5, 40)

        # Generate blocked software based on risk factors
        risk_factor = uniform(0, 1)
        num_blocked = randint(0, 3) if risk_factor > 0.7 else 0

        # Historical compliance depends on other factors
        pct_history = max(0, min(1, (
            0.8 - (days_since / 300) - (num_blocked * 0.2) + uniform(-0.1, 0.1)
        )))

        # Determine label based on features
        if num_blocked > 0 or days_since > 60 or pct_history < 0.4:
            label = 0  # non-compliant
        elif days_since > 30 or pct_history < 0.7 or num_software > 25:
            label = 1  # warning
        else:
            label = 2  # compliant

        data.append([
            os_type, device_type, days_since,
            num_software, num_blocked, pct_history, label
        ])

    return pd.DataFrame(data, columns=[
        'os_type', 'device_type', 'days_since_last_scan',
        'num_installed_software', 'num_blocked_software',
        'pct_compliant_history', 'label'
    ])


# Generate and save sample data
df = generate_training_data(1000)
df.to_csv(TRAINING_DATA_PATH, index=False)
print(f"Generated training data with shape: {df.shape} and saved to: {TRAINING_DATA_PATH}")
