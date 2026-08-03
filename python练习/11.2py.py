
with open("diary.txt", "a", encoding="utf-8") as diary_file:
    while True:
      
        content = input("请输入日记内容（输入“结束”停止）：")
       
        if content == "结束":
            break
     
        diary_file.write(content + "\n")
   
    print("你的秘密日记已保存！")