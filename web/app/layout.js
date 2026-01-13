export const metadata = {
  title: 'AlphaGPT Signal',
  description: 'AI驱动的ETF交易信号',
}

export default function RootLayout({ children }) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  )
}
