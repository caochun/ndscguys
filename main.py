"""
人事管理系统 - 主程序入口
"""
import sys
import os

# 设置 Qt 插件路径（解决 macOS 上找不到 cocoa 插件的问题）
try:
    import PyQt6.QtCore
    qt_path = os.path.dirname(PyQt6.QtCore.__file__)
    plugin_path = os.path.join(qt_path, 'Qt6', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_PLUGIN_PATH'] = plugin_path
except Exception:
    pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("人事管理系统")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

