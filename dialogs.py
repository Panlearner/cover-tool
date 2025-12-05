"""
dialogs.py - 对话框组件
"""
from PyQt5 import QtWidgets, QtCore, QtGui


class AddElementDialog(QtWidgets.QDialog):
    """添加新元素的对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新元素")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QtWidgets.QFormLayout()
        
        # 元素ID输入
        self.id_edit = QtWidgets.QLineEdit()
        self.id_edit.setPlaceholderText("例如: my_custom_text")
        layout.addRow("元素ID:", self.id_edit)
        
        # 元素类型选择
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["text", "badge", "image"])
        layout.addRow("元素类型:", self.type_combo)
        
        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        self.ok_btn = QtWidgets.QPushButton("确定")
        self.cancel_btn = QtWidgets.QPushButton("取消")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    
    def get_element_info(self):
        """获取元素信息"""
        return {
            "id": self.id_edit.text().strip(),
            "type": self.type_combo.currentText()
        }