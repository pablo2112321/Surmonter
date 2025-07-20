gunicorn_start.sh
#!/bin/bash

NAME="surmonter"
DIR=/home/ubuntu/surmonter
USER=ubuntu
GROUP=www-data
WORKERS=3
BIND=unix:$DIR/$NAME.sock
DJANGO_SETTINGS_MODULE=surmonter.settings.prod
DJANGO_WSGI_MODULE=surmonter.wsgi

source /home/ubuntu/venv/bin/activate
cd $DIR
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --user=$USER --group=$GROUP \
  --bind=$BIND \
  --log-level=debug \
  --log-file=-
