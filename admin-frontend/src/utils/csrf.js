function getCsrfToken() {
  const name = 'csrftoken'
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1))
      }
    }
  }
  return null
}

let csrfPromise = null

async function ensureCsrfToken() {
  if (getCsrfToken()) return
  if (csrfPromise) return csrfPromise

  csrfPromise = fetch('/api/auth/csrf/', {
    method: 'GET',
    credentials: 'include'
  })
    .then(() => {})
    .finally(() => { csrfPromise = null })

  return csrfPromise
}

export { getCsrfToken, ensureCsrfToken }
