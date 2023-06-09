#!/bin/sh

DOCKER_SOCKET=/var/run/docker.sock

do_docker_socket() {
    if [ ! -e $DOCKER_SOCKET ]; then
        echo "Please mount the Docker socket to $DOCKER_SOCKET"
        exit 1
    fi

    # Get the host's docker group id
    echo "Getting the Docker socket group owner ... "
    export docker_group_id=$(stat -c "%g" $DOCKER_SOCKET)

    if [ ! -e "/var/run/docker.sock" ]; then
        echo "Please mount the Docker socket to /var/run/docker.sock"
        exit 1
    fi

    # Create the docker group in this container
    echo "Creating host_docker group with gid $docker_group_id ..."
    groupadd -fr -g $docker_group_id host_docker

    # Add the daemon user to the docker group
    # The host_docker group might not be created if there's already a group with
    # the id. In that case we just grep for the existing name, this should always
    # work.
    group=$(cat /etc/group | grep $docker_group_id | sed 's/:.*//')
    echo "Adding $USER to the $group group ..."
    usermod -aG $group $USER
}

echo "Checking if DOCKER_HOST is defined ..."

if [ "x${DOCKER_HOST}" = "x" ]; then
    echo "DOCKER_HOST is not defined, gonna use $DOCKER_SOCKET"
    do_docker_socket
else
    echo "DOCKER_HOST is defined."
fi

echo "Starting celery worker..."
exec celery worker \
            -A gitmate \
            --uid=$USER --gid=$USER \
            --loglevel=info \
            -Q celery,medium,long \
            --autoscale=$MAX,$MIN \
            $EXTRA_ARGUMENTS
