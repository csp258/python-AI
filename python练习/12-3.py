while True:
    try:
        
        age = int(input("请输入年龄（0~120）："))
        
        
        if not (0 <= age <= 120):
            raise ValueError("输入的年龄不在0到120之间，请重新输入！")
        
        
        print(f"输入的年龄为:{age}")
        break  
        
    except ValueError as e:
        
        print(f"异常：{e}")