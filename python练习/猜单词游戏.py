import random
word_list=['easy','answer','python','computer','program','hello','world']
print("欢迎参加猜单词游戏")
print("把字母组合成一个正确单词")

while True:
    word = random.choice(word_list)
    scrambled_word = ''.join(random.sample(word, len(word)))
    print(f"\n乱序后的单词:{scrambled_word}")

    while True:
        guess = input("让你猜:").strip().lower()
        if guess == word: 
            print("***真棒,你猜对了!***")
            break
        else:
            print("***不正确,请继续***")

    while True:
        choice = input("是否继续(Y/N):").strip().upper()
        if choice in['Y','N']:
                    break
        print("输入无效,请输入Y或N")
    if choice== 'N':
            break
print("\n猜单词游戏结束")


