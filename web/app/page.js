'use client'
import './globals.css'
import { useState, useEffect } from 'react'

export default function Home() {
  const [signals, setSignals] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [showRules, setShowRules] = useState(false)

  useEffect(() => {
    fetch('/data/signals.json')
      .then(res => res.json())
      .then(data => {
        setSignals(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="header">
          <h1>ALPHAGPT</h1>
          <p className="subtitle">Loading...</p>
        </div>
      </div>
    )
  }

  const getSignalText = (signal, action) => {
    if (signal === 'buy') return `做多`
    if (signal === 'sell') return `空仓`
    return '观望'
  }

  const categories = ['all', ...new Set(signals?.etfs?.map(e => e.category) || [])]
  const filteredETFs = filter === 'all' 
    ? signals?.etfs 
    : signals?.etfs?.filter(e => e.category === filter)

  // 统计
  const buyCount = signals?.etfs?.filter(e => e.signal === 'buy').length || 0
  const holdCount = signals?.etfs?.filter(e => e.signal === 'hold').length || 0
  const total = signals?.etfs?.length || 0

  // 板块分析
  const getSectorAnalysis = () => {
    if (!signals?.etfs) return []
    const sectors = {}
    signals.etfs.forEach(e => {
      if (!sectors[e.category]) {
        sectors[e.category] = { items: [], totalStrength: 0, totalReturn: 0 }
      }
      sectors[e.category].items.push(e)
      sectors[e.category].totalStrength += e.strength
      sectors[e.category].totalReturn += parseFloat(e.dayReturn)
    })
    
    return Object.entries(sectors).map(([name, data]) => ({
      name,
      avgStrength: data.totalStrength / data.items.length,
      avgReturn: data.totalReturn / data.items.length,
      count: data.items.length,
      items: data.items
    })).sort((a, b) => b.avgStrength - a.avgStrength)
  }

  const sectorAnalysis = getSectorAnalysis()

  // 市场情绪判断
  const avgStrength = signals?.etfs?.reduce((a, b) => a + b.strength, 0) / total || 0
  const marketMood = avgStrength > 0.7 ? '偏多' : avgStrength > 0.4 ? '震荡' : '偏空'
  const moodColor = avgStrength > 0.7 ? '#4ade80' : avgStrength > 0.4 ? '#facc15' : '#f87171'

  return (
    <div className="container">
      <header className="header">
        <h1>A股ETF信号仪表盘</h1>
        <p className="subtitle">AI-DRIVEN TRADING SIGNALS</p>
      </header>

      {/* 更新时间状态栏 */}
      <div className="update-bar">
        <div className="update-info">
          <span className="update-label">数据更新时间</span>
          <span className="update-datetime">
            {signals?.updateTime ? new Date(signals.updateTime).toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit', 
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            }) : '-'}
          </span>
        </div>
        <div className="update-status">
          {(() => {
            if (!signals?.updateTime) return <span className="status-unknown">未知</span>
            const updateDate = new Date(signals.updateTime)
            const now = new Date()
            const diffHours = (now - updateDate) / (1000 * 60 * 60)
            const isToday = updateDate.toDateString() === now.toDateString()
            
            if (isToday && diffHours < 12) {
              return <span className="status-fresh">今日已更新</span>
            } else if (diffHours < 24) {
              return <span className="status-recent">24小时内</span>
            } else {
              return <span className="status-stale">数据较旧 ({Math.floor(diffHours / 24)}天前)</span>
            }
          })()}
        </div>
      </div>

      {/* 市场概览 */}
      <div className="overview">
        <div className="stat-card" style={{borderLeftColor: moodColor}}>
          <span className="stat-num">{(avgStrength * 100).toFixed(0)}%</span>
          <span className="stat-label">市场情绪 · {marketMood}</span>
        </div>
        <div className="stat-card buy">
          <span className="stat-num">{buyCount}</span>
          <span className="stat-label">做多信号</span>
        </div>
        <div className="stat-card hold">
          <span className="stat-num">{holdCount}</span>
          <span className="stat-label">观望</span>
        </div>
        <div className="stat-card neutral">
          <span className="stat-num">{total}</span>
          <span className="stat-label">监控ETF</span>
        </div>
      </div>

      {/* 板块分析 */}
      <div className="analysis-section">
        <h3>📊 板块分析</h3>
        <div className="sector-grid">
          {sectorAnalysis.map(sector => {
            const signal = sector.avgStrength > 0.7 ? 'buy' : sector.avgStrength > 0.3 ? 'hold' : 'sell'
            const recommendation = sector.avgStrength > 0.7 
              ? '建议买入' 
              : sector.avgStrength > 0.3 
                ? '建议观望' 
                : '建议回避'
            
            return (
              <div className={`sector-card ${signal}`} key={sector.name}>
                <div className="sector-header">
                  <span className="sector-name">{sector.name}</span>
                  <span className={`sector-signal ${signal}`}>{recommendation}</span>
                </div>
                <div className="sector-stats">
                  <div className="sector-stat">
                    <span className="stat-value">{(sector.avgStrength * 100).toFixed(0)}%</span>
                    <span className="stat-desc">信号强度</span>
                  </div>
                  <div className="sector-stat">
                    <span className={`stat-value ${sector.avgReturn >= 0 ? 'positive' : 'negative'}`}>
                      {sector.avgReturn >= 0 ? '+' : ''}{sector.avgReturn.toFixed(2)}%
                    </span>
                    <span className="stat-desc">今日涨跌</span>
                  </div>
                </div>
                <div className="sector-bar">
                  <div 
                    className={`sector-bar-fill ${signal}`} 
                    style={{width: `${sector.avgStrength * 100}%`}}
                  />
                </div>
                <div className="sector-items">
                  {sector.items.map(e => (
                    <span key={e.code} className="sector-item">
                      {e.name.replace('ETF', '')}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 今日建议 */}
      <div className="recommendation-section">
        <h3>💡 今日操作建议</h3>
        <div className="recommendation-grid">
          <div className="rec-card buy">
            <h4>可考虑买入</h4>
            <ul>
              {signals?.etfs?.filter(e => e.strength > 0.7).slice(0, 5).map(e => (
                <li key={e.code}>
                  <span className="rec-name">{e.name}</span>
                  <span className="rec-code">{e.code}</span>
                  <span className="rec-strength">{(e.strength * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="rec-card hold">
            <h4>建议观望</h4>
            <ul>
              {signals?.etfs?.filter(e => e.strength <= 0.7 && e.strength > 0.3).map(e => (
                <li key={e.code}>
                  <span className="rec-name">{e.name}</span>
                  <span className="rec-code">{e.code}</span>
                  <span className="rec-strength">{(e.strength * 100).toFixed(0)}%</span>
                </li>
              ))}
              {signals?.etfs?.filter(e => e.strength <= 0.7 && e.strength > 0.3).length === 0 && 
                <li className="empty">无</li>
              }
            </ul>
          </div>
          <div className="rec-card avoid">
            <h4>建议回避</h4>
            <ul>
              {signals?.etfs?.filter(e => e.strength <= 0.3).map(e => (
                <li key={e.code}>
                  <span className="rec-name">{e.name}</span>
                  <span className="rec-code">{e.code}</span>
                  <span className="rec-strength">{(e.strength * 100).toFixed(0)}%</span>
                </li>
              ))}
              {signals?.etfs?.filter(e => e.strength <= 0.3).length === 0 && 
                <li className="empty">无</li>
              }
            </ul>
          </div>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="filter-section">
        <h3>📋 ETF详情</h3>
        <div className="filter-bar">
          {categories.map(cat => (
            <button
              key={cat}
              className={`filter-btn ${filter === cat ? 'active' : ''}`}
              onClick={() => setFilter(cat)}
            >
              {cat === 'all' ? '全部' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* ETF卡片 */}
      <div className="grid">
        {filteredETFs?.map((etf) => (
          <div className="card" key={etf.code}>
            <div className="card-header">
              <div className="etf-info">
                <span className="category-tag">{etf.category}</span>
                <h2>{etf.name}</h2>
                <p className="code">{etf.code}</p>
              </div>
              <span className={`signal-badge ${etf.signal}`}>
                {getSignalText(etf.signal, etf.action)}
              </span>
            </div>

            <div className="metrics">
              <div className="metric">
                <p className="metric-label">收盘价</p>
                <p className="metric-value">¥{etf.price}</p>
              </div>
              <div className="metric">
                <p className="metric-label">日涨跌</p>
                <p className={`metric-value ${parseFloat(etf.dayReturn) >= 0 ? 'positive' : 'negative'}`}>
                  {etf.dayReturn}
                </p>
              </div>
              <div className="metric">
                <p className="metric-label">因子值</p>
                <p className={`metric-value ${parseFloat(etf.factor) > 0 ? 'positive' : 'negative'}`}>
                  {etf.factor > 0 ? '+' : ''}{etf.factor}
                </p>
              </div>
              <div className="metric">
                <p className="metric-label">强度</p>
                <p className="metric-value">{(etf.strength * 100).toFixed(0)}%</p>
              </div>
            </div>

            <div className="strength-bar">
              <div className="bar-container">
                <div 
                  className={`bar-fill ${etf.signal}`}
                  style={{ width: `${Math.abs(etf.strength) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 策略规则 */}
      <div className="rules-section">
        <div className="rules-header" onClick={() => setShowRules(!showRules)}>
          <h3>📖 策略原理与规则</h3>
          <span className="toggle">{showRules ? '收起' : '展开'}</span>
        </div>
        
        {showRules && (
          <div className="rules-content">
            <div className="rule-block">
              <h4>1. 核心公式</h4>
              <code>ABS(SUB(ABS(VOL_CHG), V_RET))</code>
              <p>即：|( |成交量变化率| - 量价因子 )|</p>
            </div>

            <div className="rule-block">
              <h4>2. 因子含义</h4>
              <table>
                <tbody>
                  <tr><td>VOL_CHG</td><td>成交量变化率 = 当日成交量 / 20日均量 - 1</td></tr>
                  <tr><td>V_RET</td><td>量价因子 = 日收益率 × (成交量变化+1)</td></tr>
                </tbody>
              </table>
            </div>

            <div className="rule-block">
              <h4>3. 信号逻辑</h4>
              <p><strong>量价背离原理：</strong></p>
              <ul>
                <li>放量不涨：成交量放大但价格没跟上 → 因子值大 → 可能有资金吸筹</li>
                <li>缩量不跌：成交量萎缩但价格稳定 → 因子值大 → 抛压已释放</li>
                <li>量价同步：正常走势 → 因子值小 → 无明显机会</li>
              </ul>
            </div>

            <div className="rule-block">
              <h4>4. 信号强度分级</h4>
              <table>
                <tbody>
                  <tr><td className="level-strong">强度 &gt; 70%</td><td>强信号，可考虑建仓</td></tr>
                  <tr><td className="level-medium">强度 30-70%</td><td>中等信号，观察为主</td></tr>
                  <tr><td className="level-weak">强度 &lt; 30%</td><td>弱信号，建议空仓</td></tr>
                </tbody>
              </table>
            </div>

            <div className="rule-block">
              <h4>5. 操作建议</h4>
              <ul>
                <li><strong>时间：</strong>每日14:00-14:55查看信号并决策</li>
                <li><strong>仓位：</strong>单只ETF不超过总资金20%</li>
                <li><strong>止损：</strong>设置5%止损线</li>
                <li><strong>择时：</strong>下跌日买入优于追涨（信号强+价格跌=抄底机会）</li>
                <li><strong>板块轮动：</strong>优先选择强度最高的板块</li>
              </ul>
            </div>

            <div className="rule-block">
              <h4>6. 注意事项</h4>
              <ul>
                <li>本策略基于量价关系，适合趋势行情</li>
                <li>极端行情（涨跌停、大幅跳空）时谨慎使用</li>
                <li>信号仅供参考，需结合基本面判断</li>
                <li>回测年化7.84%，Sharpe 2.12（2023-2024样本外）</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      <footer className="footer">
        <p className="disclaimer">
          免责声明：本页面仅供学习研究使用，不构成投资建议。投资有风险，入市需谨慎。
        </p>
      </footer>
    </div>
  )
}
