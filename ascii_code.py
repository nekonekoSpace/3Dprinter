
import argparse
from PIL import Image
import numpy as np
import sys

# Windowsの旧環境対策（入っていれば自動で有効化）
try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass

ASCII_CHARS = "@%#*+=-:. "  # 暗→明（好みで変更可）

def print_color_ascii(image_path, width=200, line_scale=0.55, charset=ASCII_CHARS):
    img = Image.open(image_path).convert("RGB")
    aspect = img.height / img.width
    h = max(1, int(width * aspect * line_scale))     # 文字の縦横比補正
    img = img.resize((width, h), Image.Resampling.BICUBIC)

    arr = np.array(img)                              # (H, W, 3)
    # 輝度で使用文字を選ぶ
    lum = (0.299*arr[...,0] + 0.587*arr[...,1] + 0.114*arr[...,2]).astype("uint8")
    idx = (lum * ((len(charset)-1)/255)).astype(int)

    reset = "\x1b[0m"
    out = []
    for y in range(arr.shape[0]):
        row = []
        for x in range(arr.shape[1]):
            r, g, b = map(int, arr[y, x])
            ch = charset[idx[y, x]]
            row.append(f"\x1b[38;2;{r};{g};{b}m{ch}")  # 24bit前景色
        out.append("".join(row) + reset)
    print("\n".join(out))


    width = 100
    image = "./b.png"    
    line_scale = 0.55

    
print_color_ascii(image, width, line_scale)


