import requests
import json
import http.client
import base64
from re import sub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

def plt_show(plt, width=1200, dpi=300):
# Converts matplotlib plt to image data string
# plt is the matplotlib pyplot or figure
# width is the width of the graph image in pixels
# dpi (dots per inch) is the resolution of the image
bytes = io.BytesIO()
plt.savefig(bytes, format='png', dpi=dpi) # Save as png image
if hasattr(plt, "close"):
plt.close()
bytes.seek(0)
base64_string = "data:image/png;base64," + \
base64.b64encode(bytes.getvalue()).decode("utf-8")
return "<img src='" + base64_string + "' width='" + str(width) + "'>"

def main(inputs):
city = inputs['city']
city_lower = city.replace(' ', '-').lower() 
city_title = sub(r"(_|-)+", " ", city).title() 

#AQ Data
response = requests.get('https://api.waqi.info/feed/'+ city_lower + '/?token=cb2638dede48dcdbfaa20aa4474611eef3daad2e')
aq_data = response.json()
#AQI number
try:
aqi = round(aq_data['data']['aqi'],1)
except:
aqi = 50

try:
aqi_no2= round(aq_data['data']['iaqi']['no2']['v'],1)
except:
aqi_no2 = 20

authkey = 'a49891c702df0dffa051ca5258142892:6f24285a6f6f7a4f63240f257c5f3c3f'
encoded_bytes = base64.b64encode(authkey.encode("utf-8"))
auth_key = str(encoded_bytes, "utf-8")
payload = ''
headers = {'Authorization': f'Basic {auth_key}'}
response = requests.get('https://api.roadgoat.com/api/v2/destinations/auto_complete?q=' + city, headers=headers)
result = response.json()
city_id = city_lower
try:
for destination in result['data']:
if destination ['attributes']['destination_type'] == 'City':
city_id = destination['id']
city_data_slug = destination ['attributes']['slug']
break 
except:
pass
if city_id is None:
city_id = city_lower

response = requests.get('https://api.roadgoat.com/api/v2/destinations/' + city_id, headers=headers)
roadgoat_result = response.json()

#budget
rg_rows = []
try: 
s3 = roadgoat_result['data']['attributes']['budget']
for key in s3:
rg_rows.append(['Cost of Living', key, round(s3[key]['value'], 1), s3[key]['text'], s3[key]['subText']])
except KeyError:
rg_rows.append(['Cost of Living', "no data", 0, "missing data", "missing"])

try:
s3 = roadgoat_result['data']['attributes']['safety']
for key in s3:
rg_rows.append(['Safety', key, round(s3[key]['value'], 1), s3[key]['text'], s3[key]['subText']])
except KeyError:
rg_rows.append(['Safety', "no data", 0, "missing data", "missing"])

try: 
s3 = roadgoat_result['data']['attributes']['covid']
for key in s3:
rg_rows.append(['Covid Risk', key, round(s3[key]['value'], 1), s3[key]['text'],""])
except KeyError:
rg_rows.append(['Covid Risk', "no data", 0, "missing data", "missing"])

ColumnHeaders = ["Category", "Location", "Score", "Description", "Guidelines"]
a1 = pd.DataFrame(data=rg_rows, columns=ColumnHeaders)
rg_table = a1.to_html(index=False)

ambee_key = 'fdfaf568c46501389a631b99765c08ce0171ff3127648730748e0fb922f367da'
ambee_url = "https://api.ambeedata.com/latest/pollen/by-place"
querystring = {"place":city}
headers = {
'x-api-key': ambee_key,
'Content-type': "application/json"
}
pollen_response = requests.request("GET", ambee_url, headers=headers, params=querystring) 
pollen_json = json.loads(pollen_response.text)

pg_rows = []
try:
s3 = pollen_json['data'][0]["Count"]
for key in s3:
pg_rows.append(["Count", key, s3[key] ])
except:
pass
try: 
s3 = pollen_json['data'][0]["Risk"]
for key in s3:
pg_rows.append(["Risk", key, s3[key] ])
except:
pass

try: 
s3 = pollen_json['data'][0]["Species"]
for key in s3:
if key != "Others":
for key2 in s3[key]:
pg_rows.append(["Species", key2, s3[key][key2]])
except:
pass

ColumnHeaders = ["Category", "Type", "Score"]
a1 = pd.DataFrame(data=pg_rows, columns=ColumnHeaders)
pg_table = a1.to_html(index=False)
if city_lower == "portland":
city_lower = "portland-or"
elif city_lower == "san-francisco":
city_lower = "san-francisco-bay-area"
elif city_lower =="st.-louis":
city_lower = "st-louis"
elif city_lower =="tampa-bay":
city_lower = "tampa-bay-area"
elif city_lower =="washington-d.c":
city_lower = "washington-dc"

#economic data
teleport_url = 'https://api.teleport.org/api/urban_areas/slug:' + city_lower + '/scores/'
response = requests.get(teleport_url)
quality_of_life_result = response.json()
#output variables

try:
city_summary = quality_of_life_result['summary']
city_summary = city_summary.replace("Teleport", "our")
city_summary = sub('( |\t) +', ' ', city_summary)
city_summary = city_summary.replace("\n", '')
city_scores = quality_of_life_result['categories']
except:
city_summary =""
city_scores =[]
try:
city_score = round(quality_of_life_result['teleport_city_score'],1)
except:
city_score = 62

rows = [[category['name'],round(category['score_out_of_10'], 1)] for category in city_scores]
ColumnHeaders = ["Category", "Score out of 10"]
a = pd.DataFrame(data=rows, columns=ColumnHeaders)
economic_table = a.to_html(index=False)
# draw a chart
# Figure Size
fig, ax = plt.subplots(figsize =(16, 9))
# Horizontal Bar Plot
cat2 = a['Category'].head(12)
sc2 = a['Score out of 10'].head(12)

ax.barh(cat2, sc2)
# Remove axes splines
for s in ['top', 'bottom', 'left', 'right']:
ax.spines[s].set_visible(False)
# Remove x, y Ticks
ax.xaxis.set_ticks_position('none')
ax.yaxis.set_ticks_position('none')
# Add padding between axes and labels
ax.xaxis.set_tick_params(pad = 5)
ax.yaxis.set_tick_params(pad = 10)
# Add x, y gridlines
ax.grid(b = True, color ='grey',
linestyle ='-.', linewidth = 0.5,
alpha = 0.2)
# Show top values
ax.invert_yaxis()
# Add annotation to bars
for i in ax.patches:
plt.text(i.get_width()+0.2, i.get_y()+0.5,
str(round((i.get_width()), 2)),
fontsize = 12, fontweight ='bold',
color ='grey')
# Add Plot Title
ax.set_title('Different areas and Scores for ' + city_title,
loc ='left' )
# Show Plot
economic_graph = plt_show(plt)
return {"city": city_title, 
"aqi": aqi, 
"aqi_no2": aqi_no2,
"city_score": city_score,
"city_summary":city_summary,
"city_scores": city_scores,
"economic_table": economic_table,
"rg_table": rg_table,
"pg_table": pg_table,
"economic_graph": economic_graph}
