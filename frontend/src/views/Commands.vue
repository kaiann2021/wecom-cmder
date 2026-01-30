<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">命令管理</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-row>
              <v-col cols="12" md="6">
                <span>命令列表</span>
              </v-col>
              <v-col cols="12" md="6" class="text-right">
                <v-btn color="success" prepend-icon="mdi-sync" @click="syncMenu" :loading="syncing">
                  同步菜单到企业微信
                </v-btn>
                <v-btn color="primary" prepend-icon="mdi-refresh" @click="loadCommands" class="ml-2">
                  刷新
                </v-btn>
              </v-col>
            </v-row>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col
                v-for="command in commandsByCategory"
                :key="command.category"
                cols="12"
                md="6"
                lg="4"
              >
                <v-card variant="outlined">
                  <v-card-title class="bg-grey-lighten-4">
                    <v-icon start>mdi-folder</v-icon>
                    {{ command.category }}
                  </v-card-title>
                  <v-card-text>
                    <v-list density="compact">
                      <v-list-item
                        v-for="cmd in command.commands"
                        :key="cmd.command_id"
                      >
                        <template v-slot:prepend>
                          <v-switch
                            v-model="cmd.enabled"
                            color="primary"
                            hide-details
                            @update:model-value="updateCommand(cmd)"
                          ></v-switch>
                        </template>

                        <v-list-item-title>
                          {{ cmd.name }}
                          <v-chip
                            v-if="cmd.admin_only"
                            size="x-small"
                            color="warning"
                            class="ml-2"
                          >
                            管理员
                          </v-chip>
                        </v-list-item-title>
                        <v-list-item-subtitle>
                          {{ cmd.description }}
                        </v-list-item-subtitle>

                        <template v-slot:append>
                          <v-btn
                            icon="mdi-arrow-up"
                            size="x-small"
                            variant="text"
                            @click="moveUp(cmd)"
                            :disabled="isFirst(cmd)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-arrow-down"
                            size="x-small"
                            variant="text"
                            @click="moveDown(cmd)"
                            :disabled="isLast(cmd)"
                          ></v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <v-alert v-if="commands.length === 0 && !loading" type="info" class="mt-4">
              暂无命令
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>菜单预览</v-card-title>
          <v-card-text>
            <v-alert type="info" density="compact" class="mb-4">
              企业微信菜单最多支持3个一级菜单，每个一级菜单最多5个子菜单
            </v-alert>

            <v-row>
              <v-col
                v-for="(category, index) in menuPreview"
                :key="index"
                cols="12"
                md="4"
              >
                <v-card variant="outlined">
                  <v-card-title class="text-center bg-primary">
                    {{ category.name }}
                  </v-card-title>
                  <v-list density="compact">
                    <v-list-item
                      v-for="(item, idx) in category.sub_button"
                      :key="idx"
                    >
                      <v-list-item-title>
                        {{ idx + 1 }}. {{ item.name }}
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 提示消息 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/api/client'
import type { Command } from '@/types/api'

const loading = ref(false)
const syncing = ref(false)
const commands = ref<Command[]>([])

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

// 按分类分组命令
const commandsByCategory = computed(() => {
  const grouped: Record<string, Command[]> = {}

  commands.value.forEach(cmd => {
    if (!grouped[cmd.category]) {
      grouped[cmd.category] = []
    }
    grouped[cmd.category].push(cmd)
  })

  // 按 sort_order 排序
  Object.keys(grouped).forEach(category => {
    grouped[category].sort((a, b) => a.sort_order - b.sort_order)
  })

  return Object.keys(grouped).map(category => ({
    category,
    commands: grouped[category],
  }))
})

// 菜单预览
const menuPreview = computed(() => {
  const preview: any[] = []

  commandsByCategory.value.slice(0, 3).forEach(group => {
    const enabledCommands = group.commands.filter(cmd => cmd.enabled).slice(0, 5)
    if (enabledCommands.length > 0) {
      preview.push({
        name: group.category,
        sub_button: enabledCommands.map(cmd => ({
          name: cmd.name,
          key: cmd.command_id,
        })),
      })
    }
  })

  return preview
})

const loadCommands = async () => {
  loading.value = true
  try {
    const response = await apiClient.getCommands()
    commands.value = response.commands
  } catch (error) {
    console.error('加载命令失败:', error)
    showSnackbar('加载命令失败', 'error')
  } finally {
    loading.value = false
  }
}

const updateCommand = async (command: Command) => {
  try {
    await apiClient.updateCommand(command.command_id, {
      enabled: command.enabled,
      sort_order: command.sort_order,
    })
    showSnackbar('命令更新成功', 'success')
  } catch (error) {
    console.error('更新命令失败:', error)
    showSnackbar('更新命令失败', 'error')
    // 恢复原状态
    command.enabled = !command.enabled
  }
}

const moveUp = async (command: Command) => {
  const categoryCommands = commands.value.filter(c => c.category === command.category)
  const index = categoryCommands.findIndex(c => c.command_id === command.command_id)

  if (index > 0) {
    const prevCommand = categoryCommands[index - 1]
    const tempOrder = command.sort_order
    command.sort_order = prevCommand.sort_order
    prevCommand.sort_order = tempOrder

    try {
      await Promise.all([
        apiClient.updateCommand(command.command_id, { sort_order: command.sort_order }),
        apiClient.updateCommand(prevCommand.command_id, { sort_order: prevCommand.sort_order }),
      ])
      showSnackbar('排序更新成功', 'success')
      loadCommands()
    } catch (error) {
      console.error('更新排序失败:', error)
      showSnackbar('更新排序失败', 'error')
    }
  }
}

const moveDown = async (command: Command) => {
  const categoryCommands = commands.value.filter(c => c.category === command.category)
  const index = categoryCommands.findIndex(c => c.command_id === command.command_id)

  if (index < categoryCommands.length - 1) {
    const nextCommand = categoryCommands[index + 1]
    const tempOrder = command.sort_order
    command.sort_order = nextCommand.sort_order
    nextCommand.sort_order = tempOrder

    try {
      await Promise.all([
        apiClient.updateCommand(command.command_id, { sort_order: command.sort_order }),
        apiClient.updateCommand(nextCommand.command_id, { sort_order: nextCommand.sort_order }),
      ])
      showSnackbar('排序更新成功', 'success')
      loadCommands()
    } catch (error) {
      console.error('更新排序失败:', error)
      showSnackbar('更新排序失败', 'error')
    }
  }
}

const isFirst = (command: Command) => {
  const categoryCommands = commands.value.filter(c => c.category === command.category)
  return categoryCommands[0]?.command_id === command.command_id
}

const isLast = (command: Command) => {
  const categoryCommands = commands.value.filter(c => c.category === command.category)
  return categoryCommands[categoryCommands.length - 1]?.command_id === command.command_id
}

const syncMenu = async () => {
  syncing.value = true
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
  } finally {
    syncing.value = false
  }
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  loadCommands()
})
</script>
