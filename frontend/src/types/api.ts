/**
 * API 客户端类型定义
 *
 * 更新记录:
 * - update-001: 添加认证相关类型
 */

// ========== 认证相关（update-001） ==========

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * Token 响应
 */
export interface TokenResponse {
  access_token: string
  token_type: string
}

/**
 * 用户信息
 */
export interface UserInfo {
  username: string
}

// ========== 企业微信配置 ==========

// 企业微信配置
export interface WeChatConfig {
  corp_id: string
  agent_id: string
  proxy: string
  admin_users: string[]
  token?: string
  encoding_aes_key?: string
}

export interface WeChatConfigUpdate {
  corp_id: string
  app_secret: string
  agent_id: string
  token?: string
  encoding_aes_key?: string
  admin_users: string[]
}

export interface WeChatConfigTestResponse {
  success: boolean
  message: string
  details?: Record<string, any>
}

// 消息
export interface Message {
  id: number
  msg_id: string
  msg_type: string
  from_user: string
  to_user: string
  content: string
  create_time: number
  direction: 'in' | 'out'
  status: string
  created_at: string
  updated_at: string
}

export interface MessageSend {
  type: 'text' | 'news'
  to_user: string
  content?: string
  articles?: any[]
}

export interface MessageListResponse {
  total: number
  page: number
  page_size: number
  items: Message[]
}

// 命令
export interface Command {
  id: number
  command_id: string
  name: string
  description: string
  category: string
  handler: string
  admin_only: boolean
  enabled: boolean
  sort_order: number
}

export interface CommandUpdate {
  enabled?: boolean
  sort_order?: number
}

export interface CommandSyncMenuResponse {
  success: boolean
  message: string
  menu_count?: number
}
