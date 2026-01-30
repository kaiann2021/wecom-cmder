"""企业微信API客户端

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.1 企业微信客户端 (WeChat Client)

迁移自: MoviePilot-2/app/modules/wechat/wechat.py
"""

import json
import logging
import threading
from datetime import datetime
from typing import Optional, List, Dict
import httpx

logger = logging.getLogger(__name__)

# 线程锁，用于保护 access_token 的并发访问
_lock = threading.Lock()


class WeChatClientException(Exception):
    """企业微信客户端异常"""

    pass


class WeChatClient:
    """企业微信API客户端

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.1.2 核心方法
    """

    def __init__(self, corp_id: str, app_secret: str, agent_id: str, proxy: str = "https://qyapi.weixin.qq.com"):
        """初始化客户端

        Args:
            corp_id: 企业ID
            app_secret: 应用Secret
            agent_id: 应用AgentId
            proxy: API代理地址
        """
        self.corp_id = corp_id
        self.app_secret = app_secret
        self.agent_id = agent_id
        self.proxy = proxy

        # Access Token 缓存
        self._access_token: Optional[str] = None
        self._expires_in: int = 7200
        self._access_token_time: Optional[datetime] = None

        # API URLs
        self._token_url = f"{proxy}/cgi-bin/gettoken"
        self._send_msg_url = f"{proxy}/cgi-bin/message/send"
        self._create_menu_url = f"{proxy}/cgi-bin/menu/create"
        self._delete_menu_url = f"{proxy}/cgi-bin/menu/delete"

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """获取访问令牌（带缓存）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            str: Access Token

        Raises:
            WeChatClientException: 获取失败时
        """
        with _lock:
            # 检查缓存是否有效
            if not force_refresh and self._access_token and self._access_token_time:
                elapsed = (datetime.now() - self._access_token_time).total_seconds()
                if elapsed < self._expires_in - 60:  # 提前60秒刷新
                    return self._access_token

            # 获取新的 token
            params = {"corpid": self.corp_id, "corpsecret": self.app_secret}

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self._token_url, params=params, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()

                    if data.get("errcode") == 0:
                        self._access_token = data.get("access_token")
                        self._expires_in = data.get("expires_in", 7200)
                        self._access_token_time = datetime.now()
                        logger.info("成功获取企业微信 access_token")
                        return self._access_token
                    else:
                        raise WeChatClientException(
                            f"获取access_token失败: {data.get('errmsg')}"
                        )
                except httpx.HTTPError as e:
                    raise WeChatClientException(f"请求失败: {e}")

    async def send_text_message(
        self, content: str, to_user: str = "@all"
    ) -> dict:
        """发送文本消息

        Args:
            content: 消息内容
            to_user: 接收者UserID，默认@all发给所有人

        Returns:
            dict: 发送结果

        Raises:
            WeChatClientException: 发送失败时
        """
        access_token = await self.get_access_token()

        # 分块处理超长消息
        chunks = self._split_content(content)

        for chunk in chunks:
            data = {
                "touser": to_user,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": chunk},
                "safe": 0,
            }

            result = await self._post_request(self._send_msg_url, data, access_token)
            if not result.get("success"):
                raise WeChatClientException(f"发送消息失败: {result.get('errmsg')}")

        return {"success": True}

    async def send_news_message(
        self, articles: List[dict], to_user: str = "@all"
    ) -> dict:
        """发送图文消息

        Args:
            articles: 图文列表，每项包含 title, description, picurl, url
            to_user: 接收者UserID

        Returns:
            dict: 发送结果

        Raises:
            WeChatClientException: 发送失败时
        """
        access_token = await self.get_access_token()

        data = {
            "touser": to_user,
            "msgtype": "news",
            "agentid": self.agent_id,
            "news": {"articles": articles[:8]},  # 最多8条
        }

        result = await self._post_request(self._send_msg_url, data, access_token)
        if not result.get("success"):
            raise WeChatClientException(f"发送图文消息失败: {result.get('errmsg')}")

        return result

    async def create_menu(self, menu_data: dict) -> dict:
        """创建应用菜单

        Args:
            menu_data: 菜单数据，格式见企业微信文档

        Returns:
            dict: 创建结果

        Raises:
            WeChatClientException: 创建失败时
        """
        access_token = await self.get_access_token()

        params = {"access_token": access_token, "agentid": self.agent_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._create_menu_url,
                    params=params,
                    json=menu_data,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("errcode") == 0:
                    logger.info("成功创建企业微信菜单")
                    return {"success": True}
                else:
                    raise WeChatClientException(
                        f"创建菜单失败: {data.get('errmsg')}"
                    )
            except httpx.HTTPError as e:
                raise WeChatClientException(f"请求失败: {e}")

    async def delete_menu(self) -> dict:
        """删除应用菜单

        Returns:
            dict: 删除结果

        Raises:
            WeChatClientException: 删除失败时
        """
        access_token = await self.get_access_token()

        params = {"access_token": access_token, "agentid": self.agent_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self._delete_menu_url, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("errcode") == 0:
                    logger.info("成功删除企业微信菜单")
                    return {"success": True}
                else:
                    raise WeChatClientException(
                        f"删除菜单失败: {data.get('errmsg')}"
                    )
            except httpx.HTTPError as e:
                raise WeChatClientException(f"请求失败: {e}")

    async def _post_request(
        self, url: str, data: dict, access_token: str
    ) -> dict:
        """发送POST请求

        Args:
            url: 请求URL
            data: 请求数据
            access_token: 访问令牌

        Returns:
            dict: 响应数据

        Raises:
            WeChatClientException: 请求失败时
        """
        params = {"access_token": access_token}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    params=params,
                    json=data,
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("errcode") == 0:
                    return {"success": True, **result}
                elif result.get("errcode") == 42001:
                    # Token过期，刷新后重试
                    logger.warning("access_token已过期，尝试刷新")
                    new_token = await self.get_access_token(force_refresh=True)
                    return await self._post_request(url, data, new_token)
                else:
                    return {"success": False, **result}
            except httpx.HTTPError as e:
                raise WeChatClientException(f"请求失败: {e}")

    @staticmethod
    def _split_content(content: str, max_bytes: int = 2048) -> List[str]:
        """将内容分块为不超过 max_bytes 字节的块

        Args:
            content: 待拆分的内容
            max_bytes: 最大字节数

        Returns:
            List[str]: 分块后的内容列表
        """
        content_chunks = []
        current_chunk = bytearray()

        for line in content.splitlines():
            encoded_line = (line + "\n").encode("utf-8")
            line_length = len(encoded_line)

            if line_length > max_bytes:
                # 处理超长行
                if current_chunk:
                    content_chunks.append(
                        current_chunk.decode("utf-8", errors="replace").strip()
                    )
                    current_chunk = bytearray()

                start = 0
                while start < line_length:
                    end = min(start + max_bytes, line_length)
                    # 避免拆分多字节字符
                    while end > start and (encoded_line[end - 1] & 0xC0) == 0x80:
                        end -= 1
                    truncated_line = encoded_line[start:end].decode(
                        "utf-8", errors="replace"
                    )
                    content_chunks.append(truncated_line.strip())
                    start = end
                continue

            if len(current_chunk) + line_length > max_bytes:
                content_chunks.append(
                    current_chunk.decode("utf-8", errors="replace").strip()
                )
                current_chunk = bytearray()

            current_chunk += encoded_line

        if current_chunk:
            content_chunks.append(current_chunk.decode("utf-8", errors="replace").strip())

        return content_chunks
