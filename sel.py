from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

from CarousellPost import CarousellPost

def my_strtof(s):
    r = ""
    for x in s:
        if x.isdigit() or x == ".":
            r += x
    return float(r)

def trim_by_words(s):
    while True:
        length = len(s)
        wsIdx = s.rfind(" ")

        if wsIdx == -1:
            return False

        s = s[0:wsIdx]

        length = len(s)
        wsIdx = s.rfind(" ")          
    
        if length - wsIdx == 2:
            continue
        else:
            break
    return s

################################
## Login using session cookie ##
################################
cookieVal = input("auth-session cookie value: ")


options = webdriver.ChromeOptions()

driver = webdriver.Chrome()
driver.get("https://carousell.com")
driver.add_cookie({"name": "auth-session", "value": cookieVal, "path": "/", "domain": "sg.carousell.com", "secure": True})
driver.refresh()

# ## if cant find, means login failed
driver.find_element_by_xpath("//a[contains(@href, 'likes')]/preceding-sibling::div").click()
driver.find_element_by_xpath("//a[contains(@href, 'settings')]/preceding-sibling::a").click()

# ####################
# ## Fetch listings ##
# ####################
listings = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, "//a[div[div[img]]]")))
items = []

x = 1
for listing in listings:
    link = listing.get_attribute("href")

    listingStr = listing.text.split("\n")
    if listingStr[0] == "SOLD":
        continue

    items.append({"id": x, "exclude": False, "postobj": CarousellPost(link)})
    x += 1

#############
## Options ##
#############
option = "a"
while option:
    print("---------------------------------------------------------------------------")
    print("Select items to exclude -- enter number and press enter, once for each item")
    print("---------------------------------------------------------------------------")
    for item in items:
        print(("%.2d: %s%s") % (item["id"], ("[exclude] " if item["exclude"] else ""), str(item["postobj"])))

    option = input()
    if not option: continue

    try:
        option = int(option)
    except ValueError:
        print("\n\n\n<<Not a valid choice, try again>>")
        continue

    valid = len(items)
    if option < 1 or option > valid:
        print("\n\n\n<<Not a valid choice, try again>>")
        continue
    else:
        if items[option-1]["exclude"]:
            items[option-1]["exclude"] = False
        else:
            items[option-1]["exclude"] = True
            
        print("\n\n\n")
        continue

from time import sleep

###############
## Reposting ##
###############
def fuzzy_score(s, c):
    c = re.split(r"[\n\s]", c)
    s = re.split(r"\s*[&\-,]\s*", s)
    i = list(set(c).intersection(s))
    cx = set(c) - set(i)
    r = 0
    for x in i:
        r += len(x)
    for x in cx:
        r -= len(x)
    return r

