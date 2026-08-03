def has(lst):
    return len(lst) != len(set(lst))


lists = [
    [1, 2, 3, 4, 5, 6],
    [1, 2, 3, 4, 4, 5, 6],
    [1, 2, 3, 4, 4, 5, 5, 6, 6]
]

for lst in lists:
    print(f"列表 {lst}是否存在重复元素：{has(lst)}")