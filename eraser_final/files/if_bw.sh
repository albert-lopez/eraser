#!/bin/sh	
while :
do
	tx=$(cat /sys/class/net/$1/statistics/tx_bytes)
	rx=$(cat /sys/class/net/$1/statistics/rx_bytes)
	tx_droped=$(cat /sys/class/net/$1/statistics/tx_dropped)
	rx_droped=$(cat /sys/class/net/$1/statistics/rx_dropped)
	echo "$tx:$rx:$tx_droped:$rx_droped"
	sleep 1
done
