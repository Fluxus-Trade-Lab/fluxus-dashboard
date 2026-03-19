import StockbeeRatio from './StockbeeRatio'
import EpisodicPivot from './EpisodicPivot'
import ScreenerSection from './ScreenerSection'

export default function ScreenersSection({ data }) {
  if (!data) return null

  return (
    <div className="flex flex-col gap-2">
      <StockbeeRatio data={data.stockbee_ratio} />

      {data.episodic_pivot && (
        <ScreenerSection title="Episodic Pivot" count={data.episodic_pivot.count}>
          <EpisodicPivot data={data.episodic_pivot} />
        </ScreenerSection>
      )}
    </div>
  )
}
