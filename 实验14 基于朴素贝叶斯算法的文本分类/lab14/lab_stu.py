from numpy import *
import re
import random  # 原代码缺少random导入，补充才能随机取测试集
# 1. 文本预处理
def textParse(text):
    wordList = re.split(r'\W+', text)  # 按非单词字符进行分词
    return [word.lower() for word in wordList if len(word) > 2]  # 单词转小写，只保留长度>2的单词（过滤单字母、空字符）
# 2. 遍历所有文档，生成词汇表
def vocabList(dataSet):
    """
    :param dataSet: 二维列表，每一个子列表是一篇文档的单词
    :return: 不重复单词组成的词汇列表
    """
    vocabSet = set([])
    for document in dataSet:
        vocabSet = vocabSet | set(document)  # 将当前文档单词并入总词汇集合，自动去重
    return list(vocabSet)
# 3. 基于词汇表，将文档转为词向量（词袋模型，统计单词出现次数）
def bagOfWordsVec(vocabList, inputText):
    """
    词袋模型：一篇文档 → 对应词汇表的整数词向量
    :param vocabList: 词汇表
    :param inputText: 单篇文档的单词列表
    :return: 词向量，元素为该单词在文档中的出现次数
    """
    textVec = [0] * len(vocabList)  # 初始化全0向量，长度 = 词汇表单词总数
    for word in inputText:  # 遍历当前文档每一个单词
        if word in vocabList:
            textVec[vocabList.index(word)] += 1  # 出现一次计数+1，统计词频
    return textVec  # 词汇表：[dog, stupid, love, beautiful]，文档[dog, stupid, dog] → 词向量[2, 1, 0, 0]
# 4. 训练朴素贝叶斯分类器
def trainNB(trainDocMatrix, trainCategory):
    """
    :param trainDocMatrix: 训练集词向量矩阵（二维数组）
    :param trainCategory: 训练集标签（1=垃圾邮件，0=正常邮件）
    :return: p0Vec(正常邮件对数概率数组), p1Vec(垃圾邮件对数概率数组), pClass1(垃圾邮件先验概率)
    """
    numTrainDoc = len(trainDocMatrix)  # 训练集文档总数量
    numWord = len(trainDocMatrix[0])  # 词汇表单词总数量（词向量长度）
    # 自行编写：计算先验概率 P(c1)：垃圾邮件在所有文档中的占比pClass1
    pClass1 = sum(trainCategory) / float(numTrainDoc)
    # 初始化（正常/垃圾）邮件中每个单词出现的总次数
    p0Num = ones(numWord)  # 形如[1.,1.,1.,...]
    p1Num = ones(numWord)
    # 初始化（正常/垃圾）邮件的总单词数
    p0Denom = 2.0
    p1Denom = 2.0
    # 遍历每一篇训练文档，统计词频
    for i in range(numTrainDoc):
        # 判断当前文档是否为垃圾邮件（标签=1）
        if trainCategory[i] == 1:
            p1Num += trainDocMatrix[i]  # 统计垃圾邮件中每个单词出现的总次数
            p1Denom += sum(trainDocMatrix[i])  # 统计垃圾邮件的总单词数
        # 当前文档为正常邮件（标签=0）
        else:
            p0Num += trainDocMatrix[i]
            p0Denom += sum(trainDocMatrix[i])
    # 自行编写：计算对数条件概率数组 ln(P(wj|c1))，取对数解决小数连乘下溢
    p1Vec = log(p1Num / p1Denom)
    # 自行编写：计算对数条件概率数组 ln(P(wj|c0))
    p0Vec = log(p0Num / p0Denom)
    return p0Vec, p1Vec, pClass1
