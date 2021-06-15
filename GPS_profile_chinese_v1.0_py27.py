#! /usr/bin/env python2
# _*_ coding: utf-8 _*_
import arcpy
from arcpy import env
from os import sep
import pandas as pd
import numpy as np
import math, os
import matplotlib.pyplot as plt
import pylab as plt

###################################################################
# 系统和版本要求：windows ; arcgis10.8 ; python2.7 ;
###################################################################
### 你只需要修改这个部分里的内容
fp1 = "E:/data" # 新建一个工作文件夹 # 将在googleearth里绘制的kml断层线保存到这个文件夹
fp2 = "E:/data/projections.gdb" # 在工作文件夹下新建一个gdb，在这个gdb里放置数据库格式的GPS,必须命名为inGPS_WGS
faultname = "Altyn_Tagh_fault.kml" # 与googleearth里绘制的断层名字一样
outCS = arcpy.SpatialReference('WGS 1984 World Mercator') # 定义一个投影坐标系,根据具体情况可修改
profile_len = "300 Kilometers" # GPS剖面长度
###################################################################
### 以下部分的代码切勿修改
# 清理上一次运行过程中生成的一些文件，否则容易报错
arcpy.Delete_management(fp2 + "/Polylines")
arcpy.Delete_management(fp2 + "/Polylines_UTM")
arcpy.Delete_management(fp2 + "/outGPS_UTM")
arcpy.Delete_management(fp2 + "/rectangle_UTM")
arcpy.Delete_management(fp2 + "/mysites")
###################################################################
arcpy.env.workspace = fp1 # 定义工作文件夹的位置
# 断层转换格式
for kml in arcpy.ListFiles(faultname):
    arcpy.KMLToLayer_conversion(kml, fp1) # 这一步会在工作文件夹里生成一个和断层名称相同的gdb,当你第二次运行代码的时候必须删除
for fgdb in arcpy.ListWorkspaces(faultname, 'FileGDB'):
    arcpy.env.workspace = fgdb
    for fc in arcpy.ListFeatureClasses('*', '', 'Placemarks'):
        arcpy.CopyFeatures_management(fc, fp2+"\\"+str()+fc)
# 提示成功
print("step01_kml2shp ok!")
###################################################################
arcpy.env.workspace = fp2 # 定义工作空间的位置
###################################################################
# 投影变换
arcpy.Project_management("inGPS_WGS","outGPS_UTM",outCS)
arcpy.Project_management("Polylines","Polylines_UTM",outCS)
# 提示成功
print("step02_project2utm ok!")
###################################################################
# 建立缓冲区
arcpy.Buffer_analysis("Polylines_UTM", "rectangle_UTM", profile_len, "FULL", "FLAT", "LIST") 
# 提示成功
print("step03_buffer ok!")
###################################################################
# 提取GPS站点
arcpy.Intersect_analysis (["outGPS_UTM", "rectangle_UTM"], "mysites", "ALL", "", "")
# 提示成功
print("step04_intersection ok!")
###################################################################
# 计算距离
arcpy.Near_analysis('mysites', 'Polylines_UTM','','LOCATION','ANGLE','PLANAR')
# 提示成功
print("step05_near ok!")
###################################################################
### 对上面生成的数据进行整理导出为txt
#定义读取文件函数
shppath = fp2+"/mysites" 
# 提取shp文件中的'field1', 'field2', 'field3', 'field4', 'field5', 'field6', 'field7', 'field8', 'near_dist', 'near_angle'字段 = long,lat,ve,vn,se,sn,cor,site,disance，trend
shpfields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6', 'field7', 'field8', 'near_dist', 'near_angle']
shp_1 = []
shp_2 = []
shp_3 = []
shp_4 = []
shp_5 = []
shp_6 = []
shp_7 = []
shp_8 = []
shp_9 = []
shp_10 = []
shprows = arcpy.SearchCursor(shppath, shpfields)
while True:    
    shprow = shprows.next()
    if not shprow:
        break
    shp_1.append(shprow.field1)
    shp_2.append(shprow.field2)
    shp_3.append(shprow.field3)
    shp_4.append(shprow.field4)
    shp_5.append(shprow.field5)
    shp_6.append(shprow.field6)
    shp_7.append(shprow.field7)
    shp_8.append(shprow.field8)
    shp_9.append(shprow.near_dist)
    shp_10.append(shprow.near_angle)
