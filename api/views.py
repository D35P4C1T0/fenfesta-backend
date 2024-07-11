import os
import requests

import bcrypt
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from .models import Event, Reservation, UserProfile as User
from .serializers import EventSerializer, UserSerializer, ReservationSerializer

from auth.validations import registration_validation, validate_password, validate_email


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


class EventSearchView(APIView):
    def get(self, request):
        keyword = request.query_params.get('keyword', '')
        if not keyword:
            return Response({"error": "Please provide a search keyword"}, status=status.HTTP_400_BAD_REQUEST)

        events = Event.objects.filter(
            Q(name__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(location__icontains=keyword) |
            Q(tags__icontains=keyword)
        ).distinct()

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class EventListDeleteView(generics.ListCreateAPIView):
    # admins only
    permission_classes = (permissions.IsAdminUser,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def delete(self, request, *args, **kwargs):
        try:
            events = self.queryset.all()
            for event in events:
                event.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Event.DoesNotExist:
            return Response(
                data={
                    "message": "No events to delete"
                },
                status=status.HTTP_404_NOT_FOUND
            )


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


class EventListRetrieveViewGivenMonth(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        try:
            events = self.queryset.filter(date__month=kwargs["pk"])
            return Response(EventSerializer(events, many=True).data)
        except Event.DoesNotExist:
            return Response(
                data={
                    "message": "No events for month with id: {}".format(kwargs["pk"])
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


# Geocoding
class GeocodeView(APIView):
    def get(self, request):
        address = request.data.get('address')
        if not address:
            return Response({'error': 'Address parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get API key from environment variable
        api_key = os.environ.get('GEOCODING_API_KEY')
        if not api_key:
            return Response({'error': 'API key not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Example API endpoint (replace with your actual geocoding service URL)
        geocoding_api_url = 'geocoding.openapi.it/geocode'

        # Parameters for the GET request
        params = {
            'address': address,
        }

        # Headers including the API token
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(geocoding_api_url, params=params, headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()

            if 'results' in data and data['results']:
                location = data['results'][0]
                return Response({
                    'address': address,
                    'latitude': location['latitude'],
                    'longitude': location['longitude']
                })
            else:
                return Response({'error': 'No results found'}, status=status.HTTP_404_NOT_FOUND)

        except requests.RequestException as e:
            return Response({'error': f'API request failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
