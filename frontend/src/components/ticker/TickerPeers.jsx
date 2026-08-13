import TickerLink from './TickerLink'

/**
 * Competitors / Peers table — AI-synthesized list of 5-7 same-industry tickers.
 */
export default function TickerPeers({ tickerData }) {
  const peers = tickerData?.ai_synthesis?.peers || []

  if (!peers.length) {
    return null  // hidden until AI synthesis populates
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="font-semibold mb-3 text-[14px]">Competitors / Peers</div>
      <table className="w-full text-[12.5px]">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Symbol</th>
            <th className="px-2 py-1.5">Name</th>
            <th className="px-2 py-1.5">Focus</th>
          </tr>
        </thead>
        <tbody>
          {peers.map((p, i) => (
            <tr key={i} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold">
                <TickerLink symbol={p.symbol} />
              </td>
              <td className="px-2 py-1.5">{p.name}</td>
              <td className="px-2 py-1.5 text-[var(--color-text-muted)]">{p.focus}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
