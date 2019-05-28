#-*-coding:utf-8-*-
import sys 
from gensim.models import word2vec
from gensim import corpora
import re
import jieba
import jieba.posseg as pseg
import jieba.analyse 
import os
import os.path 
import codecs
import sys

class Create_dict(object):
    def Confirm_dict(f,fwd,name):
        raw_tag=[]
        attr=[]
        for items in f:
            raw_tag.append(items)
        for it in raw_tag:                                                              #获得名词对象
            a=it.split("/")
            f_word=a[0]
            if f_word not in attr:
                attr.append(f_word)

        tag_dic={}
        for i in attr:
            #fw.write(i)
            #fw.write(":")
            kv=[]
            entity_count=0
            for lines in raw_tag:
                if str(i) == str(lines.split('/')[0]):
                    n_word = str(i)
                    a_word = lines.split('/')[1].split("\t")[0]
                    line=lines.replace("/","")
                    key =line.split("\t")[0]
                    value=int(line.split("\t")[1][:-1])
                    kv.append([key,n_word,a_word,value])
                    #tag_dic[lines.split("\t")[0]]=lines.split("\t")[1]
                    #fw.write(lines.replace("/",""))
                    #fw.write("    ")
                else:
                    continue            
            '''if len(kv) < 3:
                final_kv=kv[0][0]
            else :
                if (int(kv[0][1])-int(kv[1][1]))>(int(kv[1][1])-int(kv[2][1]))*5:
                    final_kv=kv[1][0]
                else :
                    final_kv=kv[0][0]
            '''
            kv_sort=sorted(kv,key = lambda x:x[3],reverse=True)
            #kv_tmp=np.array(kv)
            #fwd.write(str("1"))
            #fwd.write(str(kv))
            #kv_sort=kv_tmp[np.lexsort(kv_tmp.T)]
            #fwd.write(str("2"))
            #fwd.write(str(kv_sort))
            final_kv=kv_sort[0][0]
            #kv=kv_sort.tolist()
            kv_d=[]
            for li in kv_sort:
                kv_d.append([li.pop(0),li[0],li.pop(1)])
            tag_dic[final_kv]=kv_d
        


        for key,value in tag_dic.items():
            #fw.write(str(it.key))
            fwd.write("".join(str(key)))
            fwd.write(":")
            for tag in value:
                fwd.write("".join(str(tag).replace(' ',''))+" ")
            fwd.write('\n')

        return  tag_dic
    def Create_raw_dict(f,fwd):
        raw_tag=[]
        print('out')
        for line in f:
            print('in')
            raw_tag.append(line)
        return raw_tag

    def Combine_dict(f):
        raw_tag=[]
        attr=[]
        for items in f:
            item = jieba.cut(items)                                                     #jieba分词用'/'分割
            word="/".join(item)
            raw_tag.append(word)
        for it in raw_tag:                                                              #获得名词对象
            a=it.split("/")
            f_word=a[0]
            if f_word not in attr:
                attr.append(f_word)
        n_entity={}
        raw={}
        emotion=set()
        for i in attr:
            kv=[]
            entity_count=0
            for lines in raw_tag:
                if str(i) == str(lines.split('/')[0]):
                    n_word = str(i)
                    a_word = lines.split('/')[3]
                    emotion.add(a_word)
                    line=lines.replace("/","")
                    key =line.split("\t")[0]
                    value=int(line.split("\t")[1][:-1])
                    entity_count=entity_count+value
                    kv.append([key,n_word,a_word,value])
                    n_entity[str(i)]=entity_count
                else:
                    continue            
            raw[str(i)] = kv
        return  n_entity,raw,emotion
    '''def __init__:
        self.path = 'C:\\Users\\7000014355\\Documents\\TM\\tag_num\\'
        self.files = os.listdir(path) 
        for file in self.files:
            txt_path = 'C:\\Users\\7000014355\\Documents\\TM\\tag_num\\'+file
            f = codecs.open(txt_path,'r',encoding='utf-8')
            new_txt_path = 'C:\\Users\\7000014355\\Documents\\TM\\tag_res\\' + file
            fw = codecs.open(new_txt_path, 'w', encoding='utf-8')'''

'''
    def Create_T_model(f,name):
        raw_tag=[]
        attr=[]
        for items in f:
            raw_tag.append(items)
        for it in raw_tag:                                                              #获得名词对象
            a=it.split("/")
            f_word=a[0]
            if f_word not in attr:
                attr.append(f_word)
                    
        dictionary =corpora.Dictionary(attr)
        dictionary.save('C:\\Users\\7000014355\\Documents\\TM\\tag_res'+name+'.dict')
        corpus = corpora.MmCorpus('C:\\Users\\7000014355\\Documents\\TM\\tag_res'+name+'.mm')
        #tfidf = models.TfidfModel(corpus)
        #Lda = ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=100)
        return corpus,dictionary.token2id
'''
'''
    def Combine_adj_dict(f,fwd):
        raw_tag=[]
        adj=[]
        for items in f:
            raw_tag.append(items)
        for it in raw_tag:                                                              #获得名词对象
            a=it.split("/")
            f_word=a[1].split('\t')[0]
            if f_word not in adj:
                adj.append(f_word)
        return adj
'''