# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create a directory for the database
RUN mkdir -p /app/data

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a script to run migrations, create admin user, and start the server
RUN echo '#!/bin/sh' > /app/entrypoint.sh
RUN echo 'python manage.py migrate' >> /app/entrypoint.sh
RUN echo 'python manage.py create_admin' >> /app/entrypoint.sh
RUN echo 'exec "$@"' >> /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:8000", "--key-file", "key.pem", "--cert-file", "cert.pem"]