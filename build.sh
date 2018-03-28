#!/bin/bash

VERSION=$(expr $(<./VERSION) + 1)
BUILD_DIR="/tmp/Xbillboad/build-$VERSION"
PACKAGE="/tmp/Xbillboad/build-$VERSION.deb"

echo "### PREPARING BUILD DIR "

mkdir -p $BUILD_DIR
cp -r ./DEBIAN $BUILD_DIR
cp -r ./etc $BUILD_DIR
cp -r ./usr $BUILD_DIR
cp -r ./LICENSE $BUILD_DIR
cp -r ./README.md $BUILD_DIR


sed "s/Version:.*/Version:$VERSION/g" $BUILD_DIR/DEBIAN/control >&2

echo $VERSION > ./VERSION

echo "### BUILDING "


rm -vf ./dist/* 
dpkg -b $BUILD_DIR

echo "### CLEAN UP "

cp $PACKAGE ./dist/
rm -rvf $BUILD_DIR
