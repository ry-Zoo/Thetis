# -*- coding: utf-8 -*-
from math import log,sqrt
from gensim.models import word2vec
from gensim import corpora
import logging
import codecs
import jieba
import jieba.analyse 
import jieba.posseg as pseg
#import synonyms
import os
import numpy as np 
from re_sort_tag  import Create_dict as Create_dict

#创建相似矩阵 欧几里得的对称矩阵
class G_model(object):
    def Create_G_model(new_entity_list,model,fw):
        G=np.zeros((len(new_entity_list),len(new_entity_list)))                                         #构建大小和词典长度相等的全零二维矩阵
        empty_words_pattern=0                                                                           #字典和模型无法参照的词的数量
        for u in range(0,len(new_entity_list)):
            for v in range(u,len(new_entity_list)):                                                     #对二维矩阵进行遍历
                if u == v :
                    G[u,v] = G[v,u] = 1                                                                 #对角线上两词相同，相似度设为1
                    continue
                try:
                    similar = model.similarity(new_entity_list[u][0],new_entity_list[v][0])             #通过词相似矩阵获得两词之间的距离
                    if similar < 0 : 
                        G[u,v]=G[v,u] = abs(similar)        #为矩阵各位置赋值
                    else :
                        G[v,u]=G[u,v] = similar
                except :
                    similar = model.similarity(new_entity_list[u],new_entity_list[v])
                    if similar < 0 :
                        G[u,v]=G[v,u] = abs(similar)
                    else:
                        G[v,u]=G[u,v] = similar
                    empty_words_pattern += 1
                    #print ('the empty word amount:'+str(empty_words_pattern)) 
        return G                                                                                        #获得初始的用于聚类的词距离矩阵
#创建新的相似矩阵，将合并的项看作一项
    def Updata_G_mondel(new_entity_list,model,fw):                                                      #每当聚类算法改变词典序列组成，对应的词距离矩阵也需要调整
        #fw.write(str(new_entity_list))
        #fw.write(" "+str(len(new_entity_list)))
        #fw.write("\n")
        G=np.zeros((len(new_entity_list),len(new_entity_list)))                                         
        empty_words_pattern=0
        for u in range(0,len(new_entity_list)):
            for v in range(u,len(new_entity_list)): 
                if u == v :
                    G[u,v] = G[v,u] = 1
                    continue
                try:                                                                                    #由于字典中的项不再都是一维，须根据项的长度对相似距离重新计算
                    sim_tmp_res=0
                    if len(new_entity_list[u])>1:                                                       #矩阵row方向元素不为单项
                        #print('!1----'+str(len(new_entity_list[u])))
                        for u_item in new_entity_list[u]:
                            #fw.write(str(u_item))
                            if len(new_entity_list[v])>1:                                                   #矩阵col方向元素不为单项
                                for v_item in new_entity_list[v]:
                                    #fw.write(str(v_item))
                                    d_sim=model.similarity(u_item[0],v_item[0])
                                    sim_tmp_res=sim_tmp_res+d_sim
                                    #fw.write(str(sim_tmp_res))
                                    #fw.write("\n")
                                similar=sim_tmp_res/(len(new_entity_list[u])*len(new_entity_list[v]))
                            else:                                                                           #矩阵col方向元素为单项
                                o_sim=model.similarity(u_item[0],new_entity_list[v][0])
                                sim_tmp_res=sim_tmp_res+o_sim
                                similar=sim_tmp_res/len(new_entity_list[u])
                    else:                                                                               #矩阵row方向元素为单项
                        #print('1-----'+str(len(new_entity_list[v])))
                        if len(new_entity_list[v])>1:                                                       #矩阵col方向元素不为单项
                            #fw.write(str(new_entity_list[u]))
                            #fw.write(" "+str(len(new_entity_list[u])))
                            for v_item in new_entity_list[v]:
                                e_sim=model.similarity(new_entity_list[u][0],v_item[0])
                                sim_tmp_res=sim_tmp_res+e_sim
                                similar=sim_tmp_res/len(new_entity_list[v])
                            #fw.write(" "+str(similar))
                            #fw.write("\n")
                        else:                                                                               #矩阵col方向元素为单项
                            #fw.write(str(new_entity_list[u]))
                            #fw.write(" "+str(new_entity_list[v]))
                            #print ("1")
                            similar = model.similarity(new_entity_list[u][0],new_entity_list[v][0]) 
                            #print ("2")
                            #fw.write(" "+str(similar))
                            #fw.write("\n")
                    if similar < 0 : 
                        G[u,v]=G[v,u] =abs(similar)        #为矩阵各位置赋值
                    else :
                        G[v,u]=G[u,v] = similar
                except :
                    G[u,v]=G[v,u] = 0
                    #empty_words_pattern += 1
                    #print ('the empty word amount:'+str(empty_words_pattern)) 
        return G
    def Create_MI_model(all_a_list,new_adj_combo,fw):
        #print(str(new_adj_combo))
        mi_G=np.zeros((len(all_a_list),len(all_a_list)))  
        for i in range(0,len(all_a_list)):
            for j in range(i+1,len(all_a_list)):
                i_word=all_a_list[i][0]
                i_c=all_a_list[i][1]
                j_word=all_a_list[j][0]
                j_c=all_a_list[j][1]
                combo_c=new_adj_combo[(i_word,j_word)]
                fw.write(str(combo_c))
                fw.write('\n')
                mi_G[i][j]=combo_c/i_c*j_c
