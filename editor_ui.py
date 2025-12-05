"""
editor_ui.py - 封面编辑器用户界面
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QColorDialog, QFileDialog, QComboBox,
    QFormLayout, QGroupBox, QMessageBox, QSizePolicy, QToolBar, QAction,
    QListWidget, QTabWidget, QTextEdit, QSplitter, QDockWidget, QMainWindow,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon


class EditorUI(QWidget):
    # 信号定义
    sig_request_save = pyqtSignal()
    sig_request_preview = pyqtSignal()
    sig_request_refresh = pyqtSignal()
    sig_background_selected = pyqtSignal(str)
    sig_add_element_request = pyqtSignal(str, str)
    sig_delete_element_request = pyqtSignal(str)
    sig_select_element = pyqtSignal(str)
    sig_layout_changed = pyqtSignal(str, str, object)
    sig_style_changed = pyqtSignal(str, str, object)
    sig_canvas_geom_changed = pyqtSignal(str, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.core = None
        self.layout_cfg = None
        self.style_cfg = None
        self.current_bg_path = ""
        self.current_element_id = None

        # 设置窗口
        self.setWindowTitle("封面编辑器")
        self.resize(1600, 1000)

        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # === 左侧面板 ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)

        # 元素列表
        left_layout.addWidget(QLabel("元素列表"))
        self.element_list = QListWidget()
        self.element_list.itemSelectionChanged.connect(
            self.on_element_selected)
        self.element_list.setMinimumWidth(200)
        self.element_list.setMaximumWidth(250)
        left_layout.addWidget(self.element_list)

        # 添加/删除按钮
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.on_add_element)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.on_delete_element)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)

        # 布局属性组
        layout_group = QGroupBox("布局属性")
        layout_form = QFormLayout()

        self.x_spin = QSpinBox()
        self.x_spin.setRange(-1000, 3000)
        self.x_spin.valueChanged.connect(
            lambda: self.on_layout_field_changed("x"))
        layout_form.addRow("X:", self.x_spin)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(-1000, 3000)
        self.y_spin.valueChanged.connect(
            lambda: self.on_layout_field_changed("y"))
        layout_form.addRow("Y:", self.y_spin)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(0, 3000)
        self.width_spin.valueChanged.connect(
            lambda: self.on_layout_field_changed("width"))
        layout_form.addRow("宽度:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(0, 3000)
        self.height_spin.valueChanged.connect(
            lambda: self.on_layout_field_changed("height"))
        layout_form.addRow("高度:", self.height_spin)

        layout_group.setLayout(layout_form)
        left_layout.addWidget(layout_group)

        # 背景选择按钮
        self.bg_btn = QPushButton("选择背景")
        self.bg_btn.clicked.connect(self.select_background)
        left_layout.addWidget(self.bg_btn)

        # 保存按钮
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.on_save_requested)
        left_layout.addWidget(self.save_btn)

        left_layout.addStretch()

        # 设置左侧面板宽度
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(300)
        main_layout.addWidget(left_panel, 0)

        # === 中间画布区域 ===
        from canvas_widget import CanvasWidget
        self.canvas = CanvasWidget()

        # 修改：设置画布固定尺寸为1920x1080
        self.canvas.setFixedSize(1920, 1080)

        # 将画布放入滚动区域以适应窗口
        canvas_scroll = QScrollArea()
        canvas_scroll.setWidget(self.canvas)
        canvas_scroll.setWidgetResizable(False)  # 允许滚动
        canvas_scroll.setMinimumSize(1920, 1080)  # 滚动区域最小尺寸

        # 连接信号
        self.canvas.element_selected.connect(self.on_canvas_element_selected)
        self.canvas.element_moved.connect(self.on_canvas_element_moved)

        # 创建画布容器
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(canvas_scroll)

        # 给画布分配最多空间
        main_layout.addWidget(canvas_container, 1)

        # === 右侧面板 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(5)

        # 样式属性
        right_layout.addWidget(QLabel("样式属性"))
        self.style_container = QWidget()
        self.style_layout = QVBoxLayout(self.style_container)
        self.style_layout.setContentsMargins(5, 5, 5, 5)

        # 添加样式容器到滚动区域
        style_scroll = QScrollArea()
        style_scroll.setWidget(self.style_container)
        style_scroll.setWidgetResizable(True)
        style_scroll.setMinimumWidth(350)
        style_scroll.setMaximumWidth(400)

        right_layout.addWidget(style_scroll)

        # 状态标签
        self.status_label = QLabel("就绪")
        right_layout.addWidget(self.status_label)

        right_layout.addStretch()

        # 设置右侧面板宽度
        right_panel.setMinimumWidth(350)
        right_panel.setMaximumWidth(400)
        main_layout.addWidget(right_panel, 0)

        # 设置主布局
        self.setLayout(main_layout)

    # === 修复缺失的方法 ===
    def on_element_selected(self):
        """处理元素列表中的选择变化"""
        selected_items = self.element_list.selectedItems()
        if selected_items:
            elem_id = selected_items[0].text()
            self.sig_select_element.emit(elem_id)

    def on_layout_field_changed(self, field):
        """处理布局字段变化"""
        if not self.current_element_id:
            return

        value = 0
        if field == "x":
            value = self.x_spin.value()
        elif field == "y":
            value = self.y_spin.value()
        elif field == "width":
            value = self.width_spin.value()
        elif field == "height":
            value = self.height_spin.value()
        else:
            return

        self.sig_layout_changed.emit(self.current_element_id, field, value)

    def on_canvas_element_selected(self, elem_id):
        """处理画布中元素被选中"""
        self.sig_select_element.emit(elem_id)

    def on_canvas_element_moved(self, elem_id, x, y, width, height):
        """处理画布中元素移动/调整大小"""
        self.sig_canvas_geom_changed.emit(elem_id, x, y, width, height)

    # === 现有方法 ===
    def on_save_requested(self):
        """保存按钮点击"""
        self.sig_request_save.emit()
        self.status_label.setText("正在保存...")

    def set_state(self, layout_cfg, style_cfg, bg_path):
        """设置UI状态"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg
        self.current_bg_path = bg_path

        # 刷新元素列表
        self.refresh_element_list()

        # 更新画布
        if self.canvas:
            self.canvas.set_config(layout_cfg, style_cfg, bg_path)

        self.status_label.setText("就绪")

    def refresh_element_list(self):
        """刷新元素列表"""
        self.element_list.clear()
        if self.layout_cfg and "elements" in self.layout_cfg:
            for elem in self.layout_cfg["elements"]:
                elem_id = elem.get("id", "")
                elem_type = elem.get("type", "text")
                self.element_list.addItem(f"{elem_id} ({elem_type})")

    def find_element_by_id(self, elem_id):
        """根据ID查找元素"""
        if not self.layout_cfg or "elements" not in self.layout_cfg:
            return None
        for elem in self.layout_cfg["elements"]:
            if elem["id"] == elem_id:
                return elem
        return None

    def update_style_tab(self, elem_id):
        """更新样式面板"""
        # 清空样式面板
        while self.style_layout.count():
            child = self.style_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not elem_id:
            return

        elem = self.find_element_by_id(elem_id)
        if not elem:
            return

        elem_type = elem.get("type", "text")

        # 确保样式配置存在
        if "elements" not in self.style_cfg:
            self.style_cfg["elements"] = {}

        if elem_id not in self.style_cfg["elements"]:
            self.style_cfg["elements"][elem_id] = {}

        # 导入样式编辑器
        try:
            from style_editors import create_text_style_editor, create_image_style_editor, create_badge_style_editor

            # 创建样式编辑器
            if elem_type == "text":
                editor = create_text_style_editor(
                    elem_id,
                    self.style_cfg["elements"][elem_id],
                    self.on_style_changed
                )
            elif elem_type == "image":
                editor = create_image_style_editor(
                    elem_id,
                    self.style_cfg["elements"][elem_id],
                    self.on_style_changed,
                    os.path.dirname(os.path.abspath(__file__))
                )
            elif elem_type == "badge":
                editor = create_badge_style_editor(
                    elem_id,
                    self.style_cfg["elements"][elem_id],
                    self.on_style_changed
                )
            else:
                editor = create_text_style_editor(
                    elem_id,
                    self.style_cfg["elements"][elem_id],
                    self.on_style_changed
                )

            self.style_layout.addWidget(editor)

        except ImportError as e:
            error_label = QLabel(f"无法加载样式编辑器: {e}")
            self.style_layout.addWidget(error_label)

    def on_style_changed(self, elem_id, key, value):
        """样式改变"""
        self.sig_style_changed.emit(elem_id, key, value)
        self.status_label.setText(f"更新: {elem_id}.{key}")

    def update_selection(self, elem):
        """更新选中状态"""
        if not elem or (isinstance(elem, dict) and not elem):
            # 清空表单
            self.x_spin.setValue(0)
            self.y_spin.setValue(0)
            self.width_spin.setValue(100)
            self.height_spin.setValue(50)

            # 清空样式面板
            while self.style_layout.count():
                child = self.style_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # 清空画布选中
            if self.canvas:
                self.canvas.set_selected_element(None)

            self.current_element_id = None
        else:
            # 更新当前元素ID
            self.current_element_id = elem.get("id", "")

            # 更新表单
            self.x_spin.setValue(elem.get("x", 0))
            self.y_spin.setValue(elem.get("y", 0))
            self.width_spin.setValue(elem.get("width", 100))
            self.height_spin.setValue(elem.get("height", 50))

            # 更新样式面板
            self.update_style_tab(self.current_element_id)

            # 更新画布选中
            if self.canvas:
                self.canvas.set_selected_element(self.current_element_id)

            # 在列表中选择对应项
            for i in range(self.element_list.count()):
                item = self.element_list.item(i)
                if self.current_element_id in item.text():
                    self.element_list.setCurrentItem(item)
                    break

    def refresh_all(self, layout_cfg=None, style_cfg=None, highlight_elem=None):
        """刷新所有界面"""
        if layout_cfg:
            self.layout_cfg = layout_cfg
        if style_cfg:
            self.style_cfg = style_cfg

        self.refresh_element_list()

        if self.canvas:
            self.canvas.set_config(
                self.layout_cfg, self.style_cfg, self.current_bg_path)

        # 如果有需要高亮的元素
        if highlight_elem:
            for i in range(self.element_list.count()):
                item = self.element_list.item(i)
                if highlight_elem in item.text():
                    self.element_list.setCurrentItem(item)
                    break

    def show_status(self, message):
        """显示状态消息"""
        self.status_label.setText(message)

    def set_background(self, bg_path):
        """设置背景"""
        self.current_bg_path = bg_path
        if self.canvas:
            self.canvas.set_background(bg_path)

    def select_background(self):
        """选择背景图片"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "选择背景图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if file_path:
            self.sig_background_selected.emit(file_path)

    def on_add_element(self):
        """添加元素"""
        # 简化：这里直接添加一个文本元素
        # 实际中应该有对话框让用户选择元素类型
        from dialogs import AddElementDialog
        dialog = AddElementDialog(self)
        if dialog.exec_():
            elem_type, elem_id = dialog.get_element_info()
            if elem_id and elem_type:
                self.sig_add_element_request.emit(elem_type, elem_id)

    def on_delete_element(self):
        """删除当前选中元素"""
        if not self.current_element_id:
            QMessageBox.warning(self, "警告", "请先选择一个元素")
            return

        reply = QMessageBox.question(
            self, "确认", f"确定要删除元素 '{self.current_element_id}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.sig_delete_element_request.emit(self.current_element_id)

    # 其他方法保持原样...
