# # # # # a = 10
# # # # # b =20
# # # # # temp = a #emp = 10
# # # # # a = b # a = 20
# # # # # b = temp # b = 10

# # # # # print(a)
# # # # # print(b)

# # # # name = "涛哥"
# # # # age = 18
# # # # pro = "软件工程"
# # # # hobby = "python,java"
# # # # # print("大家好,我是%s,今年%s,学习的专业是%s,爱好是%s"  % (name,age,pro, hobby))

# # # # print(f"大家好,我叫{name},今年{age},我的专业是{pro},爱好是{hobby}")


# # # password = input("请输入密码")
# # # print(f"密码正确,{password}")
# # score = 680
# # if score > 650:
# #     print("欢迎加入北京大学")

# i = 1
# num = 0
# while i <= 100:
#     i += 1
#     if i % 2==0:
        # num += i
# print(num)     


# s = []
# s.insert(0,1)
# print(s)

# def circle_area_len(r):
#     """
#     """
#     area1 = 3.14 * r**2
#     area2 = 2 * 3.14 * r
#     return area1,area2
   
    

# area,len = circle_area_len(10)
# print(area,len)

# def reg_stu(name, age, gender = '男',city = "北京"):
#     print(f"注册成功,姓名:{name},年龄:{age},性别:{gender},城市:{city}")
#     return{'name':name, 'ang':age, 'gender':gender, 'city':city}

# stu =reg_stu('王林',18, gender="女")
# print(stu)

# def calc_data(*args):
#     min_data = min(args)
#     max_data = max(args)
#     avg_data = round(sum(args) / len(args),1)
#     return min_data,max_data,avg_data

# print(calc_data(2,8,58,89,100))

# def calc_order_cost(*args,coupon,score,express):
#     total_price = [goods[1] * goods[2] for goods in args]
#     total_cost = sum(total_price)

#     if total_cost >= 5000 and coupon <= 5000:
#         total_cost -= coupon

#     if total_cost >= 5000 and score // 100 <= total_cost:
#         total_cost -= score
    

#     total_cost += express
#     return total_cost


# from random import randint
# for i in range(5):
#     print(randint(1,20))
