import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement matchMedia at all. Default to "desktop" (no
// media query matches) so existing tests are unaffected; tests that need
// mobile behavior override this per-test via vi.stubGlobal('matchMedia', ...).
window.matchMedia ??= ((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => false,
})) as typeof window.matchMedia
