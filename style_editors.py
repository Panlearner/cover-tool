import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QColorDialog, QFileDialog, QComboBox,
    QFormLayout, QGroupBox, QSlider, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


def create_image_style_editor(elem_id, style_cfg, on_changed_callback, base_dir=None):
    """创建图片元素的样式编辑器"""
    editor = QWidget()
    layout = QFormLayout(editor)

    # 确保style_cfg包含必要的键
    if "image_pattern" not in style_cfg:
        style_cfg["image_pattern"] = ""
    if "opacity" not in style_cfg:
        style_cfg["opacity"] = 1.0

    # 图片路径编辑器
    path_layout = QHBoxLayout()

    pattern_edit = QLineEdit()
    pattern_edit.setText(style_cfg["image_pattern"])
    pattern_edit.setPlaceholderText("图片路径（绝对路径或相对路径）")
    path_layout.addWidget(pattern_edit)

    # 选择图片按钮
    btn_select = QPushButton("选择图片")
    btn_select.setMaximumWidth(80)
    path_layout.addWidget(btn_select)

    # 清除按钮
    btn_clear = QPushButton("清除")
    btn_clear.setMaximumWidth(60)
    path_layout.addWidget(btn_clear)

    layout.addRow("图片路径:", path_layout)

    # 当前图片预览
    preview_label = QLabel("无图片")
    preview_label.setFixedSize(100, 60)
    preview_label.setStyleSheet("""
        QLabel {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            color: #999999;
            font-size: 10px;
        }
    """)
    preview_label.setAlignment(Qt.AlignCenter)

    def update_preview():
        """更新图片预览"""
        if style_cfg["image_pattern"] and os.path.exists(style_cfg["image_pattern"]):
            preview_label.setText("")
            preview_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #cccccc;
                    background-color: white;
                }
            """)
        else:
            preview_label.setText("无图片")
            preview_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    color: #999999;
                    font-size: 10px;
                }
            """)

    layout.addRow("预览:", preview_label)

    # 不透明度滑块
    opacity_slider = QSlider(Qt.Horizontal)
    opacity_slider.setRange(0, 100)
    opacity_slider.setValue(int(style_cfg["opacity"] * 100))
    opacity_slider.setMaximumWidth(200)

    opacity_label = QLabel(f"{style_cfg['opacity']:.2f}")

    opacity_layout = QHBoxLayout()
    opacity_layout.addWidget(opacity_slider)
    opacity_layout.addWidget(opacity_label)
    opacity_layout.addStretch()

    layout.addRow("不透明度:", opacity_layout)

    # 连接信号
    def on_pattern_changed(text):
        """图片路径改变"""
        # 直接保存路径，不转换为相对路径
        style_cfg["image_pattern"] = text
        on_changed_callback(elem_id, "image_pattern", text)
        update_preview()

    pattern_edit.textChanged.connect(on_pattern_changed)

    def on_select_image():
        """选择图片文件"""
        # 文件对话框
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("选择图片文件")
        file_dialog.setNameFilter(
            "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "PNG文件 (*.png);;"
            "JPEG文件 (*.jpg *.jpeg);;"
            "所有文件 (*.*)"
        )

        # 设置初始目录（如果有基本目录）
        if base_dir and os.path.exists(base_dir):
            file_dialog.setDirectory(base_dir)

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                pattern_edit.setText(file_path)

    btn_select.clicked.connect(on_select_image)

    def on_clear_image():
        """清除图片"""
        pattern_edit.setText("")

    btn_clear.clicked.connect(on_clear_image)

    def on_opacity_changed(value):
        """不透明度改变"""
        opacity = value / 100.0
        opacity_label.setText(f"{opacity:.2f}")
        style_cfg["opacity"] = opacity
        on_changed_callback(elem_id, "opacity", opacity)

    opacity_slider.valueChanged.connect(on_opacity_changed)

    # 初始更新预览
    update_preview()

    return editor


