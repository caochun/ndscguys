"""
主窗口
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QSplitter, QLabel)
from PyQt6.QtCore import Qt
from employee_service import EmployeeService
from ui.employee_dialog import EmployeeDialog


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.employee_service = EmployeeService()
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("人事管理系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新增员工")
        self.add_btn.clicked.connect(self.add_employee)
        toolbar_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑员工")
        self.edit_btn.clicked.connect(self.edit_employee)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除员工")
        self.delete_btn.clicked.connect(self.delete_employee)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_employees)
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # 员工列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "员工编号", "姓名", "性别", "手机", "邮箱", "部门", "职位"
        ])
        
        # 设置表格属性
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 员工编号
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 姓名
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 性别
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 手机
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # 邮箱
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # 部门
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # 职位
        
        main_layout.addWidget(self.table)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def load_employees(self):
        """加载员工列表"""
        try:
            employees_data = self.employee_service.get_all_employees_with_info()
            
            self.table.setRowCount(len(employees_data))
            
            for row, data in enumerate(employees_data):
                employee = data['employee']
                employment_info = data['employment_info']
                
                # 填充表格数据
                self.table.setItem(row, 0, QTableWidgetItem(str(employee.id)))
                self.table.setItem(row, 1, QTableWidgetItem(employee.employee_number))
                self.table.setItem(row, 2, QTableWidgetItem(employee.name))
                self.table.setItem(row, 3, QTableWidgetItem(employee.gender or ""))
                self.table.setItem(row, 4, QTableWidgetItem(employee.phone or ""))
                self.table.setItem(row, 5, QTableWidgetItem(employee.email or ""))
                
                if employment_info:
                    self.table.setItem(row, 6, QTableWidgetItem(employment_info.department))
                    self.table.setItem(row, 7, QTableWidgetItem(employment_info.position))
                else:
                    self.table.setItem(row, 6, QTableWidgetItem(""))
                    self.table.setItem(row, 7, QTableWidgetItem(""))
            
            self.statusBar().showMessage(f"已加载 {len(employees_data)} 名员工")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载员工列表失败：{str(e)}")
    
    def get_selected_employee_id(self):
        """获取当前选中的员工ID"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        id_item = self.table.item(current_row, 0)
        if id_item:
            return int(id_item.text())
        return None
    
    def add_employee(self):
        """新增员工"""
        dialog = EmployeeDialog(self)
        if dialog.exec():
            self.load_employees()
            self.statusBar().showMessage("员工添加成功")
    
    def edit_employee(self):
        """编辑员工"""
        employee_id = self.get_selected_employee_id()
        if not employee_id:
            QMessageBox.warning(self, "提示", "请先选择要编辑的员工")
            return
        
        dialog = EmployeeDialog(self, employee_id=employee_id)
        if dialog.exec():
            self.load_employees()
            self.statusBar().showMessage("员工信息更新成功")
    
    def delete_employee(self):
        """删除员工"""
        employee_id = self.get_selected_employee_id()
        if not employee_id:
            QMessageBox.warning(self, "提示", "请先选择要删除的员工")
            return
        
        # 获取员工信息用于确认
        employee = self.employee_service.get_employee(employee_id)
        if not employee:
            QMessageBox.warning(self, "提示", "员工不存在")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除员工 {employee.name} ({employee.employee_number}) 吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.employee_service.delete_employee(employee_id)
                self.load_employees()
                self.statusBar().showMessage("员工删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除员工失败：{str(e)}")

