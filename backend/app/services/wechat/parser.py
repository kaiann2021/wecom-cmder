"""企业微信消息解析器

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.3 消息解析器 (Message Parser)

迁移自: MoviePilot-2/app/modules/wechat/__init__.py
"""

import logging
import xml.etree.ElementTree as ET
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型枚举

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.3.2 消息类型
    """

    TEXT = "text"
    IMAGE = "image"
    EVENT = "event"
    VOICE = "voice"
    VIDEO = "video"
    LOCATION = "location"


class EventType(str, Enum):
    """事件类型枚举"""

    CLICK = "click"  # 菜单点击
    VIEW = "view"  # 菜单跳转
    SUBSCRIBE = "subscribe"  # 订阅
    UNSUBSCRIBE = "unsubscribe"  # 取消订阅
    ENTER_AGENT = "enter_agent"  # 进入应用


class ParsedMessage(BaseModel):
    """解析后的消息对象"""

    msg_type: MessageType = Field(description="消息类型")
    from_user: str = Field(description="发送者UserID")
    to_user: str = Field(description="接收者")
    create_time: int = Field(description="创建时间（时间戳）")
    msg_id: Optional[str] = Field(None, description="消息ID")
    agent_id: Optional[str] = Field(None, description="应用ID")

    # 文本消息字段
    content: Optional[str] = Field(None, description="文本内容")

    # 事件消息字段
    event: Optional[EventType] = Field(None, description="事件类型")
    event_key: Optional[str] = Field(None, description="事件KEY值")

    # 图片消息字段
    pic_url: Optional[str] = Field(None, description="图片链接")
    media_id: Optional[str] = Field(None, description="媒体ID")


class MessageParser:
    """企业微信消息解析器

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.3.3 解析流程
    """

    @staticmethod
    def parse(xml_data: str) -> Optional[ParsedMessage]:
        """解析企业微信消息

        解析流程：
        1. XML转字典
        2. 提取基础字段（MsgType, FromUserName, CreateTime等）
        3. 根据类型提取特定字段
        4. 返回结构化消息对象

        Args:
            xml_data: XML格式的消息数据

        Returns:
            ParsedMessage: 解析后的消息对象，解析失败返回None

        消息格式示例：
        1. 文本消息：
        <xml>
           <ToUserName><![CDATA[toUser]]></ToUserName>
           <FromUserName><![CDATA[fromUser]]></FromUserName>
           <CreateTime>1348831860</CreateTime>
           <MsgType><![CDATA[text]]></MsgType>
           <Content><![CDATA[this is a test]]></Content>
           <MsgId>1234567890123456</MsgId>
           <AgentID>1</AgentID>
        </xml>

        2. 事件消息：
        <xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[UserID]]></FromUserName>
            <CreateTime>1348831860</CreateTime>
            <MsgType><![CDATA[event]]></MsgType>
            <Event><![CDATA[click]]></Event>
            <EventKey><![CDATA[EVENTKEY]]></EventKey>
            <AgentID>1</AgentID>
        </xml>
        """
        try:
            # 解析XML
            root = ET.fromstring(xml_data)

            # 提取基础字段
            msg_type_str = MessageParser._get_text(root, "MsgType")
            from_user = MessageParser._get_text(root, "FromUserName")
            to_user = MessageParser._get_text(root, "ToUserName")
            create_time_str = MessageParser._get_text(root, "CreateTime")

            # 验证必填字段
            if not msg_type_str or not from_user or not create_time_str:
                logger.warning("消息缺少必填字段")
                return None

            # 转换消息类型
            try:
                msg_type = MessageType(msg_type_str)
            except ValueError:
                logger.warning(f"不支持的消息类型: {msg_type_str}")
                return None

            # 构建基础消息对象
            message_data = {
                "msg_type": msg_type,
                "from_user": from_user,
                "to_user": to_user or "",
                "create_time": int(create_time_str),
                "msg_id": MessageParser._get_text(root, "MsgId"),
                "agent_id": MessageParser._get_text(root, "AgentID"),
            }

            # 根据消息类型提取特定字段
            if msg_type == MessageType.TEXT:
                # 文本消息
                message_data["content"] = MessageParser._get_text(root, "Content")

            elif msg_type == MessageType.EVENT:
                # 事件消息
                event_str = MessageParser._get_text(root, "Event")
                if event_str:
                    try:
                        message_data["event"] = EventType(event_str)
                        message_data["event_key"] = MessageParser._get_text(
                            root, "EventKey"
                        )
                    except ValueError:
                        logger.warning(f"不支持的事件类型: {event_str}")
                        return None

            elif msg_type == MessageType.IMAGE:
                # 图片消息
                message_data["pic_url"] = MessageParser._get_text(root, "PicUrl")
                message_data["media_id"] = MessageParser._get_text(root, "MediaId")

            # 创建消息对象
            return ParsedMessage(**message_data)

        except ET.ParseError as e:
            logger.error(f"XML解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"消息解析失败: {e}")
            return None

    @staticmethod
    def _get_text(element: ET.Element, tag: str) -> Optional[str]:
        """获取XML元素的文本内容

        Args:
            element: XML元素
            tag: 标签名

        Returns:
            str: 文本内容，不存在返回None
        """
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    @staticmethod
    def is_admin_user(user_id: str, admin_users: list) -> bool:
        """检查用户是否为管理员

        Args:
            user_id: 用户ID
            admin_users: 管理员列表

        Returns:
            bool: 是否为管理员
        """
        if not admin_users:
            return True  # 如果没有配置管理员，所有用户都有权限
        return user_id in admin_users
