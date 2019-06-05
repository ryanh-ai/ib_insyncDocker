#!/bin/bash

service xvfb start
/usr/bin/socat TCP-LISTEN:4003,fork TCP:127.0.0.1:4001 &
/usr/local/bin/python /root/ibcStart_docker.py 
