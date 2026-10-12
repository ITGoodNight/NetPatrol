from openpyxl import load_workbook
from pathlib import Path
import re

class DeviceParser:
    """
    设备清单解析器，负责从Excel文件读取设备信息并进行数据清洗
    """
    
    def __init__(self, excel_path: str = "设备清单.xlsx"):
        # 检查excel_path是否为绝对路径
        if Path(excel_path).is_absolute():
            # 如果是绝对路径，直接使用
            self.excel_path = Path(excel_path)
        else:
            # 否则，将其作为network_inspector目录下的相对路径
            current_dir = Path(__file__).parent
            self.excel_path = current_dir.parent / excel_path
            
        self.required_columns = {
            "设备名称": str,
            "设备类型": str,
            "IP地址": str,
            "端口号": (int, type(None)),
            "连接类型": str,
            "用户名": str,
            "密码": str,
            "提权密码": str  # 新增提权密码字段
        }
    
    def parse_devices(self) -> list:
        """
        解析Excel文件，返回设备列表
        
        Returns:
            list: 设备字典列表
            
        Raises:
            FileNotFoundError: Excel文件不存在时抛出
            ValueError: Excel格式错误时抛出
        """
        if not self.excel_path.exists():
            raise FileNotFoundError(f"设备清单文件 '{self.excel_path}' 不存在")
        
        try:
            # 加载Excel文件
            workbook = load_workbook(filename=str(self.excel_path), data_only=True)
            sheet = workbook.active
            
            # 查找表头行
            header_row = self._find_header_row(sheet)
            if not header_row:
                raise ValueError("Excel文件中未找到有效的表头行")
            
            # 建立列名到列索引的映射
            column_map = self._build_column_map(sheet, header_row)
            
            # 解析设备数据
            devices = []
            for row_num in range(header_row + 1, sheet.max_row + 1):
                device = self._parse_row(sheet, row_num, column_map)
                if device:
                    devices.append(device)
            
            return devices
        
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"解析Excel文件失败: {e}")
    
    def _find_header_row(self, sheet) -> int:
        """
        查找包含所需列的表头行
        
        Args:
            sheet: Excel工作表对象
            
        Returns:
            int: 表头行号（从1开始），未找到则返回0
        """
        for row_num in range(1, min(10, sheet.max_row + 1)):  # 最多检查前10行
            row_values = [cell.value for cell in sheet[row_num]]
            
            # 检查是否包含所有必需列名
            found_columns = 0
            for col_name in self.required_columns.keys():
                if col_name in row_values:
                    found_columns += 1
            
            if found_columns == len(self.required_columns):
                return row_num
        
        return 0
    
    def _build_column_map(self, sheet, header_row: int) -> dict:
        """
        建立列名到列索引的映射
        
        Args:
            sheet: Excel工作表对象
            header_row: 表头行号
            
        Returns:
            dict: 列名到列索引的映射
        """
        column_map = {}
        for col_num, cell in enumerate(sheet[header_row], 1):  # 列号从1开始
            col_name = cell.value
            if col_name in self.required_columns:
                column_map[col_name] = col_num
        
        return column_map
    
    def _parse_row(self, sheet, row_num: int, column_map: dict) -> dict or None:
        """
        解析单行设备数据
        
        Args:
            sheet: Excel工作表对象
            row_num: 行号
            column_map: 列名到列索引的映射
            
        Returns:
            dict or None: 设备字典，无效行返回None
        """
        device = {}
        
        # 解析设备名称（必须字段）
        device_name_raw = sheet.cell(row=row_num, column=column_map["设备名称"]).value
        # 先判断是否为空，再统一转成字符串处理，避免数值类型没有 strip 方法
        if device_name_raw is None:
            return None  # 跳过空行
        device_name = str(device_name_raw).strip()
        if device_name == "" or device_name.startswith("#"):
            return None  # 跳过空行或注释行
        device["设备名称"] = device_name
        
        # 解析设备类型（必须字段）
        device_type_raw = sheet.cell(row=row_num, column=column_map["设备类型"]).value
        if device_type_raw is None:
            return None  # 设备类型为空，跳过该行
        device_type = str(device_type_raw).strip()
        if device_type == "":
            return None
        device["设备类型"] = device_type.lower()
        
        # 解析IP地址（必须字段）
        ip_address_raw = sheet.cell(row=row_num, column=column_map["IP地址"]).value
        if ip_address_raw is None:
            return None  # IP地址为空，跳过该行
        ip_address = str(ip_address_raw).strip()
        if ip_address == "":
            return None
        device["IP地址"] = ip_address
        
        # 解析端口号（可选，提供默认值）
        port = sheet.cell(row=row_num, column=column_map["端口号"]).value
        device["端口号"] = int(port) if port else None  # 稍后在数据清洗中处理默认值
        
        # 解析连接类型（必须字段，默认SSH）
        conn_type = sheet.cell(row=row_num, column=column_map["连接类型"]).value
        device["连接类型"] = str(conn_type).strip().lower() if conn_type else "ssh"
        
        # 解析用户名（必须字段，允许为空）
        username = sheet.cell(row=row_num, column=column_map["用户名"]).value
        device["用户名"] = str(username).strip() if username else ""
        
        # 解析密码（必须字段，允许为空）
        password = sheet.cell(row=row_num, column=column_map["密码"]).value
        device["密码"] = str(password).strip() if password else ""
        
        # 解析提权密码（可选字段，默认为空）
        secret = sheet.cell(row=row_num, column=column_map["提权密码"]).value
        device["提权密码"] = str(secret).strip() if secret else ""
        
        # 数据清洗：填充默认值
        device = self._clean_device_data(device)
        
        return device
    
    def _clean_device_data(self, device: dict) -> dict:
        """
        清洗设备数据，填充默认值
        
        Args:
            device: 设备字典
            
        Returns:
            dict: 清洗后的设备字典
        """
        # 处理端口号默认值
        if not device["端口号"]:
            if device["连接类型"] == "ssh":
                device["端口号"] = 22
            elif device["连接类型"] == "telnet":
                device["端口号"] = 23
            else:
                device["端口号"] = 22  # 默认SSH端口
        
        # 标准化连接类型
        if device["连接类型"] not in ["ssh", "telnet"]:
            device["连接类型"] = "ssh"  # 默认为SSH
        
        return device
    
    def validate_ip_address(self, ip: str) -> bool:
        """
        验证IP地址格式是否正确
        
        Args:
            ip: IP地址字符串
            
        Returns:
            bool: IP地址格式正确返回True，否则返回False
        """
        ip_pattern = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
        return re.match(ip_pattern, ip) is not None
