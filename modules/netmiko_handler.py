from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    SSHException,
    ConfigInvalidException
)
from typing import Dict, List, Tuple, Any
import time

class NetmikoHandler:
    """
    Netmiko处理器，封装Netmiko连接、命令执行、异常处理等功能
    """
    
    def __init__(self, device_info: Dict[str, Any], read_timeout: int = 20, max_retries: int = 2):
        """
        初始化Netmiko处理器
        
        Args:
            device_info: 设备信息字典
            read_timeout: 命令执行超时时间，默认60秒
            max_retries: 连接失败重试次数，默认2次
        """
        self.device_info = device_info
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.connection = None
    
    def connect(self) -> bool:
        """
        建立网络连接
        
        Returns:
            bool: 连接成功返回True，否则返回False
        """
        # 构建Netmiko连接参数
        netmiko_params = self._build_netmiko_params()
        
        # 尝试建立连接
        for attempt in range(self.max_retries + 1):
            try:
                self.connection = ConnectHandler(**netmiko_params)
                
                # 处理提权提权 (enable)
                if self.device_info.get("提权密码"):
                    try:
                        self.connection.enable()
                    except Exception as e:
                        raise Exception(f"提权(enable)失败，请检查提权密码: {e}")
                
                return True
            except NetmikoTimeoutException:
                if attempt == self.max_retries:
                    raise Exception(f"设备超时，无法连接到 {self.device_info['IP地址']}")
            except NetmikoAuthenticationException:
                if attempt == self.max_retries:
                    raise Exception(f"认证失败，用户名或密码错误: {self.device_info['IP地址']}")
            except SSHException as e:
                if attempt == self.max_retries:
                    raise Exception(f"SSH连接失败: {e}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise Exception(f"连接失败: {e}")
            
            # 重试间隔
            time.sleep(1)
        
        return False
    
    def execute_commands(self, commands: List[str]) -> List[Tuple[str, str]]:
        """
        执行命令列表
        
        Args:
            commands: 命令列表
            
        Returns:
            List[Tuple[str, str]]: 命令执行结果列表，每个元素为(命令, 输出)
            
        Raises:
            Exception: 连接未建立或命令执行失败时抛出
        """
        if not self.connection:
            raise Exception("连接未建立，请先调用connect()方法")
        
        results = []
        for command in commands:
            try:
                output = self.connection.send_command(
                    command, 
                    read_timeout=self.read_timeout,
                    strip_command=True,
                    strip_prompt=True
                )
                results.append((command, output))
            except Exception as e:
                raise Exception(f"执行命令 '{command}' 失败: {e}")
        
        return results
    
    def disconnect(self) -> None:
        """
        关闭网络连接
        """
        if self.connection:
            try:
                self.connection.disconnect()
            except Exception:
                # 忽略断开连接时的异常
                pass
            finally:
                self.connection = None
    
    def _build_netmiko_params(self) -> Dict[str, Any]:
        """
        构建Netmiko连接参数
        
        Returns:
            Dict[str, Any]: Netmiko连接参数字典
        """
        # 从设备信息字典中提取参数
        device_type = self.device_info.get("netmiko_device_type", self.device_info["设备类型"])
        ip = self.device_info["IP地址"]
        port = self.device_info["端口号"]
        username = self.device_info["用户名"]
        password = self.device_info["密码"]
        secret = self.device_info.get("提权密码", "")
        conn_type = self.device_info["连接类型"]
        
        # 构建基础参数
        # 对于telnet连接，需要在device_type后添加"_telnet"后缀
        netmiko_device_type = device_type
        if conn_type == "telnet":
            # 确保device_type以"_telnet"结尾
            if not netmiko_device_type.endswith("_telnet"):
                netmiko_device_type = f"{netmiko_device_type}_telnet"
        
        params = {
            "device_type": netmiko_device_type,
            "host": ip,
            "port": port,
            "username": username,
            "password": password,
            "secret": secret,
            "timeout": self.read_timeout,
            "global_delay_factor": 0.5  # 增加延迟因子，提高稳定性
        }
        
        # 针对不同连接类型添加特定参数
        if conn_type == "telnet":
            # Telnet特定参数，提高连接稳定性
            params.update({
                "global_delay_factor": 1.0,  # 增加延迟因子，适配不同设备的响应速度
                "timeout": self.read_timeout,  # 明确设置连接超时时间
                "fast_cli": False,  # 关闭快速模式，提高可靠性
                "keepalive": 10  # 添加keepalive机制，防止连接断开
            })
        elif conn_type == "ssh":
            # SSH特定参数
            params.update({
                "allow_auto_change": True,
                "use_keys": False,
                "key_file": None,
                "ssh_strict": False,
                "system_host_keys": False,
                "alt_host_keys": False,
                "ssh_config_file": None
            })
        
        return params
    
    def __enter__(self):
        """
        支持上下文管理器，自动建立连接
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        支持上下文管理器，自动关闭连接
        """
        self.disconnect()
    
    def test_connection(self) -> bool:
        """
        测试连接是否正常
        
        Returns:
            bool: 连接正常返回True，否则返回False
        """
        try:
            if not self.connection:
                self.connect()
            
            # 发送一个简单命令测试连接
            test_command = "show version" if "cisco" in self.device_info.get("netmiko_device_type", "").lower() or "ruijie" in self.device_info.get("netmiko_device_type", "").lower() else "display version"
            self.connection.send_command(test_command, read_timeout=10)
            return True
        except Exception:
            return False
        finally:
            self.disconnect()
    
    def get_device_prompt(self) -> str:
        """
        获取设备提示符
        
        Returns:
            str: 设备提示符
        """
        if not self.connection:
            raise Exception("连接未建立，请先调用connect()方法")
        
        try:
            return self.connection.find_prompt()
        except Exception as e:
            raise Exception(f"获取设备提示符失败: {e}")
    
    def execute_config_commands(self, config_commands: List[str]) -> List[str]:
        """
        执行配置命令（用于配置模式）
        
        Args:
            config_commands: 配置命令列表
            
        Returns:
            List[str]: 命令执行结果列表
        """
        if not self.connection:
            raise Exception("连接未建立，请先调用connect()方法")
        
        try:
            output = self.connection.send_config_set(
                config_commands,
                read_timeout=self.read_timeout
            )
            return output.split("\n")
        except Exception as e:
            raise Exception(f"执行配置命令失败: {e}")
