import os

# 1.设计Student类
class Student:  # 定义一个学生类
    # 定义构造方法，定义实例变量name，ID，score_c，score_m，score_e，sum为默认值
    def __init__(self):
        self.name = ""
        self.ID = ""
        self.score_c = 0  # 语文成绩
        self.score_m = 0  # 数学成绩
        self.score_e = 0  # 英语成绩
        self.sum = 0      # 总分

    # 定义sumscore(self)：计算总分
    def sumscore(self):
        self.sum = self.score_c + self.score_m + self.score_e

    # 定义input(self)：从控制台输入学生信息，并调用sumscore(self)计算总分
    def input(self):
        self.ID = input("请输入学生的ID：")
        self.name = input("请输入学生的姓名：")
        # 异常处理：确保成绩输入为数字
        while True:
            try:
                self.score_c = int(input("请输入学生语文成绩："))
                self.score_m = int(input("请输入学生数学成绩："))
                self.score_e = int(input("请输入学生英语成绩："))
                break
            except ValueError:
                print("成绩请输入整数！重新输入")
        # 调用计算总分方法
        self.sumscore()

    # 定义output(self,file_object)：将学生信息写入目标文件
    def output(self, file_object):
        # 按空格分隔写入，与读取格式一致
        file_str = f"{self.ID} {self.name} {self.score_c} {self.score_m} {self.score_e} {self.sum}\n"
        file_object.write(file_str)

# 2.学号查询
def searchByID(stulist, ID):  # 按学号查找看是否学号已经存在
    for item in stulist:
        if item.ID == ID:
            return True
    return False  # 补充返回False，避免无返回值

# 3.添加学生信息
def Add(stulist, stu):
    if searchByID(stulist, stu.ID) == True:
        print("学号已经存在！")
        return False
    stulist.append(stu)  # 操作list
    file_object = open("students.txt", "a", encoding="utf-8")  # 加utf-8避免中文乱码
    stu.output(file_object)
    file_object.close()
    print("添加成功！")
    return True

# 4.定义Del(stulist, ID)：删除学生信息（采用覆盖写）
def Del(stulist, ID):
    if not searchByID(stulist, ID):
        print("学号不存在，删除失败！")
        return False
    # 从列表中删除对应学生
    for i in range(len(stulist)):
        if stulist[i].ID == ID:
            del stulist[i]
            break
    # 覆盖写入文件（先清空再重新写入所有剩余学生）
    file_object = open("students.txt", "w", encoding="utf-8")
    for stu in stulist:
        stu.output(file_object)
    file_object.close()
    print("删除成功！")
    return True

# 5.定义Change(stulist, ID)：修改学生信息（先删除再添加）
def Change(stulist, ID):
    if not searchByID(stulist, ID):
        print("学号不存在，修改失败！")
        return False
    # 先删除原信息
    Del(stulist, ID)
    # 输入新信息并添加
    new_stu = Student()
    new_stu.ID = ID  # 保持学号不变
    new_stu.name = input("请输入修改后的姓名：")
    while True:
        try:
            new_stu.score_c = int(input("请输入修改后的语文成绩："))
            new_stu.score_m = int(input("请输入修改后的数学成绩："))
            new_stu.score_e = int(input("请输入修改后的英语成绩："))
            break
        except ValueError:
            print("成绩请输入整数！重新输入")
    new_stu.sumscore()
    stulist.append(new_stu)
    # 覆盖写入文件
    file_object = open("students.txt", "w", encoding="utf-8")
    for stu in stulist:
        stu.output(file_object)
    file_object.close()
    print("修改成功！")
    return True

# 6.定义Search(stulist, ID)：查询学生信息（查询后需展示出来）
def Search(stulist, ID):
    if not searchByID(stulist, ID):
        print("学号不存在，查询失败！")
        return False
    # 遍历找到对应学生并展示
    print("学号\t姓名\t语文\t数学\t英语\t总分")
    for stu in stulist:
        if stu.ID == ID:
            print(f"{stu.ID}\t{stu.name}\t{stu.score_c}\t{stu.score_m}\t{stu.score_e}\t{stu.sum}")
    print("查询成功！")
    return True

# 7.定义display(stulist)：显示所有学生信息
def display(stulist):
    if len(stulist) == 0:
        print("暂无学生信息！")
        return
    # 格式化展示表头和所有学生信息
    print("学号\t姓名\t语文\t数学\t英语\t总分")
    for stu in stulist:
        print(f"{stu.ID}\t{stu.name}\t{stu.score_c}\t{stu.score_m}\t{stu.score_e}\t{stu.sum}")

# 8.成绩排序
def Sort(stulist):
    if len(stulist) <= 1:
        display(stulist)
        return
    selectionSort(stulist)
    print("按总分从高到低排序结果：")
    display(stulist)

def selectionSort(stulist):  # [stu1(45),stu2(67),stu3(89)]--->[stu3,stu2,stu1]
    for i in range(len(stulist)-1):
        max_idx = i  # 先假设当前位置是最大值的索引
        for j in range(i+1, len(stulist)):  # 内层循环：找到i之后的最大值的索引
            if stulist[j].sum > stulist[max_idx].sum:
                max_idx = j
        # 外层循环末尾：只交换一次（把找到的最大值放到i位置）
        stulist[i], stulist[max_idx] = stulist[max_idx], stulist[i]

# 9.初始化函数：文件内容-->列表
def Init(stulist):  # 初始化函数
    print("初始化......")
    if os.path.exists('students.txt'):
        file_object = open('students.txt', 'r', encoding="utf-8")
        for line in file_object:
            stu = Student()
            line = line.strip("\n")
            if not line:  # 跳过空行
                continue
            s = line.split(" ")  # 按空格分隔形成列表
            # 根据文件中的学生数据，创建Student对象，并将Student对象存入列表中
            stu.ID = s[0]
            stu.name = s[1]
            stu.score_c = int(s[2])
            stu.score_m = int(s[3])
            stu.score_e = int(s[4])
            stu.sum = int(s[5])
            stulist.append(stu)
        file_object.close()
        print("初始化成功！")
    else:
        print("未找到学生文件，已创建空列表！")

# 10.设计主函数
# 主菜单
def main():
    while True:
        print("*********************")
        print("--------菜单---------")
        print("增加学生信息--------1")
        print("查找学生信息--------2")
        print("删除学生信息--------3")
        print("修改学生信息--------4")
        print("所有学生信息--------5")
        print("按照分数排序--------6")
        print("退出程序------------0")
        print("*********************")

        nChoose = input("请输入你的选择：")
        if nChoose == "1":
            stu = Student()
            stu.input()
            Add(stulist, stu)
        elif nChoose == "2":
            ID = input("请输入学生的ID：")
            Search(stulist, ID)
        elif nChoose == "3":
            ID = input("请输入要删除的学生ID：")
            Del(stulist, ID)
        elif nChoose == "4":
            ID = input("请输入要修改的学生ID：")
            Change(stulist, ID)
        elif nChoose == "5":
            display(stulist)
        elif nChoose == "6":
            Sort(stulist)
        elif nChoose == "0":
            print("程序已退出，感谢使用！")
            break
        else:
            print("输入错误，请选择0-6的数字！")

# 主程序
if __name__ == '__main__':
    stulist = []
    Init(stulist)
    main()