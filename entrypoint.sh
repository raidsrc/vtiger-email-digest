#!/bin/sh -l

echo "Hello $1"
time=$(date)
echo "time is $time" >> $GITHUB_OUTPUT

