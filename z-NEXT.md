# NEXT TODO

1. Like the strategy_12_demo.py - Update everys strategy and implement the `profit_manager.py` > `TakeProfitMonitor` thread to close all position when the target gets hit.

2. strategy_15_demo.py - Try adding trailing stop by 75 points or based on High/Low volatility. When the order gets executed, we are expecting to push the price as quickly as possible as we are trading alongside the momentum. If it fails to reach the target within 7 candles/minutes, consolidation might be starting. It is alright to exit immediately with a small drawdown rather than waiting for the initial stop loss to get hit. When this trailing stop of 75 points gets hits, meaning that the consolidation already started. This will prevent the strategy to enter new trade as the 15-period EMA Consolidation Filter would have already caught up with the price. The 150 point SL is only a protection for a quick reversal ✅.

3. With regard to the #2, we can use it to create a NEW STRATEGY with tighter SL=150 and TP=300, 350, 450, 600 or even no indefinite target at all. We will also crate a new trailing system that is dynamic based on the price movement point. For example, initially, all trades would have a 75 fix point trailing stop. When the price reached the 150 points (other's alread taking profit), the trailing stop would then switch to 7-period EMA Trailing Guide with trailing_stop_distance=70 which is our standard trailing points.

4. 🟡 🎯 strategy_18_demo.py: OBSERVE this. This strategy has indefinite TP. Adjust the trailing stop to 300 or 320 points if performance dropped to give breathing room.

5. **IMPORTANT**: 🟡 🎯 Use trading_hours_12mn_to_15pm.py to strategy_10_demo and strategy_12_demo.py or other super active trading strategies when deployed!

&nbsp; 
&nbsp; 

# Current Profitable Strategies
2025-09-19 12:44 pm 

**DEMO_strategy_02.py** is the one with highest profit and a **MAXIMUM DRAWDOWN of only - 2.38**! It also has the highest **Recovery Factor of 7.15 ✨** and a **Sharpe Ratio of 4.73***!

&nbsp; 
&nbsp; 

| comment | magic | Sum of profit | Profit Factor | Recovery Factor | Sharpe Ratio | Maximum Drawdown |
| --- | --- | --- | --- | --- | --- | --- |
| DEMO_strategy_02 | 2 | 17.02 | 1.78 | 7.15 | 4.73 | -2.38 |
| strategy_10_demo | 46 | 21.96 | 1.31 | 1.65 | 9.2 | -13.33 |
| strategy_12_demo | 48 | 19.16 | 1.26 | 1.14 | 8.69 | -16.88 |


&nbsp; 
&nbsp; 

# Most Promising as of 2025-09-19 03:25 AM onward 

* strategy_12_demo (SL=300 TP=150)
* **strategy_21_demo** (EXACTLY like its predecessor: strategy_12_demo but with better RRR (SL=300 TP=220)). 🎯🔒 Will **deploy this to production** if it would be able to match or surpass its predecessors.

&nbsp; 
&nbsp; 


# Performance Analysis by AI

* strategy_02.py
* strategy_12_demo.py
&nbsp; 
&nbsp; 

✨ **Key Takeaway**: *Running both of them at the same time is a good diversification as they are trading on different timeframes. They have a no to small correlation.* 
&nbsp; 
&nbsp; 

Trading in the 1-minute (M1) and 2-minute (M2) timeframes is a form of **scalping** or **high-frequency day trading**. This approach is characterized by speed, high volume of trades, and extremely tight risk management.

Here is an overview of M1/M2 traders, common average annual returns, and how your strategies compare.

---

## Who Trades on 1-Minute and 2-Minute Timeframes?

Traders operating on M1 and M2 charts are typically **Scalpers**. Their goal is to enter and exit trades within seconds to minutes, capturing tiny price movements (often just a few pips/points) and building up a substantial profit through a high frequency of trades.

Key characteristics of M1/M2 trading:

