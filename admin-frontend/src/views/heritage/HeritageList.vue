<template>
  <div class="heritage-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>非遗项目管理</span>
          <el-button type="primary" @click="$router.push('/heritage/create')">
            <el-icon><Plus /></el-icon>新增项目
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索项目名称" clearable style="width: 200px" @clear="loadData" @keyup.enter="loadData" />
        <el-select v-model="filters.category" placeholder="类别" clearable style="width: 140px" @change="loadData">
          <el-option v-for="c in categories" :key="c.id || c" :label="c.name || c" :value="c.name || c" />
        </el-select>
        <el-select v-model="filters.level" placeholder="级别" clearable style="width: 140px" @change="loadData">
          <el-option v-for="l in levels" :key="l.id || l" :label="l.name || l" :value="l.name || l" />
        </el-select>
        <el-select v-model="filters.region" placeholder="地区" clearable style="width: 140px" @change="loadData">
          <el-option v-for="r in regions" :key="r.id || r" :label="r.name || r" :value="r.name || r" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="项目名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="level" label="级别" width="100" />
        <el-table-column prop="region" label="地区" width="100" />
        <el-table-column prop="batch" label="批次" width="80" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/heritage/${row.id}`)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import heritageApi from '@/api/heritage'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const categories = ref([])
const levels = ref([])
const regions = ref([])

const filters = ref({ search: '', category: '', level: '', region: '' })
const pagination = ref({ page: 1, pageSize: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      search: filters.value.search || undefined,
      category: filters.value.category || undefined,
      level: filters.value.level || undefined,
      region: filters.value.region || undefined
    }
    const data = await heritageApi.getList(params)
    tableData.value = data.results || []
    pagination.value.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function loadFilters() {
  try {
    const [catData, lvlData, regData] = await Promise.all([
      heritageApi.getCategories(),
      heritageApi.getLevels(),
      heritageApi.getRegions()
    ])
    categories.value = catData.categories || catData || []
    levels.value = lvlData.levels || lvlData || []
    regions.value = regData.regions || regData || []
  } catch {
    // ignore
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除「${row.name}」吗？`, '确认删除', { type: 'warning' })
  await heritageApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadData()
  loadFilters()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
