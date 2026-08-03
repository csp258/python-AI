try:
    
    num = int(input("请输入一个整数："))
   
    square = num **2
    print(f"{num}的平方是{square}")
except ValueError as e:
    
    print(f"异常：{e}")
finally:
    
    print("程序结束！")