def create_text_style_editor(elem_id, style_cfg, on_changed_callback):
    """创建文本元素的样式编辑器"""
    editor = QWidget()
    layout = QFormLayout(editor)

    # 确保style_cfg包含必要的键
    defaults = {
        "font_family": "Arial",
        "font_size": 24,
        "font_color": "#000000",
        "align": "center",
        "bold": False,
        "italic": False
    }

    for key, default_val in defaults.items():
        if key not in style_cfg:
            style_cfg[key] = default_val

    # 字体家族
    font_combo = QComboBox()
    font_combo.addItems(["Arial", "Microsoft YaHei",
                        "SimHei", "Times New Roman", "Courier New"])
    font_combo.setCurrentText(style_cfg["font_family"])
    font_combo.currentTextChanged.connect(
        lambda text: on_changed_callback(elem_id, "font_family", text)
    )
    layout.addRow("字体:", font_combo)

    # 字体大小
    size_spin = QSpinBox()
    size_spin.setRange(1, 200)
    size_spin.setValue(style_cfg["font_size"])
    size_spin.valueChanged.connect(
        lambda value: on_changed_callback(elem_id, "font_size", value)
    )
    layout.addRow("字号:", size_spin)

    # 字体颜色
    color_layout = QHBoxLayout()
    color_btn = QPushButton()
    color_btn.setFixedSize(24, 24)
    color_btn.setStyleSheet(f"background-color: {style_cfg['font_color']};")

    color_label = QLabel(style_cfg["font_color"])

    def on_color_pick():
        color = QColorDialog.getColor(QColor(style_cfg["font_color"]))
        if color.isValid():
            hex_color = color.name()
            color_btn.setStyleSheet(f"background-color: {hex_color};")
            color_label.setText(hex_color)
            on_changed_callback(elem_id, "font_color", hex_color)

    color_btn.clicked.connect(on_color_pick)

    color_layout.addWidget(color_btn)
    color_layout.addWidget(color_label)
    color_layout.addStretch()

    layout.addRow("颜色:", color_layout)

    # 对齐方式
    align_combo = QComboBox()
    align_combo.addItems(["left", "center", "right"])
    align_combo.setCurrentText(style_cfg["align"])
    align_combo.currentTextChanged.connect(
        lambda text: on_changed_callback(elem_id, "align", text)
    )
    layout.addRow("对齐:", align_combo)

    # 粗体和斜体
    bold_check = QCheckBox("粗体")
    bold_check.setChecked(style_cfg["bold"])
    bold_check.stateChanged.connect(
        lambda state: on_changed_callback(elem_id, "bold", bool(state))
    )

    italic_check = QCheckBox("斜体")
    italic_check.setChecked(style_cfg["italic"])
    italic_check.stateChanged.connect(
        lambda state: on_changed_callback(elem_id, "italic", bool(state))
    )

    style_layout = QHBoxLayout()
    style_layout.addWidget(bold_check)
    style_layout.addWidget(italic_check)
    style_layout.addStretch()

    layout.addRow("样式:", style_layout)

    return editor


def create_badge_style_editor(elem_id, style_cfg, on_changed_callback):
    """创建徽章元素的样式编辑器"""
    editor = QWidget()
    layout = QFormLayout(editor)

    # 确保style_cfg包含必要的键
    defaults = {
        "badge_type": "rectangle",
        "bg_color": "#FF5722",
        "text_color": "#FFFFFF",
        "padding": 10,
        "radius": 5
    }

    for key, default_val in defaults.items():
        if key not in style_cfg:
            style_cfg[key] = default_val

    # 徽章类型
    type_combo = QComboBox()
    type_combo.addItems(["rectangle", "circle", "pill", "ribbon"])
    type_combo.setCurrentText(style_cfg["badge_type"])
    type_combo.currentTextChanged.connect(
        lambda text: on_changed_callback(elem_id, "badge_type", text)
    )
    layout.addRow("类型:", type_combo)

    # 背景颜色
    bg_color_layout = QHBoxLayout()
    bg_color_btn = QPushButton()
    bg_color_btn.setFixedSize(24, 24)
    bg_color_btn.setStyleSheet(f"background-color: {style_cfg['bg_color']};")

    bg_color_label = QLabel(style_cfg["bg_color"])

    def on_bg_color_pick():
        color = QColorDialog.getColor(QColor(style_cfg["bg_color"]))
        if color.isValid():
            hex_color = color.name()
            bg_color_btn.setStyleSheet(f"background-color: {hex_color};")
            bg_color_label.setText(hex_color)
            on_changed_callback(elem_id, "bg_color", hex_color)

    bg_color_btn.clicked.connect(on_bg_color_pick)

    bg_color_layout.addWidget(bg_color_btn)
    bg_color_layout.addWidget(bg_color_label)
    bg_color_layout.addStretch()

    layout.addRow("背景色:", bg_color_layout)

    # 文本颜色
    text_color_layout = QHBoxLayout()
    text_color_btn = QPushButton()
    text_color_btn.setFixedSize(24, 24)
    text_color_btn.setStyleSheet(
        f"background-color: {style_cfg['text_color']};")

    text_color_label = QLabel(style_cfg["text_color"])

    def on_text_color_pick():
        color = QColorDialog.getColor(QColor(style_cfg["text_color"]))
        if color.isValid():
            hex_color = color.name()
            text_color_btn.setStyleSheet(f"background-color: {hex_color};")
            text_color_label.setText(hex_color)
            on_changed_callback(elem_id, "text_color", hex_color)

    text_color_btn.clicked.connect(on_text_color_pick)

    text_color_layout.addWidget(text_color_btn)
    text_color_layout.addWidget(text_color_label)
    text_color_layout.addStretch()

    layout.addRow("文本色:", text_color_layout)

    # 内边距
    padding_spin = QSpinBox()
    padding_spin.setRange(0, 50)
    padding_spin.setValue(style_cfg["padding"])
    padding_spin.valueChanged.connect(
        lambda value: on_changed_callback(elem_id, "padding", value)
    )
    layout.addRow("内边距:", padding_spin)

    # 圆角半径
    radius_spin = QSpinBox()
    radius_spin.setRange(0, 50)
    radius_spin.setValue(style_cfg["radius"])
    radius_spin.valueChanged.connect(
        lambda value: on_changed_callback(elem_id, "radius", value)
    )
    layout.addRow("圆角:", radius_spin)

    return editor
