<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">配置管理</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>企业微信配置</v-card-title>
          <v-card-text>
            <v-form ref="formRef" v-model="formValid">
              <v-text-field
                v-model="form.corp_id"
                label="企业ID (CorpID)"
                :rules="[rules.required]"
                hint="在企业微信管理后台「我的企业」→「企业信息」中查看"
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <v-text-field
                v-model="form.app_secret"
                label="应用Secret"
                :rules="[rules.required]"
                type="password"
                hint="在应用详情页查看"
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <v-text-field
                v-model="form.agent_id"
                label="应用AgentId"
                :rules="[rules.required]"
                hint="在应用详情页查看"
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <v-divider class="my-6"></v-divider>

              <v-text-field
                v-model="form.token"
                label="回调Token"
                hint="用于验证企业微信回调请求"
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <v-text-field
                v-model="form.encoding_aes_key"
                label="回调加密Key (EncodingAESKey)"
                hint="用于解密企业微信回调消息"
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <v-divider class="my-6"></v-divider>

              <v-combobox
                v-model="form.admin_users"
                label="管理员白名单"
                multiple
                chips
                hint="输入UserID后按回车添加，只有白名单用户可以执行命令"
                persistent-hint
                class="mb-4"
              ></v-combobox>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-btn color="warning" @click="testConfig" :loading="testing" :disabled="!formValid">
              测试配置
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn @click="loadConfig">重置</v-btn>
            <v-btn color="primary" @click="saveConfig" :loading="saving" :disabled="!formValid">
              保存配置
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>配置说明</v-card-title>
          <v-card-text>
            <v-timeline density="compact" side="end">
              <v-timeline-item dot-color="primary" size="small">
                <div class="mb-4">
                  <div class="font-weight-bold">1. 创建企业微信应用</div>
                  <div class="text-caption">
                    登录企业微信管理后台，创建自建应用
                  </div>
                </div>
              </v-timeline-item>

              <v-timeline-item dot-color="primary" size="small">
                <div class="mb-4">
                  <div class="font-weight-bold">2. 获取配置信息</div>
                  <div class="text-caption">
                    记录 CorpID、AgentId、Secret
                  </div>
                </div>
              </v-timeline-item>

              <v-timeline-item dot-color="primary" size="small">
                <div class="mb-4">
                  <div class="font-weight-bold">3. 配置回调URL</div>
                  <div class="text-caption">
                    设置回调URL并生成Token和EncodingAESKey
                  </div>
                </div>
              </v-timeline-item>

              <v-timeline-item dot-color="primary" size="small">
                <div class="mb-4">
                  <div class="font-weight-bold">4. 填写配置</div>
                  <div class="text-caption">
                    在左侧表单填写配置信息
                  </div>
                </div>
              </v-timeline-item>

              <v-timeline-item dot-color="success" size="small">
                <div>
                  <div class="font-weight-bold">5. 测试并保存</div>
                  <div class="text-caption">
                    点击「测试配置」验证，然后保存
                  </div>
                </div>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>

        <v-card class="mt-4">
          <v-card-title>回调URL</v-card-title>
          <v-card-text>
            <v-text-field
              :model-value="callbackUrl"
              label="回调URL"
              readonly
              append-icon="mdi-content-copy"
              @click:append="copyCallbackUrl"
            ></v-text-field>
            <v-alert type="info" density="compact" class="mt-2">
              将此URL配置到企业微信应用的「接收消息」设置中
            </v-alert>
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

const formRef = ref()
const formValid = ref(false)
const saving = ref(false)
const testing = ref(false)

const form = ref({
  corp_id: '',
  app_secret: '',
  agent_id: '',
  token: '',
  encoding_aes_key: '',
  admin_users: [] as string[],
})

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

const rules = {
  required: (value: string) => !!value || '此字段为必填项',
}

const callbackUrl = computed(() => {
  return `${window.location.origin}/api/v1/wechat/callback`
})

const loadConfig = async () => {
  try {
    const config = await apiClient.getWeChatConfig()
    form.value = {
      corp_id: config.corp_id || '',
      app_secret: '', // 不返回敏感信息
      agent_id: config.agent_id || '',
      token: config.token || '',
      encoding_aes_key: config.encoding_aes_key || '',
      admin_users: config.admin_users || [],
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    showSnackbar('加载配置失败', 'error')
  }
}

const saveConfig = async () => {
  if (!formRef.value?.validate()) {
    return
  }

  saving.value = true
  try {
    await apiClient.updateWeChatConfig(form.value)
    showSnackbar('配置保存成功', 'success')
  } catch (error) {
    console.error('保存配置失败:', error)
    showSnackbar('保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

const testConfig = async () => {
  if (!formRef.value?.validate()) {
    return
  }

  testing.value = true
  try {
    const result = await apiClient.testWeChatConfig(form.value)
    if (result.success) {
      showSnackbar('配置测试成功', 'success')
    } else {
      showSnackbar(`配置测试失败: ${result.message}`, 'error')
    }
  } catch (error) {
    console.error('测试配置失败:', error)
    showSnackbar('测试配置失败', 'error')
  } finally {
    testing.value = false
  }
}

const copyCallbackUrl = () => {
  navigator.clipboard.writeText(callbackUrl.value)
  showSnackbar('回调URL已复制到剪贴板', 'success')
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  loadConfig()
})
</script>
