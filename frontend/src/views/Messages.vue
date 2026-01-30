<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">消息历史</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-row>
              <v-col cols="12" md="3">
                <v-select
                  v-model="filters.direction"
                  :items="directionOptions"
                  label="消息方向"
                  density="compact"
                  @update:model-value="loadMessages"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="filters.from_user"
                  label="发送者"
                  density="compact"
                  clearable
                  @update:model-value="debouncedLoad"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-btn color="primary" prepend-icon="mdi-refresh" @click="loadMessages">
                  刷新
                </v-btn>
              </v-col>
            </v-row>
          </v-card-title>

          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="messages"
              :loading="loading"
              :items-per-page="filters.page_size"
              :page="filters.page"
              :server-items-length="total"
              @update:page="onPageChange"
              @update:items-per-page="onPageSizeChange"
            >
              <template v-slot:item.direction="{ item }">
                <v-chip :color="item.direction === 'in' ? 'blue' : 'green'" size="small">
                  <v-icon start>{{ item.direction === 'in' ? 'mdi-arrow-down' : 'mdi-arrow-up' }}</v-icon>
                  {{ item.direction === 'in' ? '接收' : '发送' }}
                </v-chip>
              </template>

              <template v-slot:item.msg_type="{ item }">
                <v-chip size="small" variant="outlined">
                  {{ item.msg_type }}
                </v-chip>
              </template>

              <template v-slot:item.content="{ item }">
                <div class="text-truncate" style="max-width: 300px;">
                  {{ item.content }}
                </div>
              </template>

              <template v-slot:item.create_time="{ item }">
                {{ formatTime(item.create_time) }}
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ getStatusText(item.status) }}
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click="viewDetail(item)">
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 消息详情对话框 -->
    <v-dialog v-model="detailDialog" max-width="800">
      <v-card v-if="selectedMessage">
        <v-card-title>消息详情</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <v-list-item-title>消息ID</v-list-item-title>
              <v-list-item-subtitle>{{ selectedMessage.msg_id }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>消息类型</v-list-item-title>
              <v-list-item-subtitle>{{ selectedMessage.msg_type }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>方向</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip :color="selectedMessage.direction === 'in' ? 'blue' : 'green'" size="small">
                  {{ selectedMessage.direction === 'in' ? '接收' : '发送' }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>发送者</v-list-item-title>
              <v-list-item-subtitle>{{ selectedMessage.from_user }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>接收者</v-list-item-title>
              <v-list-item-subtitle>{{ selectedMessage.to_user }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>创建时间</v-list-item-title>
              <v-list-item-subtitle>{{ formatTime(selectedMessage.create_time) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>状态</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip :color="getStatusColor(selectedMessage.status)" size="small">
                  {{ getStatusText(selectedMessage.status) }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            <v-divider class="my-4"></v-divider>
            <v-list-item>
              <v-list-item-title>消息内容</v-list-item-title>
              <v-list-item-subtitle>
                <pre class="mt-2" style="white-space: pre-wrap;">{{ selectedMessage.content }}</pre>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="detailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 提示消息 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import type { Message } from '@/types/api'

const loading = ref(false)
const messages = ref<Message[]>([])
const total = ref(0)
const detailDialog = ref(false)
const selectedMessage = ref<Message | null>(null)

const filters = ref({
  page: 1,
  page_size: 20,
  direction: 'all',
  from_user: '',
})

const directionOptions = [
  { title: '全部', value: 'all' },
  { title: '接收', value: 'in' },
  { title: '发送', value: 'out' },
]

const headers = [
  { title: '方向', key: 'direction', sortable: false },
  { title: '消息类型', key: 'msg_type', sortable: false },
  { title: '发送者', key: 'from_user' },
  { title: '接收者', key: 'to_user' },
  { title: '内容', key: 'content', sortable: false },
  { title: '时间', key: 'create_time' },
  { title: '状态', key: 'status', sortable: false },
  { title: '操作', key: 'actions', sortable: false },
]

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

let debounceTimer: number | null = null

const loadMessages = async () => {
  loading.value = true
  try {
    const params: any = {
      page: filters.value.page,
      page_size: filters.value.page_size,
    }

    if (filters.value.direction !== 'all') {
      params.direction = filters.value.direction
    }

    if (filters.value.from_user) {
      params.from_user = filters.value.from_user
    }

    const response = await apiClient.getMessages(params)
    messages.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载消息失败:', error)
    showSnackbar('加载消息失败', 'error')
  } finally {
    loading.value = false
  }
}

const debouncedLoad = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = window.setTimeout(() => {
    loadMessages()
  }, 500)
}

const onPageChange = (page: number) => {
  filters.value.page = page
  loadMessages()
}

const onPageSizeChange = (pageSize: number) => {
  filters.value.page_size = pageSize
  filters.value.page = 1
  loadMessages()
}

const viewDetail = (message: Message) => {
  selectedMessage.value = message
  detailDialog.value = true
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    sent: 'success',
    received: 'info',
    pending: 'warning',
    failed: 'error',
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    sent: '已发送',
    received: '已接收',
    pending: '待处理',
    failed: '失败',
  }
  return texts[status] || status
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  loadMessages()
})
</script>
