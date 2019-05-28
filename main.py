#-*-coding:utf-8-*-
import sys 
import re
import os
import os.path 
import codecs
import json 
import jieba
import jieba.posseg as pseg
import jieba.analyse 
import configparser
import collections
import xlrd
from pymongo import MongoClient
from re_sort_tag  import Create_dict as Create_dict
from model_engine import model_engine as model_engine
from fp_tree_test2 import extract_items as extract_items
from fp_tree_test2 import treeNode as treeNode

client = MongoClient('43.82.163.215',27017) 
db = client['jd_middle']
collection = db['result']
'''fp_tree use'''
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
def loadSimpDat_f(f,stopwords,fw):
    word_data=[]
    for line in f:
        item = pseg.cut(line)
        for i in item :
            if i.flag in ("a","n","nr","v"):
                if i not in stopwords:
                    fw.write("".join(i.word))
                    fw.write(" ")
        fw.write("\n")
'''fp_tree use'''
def createInitSet(dataSet):
    retDict = {}
    for trans in dataSet:
        retDict[frozenset(trans)] = 1
    return retDict
'''init_dict'''
def Tag_init(fk,freqItems,fdw):
        adj_sequence=set([])
        #n_v_sequence=set([])
        n_v_sequence=[]
        n_a_sequence=[]
        i=0
        for items in freqItems:                                                        #从频繁项集结果中取名词，形容词，动词
            n_li=[]
            v_li=[]
            a_li=[]
            for item in items:
                segs = pseg.cut(str(item).strip())
                for seg in segs:
                    if seg.flag in ["n","nr"]:
                        n_li.append(seg)
                    elif seg.flag in ("v"):
                        v_li.append(seg)
                    elif seg.flag in ("a"):
                        a_li.append(seg)
                    else:
                        continue
                    na_res_li=[]                                                    #组合成名词形容词词组
                    for item_n in n_li:
                        for item_a in a_li:
                            par_1=[]
                            par_1.append(item_n.word)
                            par_1.append(item_a.word)
                            na_res_li.append(par_1)
                    if na_res_li not in n_a_sequence:                                 #将组合添加到集合存放
                        n_a_sequence.append(na_res_li)
                    i=i+1           
        clp_a_tag=[]
        count_a=0
        for raw_a_sent in fk:                                                   #到原文中验证词组是否存在
            sent=re.split(r"[，；！。\s \n]",raw_a_sent)
            for sub_sent in sent:                                                
                a_result=jieba.tokenize(sub_sent)
                res_a_list=[]
                for re_a_li in a_result:                                            #记录句子中单词的位置
                    res_a_list.append(re_a_li)                                      
                for na_list in  n_a_sequence:                                       #在词列表中循环文本
                    for li_a_tag in na_list:
                        if len(li_a_tag)==2:
                            raw_tk_na=[]
                            for tk in res_a_list:
                                if tk[0]==li_a_tag[0]:
                                    raw_tk_na.append([li_a_tag[0],tk[1]])           #判断名词形容词出现次序
                                elif tk[0]==li_a_tag[1]:
                                    raw_tk_na.append([li_a_tag[1],tk[1]])
                                else:
                                    continue
                            if len(raw_tk_na)<2:                                    #说明句子中该词组没有共现                          
                                continue
                            else:
                                par_str="".join(li_a_tag[0])+"/"+str(li_a_tag[1])
                                clp_a_tag.append(par_str)                           #若出现了就记录
                        else:
                            continue
                count_a+=1
        s_clp_a_tag=set(clp_a_tag)                                              #记录频数
        for res_a_items in s_clp_a_tag:
            fdw.write(res_a_items)
            fdw.write("\t")
            fdw.write(str(clp_a_tag.count(res_a_items)))                         #结果是不重复的词组以及其出现的频数
            fdw.write("\n")
        fdw.close()

