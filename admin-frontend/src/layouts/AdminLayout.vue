<template>
  <el-container class="admin-layout">
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header class="header">
        <Header />
      </el-header>
      <el-main class="main-content">
        <el-scrollbar>
          <router-view />
        </el-scrollbar>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.sidebar {
  background-color: #1a1a2e;
  transition: width 0.3s;
  overflow: hidden;
  border-right: 1px solid rgba(197, 150, 58, 0.15);
}

.header {
  background: #fff;
  border-bottom: 2px solid #8B2500;
  padding: 0 20px;
  display: flex;
  align-items: center;
  height: 56px;
}

.main-content {
  background: #F5F0E8;
  padding: 0;
  overflow: hidden;
}

.main-content :deep(.el-scrollbar) {
  height: 100%;
}

.main-content :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.main-content :deep(.el-scrollbar__view) {
  padding: 20px;
}
</style>