# 5. 判断邮件类别
def classifyNB(textVec, p0Vec, p1Vec, pClass1):
    """
    :param textVec: 待分类文档词向量
    :param p0Vec: 正常邮件对数条件概率数组
    :param p1Vec: 垃圾邮件对数条件概率数组
    :param pClass1: 垃圾邮件先验概率 P(c1)
    :return: 分类结果 1(垃圾邮件) / 0(正常邮件)
    """
    # 自行编写：计算类别1综合得分：lnP(c1) + Σ( x[j] * lnP(wj|c1) )
    p1 = sum(textVec * p1Vec) + log(pClass1)
    # 自行编写：计算类别0综合得分：lnP(c0) + Σ( x[j] * lnP(wj|c0) )
    p0 = sum(textVec * p0Vec) + log(1.0 - pClass1)
    # 自行编写：判断所属类别
    if p1 > p0:
        return 1
    else:
        return 0
# 6.基于朴素贝叶斯算法的邮件分类
def spamTest():
    # 6.1 加载邮件数据
    emailWordList = []  # 存储所有邮件的单词列表（整个数据集）
    classList = [] # 存储每封邮件对应的标签：1=垃圾邮件，0=正常邮件
    # 循环读取 1~25 号垃圾邮件 + 正常邮件，共50封邮件
    for i in range(1, 26):
        # 读取并解析垃圾邮件（spam文件夹），转为单词列表
        wordList = textParse(open(r'D:\下载\visual studio code\text\实验14 基于朴素贝叶斯算法的文本分类\lab14\email\spam\%d.txt' % i, encoding="utf-8").read())
        emailWordList.append(wordList)
        classList.append(1)  # 标记为垃圾邮件
        # 读取并解析正常邮件（noSpam文件夹）
        wordList = textParse(open(r'D:\下载\visual studio code\text\实验14 基于朴素贝叶斯算法的文本分类\lab14\email\noSpam\%d.txt' % i, encoding="utf-8").read())
        emailWordList.append(wordList)
        classList.append(0)  # 标记为正常邮件
    wordTable = vocabList(emailWordList)  # 基于全部邮件，构建词汇表
    # 6.2 划分训练集和测试集
    trainingSet = list(range(50))  # 生成全集下标：0~49，对应50封邮件
    testSet = []  # 空列表：存放随机选出的测试集下标
    # 随机挑选10封邮件作为测试集
    for i in range(10):
        randIndex = int(random.uniform(0, len(trainingSet)))  # 随机生成下标
        testSet.append(trainingSet[randIndex])  # 将选中的下标加入测试集
        del(trainingSet[randIndex])  # 从全集删除该下标（剩余作为训练集）
    trainDocMat = []  # 构造训练集文档词向量矩阵
    trainDocClass = []  # 构造训练集文档对应标签
    for docIndex in trainingSet:
        trainDocMat.append(bagOfWordsVec(wordTable, emailWordList[docIndex]))  # 将训练邮件转为词向量
        trainDocClass.append(classList[docIndex])  # 取出对应标签
    # 6.3 自行编写：训练朴素贝叶斯模型
    p0V, p1V, pClass1 = trainNB(trainDocMat, trainDocClass)
    # 6.4 测试朴素贝叶斯模型
    errorCount = 0  # 统计分类错误的邮件数量
    # 遍历测试集，逐封邮件测试分类效果
    for docIndex in testSet:
        wordVector = bagOfWordsVec(wordTable, emailWordList[docIndex])  # 测试邮件转为词向量
        # 自行编写：模型预测结果 和 真实标签对比（打印分类错误的邮件下标，并统计分类错误的邮件数量）
        pred = classifyNB(wordVector, p0V, p1V, pClass1)
        trueLabel = classList[docIndex]
        if pred != trueLabel:
            print(f"分类错误，邮件下标：{docIndex}，预测：{pred}，真实：{trueLabel}")
            errorCount += 1
    # 自行编写：计算错误率 = 错误数 / 测试集总数
    errRate = errorCount / len(testSet)
    print('the  error rate is :', errRate)
# 7.运行整个程序
spamTest()