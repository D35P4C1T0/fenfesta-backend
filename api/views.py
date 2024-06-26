import bcrypt
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from .models import Event, Reservation, UserProfile as User
from .serializers import EventSerializer, UserSerializer, ReservationSerializer

from auth.validations import custom_validation, validate_password, validate_email


# Class to view all users
class UserListView(generics.ListCreateAPIView):
    # only admin has access
    permission_classes = (permissions.IsAdminUser,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Class to create a new user
# also hash the password with bcrypt
class UserRetrieveDestroyView(generics.ListCreateAPIView):
    # for admin only
    permission_classes = (permissions.IsAdminUser,)

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(pk=kwargs["pk"])
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response(
                data={
                    "message": "User with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(pk=kwargs["pk"])
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                data={
                    "message": "User with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


class UserReservationsListRetrieveView(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get(self, request, *args, **kwargs):
        try:
            reservations = Reservation.objects.filter(user_id=kwargs["pk"])
            return Response(ReservationSerializer(reservations, many=True).data)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for user with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


class UserReservedEventsListView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        try:
            reservations = Reservation.objects.filter(user_id=kwargs["pk"])
            events = Event.objects.filter(id__in=[reservation.event_id for reservation in reservations])
            return Response(EventSerializer(events, many=True).data)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for user with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


# Class to view all events
class EventListRetrieveView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def post(self, request, *args, **kwargs):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class to view a single event
class EventRetrieveViewDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        try:
            event = self.queryset.get(pk=kwargs["pk"])
            return Response(EventSerializer(event).data)
        except Event.DoesNotExist:
            return Response(
                data={
                    "message": "Event with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, *args, **kwargs):
        try:
            event = self.queryset.get(pk=kwargs["pk"])
            serializer = EventSerializer()
            updated_event = serializer.update(event, request.data)
            return Response(EventSerializer(updated_event).data)
        except Event.DoesNotExist:
            return Response(
                data={
                    "message": "Event with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        try:
            event = self.queryset.get(pk=kwargs["pk"])
            event.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Event.DoesNotExist:
            return Response(
                data={
                    "message": "Event with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


# should find users who had a reservations for a given event ID
# query the reservation table for the event ID
# then query the user table for the user ID
# also check if the event has no reservations
class EventRetrieveAttendeesGivenEvent(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        try:
            reservations = Reservation.objects.filter(event_id=kwargs["pk"])
            print(reservations.values())
            if len(reservations) == 0:
                return Response(
                    data={
                        "message": "No reservations for event with id: {}".format(kwargs["pk"])
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            users = User.objects.filter(id__in=[reservation.user_id_id for reservation in reservations])
            return Response(UserSerializer(users, many=True).data)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for event with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


class EventRetrieveReservationsGivenEvent(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get(self, request, *args, **kwargs):
        try:
            reservations = Reservation.objects.filter(event_id=kwargs["pk"])
            return Response(ReservationSerializer(reservations, many=True).data)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for event with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


# Class to view all reservations
class ReservationListRetrieveView(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer


# get all reservation for a given event ID
class ReservationListRetrieveViewGivenEvent(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get(self, request, *args, **kwargs):
        try:
            reservations = self.queryset.filter(event_id=kwargs["pk"])
            return Response(ReservationSerializer(reservations, many=True).data)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for event with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        try:
            reservations = self.queryset.filter(event_id=kwargs["pk"])
            for reservation in reservations:
                reservation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Reservation.DoesNotExist:
            return Response(
                data={
                    "message": "No reservations for event with id: {}".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )


# reservation create delete
class ReservationCreateDeleteViewGivenUser(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    # post should check if the user is already registered for the event
    def post(self, request, *args, **kwargs):
        try:
            reservation = self.queryset.get(event_id=kwargs["pk"], username=kwargs["username"])
            return Response(
                data={
                    "message": "User already registered for this event"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Reservation.DoesNotExist:
            serializer = ReservationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
