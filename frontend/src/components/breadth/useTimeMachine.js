import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { sliceToDate } from './sliceReplay'

const PLAY_INTERVAL_MS = 500

export function useTimeMachine() {
  const [replay, setReplay] = useState(null)
  const [active, setActive] = useState(false)
  const [date, setDateState] = useState(null)
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const dates = replay?.dates ?? []

  const engage = useCallback(async () => {
    setActive(true)
    if (replay) return
    setLoading(true)
    try {
      const res = await fetch('/data/output/breadth_replay.json')
      if (!res.ok) throw new Error(`replay fetch failed: ${res.status}`)
      const json = await res.json()
      setReplay(json)
      setDateState(json.dates[json.dates.length - 1])
      setError(null)
    } catch (err) {
      setError(err.message)
      setActive(false)
    } finally {
      setLoading(false)
    }
  }, [replay])

  const setDate = useCallback((d) => {
    setPlaying(false)
    setDateState(d)
  }, [])

  const step = useCallback((delta) => {
    setPlaying(false)
    setDateState((cur) => {
      const i = dates.indexOf(cur)
      if (i === -1) return cur
      const next = Math.min(Math.max(i + delta, 0), dates.length - 1)
      return dates[next]
    })
  }, [dates])

  const togglePlay = useCallback(() => setPlaying((p) => !p), [])

  const jumpYtd = useCallback(() => {
    setPlaying(false)
    if (!dates.length) return
    const year = dates[dates.length - 1].slice(0, 4)
    const first = dates.find((d) => d.startsWith(year))
    if (first) setDateState(first)
  }, [dates])

  const exitToLatest = useCallback(() => {
    setPlaying(false)
    setActive(false)
    if (dates.length) setDateState(dates[dates.length - 1])
  }, [dates])

  useEffect(() => {
    if (!playing) return undefined
    timerRef.current = setInterval(() => {
      setDateState((cur) => {
        const i = dates.indexOf(cur)
        if (i === -1 || i >= dates.length - 1) {
          setPlaying(false)
          return cur
        }
        return dates[i + 1]
      })
    }, PLAY_INTERVAL_MS)
    return () => clearInterval(timerRef.current)
  }, [playing, dates])

  const sliced = useMemo(
    () => (active && replay && date ? sliceToDate(replay, date) : null),
    [active, replay, date],
  )

  return { active, date, dates, playing, loading, error, sliced,
           engage, setDate, step, togglePlay, jumpYtd, exitToLatest }
}
