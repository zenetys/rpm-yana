#!/bin/bash -xe

if [[ $DIST == el8 ]]; then
    dnf module enable -y nodejs:16
fi

build_dl "https://dl.fedoraproject.org/pub/epel/epel-release-latest-$DIST_VERSION.noarch.rpm"
rpm -Uvh "$CACHEDIR/epel-release-latest-$DIST_VERSION.noarch.rpm"
