import { useMemo } from 'react'
import { useShortlist } from '../hooks/useShortlist'
import { useShortlistFile } from '../hooks/useShortlistFile'
import { myShortlist } from '../components/watchlist/shortlist/manualCards'

/** The tickers on 我的短名单, as Today's List shows them (see myShortlist). */
export function useMyShortlist() {
  const { names, dropped } = useShortlist()
  const { data } = useShortlistFile()
  return useMemo(() => myShortlist(names, dropped, data).map((c) => c.ticker),
    [names, dropped, data])
}
