import time

import cv2
import numpy as np
from collections import deque
from tkinter import Tk, Label, Entry, Button, StringVar, Toplevel, messagebox

print(
    '''
 ▄▄▄▄ ▓██   ██▓    ▒█████   ██▓███   ██▓ █    ██  ███▄ ▄███▓    
▓█████▄▒██  ██▒   ▒██▒  ██▒▓██░  ██▒▓██▒ ██  ▓██▒▓██▒▀█▀ ██▒
▒██▒ ▄██▒██ ██░   ▒██░  ██▒▓██░ ██▓▒▒██▒▓██  ▒██░▓██    ▓██░
▒██░█▀  ░ ▐██▓░   ▒██   ██░▒██▄█▓▒ ▒░██░▓▓█  ░██░▒██    ▒██ 
░▓█  ▀█▓░ ██▒▓░   ░ ████▓▒░▒██▒ ░  ░░██░▒▒█████▓ ▒██▒   ░██▒
░▒▓███▀▒ ██▒▒▒    ░ ▒░▒░▒░ ▒▓▒░ ░  ░░▓  ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░
▒░▒   ░▓██ ░▒░      ░ ▒ ▒░ ░▒ ░      ▒ ░░░▒░ ░ ░ ░  ░      ░
 ░    ░▒ ▒ ░░     ░ ░ ░ ▒  ░░        ▒ ░ ░░░ ░ ░ ░      ░   
 ░     ░ ░            ░ ░            ░     ░            ░   
      ░░ ░           
    '''
    + " " * 25 + "_______                                       __                          \n"
    + " " * 25 + "/       \\                                     /  |                         \n"
    + " " * 25 + "$$$$$$$  | __    __         ______    ______  $$/  __    __  _____  ____  \n"
    + " " * 25 + "$$ |__$$ |/  |  /  |       /      \\  /      \\ /  |/  |  /  |/     \\/    \\ \n"
    + " " * 25 + "$$    $$< $$ |  $$ |      /$$$$$$  |/$$$$$$  |$$ |$$ |  $$ |$$$$$$ $$$$  |\n"
    + " " * 25 + "$$$$$$$  |$$ |  $$ |      $$ |  $$ |$$ |  $$ |$$ |$$ |  $$ |$$ | $$ | $$ |\n"
    + " " * 25 + "$$ |__$$ |$$ \\__$$ |      $$ \\__$$ |$$ |__$$ |$$ |$$ \\__$$ |$$ | $$ | $$ |\n"
    + " " * 25 + "$$    $$/ $$    $$ |      $$    $$/ $$    $$/ $$ |$$    $$/ $$ | $$ | $$ |\n"
    + " " * 25 + "$$$$$$$/   $$$$$$$ |       $$$$$$/  $$$$$$$/  $$/  $$$$$$/  $$/  $$/  $$/ \n"
    + " " * 25 + "          /  \\__$$ |                $$ |                                  \n"
    + " " * 25 + "          $$    $$/                 $$ |                                  \n"
    + " " * 25 + "           $$$$$$/                  $$/          "
)

input("按回车键继续...")

# 用于存储路径像素和建筑物
path_pixels = set()
buildings = {}
clicked_points = []
scale = 1.0  # 缩放比例
path_color = (224, 75, 142)
color_tolerance = 30
selected_points = {"start": None, "end": None}

# 判断像素是否为路径
def is_path_pixel(pixel):
    return all(abs(int(pixel[i]) - path_color[i]) <= color_tolerance for i in range(3))

# 提取路径像素
def extract_path_pixels(image):
    global path_pixels
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            if is_path_pixel(image[y, x]):
                path_pixels.add((x, y))
    print(f"路径像素检测完成，共检测到 {len(path_pixels)} 个路径点。")

# 找到最近的路径点
def find_nearest_path_point(x, y):
    if not path_pixels:
        return None
    nearest_point = min(path_pixels, key=lambda p: (p[0] - x)**2 + (p[1] - y)**2)
    return nearest_point

# 寻找最短路径 (BFS)
def find_shortest_path(start, end):
    if start not in path_pixels or end not in path_pixels:
        print("起点或终点不在路径上。")
        return None

    queue = deque([start])
    visited = set()
    visited.add(start)
    parent = {start: None}

    while queue:
        current = queue.popleft()
        if current == end:
            path = []
            while current:
                path.append(current)
                current = parent[current]
            path.reverse()
            return path

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor in path_pixels and neighbor not in visited:
                queue.append(neighbor)
                visited.add(neighbor)
                parent[neighbor] = current

    return None

# 鼠标点击事件
def on_click(event, x, y, flags, param):
    global resized_image, scale, selected_points
    if event == cv2.EVENT_LBUTTONDOWN:
        original_x, original_y = int(x / scale), int(y / scale)
        nearest_point = find_nearest_path_point(original_x, original_y)
        if nearest_point:
            key = "start" if selected_points["start"] is None else "end"
            selected_points[key] = nearest_point
            # 在图像上标注
            cv2.circle(resized_image, (int(nearest_point[0] * scale), int(nearest_point[1] * scale)), 5, (0, 255, 0), -1)
            cv2.putText(resized_image, key.upper(), (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow("Map", resized_image)

            if selected_points["start"] and selected_points["end"]:
                calculate_path()

# 计算并绘制路径
def calculate_path():
    global resized_image, scale, selected_points
    start = selected_points["start"]
    end = selected_points["end"]
    shortest_path = find_shortest_path(start, end)
    if shortest_path:
        for i in range(1, len(shortest_path)):
            p1 = (int(shortest_path[i - 1][0] * scale), int(shortest_path[i - 1][1] * scale))
            p2 = (int(shortest_path[i][0] * scale), int(shortest_path[i][1] * scale))
            cv2.line(resized_image, p1, p2, (0, 0, 255), 2)
        cv2.imshow("Map", resized_image)
        print(f"最短路径长度: {len(shortest_path)}")
        messagebox.showinfo("结果", "最短路径计算完成！")
    else:
        messagebox.showerror("错误", "路径被阻塞，无法计算最短路径。")

# 创建图形化界面
def create_gui():
    root = Toplevel()
    root.title("建筑物路径规划")

    Label(root, text="点击图像标注起点和终点").pack(pady=10)

    def reset_selection():
        global resized_image, scale, selected_points
        selected_points = {"start": None, "end": None}
        resized_image = cv2.resize(image, (int(image.shape[1] * scale), int(image.shape[0] * scale)))
        cv2.imshow("Map", resized_image)

    Button(root, text="重置选择", command=reset_selection).pack(pady=10)
    Button(root, text="退出", command=lambda: root.destroy()).pack(pady=10)

# 主程序
map_path = "map.png"
image = cv2.imread(map_path)

if image is None:
    print("无法加载地图图像，请检查路径。")
else:
    print(f"图像加载成功，尺寸：{image.shape}")

    max_width, max_height = 1400, 1400
    scale = min(max_width / image.shape[1], max_height / image.shape[0])
    resized_image = cv2.resize(image, (int(image.shape[1] * scale), int(image.shape[0] * scale)))

    extract_path_pixels(image)

    # 打开图像窗口
    cv2.imshow("Map", resized_image)
    cv2.setMouseCallback("Map", on_click)

    # 创建 GUI
    root = Tk()
    root.title("路径规划工具")
    Button(root, text="更改", command=create_gui).pack(pady=20)
    root.mainloop()

    cv2.waitKey(0)
    cv2.destroyAllWindows()