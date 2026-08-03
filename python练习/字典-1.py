# 1. 加载词典文件（D盘的mydict.txt，没有就自动创建）
def load_dict():
    # 词典文件存在D盘，路径固定
    file_path = "D:/mydict.txt"
    # 用空字典存单词和翻译
    word_dict = {}
    try:
        # 尝试打开文件读内容
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # 去掉每行前后的空格和换行
                line = line.strip()
                if line:  # 跳过空行
                    # 按“:”分开英文和中文（比如“banana:香蕉”拆成两个）
                    eng_word, chn_word = line.split(":", 1)
                    word_dict[eng_word.strip()] = chn_word.strip()
    except:
        # 要是文件没找到，就新建一个空文件
        with open(file_path, "w", encoding="utf-8") as f:
            pass
        print("D盘没找到词典文件，已自动新建！")
    return word_dict

# 2. 保存词典到文件（退出时用）
def save_dict(word_dict):
    file_path = "D:/mydict.txt"
    # 把字典里的内容写到文件里，每行是“英文:中文”
    with open(file_path, "w", encoding="utf-8") as f:
        for eng, chn in word_dict.items():
            f.write(f"{eng}:{chn}\n")

# 3. 查询单词
def search(word_dict):
    word = input("请输要查的英文单词：").strip()
    if word in word_dict:
        print(f"✓ {word} 的意思是：{word_dict[word]}")
    else:
        print("✗ 字典里没这个单词哦")

# 4. 添加单词
def add(word_dict):
    word = input("请输要加的英文单词：").strip()
    chn = input("请输对应的中文意思：").strip()
    if word in word_dict:
        print("✗ 这个单词已经在字典里了！")
    else:
        word_dict[word] = chn
        print("✓ 单词添加成功啦")

# 5. 删除单词
def delete(word_dict):
    word = input("请输要删的英文单词：").strip()
    if word in word_dict:
        del word_dict[word]
        print("✓ 单词删除成功！")
    else:
        print("✗ 字典里没这个单词，删不了哦")

# 6. 修改单词
def modify(word_dict):
    word = input("请输要改的英文单词：").strip()
    if word in word_dict:
        # 先显示当前的意思
        print(f"当前意思：{word_dict[word]}")
        new_chn = input("请输新的中文意思：").strip()
        word_dict[word] = new_chn
        print("✓ 单词修改成功！")
    else:
        print("✗ 字典里没这个单词，改不了哦")

# 7. 主程序（菜单界面，用户选功能）
def main():
    print("----------------------")
    print("    英文学习词典")
    print("----------------------")
    # 先加载已有的单词
    my_dict = load_dict()
    
    # 循环显示菜单，直到用户选退出
    while True:
        print("\n选功能（输数字）：")
        print("1. 查单词  2. 加单词  3. 删单词")
        print("4. 改单词  5. 退出")
        choice = input("你的选择：").strip()
        
        # 按用户选的功能做事
        if choice == "1":
            search(my_dict)
        elif choice == "2":
            add(my_dict)
        elif choice == "3":
            delete(my_dict)
        elif choice == "4":
            modify(my_dict)
        elif choice == "5":
            # 退出前保存所有修改
            save_dict(my_dict)
            print("✓ 已保存，退出程序啦！")
            break
        else:
            print("✗ 输错啦！只能输1-5的数字哦")

# 启动程序
if __name__ == "__main__":
    main()