# China A-Shares Trending Dashboard

AI驱动的A股ETF交易信号仪表盘。使用Transformer模型自动生成因子公式，通过强化学习优化，输出可解释的交易信号。

## 功能特点

- 🤖 自动因子挖掘：Transformer + Policy Gradient生成最优公式
- 📊 覆盖17只主流ETF：宽基、科技、消费、医药、新能源、金融、债券
- 📈 每日信号更新：强度分级（强烈建议/可考虑/观望）
- 🌐 Web仪表盘：可部署到Vercel的静态页面
- ⏰ 自动化：GitHub Actions每日15:35自动更新

## 快速开始

```bash
# 安装依赖
uv sync

# 训练模型（可选，已内置最优公式）
uv run python times.py

# 查看今日信号
uv run python trading_assistant.py

# 查看单个ETF
uv run python daily_signal.py --symbol 512480
```

## 文件结构

```
├── times.py              # 核心算法：因子挖掘与训练
├── daily_signal.py       # 单ETF信号计算
├── generate_signals.py   # 批量生成所有ETF信号
├── trading_assistant.py  # 交易助手（命令行）
├── verify_algorithm.py   # 算法验证脚本
├── web/                  # Next.js前端
│   ├── app/              # 页面组件
│   └── public/data/      # 信号数据JSON
└── .github/workflows/    # GitHub Actions
```

## 监控ETF列表

| 板块 | ETF |
|------|-----|
| 宽基 | 沪深300(510300)、中证500(510500)、创业板(159915)、科创50(588000) |
| 科技 | 半导体(512480)、芯片(512760)、5G(515050)、军工(512660) |
| 消费 | 白酒(512690)、消费(159928) |
| 医药 | 医药(512010)、创新药(159992) |
| 新能源 | 新能源车(515030)、光伏(159875) |
| 金融 | 证券(512880)、银行(512800) |
| 债券 | 国债(511260) |

## 策略公式

```
ABS(SUB(ABS(VOL_CHG), V_RET))
```

量价背离因子：当成交量变化与价格变化不同步时产生信号。

**特征说明：**
- `VOL_CHG`: 成交量/20日均量 - 1
- `V_RET`: 收益率 × (成交量变化+1)

## 信号解读

| 信号强度 | 含义 | 建议 |
|----------|------|------|
| > 70% | 强信号 | 可考虑建仓 |
| 30-70% | 中等信号 | 观察为主 |
| < 30% | 弱信号 | 空仓等待 |

## 使用建议

1. **时间**：每日14:00-15:00查看信号
2. **仓位**：单只ETF不超过总资金20%
3. **止损**：设置5%止损线
4. **择时**：下跌日买入优于追涨

## 部署到Vercel

```bash
cd web
npm install
npm run build
vercel --prod
```

## 数据源

- [AKShare](https://github.com/akfamily/akshare) - 免费A股数据

## 免责声明

本项目仅供学习研究使用，不构成投资建议。投资有风险，入市需谨慎。

## License

MIT
