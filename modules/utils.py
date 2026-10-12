import datetime
import logging
from typing import Dict, Any

# 设备类型到Netmiko device_type的映射表
DEVICE_TYPE_MAPPING = {
    # 华为设备
    'huawei': 'huawei',
    '华为': 'huawei',
    'huawei_vrp': 'huawei',
    'vrp': 'huawei',
    
    # 华三设备
    'h3c': 'hp_comware',
    '华三': 'hp_comware',
    'hp_comware': 'hp_comware',
    'comware': 'hp_comware',
    
    # 思科设备
    'cisco': 'cisco_ios',
    '思科': 'cisco_ios',
    'cisco_ios': 'cisco_ios',
    'ios': 'cisco_ios',
    
    # 锐捷设备
    'ruijie': 'ruijie_os',
    '锐捷': 'ruijie_os',
    'ruijie_os': 'ruijie_os',
    
    # 中兴设备
    'zte': 'zte_zxros',
    '中兴': 'zte_zxros',
    'zxros': 'zte_zxros',
    'zte_zxros': 'zte_zxros',
    
    # 其他设备
    'mikrotik': 'mikrotik_routeros',
    '瞻博': 'juniper_junos',
    'juniper': 'juniper_junos',
    'arista': 'arista_eos',
    'dell': 'dell_powerconnect',
    'hp': 'hp_procurve'
}

class Utils:
    """
    工具函数类，包含时间格式、设备类型映射、日志格式化等工具函数
    """
    
    @staticmethod
    def get_current_time(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        获取当前时间的格式化字符串
        
        Args:
            fmt: 时间格式字符串，默认 "%Y-%m-%d %H:%M:%S"
            
        Returns:
            str: 格式化后的当前时间
        """
        return datetime.datetime.now().strftime(fmt)
    
    @staticmethod
    def get_file_time(fmt: str = "%Y%m%d_%H%M%S") -> str:
        """
        获取用于文件名的时间格式化字符串
        
        Args:
            fmt: 时间格式字符串，默认 "%Y%m%d_%H%M%S"
            
        Returns:
            str: 格式化后的当前时间
        """
        return datetime.datetime.now().strftime(fmt)
    
    @staticmethod
    def map_device_type(device_type: str) -> str:
        """
        将用户输入的设备类型映射为Netmiko所需的device_type
        
        Args:
            device_type: 用户输入的设备类型
            
        Returns:
            str: Netmiko所需的device_type
        """
        device_type = device_type.lower().strip()
        return DEVICE_TYPE_MAPPING.get(device_type, device_type)
    
    @staticmethod
    def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name: 日志记录器名称
            log_level: 日志级别，默认logging.INFO
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # 防止重复添加处理器
        if not logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            
            # 设置日志格式
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def format_log_message(level: str, device_name: str, ip: str, message: str) -> str:
        """
        格式化日志消息
        
        Args:
            level: 日志级别
            device_name: 设备名称
            ip: IP地址
            message: 日志消息
            
        Returns:
            str: 格式化后的日志消息
        """
        if ip:
            return f"{device_name} ({ip}) - {message}"
        else:
            return f"{device_name} - {message}"
    
    @staticmethod
    def validate_device_info(device: Dict[str, Any]) -> bool:
        """
        验证设备信息是否完整
        
        Args:
            device: 设备字典
            
        Returns:
            bool: 设备信息完整返回True，否则返回False
        """
        required_fields = ["设备名称", "设备类型", "IP地址", "端口号", "连接类型", "用户名", "密码"]
        for field in required_fields:
            if field not in device:
                return False
        
        # 检查关键字段是否为空
        if not device["设备名称"] or not device["IP地址"] or not device["设备类型"]:
            return False
        
        return True
    
    @staticmethod
    def get_default_port(conn_type: str) -> int:
        """
        根据连接类型获取默认端口号
        
        Args:
            conn_type: 连接类型，"ssh"或"telnet"
            
        Returns:
            int: 默认端口号
        """
        return 22 if conn_type == "ssh" else 23
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除或替换非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 定义非法字符列表
        illegal_chars = '<>:/\\|?*"'
        
        # 替换非法字符为下划线
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        return filename.strip()
