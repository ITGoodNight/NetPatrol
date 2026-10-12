import os
from pathlib import Path

class ConfigLoader:
    """
    配置加载器，负责加载和校验配置文件（支持txt格式）
    """
    
    def __init__(self, config_path: str = "config/commands.txt"):
        # 获取当前文件所在目录（modules目录）
        current_dir = Path(__file__).parent
        # 配置文件位于network_inspector目录下
        self.config_path = current_dir.parent / config_path
        self.default_config = {
            "huawei": ["display version", "display ip interface brief"],
            "h3c": ["display version", "display ip routing-table"],
            "cisco_ios": ["show version", "show ip interface brief"],
            "ruijie_os": ["show version", "show interface status"],
            "zte_zxros": ["display version", "display ip interface brief"],
            "default": ["show version"]
        }
    
    def load_config(self) -> dict:
        """
        加载配置文件，如果文件不存在则生成默认配置
        
        Returns:
            dict: 加载后的配置字典
        """
        try:
            # 检查配置文件是否存在
            if not self.config_path.exists():
                self._generate_default_config()
                return self.default_config
            
            # 读取配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析txt格式配置
            config = self._parse_txt_config(content)
            
            # 校验配置格式
            self._validate_config(config)
            return config
        
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def _generate_default_config(self) -> None:
        """
        生成默认配置文件
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("# 格式：设备类型用[]包裹，后面跟随命令列表\n")
                for device_type, commands in self.default_config.items():
                    f.write(f"[{device_type}]\n")
                    for command in commands:
                        f.write(f"{command}\n")
                    f.write("\n")
        except Exception as e:
            raise Exception(f"生成默认配置文件失败: {e}")
    
    def _parse_txt_config(self, content: str) -> dict:
        """
        解析txt格式的配置文件
        
        Args:
            content: 配置文件内容
            
        Returns:
            dict: 解析后的配置字典
        """
        config = {}
        current_device = None
        lines = content.split('\n')
        
        for line in lines:
            # 去除行首尾空白
            line = line.strip()
            
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue
            
            # 检查是否是设备类型行
            if line.startswith('[') and line.endswith(']'):
                # 提取设备类型名称
                current_device = line[1:-1].strip()
                config[current_device] = []
            elif current_device is not None:
                # 添加命令到当前设备类型
                config[current_device].append(line)
        
        return config
    
    def _validate_config(self, config: dict) -> None:
        """
        校验配置格式是否正确
        
        Args:
            config: 待校验的配置字典
            
        Raises:
            ValueError: 配置格式错误时抛出
        """
        # 检查配置是否为字典类型
        if not isinstance(config, dict):
            raise ValueError("配置解析失败，必须为正确的txt格式")
        
        # 检查每个设备类型对应的命令是否为列表
        for device_type, commands in config.items():
            if device_type.startswith('_comment'):  # 跳过注释字段
                continue
            
            if not isinstance(commands, list):
                raise ValueError(f"设备类型 '{device_type}' 对应的命令必须为列表格式")
            
            # 检查列表中的每个元素是否为字符串
            for command in commands:
                if not isinstance(command, str):
                    raise ValueError(f"设备类型 '{device_type}' 中的命令必须为字符串格式")
    
    def get_commands_for_device(self, device_type: str, config: dict) -> list:
        """
        根据设备类型获取对应的巡检命令
        
        Args:
            device_type: 设备类型
            config: 配置字典
            
        Returns:
            list: 巡检命令列表
        """
        # 优先使用精确匹配
        if device_type in config:
            return config[device_type]
        
        # 否则使用default命令
        if 'default' in config:
            return config['default']
        
        # 如果default也不存在，返回空列表
        return []
