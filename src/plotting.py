import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def _millions(x, pos):
    return '£%1.1fM' % (x * 1e-6)


def _prefix(file, results_dir):
    return results_dir + re.sub('[^a-zA-Z0-9 \n\.]', '_', file[:-4])


def plot_boxplot_R(rs_results, ts_results, file, results_dir, total_investment):
    """Boxplot comparing Revenue across Random Search and Tabu Search variants."""
    data = [rs_results.iloc[:, 0] * total_investment] + [
        ts_results[ts_results.L == L].iloc[:, 1] * total_investment
        for L in [1, 2, 5, 7, 10, 15]
    ]
    labels = ['Random Search'] + [f'Tabu Search (L* = {L})' for L in [1, 2, 5, 7, 10, 15]]

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)
    bp = ax.boxplot(data, notch=0, sym='+', vert=1, whis=1.5)
    plt.setp(bp['boxes'],    color='black')
    plt.setp(bp['whiskers'], color='black')
    plt.setp(bp['fliers'],   color='red', marker='+')
    ax.set_axisbelow(True)
    ax.set_title(f'Boxplot Revenue Values: {file}', fontsize=14)
    ax.set_ylabel('Revenue Values', fontsize=12)
    ax.set_xticklabels(labels, rotation=55, fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(_millions))
    plt.savefig(_prefix(file, results_dir) + '_Q3_R.png')
    plt.close()


def plot_boxplot_f(rs_results, ts_results, file, results_dir):
    """Boxplot comparing f-values across Random Search and Tabu Search variants."""
    data = [rs_results.iloc[:, 2]] + [
        ts_results[ts_results.L == L].iloc[:, 3]
        for L in [1, 2, 5, 7, 10, 15]
    ]
    labels = ['Random Search'] + [f'Tabu Search (L* = {L})' for L in [1, 2, 5, 7, 10, 15]]

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)
    bp = ax.boxplot(data, notch=0, sym='+', vert=1, whis=1.5)
    plt.setp(bp['boxes'],    color='black')
    plt.setp(bp['whiskers'], color='black')
    plt.setp(bp['fliers'],   color='red', marker='+')
    ax.set_axisbelow(True)
    ax.set_title(f'Boxplot f Values: {file}', fontsize=14)
    ax.set_ylabel('f Values', fontsize=12)
    ax.set_xticklabels(labels, rotation=55, fontsize=12)
    plt.savefig(_prefix(file, results_dir) + '_Q3_f.png')
    plt.close()


def market_comparison_plot():
    """Plot Efficient Frontiers of all 5 markets on one chart."""
    markets = [
        ('markets/assets1.xlsx', 'orange', '(1) Hang Seng'),
        ('markets/assets2.xlsx', 'g',      '(2) DAX'),
        ('markets/assets3.xlsx', 'k',      '(3) FTSE'),
        ('markets/assets4.xlsx', 'c',      '(4) S&P'),
        ('markets/assets5.xlsx', 'C3',     '(5) Nikkei'),
    ]
    fig = plt.figure(figsize=(8, 8))
    for path, color, label in markets:
        df = pd.read_excel(path)
        plt.plot(df.iloc[:, 1].tolist(), df.iloc[:, 0].tolist(), color=color, label=label)
    plt.xlabel('Risk - Variance', fontsize=12)
    plt.ylabel('Return', fontsize=12)
    plt.title('Efficient Frontier per Market', fontsize=14)
    plt.legend(loc='best')
    plt.show()
