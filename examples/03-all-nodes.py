#! /usr/bin/env python

# examples/03-single-node.py
#
# run a command on a single ringnode. Verify if the SSH connection was ok
# and if so if the command excuted properly. Print the result if it did,
# print the stderr output if it didn't.

import sys

try:
    from ringtools import ring
    from ringtools.node import RingNode
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools import ring
    from ringtools.node import RingNode

hosts = ring.get_ring_nodes()
result = ring.run_command('uptime', hosts)
print "succesful results:"
for res in result.get_successful_results().get_results():
    print "  %25s: %s" % (res.get_hostname(), '\n'.join(res.get_stdout()))
print "command failed:"
for res in result.get_failed_results(False).get_results():
    print "  %25s: %s" % (res.get_hostname(), '\n'.join(res.get_stderr()))

print "connection problems:"
for res in result.get_failed_results(True, True).get_results():
    print "  %25s: %s" % (res.get_hostname(), repr(res.get_ssh_errormsg()))

