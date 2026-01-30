<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>WeCom Commander 登录</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form ref="formRef" v-model="valid" @submit.prevent="handleLogin">
              <v-text-field
                v-model="username"
                label="用户名"
                prepend-icon="mdi-account"
                :rules="[rules.required]"
                required
                autofocus
              />
              <v-text-field
                v-model="password"
                label="密码"
                prepend-icon="mdi-lock"
                type="password"
                :rules="[rules.required]"
                required
                @keyup.enter="handleLogin"
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :loading="loading"
              :disabled="!valid"
              @click="handleLogin"
            >
              登录
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-alert
          v-if="error"
          type="error"
          class="mt-4"
          dismissible
          @click:close="error = ''"
        >
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const username = ref('')
const password = ref('')
const valid = ref(false)
const loading = ref(false)
const error = ref('')
const formRef = ref()

const rules = {
  required: (value: string) => !!value || '此字段为必填项',
}

const handleLogin = async () => {
  if (!valid.value) return

  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.login({
      username: username.value,
      password: password.value,
    })

    // 存储 Token
    localStorage.setItem('access_token', response.access_token)

    // 跳转到首页
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
