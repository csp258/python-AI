tuple1 = ('p', 'y', 't', ['o', 'n'])
tuple1[3].append('h')
result = ''.join([tuple1[0], tuple1[1], tuple1[2]] + tuple1[3])
print(result)