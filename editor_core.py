"""
editor_core.py - 封面编辑器核心逻辑
"""
import os
import sys
import json
import tempfile
import copy
import shutil
from PyQt5 import QtWidgets, QtCore, QtGui

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
    # 信号定义...
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
        self.current_elem = None
        self.ui = None
        self.preview_window = None
        self.current_bg_path = ""
    
    def load_configs(self):
        try:
            self.layout_cfg = load_json(LAYOUT_PATH)
            self.style_cfg = load_json(STYLE_PATH)
            
            # 获取背景图...
            bg_path = ""
            if self.style_cfg and "global" in self.style_cfg and "template_bg" in self.style_cfg["global"]:
                bg_cfg_path = self.style_cfg["global"]["template_bg"]
                if os.path.exists(bg_cfg_path):
                    bg_path = bg_cfg_path
                elif os.path.exists(os.path.join(BASE_DIR, bg_cfg_path)):
                    bg_path = os.path.join(BASE_DIR, bg_cfg_path)
                else:
                    template_dir = os.path.join(BASE_DIR, "template")
                    if os.path.exists(template_dir):
                        default_bgs = [f for f in os.listdir(template_dir) 
                                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                        if default_bgs:
                            bg_path = os.path.join(template_dir, default_bgs[0])
            
            self.current_bg_path = bg_path
            self.config_loaded.emit(self.layout_cfg, self.style_cfg, bg_path)
            self.status_message.emit("配置加载成功")
            return True
        except Exception as e:
            self.status_message.emit(f"加载配置文件失败: {e}")
            return False
    
    def save_configs(self):
        """保存配置文件 - 关键：确保配置不为空"""
        try:
            # 确保配置存在
            if not self.layout_cfg:
                self.layout_cfg = {"elements": []}
            if not self.style_cfg:
                self.style_cfg = {"elements": {}, "global": {}}
            
            # 确保样式配置结构正确
            if "elements" not in self.style_cfg:
                self.style_cfg["elements"] = {}
            
            save_json(LAYOUT_PATH, self.layout_cfg)
            save_json(STYLE_PATH, self.style_cfg)
            
            self.config_saved.emit()
            self.status_message.emit("配置已保存")
            print(f"✅ 配置已保存到: {LAYOUT_PATH}, {STYLE_PATH}")
            return True
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self.status_message.emit(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def handle_style_changed(self, elem_id, key, value):
        """处理样式属性变化 - 关键：确保正确保存"""
        print(f"🔧 样式变更: {elem_id}.{key} = {value}")
        
        # 确保样式配置结构存在
        if "elements" not in self.style_cfg:
            self.style_cfg["elements"] = {}
        if elem_id not in self.style_cfg["elements"]:
            self.style_cfg["elements"][elem_id] = {}
        
        # 特殊处理阴影配置
        if key.startswith("shadow_"):
            shadow_key = key.replace("shadow_", "")
            if "shadow" not in self.style_cfg["elements"][elem_id]:
                self.style_cfg["elements"][elem_id]["shadow"] = {}
            self.style_cfg["elements"][elem_id]["shadow"][shadow_key] = value
        else:
            self.style_cfg["elements"][elem_id][key] = value
        
        # 立即保存配置
        self.save_configs()
        
        # 验证保存
        if os.path.exists(STYLE_PATH):
            try:
                with open(STYLE_PATH, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    if elem_id in saved.get("elements", {}):
                        print(f"✅ 验证: {elem_id}.{key} 已保存到文件")
            except:
                pass
    
    def handle_element_selected(self, elem_id):
        """处理元素选中 - 修复：避免NoneType错误"""
        elem = self.find_element(elem_id)
        self.current_elem = elem
        if elem:
            self.selection_changed.emit(elem)
        else:
            # 发送空字典而不是None
            self.selection_changed.emit({})
    
    def handle_delete_element_request(self, elem_id):
        """处理删除元素请求"""
        # 导入cover_engine中的函数
        try:
            from cover_engine import delete_element
        except ImportError as e:
            self.status_message.emit(f"导入cover_engine失败: {e}")
            return False
        
        if delete_element(elem_id):
            self.load_configs()
            self.element_deleted.emit(elem_id)
            self.current_elem = None
            self.selection_changed.emit({})  # 发送空字典
            return True
        return False
    
    # 其他方法保持原样...
    def find_element(self, elem_id):
        if not self.layout_cfg or "elements" not in self.layout_cfg:
            return None
        for elem in self.layout_cfg["elements"]:
            if elem["id"] == elem_id:
                return elem
        return None
    
    def get_element(self, elem_id):
        return self.find_element(elem_id)
    
    def handle_layout_changed(self, elem_id, field, value):
        elem = self.find_element(elem_id)
        if elem:
            elem[field] = value
            self.save_configs()
    
    def handle_canvas_geom_changed(self, elem_id, x, y, w, h):
        elem = self.find_element(elem_id)
        if elem:
            elem["x"] = x
            elem["y"] = y
            elem["width"] = w
            elem["height"] = h
            self.save_configs()
    
    # ========== 添加缺失的方法 ==========
    
    def refresh_configs(self):
        """刷新配置"""
        self.load_configs()
    
    def handle_background_selected(self, bg_path):
        """处理背景选择"""
        if bg_path and os.path.exists(bg_path):
            self.current_bg_path = bg_path
            # 更新样式配置中的背景路径
            if self.style_cfg and "global" in self.style_cfg:
                self.style_cfg["global"]["template_bg"] = bg_path
                self.save_configs()
            
            self.background_updated.emit(bg_path)
            self.status_message.emit(f"背景已更新: {os.path.basename(bg_path)}")
    
    def handle_add_element_request(self, elem_type, elem_id):
        """处理添加元素请求"""
        print(f"添加元素请求: type={elem_type}, id={elem_id}")
        self.status_message.emit(f"收到添加元素请求: {elem_type} - {elem_id}")
        
        # 尝试使用cover_engine
        try:
            from cover_engine import add_element
            if add_element(elem_type, elem_id):
                self.load_configs()
                self.element_added.emit(elem_id)
                return True
        except ImportError as e:
            self.status_message.emit(f"导入cover_engine失败: {e}")
        
        # 如果cover_engine不可用，手动添加
        try:
            # 确保配置存在
            if not self.layout_cfg:
                self.layout_cfg = {"elements": []}
            if "elements" not in self.layout_cfg:
                self.layout_cfg["elements"] = []
            
            # 检查是否已存在
            for elem in self.layout_cfg["elements"]:
                if elem.get("id") == elem_id:
                    self.status_message.emit(f"元素ID已存在: {elem_id}")
                    return False
            
            # 创建新元素
            new_element = {
                "id": elem_id,
                "type": elem_type,
                "x": 100,
                "y": 100,
                "width": 200 if elem_type != "image" else 100,
                "height": 50 if elem_type != "image" else 100
            }
            
            # 添加到配置
            self.layout_cfg["elements"].append(new_element)
            
            # 初始化样式配置
            if not self.style_cfg:
                self.style_cfg = {"elements": {}, "global": {}}
            if "elements" not in self.style_cfg:
                self.style_cfg["elements"] = {}
            
            # 添加默认样式
            self.style_cfg["elements"][elem_id] = {}
            if elem_type == "text":
                self.style_cfg["elements"][elem_id] = {
                    "text": "新文本",
                    "font_size": 24,
                    "font_color": "#000000"
                }
            elif elem_type == "image":
                self.style_cfg["elements"][elem_id] = {
                    "image_path": "",
                    "opacity": 100
                }
            elif elem_type == "badge":
                self.style_cfg["elements"][elem_id] = {
                    "text": "徽章",
                    "bg_color": "#FF0000",
                    "font_color": "#FFFFFF"
                }
            
            # 保存配置
            self.save_configs()
            
            # 发送信号
            self.element_added.emit(elem_id)
            self.status_message.emit(f"已添加元素: {elem_id}")
            return True
            
        except Exception as e:
            self.status_message.emit(f"添加元素失败: {e}")
            return False
    
    def show_preview(self, ui_window):
        """显示预览窗口"""
        print("显示预览窗口")
        self.status_message.emit("预览功能准备中...")
        # 这里可以添加预览窗口的打开逻辑
        # 暂时只显示消息
        QtWidgets.QMessageBox.information(ui_window, "预览", "预览功能将在后续版本中提供")

def run_editor():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    core = EditorCore()
    from editor_ui import EditorUI
    ui = EditorUI()
    core.ui = ui
    
    # 连接信号
    ui.sig_request_save.connect(core.save_configs)
    ui.sig_request_preview.connect(lambda: core.show_preview(ui))
    ui.sig_request_refresh.connect(core.refresh_configs)
    ui.sig_background_selected.connect(core.handle_background_selected)
    ui.sig_add_element_request.connect(core.handle_add_element_request)
    ui.sig_delete_element_request.connect(core.handle_delete_element_request)
    ui.sig_select_element.connect(core.handle_element_selected)
    ui.sig_layout_changed.connect(core.handle_layout_changed)
    ui.sig_style_changed.connect(core.handle_style_changed)
    ui.sig_canvas_geom_changed.connect(core.handle_canvas_geom_changed)
    
    core.config_loaded.connect(ui.set_state)
    core.element_added.connect(lambda elem_id: ui.refresh_all(core.layout_cfg, core.style_cfg, elem_id))
    core.element_deleted.connect(lambda elem_id: ui.refresh_all(core.layout_cfg, core.style_cfg))
    core.selection_changed.connect(ui.update_selection)
    core.config_saved.connect(lambda: ui.show_status("配置已保存"))
    core.status_message.connect(ui.show_status)
    core.background_updated.connect(ui.set_background)
    
    core.load_configs()
    ui.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_editor()