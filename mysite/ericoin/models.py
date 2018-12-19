import datetime

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible



class Account(models.Model):
    account_name = models.CharField(max_length=200)
    balance = models.PositiveIntegerField()
    public_key = models.CharField(max_length=200, unique=True, editable=False)
    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set default name
            self.account_name = "Anonymous"
        super(Account, self).save(*args, **kwargs)
        return self.account_name
    def __str__(self):
        return self.public_key
    

class Transaction(models.Model):
    amount = models.PositiveIntegerField()
    index = models.PositiveIntegerField()
    recipient_key = models.CharField(max_length=200)
    sender_key = models.CharField(max_length=200)
    time_stamp = models.DateTimeField(auto_now=False, auto_now_add=False)
    
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set default name
            self.account_name = "Anonymous"
        super(Account, self).save(*args, **kwargs)
        return self.account_name
    def __str__(self):
        return self.public_key
        
    """    
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    info_text = models.CharField(max_length=200)
    class Meta:
        verbose_name_plural = "information"
    def __str__(self):
        return self.info_text
    """
