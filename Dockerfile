# Use an official Python runtime as a base image
FROM python:latest

# Install necessary dependencies (git, curl for downloading files)
RUN apt-get update && apt-get install -y git curl binwalk default-jre && rm -rf /var/lib/apt/lists/*
RUN pip install requests ubi_reader

# Set the working directory in the container
WORKDIR /app

# Copy the script into the container
COPY script.py .

# Define the command to run the script
CMD ["python", "script.py"]