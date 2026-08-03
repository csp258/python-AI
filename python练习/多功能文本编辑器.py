import tkinter as tk
from tkinter import filedialog, messagebox #文本对话框(打开/保存文件用) 消息框

# 主窗口 root就是给窗口起的名字
root = tk.Tk()
root.title("多功能文本编辑器-基础版")
root.geometry("800x600") #设置窗口大小

# 文本框
text = tk.Text(root, undo=True)
text.pack(fill=tk.BOTH, expand=True)

# 当前文件路径
current_file = None

# 新建文件
def new_file():
    global current_file
    text.delete(1.0, tk.END)
    current_file = None
    root.title("未命名 - 文本编辑器")

# 打开文件
def open_file():
    global current_file
    path = filedialog.askopenfilename(
        filetypes=[("文本文档", "*.txt"), ("所有文件", "*.*")]
    )
    if path:
        current_file = path
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            text.delete(1.0, tk.END)
            text.insert(tk.END, content)
        root.title(f"{current_file} - 文本编辑器")

# 保存文件
def save_file():
    global current_file
    if current_file:
        content = text.get(1.0, tk.END)
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("提示", "保存成功！")
    else:
        save_as_file()

# 另存为
def save_as_file():
    global current_file
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("文本文档", "*.txt"), ("所有文件", "*.*")]
    )
    if path:
        current_file = path
        content = text.get(1.0, tk.END)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        root.title(f"{current_file} - 文本编辑器")
        messagebox.showinfo("提示", "另存为成功！")

# 菜单
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="新建", command=new_file)
file_menu.add_command(label="打开", command=open_file)
file_menu.add_command(label="保存", command=save_file)
file_menu.add_command(label="另存为", command=save_as_file)
file_menu.add_separator()
file_menu.add_command(label="退出", command=root.quit)
menu_bar.add_cascade(label="文件", menu=file_menu)

root.config(menu=menu_bar)
root.mainloop()