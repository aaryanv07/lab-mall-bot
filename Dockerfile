# Use the official lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Upgrade pip to prevent installation issues
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements FIRST (for caching)
COPY requirements.txt .

# Install dependencies (This is where uvicorn gets installed)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create the static folder if it doesn't exist (Safety measure)
RUN mkdir -p static

# Expose the port
EXPOSE 8080

# Command to run the application using python module mode
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]