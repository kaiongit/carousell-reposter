import os
import requests
from bs4 import BeautifulSoup

class CarousellPost:
    def __init__(self, link):
        self.link = link
        self._scrape()

    def _scrape(self):
        page = requests.get(self.link)
        parser = BeautifulSoup(page.text, "html.parser")

        content = parser.find(id="root")
        content = content.contents[0].contents[3].contents[0].contents[0]

        images = content.contents[0]
        subImages = images.contents[0].contents[0].contents[0].contents[0]
        imageList = subImages.find_all("img")
        description = content.contents[1]
        subDescription = description.contents[4]

        self.price = my_strtof(description.contents[1].contents[0].text)
        # self.price = int(''.join(c for c in description.contents[1].contents[0].text if c.isdigit()))
        self.title = description.contents[3].contents[0].text

        conditionIcon = subDescription.find(src="https://sl3-cdn.karousell.com/components/condition_v3.svg")
        self.condition = conditionIcon.next.text
        
        dealTypeIcon = subDescription.find(src="https://sl3-cdn.karousell.com/components/caroupay_listing_details_v7.svg")
        dealType = dealTypeIcon.next.text.split(" · ")

        ## PRICE can be float LOL!
        ## free shipping

        if "Mailing" in dealType:
            shipping = subDescription.find(name="p", string="Shipping")
            self.shipping = []
            while shipping.nextSibling is not None:
                shipping = shipping.nextSibling
                shippingDetails = shipping.find_all(name="p")

                shippingType = shippingDetails[0].text
                shippingPrice = my_strtof(shippingDetails[1].text.split(" · ")[1])
                # shippingPrice = int(''.join(c for c in shippingDetails[1].text.split(" · ")[1] if c.isdigit()))

                self.shipping.append({"type": shippingType, "price": shippingPrice})

            # 3~5 days · S$1.40


            pass

        if "Meetup" in dealType:
            locationIcon = subDescription.find_all(src="https://sl3-cdn.karousell.com/components/location_v3.svg")
            self.location = []
            for location in locationIcon:                
                self.location.append(location.next.text)
            self.location.pop(0)

        self.category = subDescription.contents[0].find("a").text
        self.desc = subDescription.contents[0].contents[3].text

        
        # 
        # 

        self.imageList = []
        for image in imageList:
            self.imageList.append(image.attrs.get("src"))

    def _scrape_images(self):
        try:
            os.mkdir("_temp")
        except:
            pass

    def __str__(self):
        return self.title + " ($" + str(self.price) + ")"


def get_image(url, filename):
    image = requests.get(url)
    with open(os.path.join("images", filename), "wb") as file:
        file.write(image.content)

def my_strtof(s):
    r = ""
    for x in s:
        if x.isdigit() or x == ".":
            r += x
    return float(r)