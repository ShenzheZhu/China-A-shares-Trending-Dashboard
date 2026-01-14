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
    # ========== 宽基指数 (15) ==========
    {'code': '510300', 'name': '沪深300ETF', 'category': '宽基'},
    {'code': '510500', 'name': '中证500ETF', 'category': '宽基'},
    {'code': '159915', 'name': '创业板ETF', 'category': '宽基'},
    {'code': '588000', 'name': '科创50ETF', 'category': '宽基'},
    {'code': '510050', 'name': '上证50ETF', 'category': '宽基'},
    {'code': '159919', 'name': '沪深300ETF易方达', 'category': '宽基'},
    {'code': '510330', 'name': '沪深300ETF华夏', 'category': '宽基'},
    {'code': '159901', 'name': '深100ETF', 'category': '宽基'},
    {'code': '512100', 'name': '中证1000ETF', 'category': '宽基'},
    {'code': '560010', 'name': '中证2000ETF', 'category': '宽基'},
    {'code': '159922', 'name': '中证500ETF南方', 'category': '宽基'},
    {'code': '588080', 'name': '科创板50ETF易方达', 'category': '宽基'},
    {'code': '159605', 'name': 'A50ETF', 'category': '宽基'},
    {'code': '512910', 'name': '中证100ETF', 'category': '宽基'},
    {'code': '588050', 'name': '科创芯片ETF', 'category': '宽基'},
    
    # ========== 科技 (20) ==========
    {'code': '512480', 'name': '半导体ETF', 'category': '科技'},
    {'code': '512760', 'name': '芯片ETF', 'category': '科技'},
    {'code': '515050', 'name': '5GETF', 'category': '科技'},
    {'code': '512660', 'name': '军工ETF', 'category': '科技'},
    {'code': '159995', 'name': '芯片ETF华夏', 'category': '科技'},
    {'code': '516160', 'name': '新能源车ETF', 'category': '科技'},
    {'code': '515790', 'name': '光伏ETF易方达', 'category': '科技'},
    {'code': '159611', 'name': '电力ETF', 'category': '科技'},
    {'code': '515170', 'name': '通信ETF', 'category': '科技'},
    {'code': '515880', 'name': '通信设备ETF', 'category': '科技'},
    {'code': '512720', 'name': '计算机ETF', 'category': '科技'},
    {'code': '159998', 'name': '电子ETF', 'category': '科技'},
    {'code': '516110', 'name': '汽车ETF', 'category': '科技'},
    {'code': '515230', 'name': '软件ETF', 'category': '科技'},
    {'code': '159890', 'name': '云计算50ETF', 'category': '科技'},
    {'code': '516850', 'name': '智能电网ETF', 'category': '科技'},
    {'code': '562800', 'name': '机器人ETF', 'category': '科技'},
    {'code': '159515', 'name': '人工智能AIETF', 'category': '科技'},
    {'code': '515980', 'name': '人工智能ETF', 'category': '科技'},
    {'code': '516630', 'name': '国防军工ETF', 'category': '科技'},
    
    # ========== 消费 (12) ==========
    {'code': '512690', 'name': '白酒ETF', 'category': '消费'},
    {'code': '159928', 'name': '消费ETF', 'category': '消费'},
    {'code': '159936', 'name': '黄金消费ETF', 'category': '消费'},
    {'code': '516650', 'name': '养殖ETF', 'category': '消费'},
    {'code': '159825', 'name': '农业ETF', 'category': '消费'},
    {'code': '515710', 'name': '食品饮料ETF', 'category': '消费'},
    {'code': '516980', 'name': '旅游ETF', 'category': '消费'},
    {'code': '159766', 'name': '旅游酒店ETF', 'category': '消费'},
    {'code': '159996', 'name': '家电ETF', 'category': '消费'},
    {'code': '159768', 'name': '服装ETF', 'category': '消费'},
    {'code': '159865', 'name': '港股消费ETF', 'category': '消费'},
    {'code': '159638', 'name': '酒ETF', 'category': '消费'},
    
    # ========== 医药 (12) ==========
    {'code': '512010', 'name': '医药ETF', 'category': '医药'},
    {'code': '159992', 'name': '创新药ETF', 'category': '医药'},
    {'code': '512290', 'name': '生物医药ETF', 'category': '医药'},
    {'code': '516820', 'name': 'CRO创新药ETF', 'category': '医药'},
    {'code': '159883', 'name': '医疗器械ETF', 'category': '医药'},
    {'code': '512170', 'name': '医疗ETF', 'category': '医药'},
    {'code': '516390', 'name': '医疗设备ETF', 'category': '医药'},
    {'code': '159647', 'name': '疫苗ETF', 'category': '医药'},
    {'code': '159828', 'name': '中药ETF', 'category': '医药'},
    {'code': '159938', 'name': '医药卫生ETF', 'category': '医药'},
    {'code': '513120', 'name': '港股医药ETF', 'category': '医药'},
    {'code': '159655', 'name': '生物医药ETF华夏', 'category': '医药'},
    
    # ========== 新能源 (10) ==========
    {'code': '515030', 'name': '新能源车ETF', 'category': '新能源'},
    {'code': '159875', 'name': '光伏ETF', 'category': '新能源'},
    {'code': '516580', 'name': '光伏产业ETF', 'category': '新能源'},
    {'code': '159786', 'name': '风电ETF', 'category': '新能源'},
    {'code': '516090', 'name': '智能汽车ETF', 'category': '新能源'},
    {'code': '159755', 'name': '新能源ETF', 'category': '新能源'},
    {'code': '159637', 'name': '储能ETF', 'category': '新能源'},
    {'code': '159981', 'name': '能源ETF', 'category': '新能源'},
    {'code': '562880', 'name': '电池ETF', 'category': '新能源'},
    {'code': '159870', 'name': '化工ETF', 'category': '新能源'},
    
    # ========== 金融 (10) ==========
    {'code': '512880', 'name': '证券ETF', 'category': '金融'},
    {'code': '512800', 'name': '银行ETF', 'category': '金融'},
    {'code': '512070', 'name': '非银ETF', 'category': '金融'},
    {'code': '515020', 'name': '券商ETF', 'category': '金融'},
    {'code': '512640', 'name': '金融科技ETF', 'category': '金融'},
    {'code': '159931', 'name': '金融ETF', 'category': '金融'},
    {'code': '159841', 'name': '银行ETF华夏', 'category': '金融'},
    {'code': '516510', 'name': '券商龙头ETF', 'category': '金融'},
    {'code': '512980', 'name': '传媒ETF', 'category': '金融'},
    {'code': '159993', 'name': '龙头券商ETF', 'category': '金融'},
    
    # ========== 地产基建 (6) ==========
    {'code': '512200', 'name': '房地产ETF', 'category': '地产'},
    {'code': '159707', 'name': '建材ETF', 'category': '地产'},
    {'code': '516950', 'name': '基建ETF', 'category': '地产'},
    {'code': '516970', 'name': '央企改革ETF', 'category': '地产'},
    {'code': '159732', 'name': '国企一带一路ETF', 'category': '地产'},
    {'code': '516360', 'name': '建筑材料ETF', 'category': '地产'},
    
    # ========== 有色金属 (6) ==========
    {'code': '512400', 'name': '有色金属ETF', 'category': '有色'},
    {'code': '159617', 'name': '钢铁ETF', 'category': '有色'},
    {'code': '516780', 'name': '稀土ETF', 'category': '有色'},
    {'code': '159880', 'name': '黄金ETF', 'category': '有色'},
    {'code': '159812', 'name': '铜ETF', 'category': '有色'},
    {'code': '159671', 'name': '煤炭ETF', 'category': '有色'},
    
    # ========== 债券货币 (5) ==========
    {'code': '511260', 'name': '国债ETF', 'category': '债券'},
    {'code': '511010', 'name': '国债ETF', 'category': '债券'},
    {'code': '511220', 'name': '城投债ETF', 'category': '债券'},
    {'code': '511270', 'name': '10年国债ETF', 'category': '债券'},
    {'code': '511060', 'name': '5年地债ETF', 'category': '债券'},
    
    # ========== 跨境港股 (10) ==========
    {'code': '513050', 'name': '恒生科技ETF', 'category': '港股'},
    {'code': '159920', 'name': '恒生ETF', 'category': '港股'},
    {'code': '513060', 'name': '恒生医疗ETF', 'category': '港股'},
    {'code': '513330', 'name': '港股互联网ETF', 'category': '港股'},
    {'code': '513180', 'name': '恒生科技指数ETF', 'category': '港股'},
    {'code': '164824', 'name': '中概互联ETF', 'category': '港股'},
    {'code': '513100', 'name': '纳指ETF', 'category': '港股'},
    {'code': '513500', 'name': '标普500ETF', 'category': '港股'},
    {'code': '159941', 'name': '纳指100ETF', 'category': '港股'},
    {'code': '513090', 'name': '港股通50ETF', 'category': '港股'},
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
                # 因子值通过tanh压缩到[0,1]区间作为强度
                strength = abs(np.tanh(latest_factor))
                
                # 信号逻辑：基于强度分级
                # 强信号(>0.7): 建议买入
                # 中等信号(0.3-0.7): 观望
                # 弱信号(<0.3): 回避
                if strength > 0.7:
                    signal = 'buy'
                    action = '建议买入'
                elif strength > 0.3:
                    signal = 'hold'
                    action = '观望'
                else:
                    signal = 'sell'
                    action = '回避'
                
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
                    'strength': strength,
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
