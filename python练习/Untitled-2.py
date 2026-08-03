correct_username = "aaa"
correct_password = "123456"
correct_captcha = "qwer"

captcha = input("请输入验证码:")
if captcha != correct_captcha:
    print("验证码错误,登录失败")
else:
   username = input("请输入用户名:")
   password = input("请输入密码:")
   if username == correct_username and password == correct_password:
       print("登录成功!")
   else:
       print(" 用户名和密码错误,登录失败!")