import numpy as np
import pandas as pd


def load_dataset(file, min_invest=0.01, max_invest=1):
    """Load and preprocess a dataset file. Returns a dataset dict."""
    epsilon = min_invest
    delta = max_invest

    if 10 * epsilon > 1.0:
        raise ValueError("Epsilon is too large")
    if 10 * delta < 1.0:
        raise ValueError("Delta is too small")

    try:
        ds_raw = pd.read_csv(file, header=None)
    except Exception:
        raise IOError(f"Error reading file: {file}")

    assets_num = int(ds_raw[0][0])

    # Parse asset details (expected return, std dev)
    ds_asset_details = ds_raw.iloc[1:assets_num + 1, 0]
    ds_asset_details = ds_asset_details.str.split(' ', expand=True, n=2)
    ds_asset_details.drop(ds_asset_details.columns[[0]], axis=1, inplace=True)
    ds_asset_details.columns = ['ExpReturn', 'StDev']
    ds_asset_details['ExpReturn'] = ds_asset_details['ExpReturn'].astype(float)
    ds_asset_details['StDev'] = ds_asset_details['StDev'].astype(float)

    # Parse correlations
    ds_correlations = ds_raw.iloc[assets_num + 1:, 0]
    ds_correlations = ds_correlations.str.split(' ', expand=True, n=3)
    ds_correlations.drop(ds_correlations.columns[[0]], axis=1, inplace=True)
    ds_correlations.columns = ['Asset1', 'Asset2', 'Correlation']
    ds_correlations['Asset1'] = ds_correlations['Asset1'].astype(int)
    ds_correlations['Asset2'] = ds_correlations['Asset2'].astype(int)
    ds_correlations['Correlation'] = ds_correlations['Correlation'].astype(float)

    # Build N×N correlation matrix
    ds_rho = pd.DataFrame(index=range(1, assets_num + 1), columns=range(1, assets_num + 1))
    for i in range(len(ds_correlations)):
        ds_rho.iloc[ds_correlations.iloc[i, 0] - 1, ds_correlations.iloc[i, 1] - 1] = ds_correlations.iloc[i, 2]
        ds_rho.iloc[ds_correlations.iloc[i, 1] - 1, ds_correlations.iloc[i, 0] - 1] = ds_correlations.iloc[i, 2]

    rho = np.array(ds_rho.iloc[0].tolist())
    for i in range(1, len(ds_rho)):
        rho = np.append(rho, ds_rho.iloc[i].tolist(), axis=0)
    rho = rho.reshape((assets_num, assets_num))

    mu = np.array(ds_asset_details.ExpReturn.tolist())
    std = np.array(ds_asset_details.StDev.tolist())
    sigma = np.asarray(rho * std * std.reshape((std.shape[0], 1)))

    return {
        'N':       assets_num,
        'mu':      mu,
        'sigma':   sigma,
        'epsilon': epsilon,
        'delta':   delta,
        'F':       1.0 - 10 * epsilon,
    }


def create_candidate(N, K, forced_indices=None):
    """
    Create a random candidate solution dict.
    forced_indices: list of asset indices always included (e.g. [0] for Bitcoin).
    """
    forced = list(forced_indices) if forced_indices else []
    remaining = [i for i in range(N) if i not in forced]
    extra = list(np.random.choice(remaining, K - len(forced), replace=False))
    Q = np.array(forced + extra)
    return {
        'Q':     Q,
        's':     np.random.rand(K),
        'w':     np.zeros(N),
        'CoVar': np.nan,
        'R':     np.nan,
    }
