#docker build -t kart-dev . && docker run -it --rm --name kart-dev-run kart-dev
set -x
set -e

TAG=kart-dev

### For development remap storage from Docker to host storage.
HOST_CONFIG=${PWD}/configuration
HOST_LOG=${PWD}/tmp/log

CONTAINER_CONFIG=/usr/local/apps/kartograafer/configuration
CONTAINER_LOG=/var/log/kartograafr

## Construct mapping text.
V_CONFIG=" -v ${HOST_CONFIG}:${CONTAINER_CONFIG} "
V_LOG=" -v ${HOST_LOG}:${CONTAINER_LOG} "
####

#NET=

docker build -t $TAG . \
    && docker run -it ${NET} ${V_LOG} ${V_CONFIG} --rm --name ${TAG}-run ${TAG}
#end
