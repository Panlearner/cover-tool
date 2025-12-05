"""
cover.py - 封面生成器主界面
"""
import os
import sys
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from cover_engine import render_cover, add_custom_element, delete_element

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class CoverGenerator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("封面生成器 · cover.py")
        self.layout_cfg = load_json(os.path.join(BASE_DIR, "layout.json"))
        self.style_cfg = load_json(os.path.join(BASE_DIR, "style.json"))
        self.input_widgets = {}  # 存储输入控件
        self.image_paths = {}  # 存储图片路径
        self.custom_elements = {}  # 存储自定义元素
        self.init_ui()
    
    def init_ui(self):
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.init_toolbar()
        
        # 创建滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        
        content_widget = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        
        # 动态生成输入控件
        self.create_dynamic_inputs()
        
        # 添加通用参数
        self.create_common_parameters()
        
        content_widget.setLayout(self.form_layout)
        scroll.setWidget(content_widget)
        
        main_layout.addWidget(scroll)
        
        # 生成按钮
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_generate = QtWidgets.QPushButton("生成封面")
        self.btn_generate.setStyleSheet("font-size: 14px; padding: 10px;")
        self.btn_generate.clicked.connect(self.on_generate)
        btn_layout.addWidget(self.btn_generate)
        
        main_layout.addLayout(btn_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        self.resize(600, 800)
    
    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = self.addToolBar("工具")
        
        # 刷新按钮
        refresh_action = QtWidgets.QAction(QtGui.QIcon(), "刷新", self)
        refresh_action.triggered.connect(self.on_refresh)
        toolbar.addAction(refresh_action)
        
        # 分隔符
        toolbar.addSeparator()
        
        # 打开编辑器按钮
        editor_action = QtWidgets.QAction(QtGui.QIcon(), "打开编辑器", self)
        editor_action.triggered.connect(self.open_editor)
        toolbar.addAction(editor_action)
    
    def create_dynamic_inputs(self):
        """根据layout.json动态创建输入控件"""
        elements = self.layout_cfg.get("elements", [])
        
        # 添加标题
        title_label = QtWidgets.QLabel("封面元素配置")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.form_layout.addRow(title_label)
        
        # 添加分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.form_layout.addRow(line)
        
        # 预定义元素的映射
        predefined_mapping = {
            "title_main": ("主标题", "text", True),
            "episode_badge": ("集数", "badge", True),
            "tagline": ("副标题", "text", False)
        }
        
        for elem in elements:
            if not elem.get("enabled", True):
                continue
            
            elem_id = elem["id"]
            elem_type = elem.get("type", "text")
            
            # 确定显示标签
            if elem_id in predefined_mapping:
                label_text, _, required = predefined_mapping[elem_id]
                is_required = required
            else:
                # 自定义元素
                label_text = f"{elem_id} [{elem_type}]"
                is_required = False
                self.custom_elements[elem_id] = elem_type
            
            # 根据元素类型创建不同的输入控件
            if elem_type == "text":
                self.create_text_input(elem_id, label_text, is_required)
            elif elem_type == "badge":
                self.create_badge_input(elem_id, label_text)
            elif elem_type == "image":
                self.create_image_input(elem_id, label_text)
    
    def create_text_input(self, elem_id, label_text, is_required):
        """创建文本输入框"""
        line_edit = QtWidgets.QLineEdit()
        
        # 设置占位符
        if is_required:
            line_edit.setPlaceholderText("必填")
        else:
            line_edit.setPlaceholderText("可选")
        
        # 特殊处理主标题
        if elem_id == "title_main":
            line_edit.setStyleSheet("font-size: 14px; padding: 8px;")
        
        self.form_layout.addRow(f"{label_text}:", line_edit)
        self.input_widgets[elem_id] = line_edit
    
    def create_badge_input(self, elem_id, label_text):
        """创建徽章输入框"""
        if elem_id == "episode_badge":
            # 集数使用数字输入
            spinbox = QtWidgets.QSpinBox()
            spinbox.setRange(1, 999)
            spinbox.setValue(1)
            spinbox.setSuffix(" 集")
            self.form_layout.addRow(f"{label_text}:", spinbox)
            self.input_widgets["episode"] = spinbox
        else:
            # 自定义徽章使用文本输入
            line_edit = QtWidgets.QLineEdit()
            line_edit.setPlaceholderText("徽章文本")
            self.form_layout.addRow(f"{label_text}:", line_edit)
            self.input_widgets[elem_id] = line_edit
    
    def create_image_input(self, elem_id, label_text):
        """创建图片选择输入"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 图片路径标签
        self.image_paths[elem_id] = ""
        path_label = QtWidgets.QLabel("(使用默认图片)")
        path_label.setStyleSheet("color: #666; font-style: italic;")
        path_label.setWordWrap(True)
        
        # 按钮容器
        btn_container = QtWidgets.QWidget()
        btn_layout = QtWidgets.QVBoxLayout(btn_container)
        btn_layout.setSpacing(5)
        
        # 选择图片按钮
        btn_select = QtWidgets.QPushButton("选择图片")
        btn_select.clicked.connect(lambda checked, eid=elem_id: self.select_image(eid))
        
        # 清除按钮
        btn_clear = QtWidgets.QPushButton("清除")
        btn_clear.clicked.connect(lambda checked, eid=elem_id: self.clear_image(eid))
        
        btn_layout.addWidget(btn_select)
        btn_layout.addWidget(btn_clear)
        
        layout.addWidget(path_label, 4)
        layout.addWidget(btn_container, 1)
        
        self.form_layout.addRow(f"{label_text}:", container)
        self.input_widgets[elem_id] = path_label
    
    def create_common_parameters(self):
        """创建通用参数"""
        # 添加分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.form_layout.addRow(line)
        
        # 通用参数标题
        common_label = QtWidgets.QLabel("通用参数")
        common_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.form_layout.addRow(common_label)
        
        # 输出文件选择
        output_layout = QtWidgets.QHBoxLayout()
        self.output_edit = QtWidgets.QLineEdit(
            os.path.join(BASE_DIR, "output", "cover_test.jpg")
        )
        output_btn = QtWidgets.QPushButton("浏览")
        output_btn.clicked.connect(self.select_output_file)
        
        output_layout.addWidget(self.output_edit, 4)
        output_layout.addWidget(output_btn, 1)
        self.form_layout.addRow("输出文件:", output_layout)
        
        # 随机种子
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(0)
        self.seed_spin.setSpecialValueText("随机")
        self.seed_spin.setSuffix(" (0=随机)")
        self.form_layout.addRow("随机种子:", self.seed_spin)
    
    def select_image(self, elem_id):
        """选择图片文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择图片", 
            os.path.join(BASE_DIR, "template"),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        
        if file_path:
            self.image_paths[elem_id] = file_path
            # 显示简化的路径
            display_path = os.path.basename(file_path)
            if len(file_path) > 40:
                display_path = "..." + display_path[-30:]
            self.input_widgets[elem_id].setText(display_path)
            self.input_widgets[elem_id].setStyleSheet("color: black; font-style: normal;")
    
    def clear_image(self, elem_id):
        """清除选择的图片"""
        self.image_paths[elem_id] = ""
        self.input_widgets[elem_id].setText("(使用默认图片)")
        self.input_widgets[elem_id].setStyleSheet("color: #666; font-style: italic;")
    
    def select_output_file(self):
        """选择输出文件"""
        default_path = self.output_edit.text()
        if not os.path.exists(os.path.dirname(default_path)):
            default_path = os.path.join(BASE_DIR, "output")
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存封面",
            default_path,
            "图片文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        
        if file_path:
            self.output_edit.setText(file_path)
    
    def on_generate(self):
        """生成封面"""
        params = {}
        
        # 收集所有输入参数
        for elem_id, widget in self.input_widgets.items():
            if isinstance(widget, QtWidgets.QLineEdit):
                text = widget.text().strip()
                if text:  # 只添加非空值
                    params[elem_id] = text
            elif isinstance(widget, QtWidgets.QSpinBox):
                if elem_id == "episode":
                    ep_value = int(widget.value())
                    params["episode"] = ep_value if ep_value > 0 else None
        
        # 添加图片路径参数
        for elem_id, img_path in self.image_paths.items():
            if img_path:
                params[elem_id] = img_path
        
        # 添加其他参数
        output_path = self.output_edit.text().strip()
        if output_path:
            params["output_path"] = output_path
        
        seed_value = int(self.seed_spin.value())
        if seed_value > 0:
            params["seed"] = seed_value
        
        # 检查必填字段
        if "title_main" in self.input_widgets:
            title_widget = self.input_widgets["title_main"]
            if isinstance(title_widget, QtWidgets.QLineEdit) and not title_widget.text().strip():
                QtWidgets.QMessageBox.warning(self, "提示", "主标题不能为空")
                return

        try:
            self.statusBar().showMessage("正在生成封面...")
            QtWidgets.QApplication.processEvents()  # 更新界面
            
            path = render_cover(params)
            
            # 显示成功消息
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("完成")
            msg_box.setText(f"封面已生成：\n{path}")
            
            # 添加打开按钮
            open_btn = msg_box.addButton("打开文件", QtWidgets.QMessageBox.ActionRole)
            msg_box.addButton("确定", QtWidgets.QMessageBox.AcceptRole)
            
            msg_box.exec_()
            
            if msg_box.clickedButton() == open_btn:
                # 打开文件
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    os.system(f'open "{path}"')
                else:
                    os.system(f'xdg-open "{path}"')
            
            self.statusBar().showMessage(f"封面已生成: {os.path.basename(path)}")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", str(e))
            self.statusBar().showMessage(f"生成失败: {e}")
    
    def on_refresh(self):
        """刷新配置"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认刷新",
            "刷新将重新加载配置文件。确定要继续吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.layout_cfg = load_json(os.path.join(BASE_DIR, "layout.json"))
                self.style_cfg = load_json(os.path.join(BASE_DIR, "style.json"))
                
                # 清空表单
                for i in reversed(range(self.form_layout.count())):
                    widget = self.form_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
                
                # 重新创建表单
                self.input_widgets.clear()
                self.image_paths.clear()
                self.custom_elements.clear()
                self.create_dynamic_inputs()
                self.create_common_parameters()
                
                self.statusBar().showMessage("配置已刷新")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "错误", f"刷新失败: {e}")
    
    def open_editor(self):
        """打开编辑器"""
        try:
            import subprocess
            # 修改为直接调用 editor_core.py
            editor_path = os.path.join(BASE_DIR, "editor_core.py")
            if os.path.exists(editor_path):
                if sys.platform == "win32":
                    subprocess.Popen(["python", editor_path])
                else:
                    subprocess.Popen(["python3", editor_path])
                self.statusBar().showMessage("已启动编辑器")
            else:
                QtWidgets.QMessageBox.warning(self, "警告", "未找到编辑器文件")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"启动编辑器失败: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建调色板
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(245, 245, 245))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(0, 0, 0))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    app.setPalette(palette)
    
    w = CoverGenerator()
    w.show()
    sys.exit(app.exec_())