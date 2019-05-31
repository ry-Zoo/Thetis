##Thetis
本项目是为了从电商评论中提取出经过同义合并的【名词+形容词】组合，并用这个组合标识评论，同时附带的会辨别评论的情感极性

#操作说明
1.按照/TM_REGION/input中文件的形式，导入源数据
2.修改classification_ini.ini文件
*source_file 源数据路径
*target_file 结果数据路径
*sheet_name 源数据文件sheet页
*comment_index 标识源数据文件中评论数据的位置
*new_col 处理源数据文件中数据列名
*new_col_index 标识源数据文件中所有需要处理的数据的位置
3.运行main.py
4.最终结果可以在TM_REGION/Result/result.txt中检查





