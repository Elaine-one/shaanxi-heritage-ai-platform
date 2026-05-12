import dayjs from 'dayjs'

export function formatDate(value) {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

export function formatShortDate(value) {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD')
}

export function truncate(str, length = 50) {
  if (!str) return '-'
  return str.length > length ? str.substring(0, length) + '...' : str
}