###################################################################
### 定义速度公式
#def v(ve, vn, ta):
#    return ve*math.cos(ta) - vn*math.sin(ta)
###################################################################
# 获取angle中的最大最小值，以此判断断层走向
angle_min = min(shp_10)
angle_max = max(shp_10)
print(angle_min,angle_max)
ta = math.radians(abs(angle_min)) #角度转弧度
normalv = []
normalerr = []
parallv = []
parallerr = []
# 利用for循环计算垂直和平行断层的速度 
for i in range(0, len(shp_1)):
    
    normalv.append( shp_3[i]*math.cos(ta) - shp_4[i]*math.sin(ta))

    normalerr.append ( math.sqrt(shp_5[i]**2*math.cos(ta)**2 + shp_6[i]**2*math.sin(ta)**2) )

    parallv.append( shp_3[i]*math.sin(ta) + shp_4[i]*math.cos(ta))

    parallerr.append( math.sqrt(shp_5[i]**2*math.sin(ta)**2 + shp_6[i]**2*math.cos(ta)**2))

    print (shp_1[i], shp_2[i], shp_3[i],shp_4[i], shp_5[i], shp_6[i],shp_7[i], shp_8[i],shp_9[i], shp_10[i], normalv[i], normalerr[i], parallv[i], parallerr[i])

# 整理数据，生成list,将list进行转置生成df
    data = {
        'lon':shp_1,
        'lat':shp_2,
        've':shp_3,
        'vn':shp_4,
        'se':shp_5,
        'sn':shp_6,
        'cor':shp_7,
        'site':shp_8,
        'dist':shp_9,
        'angle':shp_10,
        'normalv':normalv,
        'normalerr':normalerr,
        'parallv':parallv,
        'parallerr':parallerr }
df = pd.DataFrame(data) #,index=['one','two','three','four','five','six','seven','eight']
cols=['lon','lat','ve','vn','se','sn','cor','site','dist','angle','normalv','normalerr','parallv','parallerr']
df=df.ix[:,cols] # 该语句表示，dataframe的行索引不变，列索引是cols中给定的索引
# print(df)
# print(df.info())
### 区分距离的方向
df1 = df[df['angle']<0]
# df2 = df1.loc[:,"dist"*-1]  
df1.loc[:,"dist"] = df1["dist"] * -1  # print(df1) 可以打印出来看看
df2 = df[df['angle']>0] # print(df2) 可以打印出来看看
df = df1.append(df2)
print (df)
# 将df写入txt
f = open(fp1+"/results.txt","w")
df.to_csv(fp1+"/results.txt",index=False,sep=',',encoding='utf_8_sig') # 输出一个包含所有数据的txt
f.close()
# 提示成功
print("step06 output_results ok!")
###########################################################################
### 绘图
plt.figure()
# 绘制垂直断层速度
plt.subplot(2,1,1)
x = df['dist']/1000
y = df['normalv']
yerr = df['normalerr']
plt.errorbar(x, y,yerr=yerr, fmt='bo',linewidth = 1, capsize=4, capthick=2)
plt.title('GPS velocity component perpendicular to the fault')
#plt.legend()
plt.xlabel('Distance(km)')
plt.ylabel('Velocity(mm/yr)')
plt.grid(axis='both')
# 绘制平行断层速度
plt.subplot(2,1,2)
x = df['dist']/1000
y = df['parallv']
yerr = df['parallerr']
plt.errorbar(x, y,yerr=yerr, fmt='bo',linewidth = 1, capsize=4, capthick=2)
plt.title('GPS velocity component parallel to the fault')
#plt.legend()
plt.xlabel('Distance(km)')
plt.ylabel('Velocity(mm/yr)')
plt.grid(axis='both')
plt.show()
# 提示成功
print("step07 plot_figure ok!")
### 剖面左侧代表断层北侧的站点，剖面右侧代表断层南侧的站点
###########################################################################
# 提示成功
print("step08 all ok!")
###########################################################################
####必读####
####必读####
####必读####
### 本代码的优点是方便快捷，但目前仅支持一次提取一个剖面
### 目前代码每次运行会将上一次在gdb里生成的一些文件删除，因此，如果有需求，建议读者每次运行之后进行保存
### 当你提取相同名称断层的剖面时，你必须提前删除和断层名字相同的gdb，该gdb位于第一步kml2shp
### 如有任何疑问请邮件：15727399488@163.com

