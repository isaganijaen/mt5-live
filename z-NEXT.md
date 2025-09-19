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