def Json_Trim(fj,fw,var_list,comment_index):
    row_count=1
    for line in fj:
        wj_dict=collections.OrderedDict()
        product=str(line).split("///")[0]
        for i in range(0,len(var_list)):
            wj_dict[var_list[i][0]]=str(line).split("///")[i+1]
            
        #product_name=str(line).split("///")[1]
        #user_level=str(line).split("///")[2]
        #star=str(line).split("///")[3]
        #comment=str(line).split("///")[4]
        #time=str(line).split("///")[5]
        opinion_tmp =str(line).split("///")[len(var_list)+1]
        opinion_list=opinion_tmp.strip('\n').split(',')
        
        #fw.write(str(opinion_list))
        #print(str(row_count)+":"+str(len(opinion_list)))
        #print(str(len(opinion_list)))      "prouduct_name":"'+product_name+'"
        

        if len(opinion_list)==1:
            try :
                if opinion_list[0]=='':
                    #json_null_str='{"product":"'+product+'","prouduct_name":"'+product_name+'","user_level":"'+user_level+'","star":"'+star+'","comment":"'+comment+'","opinion":"无","emotion":"其他","Polarity":"其他","count":1,"time":"'+time+'"}'
                    json_null_str='{"product":"'+product+'",'
                    for key,value in wj_dict.items():
                        item_str='"'+key+'":"'+value+'"'
                        json_null_str=json_null_str+item_str+','
                    json_null_str=json_null_str+'"opinion":"无","emotion":"其他","Polarity":"其他","count":1}'
                    fw.write(''.join(str(json_null_str).replace('\\','').replace('/','')))
                    fw.write('\n')
                    continue
                else:
                    senti_list=opinion_list[0].split(':::')
                    #print(str(senti_list[2]))
                    #json_null_str='{"product":"'+product+'","prouduct_name":"'+product_name+'","user_level":"'+user_level+'","star":"'+star+'","comment":"'+comment+'","opinion":"'+str(senti_list[0])+'","emotion":"'+str(senti_list[1])+'","Polarity":"'+str(senti_list[2])+'","count":1,"time":"'+time+'"}'
                    json_null_str='{"product":"'+product+'",'
                    for key,value in wj_dict.items():
                        item_str='"'+key+'":"'+value+'"'
                        json_null_str=json_null_str+item_str+','
                    json_null_str=json_null_str+'"opinion":"'+str(senti_list[0])+'","emotion":"'+str(senti_list[1])+'","Polarity":"'+str(senti_list[2])+'","count":1}'
                    fw.write(''.join(str(json_null_str).replace('\\','').replace('/','')))
                    fw.write('\n')
                    continue
            except:
                #json_str='{"product":"'+product+'","prouduct_name":"'+product_name+'","user_level":"'+user_level+'","star":"'+star+'","comment":"'+comment+'","opinion":"无","emotion":"其他","Polarity":"其他","count":1,"time":"'+time+'"}'
                json_null_str='{"product":"'+product+'",'
                for key,value in wj_dict.items():
                    item_str='"'+key+'":"'+value+'"'
                    json_null_str=json_null_str+item_str+','
                json_null_str=json_null_str+'"opinion":"无","emotion":"其他","Polarity":"其他","count":1}'
                fw.write(''.join(str(json_str).replace('\\','').replace('/','')))
                fw.write('\n')
                continue
        else:
            try:
                cur_flag=1 
                for op_items in opinion_list:
                    #json_str='{"product":"'+product+'","prouduct_name":"'+product_name+'","user_level":"'+user_level+'","star":"'+star+'","comment":"'+comment+'","opinion":"'
                    json_str='{"product":"'+product+'",'
                    for key,value in wj_dict.items():
                        item_str='"'+key+'":"'+value+'"'
                        json_str=json_str+item_str+','
                    json_str=json_str+'"opinion":"'
                    op=op_items.split(':::')
                    #fw.write('##'+str(op))
                    if cur_flag==1:
                        #print('innnn')
                        count=1
                        json_str=json_str+op[0]+'","emotion":"'+op[1]+'","Polarity":"'+op[2].strip('\n')+'","count":'+str(count)+'}'
                        fw.write(''.join(str(json_str).replace('\\','').replace('/','')))
                        fw.write('\n')
                    else:
                        #fw.write(str(op))
                        #print('ooooot')
                        count=0
                        json_str=json_str+op[0]+'","emotion":"'+op[1]+'","Polarity":"'+op[2].strip('\n')+'","count":'+str(count)+'}'
                        fw.write(''.join(str(json_str).replace('\\','').replace('/','')))
                        fw.write('\n')
                    cur_flag=0
            except:
                #json_str='{"product":"'+product+'","prouduct_name":"'+product_name+'","user_level":"'+user_level+'","star":"'+star+'","comment":"'+comment+'","opinion":"无","emotion":"其他","Polarity":"其他","count":0,"time":"'+time+'"}'
                json_str='{"product":"'+product+'",'
                for key,value in wj_dict.items():
                    item_str='"'+key+'":"'+value+'"'
                    json_str=json_str+item_str+','
                json_str=json_str+'"opinion":"无","emotion":"其他","Polarity":"其他","count":0}'
                fw.write(''.join(str(json_str).replace('\\','').replace('/','')))
                fw.write('\n')
                continue
        row_count+=1

