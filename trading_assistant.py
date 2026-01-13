"""
ETF交易助手 - 下午3点前快速决策
用法: python trading_assistant.py
"""
import json
import os
from datetime import datetime
from generate_signals import generate_all_signals, ETF_LIST, DEFAULT_FORMULA
from daily_signal import decode_formula

def print_header():
    print("\n" + "="*70)
    print("  📊 AlphaGPT ETF交易助手")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)

def print_market_summary(signals):
    """市场总览"""
    etfs = signals['etfs']
    buy_strong = [e for e in etfs if e['signal'] == 'buy' and e['strength'] > 0.7]
    buy_weak = [e for e in etfs if e['signal'] == 'buy' and e['strength'] <= 0.7]
    hold = [e for e in etfs if e['signal'] == 'hold']
    sell = [e for e in etfs if e['signal'] == 'sell']
    
    print("\n【市场总览】")
    print("-"*50)
    print(f"  🟢 强烈做多: {len(buy_strong)} 只")
    print(f"  🟡 可考虑做多: {len(buy_weak)} 只")
    print(f"  ⚪ 观望: {len(hold)} 只")
    print(f"  🔴 空仓: {len(sell)} 只")
    
    # 计算市场情绪
    avg_strength = sum(e['strength'] for e in etfs) / len(etfs) if etfs else 0
    if avg_strength > 0.7:
        mood = "偏多"
        emoji = "📈"
    elif avg_strength > 0.4:
        mood = "震荡"
        emoji = "📊"
    else:
        mood = "偏空"
        emoji = "📉"
    print(f"\n  {emoji} 市场情绪: {mood} (平均强度 {avg_strength*100:.0f}%)")

def print_recommendations(signals):
    """今日推荐"""
    etfs = signals['etfs']
    
    # 按强度排序
    sorted_etfs = sorted(etfs, key=lambda x: -x['strength'])
    
    print("\n【今日推荐 TOP 5】")
    print("-"*50)
    print(f"{'排名':^4} {'ETF':^14} {'板块':^8} {'信号强度':^10} {'日涨跌':^8}")
    print("-"*50)
    
    for i, e in enumerate(sorted_etfs[:5], 1):
        strength_bar = "█" * int(e['strength'] * 10)
        print(f" {i:^3} {e['name']:^14} {e['category']:^8} {strength_bar:10} {e['dayReturn']:>8}")

def print_sector_analysis(signals):
    """板块分析"""
    etfs = signals['etfs']
    
    # 按板块分组
    sectors = {}
    for e in etfs:
        cat = e['category']
        if cat not in sectors:
            sectors[cat] = []
        sectors[cat].append(e)
    
    print("\n【板块分析】")
    print("-"*50)
    
    for sector, items in sectors.items():
        avg_strength = sum(e['strength'] for e in items) / len(items)
        avg_return = sum(float(e['dayReturn'].replace('%', '')) for e in items) / len(items)
        
        if avg_strength > 0.7:
            signal = "🟢 做多"
        elif avg_strength > 0.3:
            signal = "🟡 观望"
        else:
            signal = "🔴 回避"
        
        names = ', '.join(e['name'].replace('ETF', '') for e in items)
        print(f"  {sector:6} | {signal} | 强度 {avg_strength*100:5.1f}% | 涨跌 {avg_return:+5.2f}%")
        print(f"         ↳ {names}")

def print_action_plan(signals):
    """操作建议"""
    etfs = signals['etfs']
    
    # 强烈建议买入
    strong_buy = [e for e in etfs if e['signal'] == 'buy' and e['strength'] > 0.9]
    # 建议观望
    hold = [e for e in etfs if e['signal'] == 'hold']
    # 今日涨幅最大
    top_gainers = sorted(etfs, key=lambda x: -float(x['dayReturn'].replace('%', '')))[:3]
    # 今日跌幅最大
    top_losers = sorted(etfs, key=lambda x: float(x['dayReturn'].replace('%', '')))[:3]
    
    print("\n【操作建议】")
    print("-"*50)
    
    print("\n  ✅ 可重点关注 (信号强度 > 90%):")
    if strong_buy:
        for e in strong_buy[:5]:
            print(f"     • {e['name']} ({e['code']}) - 强度 {e['strength']*100:.0f}%")
    else:
        print("     无")
    
    print("\n  ⏸️ 建议观望:")
    if hold:
        for e in hold:
            print(f"     • {e['name']} ({e['code']}) - 强度 {e['strength']*100:.0f}%")
    else:
        print("     无")
    
    print("\n  📈 今日领涨:")
    for e in top_gainers:
        if float(e['dayReturn'].replace('%', '')) > 0:
            print(f"     • {e['name']} {e['dayReturn']}")
    
    print("\n  📉 今日领跌:")
    for e in top_losers:
        if float(e['dayReturn'].replace('%', '')) < 0:
            print(f"     • {e['name']} {e['dayReturn']}")

def print_trading_guide():
    """交易指南"""
    print("\n【交易时间建议】")
    print("-"*50)
    print("""
  ⏰ 14:00-14:30  查看本工具信号
  ⏰ 14:30-14:50  确认买卖标的
  ⏰ 14:50-14:55  下单执行
  ⏰ 14:55-15:00  确认成交
  
  💡 操作原则:
  1. 只交易"强烈建议"(强度>70%)的ETF
  2. 单只ETF仓位不超过总资金的20%
  3. 下跌日买入优于上涨日追涨
  4. 设置5%止损线
  """)

def main():
    print_header()
    
    # 检查是否有今日数据
    cache_file = 'web/public/data/signals.json'
    need_refresh = True
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached = json.load(f)
            cache_date = cached['updateTime'][:10]
            today = datetime.now().strftime('%Y-%m-%d')
            if cache_date == today:
                signals = cached
                need_refresh = False
                print(f"\n📂 使用缓存数据 (更新于 {cached['updateTime'][11:19]})")
    
    if need_refresh:
        print("\n🔄 获取最新数据...")
        signals = generate_all_signals()
    
    print(f"\n📐 策略公式: {signals['formula']}")
    
    print_market_summary(signals)
    print_recommendations(signals)
    print_sector_analysis(signals)
    print_action_plan(signals)
    print_trading_guide()
    
    print("\n" + "="*70)
    print("  免责声明: 仅供参考，不构成投资建议")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
