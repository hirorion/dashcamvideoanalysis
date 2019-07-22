#!/usr/bin/env bash
#
# Do object tracking and speed estimation based on object recognition results and JSON data
#
# tracking.sh CUR_USER_NAME USER_DIR MOVIE_PREFIX MOVIE_FILENAME CAMERA_TYPE CAMERA_HEIGHT START_FNO END_FNO BUILD_DIR CONTAINER_NAMES
#
# docker run --rm -e CUR_USER_NAME=%s -e USER_DIR=\"%s\" -e MOVIE_PREFIX=\"%s\" -e MOVIE_FILENAME=\"%s\" -e CAMERA_TYPE=\"%s\" -e CAMERA_HEIGHT=\"%s\" -e START_FNO=%d -e END_FNO=%d -v \"%s\":/mnt/ --runtime=nvidia %s"
#    cmd = cmd % (
#        DOCKER_USER,
#        user_dir,
#        input_movie_prefix,
#        input_movie_filename,
#        parameters_json['camera_type'],
#        parameters_json['camera_height'],
#        parameters_json['start_fno'],
#        parameters_json['end_fno'],
#        BUILD_DIR,
#        CONTAINER_NAMES
#

# 自分が死んだ後、子プロセスも殺す
trap 'kill -TERM $(jobs -p) >/dev/null 2>&1' EXIT

echo "sudo docker run --rm -e CUR_USER_NAME=$1 -e USER_DIR=\"$2\" -e MOVIE_PREFIX=\"$3\" -e MOVIE_FILENAME=\"$4\" -e CAMERA_TYPE=\"$5\" -e CAMERA_HEIGHT=\"$6\" -e START_FNO=$7 -e END_FNO=$8 -v $9:/mnt/ --runtime=nvidia ${10}"
sudo docker run --rm -e CUR_USER_NAME=$1 -e USER_DIR="$2" -e MOVIE_PREFIX="$3" -e MOVIE_FILENAME="$4" -e CAMERA_TYPE="$5" -e CAMERA_HEIGHT="$6" -e START_FNO=$7 -e END_FNO=$8 -v $9:/mnt/ --runtime=nvidia ${10}
