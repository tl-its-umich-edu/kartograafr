# Script to build and run kartograafr locally (e.g. a laptop).
# OpenShift builds will be a different process but, while the external
# environment is different the same dockerfile should run in both locations.
# (That's a bit asperational at the moment)

set -x
set -e

TAG=kart-dev

### For development remap storage from Docker to host storage.
HOST_CONFIG=${PWD}/configuration
HOST_LOG=${PWD}/tmp/log

CONTAINER_CONFIG=/usr/local/apps/kartograafr/configuration
CONTAINER_LOG=/var/log/kartograafr

## Construct volume mapping
V_CONFIG=" -v ${HOST_CONFIG}:${CONTAINER_CONFIG} "
V_LOG=" -v ${HOST_LOG}:${CONTAINER_LOG} "
####

docker build -t $TAG . \
    && docker run -it ${V_LOG} ${V_CONFIG} --rm --name ${TAG}-run ${TAG}

echo "log directory: "
ls -l ${HOST_LOG}
#end
