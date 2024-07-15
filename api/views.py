import os
import requests

import bcrypt
from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Event, Reservation, UserProfile as User
from .serializers import EventSerializer, UserSerializer, ReservationSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from dotenv import load_dotenv

from auth.validations import registration_validation, validate_password, validate_email

load_dotenv()


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


class DeleteUserAccountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        user = request.user
        try:
            # Delete all reservations made by the user
            Reservation.objects.filter(user=user).delete()

            # Delete all events created by the user
            Event.objects.filter(creator=user).delete()

            # Finally, delete the user account
            user.delete()

            return Response({
                "message": "User account and all associated data have been successfully deleted."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # If any error occurs, rollback the transaction
            transaction.set_rollback(True)
            return Response({
                "error": f"An error occurred while deleting the account: {str(e)}",
                "code": "DELETE_ACCOUNT_ERROR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventCreatorInfoView(APIView):
    def get(self, request, event_id):
        try:
            # Get the event by ID
            event = get_object_or_404(Event, id=event_id)

            # Get the creator of the event
            creator = event.creator

            # Prepare the response data
            creator_info = {
                'username': creator.username,
                'first_name': creator.first_name,
                'last_name': creator.last_name
            }

            return Response(creator_info, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({
                'error': 'Event not found',
                'code': 'EVENT_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'error': f'An unexpected error occurred: {str(e)}',
                'code': 'UNEXPECTED_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IsEventReservedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Get the event or return 404 if not found
        event = get_object_or_404(Event, pk=pk)

        # Check if the user has a reservation for this event
        is_reserved = Reservation.objects.filter(user=request.user, event=event).exists()

        return Response({
            'event_id': pk,
            'is_reserved': is_reserved
        }, status=status.HTTP_200_OK)


class RemoveReservationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            with transaction.atomic():
                # Get the event or raise ObjectDoesNotExist
                try:
                    event = Event.objects.get(pk=pk)
                except Event.DoesNotExist:
                    return Response({
                        'error': 'Event not found',
                        'code': 'EVENT_NOT_FOUND'
                    }, status=status.HTTP_404_NOT_FOUND)

                # Try to get the reservation
                try:
                    reservation = Reservation.objects.get(user=request.user, event=event)
                except Reservation.DoesNotExist:
                    return Response({
                        'error': 'No reservation found for this event',
                        'code': 'RESERVATION_NOT_FOUND'
                    }, status=status.HTTP_404_NOT_FOUND)

                # Check if the event has already occurred
                from django.utils import timezone
                if event.date < timezone.now():
                    return Response({
                        'error': 'Cannot remove reservation for past events',
                        'code': 'PAST_EVENT'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Reservation exists and event is in the future, delete it
                reservation.delete()

                # Increase the event's capacity_left
                event.capacity_left += 1
                event.save()

                return Response({
                    'message': 'Reservation successfully removed',
                    'event_id': pk
                }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the exception here
            return Response({
                'error': 'An unexpected error occurred',
                'code': 'UNEXPECTED_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class UserReservedEventsListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get reservations for the authenticated user
            reservations = Reservation.objects.filter(user=request.user)

            # Get events associated with these reservations, ordered by date
            events = Event.objects.filter(
                id__in=[reservation.event_id for reservation in reservations]
            ).order_by('date')  # This line orders the events by date

            # Serialize and return the events
            return Response(EventSerializer(events, many=True).data)
        except Exception as e:
            return Response(
                data={
                    "message": f"Error retrieving reservations: {str(e)}"
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


class UpcomingEventsView(generics.ListAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        # Get current date and time
        now = timezone.now()

        # Filter events that are happening now or in the future
        return Event.objects.filter(date__gte=now).order_by('date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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


class UserReservationCountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Count reservations for the authenticated user
            reservation_count = Reservation.objects.filter(user=request.user).count()

            return Response({
                'reservation_count': reservation_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}',
                'code': 'UNEXPECTED_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class CreateEventView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # if not request.user.has_perm('your_app.add_event'):
        #     raise PermissionDenied("You don't have permission to create events.")

        print(request.data)

        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            # Add the current user as the creator of the event
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


## View to make a new reservation
class CreateReservationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        event_id = request.data.get('event_id')
        if not event_id:
            return Response({'error': 'Event ID is required', 'code': 'MISSING_EVENT_ID'},
                            status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Event, id=event_id)

        if event.capacity_left <= 0:
            return Response({'error': 'This event is fully booked', 'code': 'EVENT_FULL'},
                            status=status.HTTP_400_BAD_REQUEST)

        existing_reservation = Reservation.objects.filter(user=request.user, event=event).first()
        if existing_reservation:
            return Response({'error': 'You already have a reservation for this event', 'code': 'RESERVATION_EXISTS'},
                            status=status.HTTP_400_BAD_REQUEST)

        reservation = Reservation(user=request.user, event=event)
        reservation.save()

        event.capacity_left -= 1
        event.save()

        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Geocoding
class GeocodeView(APIView):
    def post(self, request):
        address = request.data.get('address')
        if not address:
            return Response({'error': 'Address parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get API key from environment variable
        api_key = settings.GEOCODING_API_KEY
        if not api_key:
            return Response({'error': 'API key not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Example API endpoint (replace with your actual geocoding service URL)
        geocoding_api_url = 'https://geocoding.openapi.it/geocode'

        # Body of the request
        data = {"address": address}

        # Headers including the API token
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(geocoding_api_url, headers=headers, json=data)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()

            if data['success']:
                element = data['element']
                return Response({
                    'address': element['streetName'],
                    'latitude': element['latitude'],
                    'longitude': element['longitude'],
                    'streetNumber': element['streetNumber'],
                    'city': element['locality'],
                })
            else:
                return Response({'error': 'No results found'}, status=status.HTTP_404_NOT_FOUND)

        except requests.RequestException as e:
            return Response({'error': f'API request failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
