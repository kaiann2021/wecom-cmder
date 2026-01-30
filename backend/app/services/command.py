"""命令管理器

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.4 命令管理器 (Command Manager)
"""

import logging
from typing import Dict, List, Callable, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Command(BaseModel):
    """命令定义

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.4.2 命令定义
    """

    id: str = Field(description="命令ID")
    name: str = Field(description="命令名称")
    description: str = Field(description="命令描述")
    category: str = Field(description="分类（用于菜单分组）")
    handler: Callable = Field(description="处理函数")
    admin_only: bool = Field(default=False, description="是否仅管理员可用")
    enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序")

    class Config:
        arbitrary_types_allowed = True


class CommandManager:
    """命令管理器

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.4.1 功能职责
    """

    def __init__(self):
        """初始化命令管理器"""
        self._commands: Dict[str, Command] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """注册内置命令

        根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
        章节: 3.4.3 内置命令示例
        """
        builtin_commands = [
            Command(
                id="status",
                name="系统状态",
                description="查看系统运行状态",
                category="系统",
                handler=self._handle_status,
                admin_only=False,
            ),
            Command(
                id="help",
                name="帮助",
                description="查看命令列表",
                category="系统",
                handler=self._handle_help,
                admin_only=False,
            ),
        ]

        for cmd in builtin_commands:
            self.register_command(cmd)

    def register_command(self, command: Command) -> bool:
        """注册命令

        Args:
            command: 命令对象

        Returns:
            bool: 注册是否成功
        """
        if command.id in self._commands:
            logger.warning(f"命令 {command.id} 已存在，将被覆盖")

        self._commands[command.id] = command
        logger.info(f"注册命令: {command.id} - {command.name}")
        return True

    def unregister_command(self, command_id: str) -> bool:
        """注销命令

        Args:
            command_id: 命令ID

        Returns:
            bool: 注销是否成功
        """
        if command_id in self._commands:
            del self._commands[command_id]
            logger.info(f"注销命令: {command_id}")
            return True
        return False

    def get_command(self, command_id: str) -> Optional[Command]:
        """获取命令

        Args:
            command_id: 命令ID

        Returns:
            Command: 命令对象，不存在返回None
        """
        return self._commands.get(command_id)

    def get_all_commands(self) -> List[Command]:
        """获取所有命令

        Returns:
            List[Command]: 命令列表
        """
        return list(self._commands.values())

    def get_enabled_commands(self) -> List[Command]:
        """获取所有启用的命令

        Returns:
            List[Command]: 启用的命令列表
        """
        return [cmd for cmd in self._commands.values() if cmd.enabled]

    def execute_command(
        self, command_id: str, user_id: str, is_admin: bool, **kwargs
    ) -> dict:
        """执行命令

        Args:
            command_id: 命令ID
            user_id: 用户ID
            is_admin: 是否为管理员
            **kwargs: 命令参数

        Returns:
            dict: 执行结果
        """
        command = self.get_command(command_id)

        if not command:
            return {"success": False, "message": f"命令不存在: {command_id}"}

        if not command.enabled:
            return {"success": False, "message": f"命令已禁用: {command_id}"}

        if command.admin_only and not is_admin:
            return {"success": False, "message": "权限不足，该命令仅管理员可用"}

        try:
            logger.info(f"执行命令: {command_id}, 用户: {user_id}")
            result = command.handler(user_id=user_id, **kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"执行命令失败: {command_id}, 错误: {e}")
            return {"success": False, "message": f"命令执行失败: {str(e)}"}

    def generate_menu_data(self) -> dict:
        """生成企业微信菜单数据

        根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
        章节: 3.4.1 功能职责 - 菜单自动生成

        Returns:
            dict: 菜单数据，格式符合企业微信API要求
        """
        # 获取启用的命令
        enabled_commands = self.get_enabled_commands()

        # 按分类分组
        category_dict: Dict[str, List[Command]] = {}
        for cmd in enabled_commands:
            if cmd.category not in category_dict:
                category_dict[cmd.category] = []
            category_dict[cmd.category].append(cmd)

        # 按排序排序
        for commands in category_dict.values():
            commands.sort(key=lambda x: x.sort_order)

        # 生成菜单按钮
        buttons = []
        for category, commands in category_dict.items():
            # 二级菜单（最多5个）
            sub_buttons = []
            for cmd in commands[:5]:
                sub_buttons.append(
                    {"type": "click", "name": cmd.name, "key": cmd.id}
                )

            # 一级菜单
            buttons.append({"name": category, "sub_button": sub_buttons})

        # 最多3个一级菜单
        return {"button": buttons[:3]}

    # 内置命令处理函数

    def _handle_status(self, user_id: str, **kwargs) -> str:
        """处理系统状态命令

        Args:
            user_id: 用户ID

        Returns:
            str: 状态信息
        """
        return "系统运行正常\n\n当前功能：\n- 消息推送\n- 指令接收\n- 菜单交互"

    def _handle_help(self, user_id: str, **kwargs) -> str:
        """处理帮助命令

        Args:
            user_id: 用户ID

        Returns:
            str: 帮助信息
        """
        commands = self.get_enabled_commands()

        # 按分类分组
        category_dict: Dict[str, List[Command]] = {}
        for cmd in commands:
            if cmd.category not in category_dict:
                category_dict[cmd.category] = []
            category_dict[cmd.category].append(cmd)

        # 生成帮助文本
        help_text = "可用命令列表：\n\n"
        for category, cmds in category_dict.items():
            help_text += f"【{category}】\n"
            for cmd in cmds:
                admin_mark = " [管理员]" if cmd.admin_only else ""
                help_text += f"  {cmd.name}{admin_mark}\n  {cmd.description}\n\n"

        return help_text.strip()


# 全局命令管理器实例
command_manager = CommandManager()
