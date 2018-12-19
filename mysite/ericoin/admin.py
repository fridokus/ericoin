from django.contrib import admin

from .models import Account, Transaction


admin.site.register(Account)
admin.site.register(Transaction)
