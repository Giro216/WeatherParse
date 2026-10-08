import os
import urllib.request
import urllib.parse
import json
import asyncio

class WeatherData:
    def __init__(self, temp_c, country, city):
        self.temp_c = temp_c
        self.country = country
        self.city = city

def read_cities_lazily(filePath):
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File {filePath} does not exist.")

    with open(filePath, mode="r", encoding="utf-8-sig") as f:
        for line in f:
            cleaned = line.strip()
            if cleaned:
                yield cleaned

def get_request(url, params=None):
    if params is None:
        params = {'q': 'python programming', 'lang': 'en'}
    query_string = urllib.parse.urlencode(params)
    url = url + '?' + query_string
    # Синхронный вызов urllib
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')

def json_parse(json_string, city):
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    temp_c = int(data['current_condition'][0]['temp_C'])
    country = data['nearest_area'][0]['country'][0]['value']
    return WeatherData(temp_c, country, city)

async def city_process_async(city):
    params = {'format': 'j1'}
    url = 'https://wttr.in/{City}'.format(City=city)
    
    # Так как urllib блокирующий, выполняем его в отдельном потоке внутри асинхронного приложения,
    # чтобы не блокировать цикл событий (event loop)
    response_text = await asyncio.to_thread(get_request, url, params)
    
    curr_weather_data = json_parse(response_text, city)
    return curr_weather_data

def print_city_weather(weather_data):
    if weather_data is None:
        print("No weather data available.")
        return
    print(f"{weather_data.city}, {weather_data.country} {format_temp(weather_data.temp_c)}")

def format_temp(temp):
    return f"{temp:+d}°C" if isinstance(temp, int) and temp == int(temp) else f"{temp:+.1f}°C"

def print_country_weather(country_weather_data):
    for country, weather_data in country_weather_data.items():
        temps = [data.temp_c for data in weather_data]

        city_count = len(weather_data)
        avg_temp = sum(temps) / city_count

        if avg_temp.is_integer():
            avg_temp = int(avg_temp)
        else:
            avg_temp = round(avg_temp, 1)

        min_temp = min(temps)
        max_temp = max(temps)

        print(f"{country}: {city_count} - cities, Avg: {format_temp(avg_temp)}, Min: {format_temp(min_temp)}, Max: {format_temp(max_temp)}")

async def main():
    cities_file_path = "cities.txt"
    # Собираем города из генератора в список, чтобы запустить задачи параллельно
    cities = list(read_cities_lazily(cities_file_path))
    
    # Запускаем все запросы одновременно через asyncio.gather
    tasks = [city_process_async(city) for city in cities]
    results = await asyncio.gather(*tasks)

    country_weather_data = dict()
    for weather_data in results:
        if weather_data:
            if weather_data.country not in country_weather_data:
                country_weather_data[weather_data.country] = []
            country_weather_data[weather_data.country].append(weather_data)
            print_city_weather(weather_data)

    print_country_weather(country_weather_data)

# Точка входа для асинхронного приложения
if __name__ == "__main__":
    asyncio.run(main())