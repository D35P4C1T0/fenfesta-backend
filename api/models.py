import bcrypt
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class UserProfile(AbstractUser):
    pass

# class for Event
class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    capacity = models.IntegerField()
    capacity_left = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.name + " by " + self.creator.username
                + " at " + self.location + " on " + str(self.date))


# class for Subscription. A user have a subscription with
# an amount of events that they can create and the amount left
class Subscription(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    max_amount = models.IntegerField()
    amount_left = models.IntegerField()
    due_date = models.DateTimeField()

    def __str__(self):
        return self.user.username + " has " + str(self.amount_left) + " events left"


# class for Reservation
# couples a user with an event
class Reservation(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " reserved " + self.event.name
