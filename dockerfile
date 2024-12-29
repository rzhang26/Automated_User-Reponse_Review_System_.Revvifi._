# Use the official Python image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Flask app port
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
