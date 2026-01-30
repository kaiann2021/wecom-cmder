/**
 * API 客户端封装
 *
 * 根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
 * 章节: 5. API接口设计
 */

import axios, { type AxiosInstance } from 'axios'
import type {
  WeChatConfig,
  WeChatConfigUpdate,
  WeChatConfigTestResponse,
  Message,
  MessageSend,
  MessageListResponse,
  Command,
  CommandUpdate,
  CommandSyncMenuResponse,
} from '@/types/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  // ========== 配置管理 ==========

  /**
   * 获取企业微信配置
   */
  async getWeChatConfig(): Promise<WeChatConfig> {
    const response = await this.client.get('/config/wechat')
    return response.data
  }

  /**
   * 更新企业微信配置
   */
  async updateWeChatConfig(config: WeChatConfigUpdate): Promise<WeChatConfig> {
    const response = await this.client.put('/config/wechat', config)
    return response.data
  }

  /**
   * 测试企业微信配置
   */
  async testWeChatConfig(config: WeChatConfigUpdate): Promise<WeChatConfigTestResponse> {
    const response = await this.client.post('/config/wechat/test', config)
    return response.data
  }

  // ========== 消息管理 ==========

  /**
   * 发送消息
   */
  async sendMessage(message: MessageSend): Promise<{ success: boolean; msg_id?: string; message?: string }> {
    const response = await this.client.post('/messages/send', message)
    return response.data
  }

  /**
   * 获取消息列表
   */
  async getMessages(params: {
    page?: number
    page_size?: number
    direction?: string
    from_user?: string
    start_time?: number
    end_time?: number
  }): Promise<MessageListResponse> {
    const response = await this.client.get('/messages', { params })
    return response.data
  }

  // ========== 命令管理 ==========

  /**
   * 获取命令列表
   */
  async getCommands(): Promise<{ commands: Command[] }> {
    const response = await this.client.get('/commands')
    return response.data
  }

  /**
   * 更新命令
   */
  async updateCommand(commandId: string, update: CommandUpdate): Promise<{ success: boolean; message: string }> {
    const response = await this.client.put(`/commands/${commandId}`, update)
    return response.data
  }

  /**
   * 同步菜单
   */
  async syncMenu(): Promise<CommandSyncMenuResponse> {
    const response = await this.client.post('/commands/sync-menu')
    return response.data
  }

  // ========== 健康检查 ==========

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health', { baseURL: '' })
    return response.data
  }
}

export const apiClient = new ApiClient()
