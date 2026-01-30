/**
 * API 客户端类型定义
 */

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
