# Script to build and run kartograafr locally (e.g. a laptop).
# OpenShift builds will be a different process but, while the external
# environment is different the same dockerfile should run in both locations.
# (That's a bit asperational at the moment)

set -x
set -e

TAG=kart-dev-p3-esri

### Docker file
DOCKER_FILE=./Dockerfile

### For development remap storage from Docker to host storage.
HOST_CONFIG=${PWD}/configuration
CONTAINER_CONFIG=/usr/local/apps/kartograafr/configuration

HOST_LOG=${PWD}/tmp/log
CONTAINER_LOG=/var/log/kartograafr

HOST_SECRETS=$(pwd)/OPT/SECRETS
CONTAINER_SECRETS=/opt/secrets

## Construct volume mapping
V_CONFIG=" -v ${HOST_CONFIG}:${CONTAINER_CONFIG} "
V_LOG=" -v ${HOST_LOG}:${CONTAINER_LOG} "
V_SECRETS=" -v ${HOST_SECRETS}:${CONTAINER_SECRETS} "
####

docker build -f ${DOCKER_FILE} -t $TAG . \
    && docker run -it ${V_LOG} ${V_CONFIG} ${V_SECRETS} --rm --name ${TAG}-run ${TAG} 2>&1

echo "log directory: "
ls -l ${HOST_LOG}
#end
