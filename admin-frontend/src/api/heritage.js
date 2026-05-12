import request from './request'

export default {
  getList(params) {
    return request.get('/items/', { params })
  },
  getDetail(id) {
    return request.get(`/items/${id}/`)
  },
  create(data) {
    return request.post('/items/', data)
  },
  update(id, data) {
    return request.put(`/items/${id}/`, data)
  },
  partialUpdate(id, data) {
    return request.patch(`/items/${id}/`, data)
  },
  delete(id) {
    return request.delete(`/items/${id}/`)
  },
  getCategories() {
    return request.get('/items/categories/')
  },
  getLevels() {
    return request.get('/items/levels/')
  },
  getRegions() {
    return request.get('/items/regions/')
  }
}
