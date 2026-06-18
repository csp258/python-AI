class Student:
    def __init__(self, name, chinese, math, english):
        self.name = name
        self.chinese = chinese
        self.math = math
        self.english = english

    def __str__(self):
        total = self.chinese + self.math + self.english
        return f"姓名: {self.name} 语文: {self.chinese} 数学: {self.math} 英语: {self.english} 总分: {total}"

    def update_score(self, chinese=None, math=None, english=None):
        if chinese is not None:
            self.chinese = chinese
        if math is not None:
            self.math = math
        if english is not None:
            self.english = english


def input_score(subject):
    """带校验的成绩输入"""
    while True:
        try:
            score = int(input(f"请输入学生的{subject}成绩:"))
            if 0 <= score <= 100:
                return score
            print("成绩必须在0-100之间, 请重新输入!")
        except ValueError:
            print("请输入有效的数字!")


class EduManagement:
    system_version = "1.0"
    system_name = "教务管理系统"

    def __init__(self):
        self.student_list = []

    def add_student(self):
        name = input("请输入学生的姓名:")

        for s in self.student_list:
            if s.name == name:
                print("该学生已经存在, 添加失败")
                return

        chinese = input_score("语文")
        math = input_score("数学")
        english = input_score("英语")

        stu = Student(name, chinese, math, english)
        self.student_list.append(stu)
        print("学生信息添加成功 ~")

    def update_student(self):
        name = input("请输入要修改的学生姓名:")

        for s in self.student_list:
            if s.name == name:
                print(f"当前成绩:{s}")

                chinese = input_score("修改后的语文")
                math = input_score("修改后的数学")
                english = input_score("修改后的英语")

                s.update_score(chinese, math, english)
                print("成绩修改成功 ~")
                print(f"修改后的成绩为 {s}")
                return

        print("没有找到该学生")

    def delete_student(self):
        name = input("请输入要删除的学生姓名:")
        for s in self.student_list:
            if s.name == name:
                self.student_list.remove(s)
                print("学生信息删除成功 ~")
                return
        print("未找到该学生, 删除失败")

    def query_student(self):
        name = input("请输入要查询的学生姓名:")

        for s in self.student_list:
            if s.name == name:
                print(f"学生信息:{s}")
                return
        print("未找到该学生 !")

    def list_student(self):
        if not self.student_list:
            print("暂无学生信息")
            return
        for s in self.student_list:
            print(s)

    def run(self):
        print(f"欢迎使用教务管理系统 {EduManagement.system_version}")

        while True:
            print()
            print("# # # # # # # # # # # # #")
            print("1.添加学生   2.修改学生  3.删除学生  4.查询指定学生   5.查询所有学生  6.退出系统")

            choice = input("请选择要执行的操作, 输入1-6:")

            try:
                match choice:
                    case "1":
                        self.add_student()
                    case "2":
                        self.update_student()
                    case "3":
                        self.delete_student()
                    case "4":
                        self.query_student()
                    case "5":
                        self.list_student()
                    case "6":
                        print("Bye ~")
                        break
                    case _:
                        print("输入错误, 请选择1-6之间的菜单功能")
            except Exception as e:
                print(f"程序出错: {e}")

if __name__ == "__main__":
    edu_management = EduManagement()
    edu_management.run()
