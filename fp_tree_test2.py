import jieba.posseg as pseg
import jieba
import sys 
import codecs
import re
import os
import os.path 
import codecs
import sys
'''定义树的节点的类，有计算频率的方法和遍历子节点的方法'''
class treeNode (object):
    def __init__(self,nameValue,numOccur,parentNode):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = None
        self.parent = parentNode
        self.children = {}
    def inc (self,numOccur):
        self.count += numOccur
        
    def disp(self,ind = 1):
        #print (' '*ind,self.name,'  ',self.count)
        for child in self.children.values():
            child.disp(ind+1)
class extract_items (object):
    def createTree(self,dataSet,minSup=5):
        #print("into")
        headerTable = {}
        for trans in dataSet:
            for item in trans:
                headerTable[item] = headerTable.get(item,0)+ dataSet[trans]

        for k in list(headerTable.keys()):
            if headerTable[k] < minSup:             #频率=》tf_idf
                del(headerTable[k])  
        #print(str(len(headerTable)))
        freqItemSet = set(headerTable.keys())
        if len(freqItemSet) == 0 : return None,None
        for k in headerTable:
            headerTable[k] = [headerTable[k],None]
        retTree = treeNode('Null Set',1,None)
        for tranSet ,count in dataSet.items():
            localD = {}
            for item in tranSet:
                if item in freqItemSet:
                    localD[item] = headerTable[item][0]
            if len(localD) > 0:
                orderedItems = [v[0] for v in sorted(localD.items(),key = lambda p:p[1],reverse = True)]
                self.updateTree(orderedItems,retTree,headerTable,count)
        return retTree,headerTable

    def updateTree(self,items,inTree,headerTable,count):
        if items[0] in inTree.children:
            inTree.children[items[0]].inc(count)
        else:
            inTree.children[items[0]] = treeNode(items[0],count,inTree)
            if headerTable[items[0]][1] ==None:
                headerTable[items[0]][1] = inTree.children[items[0]]
            else:
                self.updateHeader(headerTable[items[0]][1], inTree.children[items[0]])
        if len(items) > 1:
            self.updateTree(items[1::], inTree.children[items[0]], headerTable, count)
            
    def updateHeader(self,nodeToTest,targetNode):
        while (nodeToTest.nodeLink !=  None):
            nodeToTest = nodeToTest.nodeLink
        nodeToTest.nodeLink = targetNode
        



    def ascendTree(self,leafNode,prefixPath):
        if leafNode.parent !=None:
            prefixPath.append(leafNode.name)
            self.ascendTree(leafNode.parent, prefixPath)

    def findPrefixPath(self,basePat,treeNode):
        condPats={}
        while treeNode != None:
            prefixPath = []
            self.ascendTree(treeNode, prefixPath)
            if len(prefixPath) > 1:
                condPats[frozenset(prefixPath[1:])] = treeNode.count
            treeNode = treeNode.nodeLink
        return condPats

    def mineTree(self,inTree,headerTable,minSup,preFix,freqItemList):
        bigL = [v[0] for v in headerTable.items()]
        for basePat in bigL:
            newFreqSet = preFix.copy()
            newFreqSet.add(basePat)
            freqItemList.append(newFreqSet)
            condPattBases = self.findPrefixPath(basePat, headerTable[basePat][1])
            myCondTree,myHead = self.createTree(condPattBases, minSup) 
            if myHead!= None:
                #print ('conditional tree for: ',newFreqSet)
                myCondTree.disp(1) 
                self.mineTree(myCondTree, myHead, minSup, newFreqSet, freqItemList)
def loadSimpDat(f,stopwords):
    #simpDat = [['r', 'z', 'h', 'j', 'p'],
    #           ['z', 'y', 'x', 'w', 'v', 'u', 't', 's'],
    #           ['z'],
    #           ['r', 'x', 'n', 'o', 's'],
    #           ['y', 'r', 'x', 'z', 'q', 't', 'p'],
    #           ['y', 'z', 'x', 'e', 'q', 's', 't', 'm']]
    word_data=[]
    for line in f:
        segs = pseg.cut(line)
        l=[]
        for seg in segs:
            if seg.flag in ("a","n","nr","v"):
                if seg.word not in stopwords:
                    l.append(seg)
        word_data.append(l)
    return word_data

def createInitSet(dataSet):
    retDict = {}
    for trans in dataSet:
        retDict[frozenset(trans)] = 1
    return retDict


