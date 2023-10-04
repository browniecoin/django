# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory
WORKDIR /website

# Install the AWS CLI
RUN apt-get update && apt-get install -y awscli

# Set environment variables for AWS access key and secret key
ENV AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
ENV AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY

# Use the AWS CLI to download the application code from S3
RUN aws s3 cp s3://modernfarms/website.zip . && unzip my-project.zip && rm website.zip

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=myproject.settings

# Run database migrations
RUN python manage.py migrate

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Start the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
