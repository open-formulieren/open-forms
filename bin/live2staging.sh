#!/bin/bash

# This script should be run on staging.
source live2staging_settings.sh

# Script starts here
TMP_FILE="$PGSQL_PROD_DB_NAME-livedb.sql"
TMP_MEDIA_FILE="$PGSQL_PROD_DB_NAME-media.tgz"

if [ -f $TMP_FILE ]; then
    echo -n "Create new dump? [y/n] "
    read -n 1 yesno
else
    yesno="y"
fi
echo

if [ "$yesno" == "y" ]; then
    echo "Creating dump of production database, please wait..."

    PGSQLDUMP_PROD_CMD_ARGS="--dbname=postgresql://$PGSQL_PROD_USERNAME:$PGSQL_PROD_PASSWORD@127.0.0.1:5432/$PGSQL_PROD_DB_NAME "
    PGSQLDUMP_PROD_CMD="pg_dump $PGSQLDUMP_PROD_CMD_ARGS > /srv/sites/$TMP_FILE"

    ssh $PGSQL_PROD_HOST "$PGSQLDUMP_PROD_CMD"
    scp $PGSQL_PROD_HOST:/srv/sites/$TMP_FILE $TMP_FILE
fi

echo -n "Continue loading database? [y/n] "
read -n 1 cont
if [ "$cont" == "n" ]; then
    echo
    exit
fi
echo

sudo supervisorctl stop $SUPERVISOR_GROUP:*
sudo service cron stop

echo "Loading dump of production database into staging, please wait..."
sudo su postgres --command="dropdb $PGSQL_STAGING_DB_NAME"
sudo su postgres --command="createdb $PGSQL_STAGING_DB_NAME --owner=$PGSQL_STAGING_USERNAME"
PGSQL_STAGING_CMD="psql -q --dbname=postgresql://$PGSQL_STAGING_USERNAME:$PGSQL_STAGING_PASSWORD@127.0.0.1:5432/$PGSQL_STAGING_DB_NAME "
$PGSQL_STAGING_CMD < $TMP_FILE

echo "Modifying data on staging to work with production data..."
$PGSQL_STAGING_CMD < $PWD/live2staging_postimport.sql

echo "Copying media files from production to staging..."
rsync -au $PGSQL_PROD_HOST:$PROD_MEDIA_PATH/ $STAGING_MEDIA_PATH/

sudo chmod -R g+rw $STAGING_PROJECT_PATH

cd $STAGING_PROJECT_PATH
source env/bin/activate

env/bin/python src/manage.py migrate
env/bin/python src/manage.py locate_translation_files
sudo service cron start
sudo supervisorctl start $SUPERVISOR_GROUP:*

cd $PWD

NOW=$(date +"%Y-%m-%d")
FILE="$PGSQL_PROD_DB_NAME-live2staging-$NOW.sql"

if [ "$yesno" == "y" ]; then
    echo "Storing dump as $FILE..."
    cp "$PWD/$TMP_FILE" "$FILE"
    gzip $FILE
fi
