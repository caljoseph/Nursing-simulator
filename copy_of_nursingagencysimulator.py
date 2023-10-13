# -*- coding: utf-8 -*-
"""Copy of NursingAgencySimulator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BNd43TCpTYDpet6fvSDOQs4a6PwntMLD
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import requests

from google.colab import drive
drive.mount('/drive')

nursing_homes = pd.read_csv('/drive/My Drive/Nursing Homes/nursing_home_locations.csv')
us_cities = pd.read_csv('/drive/My Drive/Nursing Homes/us_cities.csv').sort_values(by='population', ascending=False).iloc[:15000]
covr_coordinates = ('/drive/My Drive/Nursing Homes/geocoded_addresses.csv')
df = pd.read_csv('/drive/My Drive/Nursing Homes/covr_addresses.csv', header=None, names=['Address'])

#transform Covr addresses file into coordinates via Google geocoding API. Commented out to not hit my google API limit

def address_to_geocode(address):
  url = 'https://maps.googleapis.com/maps/api/geocode/json'
  params = {'address': address, 'key': 'API_KEY'}
  response = requests.get(url, params=params).json()
  results = response['results']

  if results:
        location = results[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        return latitude, longitude
  else:
        return None, None

df['Latitude'], df['Longitude'] = zip(*df.iloc[:, 0].apply(address_to_geocode))
display(df)

df.to_csv('geocoded_addresses.csv', index=False)
from google.colab import files

files.download('geocoded_addresses.csv')

x = nursing_homes.LONGITUDE.values * 54.6
y = nursing_homes.LATITUDE.values * 69
min_x, min_y = np.min(x), np.min(y)
x = x - min_x
y = y - min_y
home_locations = np.transpose(np.vstack([x, y]))

x = us_cities.lng.values * 54.6
y = us_cities.lat.values * 69
x = x - min_x
y = y - min_y
city_locations = np.transpose(np.vstack([x, y]))
min_distance = 15
possible_agency_locations = []
for city in tqdm(city_locations):
  is_repeat = False
  for location in possible_agency_locations:
    if np.linalg.norm(city - location) < min_distance:
      is_repeat = True
      break
  if is_repeat == False:
    possible_agency_locations.append(city)
city_locations = np.zeros((len(possible_agency_locations), 2))
for i, city in enumerate(possible_agency_locations):
  city_locations[i] = city

len(city_locations)

plt.scatter(home_locations[:,0], home_locations[:,1], s=1, alpha=0.2, c='b')
plt.scatter(city_locations[:,0], city_locations[:,1], s=1, alpha=0.1, c='r')

def sigmoid(start_taper, end_taper, x):
  mean = (start_taper + end_taper) / 2
  range = end_taper - start_taper
  return 1 - 1 / (1 + np.exp(np.exp(1) * (mean - x) / range))

test = np.array([[1, 0.5, 0], [1, 0, 0.1]])
test2 = np.array([1, 0.8, 0.64])
np.matmul(test, test2)

def simulate_agency_locations(home_locations, city_locations, total_agencies, agencies_to_generate, mean_agencies_per_home, max_homes_per_agency, decay, easy_distance, difficult_distance):
  agencies_per_home = np.zeros(len(home_locations))
  values_of_new_agency = np.ones(len(home_locations))
  agency_locations = np.zeros((agencies_to_generate, 2))
  distances = np.zeros((len(city_locations), len(home_locations)))
  decay_array = np.ones(len(home_locations)) * decay
  aph = 0
  for i in range(mean_agencies_per_home):
    aph += decay ** i
  max_homes = round(max_homes_per_agency * len(home_locations) * aph / total_agencies)
  for i, city in enumerate(city_locations):
    x_dist_squared = (home_locations[:,0] - city[0]) ** 2
    y_dist_squared = (home_locations[:,1] - city[1]) ** 2
    distances[i] = sigmoid(easy_distance, difficult_distance, np.sqrt(x_dist_squared + y_dist_squared))
  for i in tqdm(range(agencies_to_generate)):
    location_values = np.matmul(distances, values_of_new_agency)
    best_location = np.argmax(location_values)
    agency_locations[i] = city_locations[best_location]
    dist_from_best = distances[best_location]
    best_val = location_values[best_location]
    best_values = dist_from_best * values_of_new_agency
    best_values = best_values * max_homes / best_val if best_val > max_homes else best_values
    agencies_per_home = agencies_per_home + best_values
    values_of_new_agency = values_of_new_agency * (decay_array ** best_values)
  return agency_locations, agencies_per_home

total_agencies = 4000
agencies_to_generate = 4000
mean_agencies_per_home = 10
max_homes_per_agency = 4
decay = 0.1
easy_distance = 15
difficult_distance = 50

agency_locations, agencies_per_home = simulate_agency_locations(home_locations, city_locations, total_agencies, agencies_to_generate, mean_agencies_per_home, max_homes_per_agency, decay, easy_distance, difficult_distance)

plt.scatter(home_locations[:,0], home_locations[:,1], s=1, alpha=0.2, c='b')
# plt.scatter(city_locations[:,0], city_locations[:,1], s=2, alpha=0.2, c='k')
plt.scatter(agency_locations[:,0], agency_locations[:,1], s=1, alpha=1, c='r')

agency_locations_df = pd.DataFrame()
agency_locations_df['x'] = agency_locations[:,0]
agency_locations_df['y'] = agency_locations[:,1]
agency_locations_df.to_csv('/drive/My Drive/Nursing Homes/simulated_agency_locations.csv')

