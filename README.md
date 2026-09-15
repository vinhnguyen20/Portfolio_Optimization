# Portfolio Optimization
Heuristics for cardinality constrained portfolio optimisation — hỗ trợ cả dữ liệu thị trường chứng khoán truyền thống lẫn **crypto real-time từ Binance**.

<p align="center">
<img src="imgs/datasets_assets1_Frontier_RS.png" alt="Efficient Frontier Random Search" title="Efficient Frontier Random Search" width="550"/> <img src="imgs/datasets_assets1_Frontier_TS.png" alt="Efficient Frontier Tabu Search" title="Efficient Frontier Tabu Search" width="550"/>
</p>

<br/>

---

## Summary

Dự án tối ưu hoá danh mục đầu tư với ngân sách **£1 tỷ**, xác định danh mục **10 tài sản tốt nhất** dựa trên mức độ lợi nhuận và rủi ro. Xét đến sự tương quan giữa các tài sản thông qua ma trận covariance.

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
├── main.py                  # Entry point — chạy toàn bộ pipeline
├── fetch_binance_data.py    # Fetch dữ liệu crypto real-time từ Binance API
│
├── datasets/
│   ├── assets1.txt          # Hang Seng (31 assets)
│   ├── assets2.txt          # DAX (85 assets)
│   ├── assets3.txt          # FTSE (89 assets)
│   ├── assets4.txt          # S&P 500 (98 assets)
│   ├── assets5.txt          # Nikkei (225 assets)
│   └── binance_assets.txt   # Crypto data từ Binance (tự động tạo)
│
├── src/
│   ├── dataset.py           # load_dataset(), create_candidate()
│   ├── investments.py       # evaluate(), random_search(), invest_random()
│   │                        # tabu_search(), invest_tabu()
│   ├── reporting.py         # report_random_search(), report_tabu_search()
│   │                        # results_comparison()
│   ├── frontier.py          # dominated(), efficientfrontier()
│   └── plotting.py          # plot_boxplot_R/f(), market_comparison_plot()
│
└── results_YYYY_MM_DD-HHMM/ # Kết quả mỗi lần chạy (PNG, Excel, TXT)
```

---

## Quick Start

### 1. Cài dependencies
```bash
pip install numpy pandas matplotlib requests openpyxl
```

### 2. (Tuỳ chọn) Fetch dữ liệu Binance
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
| `wi` | Tỷ trọng đầu tư vào tài sản i |
| `μi` | Expected return của tài sản i |
| `ρij` | Correlation giữa tài sản i và j |
| `σi` | Standard deviation của tài sản i |

**Ràng buộc:** chọn đúng K=10 tài sản, mỗi tài sản đầu tư tối thiểu 1% (`ε`), tổng tỷ trọng = 1.

---

## Datasets

### Thị trường chứng khoán truyền thống

| Stock Market | N assets |
|---|:---:|
| Hang Seng (Hong Kong) | 31 |
| DAX 100 (Germany) | 85 |
| FTSE 100 (UK) | 89 |
| S&P 100 (USA) | 98 |
| Nikkei 225 (Japan) | 225 |

### Crypto (Binance)

Fetch real-time từ Binance public API — không cần API key. Mặc định gồm 20 cặp lớn nhất (BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOT, ...).

### Format file dataset

```
20                    # số lượng tài sản N
.001309 .043208       # expected return, std dev của asset 1
.004177 .040258       # expected return, std dev của asset 2
...
1 1 1.000000          # correlation giữa asset 1 và asset 1 (diagonal)
1 2 0.562289          # correlation giữa asset 1 và asset 2
...
```

---

## Optimization Algorithms

### Random Search

Sinh ngẫu nhiên `1000×N` nghiệm, mỗi nghiệm chọn K=10 tài sản và phân bổ tỷ trọng ngẫu nhiên. Lấy nghiệm tốt nhất theo hàm mục tiêu f.

- Ưu điểm: đơn giản, không phụ thuộc vào trạng thái ban đầu
- Nhược điểm: không khai thác thông tin từ nghiệm đã tìm được

### Tabu Search

Thuật toán leo đồi có nhớ — bắt đầu từ nghiệm tốt nhất tìm được bởi Random Search, sau đó tìm kiếm "hàng xóm" tốt hơn bằng cách tăng/giảm tỷ trọng 10%.

**Tabu List `L_im[i][m]`:** lưu số bước còn bị cấm cho từng move `(tài sản i, hướng m)`, tránh lặp lại các bước vừa đi.

- Ưu điểm: tốt hơn Random Search về cả return lẫn rủi ro
- Tham số: `L*` (Tabu Tenure) — độ dài Tabu List

### Parameter Optimization (L*)

$$L^* = \{1, 2, 5, 7, 10, 15\}$$

| Dataset | L* tối ưu |
|---|:---:|
| Hang Seng | 5 |
| DAX | 7 |
| FTSE | 7 |
| S&P | 7 |
| Nikkei | 10 |
| Binance crypto | 7 (default) |

Quy tắc kinh nghiệm: L* nằm trong khoảng `[0.5√n, 2√n]` với n là số lượng tài sản.

$$L^* \in \left[0.5\sqrt{n},\ 2\sqrt{n}\right]$$

---

## Efficient Frontier

Chạy với E=50 giá trị λ ∈ [0,1] → ra 50 danh mục tối ưu → vẽ đường Efficient Frontier.

**Hang Seng**
<p align="center">
<img src="imgs/datasets_assets1_Frontier_RS.png" width="700"/> <img src="imgs/datasets_assets1_Frontier_TS.png" width="700"/>
</p>

---
**DAX**
<p align="center">
<img src="imgs/datasets_assets2_Frontier_RS.png" width="700"/> <img src="imgs/datasets_assets2_Frontier_TS.png" width="700"/>
</p>

---
**FTSE**
<p align="center">
<img src="imgs/datasets_assets3_Frontier_RS.png" width="700"/> <img src="imgs/datasets_assets3_Frontier_TS.png" width="700"/>
</p>

---
**S&P**
<p align="center">
<img src="imgs/datasets_assets4_Frontier_RS.png" width="700"/> <img src="imgs/datasets_assets4_Frontier_TS.png" width="700"/>
</p>

---
**Nikkei**
<p align="center">
<img src="imgs/datasets_assets5_Frontier_RS.png" width="700"/> <img src="imgs/datasets_assets5_Frontier_TS.png" width="700"/>
</p>

---

## Market Comparison

<p align="center">
<img src="imgs/MarketComparison.png" alt="Market Comparison" title="Market Comparison"/>
</p>

DAX outperforms hầu hết các thị trường còn lại với return cao và rủi ro thấp. Hang Seng có return cao nhất nhưng đi kèm rủi ro cao hơn — phù hợp cho nhà đầu tư chấp nhận rủi ro.

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
| `*_Q4_AssetsToInvest_*.xlsx` | Danh sách tài sản nên mua |
| `*_Q4_WeightToInvest_*.xlsx` | Tỷ trọng tối ưu từng tài sản |
| `*_Q4_Frontier_RS/TS.png` | Biểu đồ Efficient Frontier |

---

## References

T.-J. Chang, N. Meade, J.E. Beasley, Y.M. Sharaiha, *Heuristics for cardinality constrained portfolio optimisation*, Computers & Operations Research, 27(13):1271–1302, 2000.
https://doi.org/10.1016/S0305-0548(99)00074-X
