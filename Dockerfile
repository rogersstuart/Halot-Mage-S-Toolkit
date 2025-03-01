# Use an official Python runtime as a base image
FROM python:latest

# Install necessary dependencies (git, curl for downloading files)
RUN apt-get update && apt-get install -y git libarchive-zip-perl curl binwalk default-jre expect && rm -rf /var/lib/apt/lists/*
RUN pip install requests ubi_reader

# Set the working directory in the container
WORKDIR /app

# Copy the script into the container
COPY script.py .
COPY apps.tar.gz .
COPY extract_apps.py .
COPY run_build.sh .

# Define the command to run the script
CMD ["python", "script.py"]