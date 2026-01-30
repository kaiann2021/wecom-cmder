<template>
  <v-app>
    <!-- 只在已登录时显示导航栏（update-001） -->
    <v-app-bar v-if="isAuthenticated" color="primary" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>WeCom Commander</v-toolbar-title>
      <v-spacer></v-spacer>
      <!-- 登出按钮（update-001） -->
      <v-btn icon @click="handleLogout" title="登出">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- 只在已登录时显示侧边栏（update-001） -->
    <v-navigation-drawer v-if="isAuthenticated" v-model="drawer" app>
      <v-list>
        <v-list-item
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          link
        >
          <template v-slot:prepend>
            <v-icon>{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()
const route = useRoute()

const drawer = ref(true)

// 检查是否已登录（update-001）
const isAuthenticated = computed(() => {
  return !!localStorage.getItem('access_token') && route.path !== '/login'
})

const menuItems = [
  { title: '仪表盘', path: '/', icon: 'mdi-view-dashboard' },
  { title: '配置管理', path: '/config', icon: 'mdi-cog' },
  { title: '消息历史', path: '/messages', icon: 'mdi-message-text' },
  { title: '命令管理', path: '/commands', icon: 'mdi-console' },
]

// 登出处理（update-001）
const handleLogout = () => {
  apiClient.logout()
}
</script>
