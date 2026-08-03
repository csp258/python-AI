string_list = ["apple", "banana", "pear", "watermelon"]

sorted_list = sorted(string_list, key=lambda a: len(a))
print(sorted_list)