
text = "This is a simple text. This text is used for word frequency counting. A word is a unit of language."


lower_text = text.lower()

punctuation = ".,"
clean_text = ""
for char in lower_text:
    if char not in punctuation:  
        clean_text += char


words = clean_text.split() 


word_count = {}  
for word in words:
    if word in word_count:
       
        word_count[word] = word_count[word] + 1
    else:
        
        word_count[word] = 1


print("单词出现次数统计：")
for word, count in word_count.items():
    print(f"{word} 出现了 {count} 次")