#!/bin/sh

echo "This message goes to stderr" >&2
echo "This message goes to stdout" >&2

echo "arg1 = $1"
echo "arg2 = $2"
echo "arg3 = $3"