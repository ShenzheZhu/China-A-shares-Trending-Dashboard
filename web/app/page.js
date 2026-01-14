'use client'
import './globals.css'
import { useState, useEffect } from 'react'

export default function Home() {
  const [signals, setSignals] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
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

  const getSignalText = (signal) => {
    if (signal === 'buy') return '买入'
    if (signal === 'sell') return '回避'
    return '观望'
  }
  
  const getMaSignalText = (signal) => {
    return signal === 'buy' ? '站上MA20' : '跌破MA20'
  }

  const categories = ['all', ...new Set(signals?.etfs?.map(e => e.category) || [])]
  const filteredETFs = (signals?.etfs || [])
    .filter(e => filter === 'all' || e.category === filter)
    .filter(e => !search || 
      e.name.toLowerCase().includes(search.toLowerCase()) || 
      e.code.includes(search)
    )
    .sort((a, b) => b.strength - a.strength)

  // 统计 - 量价因子
  const buyCount = signals?.etfs?.filter(e => e.factorSignal === 'buy').length || 0
  const holdCount = signals?.etfs?.filter(e => e.factorSignal === 'hold').length || 0
  const total = signals?.etfs?.length || 0
  
  // 统计 - MA20均线
  const maAboveCount = signals?.etfs?.filter(e => e.maSignal === 'buy').length || 0
  const maBelowCount = signals?.etfs?.filter(e => e.maSignal === 'sell').length || 0

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
          <span className="stat-label">量价情绪</span>
        </div>
        <div className="stat-card buy">
          <span className="stat-num">{maAboveCount}</span>
          <span className="stat-label">站上MA20</span>
        </div>
        <div className="stat-card sell">
          <span className="stat-num">{maBelowCount}</span>
          <span className="stat-label">跌破MA20</span>
        </div>
        <div className="stat-card neutral">
          <span className="stat-num">{total}</span>
          <span className="stat-label">监控ETF</span>
        </div>
      </div>

      {/* 板块分析 */}
      <div className="analysis-section">
        <h3>📊 板块分析 (MA20趋势)</h3>
        <div className="sector-grid">
          {sectorAnalysis.map(sector => {
            // 计算板块内站上MA20的比例
            const maAbove = sector.items.filter(e => e.maSignal === 'buy').length
            const maRatio = maAbove / sector.count
            const signal = maRatio > 0.7 ? 'buy' : maRatio > 0.3 ? 'hold' : 'sell'
            const recommendation = maRatio > 0.7 
              ? '强势' 
              : maRatio > 0.3 
                ? '震荡' 
                : '弱势'
            
            return (
              <div className={`sector-card ${signal}`} key={sector.name}>
                <div className="sector-header">
                  <span className="sector-name">{sector.name}</span>
                  <span className={`sector-signal ${signal}`}>{recommendation}</span>
                </div>
                <div className="sector-stats">
                  <div className="sector-stat">
                    <span className="stat-value">{maAbove}/{sector.count}</span>
                    <span className="stat-desc">站上MA20</span>
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
                    style={{width: `${maRatio * 100}%`}}
                  />
                </div>
                <div className="sector-items">
                  {sector.items.map(e => (
                    <span key={e.code} className={`sector-item ${e.maSignal === 'buy' ? 'above' : 'below'}`}>
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
        <h3>💡 今日操作建议 (MA20趋势策略)</h3>
        <div className="recommendation-grid">
          <div className="rec-card buy">
            <h4>站上MA20 - 持有</h4>
            <ul>
              {signals?.etfs?.filter(e => e.maSignal === 'buy').slice(0, 10).map(e => (
                <li key={e.code}>
                  <span className="rec-name">{e.name}</span>
                  <span className="rec-code">{e.code}</span>
                  <span className="rec-strength">{e.maDiff}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="rec-card avoid">
            <h4>跌破MA20 - 空仓</h4>
            <ul>
              {signals?.etfs?.filter(e => e.maSignal === 'sell').slice(0, 10).map(e => (
                <li key={e.code}>
                  <span className="rec-name">{e.name}</span>
                  <span className="rec-code">{e.code}</span>
                  <span className="rec-strength">{e.maDiff}</span>
                </li>
              ))}
              {signals?.etfs?.filter(e => e.maSignal === 'sell').length === 0 && 
                <li className="empty">无</li>
              }
            </ul>
          </div>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="filter-section">
        <h3>📋 ETF详情 <span className="etf-count">共 {filteredETFs.length} 个</span></h3>
        <div className="search-bar">
          <input 
            type="text"
            placeholder="搜索ETF名称或代码..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
          {search && (
            <button className="clear-btn" onClick={() => setSearch('')}>×</button>
          )}
        </div>
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
              <div className="dual-signals">
                <span className={`signal-badge small ${etf.maSignal}`} title="MA20趋势">
                  {getMaSignalText(etf.maSignal)}
                </span>
              </div>
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
                <p className="metric-label">MA20</p>
                <p className="metric-value">¥{etf.ma20}</p>
              </div>
              <div className="metric">
                <p className="metric-label">偏离MA20</p>
                <p className={`metric-value ${parseFloat(etf.maDiff) >= 0 ? 'positive' : 'negative'}`}>
                  {etf.maDiff}
                </p>
              </div>
            </div>

            <div className="dual-strategy">
              <div className={`strategy-item ${etf.maSignal}`}>
                <span className="strategy-label">趋势策略</span>
                <span className="strategy-value">{etf.maSignal === 'buy' ? '持有' : '空仓'}</span>
              </div>
              <div className={`strategy-item ${etf.factorSignal}`}>
                <span className="strategy-label">量价因子</span>
                <span className="strategy-value">{getSignalText(etf.factorSignal)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 使用说明 */}
      <div className="rules-section">
        <div className="rules-header" onClick={() => setShowRules(!showRules)}>
          <h3>📖 使用说明</h3>
          <span className="toggle">{showRules ? '收起' : '展开'}</span>
        </div>
        
        {showRules && (
          <div className="rules-content">
            <div className="rule-block">
              <h4>市场情绪解读</h4>
              <table>
                <tbody>
                  <tr><td className="level-strong">情绪 &gt; 70%</td><td>市场整体偏多，可积极参与</td></tr>
                  <tr><td className="level-medium">情绪 40-70%</td><td>市场震荡，谨慎操作</td></tr>
                  <tr><td className="level-weak">情绪 &lt; 40%</td><td>市场偏空，建议观望</td></tr>
                </tbody>
              </table>
            </div>

            <div className="rule-block">
              <h4>信号强度说明</h4>
              <table>
                <tbody>
                  <tr><td className="level-strong">强度 &gt; 70%</td><td>强信号，可考虑建仓</td></tr>
                  <tr><td className="level-medium">强度 30-70%</td><td>中等信号，观察为主</td></tr>
                  <tr><td className="level-weak">强度 &lt; 30%</td><td>弱信号，建议空仓</td></tr>
                </tbody>
              </table>
            </div>

            <div className="rule-block">
              <h4>操作建议</h4>
              <ul>
                <li><strong>时间：</strong>每日14:00-14:55查看信号并决策</li>
                <li><strong>仓位：</strong>单只ETF不超过总资金20%</li>
                <li><strong>止损：</strong>设置5%止损线</li>
                <li><strong>择时：</strong>信号强+价格下跌时可能是较好买点</li>
                <li><strong>板块轮动：</strong>优先关注强度最高的板块</li>
              </ul>
            </div>

            <div className="rule-block">
              <h4>注意事项</h4>
              <ul>
                <li>信号基于AI量化模型生成</li>
                <li>极端行情时谨慎使用</li>
                <li>信号仅供参考，需结合自身判断</li>
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
