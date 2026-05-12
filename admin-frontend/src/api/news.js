import request from './request'

export default {
  getList(params) {
    return request.get('/news/', { params })
  },
  getDetail(id) {
    return request.get(`/news/${id}/`)
  },
  create(data) {
    return request.post('/news/', data)
  },
  update(id, data) {
    return request.put(`/news/${id}/`, data)
  },
  partialUpdate(id, data) {
    return request.patch(`/news/${id}/`, data)
  },
  delete(id) {
    return request.delete(`/news/${id}/`)
  }
}
