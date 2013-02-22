#! /usr/bin/env python

import sys

try:
    from ringtools import ring
except ImportError:
    # ringtools probaly isn't installed globally yet
    sys.path.append('..')
    from ringtools import ring


def callback(result):
    # callback to analyse the results: this function is called after running
    # the command on each hos. If the command exited ok we select the average 
    # pingtime from the result and add it to the dataset
    if result.get_exitcode() == 0 and len(result.get_stdout()) > 0:
        # add the value we grabbed from the output to the node's result
        result.add_value('dig', result.get_stdout()[-1])


# the command to be executed
COMMAND = "dig +short -t a www.facebook.com"

# pick random nodes
nodes = ring.pick_nodes(50)

# run the 'dig' command on the selected hosts with 'callback' as the analyse function
# using www.facebook.com as a target since it has many A labels
cmd_result = ring.run_command(COMMAND, nodes, analyse=callback)

# get the data for the 'dig' field grouped by value
grouped = cmd_result.get_value_grouped('dig', True)
print "results for '%s' grouped by return value:" % COMMAND
print " #  result            hosts"
for (value, hosts) in grouped:
    print "%2d: %-16s %s" % (len(hosts), value, ", ".join(hosts))
    
