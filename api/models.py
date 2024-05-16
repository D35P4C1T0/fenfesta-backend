from django.db import models

# Create your models here.

# class for User
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    hashed_password = models.CharField(max_length=100)
    is_premium = models.BooleanField()

    def __str__(self):
        return self.name + " (" + self.email + ")" + (" (Premium)" if self.is_premium else "")


# class for Event
class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    capacity = models.IntegerField()
    capacity_left = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.name + " by " + self.creator.name
                + " at " + self.location + " on " + str(self.date))


# class for Subscription. A user have a subscription with
# an amount of events that they can create and the amount left
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    max_amount = models.IntegerField()
    amount_left = models.IntegerField()
    due_date = models.DateTimeField()

    def __str__(self):
        return self.user.name + " has " + str(self.amount_left) + " events left"


# class for Reservation
# couples a user with an event
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name + " reserved " + self.event.name
