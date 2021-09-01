from . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.signin, name='login'),
    path('registration', views.registration   , name='registration'),
    path('logout',  views.logout, name='logout'),
    path('trade', views.tradeOrder, name="trade order"),
    path('profile', views.profile, name="user info"),
]