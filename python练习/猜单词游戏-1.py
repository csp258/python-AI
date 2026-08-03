import random


word_list = [
    "easy", "answer", "python", "computer", "program",
    "student", "teacher", "school", "family", "friend",
    "happy", "beautiful", "important", "different", "because"
]


def get_word_by_difficulty(difficulty):
    if difficulty == 1:
        
        words = [w for w in word_list if len(w) <= 4]
        score = 1
    elif difficulty == 2:
        
        words = [w for w in word_list if 5 <= len(w) <= 7]
        score = 2
    elif difficulty == 3:
        
        words = [w for w in word_list if len(w) > 7]
        score = 3
    else:
        words = word_list
        score = 1
    return random.choice(words), score

print("欢迎参加猜单词游戏")
print("把字母组合成一个正确的单词。")
print("请选择难度等级：1. 简单  2. 中等  3. 困难")

total_score = 0.0

while True:
    
    while True:
        try:
            difficulty = int(input("请输入难度等级（1/2/3）："))
            if difficulty in [1, 2, 3]:
                break
            else:
                print("输入无效，请输入 1、2 或 3。")
        except ValueError:
            print("输入无效，请输入数字 1、2 或 3。")

    
    word, base_score = get_word_by_difficulty(difficulty)
    
    scrambled_word = ''.join(random.sample(word, len(word)))
    print(f"乱序后单词：{scrambled_word}")

    hint_used = False
    
    while True:
        guess = input("请你猜（输入hint可获得单词首字母提示）：").strip().lower()
        if guess == "hint":
            if not hint_used:
                hint_used = True
                print(f"提示：这个单词的首字母是 {word[0]}")
            else:
                print("你已经使用过提示了！")
            continue
        if guess == word:
            if hint_used:
                
                round_score = base_score * 0.5
                print(f"***真棒，你猜对了！（使用了提示，本局得分：{round_score}）***")
            else:
                round_score = base_score
                print("***真棒，你猜对了！***")
            total_score += round_score
            break
        else:
            print("***不正确，请继续。***")

    
    while True:
        choice = input("是否继续（Y/N）：").strip().upper()
        if choice in ['Y', 'N']:
            break
        print("输入无效，请输入 Y 或 N。")

    if choice == 'N':
        break

print(f"猜单词游戏结束！你的总得分是：{total_score}")