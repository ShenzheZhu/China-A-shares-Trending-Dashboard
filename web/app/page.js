'use client'
import './globals.css'
import { useState, useEffect } from 'react'

export default function Home() {
  const [signals, setSignals] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

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
    if (signal === 'buy') return `做多 (${action})`
    if (signal === 'sell') return `空仓 (${action})`
    return '观望'
  }

  const categories = ['all', ...new Set(signals?.etfs?.map(e => e.category) || [])]
  const filteredETFs = filter === 'all' 
    ? signals?.etfs 
    : signals?.etfs?.filter(e => e.category === filter)

  // 统计
  const buyCount = signals?.etfs?.filter(e => e.signal === 'buy').length || 0
  const sellCount = signals?.etfs?.filter(e => e.signal === 'sell').length || 0
  const holdCount = signals?.etfs?.filter(e => e.signal === 'hold').length || 0
  const total = signals?.etfs?.length || 0

  return (
    <div className="container">
      <header className="header">
        <h1>ALPHAGPT</h1>
        <p className="subtitle">AI-DRIVEN ETF TRADING SIGNALS</p>
        <p className="update-time">
          更新时间: {signals?.updateTime ? new Date(signals.updateTime).toLocaleString('zh-CN') : '-'}
        </p>
      </header>

      {/* 市场概览 */}
      <div className="overview">
        <div className="stat-card buy">
          <span className="stat-num">{buyCount}</span>
          <span className="stat-label">做多信号</span>
        </div>
        <div className="stat-card hold">
          <span className="stat-num">{holdCount}</span>
          <span className="stat-label">观望</span>
        </div>
        <div className="stat-card sell">
          <span className="stat-num">{sellCount}</span>
          <span className="stat-label">空仓信号</span>
        </div>
        <div className="stat-card neutral">
          <span className="stat-num">{total}</span>
          <span className="stat-label">监控ETF</span>
        </div>
      </div>

      {/* 筛选器 */}
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

      {/* 使用指南 */}
      <div className="guide-section">
        <h3>使用指南</h3>
        <div className="guide-content">
          <div className="guide-item">
            <span className="guide-icon">🟢</span>
            <div>
              <strong>做多信号 (强度 &gt; 70%)</strong>
              <p>可考虑买入或持有</p>
            </div>
          </div>
          <div className="guide-item">
            <span className="guide-icon">⚪</span>
            <div>
              <strong>观望信号 (强度 &lt; 30%)</strong>
              <p>建议空仓等待</p>
            </div>
          </div>
          <div className="guide-item">
            <span className="guide-icon">🔴</span>
            <div>
              <strong>空仓信号</strong>
              <p>建议卖出或回避</p>
            </div>
          </div>
          <div className="guide-item">
            <span className="guide-icon">⏰</span>
            <div>
              <strong>操作时间</strong>
              <p>建议在14:30-14:55之间决策</p>
            </div>
          </div>
        </div>
      </div>

      <div className="formula-section">
        <h3>策略公式</h3>
        <code className="formula-code">{signals?.formula || 'ABS(SUB(ABS(VOL_CHG),V_RET))'}</code>
        <p className="formula-desc">量价背离因子：当成交量变化与价格变化不同步时产生信号</p>
      </div>

      <footer className="footer">
        <p className="disclaimer">
          免责声明：本页面仅供学习研究使用，不构成投资建议。投资有风险，入市需谨慎。
        </p>
      </footer>
    </div>
  )
}