'''数据验证主函数'''
def extracting_tag(tag_dic,ft,fw,fj,name,stopwords,ec_dic,var_list,comment_index):                         

    n_a_sequence=[]																	
    i=0

    for combination in tag_dic:
        fianltag=combination[0]
        candidate_entity=combination[1]
        candidate_adj=combination[2]
        n_a_sequence.append(combination)

    count_a=0
    var_len=len(var_list)
    var_dic=collections.OrderedDict()
    Comment_col_name=''
    for raw_a_sent in ft:
        #print('here')
        for vle in range(var_len):
            if int(var_list[vle][1])<0:
                var=' '
            elif int(var_list[vle][1])>=0:
                if int(var_list[vle][1])==comment_index:
                    var=raw_a_sent.split('>>>')[vle]
                    Comment_col_name=var_list[vle][0]
                else:    
                    var=raw_a_sent.split('>>>')[vle]
            else:
            	print('please check your variable')
            	break
            var_dic[var_list[vle][0]]=var

        try:	
            #适格短语运载仓，ha chi jion bi															
            par_na_li=[]															

            #根据标点分割成
            sent=re.split(r"[，；！。!,.\s \n]",var_dic[Comment_col_name])	
            #判断小句的个数								
            i = len(sent)											
            for sub_sent in sent:
                fw.write(sub_sent)
                fw.write("\n")
                par_n_li=[]
                else_word=[]
                #预设否定词
                neg_word=['没有','没','不','不算','不太','无','不会']
                #小句分词
                segs = pseg.cut(sub_sent)
                #词序标注用
                index=0								
                for seg in segs:
                    #小句里所有的词
                    else_word.append([seg.word,index])
                    #记录名词
                    if seg.flag in ("n") and seg.word not in stopwords:								
                        par_n_li.append(seg.word)
                    #记录形容词，形容词前必须有修饰对象
                    if seg.flag in ("a") and len(par_n_li) and seg.word not in stopwords:				
                        par_a=seg.word
                        for na_list in n_a_sequence:
                            for value_a in na_list[2]:
                                #小句形容词匹配短语形容词
                                if par_a==str(value_a):
                                    flag=False
                                    #存储捕获的小句组合中的名词
                                    cur_n=""
                                    #形容词匹配的状况下小句名词匹配短语名词
                                    for i in else_word:
                                        for value_n in na_list[1]:
                                            if str(value_n)==str(i[0]):
                                                cur_n=str(value_n)
                                                flag=True
                                                continue
                                    #小句短语组合捕捉到的情况下：检证该组合在语境中是否具有否定含义
                                    if flag:
                                        #该小句到该形容词为止，是否存在否定词
                                        tmp = [val for val in else_word if val[0] in neg_word]
                                        #存在的话：
                                        if len(tmp):
                                            #双重否定的话：
                                            if len(tmp)==2:
                                                #粗暴一点，反正是双重否定句，不管位置了，组合语义不变，直接填充适格短语运载仓，（名词形容词，名词，形容词）
                                                par_na_li.append((cur_n+str(par_a),str(na_list[0][2]),str(na_list[0][3])))
                                            #print(str(tmp[0]))
                                            #否定的话：判断否定词的位置
                                            else:
                                                #else_word序列中有单词位置信息
                                                n_pos=[tn for tn in else_word if str(cur_n)==tn[0]]
                                                fw.write(str(n_pos))
                                                a_pos=[ta for ta in else_word if str(par_a)==ta[0]]
                                                fw.write(str(a_pos))
                                                #一个小句应该不会出现三个否定词吧，排除了两个的情况，只有一个的序列，所以第一位的就是我们需要的否定词
                                                neg_pos=tmp[0]
                                                #否定词在形容词名词中间，反转极性和改变感情方向，中性照旧
                                                if neg_pos[1]>=n_pos[0][1] and neg_pos[1]<=a_pos[0][1]:
                                                    #print('in')
                                                    porlarity=""
                                                    emotion=""
                                                    if str(na_list[0][3])=='1':
                                                        emotion="NN"
                                                        porlarity='2'
                                                    elif str(na_list[0][3])=='2':
                                                        porlarity='1'
                                                        emotion="PH"
                                                    else:
                                                        porlarity='0'
                                                        emotion=str(na_list[0][2])
                                                    #有否定词的装填适格短语运载仓
                                                    par_na_li.append((cur_n+neg_pos[0]+str(par_a),emotion,porlarity))
                                                else:
                                                    #默认方式的装填适格短语运载仓
                                                    par_na_li.append((cur_n+str(par_a),str(na_list[0][2]),str(na_list[0][3])))
                                        else:
                                            par_na_li.append((cur_n+str(par_a),str(na_list[0][2]),str(na_list[0][3])))
                                    else:
                                        continue
                                else:
                                    continue
                    index+=1
        except Exception as e:
            s=sys.exc_info()
            print("Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            continue
        #每个小句的检证结束：短语运载仓放入短语蛆虫集装箱s_par_na_li，因为是集合
        s_combine_tag=set()
        #将列表转换为集和类型达到去重的效果
        s_par_na_li=set(par_na_li)													
        fw.write("NA_TAG:\n")

        #解包显示一下
        for tmp_na_items in s_par_na_li:
            fw.write(str(tmp_na_items))
            fw.write("  ")
        fw.write("\n")

        #极性用中文标识
        tmp_opnion=""
        for combine in s_par_na_li:
            #在emotion_category里检证一下
            for cate in ec_dic:
                #保证这个形容词匹配上
                if str(combine[1].strip()) == str(cate[1].strip()):
                    if str(combine[2])=='0' :
                        tmp_opnion=tmp_opnion+combine[0]+":::"+str(cate[0])+":::中性,"
                    if str(combine[2])=='1' :
                        tmp_opnion=tmp_opnion+combine[0]+":::"+str(cate[0])+":::积极,"
                    if str(combine[2])=='2' :
                        tmp_opnion=tmp_opnion+combine[0]+":::"+str(cate[0])+":::消极,"
                else:
                    continue

        #json集装箱：类别，原句（按小句发送），观点信息（短语，感性方向，极性）
        #json_raw_dta=name.split(".")[0]+"///"+prouduct_name+"///"+user_level+"///"+star+"///"+treasure_comment[:-2]+"///"+treasure_time[:-2]+"///"+tmp_opnion[:-1]
        json_raw_dta=name.split(".")[0]+'///'
        for key,value in var_dic.items():
            if key=="comment" or key=="time":
                #json_raw_dta=json_raw_dta+str(value)[:-2]+'///'
                json_raw_dta=json_raw_dta+str(value)+'///'
            else:
                json_raw_dta=json_raw_dta+value+'///'
        json_raw_dta=json_raw_dta+tmp_opnion[:-1]
        fj.write(''.join(str(json_raw_dta)))
        fj.write("\n")
        count_a+=1

if __name__ == "__main__":
    #fd=open("tb_tag_res5.txt","r",encoding='utf8')
    #start=time.clock()
    cp = configparser.ConfigParser()
    cur_path=os.path.abspath(os.curdir)

    print(str(cur_path)+'\\classification_ini.ini')

    cp.read(str(cur_path)+'\\classification_ini.ini')

    result_file_str= str(cp.items('Path_for_excel')[1][1]).split('\\')[-1]
    print(result_file_str)
    source_file = cur_path +'\\'+ str(cp.items('Path_for_excel')[0][1])
    target_file=  cur_path +'\\'+ str(cp.items('Path')[7][1])+result_file_str
    print(target_file)
    fw=codecs.open("jdexample.txt","w",'utf8')
    #打开文件
    ex_data = xlrd.open_workbook(source_file)

    sheet_name=str(cp.items('Path_for_excel')[2][1])
    sheet2 = ex_data.sheet_by_name(sheet_name)

    nrows = sheet2.nrows   #行
    ncols = sheet2.ncols   #列
    print(nrows,ncols)

    check_path = cur_path+'\\'+str(cp.items('Path')[8][1])+result_file_str
    print(str(check_path))
    rfw=codecs.open(target_file,"w",'utf8')
    rfw2=codecs.open(check_path,"w",'utf8')
    #modelcode_index=int(cp.items('Path_for_excel')[4][1])
    #level_index=int(cp.items('Path_for_excel')[5][1])
    #star_index=int(cp.items('Path_for_excel')[6][1])
    comment_index=int(cp.items('Path_for_excel')[3][1])
    #time_index=int(cp.items('Path_for_excel')[8][1])
    new_col=[col_name for col_name in cp.items('Path_for_excel')[4][1].split(',')]              #追加新的列
    new_col_index=[col_index for col_index in cp.items('Path_for_excel')[5][1].split(',')]       #追加新列在excel中的列号
    #add_index=len(new_col_index)                        #追加的列数

    #user_def_col=[modelcode_index,level_index,star_index,comment_index,time_index]
    #user_def_col.append(new_col_index)


    current_index=len(new_col_index)						#用户自定义的总计的列数
    print('current_index:'+str(current_index))

    var_list=[]
    for col in range(current_index):
        var_list.append([new_col[col],new_col_index[col]])


    #print("comment_index"+str(comment_index))
    model_code_dict=set()
    excel_item=[]
    for l in range(2,nrows):
        for i in var_list:
            if int(i[1])<0:
                current_value= ' '
                globals()[i[0]]=current_value
            else:
                current_value=str(sheet2.row(l)[int(i[1])].value)
                globals()[i[0]]=current_value
                if int(i[1]) == int(comment_index):
                    #print(str(i[1]))
                    rfw.write(str(current_value)+'\n')
            cur_item=[current_value]
            rfw2.write(str(current_value)+'>>>')
        rfw2.write('\n')
        model_code_dict.add(model_code)
        excel_item.append(cur_item)
    print('input Done')

    '''
    for m in model_code_dict:
        for item in excel_item:
            if str(item[0])==str(m):
                rfw.write(str(item[comment_index])+'\n')
                for index in range(current_index):
                    if index==current_index:
                        rfw2.write(str(item[index])+'\n')
                    else:
                        rfw2.write(str(item[index])+'>>>')
    '''
    '''
    path = str(cp.items('Path')[0][1])
    files_cs = codecs.open(path+ResultFile+".txt","w",'utf8')
    new_txt_path = 'C:\\Users\\7000014355\\Documents\\TM\\cut_res\\'+ResultFile+'.txt'
    Nfw = codecs.open(new_txt_path, 'w', encoding='utf-8')
    stopwords={}
    fstop = open('stopLibrary.dic', 'r',encoding="utf8")
    for eachWord in fstop:
        stopwords[eachWord.strip()] = eachWord.strip()
    fstop.close()
    jieba.load_userdict(str(cp.items('Path')[1][1]))
    loadSimpDat_f(files_cs,stopwords,Nfw)
    '''
    '''
    导入完毕，开始处理
    '''
    path = str(cur_path) +'\\'+ str(cp.items('Path')[0][1])
    files = os.listdir(path) 
    for file in files:                      #需要下钻到型号层，从目录内读型号划分的文件
        name=str(file)                      #需要创建一个函数构建型号类别对应结构
        #res_path = 'C:\\Users\\7000014355\\Documents\\TM\\category_res\\'+file
        example_path= str(cur_path) +'\\'+ str(cp.items('Path')[0][1])+file
        '''
        调用fp_tree
        '''
        f = codecs.open(example_path,'r',encoding='utf-8')
        stopwords={}
        fstop = open( str(cur_path) +'\\'+ str(cp.items('Path')[9][1]), 'r',encoding="utf8")
        for eachWord in fstop:
            stopwords[eachWord.strip()] = eachWord.strip()
        fstop.close()
        jieba.load_userdict(str(cur_path) +'\\'+ str(cp.items('Path')[1][1]))
        simpDat = loadSimpDat(f,stopwords)
        initSet = createInitSet(simpDat)
        '''构建树'''
        extract_obj=extract_items()
        myFPtree , myHeaderTab = extract_obj.createTree(initSet, 5)

        freqItems = []
        '''获得频繁集'''
        extract_obj.mineTree(myFPtree, myHeaderTab, 5, set([]), freqItems)
        print('fp_tree compelete')

        emotion_category_path=str(cur_path) +'\\'+ str(cp.items('Path')[2][1])
        #f = codecs.open(res_path,'r',encoding='utf-8')
        fk = codecs.open(example_path,'r',encoding='utf-8')
        '''初始字典生成'''
        tag_dic_path=str(cur_path) +'\\'+ str(cp.items('Path')[4][1])+file
        fdw =codecs.open(tag_dic_path, 'w', encoding='utf-8')
        Tag_init(fk,freqItems,fdw)
        print('init_dict compelete')
        ec = codecs.open(emotion_category_path,'r',encoding='utf-8')
        tag_dic ={}

        
        
        fd = codecs.open(tag_dic_path,'r',encoding='utf-8')
        sa_dict_path = str(cur_path) +'\\'+ str(cp.items('Path')[3][1])
        fsa =codecs.open(sa_dict_path, 'r', encoding='utf-8')
        new_txt_path =  str(cur_path) +'\\'+ str(cp.items('Path')[5][1]) + file
        fw = codecs.open(new_txt_path, 'w', encoding='utf-8')
        new_json_path = str(cur_path) +'\\'+ str(cp.items('Path')[6][1]) + file
        fj = codecs.open(new_json_path, 'w', encoding='utf-8')
        #tag_dic=combine_tag(fd,fw)
        jieba.load_userdict(str(cur_path) +'\\'+ str(cp.items('Path')[1][1]))

        sa_dic_list=[]
        for line in fsa:
            aw_list=line.split('\t')
            sa_dic_list.append(aw_list)
        sa_dict=sa_dic_list


        ec_dic=[]
        for line in ec:
            ec_list=line.split(' ')
            ec_dic.append(ec_list)
        #print(str(len(sa_dict)))
        engine=model_engine(fd,fdw,sa_dict,name)
        tag_dic=engine.Merge()
        #print('停止')
        ft = codecs.open(check_path,'r',encoding='utf-8')
        extracting_tag(tag_dic,ft,fw,fj,name,stopwords,ec_dic,var_list,comment_index)     #届时此处需传入两个name参数，一个类别name，一个型号name
        fj.close()
        fj = codecs.open(new_json_path,'r',encoding='utf-8')
        new_last_path = str(cur_path) +'\\'+ str(cp.items('Path_for_excel')[1][1]) 
        print(str(new_last_path))
        fe = codecs.open(new_last_path,'w',encoding='utf-8')
        Json_Trim(fj,fe,var_list,comment_index)
        fe.close()



