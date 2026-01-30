"""消息处理服务

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.5 消息处理服务 (Message Service)
"""

import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.wechat.crypto import WeChatCrypto, WeChatCryptoException
from app.services.wechat.parser import MessageParser, ParsedMessage, MessageType, EventType
from app.services.wechat.client import WeChatClient
from app.services.command import command_manager
from app.models.message import Message
from app.schemas.config import WeChatConfig

logger = logging.getLogger(__name__)


class MessageService:
    """消息处理服务

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.5.2 处理流程
    """

    def __init__(
        self,
        wechat_config: WeChatConfig,
        wechat_client: WeChatClient,
        db: Session,
    ):
        """初始化消息处理服务

        Args:
            wechat_config: 企业微信配置
            wechat_client: 企业微信客户端
            db: 数据库会话
        """
        self.config = wechat_config
        self.client = wechat_client
        self.db = db

        # 初始化加解密器
        if wechat_config.token and wechat_config.encoding_aes_key:
            self.crypto = WeChatCrypto(
                token=wechat_config.token,
                encoding_aes_key=wechat_config.encoding_aes_key,
                corp_id=wechat_config.corp_id,
            )
        else:
            self.crypto = None
            logger.warning("未配置Token和EncodingAESKey，无法处理加密消息")

    async def handle_incoming_message(
        self,
        encrypted_msg: str,
        msg_signature: str,
        timestamp: str,
        nonce: str,
    ) -> Optional[str]:
        """处理企业微信回调消息

        处理流程：
        1. 解密消息
        2. 解析消息
        3. 权限验证
        4. 保存消息记录
        5. 根据类型分发处理
           - 文本消息 → 命令解析
           - 事件消息 → 事件处理
        6. 返回响应

        Args:
            encrypted_msg: 加密的消息（XML格式）
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数

        Returns:
            str: 响应内容（可选）
        """
        try:
            # 1. 解密消息
            if not self.crypto:
                logger.error("加解密器未初始化")
                return None

            decrypted_msg = self.crypto.decrypt_message(
                msg_signature, timestamp, nonce, encrypted_msg
            )
            logger.debug(f"解密后的消息: {decrypted_msg}")

            # 2. 解析消息
            parsed_msg = MessageParser.parse(decrypted_msg)
            if not parsed_msg:
                logger.warning("消息解析失败")
                return None

            logger.info(
                f"收到消息: type={parsed_msg.msg_type}, from={parsed_msg.from_user}"
            )

            # 3. 权限验证
            is_admin = MessageParser.is_admin_user(
                parsed_msg.from_user, self.config.admin_users
            )

            # 4. 保存消息记录
            self._save_message(parsed_msg, direction="in")

            # 5. 根据类型分发处理
            response_text = None

            if parsed_msg.msg_type == MessageType.TEXT:
                # 文本消息 - 可能是命令
                response_text = await self._handle_text_message(
                    parsed_msg, is_admin
                )

            elif parsed_msg.msg_type == MessageType.EVENT:
                # 事件消息 - 菜单点击等
                response_text = await self._handle_event_message(
                    parsed_msg, is_admin
                )

            # 6. 返回响应（如果有）
            if response_text:
                # 发送响应消息
                await self.client.send_text_message(
                    content=response_text, to_user=parsed_msg.from_user
                )

            return "success"

        except WeChatCryptoException as e:
            logger.error(f"消息解密失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return None

    async def _handle_text_message(
        self, message: ParsedMessage, is_admin: bool
    ) -> Optional[str]:
        """处理文本消息

        Args:
            message: 解析后的消息
            is_admin: 是否为管理员

        Returns:
            str: 响应文本
        """
        content = message.content
        if not content:
            return None

        # 检查是否为命令（以 / 开头）
        if content.startswith("/"):
            command_id = content[1:].split()[0]  # 提取命令ID
            result = command_manager.execute_command(
                command_id=command_id,
                user_id=message.from_user,
                is_admin=is_admin,
            )

            if result.get("success"):
                return result.get("result", "命令执行成功")
            else:
                return result.get("message", "命令执行失败")

        # 非命令消息，返回帮助提示
        return "请使用菜单或发送 /help 查看可用命令"

    async def _handle_event_message(
        self, message: ParsedMessage, is_admin: bool
    ) -> Optional[str]:
        """处理事件消息

        Args:
            message: 解析后的消息
            is_admin: 是否为管理员

        Returns:
            str: 响应文本
        """
        if message.event == EventType.CLICK:
            # 菜单点击事件
            command_id = message.event_key
            if not command_id:
                return None

            # 执行命令
            result = command_manager.execute_command(
                command_id=command_id,
                user_id=message.from_user,
                is_admin=is_admin,
            )

            if result.get("success"):
                return result.get("result", "命令执行成功")
            else:
                return result.get("message", "命令执行失败")

        elif message.event == EventType.ENTER_AGENT:
            # 进入应用事件
            return "欢迎使用企业微信指令管理系统！\n\n发送 /help 查看可用命令"

        return None

    def _save_message(self, message: ParsedMessage, direction: str):
        """保存消息记录

        Args:
            message: 解析后的消息
            direction: 消息方向（in/out）
        """
        try:
            db_message = Message(
                msg_id=message.msg_id or f"{message.from_user}_{message.create_time}",
                msg_type=message.msg_type.value,
                from_user=message.from_user,
                to_user=message.to_user,
                content=message.content or message.event_key or "",
                create_time=message.create_time,
                direction=direction,
                status="sent" if direction == "out" else "received",
            )
            self.db.add(db_message)
            self.db.commit()
            logger.debug(f"保存消息记录: {db_message.msg_id}")
        except Exception as e:
            logger.error(f"保存消息记录失败: {e}")
            self.db.rollback()

    async def send_message(
        self, to_user: str, content: str, msg_type: str = "text"
    ) -> bool:
        """发送消息

        Args:
            to_user: 接收者UserID
            content: 消息内容
            msg_type: 消息类型

        Returns:
            bool: 发送是否成功
        """
        try:
            if msg_type == "text":
                result = await self.client.send_text_message(
                    content=content, to_user=to_user
                )
            else:
                logger.warning(f"不支持的消息类型: {msg_type}")
                return False

            # 保存发送记录
            db_message = Message(
                msg_id=f"out_{to_user}_{int(datetime.now().timestamp())}",
                msg_type=msg_type,
                from_user="system",
                to_user=to_user,
                content=content,
                create_time=int(datetime.now().timestamp()),
                direction="out",
                status="sent" if result.get("success") else "failed",
            )
            self.db.add(db_message)
            self.db.commit()

            return result.get("success", False)

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
