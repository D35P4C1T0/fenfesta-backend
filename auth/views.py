from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate, update_session_auth_hash
from api.models import UserProfile as UserModel
from api.serializers import UserSerializer
from .serializers import UserRegisterSerializer
from .validations import registration_validation, validate_login
from django.core.exceptions import ValidationError


# class UserRegister(APIView):
#     permission_classes = (permissions.AllowAny,)
#
#     def post(self, request):
#         clean_data = registration_validation(request.data)
#         serializer = UserRegisterSerializer(data=clean_data)
#         if serializer.is_valid(raise_exception=True):
#             user = serializer.create(clean_data)
#             if user:
#                 refresh = RefreshToken.for_user(user)
#                 return Response({
#                     'user': serializer.data,
#                     'refresh': str(refresh),
#                     'access': str(refresh.access_token),
#                 }, status=status.HTTP_201_CREATED)
#         return Response(status=status.HTTP_400_BAD_REQUEST)


class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            clean_data = validate_login(request.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        username = clean_data.get('username')
        password = clean_data.get('password')

        if not username or not password:
            return Response({'error': 'Both username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'User account is disabled'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)

        return Response({
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class UserRegistration(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'message': 'User registered successfully'
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({'error': 'Username or email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogout(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({'error': 'New password must be different from the current password'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Add any additional password validation here (e.g., minimum length, complexity)

        user.set_password(new_password)
        user.save()

        # Update the session to prevent the user from being logged out
        update_session_auth_hash(request, user)

        return Response({'message': 'Password successfully changed'}, status=status.HTTP_200_OK)
