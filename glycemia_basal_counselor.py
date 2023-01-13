#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:57:29 2023

@author: freddy@linuxtribe.fr
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import csv
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter1d
import colorsys
import datetime

def scale_lightness(rgb, scale_l):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(1, l * scale_l), s = s)

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--mydiabbycsvfile", default='myDiabby_data_20230113_fake_id.csv')
parser.add_argument("-n", "--name", type=str, default='name')
parser.add_argument("-ln", "--lastname", type=str, default='last name')
parser.add_argument("-a", "--age", type=str, required=True)
parser.add_argument("-w", "--weight", required=True, type=float)
parser.add_argument("-is", "--insulinsensitivity", required=True, type=int)
parser.add_argument("-df", "--dateforward", type=int, default=15)
parser.add_argument("-ecmd", "--enablemediandeviationcorrection", type=bool, default=False)
parser.add_argument("-cmd", "--correctmediandeviation", type=int, default=30)

args = parser.parse_args()

glycemia_stats = {}
glycemia_x = []
glycemia_median = []
glycemia_mg_p10 = []
glycemia_mg_p25 = []
glycemia_mg_p75 = []
glycemia_mg_p90 = []
glycemia_min = []
glycemia_max = []

def hm2int(hm):
	return(int(hm.split(':')[0])*3600+int(hm.split(':')[1])*60)

def int2hm(i):
	h = int(i/3600)
	m = int((i-h*3600)/60)
	hm = str(h)+ 'h' + str(m)	
	return(hm)

def correctDeviation(data, target):
	d_max = target+1
	while (d_max>target):
		i=0
		d_max = 0
		for v in data:
			d = abs(data[i-1]-data[i])
			if d>d_max:
				d_max=d
			if i>0:
				data[i-1] = (data[i-1]+data[i])/2 
			i+=1
	return(data)

capture = False;
start_date = datetime.datetime.today() - datetime.timedelta(days=args.dateforward)
end_date = datetime.datetime.now()

with open(args.mydiabbycsvfile, newline='') as mydiabby:
	mydiabby_export = csv.reader(mydiabby,delimiter=',')
	for mydiabby_line in mydiabby_export:
		t = str(mydiabby_line[1])
		
#		if args.date not in mydiabby_line[0]: # filtering mode
#			continue

		if str(start_date).split(" ")[0] in mydiabby_line[0]:
			capture = True
		
		if not capture:
			continue
			
		if 'time' in t:
			continue
		glycemia = mydiabby_line[2]
		if glycemia == '':
			continue
	
		glycemia = int(mydiabby_line[2])
		if t not in glycemia_stats.keys():
			glycemia_stats[t] = []
		glycemia_stats[t].append(glycemia)


for t in sorted(glycemia_stats.keys()):
	glycemia_x.append(hm2int(t))
	glycemia_median.append(np.median(glycemia_stats[t]))
	glycemia_mg_p10.append(np.percentile(glycemia_stats[t],10))
	glycemia_mg_p25.append(np.percentile(glycemia_stats[t],25))
	glycemia_mg_p75.append(np.percentile(glycemia_stats[t],75))
	glycemia_mg_p90.append(np.percentile(glycemia_stats[t],90))
	glycemia_min.append(min(glycemia_stats[t]))
	glycemia_max.append(max(glycemia_stats[t]))


def lfunc(slope, intercept, x):
	return slope * x + intercept

def linear_regression(t_start, t_end, data):
	t0 = t_start
	t1 = t_end

	x_selection = []
	y_selection = []

	i = 0
	for x in glycemia_x:
		if (x>=t0 and x<=t1):
			x_selection.append(glycemia_x[i])
			y_selection.append(data[i])
		i+=1

	slope, intercept, r, p, std_err = stats.linregress(x_selection, y_selection)
    
	segment = [lfunc(slope,intercept,x_selection[0]), lfunc(slope,intercept,x_selection[-1])]
		
	return(segment) # return y values as a table for t_start and t_end x position 


if args.enablemediandeviationcorrection:
	glycemia_median = correctDeviation(glycemia_median, args.correctmediandeviation)
	glycemia_min = correctDeviation(glycemia_min, args.correctmediandeviation)
	glycemia_max = correctDeviation(glycemia_max, args.correctmediandeviation)
	glycemia_mg_p10 = correctDeviation(glycemia_mg_p10, args.correctmediandeviation)
	glycemia_mg_p25 = correctDeviation(glycemia_mg_p25,args.correctmediandeviation)
	glycemia_mg_p75 = correctDeviation(glycemia_mg_p75,args.correctmediandeviation)
	glycemia_mg_p90 = correctDeviation(glycemia_mg_p90, args.correctmediandeviation)

