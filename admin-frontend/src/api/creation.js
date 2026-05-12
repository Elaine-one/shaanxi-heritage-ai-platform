import request from './request'

export default {
  getList(params) {
    return request.get('/creations/', { params })
  },
  getDetail(id) {
    return request.get(`/creations/${id}/`)
  },
  partialUpdate(id, data) {
    return request.patch(`/creations/${id}/`, data)
  },
  delete(id) {
    return request.delete(`/creations/${id}/`)
  }
}
