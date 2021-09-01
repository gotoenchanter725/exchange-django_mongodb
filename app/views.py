from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout
from django.contrib import messages
from .forms import registrationForm
from django.contrib.auth.models import User
from .models import Profile, Report, Order
from django.contrib.auth.decorators import login_required
import datetime, random, json

# Create your views here.

def home(request):
    return render(request, "index.html")

# Get informations about sell and buy orders from profile users and create a file JSON with them...

def profile(request):

    currentuserProfile = Profile.objects.get(user=request.user)
    profiles = Profile.objects.all()

    if request.method == "POST":

        dataAll=[]

        for profile in profiles:

            data = "User: " + str(profile.user), "Buy Orders: " + profile.buyOrders, "Sell Orders: " + profile.sellOrders
            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            dataAll.append(data)

        with open("report/report" + timestamp + ".json", "w") as outfile:

            json.dump(dataAll, outfile, indent="\t")

    return render(request, "profile.html", {"profile":currentuserProfile})

# Allow to login the site

def signin(request):

    if request.method == 'POST':

       username = request.POST.get('username')
       password = request.POST.get('password')
       user = authenticate(request, username=username, password=password)

       if user is not None:

           login(request, user)
           return redirect("../")

       else:

            messages.error(request, "Username o Password Errati... Riprova!")

    return render(request, 'login.html')

# Allow to register an account

def registration(request):

    if request.method == 'POST':

        form = registrationForm(request.POST)

        if form.is_valid():

            form.save()
            users = User.objects.order_by("-date_joined")
            lastUser = User.objects.get(username=users[0])
            Profile.objects.create(user=lastUser, balanceBTC=random.randrange (1,11))
            return redirect('login')

        else:

            messages.error(request, 'Account Utente non Creato... Riprova!')

    else:

        form = registrationForm()


    return render(request, "register.html", {'form':form})

# Allow to logout the site

def logout(request):

    django_logout(request)
    return redirect("../")

# Only for registered users

