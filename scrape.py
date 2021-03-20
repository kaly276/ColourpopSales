import csv
import sqlite3
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import (presence_of_element_located)
from selenium.webdriver.support.wait import WebDriverWait
from urllib.request import pathname2url

connection = sqlite3.connect('Colourpop.db')

cursor = connection.cursor()

sql_drop = '''DROP TABLE IF EXISTS products'''
sql_create = '''CREATE TABLE IF NOT EXISTS products (
id INTEGER PRIMARY KEY,
name VARCHAR(20),
price INTEGER,
sale_price INTEGER)'''

connection.execute(sql_create)                                               

urlpage = 'https://colourpop.com/collections/best-sellers'

driver = webdriver.Chrome('/Users/karla/Desktop/chromedriver')
driver.get(urlpage)
print("Loading")
driver.implicitly_wait(100)
print("Ready")

time.sleep(4)

# Scroll to load all products on webpage
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

time.sleep(5)

# Retrieve html of current page
soup = BeautifulSoup(driver.page_source, 'html.parser')
soup_names = soup.find_all('label', class_='product__listing-content--title')
soup_prices = soup.find_all('label', class_='product__listing-content--price')

# Find all product__listing
soup_product_listings = soup.find_all('div', class_='product__listing')
print(len(soup_product_listings))

# Store attributes in a list
product_names = []
product_prices = []

# Create a temporary table to store name values and insert into the main table
connection.execute('''CREATE TEMP TABLE temp_names (
id INTEGER PRIMARY KEY,
t_name VARCHAR(20))
''')

for x in range(len(soup_names)):
    table_id = str(x+1)
    temp_name = soup_names[x].get_text().strip()
    connection.execute('INSERT INTO temp_names VALUES '+
                       '('+table_id+',"'+temp_name+'")')
print('Inserted into temp_names.')

connection.execute('''CREATE TEMP TABLE temp_prices (
id INTEGER PRIMARY KEY,
t_price INTEGER,
t_sale_price INTEGER)
''')

for x in range(len(soup_prices)):
    temp_price = soup_prices[x].get_text().strip()
    table_id = str(x+1)
    if temp_price.startswith('Original Price'):
        temp_price_edit = temp_price.partition('Sale Price')[0].strip('Original Price$')
        temp_sale_price = temp_price.strip(temp_price.partition('Sale Price')[0]).strip('Sale Price$')
        connection.execute('INSERT INTO temp_prices (id, t_price, t_sale_price) VALUES '+
                           '('+table_id+','+temp_price_edit+','+temp_sale_price+')')
    else:
        temp_price = temp_price.strip('Sale Price$')
        connection.execute('INSERT INTO temp_prices (id, t_price, t_sale_price) VALUES '+
                           '('+table_id+','+temp_price+', NULL)')
print('Inserted into temp_prices.')

connection.execute('''INSERT INTO products
SELECT temp_names.id, t_name, t_price, t_sale_price
FROM temp_names
INNER JOIN temp_prices
ON temp_names.id = temp_prices.id
LEFT JOIN products
ON products.id = temp_names.id
WHERE products.id IS NULL
''')
print('Inserted into products.')

print('Database data:')
cursor.execute('SELECT * FROM products')
rows = cursor.fetchall()
for row in rows:
    print(row)

print('Sales:')
cursor.execute('SELECT * FROM products WHERE sale_price IS NOT NULL')
rows = cursor.fetchall()
for row in rows:
    print(row)

connection.close()
driver.quit()