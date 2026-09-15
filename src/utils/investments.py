import numpy as np
import pandas as pd
import random
import copy
from timeit import default_timer as timer

from .dataset import create_candidate

K = 10  # number of assets to select per portfolio


def evaluate(candidate, dataset, lamda, V, H):
    """
    Normalize weights, compute R and CoVar, evaluate objective f.
    Modifies candidate in place. Appends to H if solution improves V.
    Returns (candidate, R, CoVar, f, improved).
    """
    epsilon = dataset['epsilon']
    delta   = dataset['delta']
    w = candidate['w']
    s = candidate['s']
    Q = candidate['Q']

    L = s.sum()
    w_temp = epsilon + s * dataset['F'] / L
    is_too_large = s > delta
    while is_too_large.sum() > 0:
        capped = Q[is_too_large]
        not_capped = np.logical_not(is_too_large)
        L = s[not_capped].sum()
        F_temp = 1.0 - (epsilon * not_capped.sum() + delta * is_too_large.sum())
        w_temp = epsilon + s * F_temp / L
        w_temp[capped] = delta

    w[:] = 0
    w[Q] = w_temp
    candidate['s'] = w_temp - epsilon

    if np.any(w < 0.0) or not np.isclose(w.sum(), 1) or np.sum(w > 0.0) != K:
        if np.any(w < 0.0):
            print("Negative proportion:", w)
        elif not np.isclose(w.sum(), 1):
            print(f"Weights don't sum to 1 ({w.sum()})")
        else:
            print(f"Expected {K} assets, got {np.sum(w > 0.0)}")
        raise ValueError

    candidate['CoVar'] = np.sum((w * w.reshape((w.shape[0], 1))) * dataset['sigma'])
    candidate['R']     = np.sum(w * dataset['mu'])
    f = lamda * candidate['CoVar'] - (1 - lamda) * candidate['R']

    improved = False
    if f[0] < V[lamda[0]]:
        improved = True
        V[lamda[0]] = f[0]
        H.append(copy.deepcopy(candidate))

    return candidate, candidate['R'], candidate['CoVar'], f, improved


def random_search(dataset, max_evals, E):
    """
    Random Search over E lambda values.
    Returns (best_R, best_CoVar, best_f, best_candidate, H).
    """
    best_f         = float('inf')
    best_R         = best_CoVar = best_candidate = None
    H = []
    V = {}

    for e in range(1, E + 1):
        lamda = np.array([0.5]) if E == 1 else np.array([(e - 1) / (E - 1)])
        if E > 1:
            print(f'--RS_lamda: {e}/{E}')

        V[lamda[0]] = float('inf')
        for _ in range(max_evals):
            candidate = create_candidate(dataset['N'], K)
            candidate, R, CoVar, f, _ = evaluate(candidate, dataset, lamda, V, H)

            if f < best_f:
                best_R         = copy.deepcopy(R)
                best_CoVar     = copy.deepcopy(CoVar)
                best_f         = copy.deepcopy(f)
                best_candidate = copy.deepcopy(candidate)

    return best_R, best_CoVar, best_f, best_candidate, H


def invest_random(dataset, max_evals, E):
    """
    Run Random Search 30 times with different seeds.
    Returns DataFrame with columns [R, CoVar, f].
    """
    rows  = []
    seeds = np.random.permutation(1000)[:30]

    print('--Random Search')
    for i, seed in enumerate(seeds):
        print(f'Random seed: {i + 1}/30')
        random.seed(int(seed))
        best_R, best_CoVar, best_f, _, _ = random_search(dataset, max_evals, E)
        rows.append([best_R, best_CoVar, best_f[0]])

    return pd.DataFrame(rows, columns=['R', 'CoVar', 'f'])


def tabu_search(dataset, max_evals, L, E):
    """
    Tabu Search for a given tenure L over E lambda values.
    Returns (best_R, best_CoVar, best_f, best_candidate, H).
    """
    epsilon = dataset['epsilon']
    H = []
    V = {}

    for e in range(1, E + 1):
        lamda = np.array([0.5]) if E == 1 else np.array([(e - 1) / (E - 1)])
        if E > 1:
            print(f'--TS_lamda: {e}/{E}')

        V[lamda[0]] = float('inf')

        # Warm-start: find best of 1000 random candidates
        S_star = None
        for _ in range(1000):
            candidate = create_candidate(dataset['N'], K)
            candidate, _, _, _, improved = evaluate(candidate, dataset, lamda, V, H)
            if improved:
                S_star = copy.deepcopy(candidate)

        if S_star is None:
            continue

        L_im   = np.zeros((len(S_star['Q']), 2), dtype=int)
        T_star = int(500 * dataset['N'] / K)

        for _ in range(1, T_star):
            V_dstar = float('inf')
            S_dstar = k = n = None

            for i in range(len(S_star['Q'])):
                for m in range(1, 3):
                    C = copy.deepcopy(S_star)
                    if m == 1:
                        C['s'][i] = 0.9 * (epsilon + S_star['s'][i]) - epsilon
                    else:
                        C['s'][i] = 1.1 * (epsilon + S_star['s'][i]) - epsilon

                    if C['s'][i] < 0:
                        available = list(set(range(dataset['N'])) - set(C['Q']))
                        C['Q'][i] = random.choice(available)
                        C['s'][i] = 0

                    _, _, _, f, improved = evaluate(C, dataset, lamda, V, H)
                    if improved:
                        L_im[i][m - 1] = 0
                    if L_im[i][m - 1] == 0 and f < V_dstar:
                        V_dstar = copy.deepcopy(f)
                        S_dstar = copy.deepcopy(C)
                        k, n = i, m

            if V_dstar == float('inf') or S_dstar is None:
                break

            S_star      = S_dstar
            L_im        = np.clip(L_im - 1, 0, None)
            opp_n       = 2 if n == 1 else 1
            L_im[k][opp_n - 1] = L

    _, best_R, best_CoVar, best_f, _ = evaluate(S_star, dataset, lamda, V, H)
    return best_R, best_CoVar, best_f, S_star, H


def invest_tabu(dataset, max_evals, L_star, E):
    """
    Run Tabu Search for each L in L_star, 30 seeds each.
    Returns DataFrame with columns [L, R, CoVar, f].
    """
    rows = []

    for L in L_star:
        print(f'L = {L}')
        seeds = np.random.permutation(1000)[:30]

        for i, seed in enumerate(seeds):
            print(f'Random seed: {i + 1}/30')
            random.seed(int(seed))

            start = timer()
            best_R, best_CoVar, best_f, _, _ = tabu_search(dataset, max_evals, L, E)
            print(timer() - start)

            rows.append([L, best_R, best_CoVar, best_f[0]])

    return pd.DataFrame(rows, columns=['L', 'R', 'CoVar', 'f'])
