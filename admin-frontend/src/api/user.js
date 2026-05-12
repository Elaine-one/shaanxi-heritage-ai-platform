import request from './request'

export default {
  getList(params) {
    return request.get('/admin/users/', { params })
  },
  getDetail(id) {
    return request.get(`/admin/users/${id}/`)
  },
  partialUpdate(id, data) {
    return request.patch(`/admin/users/${id}/`, data)
  }
}
