# Use the official Python 3.12.1 base image
FROM python:3.12.1-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install any necessary dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080
ENV PORT 8080

# Run the application
CMD ["python", "app.py"]