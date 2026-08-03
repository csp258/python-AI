year = int(input("请输入年份："))

if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
    if year % 100 == 0 and year % 400 == 0:
        print(f"{year}是世纪闰年")
    else:
        print(f"{year}是普通闰年")
else:
    print(f"{year}不是闰年")