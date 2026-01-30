# 企业微信配置信息泄露风险分析

## 执行时间
2026-01-30 14:17

## 发现的安全漏洞

### 🔴 高危：GET /api/v1/config/wechat 返回敏感信息

**文件位置：** `backend/app/api/endpoints/config.py` 第 31-79 行

**问题描述：**
GET 接口返回的 `WeChatConfigResponse` 包含了 `token` 和 `encoding_aes_key` 两个敏感字段（第 73-74 行）。

**风险等级：** 🔴 高危

**影响：**
- 任何登录用户都可以通过 GET 请求获取企业微信的 token 和 encoding_aes_key
- 攻击者可以利用这些信息伪造回调请求或解密消息
- 前端代码（Config.vue）虽然注释了"不返回敏感信息"，但实际上后端会返回

**当前代码：**
```python
return WeChatConfigResponse(
    corp_id=configs.get("corp_id", ""),
    agent_id=configs.get("agent_id", ""),
    proxy="https://qyapi.weixin.qq.com",
    admin_users=configs.get("admin_users", []),
    token=configs.get("token"),  # ❌ 敏感信息
    encoding_aes_key=configs.get("encoding_aes_key"),  # ❌ 敏感信息
)
```

### 🔴 高危：WeChatConfigResponse Schema 包含敏感字段

**文件位置：** `backend/app/schemas/config.py` 第 23-32 行

**问题描述：**
`WeChatConfigResponse` 模型定义包含 `token` 和 `encoding_aes_key` 字段，注释说"不包含敏感信息"但实际包含。

**风险等级：** 🔴 高危

**当前代码：**
```python
class WeChatConfigResponse(BaseModel):
    """企业微信配置响应模型（不包含敏感信息）"""  # ❌ 注释误导
    
    corp_id: str
    agent_id: str
    proxy: str
    admin_users: List[str]
    token: Optional[str] = None  # ❌ 应该移除
    encoding_aes_key: Optional[str] = None  # ❌ 应该移除
```

### 🟡 中危：app_secret 通过 PUT 接口更新但未加密存储

**文件位置：** `backend/app/api/endpoints/config.py` 第 82-137 行

**问题描述：**
虽然 `app_secret` 不会通过 GET 返回（这是正确的），但在数据库中是明文存储的。

**风险等级：** 🟡 中危

**建议：**
考虑对 `app_secret` 进行单向哈希或加密存储（但这会影响使用，因为需要用它调用微信API）

### 🟢 低危：日志可能记录敏感信息

**文件位置：** 多处

**问题描述：**
错误日志可能会记录包含敏感信息的完整配置对象。

**建议：**
- 添加日志脱敏处理
- 避免直接打印配置对象

## 修复建议

### 1. 立即修复：移除 GET 响应中的敏感字段

修改 `WeChatConfigResponse` 模型，完全移除 `token` 和 `encoding_aes_key`：

```python
class WeChatConfigResponse(BaseModel):
    """企业微信配置响应模型（不包含敏感信息）"""
    
    corp_id: str
    agent_id: str
    proxy: str
    admin_users: List[str]
    # token 和 encoding_aes_key 已移除，仅用于内部
```

### 2. 添加掩码字段表示配置状态

如果前端需要知道是否配置了 token 和 key，可以添加布尔字段：

```python
class WeChatConfigResponse(BaseModel):
    corp_id: str
    agent_id: str
    proxy: str
    admin_users: List[str]
    has_token: bool = Field(description="是否已配置Token")
    has_encoding_aes_key: bool = Field(description="是否已配置EncodingAESKey")
```

### 3. 前端适配

前端应该：
- 在加载配置时，不期望获取 token 和 encoding_aes_key
- 保存时仍然发送这些字段
- 使用 `has_token` 等字段来显示配置状态

## 安全检查清单

- [x] 检查所有 API 响应模型
- [x] 检查数据库查询返回内容
- [x] 检查日志输出
- [x] 检查错误消息
- [ ] 进行渗透测试
- [ ] 代码审计

## 结论

当前代码存在**高危安全漏洞**，可能导致企业微信配置信息（token 和 encoding_aes_key）泄露给任何登录用户。

**必须立即修复** GET 接口和响应模型。
