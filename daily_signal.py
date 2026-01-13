"""
每日信号计算脚本
用法: python daily_signal.py [--symbol 511260] [--type etf]
"""
import akshare as ak
import pandas as pd
import numpy as np
import torch
import argparse
from datetime import datetime, timedelta

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========== 算子定义（与 times.py 保持一致）==========
@torch.jit.script
def _ts_delay(x: torch.Tensor, d: int) -> torch.Tensor:
    if d == 0: return x
    pad = torch.zeros((x.shape[0], d), device=x.device)
    return torch.cat([pad, x[:, :-d]], dim=1)

@torch.jit.script
def _ts_delta(x: torch.Tensor, d: int) -> torch.Tensor:
    return x - _ts_delay(x, d)

@torch.jit.script
def _ts_zscore(x: torch.Tensor, d: int) -> torch.Tensor:
    if d <= 1: return torch.zeros_like(x)
    B, T = x.shape
    pad = torch.zeros((B, d - 1), device=x.device)
    x_pad = torch.cat([pad, x], dim=1)
    windows = x_pad.unfold(1, d, 1)
    mean = windows.mean(dim=-1)
    std = windows.std(dim=-1) + 1e-6
    return (x - mean) / std

@torch.jit.script
def _ts_decay_linear(x: torch.Tensor, d: int) -> torch.Tensor:
    if d <= 1: return x
    B, T = x.shape
    pad = torch.zeros((B, d - 1), device=x.device)
    x_pad = torch.cat([pad, x], dim=1)
    windows = x_pad.unfold(1, d, 1)
    w = torch.arange(1, d + 1, device=x.device, dtype=x.dtype)
    w = w / w.sum()
    return (windows * w).sum(dim=-1)

OPS_CONFIG = [
    ('ADD', lambda x, y: x + y, 2),
    ('SUB', lambda x, y: x - y, 2),
    ('MUL', lambda x, y: x * y, 2),
    ('DIV', lambda x, y: x / (y + 1e-6 * torch.sign(y)), 2),
    ('NEG', lambda x: -x, 1),
    ('ABS', lambda x: torch.abs(x), 1),
    ('SIGN', lambda x: torch.sign(x), 1),
    ('DELTA5', lambda x: _ts_delta(x, 5), 1),
    ('MA20',   lambda x: _ts_decay_linear(x, 20), 1),
    ('STD20',  lambda x: _ts_zscore(x, 20), 1),
    ('TS_RANK20', lambda x: _ts_zscore(x, 20), 1),
]

FEATURES = ['RET', 'RET5', 'VOL_CHG', 'V_RET', 'TREND']
VOCAB = FEATURES + [cfg[0] for cfg in OPS_CONFIG]
OP_FUNC_MAP = {i + len(FEATURES): cfg[1] for i, cfg in enumerate(OPS_CONFIG)}
OP_ARITY_MAP = {i + len(FEATURES): cfg[2] for i, cfg in enumerate(OPS_CONFIG)}


