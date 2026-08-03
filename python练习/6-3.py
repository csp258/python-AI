# 定义正确的用户名和密码
correct_username = "user"
correct_password = "123456"

# 进入循环，只要登录不成功就一直循环
while True:
    # 提示用户输入用户名
    username = input("请输入用户名：")
    # 提示用户输入密码
    password = input("请输入用户密码：")
    
    # 判断用户名和密码是否都正确
    if username == correct_username and password == correct_password:
        print("欢迎光临")
        # 如果正确，使用 break 跳出循环，结束程序
        break
    else:
        # 如果错误，提示用户重新输入
        print("用户名或密码错误，请重新输入")