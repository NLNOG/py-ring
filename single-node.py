#! /usr/bin/env python

from ringtools import *
res = RingNode('bit01').run_command('uptime')
print res.get_stdout()
