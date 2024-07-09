from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import validate_email as django_validate_email

UserModel = get_user_model()


def registration_validation(data):
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not email:
        raise ValidationError('Email is required')
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValidationError('Invalid email format')
    if UserModel.objects.filter(email=email).exists():
        raise ValidationError('Email already exists')

    if not username:
        raise ValidationError('Username is required')
    if UserModel.objects.filter(username=username).exists():
        raise ValidationError('Username already exists')

    if not password:
        raise ValidationError('Password is required')
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')

    return data


def validate_login(data):
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # Check if login is using email or username
    if email:
        if not username:
            try:
                django_validate_email(email)
            except ValidationError:
                raise ValidationError('Invalid email format')

            try:
                username = UserModel.objects.get(email=email).username
            except UserModel.DoesNotExist:
                raise ValidationError('No user found with this email address')
    elif username:
        if not UserModel.objects.filter(username=username).exists():
            raise ValidationError('No user found with this username')
    else:
        raise ValidationError('Either email or username is required')

    if not password:
        raise ValidationError('Password is required')

    user = authenticate(username=username, password=password)

    if user is None:
        raise ValidationError('Invalid credentials')

    if not user.is_active:
        raise ValidationError('This account is inactive')

    return {
        'user': user,
        'email': email,
        'username': username,
        'password': password,
    }


def validate_email(data):
    email = data.get('email', '').strip()
    if not email:
        raise ValidationError('Email is required')
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValidationError('Invalid email format')
    if UserModel.objects.filter(email=email).exists():
        raise ValidationError('Email already exists')
    return True


def validate_username(data):
    username = data.get('username', '').strip()
    if not username:
        raise ValidationError('Username is required')
    if UserModel.objects.filter(username=username).exists():
        raise ValidationError('Username already exists')
    return True


def validate_password(data):
    password = data.get('password', '').strip()
    if not password:
        raise ValidationError('Password is required')
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    return True
