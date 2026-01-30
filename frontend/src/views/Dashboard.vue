<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">仪表盘</h1>
      </v-col>
    </v-row>

    <!-- 统计卡片 -->
    <v-row>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">系统状态</div>
            <div class="text-h5">
              <v-chip :color="systemStatus.color" size="small">
                {{ systemStatus.text }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">今日消息</div>
            <div class="text-h5">{{ todayMessages }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">启用命令</div>
            <div class="text-h5">{{ enabledCommands }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">管理员数量</div>
            <div class="text-h5">{{ adminCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 最近消息 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>最近消息</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="messageHeaders"
              :items="recentMessages"
              :loading="loading"
              :items-per-page="5"
              density="compact"
            >
              <template v-slot:item.direction="{ item }">
                <v-chip :color="item.direction === 'in' ? 'blue' : 'green'" size="small">
                  {{ item.direction === 'in' ? '接收' : '发送' }}
                </v-chip>
              </template>
              <template v-slot:item.create_time="{ item }">
                {{ formatTime(item.create_time) }}
              </template>
              <template v-slot:item.content="{ item }">
                {{ truncate(item.content, 50) }}
              </template>
            </v-data-table>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" variant="text" to="/messages">查看全部</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 快捷操作 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>快捷操作</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <v-btn block color="primary" prepend-icon="mdi-cog" to="/config">
                  配置管理
                </v-btn>
              </v-col>
              <v-col cols="12" md="3">
                <v-btn block color="success" prepend-icon="mdi-sync" @click="syncMenu">
                  同步菜单
                </v-btn>
              </v-col>
              <v-col cols="12" md="3">
                <v-btn block color="info" prepend-icon="mdi-send" @click="showSendDialog = true">
                  发送消息
                </v-btn>
              </v-col>
              <v-col cols="12" md="3">
                <v-btn block color="warning" prepend-icon="mdi-refresh" @click="loadData">
                  刷新数据
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 发送消息对话框 -->
    <v-dialog v-model="showSendDialog" max-width="600">
      <v-card>
        <v-card-title>发送消息</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="sendForm.to_user"
            label="接收者UserID"
            hint="留空则发送给所有人"
            persistent-hint
          ></v-text-field>
          <v-textarea
            v-model="sendForm.content"
            label="消息内容"
            rows="5"
            class="mt-4"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showSendDialog = false">取消</v-btn>
          <v-btn color="primary" @click="sendMessage" :loading="sending">发送</v-btn>
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
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/api/client'
import type { Message } from '@/types/api'

const loading = ref(false)
const sending = ref(false)
const showSendDialog = ref(false)
const recentMessages = ref<Message[]>([])
const commands = ref<any[]>([])
const config = ref<any>(null)

const sendForm = ref({
  to_user: '@all',
  content: '',
})

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

const messageHeaders = [
  { title: '方向', key: 'direction', sortable: false },
  { title: '发送者', key: 'from_user' },
  { title: '消息类型', key: 'msg_type' },
  { title: '内容', key: 'content', sortable: false },
  { title: '时间', key: 'create_time' },
]

// 计算属性
const systemStatus = computed(() => {
  return { text: '运行中', color: 'success' }
})

const todayMessages = computed(() => {
  const today = new Date().setHours(0, 0, 0, 0) / 1000
  return recentMessages.value.filter(m => m.create_time >= today).length
})

const enabledCommands = computed(() => {
  return commands.value.filter(c => c.enabled).length
})

const adminCount = computed(() => {
  return config.value?.admin_users?.length || 0
})

// 方法
const loadData = async () => {
  loading.value = true
  try {
    // 加载最近消息
    const messagesRes = await apiClient.getMessages({ page: 1, page_size: 5 })
    recentMessages.value = messagesRes.items

    // 加载命令列表
    const commandsRes = await apiClient.getCommands()
    commands.value = commandsRes.commands

    // 加载配置
    config.value = await apiClient.getWeChatConfig()
  } catch (error) {
    console.error('加载数据失败:', error)
    showSnackbar('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

const syncMenu = async () => {
  try {
    const result = await apiClient.syncMenu()
    if (result.success) {
      showSnackbar(`菜单同步成功，共 ${result.menu_count} 个命令`, 'success')
    } else {
      showSnackbar(result.message, 'error')
    }
  } catch (error) {
    console.error('同步菜单失败:', error)
    showSnackbar('同步菜单失败', 'error')
  }
}

const sendMessage = async () => {
  if (!sendForm.value.content) {
    showSnackbar('请输入消息内容', 'warning')
    return
  }

  sending.value = true
  try {
    const result = await apiClient.sendMessage({
      type: 'text',
      to_user: sendForm.value.to_user || '@all',
      content: sendForm.value.content,
    })

    if (result.success) {
      showSnackbar('消息发送成功', 'success')
      showSendDialog.value = false
      sendForm.value.content = ''
      loadData()
    } else {
      showSnackbar(result.message || '消息发送失败', 'error')
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    showSnackbar('发送消息失败', 'error')
  } finally {
    sending.value = false
  }
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

const truncate = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

onMounted(() => {
  loadData()
})
</script>
