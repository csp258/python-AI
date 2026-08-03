from my_utils import *

# 1. 测试字符串工具
test_str = "hello world"
print("=== 字符串工具测试 ===")
print(f"原字符串：{test_str}")
print(f"反转结果：{str_util.str_reverse(test_str)}")
print(f"切片（下标2-7）：{str_util.sub_str(test_str, 2, 7)}")
print(f"去空格结果：{str_util.str_delspace(test_str)}")

# 2. 测试数学工具
print("\n=== 数学工具测试 ===")
num1, num2 = 23, 45
print(f"{num1}和{num2}的较大值：{math_util.max_num(num1, num2)}")
test_num = 10
print(f"{test_num}之前所有正奇数的和：{math_util.sum_oddnum(test_num)}")

# 3. 测试文件处理工具
print("\n=== 文件处理工具测试 ===")
test_file = "test_file.txt"
math_util.append_to_file(test_file, "测试数据1")
math_util.append_to_file(test_file, "测试数据2")
file_util.print_file_info(test_file)