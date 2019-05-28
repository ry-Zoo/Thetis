# -*- coding: utf-8 -*-
from math import log,sqrt
from gensim.models import word2vec
from gensim import corpora
import logging
import codecs
import jieba
import jieba.analyse 
import jieba.posseg as pseg
import os
import numpy as np 
from re_sort_tag  import Create_dict as Create_dict
from  mid_model import  G_model as G_model
from mid_model import Cluster_merge as Cluster_merge
from mid_model import All_Doc_Count as All_Doc_Count
class model_engine(object):
    def __init__(self,fd,fwd,sa_dict,name):
        self.model = word2vec.Word2Vec.load("D:\\TM\\Text_Mining\\TM_REGION\\middle\\all_category.model")
        new_txt_path = 'D:\\TM\\Text_Mining\\TM_REGION\\middle\\gensimtest.txt'
        self.fw = codecs.open(new_txt_path, 'w', encoding='utf-8')
        self.name=name
        self.fd = fd
        self.fwd = fwd 
        self.sa_dict = sa_dict 
        self.stopwords={}
        fstop = open('D:\\TM\\Text_Mining\\TM_REGION\\dict\\stopLibrary.dic', 'r',encoding="utf8")
        for eachWord in fstop:
            self.stopwords[eachWord.strip()] = eachWord.strip()
        fstop.close()

        jieba.load_userdict('D:\\TM\\Text_Mining\\TM_REGION\\dict\\user_dict.txt')
        self.entity_dic,self.raw,self.emotion_dic=Create_dict.Combine_dict(self.fd)									#entity_dic包含了名词和名词共现数量，raw包含了全部的组合信息,emotion字典中出现的形容词

        entity_list=[]
        for key,value in self.entity_dic.items():
            entity_list.append([key,value])
        self.fw.write(str(self.name))
        self.sort_entity_list=sorted(entity_list,key = lambda x:x[1],reverse=True)			#排序过的名词和数量序列


        self.sort_only_entity=[] 
        self.sort_only_entity_copy=[]
        for i in self.sort_entity_list:
            self.sort_only_entity.append([i[0]]) 
        #fw.write(str(sort_only_entity))
        self.sort_only_entity_copy = self.sort_only_entity.copy()                                         #获得不带词频的排序好的候选词序列


    def Merge(self):

        fw=self.fw
        fwd=self.fwd
        name=self.name
        model=self.model
        sort_only_entity=self.sort_only_entity
        sort_only_entity_copy=self.sort_only_entity_copy
        sort_entity_list=self.sort_entity_list
        raw=self.raw
        emotion_dic=self.emotion_dic
        sa_dict=self.sa_dict

        G=G_model.Create_G_model(sort_only_entity,model,fw)                                #初始的model
        #经过合并的名词实体聚类结果
        Cluster_merge.Get_merge_similarity(G,sort_only_entity,G_model,model,fw)

        #----------------------------------------------------------------------------------------------------
        real_combine_dic={}
        for res in sort_only_entity:
            if len(res)==1:
                cur_entity_num=0														#计算单个项的实体，对照原记录组获得之
                for t in sort_entity_list:
                    if res[0]==t[0]:
                        cur_entity_num=t[1]
                    cur_entity=tuple([res[0],cur_entity_num])
                real_combine_dic[cur_entity]=res
            else:
                c=0
                c_list=[]
                cur_entity_num=0
                sc_list=[]
                for inner_res in res:
                    for it in sort_entity_list:
                        if inner_res[0] == it[0] :
                            c_list.append(it)
                        else:
                            continue
                        sc_list=sorted(c_list,key =lambda x:x[1],reverse=True)
                        if len(sc_list)>1:
                            for sc in sc_list:
                                cur_entity_num=cur_entity_num+int(sc[1])				#计算多个项的实体的共现频数
                        else:
                            continue
                cur_entity=tuple([sc_list[0][0],cur_entity_num])				#将共现次数最大的词和实体的共现频数和组合作为key
                real_combine_dic[cur_entity]=res
                #产生形如('手机', 13):[['手机'], ['电脑']]的字典--$获得名词共现聘书要素$

        old_path='D:\\TM\\Text_Mining\\TM_REGION\\middle\\Cut_Res\\'+name
        all_doc_entity={}
        all_doc_adj={}
        d_count=0
        #fw.write(str(sort_only_entity_copy))
        all_doc_entity,d_count=All_Doc_Count.All_Doc_Entity(sort_only_entity_copy,old_path,name)					#名词实体全文频数
        all_doc_adj,d_count=All_Doc_Count.All_Doc_Adj(emotion_dic,old_path,name)								#形容词全文频数
        real_condition_adj=[]				
        for key,values in real_combine_dic.items():
            n_dic={}
            n_dic[key[0]]=key[1]
            a_dic={}
            complex_list=[]
            for value in values:
                for k,v in raw.items():
                    for cp in v:
                        if cp[1]==''.join(value):
                            if cp[2] not in a_dic.keys():
                                a_dic[cp[2]]=int(cp[3])
                            else:
                                a_dic[cp[2]]+=int(cp[3]) 
            complex_list=[n_dic,a_dic]
            real_condition_adj.append(complex_list)											#获得在名词确定的条件下的形容词和共现频数序列
        #real_condition_adj：[[{最终名词1：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}],....,[{最终名词n：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}]]
        #fw.write(str(real_condition_adj))
        #fw.write('\n')

        #需要对形容词 进行聚类操作 候选集建立矩阵，层次聚类(分裂)距离最大的先分裂，其余项分别计算和这两项的距离，较近的就划归，候选形容词集分成两类
        
        '''
        all_a_list=[]
        for dak,dav in all_doc_adj.items():
        	all_a_list.append([dak,dav])
        a_G=G_model.Create_MI_model(all_a_list,new_adj_combo,fw)								#创建互信息度量的形容词关联矩阵
        '''
        '''
        dis_list = set()
        exist_list = set()
        for emo_item in emotion_dic:
            for sa in sa_dict:
                if sa[0] == emo_item:
                    fw.write(str(sa))
                    fw.write('\n')
                    exist_list.add(emo_item)
                else:
                    dis_list.add(str(emo_item))            
        for dis in dis_list:
            if dis in exist_list:
                continue
            else:
                fw.write(str(dis))
                fw.write('\n')
        '''

        '''
        merge_adj_list=[]
        for ma in real_condition_adj:
            merge_adj=[]
            ma_list=[]
            merge_adj.append(ma[0])
            for ma_k,ma_v in ma[1].items():
                ma_list.append(ma_k)

            #构建形容词互信息参照（互信息所需的要素：形容词词频，名词词频，共现词频，互信息计算方法：共现词频/（名词词频*形容词词频））
            
            a_G=G_model.Create_G_model(ma_list,model,fw)
            Cluster_merge.Adj_merge_similarity(a_G,ma_list,G_model,model,fw)
            #fw.write(str(ma_list))
            #fw.write("\n")
            #合并的ma_list：[[1set]，[2set]]
            for mk,mv in ma[1].items():
                if mk in ma_list[0]:
                    merge_adj.append([mk,mv])
                elif mk in ma_list[1]:
                    merge_adj.append([mk,mv])
                else:
                    continue
            merge_adj_list.append(merge_adj)
        #merge_adj_list:[[{最终名词1：词频},[形容词1：词频，形容词2：词频....],[形容词i：词频，形容词j：词频...]]]  len(merge_adj_list):2 or 3
        '''

        

        '''
        #最终计算度量合并形容词
        final_dic={}
        complete_list=[]
        for item in real_condition_adj:  #real_condition_adj：[[{最终名词1：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}],....,[{最终名词n：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}]]
            final=item[0]
            final_n=''
            for k,v in final.items():
                final_n=k
                final_n_count=v
            #fw.write(str(final_n)+str(final_n_count))
            #fw.write('\n')
            pick_final_adj=[]
            candidate_a_list=[]
            for ka,va in item[1].items():
                candidate_a=ka
                candidate_a_list.append(candidate_a)
                candidate_a_count=va
                #print(str(d_count)+":"+str(candidate_a_count)+":"+str(final_n_count))
                for da_key,da_value in all_doc_adj.items():
                    #fw.write(str(da_key)+str(da_value)+str(candidate_a))
                    #fw.write('\n')
                    if da_key == candidate_a:														#使用了TF—IDF,粗略看来比条件概率好
                        idf_value=(candidate_a_count*1.0/final_n_count)*(log(d_count*1.0/(1+da_value)))*(log(d_count*1.0/(1+final_n_count)))
                        #idf_value=log( (d_count*candidate_a_count*1.0) / (da_value*final_n_count) ) / -log( (candidate_a_count *1.0 ) / final_n_count)
                        pick_final_adj.append([candidate_a,idf_value])
                #P=(candidate_a_count/final_n_count)*(final_n_count/d_count)						#条件概率结果
                #pick_final_adj.append([candidate_a,P])
                #fw.write(str(final_n_count)+":"+str(candidate_a_count)+":"+str(pick_final_adj))
                #fw.write('\n')
            pick_final_adj=sorted(pick_final_adj,key =lambda x:x[1],reverse=True)
            final_adj=pick_final_adj[0][0]
            final_dic[final_n]=final_adj
            for kn,vn in real_combine_dic.items():
                candidate_n_list=[]
                if len(vn)>1:
                    for ca in vn:
                        candidate_n_list.append(ca[0])
                else:
                    for ca in vn:
                        candidate_n_list.append(ca)
                complete_item=[]
                #fw.write(str(kn))
                if final_n==kn[0]:
                    complete_item=[[final_n,final_dic[final_n]],candidate_n_list,candidate_a_list]
                else:
                    continue
                complete_list.append(complete_item)																#应为最终结果
        for line in complete_list:
            fw.write(str(line))
            fw.write('\n')
        for item in complete_list:
            fwd.write(str(item))
            fwd.write('\n')
        return complete_list
		'''
        #complete_list：[[{最终名词，最终形容词}，{从属名词1:词频...从属名词n：词频}，{从属形容词1：词频...从属形容词n：词频}]，[]，[]]
        #实际complete_list：[[[最终名词，最终形容词]，[（最终名词1:词频）：从属名词1..从属名词n]，{从属形容词1：词频...从属形容词n：词频}]，[]，[]]
        #更改后的简易形式为[[[最终名词，最终形容词]，[从属名词1..从属名词n]，[从属形容词1...从属形容词n]，[]，[]]，即可满足查询合并结果的要求

        '''
		还需完成1.名词实体全文当频数---done
			   2.形容词全文档频数----done
			   3.形容词共现频数计算方法,由名词决定的范围下的形容词----done
		'''
        final_dic={}
        complete_list=[]
        #fw.write(str(real_condition_adj))
        #fw.write('\n')
        for item in real_condition_adj:  #real_condition_adj：[[{最终名词1：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}],....,[{最终名词n：词频},{形容词1：词频，形容词2：词频，.....形容词n：词频}]]
            final=item[0]
            final_n=''
            for k,v in final.items():	#获得名次信息
                final_n=k
                final_n_count=v 		
            pick_final_adj=[]
            candidate_a_list=[]			#一个名词下的候选形容词的情感信息和词频
            for ka,va in item[1].items():#获得形容词信息
                candidate_a=ka
                flag=1
                for sa in sa_dict:
                    if candidate_a == sa[0] and flag==1:
                        sa_copy=sa.copy()
                        sa_copy.append(va)
                        candidate_a_list.append(sa_copy)	#可能出现一词多义 flag保证只取一个情感词典意义
                        flag=0
            saa_n=[]
            saa_p=[]
            saa_c=[]
            #fw.write(str(candidate_a_list)+'\n')
            for saa in candidate_a_list:
                if saa[3].strip('\r\n')=='2':
                    saa_n.append(saa)
                elif saa[3].strip('\r\n')=='1':
                    saa_p.append(saa)
                elif saa[3].strip('\r\n')=='0':
                    saa_c.append(saa)
                else:
                    continue
            #fw.write(str(saa_n))
            #fw.write('\n')
            for kn,vn in real_combine_dic.items():
                candidate_n_list=[]
                if len(vn)>1:
                    for ca in vn:
                        candidate_n_list.append(ca[0])
                else:
                    for ca in vn:
                        candidate_n_list.append(ca)
                complete_item=[]
                #fw.write(str(kn))
                if final_n==kn[0]:
                    if  len(saa_p):
                        candidate_ap=sorted(saa_p, key=lambda x:x[4],reverse=True)
                        pick_final_ap=[]
                        ap_list=[]
                        for ap in candidate_ap:
                            for da_key,da_value in all_doc_adj.items():
                                if ap[0]== da_key:
                                    ap_list.append(ap[0])
                                    idf_value=(ap[4]*1.0/final_n_count)*(log(d_count*1.0/(1+da_value)))*(log(d_count*1.0/(1+final_n_count)))
                                    pick_final_ap.append([ap[0],idf_value,ap[1],ap[3].strip('\r\n')])
                        pick_final_ap=sorted(pick_final_ap,key =lambda x:x[1],reverse=True)
                        complete_item_ap=[[final_n,pick_final_ap[0][0],pick_final_ap[0][2],pick_final_ap[0][3]],candidate_n_list,ap_list]
                        complete_list.append(complete_item_ap)
                    if len(saa_n):
                        candidate_an=sorted(saa_n, key=lambda x:x[4],reverse=True)
                        pick_final_an=[]
                        an_list=[]
                        for an in candidate_an:
                            for da_key,da_value in all_doc_adj.items():
                                if an[0]== da_key:
                                    an_list.append(an[0])
                                    idf_value=(an[4]*1.0/final_n_count)*(log(d_count*1.0/(1+da_value)))*(log(d_count*1.0/(1+final_n_count)))
                                    pick_final_an.append([an[0],idf_value,an[1],an[3].strip('\r\n')])
                        pick_final_an=sorted(pick_final_an,key =lambda x:x[1],reverse=True)
                        complete_item_an=[[final_n,pick_final_an[0][0],pick_final_an[0][2],pick_final_an[0][3]],candidate_n_list,an_list]
                        complete_list.append(complete_item_an)
                    if len(saa_c):
                        candidate_ac=sorted(saa_c, key=lambda x:x[4],reverse=True)
                        pick_final_ac=[]
                        ac_list=[]
                        for ac in candidate_ac:
                            for da_key,da_value in all_doc_adj.items():
                                if ac[0]== da_key:
                                    ac_list.append(ac[0])
                                    idf_value=(ac[4]*1.0/final_n_count)*(log(d_count*1.0/(1+da_value)))*(log(d_count*1.0/(1+final_n_count)))
                                    pick_final_ac.append([ac[0],idf_value,ac[1],ac[3].strip('\r\n')])
                        pick_final_ac=sorted(pick_final_ac,key =lambda x:x[1],reverse=True)
                        complete_item_ac=[[final_n,pick_final_ac[0][0],pick_final_ac[0][2],pick_final_ac[0][3]],candidate_n_list,ac_list]
                        complete_list.append(complete_item_ac)
                    else:
                        continue   
                else:
                    continue
        for line in complete_list:
            fw.write(str(line))
            fw.write('\n')
        return complete_list
#---------------------------------------------------------------------------------------#
        #关于形容词的合并，应该参考逆文档频率，对不同的名词下的形容词的条件概率
        #adj_list=Create_dict.Combine_adj_dict(fd,fwd)
        #adj_G=G_model.Create_G_model(adj_list,model)
        #cluster_merge.Get_merge_similarity(adj_G,adj_list,G_model,model,fw)

        #find_most_appropriate()
        #for item in new_entity_list:
        #    for inter_item in range(0,len(item)):
        #        fw.write(str(inter_item))
        #        fw.write("  ")
        #    fw.write("\n")
            #compare_key=str(entity_a[0])+str(entity_b[0])
            #compare_ent_dic[compare_key]=model.similarity(str(entity_a[0]),str(entity_b[0]))











