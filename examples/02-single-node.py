#! /usr/bin/env python

# examples/single-node.py
#
# run a command on a single ringnode. Verify if the SSH connection was ok
# and if so if the command excuted properly. Print the result if it did,
# print the stderr output if it didn't.


import sys

try:
    from ringtools.node import RingNode
    from ringtools.result import NodeResult
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools.node import RingNode
    from ringtools.result import NodeResult

res = RingNode('bit01').run_command('uptime')
if res.get_ssh_result() != NodeResult.SSH_OK:
    print "Failed to execute the SSH command."
    print "Error message: %s" % res.get_ssh_errormsg()
    sys.exit()

if res.get_exitcode() != 0:
    print "Non-zero exitcode for the command: %d" % res.get_exitcode()
    print "Output of stderr:"
    print "\n".join(res.get_stderr())
    sys.exit()

print "Command executed ok. Here's the output:"
print "\n".join(res.get_stdout())
