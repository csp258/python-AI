try:
    print("-------------------------------")
    print(my_name)
    print("-------------------------------")
# except NameError as e: #捕获的是NameError 类型的异常
    # print(f"程序运行出错,请联系管理员 ~ 异常信息:{e}")

except Exception as e: #捕获的是所有异常类型的信息
    print(f"程序运行出错,请联系管理员,错误信息为 {e}")
finally: #无论程序是否正常运行,finally代码块中的代码都会运行
    print("资源释放")