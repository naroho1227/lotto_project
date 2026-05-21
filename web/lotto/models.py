import json
from django.db import models
from django.contrib.auth.models import User


class LottoDraw(models.Model):
    draw_number = models.IntegerField(unique=True)
    numbers     = models.CharField(max_length=50)   # JSON 예: "[1,2,3,4,5,6]"
    bonus       = models.IntegerField()
    draw_date   = models.DateTimeField(auto_now_add=True)

    def get_numbers(self):
        return json.loads(self.numbers)

    def __str__(self):
        return f"{self.draw_number}회차"


class LottoTicket(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    draw         = models.ForeignKey(LottoDraw, null=True, blank=True, on_delete=models.SET_NULL)
    numbers      = models.CharField(max_length=50)   # JSON 예: "[1,2,3,4,5,6]"
    is_auto      = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(auto_now_add=True)
    rank         = models.IntegerField(null=True, blank=True)  # None=미추첨, 0=낙첨

    def get_numbers(self):
        return json.loads(self.numbers)

    def __str__(self):
        return f"{self.user.username} - {self.get_numbers()}"