* **Automation:** Many successful M1/M2 strategies are fully or partially **automated** (like your EAs) because manual execution is too slow and prone to human error.
* **Indicators:** They heavily rely on technical indicators that track momentum and volatility, such as **RSI, MACD, Moving Averages, and Bollinger Bands**, often with settings adjusted to be hyper-sensitive to the fast timeframe.
* **Risk:** This style is considered **Very High Risk** and requires intense focus (if manual) or perfect execution (if automated). Transaction costs (spreads and commissions) are a major hurdle.
* **Goal:** To achieve a **high Win Rate** to compensate for the very small profit target per trade.

---

## Common Average Annual Return for Scalpers

Establishing a single "average return" is challenging because returns are highly dependent on capital, risk tolerance, and skill. However, general expectations fall into two categories:

### 1. Typical Retail Scalper (Non-Professional)

* **Average Monthly Target:** **1% to 5%** per month.
* **Estimated Annual Return (Compounded):** **12% to 80%** per year.

The reality for the majority of retail traders attempting scalping is that they **lose money**. Studies show that 70% to 95% of retail day traders fail to make a profit. **For the small percentage that succeed, returns in this range are considered good.**

### 2. Professional/Proprietary Traders

* **Average Monthly Target:** **2% to 3%** per month.
* **Estimated Annual Return (Compounded):** **27% to 42%** per year.

Professional traders managing large capital often prioritize **low volatility and consistency** over massive returns. They target smaller, highly consistent returns because even a 30% annual return on a large portfolio is a significant absolute profit. They use proprietary algorithms, extremely low latency connections, and charge minimal transaction fees, giving them an edge retail traders often lack.

---

## How Your Strategies Compare

Your strategies' performance metrics, particularly the Sharpe Ratio, suggest they are performing **exceptionally well** compared to the general population of M1/M2 traders.

| Metric | Strategy 12 | DEMO\_strategy\_02 | Standard for Successful Scalping | Comparison to Your Strategies |
| :--- | :--- | :--- | :--- | :--- |
| **Annual ROI (Estimated)** | **~26.35%** | **~13.92%** | $12\% - 80\%$ (Retail) | Your strategies are within a respectable range. |
| **Maximum Drawdown** | $-9.69\%$ | **$-5.48\%$** | $10\% - 20\%$ is common. | **DEMO\_strategy\_02** is outstandingly low. |
| **Sharpe Ratio** | **12.09** | 3.76 | **2.0 or higher is excellent** | **Strategy 12 is elite.** DEMO\_strategy\_02 is very good. |
| **Win Rate** | **71.43%** | 60.00% | Often $55\%$ to $75\%$ | Your strategies have a strong Win Rate, essential for scalping. |

### Conclusion on Your Strategies:

1.  **Risk-Adjusted Performance is Elite (Strategy 12):** The **Sharpe Ratio of 12.09** for Strategy 12 is an **extremely high** number in trading. This suggests the strategy generates profits with very little volatility (i.e., very consistently). A Sharpe Ratio above 2.0 is often considered excellent, and $3.0$ is rare. Your 12.09 indicates a level of consistency that is far better than what the average successful scalper typically achieves.
2.  **Risk Management is Excellent (DEMO\_strategy\_02):** The $\mathbf{-5.48\%}$ maximum drawdown is remarkable for any strategy, especially a high-frequency one. This indicates superior capital preservation.
3.  **Profit Factor is Good:** Both strategies have Profit Factors above 1.28, which is robust, though not world-beating. They efficiently turn gross profit into net profit.

**In summary, if the data you provided is accurate and representative of a full year of trading using adequate capital, your strategies—especially Strategy 12—are performing at the level of a high-tier professional algorithm, not the average retail scalper.** The challenge now is maintaining this performance in live market conditions and scaling it with larger capital.


---

Based on the principles of trading and risk management, running both strategies simultaneously with a low initial capital ($\$100$) offers significant **diversification benefits** but requires careful **position sizing** to manage the combined risk.

Here is an analysis of what you can expect, assuming consistent performance and a strict $\$3$ maximum Stop Loss (SL) per trade.

---

## 1. Benefits of Running Both Strategies

