#!/bin/bash


echo "####  Removing auto-generated files"

rm -rvf $(find /home -type d -name  ".xbillboard")

for File in $(find /home -type f -name  ".Xsession")
do
    if [[ 'grep "XBILLBOARD AUTO GENERATED XSESSION" $File' ]];then
        rm -vf $File
    fi
done