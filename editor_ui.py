"""
editor_ui.py - 编辑器UI布局与交互
"""
from PyQt5 import QtWidgets, QtCore, QtGui
import os
from canvas_widget import CanvasWidget
import style_editors


class EditorUI(QtWidgets.QWidget):
    sig_request_save = QtCore.pyqtSignal()
    sig_request_refresh = QtCore.pyqtSignal()
    sig_background_selected = QtCore.pyqtSignal(str)
    sig_add_element_request = QtCore.pyqtSignal(str, str)
    sig_delete_element_request = QtCore.pyqtSignal(str)
    sig_select_element = QtCore.pyqtSignal(str)
    sig_layout_changed = QtCore.pyqtSignal(str, str, object)
    sig_style_changed = QtCore.pyqtSignal(str, str, object)
    sig_canvas_geom_changed = QtCore.pyqtSignal(str, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.current_element_id = ""
        self.layout_cfg = None
        self.style_cfg = None
        self.bg_path = ""
        self.current_style_editor = None
        self.element_counter = {
            "text": 1,
            "image": 1,
            "badge": 1
        }

        self.init_ui()

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle("封面编辑器")

        # 主布局
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ========== 左侧面板 ==========
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_panel.setMinimumWidth(350)
        left_panel.setMaximumWidth(400)

        # 1. 元素列表
        elem_group = QtWidgets.QGroupBox("元素列表")
        elem_layout = QtWidgets.QVBoxLayout(elem_group)

        self.element_list = QtWidgets.QListWidget()
        self.element_list.itemSelectionChanged.connect(
            self.on_element_list_select)
        elem_layout.addWidget(self.element_list)

        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("添加")
        self.add_btn.clicked.connect(self.on_add_element)
        self.del_btn = QtWidgets.QPushButton("删除")
        self.del_btn.clicked.connect(self.on_delete_element)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        elem_layout.addLayout(btn_layout)

        left_layout.addWidget(elem_group)

        # 2. 布局属性
        layout_group = QtWidgets.QGroupBox("布局属性")
        layout_form = QtWidgets.QFormLayout(layout_group)

        self.x_input = QtWidgets.QSpinBox()
        self.x_input.setRange(-1000, 3000)
        self.y_input = QtWidgets.QSpinBox()
        self.y_input.setRange(-1000, 3000)
        self.w_input = QtWidgets.QSpinBox()
        self.w_input.setRange(1, 2000)
        self.h_input = QtWidgets.QSpinBox()
        self.h_input.setRange(1, 2000)

        self.x_input.valueChanged.connect(self.on_layout_change)
        self.y_input.valueChanged.connect(self.on_layout_change)
        self.w_input.valueChanged.connect(self.on_layout_change)
        self.h_input.valueChanged.connect(self.on_layout_change)

        layout_form.addRow("X:", self.x_input)
        layout_form.addRow("Y:", self.y_input)
        layout_form.addRow("宽:", self.w_input)
        layout_form.addRow("高:", self.h_input)

        left_layout.addWidget(layout_group)

        # 3. 样式面板（在左侧底部）
        style_group = QtWidgets.QGroupBox("样式属性")
        style_layout = QtWidgets.QVBoxLayout(style_group)

        self.style_container = QtWidgets.QWidget()
        self.style_container_layout = QtWidgets.QVBoxLayout(
            self.style_container)
        self.style_container_layout.setContentsMargins(2, 2, 2, 2)

        style_scroll = QtWidgets.QScrollArea()
        style_scroll.setWidget(self.style_container)
        style_scroll.setWidgetResizable(True)
        style_scroll.setMinimumHeight(300)
        style_layout.addWidget(style_scroll)

        left_layout.addWidget(style_group, 1)

        # 4. 底部按钮 (替换部分)
        bottom_layout = QtWidgets.QHBoxLayout()

        self.bg_btn = QtWidgets.QPushButton("背景")
        self.bg_btn.clicked.connect(self.on_select_background)
        bottom_layout.addWidget(self.bg_btn)

        self.image_btn = QtWidgets.QPushButton("选择图片")
        self.image_btn.clicked.connect(self.on_select_image_for_element)
        bottom_layout.addWidget(self.image_btn)

        self.save_btn = QtWidgets.QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        bottom_layout.addWidget(self.save_btn)

        left_layout.addLayout(bottom_layout)
        # (替换部分结束)

        # ========== 画布区域 ==========
        # 创建画布
        self.canvas = CanvasWidget()
        self.canvas.element_selected.connect(self.on_canvas_select)
        self.canvas.element_moved.connect(self.on_canvas_move)

        # 添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.canvas, 1)

        self.resize(1400, 900)

    def on_add_element(self):
        """添加元素 - 简化：直接选择类型，自动生成ID"""
        # 创建类型选择对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("添加新元素")
        dialog.setFixedSize(300, 200)

        layout = QtWidgets.QVBoxLayout(dialog)

        # 标题
        title_label = QtWidgets.QLabel("选择要添加的元素类型：")
        title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)

        # 类型选择按钮组
        button_group = QtWidgets.QButtonGroup(dialog)

        # 文本元素按钮
        text_btn = QtWidgets.QPushButton("📝 文本元素")
        text_btn.setCheckable(True)
        text_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
        """)
        button_group.addButton(text_btn, 0)
        layout.addWidget(text_btn)

        # 图片元素按钮
        image_btn = QtWidgets.QPushButton("🖼️ 图片元素")
        image_btn.setCheckable(True)
        image_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: white;
            }
        """)
        button_group.addButton(image_btn, 1)
        layout.addWidget(image_btn)

        # 徽章元素按钮
        badge_btn = QtWidgets.QPushButton("🏷️ 徽章元素")
        badge_btn.setCheckable(True)
        badge_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #FF9800;
                color: white;
            }
        """)
        button_group.addButton(badge_btn, 2)
        layout.addWidget(badge_btn)

        # 默认选中文本元素
        text_btn.setChecked(True)

        # 按钮
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        # 显示对话框
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # 获取选中的类型
            checked_btn = button_group.checkedButton()
            if checked_btn == text_btn:
                elem_type = "text"
                elem_id = f"text_{self.element_counter['text']}"
                self.element_counter["text"] += 1
            elif checked_btn == image_btn:
                elem_type = "image"
                elem_id = f"image_{self.element_counter['image']}"
                self.element_counter["image"] += 1
            else:  # badge_btn
                elem_type = "badge"
                elem_id = f"badge_{self.element_counter['badge']}"
                self.element_counter["badge"] += 1

            # 发送信号
            self.sig_add_element_request.emit(elem_type, elem_id)

    def on_delete_element(self):
        if not self.current_element_id:
            QtWidgets.QMessageBox.warning(self, "提示", "请先选中要删除的元素")
            return

        reply = QtWidgets.QMessageBox.question(
            self, "确认删除",
            f"确定要删除元素 '{self.current_element_id}' 吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.sig_delete_element_request.emit(self.current_element_id)

    def on_element_list_select(self):
        items = self.element_list.selectedItems()
        if items:
            elem_id = items[0].text()
            self.current_element_id = elem_id
            self.sig_select_element.emit(elem_id)
            self.update_layout_attr(elem_id)
            self.update_style_panel(elem_id)

    def on_canvas_select(self, elem_id):
        self.current_element_id = elem_id
        if elem_id:
            for i in range(self.element_list.count()):
                if self.element_list.item(i).text() == elem_id:
                    self.element_list.setCurrentRow(i)
                    break
            self.update_layout_attr(elem_id)
            self.update_style_panel(elem_id)

    def on_canvas_move(self, elem_id, x, y, w, h):
        self.current_element_id = elem_id
        self.x_input.setValue(x)
        self.y_input.setValue(y)
        self.w_input.setValue(w)
        self.h_input.setValue(h)
        self.sig_canvas_geom_changed.emit(elem_id, x, y, w, h)

    def on_layout_change(self):
        if not self.current_element_id:
            return
        self.sig_layout_changed.emit(
            self.current_element_id, "x", self.x_input.value())
        self.sig_layout_changed.emit(
            self.current_element_id, "y", self.y_input.value())
        self.sig_layout_changed.emit(
            self.current_element_id, "width", self.w_input.value())
        self.sig_layout_changed.emit(
            self.current_element_id, "height", self.h_input.value())

    def on_select_background(self):
        """选择背景图片"""
        # 默认打开 template 目录
        template_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "template")
        if not os.path.exists(template_dir):
            template_dir = ""

        bg_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择背景图片",
            template_dir,
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)")

        if bg_path:
            # 立即更新画布显示
            self.canvas.set_background(bg_path)
            # 发送信号保存配置
            self.sig_background_selected.emit(bg_path)

    def on_select_image_for_element(self):
        if not self.current_element_id:
            QtWidgets.QMessageBox.warning(self, "提示", "请先在左侧选中一个元素")
            return

        # 只允许图片元素选图片
        elem_type = None
        if self.layout_cfg:
            for elem in self.layout_cfg.get("elements", []):
                if elem.get("id") == self.current_element_id:
                    elem_type = elem.get("type", "text")
                    break

        if elem_type != "image":
            QtWidgets.QMessageBox.warning(self, "提示", "当前选中的不是图片元素")
            return

        template_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "template"
        )
        if not os.path.exists(template_dir):
            template_dir = ""

        img_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择图片文件",
            template_dir,
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if not img_path:
            return

        self.sig_style_changed.emit(
            self.current_element_id, "image_pattern", img_path)
        self.update_style_panel(self.current_element_id)

    def on_save(self):
        self.sig_request_save.emit()

    def update_layout_attr(self, elem_id):
        """更新布局属性显示"""
        if not self.layout_cfg:
            return

        for elem in self.layout_cfg.get("elements", []):
            if elem.get("id") == elem_id:
                self.x_input.setValue(elem.get("x", 0))
                self.y_input.setValue(elem.get("y", 0))
                self.w_input.setValue(elem.get("width", 100))
                self.h_input.setValue(elem.get("height", 50))
                break

    def update_style_panel(self, elem_id):
        """更新样式面板"""
        # 清空现有样式面板
        if self.current_style_editor:
            self.current_style_editor.deleteLater()
            self.current_style_editor = None

        # 获取元素类型
        elem_type = ""
        for elem in self.layout_cfg.get("elements", []):
            if elem.get("id") == elem_id:
                elem_type = elem.get("type", "text")
                break

        # 获取样式配置
        elem_style = self.style_cfg.get("elements", {}).get(elem_id, {})

        # 创建对应的样式编辑器
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if elem_type == "image":
            self.current_style_editor = style_editors.create_image_style_editor(
                elem_id, elem_style, self.sig_style_changed.emit, base_dir)
        elif elem_type == "badge":
            self.current_style_editor = style_editors.create_badge_style_editor(
                elem_id, elem_style, self.sig_style_changed.emit)
        else:
            self.current_style_editor = style_editors.create_text_style_editor(
                elem_id, elem_style, self.sig_style_changed.emit)

        if self.current_style_editor:
            self.style_container_layout.addWidget(self.current_style_editor)

    def set_state(self, layout_cfg, style_cfg, bg_path):
        """设置编辑器状态"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg
        self.bg_path = bg_path

        # 给没有 content 的元素补一个默认值，方便画面预览
        for elem in self.layout_cfg.get("elements", []):
            if not elem.get("content"):
                elem_type = elem.get("type", "text")
                elem_id = elem.get("id", "")
                if elem_type in ("text", "badge"):
                    elem["content"] = elem_id
                elif elem_type == "image":
                    style = self.style_cfg.get("elements", {}).get(elem_id, {})
                    elem["content"] = style.get("image_pattern", "")

        # 更新元素列表
        self.element_list.clear()
        for elem in self.layout_cfg.get("elements", []):
            self.element_list.addItem(elem.get("id", ""))

        # 更新画布
        self.canvas.set_config(self.layout_cfg, self.style_cfg, bg_path)

        # 清除选中状态
        self.current_element_id = ""
        self.x_input.setValue(0)
        self.y_input.setValue(0)
        self.w_input.setValue(100)
        self.h_input.setValue(50)

        # 清空样式面板
        if self.current_style_editor:
            self.current_style_editor.deleteLater()
            self.current_style_editor = None

    def set_background(self, bg_path):
        """设置背景图片"""
        if bg_path:
            self.bg_path = bg_path
            self.canvas.set_background(bg_path)

    def refresh_all(self, layout_cfg, style_cfg, selected_elem_id=None):
        """刷新所有显示"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg

        # 更新元素列表
        self.element_list.clear()
        for elem in layout_cfg.get("elements", []):
            self.element_list.addItem(elem.get("id", ""))

        # 更新画布
        self.canvas.set_config(layout_cfg, style_cfg, self.bg_path)

        # 选中指定元素
        if selected_elem_id:
            for i in range(self.element_list.count()):
                if self.element_list.item(i).text() == selected_elem_id:
                    self.element_list.setCurrentRow(i)
                    self.current_element_id = selected_elem_id
                    self.update_layout_attr(selected_elem_id)
                    self.update_style_panel(selected_elem_id)
                    break

        # 如果没有指定新元素，但当前有元素选中，仍需更新样式面板
        elif self.current_element_id:
            self.update_style_panel(self.current_element_id)

    def update_selection(self, elem_info):
        """更新选中元素信息"""
        if elem_info:
            elem_id = elem_info.get("id", "")
            if elem_id:
                self.current_element_id = elem_id
                self.update_layout_attr(elem_id)
                self.update_style_panel(elem_id)

    def show_status(self, message):
        """显示状态消息"""
        if any(keyword in message for keyword in ["成功", "失败", "错误", "已保存", "已加载", "已删除", "已添加"]):
            print(f"[状态] {message}")
