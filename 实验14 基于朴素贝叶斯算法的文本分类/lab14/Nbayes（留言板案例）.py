from numpy import *
import re
def  loadDataSet():
    postingList = [['my','dog','has','flea','problems','help','please'],
                ['maybe','not','take','him','to','dog','park','stupid'],
                ['my','dalmation','is','so','cute','I','love','him'],
                ['stop','posting','stupid','worthless','garbage'],
                ['mr','licks','ate','my','steak','how','to','stop','him'],
                ['quit','buying','worthless','dog','food','stupid']]
    classVec = [0,1,0,1,0,1]    #1代表侮辱性文字，0代表正常言论
    return postingList,classVec

def vocabList(dataSet):
    vocabSet = set([])  #使用set创建不重复的词汇集
    for document in dataSet:
        vocabSet = vocabSet|set(document)  #创建两个集合的并集
    return list(vocabSet)

def setOfWordsVec(vocabList,inputText):  #得到某个文档的词向量（词集模型）
    textVec = [0]*len(vocabList)#创建一个所包含元素都为0的向量
   #遍历文档中的所有单词，如果出现了词汇表中的单词，则将输出的文档向量中的对应值设为1
    for word in inputText:
      if word in vocabList:
          textVec[vocabList.index(word)] = 1
    return textVec

def bagOfWordsVec(vocabList,inputText):#得到某个文档的词向量（词袋模型）
    textVec = [0]*len(vocabList)  #创建一个所包含元素都为0的向量
    #遍历文档中所有单词，若出现了词汇表中的单词，则将文档向量中的对应值+1
    for word in inputText:
      if word in vocabList:
          textVec[vocabList.index(word)] += 1
    return textVec

def trainNB(trainDocMatrix,trainCategory):
    numTrainDoc = len(trainDocMatrix)  #文档数
    numWord = len(trainDocMatrix[0])   #单词数
    # 侮辱性文件的出现概率，即用trainCategory中所有的1的个数除以文档总数
    pAbusive = sum(trainCategory)/float(numTrainDoc)
    #构造单词出现的次数列表，初值为0，大小为单词数
    p0Num = ones(numWord)
    p1Num = ones(numWord)
    # 整个数据集单词出现总数
    p0Denom = 2.0
    p1Denom = 2.0
    #对每个文档遍历
    for i in range(numTrainDoc):
        #是否是侮辱性文档
        if trainCategory[i] ==1:
            # 如果是侮辱性文档，对侮辱性文档的向量进行加和
            p1Num+=trainDocMatrix[i]
            # 对向量中所有元素求和，也就是计算所有侮辱性文档中出现的单词总数
            p1Denom+=sum(trainDocMatrix[i])
        else:
            p0Num+=trainDocMatrix[i]
            p0Denom+=sum(trainDocMatrix[i])
    #类别1下，每个单词出现的概率，即
    p1Vec = log(p1Num/p1Denom)
    #类别0下，每个单词出现的概率，即
    p0Vec = log(p0Num/p0Denom)
    return p0Vec,p1Vec,pAbusive


def classifyNB(textVec,p0Vec,p1Vec,pClass1):
    """
     分类函数
    :param textVec: 要分类的文档向量
    :param p0Vec: 正常文档类（类别0）下的单词概率列表
    :param p1Vec: 侮辱性文档类（类别1）下的单词概率列表
    :param pClass1: 侮辱性文档（类别1）概率
    :return: 类别1 or 0
    """
    p1=sum(textVec*p1Vec)+log(pClass1)
    p0=sum(textVec*p0Vec)+log(1.0-pClass1)
   # print('p1=',p1)
   # print('p0=',p0)
    if p1>p0:
        return 1
    else:
        return 0

def testNB():
    """
    朴素贝叶斯算法测试
    """
    #1、加载数据集
    listOposts,listClasses = loadDataSet()
    #2、创建词汇表
    wordList = vocabList(listOposts)
    #3、构造训练数据的文档单词矩阵
    trainDocMat=[]
    for inDoc in listOposts:
        trainDocMat.append(bagOfWordsVec(wordList, inDoc))
    #4、训练数据
    p0V,p1V,pAb = trainNB(array(trainDocMat),array(listClasses))
    #5、测试数据
    testText=['love','my','ate']
    thisDoc = array(bagOfWordsVec(wordList,testText))
    print(testText,'classified as:',classifyNB(thisDoc,p0V,p1V,pAb))
    testText = ['stupid','dog']
    thisDoc = array(bagOfWordsVec(wordList,testText))
    print(testText,'classified as:',classifyNB(thisDoc,p0V,p1V,pAb))
testNB()

