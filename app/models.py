from djongo import models
from django.contrib.auth.models import User
import json, requests

# Create your models here.

class Profile(models.Model):

    _id = models.ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.FloatField(default=0)
    balanceBTC = models.FloatField(default=0)
    buyOrders = models.Field()
    sellOrders = models.Field()
    profit = models.FloatField(default=0)

class Order(models.Model):

    _id = models.ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.Field(default="")
    price = models.FloatField(default=0)
    BTCs = models.FloatField(default=0)
    datetime = models.DateTimeField(auto_now_add=True,auto_now=False)
    status = models.Field(default="")
    value = models.FloatField(default=0)

    def orderPurchased(self, profile):

        jsonOrder = json.dumps({
            "ID": str(self._id),
            "Amount": self.BTCs,
            "Price": self.price,
            "Value": self.value,
        })
        profile.buyOrders+=jsonOrder
        profile.profit-=self.value
        profile.save()


    def orderSold(self, profile):

        jsonOrder = json.dumps({
                "ID": str(self._id),
                "Amount": self.BTCs,
                "Price": self.price,
                "Value": self.value,
        })
        profile.sellOrders+=jsonOrder
        profile.profit+=self.value
        profile.save()

class Report:

    def __init__(self):

        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

        self.params = {
        'start':'1',
        'limit':1,
        'convert':'USD'
    }

        self.headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '8b1af74b-28fd-4c01-838e-71d152144e7c' # Put your CoinMarket Key to get BTC data
    }

    def cryptoData(self):

        data = requests.get(url=self.url,params=self.params,headers=self.headers).json()

        for currency in data['data']:

            btcPrice = int(currency['quote']['USD']['price'])

        return btcPrice


