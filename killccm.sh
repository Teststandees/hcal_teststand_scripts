#!/bin/bash
pids="$(pgrep -u `whoami` ngccm)"
for pid in $pids
do
t="$(ps -p $pid -o etime=)"
t="$(echo $t | tr '-' ':' | awk -F: '{ total=0; m=1; } { for (i=0; i < NF; i++) {total += $(NF-i)*m; m *= i >= 2 ? 24 : 60 }} {print total}')"
if [ "$t" -gt 18000 ]
then
kill -9 $pid &> /dev/null
#echo $pid: $t '->' Kill
#else
#echo $pid: $t '->' Mercy
fi
done
