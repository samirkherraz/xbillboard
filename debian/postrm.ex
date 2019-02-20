#!/bin/bash


echo "####  Removing auto-generated files"

rm -rvf $(find /home -type d -name  ".xbillboard")
