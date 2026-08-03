def fact(n,m):
    s = 1
    for i in range(n,m+1):
        s*= i
        print(s)
    return s
fact(5, 10)