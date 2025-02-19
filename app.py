from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import json

app = Flask(__name__)

def format_price(price):
    price = str(price)[0:-2]
    clean_price = price.replace('.', '')
    return int(clean_price)

def get_home_listings(selected_il, price_value):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--no-sandbox') 
    chrome_options.add_argument('--disable-dev-shm-usage') 
    chrome_options.add_argument('--disable-gpu')  

    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://www.emlakjet.com/')

    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="headlessui-tabs-panel-:r9:"]/div/div[2]/div/div/div/input'))
        )
        search_input.send_keys(f'{selected_il}')
        
        dropdown_button = driver.find_element(By.XPATH, '//*[@id="headlessui-listbox-button-:rh:"]')
        dropdown_button.click()
        
        price_value = format_price(price_value)
        lower_bound = price_value - 500000
        upper_bound = price_value + 500000
        
        first_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-options-:ri:"]/ul[1]/div[1]/div/div[1]/input'))
        )
        first_input.clear()
        first_input.send_keys(str(lower_bound))

        second_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-options-:ri:"]/ul[2]/div[1]/div/div[1]/input'))
        )
        second_input.clear()
        second_input.send_keys(str(upper_bound))
        
        find_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="headlessui-tabs-panel-:r9:"]/div/div[5]/div/button'))
        )
        find_button.click()

        i = 1
        data = []
        while i <= 10:
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="content-wrapper"]/div[1]/div[4]/div[2]/div[3]/div[{i}]/div/a')
                ))
                link = driver.find_element(By.XPATH, f'//*[@id="content-wrapper"]/div[1]/div[4]/div[2]/div[3]/div[{i}]/div/a')
                driver.get(link.get_attribute('href'))
                detail_url = driver.current_url
                
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.ID, "ilan-hakkinda"))
                )
                
                try:
                    ul = driver.find_element(By.XPATH, '//*[@id="ilan-hakkinda"]/div/div/ul')
                    list_items = ul.find_elements(By.TAG_NAME, 'li')

                    details = {}
                    for item in list_items:
                        try:
                            key = item.find_element(By.CLASS_NAME, 'styles_key__VqMhC').text
                            value = item.find_element(By.CLASS_NAME, 'styles_value__3QmL3').text
                            details[key] = value
                        except NoSuchElementException:
                            continue

                    title = driver.find_element(By.XPATH, '//*[@id="content-wrapper"]/div[2]/div[1]/div/h1').text
                    resim_url = driver.find_element(By.XPATH, '//*[@id="content-wrapper"]/div[2]/div[2]/div[2]/img').get_attribute('src')
                    fiyat = driver.find_element(By.XPATH, '//*[@id="genel-bakis"]/div[1]/div[1]/div[1]/div/span').text
                    fiyat = int(fiyat.replace('.', '').replace('TL', ''))
                    
                    details['url'] = detail_url
                    details['title'] = title
                    details['resim_url'] = resim_url
                    details['price'] = fiyat
                    
                    data.append(details)
                except NoSuchElementException:
                    pass
                driver.execute_script("window.history.go(-1)")
            except Exception:
                pass
            i += 1

    finally:
        driver.quit()
    
    return data

@app.route('/get_listings', methods=['GET'])
def get_listings():
    selected_il = request.args.get('city')
    price_value = request.args.get('price')

    if not selected_il or not price_value:
        return jsonify({'error': 'city and price parameters are required'}), 400

    try:
        price_value = int(price_value)
    except ValueError:
        return jsonify({'error': 'price should be an integer'}), 400

    listings = get_home_listings(selected_il, price_value)
    return jsonify(listings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
