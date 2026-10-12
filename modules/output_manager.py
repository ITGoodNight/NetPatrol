from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import html
import os

from modules.utils import Utils

class OutputManager:
    """
    输出管理器，负责结果目录创建、文件输出、编码处理等功能
    """
    
    def __init__(self, result_dir: str = "reports", output_format: str = "HTML"):
        """
        初始化输出管理器
        
        Args:
            result_dir: 结果目录名称，默认 "reports"
            output_format: 输出格式，支持 "HTML" 或 "TXT"
        """
        # 获取当前文件所在目录（modules目录）
        current_dir = Path(__file__).parent
        # 结果目录位于network_inspector目录下
        self.result_dir = current_dir.parent / result_dir
        self._ensure_dir_exists()
        
        self.output_format = output_format.upper()
    
    def _ensure_dir_exists(self) -> None:
        """
        确保结果目录存在，如果不存在则创建
        """
        try:
            self.result_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"创建结果目录失败: {e}")
    
    def set_output_format(self, output_format: str) -> None:
        """
        动态设置输出格式
        """
        if output_format:
            self.output_format = output_format.upper()

    def generate_result_file(self, device_info: Dict[str, Any], commands_results: List[Tuple[str, str]]) -> str:
        """
        生成设备巡检结果文件
        
        Args:
            device_info: 设备信息字典
            commands_results: 命令执行结果列表，每个元素为(命令, 输出)
            
        Returns:
            str: 生成的结果文件路径
            
        Raises:
            Exception: 生成结果文件失败时抛出
        """
        try:
            # 确定格式
            current_format = self.output_format.upper()
            
            # 生成文件名
            device_name = Utils.sanitize_filename(device_info["设备名称"])
            file_time = Utils.get_file_time()
            
            # 根据格式确定扩展名
            current_format = self.output_format.upper()
            if "TXT" in current_format:
                extension = "txt"
            elif "HTML" in current_format:
                extension = "html"
            else:
                extension = "txt"  # 默认为txt，更安全
            
            filename = f"{device_name}_{file_time}.{extension}"
            file_path = self.result_dir / filename
            
            # 构建文件内容
            if "HTML" in current_format:
                content = self._build_file_content(device_info, commands_results)
            else:
                content = self._build_txt_content(device_info, commands_results)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(file_path)
        
        except Exception as e:
            raise Exception(f"生成结果文件失败: {e}")
    
    def _build_file_content(self, device_info: Dict[str, Any], commands_results: List[Tuple[str, str]]) -> str:
        """
        构建清晰明了的浅色表格风格 HTML 巡检报告
        """
        device_name = html.escape(str(device_info.get("设备名称", "未知")))
        ip_address = html.escape(str(device_info.get("IP地址", "未知")))
        device_type = html.escape(str(device_info.get("设备类型", "未知")).upper())
        conn_type = html.escape(str(device_info.get("连接类型", "未知")).upper())
        port = html.escape(str(device_info.get("端口号", "未知")))

        html_content = '<!DOCTYPE html>\n'
        html_content += '<html lang="zh-CN">\n'
        html_content += '<head>\n'
        html_content += '    <meta charset="UTF-8">\n'
        html_content += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        html_content += f'    <title>网络设备巡检报告 - {device_name} ({ip_address})</title>\n'
        html_content += '    <style>\n'
        html_content += '        * { box-sizing: border-box; margin: 0; padding: 0; }\n'
        html_content += '        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; background-color: #f8fafc; color: #1e293b; line-height: 1.5; padding: 30px 16px; }\n'
        html_content += '        .report-paper { max-width: 1000px; margin: 0 auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); padding: 36px 40px; }\n'
        html_content += '        .report-header { text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }\n'
        html_content += '        .report-title { font-size: 24px; font-weight: 700; color: #0f172a; letter-spacing: 1px; margin: 0; }\n'
        html_content += '        .section-heading { font-size: 15px; font-weight: 700; color: #1e293b; margin: 24px 0 12px 0; display: flex; align-items: center; gap: 8px; }\n'
        html_content += '        .section-heading::before { content: ""; display: inline-block; width: 4px; height: 16px; background: #2563eb; border-radius: 2px; }\n'
        html_content += '        .grid-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }\n'
        html_content += '        .grid-table th, .grid-table td { border: 1px solid #cbd5e1; padding: 10px 14px; text-align: left; }\n'
        html_content += '        .grid-table th { background-color: #f1f5f9; color: #334155; font-weight: 600; width: 140px; }\n'
        html_content += '        .grid-table td { background-color: #ffffff; color: #0f172a; }\n'
        html_content += '        .cmd-card { border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 16px; overflow: hidden; background: #ffffff; }\n'
        html_content += '        .cmd-header { background-color: #f8fafc; border-bottom: 1px solid #cbd5e1; padding: 9px 14px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }\n'
        html_content += '        .cmd-name { font-family: Consolas, "Courier New", monospace; font-weight: 700; color: #1d4ed8; font-size: 13px; }\n'
        html_content += '        .cmd-lines { font-size: 12px; color: #64748b; background: #e2e8f0; padding: 2px 8px; border-radius: 3px; }\n'
        html_content += '        .cmd-content { padding: 14px 16px; font-family: Consolas, "Courier New", monospace; font-size: 12.5px; line-height: 1.55; color: #1e293b; background-color: #fafbfc; white-space: pre-wrap; word-break: break-all; overflow-x: auto; max-height: 600px; overflow-y: auto; }\n'
        html_content += '        @media print {\n'
        html_content += '            body { background: #fff; padding: 0; }\n'
        html_content += '            .report-paper { box-shadow: none; border: none; padding: 0; max-width: 100%; }\n'
        html_content += '            .cmd-card { page-break-inside: avoid; }\n'
        html_content += '            .cmd-content { max-height: none; background: #fff; }\n'
        html_content += '        }\n'
        html_content += '    </style>\n'
        html_content += '</head>\n'
        html_content += '<body>\n'
        html_content += '    <div class="report-paper">\n'
        html_content += '        <div class="report-header">\n'
        html_content += '            <h1 class="report-title">网络设备自动化巡检报告</h1>\n'
        html_content += '        </div>\n\n'
        html_content += '        <div class="section-heading">一、设备基本信息</div>\n'
        html_content += '        <table class="grid-table">\n'
        html_content += '            <tr>\n'
        html_content += f'                <th>设备名称</th><td>{device_name}</td>\n'
        html_content += f'                <th>管理 IP</th><td>{ip_address}</td>\n'
        html_content += '            </tr>\n'
        html_content += '            <tr>\n'
        html_content += f'                <th>设备厂商</th><td>{device_type}</td>\n'
        html_content += f'                <th>连接方式</th><td>{conn_type} (端口: {port})</td>\n'
        html_content += '            </tr>\n'
        html_content += '        </table>\n\n'
        html_content += '        <div class="section-heading">二、巡检指令执行记录</div>\n'

        for i, (command, output) in enumerate(commands_results, 1):
            safe_cmd = html.escape(command)
            safe_output = html.escape(output)
            out_lines = len(output.splitlines())
            html_content += '        <div class="cmd-card">\n'
            html_content += '            <div class="cmd-header">\n'
            html_content += f'                <span class="cmd-name">{safe_cmd}</span>\n'
            html_content += f'                <span class="cmd-lines">{out_lines} 行输出</span>\n'
            html_content += '            </div>\n'
            html_content += f'            <pre class="cmd-content">{safe_output}</pre>\n'
            html_content += '        </div>\n'

        html_content += '    </div>\n'
        html_content += '</body>\n'
        html_content += '</html>\n'

        return html_content

    def _build_txt_content(self, device_info: Dict[str, Any], commands_results: List[Tuple[str, str]]) -> str:
        """
        构建清晰、规整的表格样式 TXT 格式巡检报告
        """
        device_name = device_info.get("设备名称", "未知")
        ip_address = device_info.get("IP地址", "未知")
        device_type = str(device_info.get("设备类型", "未知")).upper()
        conn_type = str(device_info.get("连接类型", "未知")).upper()
        port = device_info.get("端口号", "未知")

        txt_content = "=" * 80 + "\n"
        txt_content += "                         网络设备自动化巡检报告                         \n"
        txt_content += "=" * 80 + "\n\n"

        txt_content += "【一、设备基本信息】\n"
        txt_content += "+-----------------------+------------------------------------------------------+\n"
        txt_content += f"| 设备名称              | {device_name:<52} |\n"
        txt_content += f"| IP 地址               | {ip_address:<52} |\n"
        txt_content += f"| 设备厂商              | {device_type:<52} |\n"
        txt_content += f"| 连接方式              | {conn_type + ' (端口: ' + str(port) + ')':<52} |\n"
        txt_content += "+-----------------------+------------------------------------------------------+\n\n"

        txt_content += "【二、巡检指令执行记录】\n"
        txt_content += "=" * 80 + "\n"

        for i, (command, output) in enumerate(commands_results, 1):
            txt_content += f"\n>>> {command}\n"
            txt_content += "-" * 80 + "\n"
            txt_content += output.rstrip() + "\n"
            txt_content += "-" * 80 + "\n"

        txt_content += "\n" + "=" * 80 + "\n"
        txt_content += "                               --- 报告结束 ---\n"
        txt_content += "=" * 80 + "\n"

        return txt_content
    
    def get_result_dir(self) -> str:
        """
        获取结果目录的绝对路径
        
        Returns:
            str: 结果目录的绝对路径
        """
        return str(self.result_dir.absolute())
    
    def list_result_files(self) -> List[str]:
        """
        列出结果目录中的所有文件
        
        Returns:
            List[str]: 结果文件路径列表
        """
        try:
            # 列出所有 html 和 txt 文件
            files = []
            for ext in ["*.html", "*.txt"]:
                files.extend([str(file) for file in self.result_dir.glob(ext)])
            return files
        except Exception as e:
            raise Exception(f"列出结果文件失败: {e}")
    
    def delete_result_file(self, file_path: str) -> bool:
        """
        删除指定的结果文件
        
        Args:
            file_path: 要删除的文件路径
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        try:
            file = Path(file_path)
            if file.exists() and file.parent == self.result_dir:
                file.unlink()
                return True
            return False
        except Exception:
            return False
    
    def clear_result_dir(self) -> bool:
        """
        清空结果目录中的所有文件
        
        Returns:
            bool: 清空成功返回True，否则返回False
        """
        try:
            for ext in ["*.html", "*.txt"]:
                for file in self.result_dir.glob(ext):
                    file.unlink()
            return True
        except Exception:
            return False
    
    def append_to_log(self, log_message: str, log_file: str = "inspection.log") -> None:
        """
        不再生成日志文件，直接返回
        
        Args:
            log_message: 日志消息
            log_file: 日志文件名，默认 "inspection.log"
        """
        # 不再生成日志文件，直接返回
        return
