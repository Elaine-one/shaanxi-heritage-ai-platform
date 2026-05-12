import request from './request'

export default {
  getPosts(params) {
    return request.get('/forum/posts/', { params })
  },
  getPostDetail(id) {
    return request.get(`/forum/posts/${id}/`)
  },
  deletePost(id) {
    return request.delete(`/forum/posts/${id}/`)
  },
  updatePostStatus(id, status) {
    return request.patch(`/forum/posts/${id}/`, { status })
  },
  togglePin(id) {
    return request.post(`/forum/posts/${id}/pin/`)
  },
  toggleFeature(id) {
    return request.post(`/forum/posts/${id}/feature/`)
  },
  getTags(params) {
    return request.get('/forum/tags/', { params })
  },
  getAnnouncements(params) {
    return request.get('/forum/announcements/', { params })
  },
  getRules(params) {
    return request.get('/forum/rules/', { params })
  },
  getReports(params) {
    return request.get('/forum/reports/', { params })
  },
  handleReport(id, data) {
    return request.patch(`/forum/reports/${id}/`, data)
  }
}
