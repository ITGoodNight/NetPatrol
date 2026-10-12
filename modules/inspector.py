from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Tuple, Optional
import threading
from PySide6.QtCore import Signal, QObject

from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    SSHException
)
from modules.config_loader import ConfigLoader
from modules.netmiko_handler import NetmikoHandler
from modules.output_manager import OutputManager
from modules.utils import Utils

class Inspector(QObject):
    """
    巡检管理器，负责多线程调度、任务分发、结果聚合等功能
    """
    
    # 定义日志信号
    log_signal = Signal(str, str)  # 日志信号，参数：日志级别，日志消息
    
    def __init__(self, max_workers: int = 10, result_dir: str = None, output_format: str = "HTML"):
        """
        初始化巡检管理器
        
        Args:
            max_workers: 最大线程数，默认10，最大50
            result_dir: 巡检结果目录，默认使用OutputManager的默认目录
            output_format: 输出格式，支持 "HTML" 或 "TXT"
        """
        super().__init__()
        # 移除线程数限制，支持大规模并发
        self.max_workers = max_workers
        self.total_devices = 0
        self.completed_devices = 0
        self.successful_devices = 0
        self.failed_devices = 0
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # 保存输出格式
        self.output_format = output_format
        
        # 根据参数创建OutputManager，明确指定所有关键字参数
        if result_dir:
            self.output_manager = OutputManager(
                result_dir=result_dir, 
                output_format=self.output_format
            )
        else:
            self.output_manager = OutputManager(
                result_dir="reports",
                output_format=self.output_format
            )
        
        self.config = None
        self.results = []
        self._log_callback: Optional[Callable[[str, str], None]] = None

    def set_log_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置线程安全的日志回调（Web 模式下推送到 WebSocket）"""
        self._log_callback = callback

    def _emit_log(self, level: str, message: str) -> None:
        """统一输出日志到文件、WebSocket 及 Qt 信号"""
        self.output_manager.append_to_log(message)
        if self._log_callback:
            try:
                self._log_callback(level, message)
            except Exception:
                pass
        self.log_signal.emit(level, message)
    
    def set_result_dir(self, result_dir: str) -> None:
        """
        设置巡检结果目录
        
        Args:
            result_dir: 巡检结果目录路径
        """
        self.output_manager = OutputManager(
            result_dir=result_dir,
            output_format=self.output_format
        )
        
    def start_inspection(self, devices: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
        """
        开始巡检任务
        
        Args:
            devices: 设备列表
            config: 配置字典
        """
        self.total_devices = len(devices)
        self.completed_devices = 0
        self.successful_devices = 0
        self.failed_devices = 0
        self._stop_event.clear()
        self.config = config
        self.results = []
        
        # 强制同步输出格式到 OutputManager
        if hasattr(self, 'output_manager'):
            self.output_manager.set_output_format(self.output_format)
        
        start_message = "开始巡检设备..."
        self._emit_log("INFO", start_message)
        
        thread_message = f"启动 {self.max_workers} 个线程进行巡检..."
        self._emit_log("INFO", thread_message)
        
        # 使用ThreadPoolExecutor执行多线程巡检
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_device = {}
            for device in devices:
                self._emit_log(
                    "INFO",
                    Utils.format_log_message(
                        "INFO",
                        device["设备名称"],
                        device["IP地址"],
                        f"已提交巡检任务（{device.get('连接类型', 'ssh').upper()}:{device.get('端口号', 22)}）",
                    ),
                )
                future_to_device[executor.submit(self._inspect_device, device)] = device
            
            # 处理执行结果
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    # 记录设备巡检失败
                    with self._lock:
                        self.failed_devices += 1
                        self.completed_devices += 1
                    
                    # 生成失败日志
                    log_message = f"{device['IP地址']} 连接失败: {str(e)}"
                    self._emit_log("ERROR", log_message)
                    
                    device_fail_msg = f"设备 {device['设备名称']} 巡检失败"
                    self._emit_log("ERROR", device_fail_msg)

                    self.results.append({
                        "device": device,
                        "status": "failed",
                        "result_file": None,
                        "error": str(e),
                    })
        
        finish_message = f"巡检完成：成功 {self.successful_devices} 个，失败 {self.failed_devices} 个"
        self._emit_log("INFO", finish_message)
        
        if self.failed_devices > 0:
            failed_devices = [result["device"]["设备名称"] for result in self.results if result["status"] == "failed"]
            failed_msg = f"失败的设备：{', '.join(failed_devices)}"
            self._emit_log("INFO", failed_msg)
        
        result_path_msg = f"结果已保存到：{self.output_manager.get_result_dir()}"
        self._emit_log("INFO", result_path_msg)
        
    def _inspect_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """
        单个设备的巡检逻辑
        
        Args:
            device: 设备信息字典
            
        Returns:
            dict: 巡检结果字典
        """
        if self._stop_event.is_set():
            raise Exception("巡检任务已停止")
        
        device_name = device["设备名称"]
        ip_address = device["IP地址"]
        device_type = device["设备类型"]
        conn_type = device["连接类型"]
        port = device["端口号"]
        
        try:
            # 映射设备类型到Netmiko设备类型
            netmiko_device_type = Utils.map_device_type(device_type)
            device["netmiko_device_type"] = netmiko_device_type
            
            # 记录设备信息日志
            log_level = "INFO"
            log_content = f"设备信息 - 类型: {device_type}, 连接方式: {conn_type}, 端口: {port}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            # 发送日志信号到UI
            self._emit_log(log_level, log_message)
            
            # 获取设备对应的命令
            commands = self._get_device_commands(device_type)
            if not commands:
                raise Exception("未找到匹配的巡检命令")
            
            # 记录开始巡检日志
            log_level = "INFO"
            log_content = f"开始巡检，将执行 {len(commands)} 条命令: {', '.join(commands)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            # 创建Netmiko处理器
            log_level = "INFO"
            log_content = f"正在建立连接..."
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            # 执行命令
            commands_results = []
            with NetmikoHandler(device) as handler:
                # 记录连接成功日志
                log_level = "INFO"
                log_content = f"连接成功，准备执行命令"
                log_message = Utils.format_log_message(
                    log_level, 
                    device_name, 
                    ip_address, 
                    log_content
                )
                self._emit_log(log_level, log_message)
                
                for i, command in enumerate(commands, 1):
                    # 记录执行命令日志
                    log_level = "INFO"
                    log_content = f"执行命令 {i}/{len(commands)}: {command}"
                    log_message = Utils.format_log_message(
                        log_level, 
                        device_name, 
                        ip_address, 
                        log_content
                    )
                    self._emit_log(log_level, log_message)
                    
                    # 记录命令执行开始日志
                    log_level = "INFO"
                    log_content = f"命令 '{command}' 执行中..."
                    log_message = Utils.format_log_message(
                        log_level, 
                        device_name, 
                        ip_address, 
                        log_content
                    )
                    self._emit_log(log_level, log_message)
                    
                    # 执行单个命令
                    cmd_result = handler.execute_commands([command])
                    commands_results.extend(cmd_result)
                    
                    # 记录命令执行结果日志
                    output_lines = cmd_result[0][1].split('\n')
                    log_level = "INFO"
                    log_content = f"命令 '{command}' 执行完成，输出行数: {len(output_lines)}"
                    log_message = Utils.format_log_message(
                        log_level, 
                        device_name, 
                        ip_address, 
                        log_content
                    )
                    self._emit_log(log_level, log_message)
            
            # 记录连接关闭日志
            log_level = "DEBUG"
            log_content = f"连接已关闭"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            # 生成结果文件
            log_level = "INFO"
            log_content = f"正在生成 {self.output_format} 格式的结果文件..."
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            result_file = self.output_manager.generate_result_file(device, commands_results)
            
            # 记录结果文件生成日志
            log_level = "INFO"
            log_content = f"结果文件已生成: {result_file}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            # 更新成功计数
            with self._lock:
                self.successful_devices += 1
                self.completed_devices += 1
            
            # 记录巡检完成日志
            log_level = "INFO"
            log_content = f"巡检完成，所有命令执行成功"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            return {
                "device": device,
                "status": "success",
                "result_file": result_file,
                "error": None
            }
        
        except NetmikoTimeoutException as e:
            # 更新失败计数
            with self._lock:
                self.failed_devices += 1
                self.completed_devices += 1
            
            # 记录超时日志
            log_level = "ERROR"
            log_content = f"设备超时，无法连接: {str(e)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            return {
                "device": device,
                "status": "failed",
                "result_file": None,
                "error": f"设备超时: {str(e)}"
            }
        
        except NetmikoAuthenticationException as e:
            # 更新失败计数
            with self._lock:
                self.failed_devices += 1
                self.completed_devices += 1
            
            # 记录认证失败日志
            log_level = "ERROR"
            log_content = f"认证失败，用户名或密码错误: {str(e)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            return {
                "device": device,
                "status": "failed",
                "result_file": None,
                "error": f"认证失败: {str(e)}"
            }
        
        except SSHException as e:
            # 更新失败计数
            with self._lock:
                self.failed_devices += 1
                self.completed_devices += 1
            
            # 记录SSH失败日志
            log_level = "ERROR"
            log_content = f"SSH连接失败: {str(e)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            return {
                "device": device,
                "status": "failed",
                "result_file": None,
                "error": f"SSH连接失败: {str(e)}"
            }
        
        except Exception as e:
            # 更新失败计数
            with self._lock:
                self.failed_devices += 1
                self.completed_devices += 1
            
            # 记录其他错误日志
            log_level = "ERROR"
            log_content = f"巡检失败: {str(e)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            # 记录详细错误信息
            log_level = "DEBUG"
            log_content = f"详细错误信息: {repr(e)}"
            log_message = Utils.format_log_message(
                log_level, 
                device_name, 
                ip_address, 
                log_content
            )
            self._emit_log(log_level, log_message)
            
            return {
                "device": device,
                "status": "failed",
                "result_file": None,
                "error": str(e)
            }
    
    def _get_device_commands(self, device_type: str) -> List[str]:
        """
        根据设备类型获取巡检命令
        
        Args:
            device_type: 设备类型
            
        Returns:
            List[str]: 巡检命令列表
        """
        # 优先使用设备类型匹配的命令
        if device_type in self.config:
            return self.config[device_type]
        
        # 否则使用default命令
        if "default" in self.config:
            return self.config["default"]
        
        # 如果default也不存在，返回空列表
        return []
    
    def get_progress(self) -> Dict[str, int]:
        """
        获取当前巡检进度
        
        Returns:
            Dict[str, int]: 进度字典，包含总设备数、已完成设备数、成功设备数、失败设备数
        """
        with self._lock:
            return {
                "total": self.total_devices,
                "completed": self.completed_devices,
                "successful": self.successful_devices,
                "failed": self.failed_devices
            }
    
    def stop_inspection(self) -> None:
        """
        停止巡检任务
        """
        self._stop_event.set()
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        获取巡检结果列表
        
        Returns:
            List[Dict[str, Any]]: 巡检结果列表
        """
        return self.results
    
    def set_result_dir(self, result_dir: str) -> None:
        """
        设置结果目录
        
        Args:
            result_dir: 结果目录路径
        """
        # 根据参数创建OutputManager，传递保存的AI开关状态
        self.output_manager = OutputManager(result_dir)
    
    def get_result_dir(self) -> str:
        """
        获取结果目录路径
        
        Returns:
            str: 结果目录的绝对路径
        """
        return self.output_manager.get_result_dir()
