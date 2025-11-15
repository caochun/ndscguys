"""
员工信息编辑对话框
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QDateEdit, QPushButton,
                             QMessageBox, QGroupBox, QLabel)
from PyQt6.QtCore import QDate, Qt
from datetime import datetime
from employee_service import EmployeeService
from model import Employee, EmploymentInfo


class EmployeeDialog(QDialog):
    """员工信息编辑对话框"""
    
    def __init__(self, parent=None, employee_id=None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            employee_id: 员工ID，如果为None则是新增模式，否则是编辑模式
        """
        super().__init__(parent)
        self.employee_service = EmployeeService()
        self.employee_id = employee_id
        self.is_edit_mode = employee_id is not None
        
        # 保存原始入职信息，用于判断是否有变更
        self.original_employment_info = None
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_employee_data()
    
    def init_ui(self):
        """初始化界面"""
        if self.is_edit_mode:
            self.setWindowTitle("编辑员工信息")
        else:
            self.setWindowTitle("新增员工")
        
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # ========== 个人信息部分 ==========
        personal_group = QGroupBox("个人信息（不变动）")
        personal_layout = QFormLayout()
        
        # 员工编号
        self.employee_number_edit = QLineEdit()
        if self.is_edit_mode:
            self.employee_number_edit.setEnabled(False)  # 编辑模式下不允许修改编号
        personal_layout.addRow("员工编号 *:", self.employee_number_edit)
        
        # 姓名
        self.name_edit = QLineEdit()
        personal_layout.addRow("姓名 *:", self.name_edit)
        
        # 出生日期
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate())
        self.birth_date_edit.setDisplayFormat("yyyy-MM-dd")
        personal_layout.addRow("出生日期:", self.birth_date_edit)
        
        # 性别
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "男", "女", "其他"])
        personal_layout.addRow("性别:", self.gender_combo)
        
        # 手机
        self.phone_edit = QLineEdit()
        personal_layout.addRow("手机:", self.phone_edit)
        
        # 邮箱
        self.email_edit = QLineEdit()
        personal_layout.addRow("邮箱:", self.email_edit)
        
        personal_group.setLayout(personal_layout)
        layout.addWidget(personal_group)
        
        # ========== 入职信息部分 ==========
        employment_group = QGroupBox("入职信息（会变动）")
        employment_layout = QFormLayout()
        
        # 部门
        self.department_edit = QLineEdit()
        employment_layout.addRow("部门 *:", self.department_edit)
        
        # 职位
        self.position_edit = QLineEdit()
        employment_layout.addRow("职位 *:", self.position_edit)
        
        # 上级
        self.supervisor_combo = QComboBox()
        self.supervisor_combo.addItem("（无）", None)
        self.load_supervisors()
        employment_layout.addRow("上级:", self.supervisor_combo)
        
        # 入职时间
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setDisplayFormat("yyyy-MM-dd")
        employment_layout.addRow("入职时间 *:", self.hire_date_edit)
        
        # 变更原因（仅在编辑模式下显示）
        if self.is_edit_mode:
            self.change_reason_edit = QLineEdit()
            self.change_reason_edit.setPlaceholderText("如果入职信息有变更，请填写变更原因")
            employment_layout.addRow("变更原因:", self.change_reason_edit)
        
        employment_group.setLayout(employment_layout)
        layout.addWidget(employment_group)
        
        # ========== 按钮 ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_employee)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_supervisors(self):
        """加载上级员工列表"""
        try:
            employees = self.employee_service.get_all_employees()
            for emp in employees:
                # 编辑模式下，排除自己
                if self.is_edit_mode and emp.id == self.employee_id:
                    continue
                self.supervisor_combo.addItem(f"{emp.name} ({emp.employee_number})", emp.id)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载上级列表失败：{str(e)}")
    
    def load_employee_data(self):
        """加载员工数据（编辑模式）"""
        try:
            data = self.employee_service.get_employee_with_employment_info(self.employee_id)
            if not data:
                QMessageBox.warning(self, "错误", "员工不存在")
                self.reject()
                return
            
            employee = data['employee']
            employment_info = data['employment_info']
            
            # 填充个人信息
            self.employee_number_edit.setText(employee.employee_number)
            self.name_edit.setText(employee.name)
            
            if employee.birth_date:
                date = QDate.fromString(employee.birth_date, "yyyy-MM-dd")
                if date.isValid():
                    self.birth_date_edit.setDate(date)
            
            if employee.gender:
                index = self.gender_combo.findText(employee.gender)
                if index >= 0:
                    self.gender_combo.setCurrentIndex(index)
            
            self.phone_edit.setText(employee.phone or "")
            self.email_edit.setText(employee.email or "")
            
            # 填充入职信息
            if employment_info:
                self.original_employment_info = employment_info
                self.department_edit.setText(employment_info.department)
                self.position_edit.setText(employment_info.position)
                
                if employment_info.hire_date:
                    date = QDate.fromString(employment_info.hire_date, "yyyy-MM-dd")
                    if date.isValid():
                        self.hire_date_edit.setDate(date)
                
                # 设置上级
                if employment_info.supervisor_id:
                    index = self.supervisor_combo.findData(employment_info.supervisor_id)
                    if index >= 0:
                        self.supervisor_combo.setCurrentIndex(index)
            else:
                # 如果没有入职信息，说明是新员工，入职时间默认为今天
                self.hire_date_edit.setDate(QDate.currentDate())
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载员工数据失败：{str(e)}")
            self.reject()
    
    def validate_input(self):
        """验证输入"""
        # 必填项检查
        if not self.employee_number_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "员工编号不能为空")
            return False
        
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "姓名不能为空")
            return False
        
        if not self.department_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "部门不能为空")
            return False
        
        if not self.position_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "职位不能为空")
            return False
        
        return True
    
    def has_employment_info_changed(self):
        """检查入职信息是否有变更"""
        if not self.original_employment_info:
            return False
        
        return (
            self.department_edit.text().strip() != self.original_employment_info.department or
            self.position_edit.text().strip() != self.original_employment_info.position or
            self.hire_date_edit.date().toString("yyyy-MM-dd") != self.original_employment_info.hire_date or
            self.supervisor_combo.currentData() != self.original_employment_info.supervisor_id
        )
    
    def save_employee(self):
        """保存员工信息"""
        if not self.validate_input():
            return
        
        try:
            # 准备数据
            employee_number = self.employee_number_edit.text().strip()
            name = self.name_edit.text().strip()
            birth_date = self.birth_date_edit.date().toString("yyyy-MM-dd") if self.birth_date_edit.date().isValid() else None
            gender = self.gender_combo.currentText() if self.gender_combo.currentText() else None
            phone = self.phone_edit.text().strip() or None
            email = self.email_edit.text().strip() or None
            
            department = self.department_edit.text().strip()
            position = self.position_edit.text().strip()
            hire_date = self.hire_date_edit.date().toString("yyyy-MM-dd")
            supervisor_id = self.supervisor_combo.currentData()
            change_reason = None
            
            if self.is_edit_mode:
                # 更新员工信息
                employee = self.employee_service.get_employee(self.employee_id)
                employee.name = name
                employee.birth_date = birth_date
                employee.gender = gender
                employee.phone = phone
                employee.email = email
                
                self.employee_service.update_employee(employee)
                
                # 检查入职信息是否有变更，如果有变更则更新（会自动记录历史）
                if self.has_employment_info_changed():
                    change_reason = self.change_reason_edit.text().strip() or "未填写变更原因"
                    self.employee_service.update_employment_info(
                        self.employee_id,
                        department,
                        position,
                        hire_date,
                        supervisor_id,
                        change_reason
                    )
            else:
                # 新增模式
                employee = Employee(
                    employee_number=employee_number,
                    name=name,
                    birth_date=birth_date,
                    gender=gender,
                    phone=phone,
                    email=email
                )
                
                employee_id = self.employee_service.create_employee(employee)
                
                # 创建入职信息
                employment_info = EmploymentInfo(
                    employee_id=employee_id,
                    department=department,
                    position=position,
                    hire_date=hire_date,
                    supervisor_id=supervisor_id
                )
                
                self.employee_service.create_employment_info(employment_info)
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "验证失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

