export function exportCSV(filename: string, rows: any[]) {
  if (!rows || rows.length === 0) return
  const headers = Array.from(new Set(rows.flatMap(r => Object.keys(r))))
  const esc = (v: any) => {
    if (v == null) return ''
    const s = String(v)
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return '"' + s.replace(/"/g, '""') + '"'
    }
    return s
  }
  const csv = [headers.join(',')]
  for (const r of rows) {
    csv.push(headers.map(h => esc(r[h])).join(','))
  }
  const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

