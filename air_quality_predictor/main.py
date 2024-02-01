import requests
import json
import csv
import os


def main():
    try:
        API_TOKEN = os.environ["API_TOKEN"]
    except KeyError:
        API_TOKEN = "Token not available!"

    # coordinates set for usaquen, bogota colombia
    lat = 4.7033
    lng = -74.0329
    # Format the URL with the provided city name, token, latitude and longitude
    url = f"https://api.waqi.info/feed/geo:{lat};{lng}/?token={API_TOKEN}"

    # Make the API request
    response = requests.get(url)

    pollutant_list = [pollutant for pollutant in response.json()['data']['iaqi']]
    pollutant_value = []
    for pollutant in pollutant_list:
        pollutant_value.append(response.json()['data']['iaqi'][pollutant]['v'])

    pollutant_list.append("aqi")
    pollutant_value.append(response.json()['data']['aqi'])
    pollutant_list.append("time")
    pollutant_value.append(response.json()['data']['time']['s'])

    with open('aqi_usaquen.csv','a') as fd:
        writer = csv.writer(fd)
        writer.writerow(pollutant_value) 


if __name__ == "__main__":
    main()
