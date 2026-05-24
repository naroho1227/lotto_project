from django.urls import path
from . import views

urlpatterns = [
    path('',                     views.index,         name='index'),
    path('login/',               views.login_view,    name='login'),
    path('logout/',              views.logout_view,   name='logout'),
    path('register/',            views.register_view, name='register'),
    path('buy/manual/',          views.buy_manual,    name='buy_manual'),
    path('buy/auto/',            views.buy_auto,      name='buy_auto'),
    path('my-tickets/',          views.my_tickets,    name='my_tickets'),
    path('check/',               views.check,         name='check'),
    path('admin-panel/sales/',   views.admin_sales,   name='admin_sales'),
    path('admin-panel/draw/',    views.admin_draw,    name='admin_draw'),
    path('admin-panel/winners/', views.admin_winners, name='admin_winners'),
]