#聚类方法
class Cluster_merge(object):
    def Get_merge_similarity(G,new_entity_list,G_model,model,fw):
        min_min = 0                                                                                     #定义获得最大相似度的变量
        closest_cluster_Main = 0                                                                        #定义本轮最大相似的词A的词典位置指数
        closest_cluster_Secondary = 0                                                                   #定义本轮最大相似的词B的词典位置指数
        for i in range(0,len(new_entity_list)):
            for j in range(i+1,len(new_entity_list)):
                min_body=G[i][j]
                #print (str(min_body))
                if min_body>min_min and min_body>0.9 :                                                  #获得最大值，并且最大之满足相似度>0.9
                    min_min=min_body
                    closest_cluster_Main= i 
                    closest_cluster_Secondary= j
                else:
                    continue
        if closest_cluster_Secondary==0 and closest_cluster_Main == 0:                                  #没有满足上述条件的情况，结束迭代，当前字典结果即最终结果
            return new_entity_list
        else:                                                                                           #满足上述条件，说明可以继续聚类，以下为四种情况
            #print(str(new_entity_list[closest_cluster_Main].ndim))
            #print(str(new_entity_list[closest_cluster_Main].shape[1]))
            #fw.write(str(new_entity_list[closest_cluster_Main]))
            #fw.write(str(new_entity_list[closest_cluster_Secondary]))
            #fw.write("\n")
            merge_cluster=[]
            if len(new_entity_list[closest_cluster_Main])>1 and len(new_entity_list[closest_cluster_Secondary])>1:
                #print('a')
                #print(str(new_entity_list[closest_cluster_Main].shape[1]))
                new_entity_list[closest_cluster_Main].extend(new_entity_list[closest_cluster_Secondary])
                merge_cluster.append(new_entity_list[closest_cluster_Main])
            elif len(new_entity_list[closest_cluster_Main])>1 and len(new_entity_list[closest_cluster_Secondary])==1:
                #print('b')
                #print(str(new_entity_list[closest_cluster_Main].shape[1]))
                new_entity_list[closest_cluster_Main].append(new_entity_list[closest_cluster_Secondary])
                merge_cluster.append(new_entity_list[closest_cluster_Main])
            elif len(new_entity_list[closest_cluster_Main])==1 and len(new_entity_list[closest_cluster_Secondary])>1:
                #print('c')
                new_entity_list[closest_cluster_Secondary].append(new_entity_list[closest_cluster_Main])
                merge_cluster.append(new_entity_list[closest_cluster_Secondary])
            else:
                #print('d')
                #print(str(new_entity_list[closest_cluster_Main].shape[1]))
                merge_cluster=[[new_entity_list[closest_cluster_Main],new_entity_list[closest_cluster_Secondary]]]
                #merge_cluster=np.array(merge_cluster)
            del new_entity_list[closest_cluster_Main]
            del new_entity_list[closest_cluster_Secondary-1]                                            #新项保持一维数组的形式
            new_entity_list.append(merge_cluster[0])                                                    #去除被合并的项，添加合并的新项
            G=G_model.Updata_G_mondel(new_entity_list,model,fw)                                         #更新相似矩阵
            Cluster_merge.Get_merge_similarity(G,new_entity_list,G_model,model,fw)                      #迭代该方法
    #合并形容词的方法改进1：利用w2v的语义距离代入，先计算最大距离的词分成两类，再围绕两个类别聚类
    def Adj_merge_similarity(G,ma_list,G_model,model,fw):
        #第一轮
        dis_list=[]
        for item in ma_list:
            for wsa in sa_dict:
                if item==wsa[0]:
                    fw.write(str(wsa))
                    fw.write('\n')
                else:
                    dis_list.append(item)
        for dis in dis_list:
            fw.write(str(dis))
            fw.write('\n')
        '''
        max_max = 1                                                                                     #定义获得最大相似度的变量
        min_min = 0                                                                                     #定义获得最小相似度的变量
        closest_cluster_Main = 0                                                                        #定义本轮最大相似的词A的词典位置指数
        closest_cluster_Secondary = 0                                                                   #定义本轮最大相似的词B的词典位置指数
        for i in range(0,len(ma_list)):
            for j in range(i+1,len(ma_list)):
                max_body=G[i][j]
                fw.write(str(ma_list[i]))
                fw.write(str(ma_list[j]))
                fw.write(str(max_body))
                fw.write('\n')
                if max_body<max_max and max_body<0.1 :                                                  #获得最大值，并且最大之满足相似度>0.9
                    max_max=max_body
                    closest_cluster_Main= i 
                    closest_cluster_Secondary= j
                    break
                else:
                    continue
        merge_adj_list=[]
        one_list=[ma_list[closest_cluster_Main]]
        another_list=[ma_list[closest_cluster_Secondary]]
        #fw.write(str(one_list)+" "+str(another_list))
        #fw.write('\n')
        for y in range(0,len(ma_list)):
            if G[y][closest_cluster_Main]>=G[y][closest_cluster_Secondary]:
                one_list.append(ma_list[y])
            else :
                another_list.append(ma_list[y])
        merge_adj_list=[one_list,another_list]
        '''
