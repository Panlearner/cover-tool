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
        self.scale_factor = 1.0
        self.dragging = False
        self.drag_element = None
        self.drag_offset = (0, 0)
        self.drag_resize = None
        self.selected_elem = None
        self.layout_cfg = None
        self.style_cfg = None
        self.canvas_rect = None

        # 设置画布最小尺寸为1920x1080，但可以更大
        self.setMinimumSize(1920, 1080)

    def set_config(self, layout_cfg, style_cfg, bg_path):
        """设置画布配置"""
        self.layout_cfg = layout_cfg
        self.style_cfg = style_cfg

        if bg_path and os.path.exists(bg_path):
            self.bg_path = bg_path
            self.bg_image = QtGui.QImage(bg_path)
            if self.bg_image.isNull():
                self.bg_image = None
                print(f"无法加载背景图片: {bg_path}")
            else:
                print(f"背景图片已加载: {bg_path}")
                img_width = self.bg_image.width()
                img_height = self.bg_image.height()
                print(f"图片尺寸: {img_width}x{img_height}")

                # 调整画布大小为图片尺寸（但至少1920x1080）
                new_width = max(img_width, 1920)
                new_height = max(img_height, 1080)
                self.setFixedSize(new_width, new_height)
                print(f"画布调整为: {new_width}x{new_height}")

        self.update()

    def set_background(self, bg_path):
        """设置背景图片"""
        if bg_path and os.path.exists(bg_path):
            self.bg_path = bg_path
            self.bg_image = QtGui.QImage(bg_path)
            if self.bg_image.isNull():
                self.bg_image = None
                print(f"无法加载背景图片: {bg_path}")
            else:
                print(f"背景图片已更换: {bg_path}")
                img_width = self.bg_image.width()
                img_height = self.bg_image.height()
                print(f"图片尺寸: {img_width}x{img_height}")

                # 调整画布大小为图片尺寸（但至少1920x1080）
                new_width = max(img_width, 1920)
                new_height = max(img_height, 1080)
                self.setFixedSize(new_width, new_height)
                print(f"画布调整为: {new_width}x{new_height}")

            self.update()

    def set_selected_element(self, elem_id):
        """设置选中的元素"""
        self.selected_elem = elem_id
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 1. 绘制背景色
        painter.fillRect(self.rect(), QtGui.QColor(240, 240, 240))

        # 2. 绘制背景图片（如果有）
        if self.bg_image and not self.bg_image.isNull():
            img_width = self.bg_image.width()
            img_height = self.bg_image.height()
            canvas_width = self.width()
            canvas_height = self.height()

            # 图片从(0,0)开始绘制，保持原始尺寸，不拉伸
            painter.drawImage(0, 0, self.bg_image)

            # 绘制画布边界线
            painter.setPen(QtGui.QPen(QtGui.QColor(
                150, 150, 150), 2, QtCore.Qt.DashLine))
            painter.drawRect(0, 0, canvas_width - 1, canvas_height - 1)

        # 3. 绘制网格（辅助线）- 只在1920x1080基本区域内绘制
        grid_size = 20
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200, 100), 1))

        # 只绘制1920x1080基本区域的网格
        base_width = min(self.width(), 1920)
        base_height = min(self.height(), 1080)

        for x in range(0, base_width, grid_size):
            painter.drawLine(x, 0, x, base_height)
        for y in range(0, base_height, grid_size):
            painter.drawLine(0, y, base_width, y)

        # 4. 绘制中心参考线（1920x1080区域）
        center_x = min(self.width() // 2, 1920 // 2)
        center_y = min(self.height() // 2, 1080 // 2)
        painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150, 150), 2))
        painter.drawLine(center_x, 0, center_x, base_height)
        painter.drawLine(0, center_y, base_width, center_y)

        # 5. 绘制安全区域框（油管缩略图常用尺寸）- 居中于1920x1080区域
        thumb_width, thumb_height = 1280, 720
        thumb_x = (base_width - thumb_width) // 2
        thumb_y = (base_height - thumb_height) // 2
        painter.setPen(QtGui.QPen(QtGui.QColor(
            255, 100, 100, 150), 3, QtCore.Qt.DashLine))
        painter.drawRect(thumb_x, thumb_y, thumb_width, thumb_height)

        # 6. 绘制元素
        if self.layout_cfg and "elements" in self.layout_cfg:
            for elem in self.layout_cfg["elements"]:
                self.draw_element(painter, elem)

    def draw_element(self, painter, elem):
        """绘制单个元素"""
        elem_id = elem.get("id", "")
        elem_type = elem.get("type", "text")
        x = elem.get("x", 0)
        y = elem.get("y", 0)
        width = elem.get("width", 100)
        height = elem.get("height", 50)
        print(f"📐 绘制元素: {elem_id} 在({x},{y}) 大小({width}x{height})")

        # 获取样式
        style = {}
        if self.style_cfg and "elements" in self.style_cfg and elem_id in self.style_cfg["elements"]:
            style = self.style_cfg["elements"][elem_id]

        # 检查元素是否在画布可见区域内
        canvas_width = self.width()
        canvas_height = self.height()

        # 绘制矩形框
        if elem_id == self.selected_elem:
            painter.setPen(QtGui.QPen(QtCore.Qt.blue, 2))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 255, 30)))
        else:
            painter.setPen(QtGui.QPen(
                QtCore.Qt.darkGray, 1, QtCore.Qt.DashLine))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 200, 200, 50)))

        painter.drawRect(x, y, width, height)

        # 绘制元素内容
        if elem_type == "text":
            text = style.get("text", "文本")
            font_size = style.get("font_size", 12)
            font_color = style.get("font_color", "#000000")

            painter.setPen(QtGui.QColor(font_color))
            font = painter.font()
            font.setPointSize(font_size)
            painter.setFont(font)
            painter.drawText(x + 5, y + 20, text)

        elif elem_type == "image":
            # 绘制图片占位符
            painter.setPen(QtCore.Qt.darkGray)
            painter.drawText(x + 10, y + 25, "图片")

        elif elem_type == "badge":
            bg_color = style.get("bg_color", "#FF0000")
            text = style.get("text", "徽章")

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(bg_color))
            painter.drawRect(x, y, width, height)

            painter.setPen(QtCore.Qt.white)
            painter.drawText(x + 5, y + 20, text)

    def find_element_at_pos(self, pos):
        """查找指定位置的元素"""
        if not self.layout_cfg or "elements" not in self.layout_cfg:
            return None

        # 从后往前查找，这样后添加的元素在上面
        for elem in reversed(self.layout_cfg["elements"]):
            x = elem.get("x", 0)
            y = elem.get("y", 0)
            width = elem.get("width", 100)
            height = elem.get("height", 50)

            rect = QtCore.QRect(x, y, width, height)
            if rect.contains(pos):
                return elem

        return None

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()

            # 查找点击的元素
            elem = self.find_element_at_pos(pos)
            if elem:
                elem_id = elem.get("id", "")
                self.selected_elem = elem_id
                self.element_selected.emit(elem_id)

                # 开始拖动
                self.dragging = True
                self.drag_element = elem_id
                self.drag_offset = (pos.x() - elem.get("x", 0),
                                    pos.y() - elem.get("y", 0))

                self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and self.drag_element and self.layout_cfg:
            pos = event.pos()

            # 找到要拖动的元素
            for elem in self.layout_cfg["elements"]:
                if elem.get("id") == self.drag_element:
                    # 计算新位置
                    new_x = pos.x() - self.drag_offset[0]
                    new_y = pos.y() - self.drag_offset[1]

                    # 更新元素位置
                    elem["x"] = new_x
                    elem["y"] = new_y

                    # 发出信号通知位置改变
                    self.element_moved.emit(self.drag_element, new_x, new_y,
                                            elem.get("width", 100), elem.get("height", 50))

                    self.update()
                    break

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            self.drag_element = None

    def wheelEvent(self, event):
        """鼠标滚轮事件"""
        pass
