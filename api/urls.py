from django.urls import path
from . import views

urlpatterns = [
    # Events
    path('events/', views.EventListRetrieveView.as_view(), name='events'),
    path('events/<int:pk>/', views.EventRetrieveViewDestroy.as_view(), name='event'),
    path('events/<int:pk>/reservations/', views.ReservationListRetrieveViewGivenEvent.as_view(), name='event_reservationsnmt'),
    path('events/<int:pk>/reservations/<str:username>/', views.ReservationCreateDeleteViewGivenUser.as_view(), name='event_reservations'),
    path('events/<int:pk>/attendees/', views.EventRetrieveAttendeesGivenEvent.as_view(), name='event_reservations'),

    # Users
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/register/', views.UserCreateView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDeleteView.as_view(), name='users'),
    path('users/<int:pk>/reservations/', views.UserReservationsListRetrieveView.as_view(), name='user_reservations'),
    path('users/<int:pk>/reserved_events/', views.UserReservedEventsListView.as_view(), name='user_reserved_events'),

    # Reservations
    path('reservations/', views.ReservationListRetrieveView.as_view(), name='reservations'),
    path('reservations/<int:pk>/', views.ReservationListRetrieveViewGivenEvent.as_view(), name='reservation'),

]
