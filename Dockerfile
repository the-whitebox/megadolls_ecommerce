FROM 556229327848.dkr.ecr.us-east-1.amazonaws.com/python:3.6-buster
RUN python -m pip install --upgrade pip
ENV PYTHONUNBUFFERED 1
# Set build arguments
ARG DEBUG
ARG ALLOWED_HOSTS
ARG SITE_URL
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD
ARG DB_ENGINE
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST
ARG DB_PORT
ARG STRIPE_PUBLIC_KEY1
ARG STRIPE_SECRET_KEY1
ARG STRIPE_PUBLIC_KEY
ARG STRIPE_SECRET_KEY
ARG TAX_JAR_TOKEN1
ARG TAX_JAR_TOKEN
ARG SHIP_STATION_TOKEN
ARG SHIP_STATION_USERNAME
ARG SHIP_STATION_PASSWORD
ARG TWILIO_ACCOUNT_SID
ARG TWILIO_AUTH_TOKEN
ARG TWILIO_NUMBER
ARG FACEBOOK_CLIENT_ID
ARG FACEBOOK_SECRET
ARG GOOGLE_CLIENT_ID
ARG GOOGLE_SECRET
ARG SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
ARG SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
ARG SECRET_KEY
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_STORAGE_BUCKET_NAME
ARG DEFAULT_FILE_STORAGE

# Use the build arguments in your Dockerfile
ENV ALLOWED_HOSTS=$ALLOWED_HOSTS
ENV DEBUG=$DEBUG
ENV SITE_URL=$SITE_URL
ENV EMAIL_HOST_USER=$EMAIL_HOST_USER
ENV EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
ENV DB_ENGINE=$DB_ENGINE
ENV DB_NAME=$DB_NAME
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV STRIPE_PUBLIC_KEY1=$STRIPE_PUBLIC_KEY1
ENV STRIPE_SECRET_KEY1=$STRIPE_SECRET_KEY1
ENV STRIPE_PUBLIC_KEY=$STRIPE_PUBLIC_KEY
ENV STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
ENV TAX_JAR_TOKEN1=$TAX_JAR_TOKEN1
ENV TAX_JAR_TOKEN=$TAX_JAR_TOKEN
ENV SHIP_STATION_TOKEN=$SHIP_STATION_TOKEN
ENV SHIP_STATION_USERNAME=$SHIP_STATION_USERNAME
ENV SHIP_STATION_PASSWORD=$SHIP_STATION_PASSWORD
ENV TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
ENV TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
ENV TWILIO_NUMBER=$TWILIO_NUMBER
ENV FACEBOOK_CLIENT_ID=$FACEBOOK_CLIENT_ID
ENV FACEBOOK_SECRET=$FACEBOOK_SECRET
ENV GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
ENV GOOGLE_SECRET=$GOOGLE_SECRET
ENV SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=$SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
ENV SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=$SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
ENV SECRET_KEY=$SECRET_KEY
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ENV AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME
ENV DEFAULT_FILE_STORAGE=$DEFAULT_FILE_STORAGE
RUN mkdir /code
WORKDIR /code
RUN apt-get -y update \
    && apt-get install -y cron \
    # Cleanup apt cache
    && apt-get clean
COPY requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/

RUN echo "uwsgi --http=0.0.0.0:9000 --module=megadolls.wsgi:application --py-autoreload=1" >> /code/docker-entrypoint.sh

RUN python manage.py crontab add
# RUN python manage.py crontab show

CMD ["bash", "/code/docker-entrypoint.sh"]