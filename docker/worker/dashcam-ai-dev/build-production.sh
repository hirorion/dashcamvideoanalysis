# for production build
# for development build
# APP_USER_ID is host user id for map to docker. it must be set.
# APP_GROUP_ID is host group id for map to docker. it must be set.
# APP_USER_NAME is host user accout name for map to docker. it must be set.
docker build --build-arg APP_USER_ID=1000 --build-arg APP_USER_NAME=mitsui --build-arg APP_GROUP_ID=1000 --no-cache --target=production -t "dashcam/ai:1.0" .