def fetch_data(symbol: str, symbol_type: str, days: int = 120):
    """获取最近N天行情数据"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    print(f"📡 获取 {symbol} 最近 {days} 天数据...")
    
    if symbol_type == 'etf':
        df = ak.fund_etf_hist_em(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'vol'
        })
    elif symbol_type == 'stock':
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'vol'
        })
    else:  # index
        df = ak.stock_zh_index_daily(symbol=symbol)
        df = df.rename(columns={'date': 'trade_date', 'volume': 'vol'})
        df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
    
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df


def compute_features(df: pd.DataFrame) -> torch.Tensor:
    """计算特征张量"""
    close = df['close'].values.astype(np.float32)
    vol = df['vol'].values.astype(np.float32)
    
    # RET: 日收益率
    ret = np.zeros_like(close)
    ret[1:] = (close[1:] - close[:-1]) / (close[:-1] + 1e-6)
    
    # RET5: 5日收益率
    ret5 = pd.Series(close).pct_change(5).fillna(0).values.astype(np.float32)
    
    # VOL_CHG: 成交量变化
    vol_ma = pd.Series(vol).rolling(20).mean().values
    vol_chg = np.zeros_like(vol)
    mask = vol_ma > 0
    vol_chg[mask] = vol[mask] / vol_ma[mask] - 1
    vol_chg = np.nan_to_num(vol_chg).astype(np.float32)
    
    # V_RET: 量价因子
    v_ret = (ret * (vol_chg + 1)).astype(np.float32)
    
    # TREND: 趋势因子
    ma60 = pd.Series(close).rolling(60).mean().values
    trend = np.zeros_like(close)
    mask = ma60 > 0
    trend[mask] = close[mask] / ma60[mask] - 1
    trend = np.nan_to_num(trend).astype(np.float32)
    
    def robust_norm(x):
        x = x.astype(np.float32)
        median = np.nanmedian(x)
        mad = np.nanmedian(np.abs(x - median)) + 1e-6
        res = (x - median) / mad
        return np.clip(res, -5, 5).astype(np.float32)
    
    feat_data = torch.stack([
        torch.from_numpy(robust_norm(ret)).to(DEVICE),
        torch.from_numpy(robust_norm(ret5)).to(DEVICE),
        torch.from_numpy(robust_norm(vol_chg)).to(DEVICE),
        torch.from_numpy(robust_norm(v_ret)).to(DEVICE),
        torch.from_numpy(robust_norm(trend)).to(DEVICE)
    ])
    
    return feat_data


def execute_formula(tokens: list, feat_data: torch.Tensor):
    """执行公式，返回因子值"""
    stack = []
    try:
        for t in reversed(tokens):
            if t < len(FEATURES):
                stack.append(feat_data[t])
            else:
                arity = OP_ARITY_MAP[t]
                if len(stack) < arity:
                    raise ValueError("栈不足")
                args = [stack.pop() for _ in range(arity)]
                func = OP_FUNC_MAP[t]
                if arity == 2:
                    res = func(args[0], args[1])
                else:
                    res = func(args[0])
                if torch.isnan(res).any():
                    res = torch.nan_to_num(res)
                stack.append(res)
        
        if len(stack) >= 1:
            return stack[-1]
    except Exception as e:
        print(f"公式执行错误: {e}")
    return None


def decode_formula(tokens: list) -> str:
    """将token序列解码为可读公式"""
    stream = list(tokens)
    def _parse():
        if not stream:
            return ""
        t = stream.pop(0)
        if t < len(FEATURES):
            return FEATURES[t]
        args = [_parse() for _ in range(OP_ARITY_MAP[t])]
        return f"{VOCAB[t]}({','.join(args)})"
    try:
        return _parse()
    except:
        return "Invalid"


def main():
    parser = argparse.ArgumentParser(description='每日信号计算')
    parser.add_argument('--symbol', type=str, default='511260', help='标的代码')
    parser.add_argument('--type', type=str, default='etf', choices=['etf', 'index', 'stock'], help='标的类型')
    parser.add_argument('--formula', type=str, default=None, help='公式token（JSON格式），留空则从训练结果读取')
    args = parser.parse_args()
    
    # 1. 加载公式
    # 默认公式: ABS(SUB(ABS(VOL_CHG), V_RET)) -> [10, 6, 10, 2, 3]
    # FEATURES: RET=0, RET5=1, VOL_CHG=2, V_RET=3, TREND=4
    # OPS: ADD=5, SUB=6, MUL=7, DIV=8, NEG=9, ABS=10, SIGN=11, DELTA5=12, MA20=13, STD20=14, TS_RANK20=15
    DEFAULT_FORMULA = [10, 6, 10, 2, 3]  # ABS(SUB(ABS(VOL_CHG), V_RET))
    
    if args.formula:
        import json
        best_formula = json.loads(args.formula)
    else:
        best_formula = DEFAULT_FORMULA
        print(f"📌 使用默认公式（训练所得最优）")
    
    print(f"\n📊 标的: {args.symbol} ({args.type})")
    print(f"📐 公式: {decode_formula(best_formula)}")
    print(f"🔢 Token: {best_formula}\n")
    
    # 2. 获取数据
    df = fetch_data(args.symbol, args.type, days=120)
    print(f"✅ 数据获取完成，共 {len(df)} 条记录")
    print(f"   时间范围: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}")
    
    # 3. 计算特征
    feat_data = compute_features(df)
    
    # 4. 执行公式
    factor = execute_formula(best_formula, feat_data)
    if factor is None:
        print("❌ 公式执行失败")
        return
    
    # 5. 生成信号
    latest_factor = factor[-1].item()
    signal = np.tanh(latest_factor)
    position = np.sign(signal)
    
    # 6. 输出结果
    print("\n" + "="*50)
    print("📈 今日信号")
    print("="*50)
    print(f"日期: {df['trade_date'].iloc[-1]}")
    print(f"收盘价: {df['close'].iloc[-1]:.4f}")
    print(f"因子值: {latest_factor:.4f}")
    print(f"信号强度: {signal:.4f}")
    print("-"*50)
    
    if position > 0:
        print("🟢 建议: 做多 (BUY)")
    elif position < 0:
        print("🔴 建议: 做空/空仓 (SELL)")
    else:
        print("⚪ 建议: 观望 (HOLD)")
    
    print("="*50)
    
    # 7. 显示近5日信号历史
    print("\n📅 近5日信号历史:")
    print("-"*50)
    for i in range(-5, 0):
        date = df['trade_date'].iloc[i]
        close = df['close'].iloc[i]
        f_val = factor[i].item()
        sig = np.tanh(f_val)
        pos = "多" if sig > 0 else "空"
        print(f"  {date} | 收盘 {close:.4f} | 因子 {f_val:+.3f} | {pos}")


if __name__ == "__main__":
    main()
