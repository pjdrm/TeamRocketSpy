#!/bin/bash

cmd=$1
seconds=$2

while true
do
echo "Executing: ${cmd} for $seconds seconds"
$cmd&

cmdpid=$!
sleep $seconds

if [ -d /proc/$cmdpid ]
then
  echo "terminating program PID:$cmdpid"
  kill $cmdpid
fi
sleep 10
done
