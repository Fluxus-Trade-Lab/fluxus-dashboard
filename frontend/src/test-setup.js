import '@testing-library/jest-dom/vitest'

/**
 * A real localStorage for the test environment.
 *
 * jsdom here exposes a `localStorage` object with none of Storage's methods —
 * no getItem, no setItem, no clear. Every store on this site wraps its access
 * in try/catch (a quota error must not eat a keystroke), so under test they did
 * not fail: they silently did nothing, and any assertion about persistence was
 * passing on an empty read. Found while testing the writing store's merge.
 */
if (typeof localStorage === 'undefined' || typeof localStorage.getItem !== 'function') {
  const store = new Map()
  const shim = {
    getItem: (k) => (store.has(String(k)) ? store.get(String(k)) : null),
    setItem: (k, v) => { store.set(String(k), String(v)) },
    removeItem: (k) => { store.delete(String(k)) },
    clear: () => store.clear(),
    key: (i) => [...store.keys()][i] ?? null,
    get length() { return store.size },
  }
  Object.defineProperty(globalThis, 'localStorage', {
    value: shim, writable: true, configurable: true,
  })
  if (typeof window !== 'undefined') {
    Object.defineProperty(window, 'localStorage', {
      value: shim, writable: true, configurable: true,
    })
  }
}
