# 导入所有需要的包
from sklearn import datasets
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB #导入多项式贝叶斯算法包(也有其他选择，见P311)
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

#留言板案例的Scikit-Learn实现
def testNB_skl():
    posting=['my dog has flea problems help please','maybe not take him to dog park stupid',
                'my dalmation is  so cute I love him','stop posting stupid worthless garbage',
                'mr licks ate my steak how to stop him','quit buying worthless dog food stupid']
    classVec = [0,1,0,1,0,1]
    #交叉验证选择训练集和测试集
    train_data,test_data,train_y,test_y=train_test_split(posting,classVec,test_size=0.2,train_size=0.8)
    #生成文本的词频矩阵
    vectorizer=CountVectorizer()#CountVectorizer用于词袋模型统计词频
    wordX=vectorizer.fit_transform(train_data)
    #训练分类器
    clf = MultinomialNB().fit(wordX,train_y)
    #预测测试集的分类结果
    test_wordX=vectorizer.transform(test_data).toarray()
    predicted = clf.predict(test_wordX) #预测
    for doc,category in zip(test_data,predicted):
        print(doc,":",category)
    #在测试集上的性能评估
    classTarget_names = ['正常言论 0','侮辱性言论 1']
    print(classification_report(test_y,predicted,target_names=classTarget_names))
testNB_skl()

#垃圾邮件过滤的Scikit-Learn实现
def spamTest_skl():
    #加载email文件夹下的数据
    base_data = datasets.load_files(r"D:\下载\visual studio code\text\实验14 基于朴素贝叶斯算法的文本分类\lab14\email/")
    #交叉验证选择训练集和测试集
    train_data,test_data,train_y,test_y=train_test_split(base_data.data,base_data.target,test_size=0.2,train_size=0.8)
    #生成文本的词频矩阵
    vectorizer=CountVectorizer(stop_words="english",decode_error='ignore')
    wordX=vectorizer.fit_transform(train_data)
    #训练分类器
    clf = MultinomialNB().fit(wordX,train_y)
    #预测测试集的分类结果
    test_wordX=vectorizer.transform(test_data).toarray()
    #newDoc_tfidf = transformer.transform(newDoc_wordX) #得到新文档每个词的TF-IDF值
    predicted = clf.predict(test_wordX) #预测
    print(predicted)
    #在测试集上的性能评估
    print(classification_report(test_y,predicted,target_names=base_data.target_names))
spamTest_skl()