fig, ax = plt.subplots()
median_patch = mpatches.Patch(color='indigo', label='median', alpha=0.25)
mg_p25_75_patch = mpatches.Patch(color='blueviolet', label='25-75%', alpha=0.25)
mg_p10_90_patch = mpatches.Patch(color='violet', label='10-90%', alpha=0.25)
minmax_patch =  mpatches.Patch(color='mediumpurple', label='min-max', alpha=0.25)
ax.legend(handles=[median_patch,mg_p25_75_patch,mg_p10_90_patch,minmax_patch])
  
plt.suptitle("OpenSource Insulin Basal Counselor",fontsize=20)

plt.text(-5000,360,s="DISCUSS THE RESULTS WITH YOUR DOCTOR TO DEFINE WHAT TO DO FIRST",color='red',fontsize=7)
plt.text(-5000,366,s="!!! DO NOT APPLY ALL RECOMMANDED CHANGES AT THE SAME TIME !!! ",color='red',fontsize=7)
plt.text(-5000,372,s="WARNINGS !!! DO NOT USE THIS TOOL WITH HEALTH DATA OLDER THAN 15 days",color='red',fontsize=7)

plt.text(8*3600,354,s="data source:        "+args.mydiabbycsvfile,fontsize=7)
plt.text(8*3600,360,s="date:                   "+str(datetime.datetime.now()),fontsize=7)
plt.text(8*3600,366,s="data length :       "+str(args.dateforward)+" days",fontsize=7)
plt.text(8*3600,372,s="data start :          "+str(start_date),fontsize=7)

plt.text(14.5*3600,372,s="patient : "+args.name+" "+args.lastname,fontsize=7)
plt.text(14.5*3600,366,s="age : "+str(args.age),fontsize=7)
plt.text(14.5*3600,360,s="weight : "+str(args.weight)+"Kg",fontsize=7)
plt.text(14.5*3600,354,s="insulin sensitivity : "+str(args.insulinsensitivity)+" mg/dl for 1U",fontsize=7)

plt.text(21.3*3600,372,s='author: Freddy Frouin <freddy@linuxtribe.fr>',fontsize=7)
plt.text(21.3*3600,366,s="revision : beta v0.5",fontsize=7)
plt.text(21.3*3600,360,s="created on : 20230111",fontsize=7)
plt.text(21.3*3600,354,s="sources : https://github.com/ffrouin/myDiabby",fontsize=7)

plt.text(-5000,-20,s="The OpenSource Insulin Counseler takes patient meals time as entry data table and then it looks for the daily time ranges where the glucose",fontsize=7)
plt.text(-5000,-26,s="concentration in blood should be stable. In these areas, using a linear regressive process against the median values of glucose concentration",fontsize=7)
plt.text(-5000,-32,s="helps to evaluate how to modify the patient basal scheme. In this example, meals are planned at 7am 12am 16pm and 19pm and we do exclude",fontsize=7)
plt.text(-5000,-38,s="2h after meals of processing as this are the areas where glucose concentration may not be stable due to the difference between insulin action",fontsize=7)
plt.text(-5000,-44,s="and the patient digestion of his meal (ie. glucose assimilation process and rates).",fontsize=7)
		 
plt.ylabel('glucose mg/dl')
plt.ylim(0,350)
plt.yticks([0,50,70,100,150,180,200,250,300,350])

plt.xlabel('time')
plt.xticks(ticks=[0,3600,7200,10800,14400,18000,21600,25200,28800,32400,36000,\
				 39600,43200,46800,50400,54000,57600,61200,64800,68400,72000,\
				 75600,79200,82800,86400], labels=['0h00','1h00','2h00','3h00','4h00',
				 '5h00','6h00','7h00','8h00','9h00','10h00','11h00','12h00',\
				 '13h00','14h00','15h00','16h00','17h00','18h00','19h00',\
				 '20h00','21h00','22h00','23h00','24h00'])

plt.bar(-301,350,600,color='red',alpha=0.75)
plt.bar(-301,250,600,color='orange',alpha=0.75)
plt.bar(-301,179,600,color='lightgreen',alpha=0.75)
plt.bar(-301,70,600,color='lightblue',alpha=0.75)
plt.bar(-301,50,600,color='darkblue',alpha=0.75)

plt.bar(86701,350,600,color='red',alpha=0.75)
plt.bar(86701,250,600,color='orange',alpha=0.75)
plt.bar(86701,179,600,color='lightgreen',alpha=0.75)
plt.bar(86701,70,600,color='lightblue',alpha=0.75)
plt.bar(86701,50,600,color='darkblue',alpha=0.75)

plt.axhline(y=70, color="lightblue",linewidth=0.5,linestyle='dashed',alpha=0.75)
plt.axhline(y=180, color="orange",linewidth=0.5,linestyle='dashed',alpha=0.75)
plt.axhline(y=250, color="red",linewidth=0.5,linestyle='dashed',alpha=0.75)	

plt.grid(color='lightblue',alpha=0.25,axis='y')
	   
s=10

