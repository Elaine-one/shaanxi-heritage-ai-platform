import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'heritage',
        name: 'HeritageList',
        component: () => import('@/views/heritage/HeritageList.vue'),
        meta: { title: '非遗项目', icon: 'Collection' }
      },
      {
        path: 'heritage/create',
        name: 'HeritageCreate',
        component: () => import('@/views/heritage/HeritageDetail.vue'),
        meta: { title: '新增非遗项目', hidden: true }
      },
      {
        path: 'heritage/:id',
        name: 'HeritageDetail',
        component: () => import('@/views/heritage/HeritageDetail.vue'),
        meta: { title: '非遗项目详情', hidden: true }
      },
      {
        path: 'news',
        name: 'NewsList',
        component: () => import('@/views/news/NewsList.vue'),
        meta: { title: '新闻资讯', icon: 'Document' }
      },
      {
        path: 'news/create',
        name: 'NewsCreate',
        component: () => import('@/views/news/NewsDetail.vue'),
        meta: { title: '新增资讯', hidden: true }
      },
      {
        path: 'news/:id',
        name: 'NewsDetail',
        component: () => import('@/views/news/NewsDetail.vue'),
        meta: { title: '资讯详情', hidden: true }
      },
      {
        path: 'policy',
        name: 'PolicyList',
        component: () => import('@/views/policy/PolicyList.vue'),
        meta: { title: '政策法规', icon: 'Notebook' }
      },
      {
        path: 'policy/create',
        name: 'PolicyCreate',
        component: () => import('@/views/policy/PolicyDetail.vue'),
        meta: { title: '新增政策', hidden: true }
      },
      {
        path: 'policy/:id',
        name: 'PolicyDetail',
        component: () => import('@/views/policy/PolicyDetail.vue'),
        meta: { title: '政策详情', hidden: true }
      },
      {
        path: 'forum/posts',
        name: 'PostList',
        component: () => import('@/views/forum/PostList.vue'),
        meta: { title: '帖子管理', icon: 'ChatDotRound' }
      },
      {
        path: 'forum/tags',
        name: 'TagList',
        component: () => import('@/views/forum/TagList.vue'),
        meta: { title: '标签管理', icon: 'PriceTag' }
      },
      {
        path: 'forum/announcements',
        name: 'AnnouncementList',
        component: () => import('@/views/forum/AnnouncementList.vue'),
        meta: { title: '公告管理', icon: 'Bell' }
      },
      {
        path: 'forum/rules',
        name: 'RuleList',
        component: () => import('@/views/forum/RuleList.vue'),
        meta: { title: '版规管理', icon: 'List' }
      },
      {
        path: 'forum/reports',
        name: 'ReportList',
        component: () => import('@/views/forum/ReportList.vue'),
        meta: { title: '举报管理', icon: 'Warning' }
      },
      {
        path: 'creation',
        name: 'CreationList',
        component: () => import('@/views/creation/CreationList.vue'),
        meta: { title: '创作管理', icon: 'Picture' }
      },
      {
        path: 'creation/:id',
        name: 'CreationDetail',
        component: () => import('@/views/creation/CreationDetail.vue'),
        meta: { title: '创作详情', hidden: true }
      },
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/user/UserList.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'users/:id',
        name: 'UserDetail',
        component: () => import('@/views/user/UserDetail.vue'),
        meta: { title: '用户详情', hidden: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/vue-admin/'),
  routes
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false) {
    if (!authStore.isLoggedIn) {
      const user = await authStore.fetchUser()
      if (!user) {
        return { name: 'Login', query: { redirect: to.fullPath } }
      }
    }
    if (authStore.user && !authStore.user.is_staff && !authStore.user.is_superuser) {
      authStore.clearUser()
      return { name: 'Login' }
    }
  }

  if (to.name === 'Login' && authStore.isLoggedIn) {
    return { name: 'Dashboard' }
  }
})

export default router