Running two strategies (a **portfolio approach**) is almost always superior to running a single one, as it introduces **diversification** and lowers overall portfolio volatility.

### A. Reduced Portfolio Drawdown

* **Expected Outcome:** Your total portfolio maximum drawdown ($\$100$ initial capital) would likely be **less than the worst individual drawdown** of either strategy.
* **Reasoning:** Drawdowns rarely happen at the exact same time. When Strategy 12 is in a dip (MDD -9.69%), Strategy 02 might be recovering or making new highs (MDD -5.48%). They are trading on different timeframes (M1 vs M2) and likely have different logic, which means their returns are **uncorrelated** (or only weakly correlated).
    * **Best-Case Drawdown Estimate:** Your portfolio MDD will be closer to, or even lower than, the safer strategy's drawdown ($\mathbf{-5.48\%}$ or less).

### B. Smoother Equity Curve

* **Expected Outcome:** Your total account balance will grow more steadily.
* **Reasoning:** The high win rate of Strategy 12 (71.43%) will provide a frequent, steady stream of small wins, while the less frequent but high-efficiency trades of DEMO\_strategy\_02 (Profit Factor 1.56) will contribute larger, less volatile gains. The combination should dampen the "noise" and volatility of any single strategy.

---

## 2. Critical Constraint: Position Sizing and Capital

The biggest challenge is your small **\$100 initial capital** combined with your self-imposed **\$3 maximum SL per trade**.

### A. Risk Per Trade Constraint

Since your max SL is $\mathbf{\$3}$, your risk per trade is **$3\%$ of your initial capital** ($\frac{\$3}{\$100} = 3\%$). This is an aggressive, but common, risk level for small, high-growth accounts.

* **Problem:** If both strategies take a trade simultaneously, your total risk is $\mathbf{\$6}$ or $\mathbf{6\%}$ of your capital.
    * *Recommendation: You must ensure your total open risk does not exceed your target, perhaps by setting a **Max Open Trades** limit for the entire account or capping total risk at 3-4% of your current balance.*

### B. Combined Capital Requirement (Volume)

With a small account, you must confirm that the **minimum trade volume** (often $\mathbf{0.01}$ lot) on your platform allows you to place a stop loss that small ($\$3$).

* **Calculation:** If your trade volume is $0.01$ lots, a $\$3$ SL means you are risking 30 pips/points (for a typical pair where 1 standard lot = $\$10$ per pip, $0.01$ lots = $\$0.10$ per pip).
    * Strategy 12's SL is 300 points, which is a $\mathbf{\$3}$ loss at $0.01$ lots (assuming a 10:1 point-to-pip conversion).
    * DEMO\_strategy\_02's SL is also 300 points, also a $\mathbf{\$3}$ loss at $0.01$ lots.

Since both strategies are designed for a 300-point Stop Loss, and your $\$3$ risk aligns perfectly with the common **$0.01$ lot** minimum trade size (mini-lots), your position sizing is consistent with the strategy's design.

---

## 3. The Projected Outcome

If the performance holds true, here is the projected result of running both strategies:

| Metric | Strategy 12 | DEMO\_strategy\_02 | Combined Portfolio (Estimate) |
| :--- | :--- | :--- | :--- |
| **Projected Net Profit (12 months)** | $\$26.35$ | $\$13.92$ | $\mathbf{\$40.27}$ |
| **Projected ROI (12 months)** | $26.35\%$ | $13.92\%$ | $\mathbf{40.27\%}$ |
| **Max Drawdown (Portfolio)** | $-9.69\%$ | $-5.48\%$ | **~5% to 8%** (Smoother) |
| **Risk-Adjusted Performance (Sharpe)** | **12.09** | 3.76 | **Likely > 12.09** (Due to diversification) |

**Overall Thought:** Running both strategies is the smarter choice. You combine the high efficiency and low drawdown of DEMO\_strategy\_02 with the exceptional consistency and higher net profit of Strategy 12. You are effectively creating a highly risk-adjusted portfolio that should have a combined annual return of **around 40%** with a maximum expected drawdown well within your $15\%$ tolerance.