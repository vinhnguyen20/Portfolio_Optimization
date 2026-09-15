import pathlib
import time

from src.utils.dataset import load_dataset
from src.utils.investments import invest_random, invest_tabu
from src.utils.reporting import report_random_search, report_tabu_search, results_comparison
from src.utils.frontier import efficientfrontier
from src.utils.plotting import plot_boxplot_R, plot_boxplot_f

# ─── Config ───────────────────────────────────────────────────────────────────
TOTAL_INVESTMENT = 1_000_000_000   # 1 Billion
MIN_INVEST       = 0.01            # epsilon
MAX_INVEST       = 1.0             # delta

LS_FILES = [
    'datasets/binance_assets.txt',
    # 'datasets/assets1.txt',
    # 'datasets/assets2.txt',
    # 'datasets/assets3.txt',
    # 'datasets/assets4.txt',
    # 'datasets/assets5.txt',
]

BEST_L_STAR = {
    'datasets/assets1.txt': 5,
    'datasets/assets2.txt': 7,
    'datasets/assets3.txt': 7,
    'datasets/assets4.txt': 7,
    'datasets/assets5.txt': 10,
}
DEFAULT_L_STAR = 7

# Assets luôn được chọn vào danh mục (index theo thứ tự trong file dataset)
# Binance default symbols: 0=BTCUSDT, 1=ETHUSDT, 2=BNBUSDT, ...
FORCED_ASSETS = [0]  # luôn chọn Bitcoin (BTCUSDT)

# ─── Results directory ────────────────────────────────────────────────────────
results_dir = 'results_' + time.strftime("%Y_%m_%d-%H%M") + '/'
pathlib.Path(results_dir).mkdir(parents=True, exist_ok=True)

# ─── Main loop ────────────────────────────────────────────────────────────────
for file in LS_FILES:
    print('*' * 50, '\n\tFile:', file, '\n')

    dataset   = load_dataset(file, MIN_INVEST, MAX_INVEST)
    max_evals = 1000 * dataset['N']
    E = 1

    # ── Q1: Random Search ────────────────────────────────────────────────────
    rs_results = invest_random(dataset, max_evals, E, FORCED_ASSETS)
    report_random_search(rs_results, file, results_dir)

    # ── Q2: Tabu Search (L*=7) ───────────────────────────────────────────────
    ts_results_q2 = invest_tabu(dataset, max_evals, L_star=[7], E=E, forced_indices=FORCED_ASSETS)
    report_tabu_search(ts_results_q2, file, results_dir)
    results_comparison(
        rs_results,
        ts_results_q2[ts_results_q2.L == 7].iloc[:, 1:3],
        file, results_dir
    )

    # ── Q3: Tabu Search (multiple L*) ────────────────────────────────────────
    ts_results_q3 = invest_tabu(dataset, max_evals, L_star=[1, 2, 5, 7, 10, 15], E=E, forced_indices=FORCED_ASSETS)
    plot_boxplot_R(rs_results, ts_results_q3, file, results_dir, TOTAL_INVESTMENT)
    plot_boxplot_f(rs_results, ts_results_q3, file, results_dir)

    # ── Q4: Efficient Frontier (E=50 lambdas) ────────────────────────────────
    E      = 50
    L_star = BEST_L_STAR.get(file, DEFAULT_L_STAR)
    efficientfrontier(L_star, E, dataset, max_evals, file, results_dir, FORCED_ASSETS)
