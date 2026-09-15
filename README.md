# Portfolio Optimization — Crypto

Tối ưu hoá danh mục đầu tư crypto bằng thuật toán heuristic, dữ liệu real-time từ **Binance**.

---

## Tổng quan

Chọn **10 coin tốt nhất** từ danh sách coin Binance và phân bổ tỷ trọng tối ưu, dựa trên hai tiêu chí:

- **Tối đa hoá** lợi nhuận kỳ vọng `R`
- **Tối thiểu hoá** rủi ro `CoVar`

Hai thuật toán được so sánh: **Random Search** (baseline) và **Tabu Search** (tốt hơn đáng kể).

---

## Cấu trúc project

```
PortfolioOptimization/
│
├── main.py                      # Chạy toàn bộ pipeline
├── fetch_binance_data.py        # Fetch dữ liệu từ Binance API
│
├── datasets/
│   └── binance_assets.txt       # Dữ liệu coin (tự động tạo)
│
├── src/utils/
│   ├── dataset.py               # load_dataset(), create_candidate()
│   ├── investments.py           # evaluate(), random_search(), invest_random()
│   │                            # tabu_search(), invest_tabu()
│   ├── reporting.py             # report_random_search(), report_tabu_search()
│   │                            # results_comparison()
│   ├── frontier.py              # dominated(), efficientfrontier()
│   └── plotting.py              # plot_boxplot_R/f(), market_comparison_plot()
│
└── results_YYYY_MM_DD-HHMM/     # Kết quả mỗi lần chạy
```

---

## Cách chạy

### 1. Cài thư viện
```bash
pip install numpy pandas matplotlib requests openpyxl
```

### 2. Fetch dữ liệu Binance
```bash
# Mặc định: top 20 crypto, daily, 1 năm
python fetch_binance_data.py

# Tuỳ chỉnh
python fetch_binance_data.py \
  --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT \
  --interval 1d --lookback 365 \
  --output datasets/binance_assets.txt
```

### 3. Chạy tối ưu hoá
```bash
python main.py
```

---

## Cấu hình (`main.py`)

```python
FORCED_ASSETS    = [0]           # Coin luôn được chọn (0 = BTC, 1 = ETH, ...)
TOTAL_INVESTMENT = 1_000_000_000 # Vốn đầu tư
MIN_INVEST       = 0.01          # Tỷ trọng tối thiểu mỗi coin (1%)
MAX_INVEST       = 1.0           # Tỷ trọng tối đa mỗi coin (100%)
DEFAULT_L_STAR   = 7             # Tabu tenure mặc định
```

---

## Hàm mục tiêu

$$f = \lambda \cdot CoVar - (1 - \lambda) \cdot R$$

$$CoVar = \sum_{i=1}^{N} \sum_{j=1}^{N} w_i \, w_j \, \rho_{ij} \, \sigma_i \, \sigma_j \qquad R = \sum_{i=1}^{N} w_i \, \mu_i$$

| Ký hiệu | Ý nghĩa |
|---|---|
| `λ` | Cân bằng rủi ro và lợi nhuận (0 → 1) |
| `CoVar` | Rủi ro danh mục |
| `R` | Lợi nhuận kỳ vọng |
| `wi` | Tỷ trọng coin i |
| `μi` | Lợi suất kỳ vọng coin i |
| `ρij` | Correlation giữa coin i và j |
| `σi` | Độ lệch chuẩn coin i |

**Ràng buộc:** đúng K=10 coin, mỗi coin tối thiểu 1%, tổng tỷ trọng = 1.

---

## Thuật toán

### Random Search
Sinh ngẫu nhiên `1000 × N` nghiệm, mỗi nghiệm chọn 10 coin và phân bổ tỷ trọng ngẫu nhiên. Lấy nghiệm có `f` nhỏ nhất.

### Tabu Search
Leo đồi có nhớ — bắt đầu từ nghiệm tốt nhất của Random Search, tìm "hàng xóm" bằng cách tăng/giảm tỷ trọng 10%. Cấm quay lại các nước đi vừa thực hiện trong `L*` bước.

Các giá trị `L*` được kiểm tra:

$$L^* \in \{1,\ 2,\ 5,\ 7,\ 10,\ 15\}$$

Quy tắc chọn `L*` theo kích thước bài toán `n`:

$$L^* \in \left[0.5\sqrt{n},\ 2\sqrt{n}\right]$$

---

## Giải thích từng hàm

| Hàm | File | Chức năng |
|---|---|---|
| `load_dataset()` | `dataset.py` | Đọc file .txt → dict (N, mu, sigma, ...) |
| `create_candidate()` | `dataset.py` | Tạo 1 danh mục ngẫu nhiên (Q, s, w) |
| `evaluate()` | `investments.py` | Tính R, CoVar, f cho 1 danh mục |
| `random_search()` | `investments.py` | Chạy 1 lần Random Search |
| `invest_random()` | `investments.py` | Chạy Random Search 30 lần × 30 seed |
| `tabu_search()` | `investments.py` | Chạy 1 lần Tabu Search |
| `invest_tabu()` | `investments.py` | Chạy Tabu Search cho nhiều L* × 30 seed |
| `report_random_search()` | `reporting.py` | Lưu thống kê RS → file .txt |
| `report_tabu_search()` | `reporting.py` | Lưu thống kê TS → file .txt |
| `results_comparison()` | `reporting.py` | So sánh RS vs TS |
| `dominated()` | `frontier.py` | Lọc Efficient Frontier (Pareto) |
| `efficientfrontier()` | `frontier.py` | Vẽ biểu đồ Efficient Frontier |
| `plot_boxplot_R/f()` | `plotting.py` | Vẽ boxplot so sánh các thuật toán |

---

## Kết quả đầu ra

Mỗi lần chạy tạo thư mục `results_YYYY_MM_DD-HHMM/`:

| File | Nội dung |
|---|---|
| `*_Q1.txt` | Thống kê Random Search (30 runs) |
| `*_Q2_d.txt` | Thống kê Tabu Search L*=7 |
| `*_Q2_e.txt` | So sánh RS vs TS |
| `*_Q3_R.png` | Boxplot Revenue theo L* |
| `*_Q3_f.png` | Boxplot f-value theo L* |
| `*_Q4_AssetsToInvest_*.xlsx` | Danh sách 10 coin nên mua |
| `*_Q4_WeightToInvest_*.xlsx` | Tỷ trọng tối ưu từng coin |
| `*_Q4_H_*_filtered.xlsx` | Tất cả danh mục trên Efficient Frontier |
| `*_Q4_Frontier_RS/TS.png` | Biểu đồ Efficient Frontier |

---

## Tham khảo

T.-J. Chang, N. Meade, J.E. Beasley, Y.M. Sharaiha, *Heuristics for cardinality constrained portfolio optimisation*, Computers & Operations Research, 27(13):1271–1302, 2000.
https://doi.org/10.1016/S0305-0548(99)00074-X
