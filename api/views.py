from django.shortcuts import render
# api/views.py
from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.http import JsonResponse

def interpolate_population_data(data):
    result = {}
    for record in data["results"]["bindings"]:
        # print(data)
        country = record['countryLabel']["value"]
        lat = float(record['lat']["value"])
        long = float(record['long']["value"])
        population = float(record['population']["value"])
        year = int(record['year']["value"])
        
        if country not in result:
            result[country] = {
                'position': [lat, long],
                'population': [],
                'time': [],
                'radius': []
            }
        
        result[country]['population'].append(population)
        result[country]['time'].append(year)
        result[country]['radius'].append((population ** 0.5) / 1000)

    # データ補完処理
    for country in result.keys():
        population = result[country]['population']
        time = result[country]['time']
        radius = result[country]['radius']
        
        # 補完ロジック
        for i in range(len(time) - 1):
            interval = time[i + 1] - time[i]
            # print(type(interval))
            if interval > 1:
                step = (population[i + 1] - population[i]) / interval
                for j in range(1, interval):
                    interpolated_population = population[i] + step * j
                    population.insert(i + j, interpolated_population)
                    time.insert(i + j, time[i] + j)
                    radius.insert(i + j, (interpolated_population ** 0.5) / 1000)
    return result

@csrf_exempt
# api/views.py

def get_population_data(request):
    endpoint = "https://query.wikidata.org/sparql"
    query = """
        select ?countryLabel ?lat ?long ?population ?time (year(?time) as ?year)
        where {
            ?country wdt:P31 wd:Q6256;
                    wdt:P625 ?location;
                    p:P1082 ?populationStatement.
            ?populationStatement ps:P1082 ?population.
            
            optional {{?populationStatement pq:P585 ?time.} union {?populationStatement pq:P577 ?time.}}
            FILTER(year(?time) >= 2000 && year(?time) <= 2020)
          
            bind(geof:latitude(?location) AS ?lat)
            bind(geof:longitude(?location) as ?long)
            SERVICE wikibase:label { bd:serviceParam wikibase:language "ja". }
        }
        order by asc(?time)
    """
    headers = {
        "Accept": "application/json"
    }
    
    # SPARQLクエリを実行してデータを取得
    response = requests.get(endpoint, params={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        data = interpolate_population_data(data)
        return JsonResponse(data)
    else:
        return JsonResponse({"error": "Failed to fetch data"}, status=response.status_code)
# Create your views here.
