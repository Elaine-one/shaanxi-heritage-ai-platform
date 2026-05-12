<template>
  <div class="sidebar-container">
    <div class="logo">
      <div class="logo-emblem" v-if="!appStore.sidebarCollapsed">非遗</div>
      <div class="logo-emblem-mini" v-else>非</div>
      <span v-if="!appStore.sidebarCollapsed" class="logo-text">管理后台</span>
    </div>
    <el-scrollbar class="menu-scrollbar">
      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        background-color="#1a1a2e"
        text-color="#8B9BB4"
        active-text-color="#C5963A"
        router
      >
        <template v-for="item in menuItems" :key="item.path">
          <el-sub-menu v-if="item.children" :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
              <el-icon><component :is="child.icon" /></el-icon>
              <span>{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)

const menuItems = [
  { path: '/', title: '仪表盘', icon: 'Odometer' },
  { path: '/heritage', title: '非遗项目', icon: 'Collection' },
  { path: '/news', title: '新闻资讯', icon: 'Document' },
  { path: '/policy', title: '政策法规', icon: 'Notebook' },
  {
    path: '/forum',
    title: '论坛管理',
    icon: 'ChatDotRound',
    children: [
      { path: '/forum/posts', title: '帖子管理', icon: 'ChatDotRound' },
      { path: '/forum/tags', title: '标签管理', icon: 'PriceTag' },
      { path: '/forum/announcements', title: '公告管理', icon: 'Bell' },
      { path: '/forum/rules', title: '版规管理', icon: 'List' },
      { path: '/forum/reports', title: '举报管理', icon: 'Warning' }
    ]
  },
  { path: '/creation', title: '创作管理', icon: 'Picture' },
  { path: '/users', title: '用户管理', icon: 'User' }
]
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background-color: #16213e;
  border-bottom: 1px solid rgba(197, 150, 58, 0.2);
}

.logo-emblem {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #8B2500, #A9442A);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C5963A;
  font-size: 13px;
  font-weight: 700;
  border: 1.5px solid #C5963A;
  flex-shrink: 0;
}

.logo-emblem-mini {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #8B2500, #A9442A);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C5963A;
  font-size: 16px;
  font-weight: 700;
  border: 1.5px solid #C5963A;
}

.logo-text {
  color: #C5963A;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 3px;
}

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

.menu-scrollbar :deep(.el-scrollbar__thumb) {
  background-color: rgba(197, 150, 58, 0.3);
}

.menu-scrollbar :deep(.el-scrollbar__thumb:hover) {
  background-color: rgba(197, 150, 58, 0.5);
}

.el-menu {
  border-right: none;
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(197, 150, 58, 0.1) !important;
  border-right: 3px solid #C5963A;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(197, 150, 58, 0.08) !important;
}

:deep(.el-sub-menu__title:hover) {
  background-color: rgba(197, 150, 58, 0.08) !important;
}
</style>
