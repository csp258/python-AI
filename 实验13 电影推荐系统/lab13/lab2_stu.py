import csv
from math import pow, sqrt

# 1. 读取电影名称映射，DictReader兼容片名带逗号
movie_name_map = {}
with open(r'D:\下载\visual studio code\text\实验13 电影推荐系统\lab13\movies.csv', encoding='UTF-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        mid = row['movieId']
        mname = row['title']
        movie_name_map[mid] = mname

# 2. 读取用户评分数据 merged.csv
data = {}
with open(r'D:\下载\visual studio code\text\实验13 电影推荐系统\lab13\merged.csv', encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        user_id = row[0]
        movie_id = row[1]
        rating = float(row[2])
        if user_id not in data:
            data[user_id] = {}
        data[user_id][movie_id] = rating

# 3. 欧氏距离相似度
def Euclidean(user1, user2):
    user1_data = data[user1]
    user2_data = data[user2]
    common_movies = user1_data.keys() & user2_data.keys()
    if not common_movies:
        return 0.0
    distance = 0.0
    for movie in common_movies:
        distance += pow(user1_data[movie] - user2_data[movie], 2)
    euclidean_dist = sqrt(distance)
    similarity = 1 / (1 + euclidean_dist)
    return similarity

# 4. 获取前10相似用户
def top10_similar(userID):
    res = []
    for user in data:
        if user != userID:
            sim = Euclidean(userID, user)
            res.append((user, sim))
    res.sort(key=lambda x: x[1], reverse=True)
    return res[:10]

# 5. 推荐函数，固定返回 [(movie_id, score)]
def recommend(user, k=5):
    similar_users = top10_similar(user)
    recomm_scores = {}
    for sim_user, similarity in similar_users:
        for movie_id, rating in data[sim_user].items():
            if movie_id not in data[user]:
                weighted_rating = similarity * rating
                if movie_id in recomm_scores:
                    recomm_scores[movie_id] += weighted_rating
                else:
                    recomm_scores[movie_id] = weighted_rating
    # 排序：key=x[1] 按分数降序，返回(电影ID,分数)
    sorted_items = sorted(recomm_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:k]

# 6. 主程序（带调试+容错）
if __name__ == "__main__":
    target_user = input("请告诉我，为哪位用户进行电影推荐：")
    if target_user not in data:
        print(f"错误：用户 {target_user} 不存在！")
    else:
        rec_list = recommend(target_user, k=5)
        print("推荐结果如下所示：")
        # 严格顺序：movie_id在前，score在后，增加容错判断
        for movie_id, score in rec_list:
            if movie_id in movie_name_map:
                print(movie_name_map[movie_id])
            else:
                print(f"暂无片名，电影ID：{movie_id}")