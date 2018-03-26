#!/bin/bash 

if [ ! -d $HOME/.xbillboard  ]; then
    mkdir $HOME/.xbillboard 
fi

if [ ! -f $HOME/.Xsession  ]; then
    cp /etc/xbillboard/xsession-default $HOME/.Xsession
fi

if [ ! -f $HOME/.xbillboard/xbillboard.conf  ]; then
    cp /etc/xbillboard/xbillboard.conf $HOME/.xbillboard/xbillboard.conf
fi

if [ ! -d $HOME/.xbillboard/screens ]; then
    mkdir $HOME/.xbillboard/screens
fi

