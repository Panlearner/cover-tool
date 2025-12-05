"""
editor_core.py - 封面编辑器核心逻辑
"""
import os
import sys
import json

# 首先检查 PyQt5
try:
    from PyQt5 import QtWidgets, QtCore
    print("[editor_core] PyQt5 导入成功")
except ImportError as e:
    print(f"[editor_core] PyQt5 导入失败: {e}")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAYOUT_PATH = os.path.join(BASE_DIR, "layout.json")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class EditorCore(QtCore.QObject):
    config_loaded = QtCore.pyqtSignal(dict, dict, str)
    element_added = QtCore.pyqtSignal(str)
    element_deleted = QtCore.pyqtSignal(str)
    selection_changed = QtCore.pyqtSignal(dict)
    config_saved = QtCore.pyqtSignal()
    status_message = QtCore.pyqtSignal(str)
    background_updated = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.layout_cfg = None
        self.style_cfg = None
        self.current_bg_path = ""
        self.ui = None

        self.load_configs()

    def load_configs(self):
        """加载配置"""
        # 1. 加载布局配置
        try:
            self.layout_cfg = load_json(LAYOUT_PATH)
        except Exception as e:
            print(f"[核心] 无法加载布局配置 ({LAYOUT_PATH}): {e}")
            self.layout_cfg = {"elements": []}

        # 2. 加载样式配置
        try:
            self.style_cfg = load_json(STYLE_PATH)
        except Exception as e:
            print(f"[核心] 无法加载样式配置 ({STYLE_PATH}): {e}")
            self.style_cfg = {"elements": {}, "global": {}}

        # 3. 提取背景路径
        if "global" in self.style_cfg and "template_bg" in self.style_cfg["global"]:
            self.current_bg_path = self.style_cfg["global"]["template_bg"]
        else:
            self.current_bg_path = ""

        print("[核心] 配置加载完成")
        self.config_loaded.emit(
            self.layout_cfg, self.style_cfg, self.current_bg_path)
        self.status_message.emit("配置已加载")

    def save_configs(self):
        """保存布局和样式配置（静默，不刷屏）"""
        try:
            with open(LAYOUT_PATH, "w", encoding="utf-8") as f:
                json.dump(self.layout_cfg, f, ensure_ascii=False, indent=2)
            with open(STYLE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.style_cfg, f, ensure_ascii=False, indent=2)
            self.config_saved.emit()
            # 不在每次细微修改时打印状态，避免终端刷屏
        except Exception as e:
            print(f"[核心] 保存配置失败: {e}")
            self.status_message.emit(f"保存配置失败: {e}")

    def handle_background_selected(self, bg_path):
        """处理背景图片选择 - 修复版"""
        print(f"[核心] 接收到背景图: {bg_path}")

        if not bg_path or not os.path.exists(bg_path):
            self.status_message.emit(f"背景图片不存在: {bg_path}")
            return

        # 更新当前背景路径
        self.current_bg_path = bg_path

        # 确保样式配置存在
        if not self.style_cfg:
            self.style_cfg = {"elements": {}, "global": {}}
        if "global" not in self.style_cfg:
            self.style_cfg["global"] = {}

        # 保存背景路径
        self.style_cfg["global"]["template_bg"] = bg_path

        # 立即保存配置
        try:
            if self.layout_cfg:  # 确保布局配置存在
                save_json(LAYOUT_PATH, self.layout_cfg)
            save_json(STYLE_PATH, self.style_cfg)
            print(f"[核心] 配置已保存，背景路径: {bg_path}")
        except Exception as e:
            print(f"[核心] 保存配置失败: {e}")
            self.status_message.emit(f"保存背景失败: {e}")
            return

        # 发送信号更新UI
        self.background_updated.emit(bg_path)
        self.status_message.emit(f"背景已更新: {os.path.basename(bg_path)}")

    def handle_add_element_request(self, elem_type, elem_id):
        """处理添加元素请求"""
        # 1. 更新布局配置
        new_element = {
            "id": elem_id,
            "type": elem_type,
            "x": 10, "y": 10, "width": 100, "height": 50,
            "z_index": len(self.layout_cfg["elements"])
        }
        if elem_type == "text":
            new_element["content"] = "新的文本元素"
        elif elem_type == "image":
            new_element["content"] = "template/default_image.png"
            new_element["width"] = 150
            new_element["height"] = 150
        elif elem_type == "badge":
            new_element["content"] = "Badge"
            new_element["width"] = 80
            new_element["height"] = 30

        self.layout_cfg["elements"].append(new_element)

        # 2. 更新样式配置 (如果需要默认样式)
        if elem_id not in self.style_cfg.get("elements", {}):
            if elem_type == "text":
                self.style_cfg["elements"][elem_id] = {
                    "font_family": "SimHei",
                    "font_size": 16,
                    "text_color": "#000000",
                    "align": "left"
                }
            elif elem_type == "image":
                self.style_cfg["elements"][elem_id] = {
                    "image_pattern": new_element["content"],
                    "opacity": 1.0
                }
            elif elem_type == "badge":
                self.style_cfg["elements"][elem_id] = {
                    "text_color": "#ffffff",
                    "bg_color": "#3498db",
                    "font_size": 12,
                    "padding": 5,
                    "border_radius": 5
                }

        # 3. 保存配置
        self.save_configs()

        # 4. 通知UI更新
        self.element_added.emit(elem_id)
        self.status_message.emit(f"已添加元素: {elem_id}")

    def handle_delete_element_request(self, elem_id):
        """处理删除元素请求"""
        # 1. 更新布局配置
        self.layout_cfg["elements"] = [
            elem for elem in self.layout_cfg["elements"] if elem["id"] != elem_id
        ]

        # 2. 更新样式配置
        if elem_id in self.style_cfg.get("elements", {}):
            del self.style_cfg["elements"][elem_id]

        # 3. 保存配置
        self.save_configs()

        # 4. 通知UI更新
        self.element_deleted.emit(elem_id)
        self.status_message.emit(f"已删除元素: {elem_id}")

    def handle_element_selected(self, elem_id):
        """处理元素选中事件"""
        for elem in self.layout_cfg.get("elements", []):
            if elem.get("id") == elem_id:
                self.selection_changed.emit(elem)
                break

    def handle_layout_changed(self, elem_id, key, value):
        """处理布局属性变更"""
        for elem in self.layout_cfg.get("elements", []):
            if elem.get("id") == elem_id:
                elem[key] = value
                self.save_configs()
                self.ui.canvas.update_element(
                    elem_id, self.layout_cfg, self.style_cfg)
                break

    def handle_style_changed(self, elem_id, key, value):
        """处理样式属性变更"""
        # 深拷贝 style_cfg，避免元素间共用引用
        self.style_cfg = json.loads(json.dumps(self.style_cfg))
        if elem_id not in self.style_cfg.get("elements", {}):
            self.style_cfg["elements"][elem_id] = {}
        self.style_cfg["elements"][elem_id][key] = value

        # 如果修改的是 image_pattern，需要同步更新 layout_cfg 中的 content 字段
        if key == "image_pattern" and self.layout_cfg:
            for elem in self.layout_cfg.get("elements", []):
                if elem.get("id") == elem_id:
                    elem["content"] = value
                    break

        self.save_configs()
        self.ui.canvas.update_element(elem_id, self.layout_cfg, self.style_cfg)

    def handle_canvas_geom_changed(self, elem_id, x, y, w, h):
        """处理画布上元素移动/缩放引起的几何变化"""
        updated = False
        for elem in self.layout_cfg.get("elements", []):
            if elem.get("id") == elem_id:
                if elem.get("x") != x:
                    elem["x"] = x
                    updated = True
                if elem.get("y") != y:
                    elem["y"] = y
                    updated = True
                if elem.get("width") != w:
                    elem["width"] = w
                    updated = True
                if elem.get("height") != h:
                    elem["height"] = h
                    updated = True
                break

        if updated:
            self.save_configs()

    def update_background(self, bg_path):
        """在配置加载后设置背景"""
        if bg_path and os.path.exists(bg_path):
            # 将路径设置给UI和核心
            self.current_bg_path = bg_path

            # 确保 style_cfg["global"]["template_bg"] 被设置
            if "global" not in self.style_cfg:
                self.style_cfg["global"] = {}
            self.style_cfg["global"]["template_bg"] = bg_path

            self.background_updated.emit(bg_path)


