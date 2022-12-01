import scrapy
from scrapy_splash import SplashRequest


class CarSpider(scrapy.Spider):
    name = 'carspider'
    page_nr = 1
    index = 1
    link_list = []

    def start_requests(self):
        url = 'https://pp.lv/lv/transports-un-tehnika/vieglie-auto?page=1'
        yield SplashRequest(url=url, callback=self.get_link_list, args={'wait': 2, 'images': 0})

    def get_link_list(self, response):
        page_cars = response.css('div.pp-list-view')
        for car in page_cars:
            self.link_list.append(car.css('a::attr(href)').get())
        if response.css('i.pp-ico.pp-angle-right'):
            self.page_nr += 1
            yield SplashRequest(
                url=f'https://pp.lv/lv/transports-un-tehnika/vieglie-auto?page={self.page_nr}',
                callback=self.get_link_list,
                args={'wait': 5, 'images': 0}
            )
        else:
            yield SplashRequest(
                url=f'https://pp.lv{self.link_list[0]}',
                callback=self.parse,
                args={'wait': 3, 'images': 0}
            )

    def parse(self, response):
        current_url = response.url
        split_url = current_url.split('/')
        car_map = {}
        raw_key = response.css('div.single-pp-data-key.col-6.col-sm-5::text').getall()
        raw_value = response.css('div.single-pp-data-value.col-6.col-sm-7::text').getall()
        try:
            raw_key.remove(' VIN: ')
            raw_value.remove(' ')
        except ValueError:
            pass
        half_key_length = round(len(raw_key) / 2)
        half_value_length = round(len(raw_value) / 2)
        if half_key_length < half_value_length:
            key = raw_key[:half_key_length + 1]
        else:
            key = raw_key[:half_key_length]
        if half_key_length > half_value_length:
            value = raw_value[:half_value_length + 2]
        else:
            value = raw_value[:half_value_length]
        for i in range(len(key)):
            car_map[key[i]] = value[i]
        make = split_url[6]
        model = split_url[-2]
        year = None
        mileage = None
        plate = None
        vin = None
        if ' Izlaiduma gads ' in car_map:
            year = car_map[' Izlaiduma gads ']
        if ' Nobraukums, km ' in car_map:
            mileage = car_map[' Nobraukums, km ']
        if ' Auto numurs ' in car_map:
            plate = car_map[' Auto numurs ']
        try:
            vin = response.css('a.btn.btn-sm.w-auto.btn-primary::attr(href)').get().split('=')[1]
            if vin == '':
                vin = None
        except AttributeError:
            pass
        yield {
            'make': make,
            'model': model,
            'year': year,
            'mileage': mileage,
            'vin': vin,
            'plate': plate
        }
        if self.index < len(self.link_list):
            self.index += 1
            yield SplashRequest(
                    url=f'https://pp.lv{self.link_list[self.index]}',
                    callback=self.parse,
                    args={'wait': 3, 'images': 0}
                )