@login_required()
def tradeOrder(request):

    user=request.user
    profile = Profile.objects.get(user=user)
    opensellOrders = Order.objects.filter(position="Sell", status="Open").order_by("price")
    openbuyOrders = Order.objects.filter(position="Buy", status="Open").order_by("price")
    getData = Report()
    lastPrice = getData.cryptoData() # Get BTC value from the CoinMarket Api

    if request.method == "POST":

        buyprice = request.POST.get("buyprice")
        sellprice = request.POST.get("sellprice")
        buybtc = request.POST.get("buybtc")
        sellbtc = request.POST.get("sellbtc")

        if request.POST.get("buybtc") and request.POST.get("buyprice"):

            if float(buybtc) * float(buyprice) <= profile.balance:

                newOrder = Order.objects.create(user=user, price=float(buyprice), BTCs=float(buybtc),
                                            value=float(buyprice) * float(buybtc), position="Buy", status="Open",
                                            datetime=datetime.datetime.now())
                newOrder.save()
                messages.success(request, "Order Placed!")

                if len(opensellOrders)>0:

                    for order in opensellOrders:

                        if order.price <= newOrder.price:

                            if order.BTCs > newOrder.BTCs:

                                order.BTCs-=newOrder.BTCs
                                newOrder.status="Close"
                                orderComplete = Order.objects.create(user=order.user, price=float(buyprice), BTCs=float(buybtc),
                                            value=float(buyprice) * float(buybtc), position="Sell", status="Close",
                                            datetime=datetime.datetime.now())
                                profileVendor = Profile.objects.get(user=order.user)
                                profileVendor.balance += newOrder.value
                                profile.balance -= newOrder.value
                                profileVendor.balanceBTC -= newOrder.BTCs
                                profile.balanceBTC += newOrder.BTCs
                                profile.save()
                                orderComplete.orderSold(profileVendor)
                                newOrder.orderPurchased(profile)
                                profileVendor.save()
                                orderComplete.save()
                                order.save()
                                newOrder.save()
                                return redirect("../trade")

                            elif order.BTCs == newOrder.BTCs:

                                order.status="Close"
                                newOrder.status="Close"
                                profileVendor = Profile.objects.get(user=order.user)
                                profileVendor.balance += newOrder.value
                                profile.balance -= newOrder.value
                                profileVendor.balanceBTC -= newOrder.BTCs
                                profile.balanceBTC += newOrder.BTCs
                                order.orderSold(profileVendor)
                                newOrder.orderPurchased(profile)
                                profile.save()
                                profileVendor.save()
                                order.save()
                                newOrder.save()
                                return redirect("../trade")

                            elif order.BTCs < newOrder.BTCs:

                                newOrder.BTCs-=order.BTCs
                                order.status="Close"
                                orderComplete = Order.objects.create(user=user, price=float(buyprice), BTCs=float(buybtc),
                                                             value=float(buyprice) * float(buybtc), position="Buy",
                                                             status="Close",
                                                             datetime=datetime.datetime.now())
                                profileVendor = Profile.objects.get(user=order.user)
                                profileVendor.balance += newOrder.value
                                profile.balance -= newOrder.value
                                profileVendor.balanceBTC -= newOrder.BTCs
                                profile.balanceBTC += newOrder.BTCs
                                orderComplete.orderPurchased(profile)
                                order.orderSold(profileVendor)
                                profile.save()
                                profileVendor.save()
                                orderComplete.save()
                                order.save()
                                newOrder.save()
                                return redirect("../trade")

                        else:

                            return redirect("../trade")

                else:
                    return redirect("../trade")

            else:
                messages.error(request, "You haven't enough credit to buy!")
                return redirect("../trade")



        elif request.POST.get("sellbtc") and request.POST.get("sellprice"):

            if float(sellbtc) <= profile.balanceBTC:

                newOrder = Order.objects.create(user=user, price=float(sellprice), BTCs=float(sellbtc),
                                            value=int(sellbtc) * float(sellprice), position="Sell", status="Open",
                                            datetime=datetime.datetime.now())
                newOrder.save()
                messages.success(request, "Order Placed!")

                if len(openbuyOrders) > 0:

                    for order in openbuyOrders:

                        if order.price >= newOrder.price:

                            if order.BTCs > newOrder.BTCs:

                                order.BTCs -= newOrder.BTCs
                                newOrder.status="Close"
                                orderComplete = Order.objects.create(user=order.user, price=float(sellprice), BTCs=float(sellbtc),
                                                             value=float(sellprice) * float(sellbtc), position="Buy",
                                                             status="Close",
                                                             datetime=datetime.datetime.now())
                                profileBuyer = Profile.objects.get(user=order.user)
                                profileBuyer.balance -= newOrder.value
                                profile.balance += newOrder.value
                                profileBuyer.balanceBTC += newOrder.BTCs
                                profile.balanceBTC -= newOrder.BTCs
                                orderComplete.orderPurchased(profileBuyer)
                                newOrder.orderSold(profile)
                                profile.save()
                                profileBuyer.save()
                                orderComplete.save()
                                order.save()
                                newOrder.save()
                                return redirect("../trade")

                            elif order.BTCs == newOrder.BTCs:

                                order.status="Close"
                                newOrder.status="Close"
                                profileBuyer = Profile.objects.get(user=order.user)
                                profileBuyer.balance -= newOrder.value
                                profile.balance += newOrder.value
                                profileBuyer.balanceBTC += newOrder.BTCs
                                profile.balanceBTC -= newOrder.BTCs
                                order.orderPurchased(profileBuyer)
                                newOrder.orderSold(profile)
                                profile.save()
                                profileBuyer.save()
                                order.save()
                                newOrder.save()
                                return redirect("../trade")

                            elif order.BTCs < newOrder.BTCs:

                                newOrder.BTCs -= order.BTCs
                                order.status="Close"
                                orderComplete = Order.objects.create(user=user, price=float(sellprice), BTCs=float(sellbtc),
                                                             value=float(sellprice) * float(sellbtc), position="Sell",
                                                             status="Close",
                                                             datetime=datetime.datetime.now())
                                profileBuyer = Profile.objects.get(user=order.user)
                                profileBuyer.balance -= newOrder.value
                                profile.balance += newOrder.value
                                profileBuyer.balanceBTC += newOrder.BTCs
                                profile.balanceBTC -= newOrder.BTCs
                                orderComplete.orderSold(profile)
                                order.orderPurchased(profileBuyer)
                                profile.save()
                                profileBuyer.save()
                                orderComplete.save()
                                order.save()
                                newOrder.save()
                                return redirect("")


                        else:

                            return redirect("../trade")
                else:

                    return redirect("../trade")

            else:
                messages.error(request, "You haven't enough BTC to sell!")
                return redirect("../trade")

    return render(request, "trade.html", {"lastPrice":lastPrice, "opensellOrders":opensellOrders, "openbuyOrders":openbuyOrders})



