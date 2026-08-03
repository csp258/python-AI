import tkinter as tk
from tkinter import ttk
import calendar
import datetime

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("万年历")
        
        # 顶部控制区
        self.frame_top = ttk.Frame(root)
        self.frame_top.pack(padx=10, pady=10)
        
        # 年份选择
        self.label_year = ttk.Label(self.frame_top, text="年")
        self.label_year.grid(row=0, column=0, padx=5)
        self.year_var = tk.IntVar()
        self.year_spin = ttk.Spinbox(self.frame_top, from_=1900, to=2100, textvariable=self.year_var, width=8)
        self.year_spin.grid(row=0, column=1, padx=5)
        
        # 月份选择
        self.label_month = ttk.Label(self.frame_top, text="月")
        self.label_month.grid(row=0, column=2, padx=5)
        self.month_var = tk.IntVar()
        self.month_spin = ttk.Spinbox(self.frame_top, from_=1, to=12, textvariable=self.month_var, width=5)
        self.month_spin.grid(row=0, column=3, padx=5)
        
        # 日期选择
        self.label_day = ttk.Label(self.frame_top, text="日")
        self.label_day.grid(row=0, column=4, padx=5)
        self.day_var = tk.IntVar()
        self.day_spin = ttk.Spinbox(self.frame_top, from_=1, to=31, textvariable=self.day_var, width=5)
        self.day_spin.grid(row=0, column=5, padx=5)
        
        # 更新按钮
        self.btn_update = ttk.Button(self.frame_top, text="更新日历", command=self.update_calendar)
        self.btn_update.grid(row=0, column=6, padx=5)
        
        # 星期标题行
        self.frame_calendar = ttk.Frame(root)
        self.frame_calendar.pack(padx=10, pady=10)
        weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        for i, day in enumerate(weekdays):
            ttk.Label(self.frame_calendar, text=day, width=6).grid(row=0, column=i)
        
        # 底部月份切换按钮区
        self.frame_bottom = ttk.Frame(root)
        self.frame_bottom.pack(padx=10, pady=10)
        self.btn_prev = ttk.Button(self.frame_bottom, text="上月", command=self.prev_month)
        self.btn_prev.grid(row=0, column=0, padx=5)
        self.btn_next = ttk.Button(self.frame_bottom, text="下月", command=self.next_month)
        self.btn_next.grid(row=0, column=1, padx=5)
        
        # 初始化日期为当前日期
        now = datetime.datetime.now()
        self.year_var.set(now.year)
        self.month_var.set(now.month)
        self.day_var.set(now.day)
        self.update_calendar()

    def update_calendar(self):
        # 清空旧的日期格子
        for widget in self.frame_calendar.winfo_children():
            if widget.grid_info()["row"] > 0:
                widget.destroy()
        
        year = self.year_var.get()
        month = self.month_var.get()
        
        # 获取当月第一天是星期几和当月天数
        first_day, num_days = calendar.monthrange(year, month)
        # 转换为周日为起始的星期（calendar模块周一为0，这里改为周日为0）
        first_day = (first_day + 1) % 7
        
        day = 1
        row = 1
        col = first_day
        
        while day <= num_days:
            ttk.Label(self.frame_calendar, text=str(day), width=6).grid(row=row, column=col)
            day += 1
            col += 1
            if col > 6:
                col = 0
                row += 1

    def prev_month(self):
        # 切换到上月
        year = self.year_var.get()
        month = self.month_var.get()
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        self.year_var.set(year)
        self.month_var.set(month)
        self.update_calendar()

    def next_month(self):
        # 切换到下月
        year = self.year_var.get()
        month = self.month_var.get()
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        self.year_var.set(year)
        self.month_var.set(month)
        self.update_calendar()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()