
friend_list = []

while True:
    print("\n好友管理系统功能菜单：")
    print("1. 添加好友")
    print("2. 删除好友")
    print("3. 修改好友")
    print("4. 展示好友")
    print("5. 退出")
    
    choice = input("请输入功能序号：")
    
    if choice == "1":
        name = input("请输入要添加的好友姓名：")
        if name in friend_list:
            print("该好友已存在")
        else:
            friend_list.append(name)
            print("好友添加成功")
    elif choice == "2":
        name = input("请输入删除好友姓名：")
        if name in friend_list:
            friend_list.remove(name)
            print("删除成功")
        else:
            print("该好友不存在")
    elif choice == "3":
        old_name = input("请输入要修改的好友姓名：")
        if old_name in friend_list:
            new_name = input("请输入修改后的好友姓名：")
            index = friend_list.index(old_name)
            friend_list[index] = new_name
            print("修改成功")
        else:
            print("该好友不存在")
    elif choice == "4":
        if not friend_list:
            print("好友列表为空")
        else:
            print("好友列表：", friend_list)
    elif choice == "5":
        print("已退出好友管理系统")
        break
    else:
        print("输入序号无效，请重新输入")