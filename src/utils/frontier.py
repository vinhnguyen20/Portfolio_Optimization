import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re

from .investments import random_search, tabu_search


def _prefix(file, results_dir):
    return results_dir + re.sub('[^a-zA-Z0-9 \n\.]', '_', file[:-4]) + '_Q4_'


def dominated(H, alg, file, results_dir):
    """
    Filter non-dominated (efficient) solutions from H.
    Exports dominated and dominating points to Excel.
    Returns (dominated_points, dominating_points).
    """
    points  = np.array([]).reshape((0, 2))
    assets  = np.array([]).reshape((0, 10))
    weights = np.array([]).reshape((0, 10))

    for c in H:
        R, CoVar = c['R'], c['CoVar']
        Q = np.sort(c['Q'])
        if [R, CoVar] not in points:
            points  = np.append(points,  [[R, CoVar]], axis=0)
            assets  = np.append(assets,  [Q],          axis=0)
            weights = np.append(weights, [c['w'][np.nonzero(c['w'])]], axis=0)

    # Sort by Return ascending
    order   = points[:, 0].argsort()
    points  = points[order]
    assets  = assets[order]
    weights = weights[order]

    # Find dominated indices
    to_delete = []
    for i in range(len(points)):
        for j in range(len(points)):
            if points[j, 0] != points[i, 0] and points[j, 1] != points[i, 1]:
                if points[j, 0] >= points[i, 0] and points[j, 1] <= points[i, 1]:
                    to_delete.append(i)
                    break

    dominated_points  = points[to_delete]
    dominating_points = np.delete(points,  to_delete, axis=0)
    assets            = np.delete(assets,  to_delete, axis=0)
    weights           = np.delete(weights, to_delete, axis=0)

    prefix = _prefix(file, results_dir)
    pd.DataFrame(dominated_points).to_excel( prefix + 'H_' + alg + '.xlsx',           index=False)
    pd.DataFrame(dominating_points).to_excel(prefix + 'H_' + alg + '_filtered.xlsx',  index=False)
    pd.DataFrame(assets).to_excel(           prefix + 'AssetsToInvest_' + alg + '.xlsx', index=False)
    pd.DataFrame(weights).to_excel(          prefix + 'WeightToInvest_' + alg + '.xlsx', index=False)

    return dominated_points, dominating_points


def efficientfrontier(L_star, E, dataset, max_evals, file, results_dir):
    """Compute and plot Efficient Frontier for both Random Search and Tabu Search."""
    prefix = _prefix(file, results_dir)

    # ── Random Search ──────────────────────────────────────────────────────────
    _, _, _, _, H_rs = random_search(dataset, max_evals, E)
    dominated_rs, dominating_rs = dominated(H_rs, 'RS', file, results_dir)

    fig = plt.figure(figsize=(8, 6))
    plt.plot(dominated_rs[:, 1],  dominated_rs[:, 0],  'o', markersize=5,   label='Available Portfolio')
    plt.plot(dominating_rs[:, 1], dominating_rs[:, 0], 'o', color='orange', markersize=8, label='Efficient Frontier')
    plt.xlabel('Risk - Variance', fontsize=12)
    plt.ylabel('Return', fontsize=12)
    plt.title('Efficient Frontier (Random Search)', fontsize=14)
    plt.legend(loc='best')
    fig.savefig(prefix + '_Frontier_RS.png')
    plt.close(fig)

    # ── Tabu Search ────────────────────────────────────────────────────────────
    _, _, _, _, H_ts = tabu_search(dataset, max_evals, L_star, E)
    dominated_ts, dominating_ts = dominated(H_ts, 'TS', file, results_dir)

    fig = plt.figure(figsize=(8, 6))
    plt.plot(dominated_ts[:, 1],  dominated_ts[:, 0],  'o', markersize=0.7, label='Available Portfolio')
    plt.plot(dominating_ts[:, 1], dominating_ts[:, 0], 'o', color='orange', markersize=3, label='Efficient Frontier')
    plt.xlabel('Risk - Variance', fontsize=12)
    plt.ylabel('Return', fontsize=12)
    plt.title('Efficient Frontier (Tabu Search)', fontsize=14)
    plt.legend(loc='best')
    fig.savefig(prefix + '_Frontier_TS.png')
    plt.close(fig)

    return True
