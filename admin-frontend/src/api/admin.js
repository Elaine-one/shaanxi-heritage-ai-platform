import request from './request'

export default {
  login(data) {
    return request.post('/admin/login/', data)
  },
  getStats() {
    return request.get('/admin/stats/')
  },
  getOperationLogs(params) {
    return request.get('/admin/operation-logs/', { params })
  },

  getUsers(params) {
    return request.get('/admin/users/', { params })
  },
  getUserDetail(id) {
    return request.get(`/admin/users/${id}/`)
  },
  createUser(data) {
    return request.post('/admin/users/create/', data)
  },
  updateUser(id, data) {
    return request.patch(`/admin/users/${id}/`, data)
  },
  resetPassword(id, data) {
    return request.post(`/admin/users/${id}/reset-password/`, data)
  },

  getTags() {
    return request.get('/admin/forum/tags/')
  },
  createTag(data) {
    return request.post('/admin/forum/tags/', data)
  },
  updateTag(id, data) {
    return request.patch(`/admin/forum/tags/${id}/`, data)
  },
  deleteTag(id) {
    return request.delete(`/admin/forum/tags/${id}/`)
  },

  getAnnouncements() {
    return request.get('/admin/forum/announcements/')
  },
  createAnnouncement(data) {
    return request.post('/admin/forum/announcements/', data)
  },
  updateAnnouncement(id, data) {
    return request.patch(`/admin/forum/announcements/${id}/`, data)
  },
  deleteAnnouncement(id) {
    return request.delete(`/admin/forum/announcements/${id}/`)
  },

  getRules() {
    return request.get('/admin/forum/rules/')
  },
  createRule(data) {
    return request.post('/admin/forum/rules/', data)
  },
  updateRule(id, data) {
    return request.patch(`/admin/forum/rules/${id}/`, data)
  },
  deleteRule(id) {
    return request.delete(`/admin/forum/rules/${id}/`)
  },

  getReports(params) {
    return request.get('/admin/forum/reports/', { params })
  },
  getReportDetail(id) {
    return request.get(`/admin/forum/reports/${id}/`)
  },
  handleReport(id, data) {
    return request.patch(`/admin/forum/reports/${id}/`, data)
  },

  getPosts(params) {
    return request.get('/admin/forum/posts/', { params })
  },
  getPostDetail(id) {
    return request.get(`/admin/forum/posts/${id}/`)
  },
  updatePost(id, data) {
    return request.patch(`/admin/forum/posts/${id}/`, data)
  },
  deletePost(id) {
    return request.delete(`/admin/forum/posts/${id}/`)
  },

  getCreations(params) {
    return request.get('/admin/creations/', { params })
  },
  getCreationDetail(id) {
    return request.get(`/admin/creations/${id}/`)
  },
  updateCreation(id, data) {
    return request.patch(`/admin/creations/${id}/`, data)
  },
  deleteCreation(id) {
    return request.delete(`/admin/creations/${id}/`)
  },
}
