# Use the official Apify Actor Python base image
FROM apify/actor-python:3.11

# Copy requirements.txt and install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy source code
COPY . ./

RUN python3 -m compileall -q .

# Set the command to run the Actor
CMD ["python3", "-m", "src"]