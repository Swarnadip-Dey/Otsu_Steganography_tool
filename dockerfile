# Use a smaller, Alpine-based Python image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apk update && apk add --no-cache gcc musl-dev libffi-dev

# Copy requirements.txt to the container
COPY requirements.txt /app/

# Install Python dependencies and clean up
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev libffi-dev

# Copy the rest of the application code into the container
COPY . /app

# Expose the Flask default port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Command to run the Flask app
CMD ["flask", "run"]
