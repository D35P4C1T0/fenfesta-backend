from django.urls import path

import api.views
import auth.views
from . import views

urlpatterns = [
    # Events
    path('events/', views.EventListRetrieveView.as_view(), name='events'),
    path('events/new', views.CreateEventView.as_view(), name='events'),
    path('events/<int:pk>/', views.EventRetrieveViewDestroy.as_view(), name='event'),
    path('events/month/<int:pk>/', views.EventListRetrieveViewGivenMonth.as_view(), name='events_month'),
    path('events/search', views.EventSearchView.as_view(), name='event-search'),
    path('events/<int:pk>/reservations/', views.ReservationListRetrieveViewGivenEvent.as_view(),
         name='event_reservation'),
    path('events/<int:pk>/reservations/<str:username>/', views.ReservationCreateDeleteViewGivenUser.as_view(),
         name='event_reservations'),
    path('events/<int:pk>/attendees/', views.EventRetrieveAttendeesGivenEvent.as_view(), name='event_reservations'),

    # Users
    path('users/profile/', auth.views.UserView.as_view(), name='user'),  # protected route
    path('users/<int:pk>/', views.UserRetrieveDestroyView.as_view(), name='user'),
    path('users/all/', views.UserListView.as_view(), name='all_users'),
    # path('users/register/', views.UserCreateView.as_view(), name='users'),    # spostati in auth
    # path('users/<int:pk>/', views.UserDeleteView.as_view(), name='users'),
    path('users/<int:pk>/reservations/', views.UserReservationsListRetrieveView.as_view(), name='user_reservations'),
    path('users/<int:pk>/reserved_events/', views.UserReservedEventsListView.as_view(), name='user_reserved_events'),

    # Reservations
    path('reservations/', views.ReservationListRetrieveView.as_view(), name='reservations'),
    path('reservations/<int:pk>/', views.ReservationListRetrieveViewGivenEvent.as_view(), name='reservation'),

    # Geocode
    path('geocode/', views.GeocodeView.as_view(), name='geocode'),
]
