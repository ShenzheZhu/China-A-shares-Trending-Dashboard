"""
验证算法逻辑正确性
"""
import numpy as np
import pandas as pd
from daily_signal import (
    fetch_data, compute_features, execute_formula, 
    decode_formula, FEATURES, VOCAB, DEVICE
)
import torch

print("="*60)
print("AlphaGPT 算法验证")
print("="*60)

# 1. 公式解析验证
print("\n【1】公式解析验证")
print("-"*40)
formula = [10, 6, 10, 2, 3]  # ABS(SUB(ABS(VOL_CHG), V_RET))
decoded = decode_formula(formula)
print(f"Token序列: {formula}")
print(f"解码公式: {decoded}")
print(f"公式含义: |( |成交量变化率| - 量价因子 )|")
print(f"  - VOL_CHG: 当日成交量 / 20日均量 - 1")
print(f"  - V_RET: 收益率 × (成交量变化+1)")
print(f"  - 当量价背离时(放量不涨或缩量不跌)，因子值较大")

# 2. 特征计算验证
print("\n【2】特征计算验证")
print("-"*40)
df = fetch_data('511260', 'etf', days=30)
print(f"数据条数: {len(df)}")
print(f"最新日期: {df['trade_date'].iloc[-1]}")
print(f"最新收盘: {df['close'].iloc[-1]:.4f}")

feat = compute_features(df)
print(f"\n特征维度: {feat.shape}")
print(f"特征列表: {FEATURES}")

# 显示最新一天的特征值
print(f"\n最新特征值:")
for i, name in enumerate(FEATURES):
    val = feat[i, -1].item()
    print(f"  {name:10s}: {val:+.4f}")

# 3. 公式执行验证
print("\n【3】公式执行验证")
print("-"*40)
factor = execute_formula(formula, feat)
if factor is not None:
    latest = factor[-1].item()
    signal = np.tanh(latest)
    position = np.sign(signal)
    print(f"因子值(最新): {latest:.4f}")
    print(f"信号强度: {signal:.4f}")
    print(f"持仓方向: {'做多' if position > 0 else '做空' if position < 0 else '空仓'}")
    
    # 手动验证公式
    vol_chg = feat[2, -1].item()  # VOL_CHG
    v_ret = feat[3, -1].item()    # V_RET
    manual = abs(abs(vol_chg) - v_ret)
    print(f"\n手动计算验证:")
    print(f"  |VOL_CHG| = |{vol_chg:.4f}| = {abs(vol_chg):.4f}")
    print(f"  V_RET = {v_ret:.4f}")
    print(f"  ||VOL_CHG| - V_RET| = |{abs(vol_chg):.4f} - {v_ret:.4f}| = {manual:.4f}")
    print(f"  公式计算值 = {latest:.4f}")
    print(f"  误差: {abs(manual - latest):.6f}")
else:
    print("公式执行失败!")

# 4. 信号逻辑验证
print("\n【4】信号生成逻辑")
print("-"*40)
print("tanh(因子值) → 信号强度 [-1, 1]")
print("sign(信号强度) → 持仓方向")
print("  > 0: 做多")
print("  < 0: 做空/空仓")
print("  = 0: 观望")

print("\n近5日信号验证:")
for i in range(-5, 0):
    date = df['trade_date'].iloc[i]
    close = df['close'].iloc[i]
    f_val = factor[i].item()
    sig = np.tanh(f_val)
    pos = "多" if sig > 0 else "空"
    print(f"  {date} | 收盘 {close:.4f} | 因子 {f_val:+.3f} | tanh={sig:+.4f} | {pos}")

# 5. 回测逻辑说明
print("\n【5】回测逻辑说明")
print("-"*40)
print("收益计算: Open-to-Open (T日开盘买入, T+1日开盘卖出)")
print("适用于ETF: 可T+0或近似T+0的品种")
print("交易成本: 0.05% (万五双边)")
print("评价指标: Sortino比率 (风险调整后收益)")

# 6. 潜在问题
print("\n【6】潜在问题与建议")
print("-"*40)
print("⚠️ 当前公式特点:")
print("   - 因子值恒为正数 (ABS嵌套)")
print("   - 信号几乎永远是做多")
print("   - 适合单边上涨市场")
print("\n💡 建议:")
print("   - 对于ETF，可以配合大盘趋势过滤")
print("   - 信号强度 < 0.5 时可选择空仓")
print("   - 不同板块应使用不同阈值")

print("\n" + "="*60)
print("验证完成")
print("="*60)
