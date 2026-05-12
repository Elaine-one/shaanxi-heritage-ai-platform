import request from './request'

export default {
  getCsrfToken() {
    return request.get('/auth/csrf/')
  },
  generateCaptcha() {
    return request.get('/auth/captcha/generate/')
  },
  adminLogin(data) {
    return request.post('/admin/login/', data)
  },
  login(data) {
    return request.post('/auth/login/', data)
  },
  logout() {
    return request.post('/auth/logout/')
  },
  getUser() {
    return request.get('/auth/user/')
  }
}
