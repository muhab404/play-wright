# Use valid Playwright base image with browsers pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# # Set the Lambda runtime interface client
# RUN pip install aws-lambda-py
RUN pip install awslambdaric
RUN pip install playwright  # Ensure playwright is installed
RUN playwright install

# Copy application files
COPY . .
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-account-key.json

ENTRYPOINT [ "python", "-m", "awslambdaric" ]
# Define handler for AWS Lambda
CMD ["google_drive_handler.lambda_handler"]