def run_editor():
    from editor_ui import EditorUI

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    core = EditorCore()
    ui = EditorUI()
    core.ui = ui

    # 连接信号
    ui.sig_request_save.connect(core.save_configs)
    ui.sig_request_refresh.connect(core.load_configs)
    ui.sig_background_selected.connect(core.handle_background_selected)
    ui.sig_add_element_request.connect(core.handle_add_element_request)
    ui.sig_delete_element_request.connect(core.handle_delete_element_request)
    ui.sig_select_element.connect(core.handle_element_selected)
    ui.sig_layout_changed.connect(core.handle_layout_changed)
    ui.sig_style_changed.connect(core.handle_style_changed)
    ui.sig_canvas_geom_changed.connect(core.handle_canvas_geom_changed)

    core.config_loaded.connect(ui.set_state)
    core.element_added.connect(lambda elem_id: ui.refresh_all(
        core.layout_cfg, core.style_cfg, elem_id))
    core.element_deleted.connect(
        lambda elem_id: ui.refresh_all(core.layout_cfg, core.style_cfg))
    core.selection_changed.connect(ui.update_selection)
    core.status_message.connect(ui.show_status)
    core.background_updated.connect(ui.set_background)

    # 启动应用
    ui.show()
    core.load_configs()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_editor()
