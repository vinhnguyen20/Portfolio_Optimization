import re
import pandas as pd


def _prefix(file, results_dir):
    return results_dir + re.sub('[^a-zA-Z0-9 \n\.]', '_', file[:-4])


def report_random_search(df_results, file, results_dir):
    """Print and save Random Search statistics to file."""
    print(df_results.describe())
    with open(_prefix(file, results_dir) + '_Q1.txt', 'w') as f:
        print(df_results.describe(), file=f)


def report_tabu_search(df_results, file, results_dir):
    """Print and save Tabu Search statistics to file."""
    print(df_results.describe())
    with open(_prefix(file, results_dir) + '_Q2_d.txt', 'w') as f:
        print(df_results.describe(), file=f)


def results_comparison(rs_results, ts_results, file, results_dir):
    """Compare Random Search vs Tabu Search and save to file."""
    comp = pd.concat(
        [rs_results.iloc[:, [0, 1]], ts_results.iloc[:, [0, 1]]],
        axis=1, ignore_index=True
    )
    comp.columns = ['RandomSearch_R', 'RandomSearch_CoVar', 'TabuSearch_R', 'TabuSearch_CoVar']
    print(comp.describe())

    with open(_prefix(file, results_dir) + '_Q2_e.txt', 'w') as f:
        print(comp.describe(), file=f)

    return comp
