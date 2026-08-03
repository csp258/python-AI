import tkinter as tk
from tkinter import filedialog, messagebox

root = tk.Tk()
root.title("多功能文本编辑器-完整版")
root.geometry("800x600")

text = tk.Text(root, undo=True)
text.pack(fill=tk.BOTH, expand=True)
current_file = None

# ========== 文件功能 ==========
def new_file():
    global current_file
    text.delete(1.0, tk.END)
    current_file = None
    root.title("未命名 - 文本编辑器")

def open_file():
    global current_file
    path = filedialog.askopenfilename(filetypes=[("文本文档", "*.txt"), ("所有文件", "*.*")])
    if path:
        current_file = path
        with open(path, "r", encoding="utf-8") as f:
            text.delete(1.0, tk.END)
            text.insert(tk.END, f.read())
        root.title(f"{current_file} - 文本编辑器")

def save_file():
    global current_file
    if current_file:
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(text.get(1.0, tk.END))
        messagebox.showinfo("提示", "保存成功")
    else:
        save_as_file()

def save_as_file():
    global current_file
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文档", "*.txt")])
    if path:
        current_file = path
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.get(1.0, tk.END))
        root.title(f"{current_file} - 文本编辑器")
        messagebox.showinfo("提示", "另存为成功")

# ========== 编辑操作 ==========
def undo():
    try:
        text.edit_undo()
    except:
        pass

def redo():
    try:
        text.edit_redo()
    except:
        pass

def cut():
    text.event_generate("<<Cut>>")

def copy():
    text.event_generate("<<Copy>>")

def paste():
    text.event_generate("<<Paste>>")

def select_all():
    text.tag_add(tk.SEL, 1.0, tk.END)

def find_text():
    def search():
        target = entry.get()
        content = text.get(1.0, tk.END)
        if target in content:
            messagebox.showinfo("查找", f"找到：{target}")
        else:
            messagebox.showinfo("查找", f"未找到：{target}")
        top.destroy()

    top = tk.Toplevel(root)
    top.title("查找")
    tk.Label(top, text="查找内容：").pack(side=tk.LEFT)
    entry = tk.Entry(top)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(top, text="查找", command=search).pack(side=tk.LEFT)

# ========== 关于 ==========
def about_author():
    messagebox.showinfo("作者", "姓名：陈仕鹏\n学号：2440131237")

def about_soft():
    messagebox.showinfo("关于", "多功能文本编辑器\n基于tkinter实现\n实验4")

# ========== 菜单构建 ==========
menu_bar = tk.Menu(root)

# 文件菜单
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="新建", command=new_file)
file_menu.add_command(label="打开", command=open_file)
file_menu.add_command(label="保存", command=save_file)
file_menu.add_command(label="另存为", command=save_as_file)
file_menu.add_separator()
file_menu.add_command(label="退出", command=root.quit)
menu_bar.add_cascade(label="文件", menu=file_menu)

# 操作菜单
edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="撤销", command=undo)
edit_menu.add_command(label="重做", command=redo)
edit_menu.add_separator()
edit_menu.add_command(label="剪切", command=cut)
edit_menu.add_command(label="复制", command=copy)
edit_menu.add_command(label="粘贴", command=paste)
edit_menu.add_separator()
edit_menu.add_command(label="查找", command=find_text)
edit_menu.add_command(label="全选", command=select_all)
menu_bar.add_cascade(label="操作", menu=edit_menu)

# About菜单
about_menu = tk.Menu(menu_bar, tearoff=0)
about_menu.add_command(label="作者", command=about_author)
about_menu.add_command(label="关于", command=about_soft)
menu_bar.add_cascade(label="About", menu=about_menu)

root.config(menu=menu_bar)
root.mainloop()