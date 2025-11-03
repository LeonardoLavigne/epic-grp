export function formatMoney(value: string | number, currency: string = 'EUR', locale?: string) {
  const v = typeof value === 'string' ? Number(value) : value
  const safe = Number.isFinite(v) ? v : 0
  const loc = locale || (typeof navigator !== 'undefined' ? navigator.language : 'pt-PT')
  try {
    return new Intl.NumberFormat(loc, { style: 'currency', currency }).format(safe)
  } catch {
    return `${safe.toFixed(2)} ${currency}`
  }
}

