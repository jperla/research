#!/usr/bin/python
import simplejson
import sys
input = sys.stdin.read()
sys.stdout.write(simplejson.dumps(simplejson.loads(input)))