'''
def find_most_appropriate(sort_only_entity,sort_entity_list,adj_list,raw_dict):
    for n_item in sort_only_entity:
        for a_item in adj_res:

'''
class All_Doc_Count(object):
    def All_Doc_Entity(sort_only_entity,old_path,name):
        f = codecs.open(old_path,'r',encoding='utf-8')
        doc=[]
        D_count=0
        for line in f:
            doc.append(line.strip())
            D_count+=1
        dictionary =corpora.Dictionary(sort_only_entity)
        #dictionary.save('D:\\TM\\Text_Mining\\TM_REGION\\Tag_Dic_Tmp\\'+name+'_n.dict')
        corpus = [dictionary.doc2bow(d.split()) for d in doc]  
        #corpora.MmCorpus('C:\\Users\\7000014355\\Documents\\TM\\tag_res\\'+name+'_n.mm',corpus)    
        HD_entity={}                    
        for li in corpus:
            for l in range(0,len(li)):
                for w,wid in dictionary.items():
                    if w==li[l][0]:
                        if wid in HD_entity.keys():
                            HD_entity[wid]+=int(li[l][1])
                        else:
                            HD_entity[wid]=int(li[l][1])                            
        return HD_entity,D_count

    def All_Doc_Adj(emotion_dic,old_path,name):
        f = codecs.open(old_path,'r',encoding='utf-8')
        doc=[]
        D_count=0
        for line in f:
            doc.append(line.strip())
            D_count+=1
        emotion_list=[]
        for ed in  emotion_dic:
            emotion_list.append([ed])
        dictionary =corpora.Dictionary(emotion_list)  
        #dictionary.save('D:\\TM\\Text_Mining\\TM_REGION\\Tag_Dic_Tmp\\'+name+'_a.dict')
        corpus = [dictionary.doc2bow(d.split()) for d in doc]  
        #corpora.MmCorpus('C:\\Users\\7000014355\\Documents\\TM\\tag_res\\'+name+'_a.mm',corpus)
        '''
        #使用互信息的方法度量形容词之间距离
        #构建文档-词矩阵
        print(str(D_count)+" "+str(len(emotion_list)))
        da_G=np.zeros((D_count,len(emotion_list)))
        c_t=0
        for t in corpus:
            for i in t:
                #print(str(c_t)+" "+str(len(da_G[t])))
                da_G[c_t][i[0]]=1
            c_t+=1
        #print(str(da_G))
        #根据矩阵计算形容词共现频数{(id,id):count}
        adj_combo={}
        for emo in range (0,len(emotion_list)):
            for doc in range (0,D_count):
                appear_list=[]
                if da_G[doc][emo]==1:
                    appear_list.append(doc)
            for ap in appear_list:
                for re_emo in range (emo+1,len(emotion_list)):
                    if da_G[emo][re_emo]==1:
                        kt=tuple([emo,re_emo])
                        if kt in adj_combo.keys():
                            adj_combo[kt]+=1
                        else:
                            adj_combo[kt]=1
                    else:
                        continue
                else:
                    continue
        print(str(adj_combo))
        #参照dictionary变换为{(word,word):count}
        new_adj_combo={}
        for k_combo,v_combo in adj_combo.items():
            new_key_list=[]
            for k_dic,v_dic in dictionary.items():
                if k_dic==k_combo[0]:
                    new_key_list.append(v_dic)
                elif k_dic==k_combo[1]:
                    new_key_list.append(v_dic)
                else:
                    continue
                new_key=tuple(new_key_list)
                #print(str(new_key))
                new_adj_combo[new_key]=v_combo
        #互信息方法
        '''
        HD_adj={}              
        for li in corpus:
            for l in range(0,len(li)):
                for w,wid in dictionary.items():
                    if w==li[l][0]:
                        if wid in HD_adj.keys():
                            HD_adj[wid]+=int(li[l][1])
                        else:
                            HD_adj[wid]=int(li[l][1]) 
        #需要计算两个共线的频数


        return HD_adj,D_count




























