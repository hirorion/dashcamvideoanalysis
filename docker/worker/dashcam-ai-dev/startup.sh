#!/bin/bash

id $CUR_USER_NAME
if [ $? = 0 ]; then
    HOME=/home/$CUR_USER_NAME SHELL=/bin/bash su - $CUR_USER_NAME -c "launch_docker.sh $USER_DIR $MOVIE_PREFIX $MOVIE_FILENAME $CAMERA_TYPE $CAMERA_HEIGHT $START_FNO $END_FNO"
else
    echo "$CUR_USER_NAME was not found"
fi
