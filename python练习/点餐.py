print("欢迎来的美食小站")
print("请选择您要点的食物:")
print("1.汉堡")
print("2.披萨")

food_choice = input("请输入您的选择(1/2):")

if food_choice == "1":
    print("您选择了汉堡")
    cheese = input("您是否需要加奶酪?(y/n):")
    bacon = input("您是否需要加培根?(y/n):")
    order = "您的订单: 汉堡"
    if cheese == "y":
        order += " + 奶酪" 
if bacon == "y":
        order += " + 培根"  
        print(order)
elif food_choice == "2":
     print("您选择了披萨")
     seafood = input("您是否需要加海鲜?(y/n):")
order = "您的订单: 披萨"
if seafood == "y":
        order += " + 海鲜" 
        print(order) 
else:
      print("无效选择,请重新运行程序.")