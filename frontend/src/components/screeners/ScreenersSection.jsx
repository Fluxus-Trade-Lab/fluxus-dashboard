import StockbeeRatio from './StockbeeRatio'
import EpisodicPivot from './EpisodicPivot'
import ScreenerSection from './ScreenerSection'

export default function ScreenersSection({ data }) {
  if (!data) return null

  return (
    <div className="flex flex-col gap-2">
      <StockbeeRatio data={data.stockbee_ratio} />

      {data.ep_stockbee && (
        <ScreenerSection title="Episodic Pivot · Stockbee" count={data.ep_stockbee.count}>
          <EpisodicPivot data={data.ep_stockbee} />
        </ScreenerSection>
      )}
      {data.ep_qullamaggie && (
        <ScreenerSection title="Episodic Pivot · Qullamaggie" count={data.ep_qullamaggie.count}>
          <EpisodicPivot data={data.ep_qullamaggie} />
        </ScreenerSection>
      )}
    </div>
  )
}
