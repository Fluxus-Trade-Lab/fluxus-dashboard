import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Name } from './WatchlistPage'

// DATA ALEX 09-18: TML follows Moglen 2020; `top20_industry` ships on every
// panel row as a mark ("often in the Top 20 Industry groups"), not a filter.
describe('top-20 industry mark', () => {
  it('shows T20 when the row carries the flag', () => {
    const { container } = render(<Name row={{ ticker: 'CRWD', rs_1m: 97, top20_industry: true }} />)
    expect(container.textContent).toContain('T20')
  })
  it('stays silent without it', () => {
    const { container } = render(<Name row={{ ticker: 'CRWD', rs_1m: 97, top20_industry: false }} />)
    expect(container.textContent).not.toContain('T20')
  })
})
