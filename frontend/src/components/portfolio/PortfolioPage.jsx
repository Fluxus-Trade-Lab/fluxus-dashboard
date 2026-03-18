import { PortfolioProvider } from './context/PortfolioContext'
import PortfolioLayout from './PortfolioLayout'

export default function PortfolioPage() {
  return (
    <PortfolioProvider>
      <PortfolioLayout />
    </PortfolioProvider>
  )
}
