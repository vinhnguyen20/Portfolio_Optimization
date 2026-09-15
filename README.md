# Portfolio Optimization
Heuristics for cardinality constrained portfolio optimisation trên thị trường **Crypto** với dữ liệu real-time từ **Binance**.

<br/>

---

## Summary

Dự án tối ưu hoá danh mục đầu tư crypto với ngân sách **£1 tỷ**, xác định danh mục **10 coin tốt nhất** dựa trên mức độ lợi nhuận và rủi ro, có xét đến sự tương quan giữa các coin thông qua ma trận covariance.

Hai mục tiêu chính:
- **Tối thiểu hoá** expected variance (rủi ro) của danh mục
- **Tối đa hoá** expected return (lợi nhuận) của danh mục

Hai thuật toán heuristic được triển khai và so sánh:
- **Random Search** — baseline ngẫu nhiên
- **Tabu Search** — leo đồi có nhớ, cho kết quả tốt hơn đáng kể

---

## Project Structure

```
PortfolioOptimization/
│
├── main.py                      # Entry point — chạy toàn bộ pipeline
├── fetch_binance_data.py        # Fetch dữ liệu crypto real-time từ Binance API
│
├── datasets/
│   └── binance_assets.txt       # Crypto data từ Binance (tự động tạo)
│
├── src/
│   └── utils/
│       ├── dataset.py           # load_dataset(), create_candidate()
│       ├── investments.py       # evaluate(), random_search(), invest_random()
│       │                        # tabu_search(), invest_tabu()
│       ├── reporting.py         # report_random_search(), report_tabu_search()
│       │                        # results_comparison()
│       ├── frontier.py          # dominated(), efficientfrontier()
│       └── plotting.py          # plot_boxplot_R/f()
│
└── results_YYYY_MM_DD-HHMM/     # Kết quả mỗi lần chạy (PNG, Excel, TXT)
```

---

## Quick Start

### 1. Cài dependencies
```bash
pip install numpy pandas matplotlib requests openpyxl
```

### 2. Fetch dữ liệu từ Binance
```bash
# Mặc định: top 20 crypto, daily, 1 năm
python fetch_binance_data.py

# Tuỳ chỉnh symbols và interval
python fetch_binance_data.py \
  --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT \
  --interval 1d --lookback 365 \
  --output datasets/binance_assets.txt
```

### 3. Chạy tối ưu hoá
```bash
python main.py
```

Kết quả được lưu vào thư mục `results_YYYY_MM_DD-HHMM/`.

---

## Objective Function

Tối thiểu hoá hàm mục tiêu:

$$f(s) = \lambda \cdot CoVar(s) - (1 - \lambda) \cdot R(s)$$

Trong đó:

$$CoVar = \sum_{i=1}^{N} \sum_{j=1}^{N} w_i \, w_j \, \rho_{ij} \, \sigma_i \, \sigma_j$$

$$R = \sum_{i=1}^{N} w_i \, \mu_i$$

| Ký hiệu | Ý nghĩa |
|---|---|
| `λ` (lambda) | Tham số cân bằng risk vs return ∈ [0, 1] |
| `CoVar` | Covariance — đo rủi ro danh mục |
| `R` | Expected return — lợi nhuận kỳ vọng |
| `wi` | Tỷ trọng đầu tư vào coin i |
| `μi` | Expected return của coin i |
| `ρij` | Correlation giữa coin i và j |
| `σi` | Standard deviation của coin i |

**Ràng buộc:** chọn đúng K=10 coin, mỗi coin đầu tư tối thiểu 1% (`ε`), tổng tỷ trọng = 1.

---

## Dataset Format

File `datasets/binance_assets.txt` được tạo tự động bởi `fetch_binance_data.py`:

```
20                    # số lượng coin N
-0.283070 0.369139   # annualized return, std dev của coin 1 (BTCUSDT)
-0.409019 0.531174   # annualized return, std dev của coin 2 (ETHUSDT)
...
1 1 1.000000         # correlation giữa coin 1 và coin 1 (diagonal)
1 2 0.874521         # correlation giữa coin 1 và coin 2
...
```

---

## Optimization Algorithms

### Random Search

Sinh ngẫu nhiên `1000×N` nghiệm, mỗi nghiệm chọn K=10 coin và phân bổ tỷ trọng ngẫu nhiên. Lấy nghiệm tốt nhất theo hàm mục tiêu f.

### Tabu Search

Thuật toán leo đồi có nhớ — bắt đầu từ nghiệm tốt nhất của Random Search, tìm kiếm "hàng xóm" bằng cách tăng/giảm tỷ trọng 10%.

**Tabu List `L_im[i][m]`:** cấm đi lại các bước vừa thực hiện trong `L*` bước tiếp theo.

### Parameter Optimization (L*)

Các giá trị L* được kiểm tra:

$$L^* = \{1, 2, 5, 7, 10, 15\}$$

Quy tắc kinh nghiệm chọn L* tối ưu theo kích thước bài toán n:

$$L^* \in \left[0.5\sqrt{n},\ 2\sqrt{n}\right]$$

Với 20 coin (N=20): L* tối ưu = **7**.

---

## Efficient Frontier

Chạy với E=50 giá trị λ ∈ [0,1] → 50 danh mục tối ưu → đường Efficient Frontier.

```
Return
  ^
  |        ● ●
  |      ●       ← Efficient Frontier
  |    ●            (danh mục tốt nhất tại mỗi mức rủi ro)
  |  ●
  +──────────────> Risk (CoVar)
```

---

## Results Output

Mỗi lần chạy tạo ra thư mục `results_YYYY_MM_DD-HHMM/` chứa:

| File | Nội dung |
|---|---|
| `*_Q1.txt` | Thống kê Random Search (30 runs) |
| `*_Q2_d.txt` | Thống kê Tabu Search L*=7 |
| `*_Q2_e.txt` | So sánh RS vs TS |
| `*_Q3_R.png` | Boxplot Revenue theo L* |
| `*_Q3_f.png` | Boxplot f-value theo L* |
| `*_Q4_H_RS/TS_filtered.xlsx` | Efficient Frontier points |
| `*_Q4_AssetsToInvest_*.xlsx` | Danh sách coin nên mua |
| `*_Q4_WeightToInvest_*.xlsx` | Tỷ trọng tối ưu từng coin |
| `*_Q4_Frontier_RS/TS.png` | Biểu đồ Efficient Frontier |

---

## References

T.-J. Chang, N. Meade, J.E. Beasley, Y.M. Sharaiha, *Heuristics for cardinality constrained portfolio optimisation*, Computers & Operations Research, 27(13):1271–1302, 2000.
https://doi.org/10.1016/S0305-0548(99)00074-X
