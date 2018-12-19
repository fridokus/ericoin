from django.conf.urls import url

from . import views


app_name = 'ericoin'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^balances/$', views.BalanceView.as_view(), name='balances'),
    url(r'^blockchain/$', views.ChainView.as_view(), name='blockchain'),
    url(r'^transactions/$', views.TransactionView.as_view(), name='transactions'),
    url(r'^posted-transaction/$', views.TransactionView.make_transaction, name='sent')
]

