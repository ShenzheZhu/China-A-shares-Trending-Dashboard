"""
生成信号数据供Web展示
用法: python generate_signals.py
输出: web/public/data/signals.json
"""
import json
import os
from datetime import datetime
from daily_signal import (
    fetch_data, compute_features, execute_formula, 
    decode_formula, DEVICE
)

ETF_LIST = [
    # 宽基指数
    {'code': '510300', 'name': '沪深300ETF', 'category': '宽基'},
    {'code': '510500', 'name': '中证500ETF', 'category': '宽基'},
    {'code': '159915', 'name': '创业板ETF', 'category': '宽基'},
    {'code': '588000', 'name': '科创50ETF', 'category': '宽基'},
    # 科技板块
    {'code': '512480', 'name': '半导体ETF', 'category': '科技'},
    {'code': '512760', 'name': '芯片ETF', 'category': '科技'},
    {'code': '515050', 'name': '5GETF', 'category': '科技'},
    {'code': '512660', 'name': '军工ETF', 'category': '科技'},
    # 消费医药
    {'code': '512690', 'name': '白酒ETF', 'category': '消费'},
    {'code': '159928', 'name': '消费ETF', 'category': '消费'},
    {'code': '512010', 'name': '医药ETF', 'category': '医药'},
    {'code': '159992', 'name': '创新药ETF', 'category': '医药'},
    # 新能源
    {'code': '515030', 'name': '新能源车ETF', 'category': '新能源'},
    {'code': '159875', 'name': '光伏ETF', 'category': '新能源'},
    # 金融地产
    {'code': '512880', 'name': '证券ETF', 'category': '金融'},
    {'code': '512800', 'name': '银行ETF', 'category': '金融'},
    # 债券
    {'code': '511260', 'name': '国债ETF', 'category': '债券'},
]

# 最优公式: ABS(SUB(ABS(VOL_CHG), V_RET))
DEFAULT_FORMULA = [10, 6, 10, 2, 3]

import numpy as np

def generate_all_signals():
    results = {
        'updateTime': datetime.now().isoformat(),
        'etfs': []
    }
    
    for etf in ETF_LIST:
        print(f"处理 {etf['code']} {etf['name']}...")
        try:
            df = fetch_data(etf['code'], 'etf', days=120)
            feat_data = compute_features(df)
            factor = execute_formula(DEFAULT_FORMULA, feat_data)
            
            if factor is not None:
                latest_factor = factor[-1].item()
                signal_strength = np.tanh(latest_factor)
                
                # 改进信号逻辑：考虑信号强度阈值
                # 强信号(>0.7): 建议操作
                # 中等信号(0.3-0.7): 可选操作
                # 弱信号(<0.3): 观望
                abs_strength = abs(float(signal_strength))
                if abs_strength > 0.7:
                    signal = 'buy' if signal_strength > 0 else 'sell'
                    action = '强烈建议'
                elif abs_strength > 0.3:
                    signal = 'buy' if signal_strength > 0 else 'sell'
                    action = '可考虑'
                else:
                    signal = 'hold'
                    action = '观望'
                
                # 计算日涨跌幅
                if len(df) >= 2:
                    day_return = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
                else:
                    day_return = 0
                
                results['etfs'].append({
                    'code': etf['code'],
                    'name': etf['name'],
                    'category': etf.get('category', '其他'),
                    'price': f"{df['close'].iloc[-1]:.4f}",
                    'dayReturn': f"{day_return:+.2f}%",
                    'factor': f"{latest_factor:.4f}",
                    'strength': abs_strength,
                    'signal': signal,
                    'action': action,
                    'date': str(df['trade_date'].iloc[-1])
                })
            else:
                print(f"  ⚠️ {etf['code']} 公式执行失败")
        except Exception as e:
            print(f"  ❌ {etf['code']} 错误: {e}")
    
    # 确保输出目录存在
    os.makedirs('web/public/data', exist_ok=True)
    
    # 写入JSON
    output_path = 'web/public/data/signals.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 信号数据已生成: {output_path}")
    print(f"   共 {len(results['etfs'])} 个ETF")
    
    return results

if __name__ == "__main__":
    generate_all_signals()