for item in items:
    if item["exclude"]:
        continue
    else:
        postObj = item["postobj"]

        print(("Reposting -- %s") % (str(item["postobj"])))

        driver.get(postObj.link)
        rainbutton = driver.find_elements_by_xpath("//button[@type='button']")
        rainbutton[-1].click()
        delete = driver.find_element_by_xpath("//span[text()='Delete']")
        delete = delete.find_element_by_xpath("./..")
        delete.click()
        confirmdel = driver.find_element_by_xpath("//button[text()='Yes, delete']")
        confirmdel.click()
        sleep(1)
        # pass
        # exit()



        driver.get("https://carousell.com/sell")

        sleep(1)

        imageInput = driver.find_element_by_xpath("//input[@type='file']")


        categoryDD = driver.find_element_by_xpath("//p[text()='Select a category']").click()
        categorySearch = driver.find_element_by_xpath("//input[@placeholder='Search for a category...']")

        ## tabulate category fuzzy scores
        searchTerm = item["postobj"].category
        fuzzyScores = []
        while True:
            categorySearch.send_keys(Keys.CONTROL + "a");
            categorySearch.send_keys(Keys.DELETE);
            categorySearch.send_keys(searchTerm)
            sleep(0.5)

            categoryResults = driver.find_elements_by_xpath("//div[div[div[div[input[@placeholder='Search for a category...']]]]]/*[not(svg)]")
            categoryResults.pop(0)

            for i in reversed(range(0, len(categoryResults))):
                categoryChildren = categoryResults[i].find_elements_by_xpath("./*")
                ## no results found has no child
                if len(categoryChildren) == 0:
                    continue
                ## check if is an expandable option    
                elif categoryChildren[len(categoryChildren)-1].tag_name == "svg":
                    # categoryResults.remove(categoryResults[i])
                    continue
                else:
                    fuzzyScores.append({
                        "searchTerm": searchTerm
                        ,"categoryText": categoryResults[i].text
                        ,"score": fuzzy_score(item["postobj"].category, categoryResults[i].text)
                        })

            if not trim_by_words(searchTerm):
                break
            else:
                searchTerm = trim_by_words(searchTerm)
                continue

        ## get best score, enter search term, select options
        bestFit = sorted(fuzzyScores, key = lambda x: x['score'], reverse=True)[0]

        categorySearch.send_keys(Keys.CONTROL + "a");
        categorySearch.send_keys(Keys.DELETE);
        categorySearch.send_keys(bestFit["searchTerm"])
        sleep(0.5)

        categoryResults = driver.find_elements_by_xpath("//div[div[div[div[input[@placeholder='Search for a category...']]]]]/*[not(svg)]")
        categoryResults.pop(0)

        for category in categoryResults:
            if category.text == bestFit["categoryText"]:
                category.click()
                break

        ## insert other info
        # mainForm = driver.find_elements_by_xpath("//form/section")
        # test = driver.find_elements_by_xpath("./*")

        ## change to explicit wait
        sleep(1)
        titleInput = driver.find_element_by_xpath("//input[@aria-label='Listing Title']")
        titleInput.send_keys(item["postobj"].title)
        priceInput = driver.find_element_by_xpath("//input[@aria-label='Price']")
        priceInput.send_keys(str(item["postobj"].price + 0.1))
        descInput = driver.find_element_by_name("field_3")
        descInput.send_keys(item["postobj"].desc)

        ## radios
        usedRadios = driver.find_elements_by_name("field_1")
        if postObj.condition == "New":
            usedRadios[0].click()
        else:
            usedRadios[1].click()

        ## location
        locationCB = driver.find_element_by_name("field_5")
        locationCB.click()
        locationInput = driver.find_element_by_xpath("//input[@aria-label='Add location']")
        if postObj.location is not None:
            locationFuzzyScores = []
            for location in postObj.location:
                locationInput.send_keys(location)
                sleep(1.5)
                locationChildren = locationInput.find_elements_by_xpath("./../../../..//div/div[p]")
                for locationChild in locationChildren:
                    locationChildParas = locationChild.find_elements_by_css_selector("p")
                    if len(locationChildParas) <= 1:
                        continue
                    else:
                        locationFuzzyScores.append({
                            "locationText": locationChildParas[0].text
                            ,"score": fuzzy_score(location, locationChildParas[0].text)
                            })
                locationBestFit = sorted(locationFuzzyScores, key = lambda x: x['score'], reverse=True)[0]
                for locationChild in locationChildren:
                    locationChildParas = locationChild.find_elements_by_css_selector("p")
                    if locationChildParas[0].text == locationBestFit["locationText"]:
                        locationChild.click()
                        driver.find_element_by_xpath("//body").click()
                        break

        ## checkboxes
        if postObj.shipping is not None:
            basicShip = next((ship for ship in postObj.shipping if ship["type"] == "Basic Package"), None)
            trackedShip = next((ship for ship in postObj.shipping if ship["type"] == "Tracked Package"), None)
            registeredShip = next((ship for ship in postObj.shipping if ship["type"] == "Registered Mail"), None)

            if basicShip:
                basicShipCB = driver.find_element_by_xpath("//div[p[text()='Basic Package']]/preceding-sibling::input")
                basicShipCB.click()

                basicShipDD = basicShipCB.find_element_by_xpath("./../../div/button")
                basicShipDD.click()

                basicShipOptions = basicShipDD.find_elements_by_xpath("./../div/div/div")
                for basicShipOption in basicShipOptions:
                    basicShipOptionPrice = my_strtof(basicShipOption.text.split(" ")[-1])
                    if basicShipOptionPrice == basicShip["price"]:
                        basicShipOption.click()
                        break

            if trackedShip:
                trackedShipCB = driver.find_element_by_xpath("//div[p[text()='Tracked Package']]/preceding-sibling::input")
                trackedShipCB.click()

                trackedShipDD = trackedShipCB.find_element_by_xpath("./../../div/button")
                trackedShipDD.click()

                trackedShipOptions = trackedShipDD.find_elements_by_xpath("./../div/div/div")
                for trackedShipOption in trackedShipOptions:
                    trackedShipOptionPrice = my_strtof(trackedShipOption.text.split(" ")[-1])
                    if trackedShipOptionPrice == trackedShip["price"]:
                        trackedShipOption.click()
                        break

            if registeredShip:
                registeredShipCB = driver.find_element_by_xpath("//div[p[text()='Registered Mail']]/preceding-sibling::input")
                registeredShipCB.click()

                registeredShipDD = registeredShipCB.find_element_by_xpath("./../../div/button")
                registeredShipDD.click()

                registeredShipOptions = registeredShipDD.find_elements_by_xpath("./../div/div/div")
                for registeredShipOption in registeredShipOptions:
                    registeredShipOptionPrice = my_strtof(registeredShipOption.text.split(" ")[-1])
                    if registeredShipOptionPrice == registeredShip["price"]:
                        registeredShipOption.click()
                        break
            
            
        # check if field 6 and field 8 is visible, if so 5 and  7 are checked
        sleep(1)
        submitButton = driver.find_elements_by_xpath("//button[@type='submit']")
        submitButton[-1].click()
        sleep(3)


driver.quit()