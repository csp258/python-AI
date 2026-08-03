import csv
from math import pow, sqrt

# 1.读取用户对电影的评分数据，存入字典data，格式为{用户ID: {电影ID: 评分,...},...}
data = {}  # 构建用户ID-电影ID-评分字典
with open(r'D:\下载\visual studio code\text\实验13 电影推荐系统\lab13\merged.csv', encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)  # 跳过标题行
    # reader是一个可迭代对象，可通过for循环逐行读取CSV文件的内容。每迭代一次，返回一行数据，格式为列表
    for row in reader:
        user_id = row[0]
        movie_id = row[1]
        rating = float(row[2])

    #初始化用户字典(如果用户不存在)
        if user_id not in data: 
            data[user_id] = {} 
        data[user_id][movie_id] = rating  # 不管电影是否存在，直接赋值就行



# 2.计算两个用户之间的欧氏距离相似度，相似度值 = 1/(1+欧氏距离)
def Euclidean(user1, user2):
    # 取出两位用户分别评论过的电影
    user1_data = data[user1]
    user2_data = data[user2]
    # 找到两位用户都评论过的电影
    common_movies = user1_data.keys() & user2_data.keys()
    # 计算相似度
    if not common_movies:
        return 0  # 没有共同评论电影，相似度为0
    # 计算欧氏距离
    distance = 0.0
    for movie_id in common_movies:
        distance += pow(user1_data[movie_id] - user2_data[movie_id], 2)
    distance = sqrt(distance)
    # 计算相似度
    similarity = 1 / (1 + distance)
    return similarity  # 相似度值 = 1/(1+distance)



# 3.获取最相似用户：找出与指定用户最相似的前 10 个用户
def top10_similar(userID):
    res = []  # 构建用户 - 相似度列表，格式为[(用户ID, 相似度), ...]
    # 遍历所有用户，计算相似度
    for user_id in data:
        if user_id != userID:  # 排除用户自己
            similarity = Euclidean(userID, user_id)
            res.append((user_id, similarity))  # 存入用户ID-相似度元组
    # 按相似度降序排序
    res.sort(key=lambda x: x[1], reverse=True)
    # 取前 10 个用户
    res = res[:10]
    return res  # 返回用户ID-相似度元组列表




# 4.推荐电影:为指定用户推荐k部电影
def recommend(user, k=5):
    # 找到最相似的 10 个用户
    similar_users = top10_similar(user)
    
    # 存储每部电影的加权总分
    recomm_scores = {}
    for sim_user, similarity in similar_users:
        for movie_id, rating in data[sim_user].items():
            if movie_id not in data[user]:  # 排除用户已看过的电影
                weighted_rating = similarity * rating
                if movie_id in recomm_scores:
                    recomm_scores[movie_id] += weighted_rating
                else:
                    recomm_scores[movie_id] = weighted_rating
    
    # 按推荐分数降序排序，得到 [(movie_id, score), ...]
    sorted_items = sorted(recomm_scores.items(), key=lambda x: x[1], reverse=True)
    # 直接返回前k个元组，满足 [(电影ID, 推荐分数)] 格式
    return sorted_items[:k]


# 5.测试推荐系统
if __name__ == '__main__':
    test_user = '1'
    if test_user not in data:
        print(f"用户{test_user}不存在！")
    else:
        recommended_movies = recommend(test_user, k=5)
        print("电影推荐列表：", recommended_movies)
       
