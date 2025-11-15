"""
考勤管理服务层
"""
from typing import List, Optional
from datetime import datetime, timedelta
from app.daos.attendance_dao import AttendanceDAO
from app.daos.leave_record_dao import LeaveRecordDAO
from app.daos.employee_dao import EmployeeDAO
from app.models import Attendance, LeaveRecord


class AttendanceService:
    """考勤管理服务类"""
    
    def __init__(self):
        self.attendance_dao = AttendanceDAO()
        self.leave_record_dao = LeaveRecordDAO()
        self.employee_dao = EmployeeDAO()
    
    # ========== 考勤记录管理 ==========
    
    def create_attendance(self, attendance: Attendance) -> int:
        """
        创建考勤记录
        
        Args:
            attendance: 考勤记录对象
            
        Returns:
            新创建的考勤记录ID
        """
        # 如果提供了 employee_id，验证其存在性
        if attendance.employee_id:
            employee = self.employee_dao.get_by_id(attendance.employee_id)
            if not employee:
                raise ValueError(f"员工ID {attendance.employee_id} 不存在")
            # 确保 employee_id 对应的 person_id 与 attendance.person_id 一致
            if employee.person_id != attendance.person_id:
                raise ValueError("员工ID与人员ID不匹配")
        
        # 计算请假时长（汇总该日期所有已批准的请假记录）
        leave_hours = self._calculate_leave_hours(
            attendance.person_id, 
            attendance.company_name, 
            attendance.attendance_date
        )
        attendance.leave_hours = leave_hours
        
        # 如果没有指定状态，根据数据自动判断
        if not attendance.status:
            attendance.status = self._determine_status(
                attendance.check_in_time,
                attendance.check_out_time,
                leave_hours,
                attendance.standard_hours
            )
        
        # 计算工作时长
        if attendance.check_in_time and attendance.check_out_time:
            attendance.work_hours = self._calculate_work_hours(
                attendance.check_in_time,
                attendance.check_out_time
            )
            # 计算加班时长
            if attendance.work_hours > attendance.standard_hours:
                attendance.overtime_hours = attendance.work_hours - attendance.standard_hours
        
        return self.attendance_dao.create(attendance)
    
    def get_attendance_by_id(self, attendance_id: int) -> Optional[Attendance]:
        """根据ID获取考勤记录"""
        return self.attendance_dao.get_by_id(attendance_id)
    
    def get_attendance_by_person(self, person_id: int, 
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> List[Attendance]:
        """
        获取人员的考勤记录（跨公司）
        
        Args:
            person_id: 人员ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.attendance_dao.get_by_person_id(person_id, start_date, end_date)
    
    def get_attendance_by_person_and_company(self, person_id: int, company_name: str,
                                            start_date: Optional[str] = None,
                                            end_date: Optional[str] = None) -> List[Attendance]:
        """
        获取人员在某个公司的考勤记录
        
        Args:
            person_id: 人员ID
            company_name: 公司名称
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.attendance_dao.get_by_person_and_company(
            person_id, company_name, start_date, end_date
        )
    
    def get_attendance_by_employee(self, employee_id: int,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Attendance]:
        """
        获取员工的考勤记录
        
        Args:
            employee_id: 员工ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.attendance_dao.get_by_employee_id(employee_id, start_date, end_date)
    
    def get_attendance_by_date(self, attendance_date: str, 
                              company_name: Optional[str] = None) -> List[Attendance]:
        """
        获取某日期的考勤记录
        
        Args:
            attendance_date: 考勤日期
            company_name: 公司名称（可选）
        """
        return self.attendance_dao.get_by_date(attendance_date, company_name)
    
    def get_attendance_by_date_range(self, start_date: Optional[str] = None,
                                    end_date: Optional[str] = None,
                                    company_name: Optional[str] = None) -> List[Attendance]:
        """
        根据日期范围获取考勤记录（所有人员）
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            company_name: 公司名称（可选）
        """
        return self.attendance_dao.get_by_date_range(start_date, end_date, company_name)
    
    def update_attendance(self, attendance: Attendance) -> bool:
        """
        更新考勤记录
        
        注意：更新时会重新计算请假时长和工作时长
        """
        if attendance.id is None:
            raise ValueError("考勤记录ID不能为空")
        
        # 重新计算请假时长
        attendance.leave_hours = self._calculate_leave_hours(
            attendance.person_id,
            attendance.company_name,
            attendance.attendance_date
        )
        
        # 重新计算工作时长和加班时长
        if attendance.check_in_time and attendance.check_out_time:
            attendance.work_hours = self._calculate_work_hours(
                attendance.check_in_time,
                attendance.check_out_time
            )
            if attendance.work_hours > attendance.standard_hours:
                attendance.overtime_hours = attendance.work_hours - attendance.standard_hours
            else:
                attendance.overtime_hours = 0.0
        
        # 重新判断状态
        attendance.status = self._determine_status(
            attendance.check_in_time,
            attendance.check_out_time,
            attendance.leave_hours,
            attendance.standard_hours
        )
        
        return self.attendance_dao.update(attendance)
    
    def delete_attendance(self, attendance_id: int) -> bool:
        """删除考勤记录"""
        return self.attendance_dao.delete(attendance_id)
    
    # ========== 请假记录管理 ==========
    
    def create_leave_record(self, leave_record: LeaveRecord) -> int:
        """
        创建请假记录
        
        Args:
            leave_record: 请假记录对象
            
        Returns:
            新创建的请假记录ID
        """
        # 如果提供了 employee_id，验证其存在性
        if leave_record.employee_id:
            employee = self.employee_dao.get_by_id(leave_record.employee_id)
            if not employee:
                raise ValueError(f"员工ID {leave_record.employee_id} 不存在")
            # 确保 employee_id 对应的 person_id 与 leave_record.person_id 一致
            if employee.person_id != leave_record.person_id:
                raise ValueError("员工ID与人员ID不匹配")
        
        leave_id = self.leave_record_dao.create(leave_record)
        
        # 如果请假已批准，更新对应日期的考勤记录的请假时长
        if leave_record.status == 'approved':
            self._update_attendance_leave_hours(
                leave_record.person_id,
                leave_record.company_name,
                leave_record.leave_date
            )
        
        return leave_id
    
    def get_leave_record_by_id(self, leave_id: int) -> Optional[LeaveRecord]:
        """根据ID获取请假记录"""
        return self.leave_record_dao.get_by_id(leave_id)
    
    def get_leave_records_by_person(self, person_id: int,
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        获取人员的请假记录（跨公司）
        
        Args:
            person_id: 人员ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.leave_record_dao.get_by_person_id(person_id, start_date, end_date)
    
    def get_leave_records_by_person_and_company(self, person_id: int, company_name: str,
                                                start_date: Optional[str] = None,
                                                end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        获取人员在某个公司的请假记录
        
        Args:
            person_id: 人员ID
            company_name: 公司名称
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.leave_record_dao.get_by_person_and_company(
            person_id, company_name, start_date, end_date
        )
    
    def get_leave_records_by_employee(self, employee_id: int,
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        获取员工的请假记录
        
        Args:
            employee_id: 员工ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        return self.leave_record_dao.get_by_employee_id(employee_id, start_date, end_date)
    
    def update_leave_record(self, leave_record: LeaveRecord) -> bool:
        """
        更新请假记录
        
        注意：如果状态改变，会更新对应日期的考勤记录
        """
        if leave_record.id is None:
            raise ValueError("请假记录ID不能为空")
        
        # 获取旧记录以判断状态是否改变
        old_record = self.leave_record_dao.get_by_id(leave_record.id)
        old_status = old_record.status if old_record else None
        
        result = self.leave_record_dao.update(leave_record)
        
        # 如果状态改变，更新考勤记录
        if old_status != leave_record.status and leave_record.status == 'approved':
            self._update_attendance_leave_hours(
                leave_record.person_id,
                leave_record.company_name,
                leave_record.leave_date
            )
        
        return result
    
    def delete_leave_record(self, leave_id: int) -> bool:
        """
        删除请假记录
        
        注意：删除后会更新对应日期的考勤记录
        """
        # 获取记录信息以便更新考勤
        leave_record = self.leave_record_dao.get_by_id(leave_id)
        
        result = self.leave_record_dao.delete(leave_id)
        
        # 如果删除的是已批准的请假，更新考勤记录
        if leave_record and leave_record.status == 'approved':
            self._update_attendance_leave_hours(
                leave_record.person_id,
                leave_record.company_name,
                leave_record.leave_date
            )
        
        return result
    
    # ========== 辅助方法 ==========
    
    def _calculate_leave_hours(self, person_id: int, company_name: str, 
                             attendance_date: str) -> float:
        """
        计算某日期已批准的请假总时长
        
        Args:
            person_id: 人员ID
            company_name: 公司名称
            attendance_date: 考勤日期
            
        Returns:
            请假总时长（小时）
        """
        leave_records = self.leave_record_dao.get_by_person_and_date(
            person_id, attendance_date
        )
        # 只统计已批准且属于该公司的请假
        total_hours = sum(
            record.leave_hours 
            for record in leave_records 
            if record.status == 'approved' and record.company_name == company_name
        )
        return total_hours
    
    def _calculate_work_hours(self, check_in_time: str, check_out_time: str) -> float:
        """
        计算工作时长（小时）
        
        Args:
            check_in_time: 签到时间（格式：YYYY-MM-DD HH:MM:SS）
            check_out_time: 签退时间（格式：YYYY-MM-DD HH:MM:SS）
            
        Returns:
            工作时长（小时，保留2位小数）
        """
        try:
            check_in = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S')
            delta = check_out - check_in
            hours = delta.total_seconds() / 3600.0
            return round(hours, 2)
        except (ValueError, TypeError):
            return 0.0
    
    def _determine_status(self, check_in_time: Optional[str], 
                         check_out_time: Optional[str],
                         leave_hours: float,
                         standard_hours: float) -> str:
        """
        根据签到签退时间和请假时长判断考勤状态
        
        Args:
            check_in_time: 签到时间（可选）
            check_out_time: 签退时间（可选）
            leave_hours: 请假时长
            standard_hours: 标准工作时长
            
        Returns:
            考勤状态
        """
        # 如果请假时长达到或超过标准工作时长，视为请假
        if leave_hours >= standard_hours:
            return 'leave'
        
        # 如果没有签到，视为缺勤
        if not check_in_time:
            if leave_hours > 0:
                return 'partial_leave'  # 部分请假
            return 'absent'
        
        # 如果有签到但没有签退，无法判断，返回 None 或 'incomplete'
        if not check_out_time:
            return 'incomplete'
        
        # 计算工作时长
        work_hours = self._calculate_work_hours(check_in_time, check_out_time)
        
        # 判断是否迟到（这里简化处理，实际应该根据标准上班时间判断）
        # 判断是否早退（这里简化处理，实际应该根据标准下班时间判断）
        # 如果工作时长小于标准时长减去请假时长，可能早退
        if work_hours < (standard_hours - leave_hours) * 0.8:
            return 'early_leave'
        
        # 默认正常
        return 'normal'
    
    def _update_attendance_leave_hours(self, person_id: int, company_name: str,
                                      attendance_date: str):
        """
        更新考勤记录的请假时长
        
        当请假记录创建、更新或删除时调用
        """
        # 查找或创建考勤记录
        attendance_list = self.attendance_dao.get_by_person_and_company(
            person_id, company_name, attendance_date, attendance_date
        )
        
        # 计算新的请假时长
        leave_hours = self._calculate_leave_hours(person_id, company_name, attendance_date)
        
        if attendance_list:
            # 更新现有考勤记录
            attendance = attendance_list[0]
            attendance.leave_hours = leave_hours
            # 重新判断状态
            attendance.status = self._determine_status(
                attendance.check_in_time,
                attendance.check_out_time,
                leave_hours,
                attendance.standard_hours
            )
            self.attendance_dao.update(attendance)
        # 如果没有考勤记录，不自动创建（需要手动创建考勤记录）

