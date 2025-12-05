"""
editor_preview.py - 封面预览功能
"""
import os
import sys
import json
import tempfile
import shutil
from PyQt5 import QtWidgets, QtCore, QtGui


def show_preview(parent, layout_cfg, style_cfg):
    """
    显示预览对话框
    
    Args:
        parent: 父窗口
        layout_cfg: 布局配置
        style_cfg: 样式配置
    """
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="cover_preview_")
        
        # 保存临时配置
        temp_layout_path = os.path.join(temp_dir, "layout.json")
        temp_style_path = os.path.join(temp_dir, "style.json")
        
        with open(temp_layout_path, "w", encoding="utf-8") as f:
            json.dump(layout_cfg, f, ensure_ascii=False, indent=2)
        
        with open(temp_style_path, "w", encoding="utf-8") as f:
            json.dump(style_cfg, f, ensure_ascii=False, indent=2)
        
        # 构造示例参数
        params = {
            "title": "示例标题",
            "episode": 1,
            "tagline": "示例副标题"
        }
        
        # 为所有元素添加示例文本
        if "elements" in layout_cfg:
            for elem in layout_cfg["elements"]:
                elem_id = elem["id"]
                elem_type = elem.get("type", "text")
                
                if elem_type == "text":
                    # 预定义元素映射
                    if elem_id == "title_main":
                        params[elem_id] = "示例标题"
                    elif elem_id == "tagline":
                        params[elem_id] = "示例副标题"
                    else:
                        # 自定义文本元素
                        params[elem_id] = f"示例文本 [{elem_id}]"
                
                elif elem_type == "badge":
                    if elem_id == "episode_badge":
                        params["episode"] = 1
                    else:
                        # 自定义徽章元素
                        params[elem_id] = f"徽章"
                
                elif elem_type == "image":
                    # 图片元素 - 留空，使用默认图片模式
                    pass
        
        # 设置输出路径
        temp_output_path = os.path.join(temp_dir, "preview.png")
        params["output_path"] = temp_output_path
        
        # 临时修改cover_engine的配置路径
        import cover_engine
        original_layout_path = cover_engine.LAYOUT_PATH
        original_style_path = cover_engine.STYLE_PATH
        
        try:
            # 临时替换配置路径
            cover_engine.LAYOUT_PATH = temp_layout_path
            cover_engine.STYLE_PATH = temp_style_path
            
            # 渲染封面
            output_path = cover_engine.render_cover(params)
            
            # 创建预览对话框
            dialog = PreviewDialog(parent, output_path, temp_dir)
            dialog.exec_()
            
        finally:
            # 恢复原始路径
            cover_engine.LAYOUT_PATH = original_layout_path
            cover_engine.STYLE_PATH = original_style_path
            
            # 清理临时目录（如果对话框没有保存图片）
            if not dialog.saved:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "预览错误", f"生成预览失败: {str(e)}")


class PreviewDialog(QtWidgets.QDialog):
    """预览对话框"""
    
    def __init__(self, parent, image_path, temp_dir):
        super().__init__(parent)
        self.image_path = image_path
        self.temp_dir = temp_dir
        self.saved = False
        
        self.setWindowTitle("封面预览")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        
        # 设置窗口标志
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowCloseButtonHint)
    
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # 图片显示区域
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        # 加载图片
        self.load_preview_image()
        
        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.image_label)
        
        layout.addWidget(scroll, 4)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        
        # 保存按钮
        save_btn = QtWidgets.QPushButton("保存为PNG")
        save_btn.clicked.connect(self.save_image)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_preview_image(self):
        """加载预览图片"""
        if os.path.exists(self.image_path):
            pixmap = QtGui.QPixmap(self.image_path)
            if not pixmap.isNull():
                # 缩放以适应窗口
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size() * 0.9, 
                    QtCore.Qt.KeepAspectRatio, 
                    QtCore.Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("预览图片加载失败")
        else:
            self.image_label.setText("预览图片不存在")
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        if hasattr(self, 'image_label') and self.image_label.pixmap():
            self.load_preview_image()
    
    def save_image(self):
        """保存图片"""
        if not os.path.exists(self.image_path):
            QtWidgets.QMessageBox.warning(self, "保存失败", "预览图片不存在")
            return
        
        # 选择保存路径
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存预览图片",
            os.path.join(os.path.expanduser("~"), "cover_preview.png"),
            "PNG图片 (*.png);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 复制图片到指定位置
                import shutil
                shutil.copy2(self.image_path, file_path)
                
                QtWidgets.QMessageBox.information(self, "保存成功", f"图片已保存到:\n{file_path}")
                self.saved = True
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "保存失败", f"保存图片时出错:\n{str(e)}")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 清理临时目录
        if not self.saved and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
        super().closeEvent(event)