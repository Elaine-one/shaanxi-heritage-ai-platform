import request from './request'

export default {
  getList(params) {
    return request.get('/policies/', { params })
  },
  getDetail(id) {
    return request.get(`/policies/${id}/`)
  },
  create(data) {
    return request.post('/policies/', data)
  },
  update(id, data) {
    return request.put(`/policies/${id}/`, data)
  },
  partialUpdate(id, data) {
    return request.patch(`/policies/${id}/`, data)
  },
  delete(id) {
    return request.delete(`/policies/${id}/`)
  }
}