plt.fill_between(glycemia_x, gaussian_filter1d(glycemia_max, sigma=s), gaussian_filter1d(glycemia_min, sigma=s), interpolate=True, color='mediumpurple', alpha=0.25)
plt.fill_between(glycemia_x, gaussian_filter1d(glycemia_mg_p10, sigma=s), gaussian_filter1d(glycemia_mg_p90, sigma=s), interpolate=True, color='violet', alpha=0.25)
plt.fill_between(glycemia_x, gaussian_filter1d(glycemia_mg_p25,sigma=s), gaussian_filter1d(glycemia_mg_p75, sigma=s), interpolate=True, color='blueviolet', alpha=0.25)

#plt.scatter(glycemia_x, glycemia_median, 1, color='indigo')

plt.plot(glycemia_x, gaussian_filter1d(glycemia_median, sigma=s), 3, color='indigo')

#plt.plot(glycemia_x, gaussian_filter1d(glycemia_min, sigma=s), 3, color='mediumpurple')
#plt.plot(glycemia_x, gaussian_filter1d(glycemia_max, sigma=s), 5, color='mediumpurple')
#plt.plot(glycemia_x, gaussian_filter1d(glycemia_mg_p10, sigma=s), 1, color='orchid')
#plt.plot(glycemia_x, gaussian_filter1d(glycemia_mg_p25, sigma=s), 1, color='orchid')
#plt.plot(glycemia_x, gaussian_filter1d(glycemia_mg_p75, sigma=s), 1, color='orchid')
#plt.plot(glycemia_x, gaussian_filter1d(glycemia_mg_p90, sigma=s), 1, color='orchid')

meals = [ '07:00', '12:00', '16:00', '19:00' ]
insulin_active_length = 7200 # secs
insulin_sensitivity = args.insulinsensitivity # mg/dl

def basalEfficientRanges(meals):
	range = []
	last = 0
	for m in meals:
		range.append([last, hm2int(m)])
		last = hm2int(m)+insulin_active_length
	range.append([last, 86400])
	return(range)

def basalEfficientSubRanges(ranges):
	positive = False
	subRanges = []
	last = 0
	init = False
	for r in ranges:
		init = True
		for i in range(r[0]+3600,r[1],300):
			seg = linear_regression(i-3600,i+3600, gaussian_filter1d(glycemia_median,sigma=s))
			if seg[1] > seg[0]:
				if not positive:
					positive = True
					if init:
						init = False
						if i - r[0] > 2700:
							subRanges.append([r[0], i])
					else:
						if i - last > 2700:
							subRanges.append([last,i])					
					last = i
			else:
				if positive:
					positive = False
					if init:
						init = False
						if i - r[0] > 2700:
							subRanges.append([r[0], i])
					else:
						if i - last > 2700:
							subRanges.append([last,i])
					last = i
		if r[-1] - last > 2700:
			subRanges.append([last, r[-1]])
	if ranges[-1][-1] - last > 2700:
		subRanges.append([last, ranges[-1][-1]])
	return(subRanges)
		
x = []
y = []

advices_timeranges = []
advices_gdelta = []
advices_iquantity = []
advices_irate = []

# br for basal range
br = basalEfficientRanges(meals)
advices_timeranges = basalEfficientSubRanges(br)

for r in advices_timeranges:
	seg = linear_regression(r[0], r[1], glycemia_median)
	d = abs(((seg[1]-seg[0])/insulin_sensitivity)/((r[1]-r[0])/3600))
	if d < 0.025:
		continue
	x.append([r[0], r[1]])
	y.append(seg)
	advices_gdelta.append(seg[1]-seg[0])
	advices_iquantity.append((seg[1]-seg[0])/insulin_sensitivity)
	advices_irate.append(((seg[1]-seg[0])/insulin_sensitivity)/((r[1]-r[0])/3600))
#	print(int2hm(r[0])+"-"+int2hm(r[1])+" "+str(seg[1]-seg[0])+"mg/dl " + str((seg[1]-seg[0])/160) + "U " + str(((seg[1]-seg[0])/160)/((r[1]-r[0])/3600)) + "U/h")
	
i=0
for r in x:
	color=np.random.rand(3,)
	plt.plot(r,y[i],c=color)
	label = '';
	if advices_irate[i] > 0:
		label = str(int2hm(r[0])+"-"+int2hm(r[1])+" +"+f'{advices_irate[i]:.3f}'+"U/h")
	else:
		label = str(int2hm(r[0])+"-"+int2hm(r[1])+" "+f'{advices_irate[i]:.3f}'+"U/h")
	plt.text((r[0]+r[1])/2,y[i][-1]+50,s=label,fontsize=9,c=scale_lightness(color, 0.75))
	label = ''
	if (advices_gdelta[i] >0):
		label = '[+'
	label += f'{advices_gdelta[i]:.2f}' + 'mg/dl ' + f'{advices_iquantity[i]:.3f}' + 'U]'
	plt.text((r[0]+r[1])/2,y[i][-1]+43,s=label,fontsize=7, c=scale_lightness(color, 0.75))
	i+=1

plt.show()

