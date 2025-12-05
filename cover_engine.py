import os
import json
import glob
import random
import copy
from typing import Dict, Any, List, Optional, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAYOUT_PATH = os.path.join(BASE_DIR, "layout.json")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]):
    """保存JSON文件，确保目录存在"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def hex_to_rgba(color: str):
    """将十六进制颜色转换为RGBA元组"""
    if color is None:
        return (255, 255, 255, 255)
    
    color = color.lstrip("#")
    if len(color) == 6:
        r, g, b = bytes.fromhex(color[:6])
        return (r, g, b, 255)
    elif len(color) == 8:
        r, g, b, a = bytes.fromhex(color[:8])
        return (r, g, b, a)
    return (255, 255, 255, 255)


def apply_opencv_filters(pil_img: Image.Image, filters_cfg: Dict[str, Any]) -> Image.Image:
    """应用OpenCV滤镜"""
    if not filters_cfg.get("enable", True):
        return pil_img

    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 对比度和亮度调整
    cr = filters_cfg.get("contrast_range", [1.0, 1.0])
    br = filters_cfg.get("brightness_range", [0, 0])
    alpha = float(np.random.uniform(cr[0], cr[1]))
    beta = int(np.random.randint(br[0], br[1] + 1))
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    # 暗角效果
    vg_strength = float(filters_cfg.get("vignette_strength", 0.0))
    if vg_strength > 0:
        h, w = img.shape[:2]
        x = cv2.getGaussianKernel(w, int(w * vg_strength))
        y = cv2.getGaussianKernel(h, int(h * vg_strength))
        mask = y * x.T
        mask = mask / mask.max()
        mask = cv2.merge([mask, mask, mask])
        img = (img * mask).astype(np.uint8)

    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def get_random_variation(variation_cfg: Dict[str, Any], seed: Optional[int] = None) -> Dict[str, Any]:
    """根据配置生成随机变化"""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    result = {}
    
    # 位置抖动
    if "jitter_x" in variation_cfg:
        jitter = variation_cfg["jitter_x"]
        if isinstance(jitter, list) and len(jitter) == 2:
            result["jitter_x"] = random.randint(jitter[0], jitter[1])
    
    if "jitter_y" in variation_cfg:
        jitter = variation_cfg["jitter_y"]
        if isinstance(jitter, list) and len(jitter) == 2:
            result["jitter_y"] = random.randint(jitter[0], jitter[1])
    
    # 色彩微调
    if "color_adjust" in variation_cfg:
        color_adj = variation_cfg["color_adjust"]
        if isinstance(color_adj, list) and len(color_adj) == 2:
            adj_r = random.randint(color_adj[0], color_adj[1])
            adj_g = random.randint(color_adj[0], color_adj[1])
            adj_b = random.randint(color_adj[0], color_adj[1])
            result["color_adjust"] = (adj_r, adj_g, adj_b)
    
    # 透明度变化
    if "opacity_range" in variation_cfg:
        opacity_range = variation_cfg["opacity_range"]
        if isinstance(opacity_range, list) and len(opacity_range) == 2:
            result["opacity"] = random.uniform(opacity_range[0], opacity_range[1])
    
    # 旋转角度
    if "rotate_range" in variation_cfg:
        rotate_range = variation_cfg["rotate_range"]
        if isinstance(rotate_range, list) and len(rotate_range) == 2:
            result["rotate"] = random.randint(rotate_range[0], rotate_range[1])
    
    return result


def adjust_color(color: tuple, adjustment: Optional[tuple]) -> tuple:
    """根据调整值修改颜色"""
    if not adjustment:
        return color
    
    r, g, b, a = color
    adj_r, adj_g, adj_b = adjustment
    r = max(0, min(255, r + adj_r))
    g = max(0, min(255, g + adj_g))
    b = max(0, min(255, b + adj_b))
    return (r, g, b, a)


def draw_text_with_style(draw, elem_box, text, style_cfg, font_dir, align="left", 
                         variation: Optional[Dict[str, Any]] = None):
    """绘制带样式的文本"""
    if not text:
        return

    # 获取字体文件路径
    font_file = style_cfg.get("font_file", "MSYHBD.TTC")
    font_path = os.path.join(font_dir, font_file)
    
    # 获取字号配置
    base_size = style_cfg.get("base_size", style_cfg.get("size", 64))
    min_size = style_cfg.get("min_size", max(10, base_size // 2))
    max_size = style_cfg.get("max_size", min(200, base_size * 2))

    w_box, h_box = elem_box["width"], elem_box["height"]
    font_size = base_size
    
    # 尝试加载字体
    try:
        # 尝试找到合适的字体大小
        while font_size >= min_size:
            try:
                font = ImageFont.truetype(font_path, font_size)
                # 使用textbbox获取文本尺寸
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if w <= w_box and h <= h_box:
                    break
            except:
                pass
            font_size -= 2
        
        font_size = max(min(font_size, max_size), min_size)
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        # 如果字体加载失败，使用默认字体
        print(f"字体加载失败 {font_path}: {e}")
        font = ImageFont.load_default()
        font_size = 20

    x, y = elem_box["x"], elem_box["y"]
    
    # 应用位置抖动
    if variation:
        x += variation.get("jitter_x", 0)
        y += variation.get("jitter_y", 0)
    
    # 获取文本边界框
    bbox = draw.textbbox((0, 0), text, font=font)
    w_text, h_text = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # 根据对齐方式调整位置
    if align == "center":
        x = x + (w_box - w_text) / 2
    elif align == "right":
        x = x + (w_box - w_text)

    # 获取颜色并应用微调
    fill_color = hex_to_rgba(style_cfg.get("fill_color", "#FFFFFF"))
    if variation and "color_adjust" in variation:
        fill_color = adjust_color(fill_color, variation["color_adjust"])
    
    stroke_color = hex_to_rgba(style_cfg.get("stroke_color", "#000000"))
    stroke_width = style_cfg.get("stroke_width", 0)

    # 绘制阴影
    shadow_cfg = style_cfg.get("shadow", {})
    if shadow_cfg.get("enabled", False):
        sx = shadow_cfg.get("offset_x", 2)
        sy = shadow_cfg.get("offset_y", 2)
        shadow_color = hex_to_rgba(shadow_cfg.get("color", "#00000080"))
        draw.text((x + sx, y + sy), text, font=font, fill=shadow_color)

    # 绘制描边
    if stroke_width > 0:
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)

    # 绘制文本
    draw.text((x, y), text, font=font, fill=fill_color)


def draw_badge(draw, elem_box, text, style_cfg, font_dir, variation: Optional[Dict[str, Any]] = None):
    """绘制徽章元素"""
    if not text:
        return

    # 获取字体
    font_file = style_cfg.get("font_file", "MSYHBD.TTC")
    font_path = os.path.join(font_dir, font_file)
    try:
        font = ImageFont.truetype(font_path, style_cfg.get("size", 48))
    except:
        font = ImageFont.load_default()

    x, y, w, h = elem_box["x"], elem_box["y"], elem_box["width"], elem_box["height"]
    
    # 应用位置抖动
    if variation:
        x += variation.get("jitter_x", 0)
        y += variation.get("jitter_y", 0)
    
    # 获取内边距
    pad_x = style_cfg.get("padding_x", 20)
    pad_y = style_cfg.get("padding_y", 10)

    # 获取文本大小
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # 计算徽章大小
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    bx = x + (w - bw) / 2
    by = y + (h - bh) / 2

    # 获取背景色并应用微调
    bg_color = hex_to_rgba(style_cfg.get("badge_bg_color", "#FFCC00"))
    if variation and "color_adjust" in variation:
        bg_color = adjust_color(bg_color, variation["color_adjust"])
    
    radius = style_cfg.get("corner_radius", 20)

    # 创建圆角矩形
    rect = Image.new("RGBA", draw.im.size, (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rect)
    rdraw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=radius, fill=bg_color)
    
    # 应用透明度
    opacity = variation.get("opacity", 1.0) if variation else 1.0
    if opacity < 1.0:
        rect = rect.copy()
        alpha = rect.split()[3]
        alpha = alpha.point(lambda p: p * opacity)
        rect.putalpha(alpha)
    
    # 合成到画布
    draw.im.alpha_composite(rect)

    # 绘制徽章文字
    text_color = hex_to_rgba(style_cfg.get("badge_text_color", "#000000"))
    draw.text((bx + pad_x, by + pad_y), text, font=font, fill=text_color)


def draw_image_element(draw, elem_box, style_cfg, base_dir, 
                       custom_image_path: Optional[str] = None, 
                       variation: Optional[Dict[str, Any]] = None):
    """绘制图片元素"""
    # 优先使用自定义图片路径
    image_path = custom_image_path
    
    # 如果没有自定义路径，则使用样式配置中的图片模式
    if not image_path or not os.path.exists(image_path):
        image_pattern = style_cfg.get("image_pattern", "template/deco_*.png")
        if image_pattern:
            pattern_path = os.path.join(base_dir, image_pattern)
            image_files = glob.glob(pattern_path)
            if image_files:
                # 随机选择一张图片
                image_path = random.choice(image_files)
    
    if not image_path or not os.path.exists(image_path):
        return
    
    try:
        # 打开并处理图片
        img = Image.open(image_path).convert("RGBA")
        
        # 缩放图片到元素大小
        img = img.resize((elem_box["width"], elem_box["height"]), Image.Resampling.LANCZOS)
        
        # 应用旋转
        if variation and "rotate" in variation:
            img = img.rotate(variation["rotate"], expand=True, resample=Image.Resampling.BICUBIC)
            # 重新调整大小
            img = img.resize((elem_box["width"], elem_box["height"]), Image.Resampling.LANCZOS)
        
        # 应用透明度
        opacity = variation.get("opacity", 1.0) if variation else style_cfg.get("opacity", 1.0)
        if opacity < 1.0:
            img = img.copy()
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: p * opacity)
            img.putalpha(alpha)
        
        # 粘贴到画布上
        x, y = elem_box["x"], elem_box["y"]
        if variation:
            x += variation.get("jitter_x", 0)
            y += variation.get("jitter_y", 0)
        
        draw.im.alpha_composite(img, (int(x), int(y)))
    except Exception as e:
        print(f"无法加载图片 {image_path}: {e}")


def get_default_element_config(element_type: str, element_id: str) -> tuple:
    """获取元素的默认配置"""
    # 默认布局配置
    default_layout = {
        "id": element_id,
        "type": element_type,
        "x": 100,
        "y": 100,
        "width": 300,
        "height": 100,
        "align": "left",
        "enabled": True
    }
    
    # 默认样式配置
    default_style = {}
    
    if element_type == "text":
        default_style = {
            "font_file": "MSYHBD.TTC",
            "base_size": 48,
            "min_size": 24,
            "max_size": 72,
            "fill_color": "#FFFFFF",
            "stroke_color": "#000000",
            "stroke_width": 2,
            "shadow": {
                "enabled": False,
                "offset_x": 2,
                "offset_y": 2,
                "color": "#00000080"
            },
            "variation": {
                "jitter_x": [-2, 2],
                "jitter_y": [-2, 2],
                "color_adjust": [-5, 5]
            }
        }
    elif element_type == "badge":
        default_style = {
            "font_file": "MSYHBD.TTC",
            "size": 36,
            "badge_bg_color": "#FFCC00",
            "badge_text_color": "#000000",
            "corner_radius": 15,
            "padding_x": 15,
            "padding_y": 8,
            "format": "CUSTOM",
            "variation": {
                "jitter_x": [-3, 3],
                "jitter_y": [-3, 3],
                "opacity_range": [0.9, 1.0]
            }
        }
    elif element_type == "image":
        default_style = {
            "image_pattern": "template/deco_*.png",
            "opacity": 1.0,
            "variation": {
                "jitter_x": [-10, 10],
                "jitter_y": [-10, 10],
                "opacity_range": [0.8, 1.0],
                "rotate_range": [-5, 5]
            }
        }
    
    return default_layout, default_style


def add_custom_element(element_type: str, element_id: str) -> bool:
    """添加自定义元素到配置文件"""
    try:
        # 加载现有配置
        layout = load_json(LAYOUT_PATH)
        style = load_json(STYLE_PATH)
        
        # 检查元素ID是否已存在
        existing_ids = [elem["id"] for elem in layout.get("elements", [])]
        if element_id in existing_ids:
            print(f"元素ID '{element_id}' 已存在")
            return False
        
        # 获取默认配置
        default_layout, default_style = get_default_element_config(element_type, element_id)
        
        # 添加到布局配置
        if "elements" not in layout:
            layout["elements"] = []
        layout["elements"].append(default_layout)
        
        # 添加到样式配置
        if "elements" not in style:
            style["elements"] = {}
        style["elements"][element_id] = default_style
        
        # 保存配置文件
        save_json(LAYOUT_PATH, layout)
        save_json(STYLE_PATH, style)
        
        print(f"已添加自定义元素: {element_id} ({element_type})")
        return True
        
    except Exception as e:
        print(f"添加自定义元素失败: {e}")
        return False


def delete_element(element_id: str) -> bool:
    """从配置文件中删除元素"""
    try:
        # 加载现有配置
        layout = load_json(LAYOUT_PATH)
        style = load_json(STYLE_PATH)
        
        # 从布局配置中删除
        if "elements" in layout:
            layout["elements"] = [elem for elem in layout["elements"] if elem["id"] != element_id]
        
        # 从样式配置中删除
        if "elements" in style and element_id in style["elements"]:
            del style["elements"][element_id]
        
        # 保存配置文件
        save_json(LAYOUT_PATH, layout)
        save_json(STYLE_PATH, style)
        
        print(f"已删除元素: {element_id}")
        return True
        
    except Exception as e:
        print(f"删除元素失败: {e}")
        return False


def render_cover(params: Dict[str, Any]) -> str:
    """
    渲染封面
    
    params:
        title: str - 主标题
        episode: int | None - 集数
        tagline: str | None - 副标题
        output_path: str | None - 输出路径
        seed: int | None - 随机种子
        其他自定义元素参数: 键名为元素ID，值为文本内容或图片路径
    """
    layout = load_json(LAYOUT_PATH)
    style = load_json(STYLE_PATH)

    global_cfg = style.get("global", {})
    font_dir = os.path.join(BASE_DIR, global_cfg.get("font_dir", "fonts"))
    bg_path = os.path.join(BASE_DIR, global_cfg.get("template_bg", "template/bg.jpg"))

    # 设置随机种子
    seed = params.get("seed")
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # 加载背景图片
    bg = Image.open(bg_path).convert("RGBA")
    bg = apply_opencv_filters(bg, global_cfg.get("opencv_filters", {}))
    draw = ImageDraw.Draw(bg, "RGBA")

    elements = layout.get("elements", [])
    style_elems = style.get("elements", {})

    # 预定义参数映射
    param_mapping = {
        "title_main": "title",
        "tagline": "tagline",
        "episode_badge": "episode"
    }

    for elem in elements:
        if not elem.get("enabled", True):
            continue
        
        elem_id = elem["id"]
        elem_type = elem.get("type", "text")
        elem_style = style_elems.get(elem_id, {})

        align = elem.get("align", "left")
        box = {
            "x": elem["x"],
            "y": elem["y"],
            "width": elem["width"],
            "height": elem["height"],
        }

        # 获取随机变化配置
        variation_cfg = elem_style.get("variation", {})
        variation = get_random_variation(variation_cfg, seed) if variation_cfg else None

        # 根据元素类型进行渲染
        if elem_type == "text":
            # 确定文本来源
            if elem_id in param_mapping:
                # 预定义元素从对应的参数获取文本
                text = params.get(param_mapping[elem_id], "")
            else:
                # 自定义元素直接从params中获取，键名为元素ID
                text = params.get(elem_id, "")
            
            draw_text_with_style(draw, box, text, elem_style, font_dir, align=align, variation=variation)

        elif elem_type == "badge":
            # 确定徽章文本来源
            if elem_id in param_mapping:
                # 预定义徽章（如episode_badge）
                ep = params.get(param_mapping[elem_id])
                if ep is None:
                    continue
                fmt = elem_style.get("format", "EP {ep:02d}")
                text = fmt.format(ep=int(ep))
            else:
                # 自定义徽章，从params中获取文本或使用默认文本
                text = params.get(elem_id, elem_style.get("format", "CUSTOM"))
            
            draw_badge(draw, box, text, elem_style, font_dir, variation=variation)

        elif elem_type == "image":
            # 获取自定义图片路径（如果有）
            custom_image_path = params.get(elem_id)
            if not custom_image_path and elem_id in param_mapping:
                # 检查是否有映射的参数
                custom_image_path = params.get(param_mapping[elem_id])
            
            draw_image_element(draw, box, elem_style, BASE_DIR, custom_image_path, variation=variation)

    # 确保输出目录存在
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 确定输出路径
    output_path = params.get("output_path")
    if not output_path:
        # 生成默认文件名
        title = params.get("title", "cover")
        episode = params.get("episode", 1)
        output_path = os.path.join(output_dir, f"{title}_ep{episode:03d}.jpg")

    # 保存图片
    bg.convert("RGB").save(output_path, quality=95)
    return output_path