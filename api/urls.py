from django.urls import path

import api.views
import auth.views
from . import views

urlpatterns = [
    # Events
    path('events/', views.EventListRetrieveView.as_view(), name='events'),
    path('events/upcoming', views.UpcomingEventsView.as_view(), name='events'),
    path('events/new', views.CreateEventView.as_view(), name='events'),
    path('events/<int:pk>/', views.EventRetrieveViewDestroy.as_view(), name='event'),
    path('events/month/<int:pk>/', views.EventListRetrieveViewGivenMonth.as_view(), name='events_month'),
    path('events/search', views.EventSearchView.as_view(), name='event-search'),
    path('events/<int:pk>/reservations/', views.ReservationListRetrieveViewGivenEvent.as_view(),
         name='event_reservation'),
    path('events/<int:pk>/reservations/<str:username>/', views.ReservationCreateDeleteViewGivenUser.as_view(),
         name='event_reservations'),
    path('events/<int:pk>/attendees/', views.EventRetrieveAttendeesGivenEvent.as_view(), name='event_reservations'),
    path('events/<int:event_id>/creator-info/', views.EventCreatorInfoView.as_view(), name='event-creator-info'),
    # Users
    path('users/profile/', auth.views.UserView.as_view(), name='user'),  # protected route
    path('users/number-of-reservations/', views.UserReservationCountView.as_view(), name='user_reservations_count'),
    path('users/<int:pk>/', views.UserRetrieveDestroyView.as_view(), name='user'),
    path('users/delete-account', views.DeleteUserAccountView.as_view(), name='delete_account'),
    path('users/all/', views.UserListView.as_view(), name='all_users'),
    # path('users/register/', views.UserCreateView.as_view(), name='users'),    # spostati in auth
    # path('users/<int:pk>/', views.UserDeleteView.as_view(), name='users'),
    path('users/<int:pk>/reservations/', views.UserReservationsListRetrieveView.as_view(), name='user_reservations'),
    path('users/reserved_events/', views.UserReservedEventsListView.as_view(), name='user_reserved_events'),

    # Reservations
    path('reservations/', views.ReservationListRetrieveView.as_view(), name='reservations'),
    path('reservations/<int:pk>/', views.ReservationListRetrieveViewGivenEvent.as_view(), name='reservation'),

    path('reservations/<int:pk>/is_reserved', views.IsEventReservedView.as_view(), name='reservation'),

    path('reservations/<int:pk>/remove', views.RemoveReservationView.as_view(), name='delete_reservation'),

    path('reservations/new', views.CreateReservationView.as_view(), name='create_reservation'),

    # Geocode
    path('geocode/', views.GeocodeView.as_view(), name='geocode'),
]
