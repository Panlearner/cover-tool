"""
canvas_widget.py - 画布组件
"""
import os
from PyQt5 import QtWidgets, QtCore, QtGui


class CanvasWidget(QtWidgets.QWidget):
    element_selected = QtCore.pyqtSignal(str)
    element_moved = QtCore.pyqtSignal(str, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.bg_path = ""
        self.bg_image = None
        self.dragging = False
        self.drag_element = None
        self.drag_offset = (0, 0)
        self.selected_elem = None
        self.layout_cfg = None
        self.style_cfg = None

        # 图片缓存：避免重复加载
        self.image_cache = {}

        # 固定画布大小为1920x1080
        self.setFixedSize(1920, 1080)
        self.setStyleSheet("background-color: #f0f0f0;")

    def set_config(self, layout_cfg, style_cfg, bg_path):
        """设置画布配置"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg
        # set_config 应该只加载配置，设置背景应调用 set_background
        # self.bg_path = bg_path
        self.image_cache.clear()  # 清空缓存

        if bg_path and os.path.exists(bg_path):
            self.set_background(bg_path)
            # self.bg_image = QtGui.QImage(bg_path)
            # if self.bg_image.isNull():
            #     self.bg_image = None

        self.update()

    def set_background(self, bg_path):
        """设置背景图片 - 修复版"""
        print(f"[画布] 设置背景: {bg_path}")

        if bg_path and os.path.exists(bg_path):
            try:
                self.bg_image = QtGui.QImage(bg_path)
                if self.bg_image.isNull():
                    print(f"[画布] 图片加载失败: {bg_path}")
                    self.bg_image = None
                else:
                    print(
                        f"[画布] 图片加载成功: {self.bg_image.width()}x{self.bg_image.height()}")
                    self.bg_path = bg_path
            except Exception as e:
                print(f"[画布] 加载图片出错: {e}")
                self.bg_image = None
        else:
            print(f"[画布] 背景路径无效: {bg_path}")
            self.bg_image = None

        # 强制重绘画布
        self.update()

    def paintEvent(self, event):
        """重写绘图事件"""
        painter = QtGui.QPainter(self)

        # 1. 绘制背景图片
        # 背景：等比缩放，只缩不放，居中 (新逻辑)
        if self.bg_image and not self.bg_image.isNull():
            cw, ch = self.width(), self.height()
            iw, ih = self.bg_image.width(), self.bg_image.height()

            if iw > 0 and ih > 0:
                # 计算缩放比例，最大不超过 1.0 (只缩不放)
                scale_w = float(cw) / iw
                scale_h = float(ch) / ih
                scale = min(scale_w, scale_h)
                scale = min(scale, 1.0)  # 关键：确保不放大

                draw_w = int(iw * scale)
                draw_h = int(ih * scale)
                x = (cw - draw_w) // 2
                y = (ch - draw_h) // 2

                # 按计算出的尺寸进行缩放
                scaled_bg = self.bg_image.scaled(
                    draw_w, draw_h,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                painter.drawImage(x, y, scaled_bg)

        # 2. 绘制所有元素
        if self.layout_cfg and self.style_cfg:
            elements = self.layout_cfg.get("elements", [])
            # 按 z_index 排序
            elements.sort(key=lambda x: x.get("z_index", 0))

            for elem in elements:
                self.draw_element(painter, elem)

        # 3. 绘制选中边框
        if self.selected_elem:
            self.draw_selection_border(painter, self.selected_elem)

    def get_element_rect(self, elem):
        """获取元素的矩形区域"""
        return QtCore.QRect(
            elem.get("x", 0),
            elem.get("y", 0),
            elem.get("width", 100),
            elem.get("height", 50)
        )

    def draw_element(self, painter, elem):
        """绘制单个元素"""
        elem_id = elem.get("id")
        elem_type = elem.get("type", "text")
        rect = self.get_element_rect(elem)
        style = self.style_cfg.get("elements", {}).get(elem_id, {})
        content = elem.get("content", "")

        painter.save()

        if elem_type == "text":
            self._draw_text(painter, rect, content, style)
        elif elem_type == "image":
            self._draw_image(painter, rect, content, style)
        elif elem_type == "badge":
            self._draw_badge(painter, rect, content, style)

        painter.restore()

    def _draw_text(self, painter, rect, content, style):
        """绘制文本元素"""
        # 文本样式
        font = QtGui.QFont(
            style.get("font_family", "SimHei"),
            style.get("font_size", 16)
        )
        # 文本颜色
        color = QtGui.QColor(style.get("text_color", "#000000"))

        painter.setFont(font)
        painter.setPen(QtGui.QPen(color))

        # 文本对齐
        align_str = style.get("align", "left")
        alignment = QtCore.Qt.AlignLeft
        if align_str == "center":
            alignment = QtCore.Qt.AlignCenter
        elif align_str == "right":
            alignment = QtCore.Qt.AlignRight

        # 垂直居中
        alignment |= QtCore.Qt.AlignVCenter

        painter.drawText(rect, alignment, content)

    def _draw_image(self, painter, rect, content, style):
        """绘制图片元素"""
        # 获取图片路径
        image_path = content
        if not image_path:
            return

        # 检查缓存
        if image_path not in self.image_cache:
            if not os.path.exists(image_path):
                # 尝试查找相对路径
                base_dir = os.path.dirname(os.path.abspath(__file__))
                potential_path = os.path.join(base_dir, image_path)
                if os.path.exists(potential_path):
                    image_path = potential_path
                else:
                    # 静默忽略缺失图片，避免终端刷屏
                    return

            # 加载图片并放入缓存
            image = QtGui.QImage(image_path)
            if image.isNull():
                print(f"[画布] 图片加载失败: {image_path}")
                return
            self.image_cache[image_path] = image

        image = self.image_cache[image_path]

        # 设置不透明度
        opacity = style.get("opacity", 1.0)
        painter.setOpacity(opacity)

        # 缩放图片并绘制
        scaled_image = image.scaled(
            rect.size(),
            QtCore.Qt.KeepAspectRatio,  # 保持比例
            QtCore.Qt.SmoothTransformation
        )

        # 计算居中绘制的偏移量
        x_offset = rect.x() + (rect.width() - scaled_image.width()) // 2
        y_offset = rect.y() + (rect.height() - scaled_image.height()) // 2

        painter.drawImage(x_offset, y_offset, scaled_image)

        # 恢复不透明度
        painter.setOpacity(1.0)

    def _draw_badge(self, painter, rect, content, style):
        """绘制徽章元素"""
        # 背景
        bg_color = QtGui.QColor(style.get("bg_color", "#3498db"))
        border_radius = style.get("border_radius", 5)
        padding = style.get("padding", 5)

        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, border_radius, border_radius)

        # 文本
        font = QtGui.QFont(
            style.get("font_family", "SimHei"),
            style.get("font_size", 12)
        )
        text_color = QtGui.QColor(style.get("text_color", "#ffffff"))

        painter.setFont(font)
        painter.setPen(QtGui.QPen(text_color))

        # 绘制文本，考虑内边距
        text_rect = QtCore.QRect(
            rect.x() + padding,
            rect.y() + padding,
            rect.width() - 2 * padding,
            rect.height() - 2 * padding
        )

        painter.drawText(text_rect, QtCore.Qt.AlignCenter |
                         QtCore.Qt.AlignVCenter, content)

    def draw_selection_border(self, painter, elem):
        """绘制选中元素的边框和控制点"""
        rect = self.get_element_rect(elem)

        # 绘制虚线边框
        pen = QtGui.QPen(QtCore.Qt.blue, 2)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(rect)

        # 绘制四个角的控制点（用于调整大小，但目前只支持移动）
        handle_size = 10
        painter.setPen(QtGui.QPen(QtCore.Qt.darkBlue, 1))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.white))

        # 左上角
        painter.drawRect(rect.topLeft().x() - handle_size // 2,
                         rect.topLeft().y() - handle_size // 2,
                         handle_size, handle_size)
        # 右上角
        painter.drawRect(rect.topRight().x() - handle_size // 2,
                         rect.topRight().y() - handle_size // 2,
                         handle_size, handle_size)
        # 左下角
        painter.drawRect(rect.bottomLeft().x() - handle_size // 2,
                         rect.bottomLeft().y() - handle_size // 2,
                         handle_size, handle_size)
        # 右下角
        painter.drawRect(rect.bottomRight().x() - handle_size // 2,
                         rect.bottomRight().y() - handle_size // 2,
                         handle_size, handle_size)

    def hit_test(self, pos):
        """检测哪个元素被点击了，返回元素ID"""
        if not self.layout_cfg:
            return None

        elements = self.layout_cfg.get("elements", [])
        # 反向遍历，确保z_index最高的元素优先被选中
        for elem in reversed(elements):
            rect = self.get_element_rect(elem)
            if rect.contains(pos):
                return elem.get("id")
        return None

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()
            elem_id = self.hit_test(pos)

            if elem_id:
                # 选中元素
                self.dragging = True
                self.drag_element = elem_id

                # 记录选中状态
                self.selected_elem = next((elem for elem in self.layout_cfg["elements"]
                                           if elem["id"] == elem_id), None)

                # 发出选中信号
                self.element_selected.emit(elem_id)

                # 计算拖动偏移量
                elem = self.selected_elem
                self.drag_offset = (pos.x() - elem.get("x", 0),
                                    pos.y() - elem.get("y", 0))
                self.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))
                self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and self.drag_element and self.layout_cfg:
            pos = event.pos()

            for elem in self.layout_cfg["elements"]:
                if elem.get("id") == self.drag_element:
                    new_x = pos.x() - self.drag_offset[0]
                    new_y = pos.y() - self.drag_offset[1]

                    # 限制在画布范围内
                    new_x = max(0, min(new_x, 1920 - elem.get("width", 100)))
                    new_y = max(0, min(new_y, 1080 - elem.get("height", 50)))

                    elem["x"] = new_x
                    elem["y"] = new_y

                    self.element_moved.emit(self.drag_element, new_x, new_y,
                                            elem.get("width", 100), elem.get("height", 50))

                    self.update()
                    break

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            self.drag_element = None
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            self.update()

    def update_element(self, elem_id, layout_cfg, style_cfg):
        """根据配置更新单个元素"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg

        # 刷新选中的元素信息
        if self.selected_elem and self.selected_elem.get("id") == elem_id:
            self.selected_elem = next((elem for elem in self.layout_cfg["elements"]
                                       if elem["id"] == elem_id), None)

        # 清空图片缓存，如果样式变化涉及图片内容
        elem_type = next((elem.get("type") for elem in self.layout_cfg["elements"]
                          if elem.get("id") == elem_id and "type" in elem), None)
        if elem_type == "image":
            # 这是一个简单的清除，更精细的做法是检查 content 或 image_pattern 是否变化
            self.image_cache.clear()

        self.update()