'''
for key ,value in compare_ent_dic.items():
	fw.write(str(key))
	fw.write(":")
	fw.write(str(value))
	fw.write("\n")
'''

'''
## 计算某个词的相关词列表
y2 = model.most_similar(u"音质", topn=20)  # 20个最相关的
fw.write(u"和【音质】最相关的词有：\n")
for item in y2:
    cur_word=pseg.cut(str(item[0]))
    for c in cur_word:
        if c.flag=='n':
            fw.write(str(item[0]))
            fw.write("\n")
            fw.write(str(item[1]))
fw.write( "--------\n")
y20 = model.most_similar(u"画面", topn=20)  # 20个最相关的
fw.write(u"和【画面】最相关的词有：\n")
for item in y20:
    cur_word=pseg.cut(str(item[0]))
    for c in cur_word:
        if c.flag=='n':
            fw.write(str(item[0]))
            fw.write("\n")
            fw.write(str(item[1]))
fw.write( "--------\n")
y200 = model.most_similar(u"价格", topn=20)  # 20个最相关的
fw.write(u"和【价格】最相关的词有：\n")
for item in y200:
    cur_word=pseg.cut(str(item[0]))
    for c in cur_word:
        if c.flag=='n':
            fw.write(str(item[0]))
            fw.write("\n")
            fw.write(str(item[1]))
fw.write( "--------\n")

## 寻找对应关系
fw.write(u"快-发货  ")
y3 = model.most_similar([u'快', u'发货'], [u'快'], topn=3)
for item in y3:
    fw.write(str(item[0]))
    fw.write(" ")
    fw.write(str(item[1]))
fw.write( "--------\n")

'''


## 寻找不合群的词
#y4 = model.doesnt_match(u"书 书籍 教材 很".split())
#print u"不合群的词：", y4
#print "--------\n"

# 保存模型，以便重用
#model.save(u"category.model")
# 对应的加载方式
# model_2 = word2vec.Word2Vec.load("text8.model")

# 以一种C语言可以解析的形式存储词向量
#model.save_word2vec_format(u"animal.model.bin", binary=True)
# 对应的加载方式
# model_3 = word2vec.Word2Vec.load_word2vec_format("text8.model.bin", binary=True)



'''
fw.write("--------------\n")
for entity in new_entitydic:
    fw.write(str(entity[0]))
    fw.write(" ")
    fw.write(str(entity[1]))
    fw.write("\n")
'''
    #尝试：二分随机选择质心 ，比较计算其他的项到两质心的距离，距离近的纳入其下，递归的进行这个操作

'''
    T_model,dict_no=Create_dict.Create_T_model(fd,name)
    for it in entity_list:
        for key,token in dict_no:
            if it[0]==key:
            	it.append(token)
            else:
            	continue
    tok_entity_list=sorted(entity_list,key = lambda x:x[2],reverse=True)  	
    T=np.zeros(len(tok_entity_list),len(tok_entity_list))
    for h in xrange(0,len(tok_entity_list)):
        for k in xrange(h,len(tok_entity_list)):
            word_h=tok_entity_list[h][0]
            word_k=tok_entity_list[k][0]
            if h == k:
                T[h][k] = T[k][h] = 1
                continue
            if tok_entity_list > self.terms_hash_sequence[word_j]:   	#矩阵右上侧
'''

