#! /usr/bin/env python

import sys

try:
    from ringtools import ring, result
except ImportError:
    # ringtools probaly isn't installed globally yet
    sys.path.append('..')
    from ringtools import ring, result


def callback(result):
    # callback to analyse the results: this function is called after running
    # the command on each hos. If the command exited ok we select the average 
    # pingtime from the result and add it to the dataset
    if result.get_exitcode() == 0:
        # quick 'n dirty ;-)
        avg = result.get_stdout()[-1].split(" ")[3].split("/")[1]
        # add the value we grabbed from the output to the node's result
        result.add_value("avg", float(avg))


# pick 10 random nodes
nodes = ring.pick_nodes(count=10)
print "picked nodes: %s" % ", ".join(nodes)

# run the ping command on the selected hosts with 'callback' as the analyse function
cmd_result = ring.run_command('ping -c1 -q ring.nlnog.net', nodes, analyse=callback)

# get the succesful and failed results
s_res = cmd_result.get_successful_results()
f_res = cmd_result.get_failed_results()

# print the number and names of succesful and failed hosts
print "results: %d nodes ok (%s), %d nodes failed (%s)." % (
    len(s_res.get_results()), ", ".join(s_res.get_hostnames()), 
    len(f_res.get_results()), ", ".join(f_res.get_hostnames()))

# get a resultset sorted by 'avg' values and print the values
sort = s_res.get_value_sorted("avg")
print "results fastest to slowest:"
for (host, val) in sort:
    print "%s: %.3fms" % (host, val)

print "\nmedian: %s (%.2fms)" % (sort[len(sort)/2])
# use NodeResultSet's get_value_avg to calculate the average
print "average: %.2fms\n" % s_res.get_value_avg("avg")

# let's tell something about the nodes which failed as well
if len(f_res.get_results()) > 0:
    print "failures:"
    for r in f_res.get_results():
        # SSH connect failed
        if r.get_ssh_result() != result.NodeResult.SSH_OK:
            print "%s: %s" % (r.get_hostname(), r.get_ssh_errormsg())
        # SSH connect was ok, exitcode for the command was non-zero.
        # so print the exitcode and the output of stderr
        elif r.get_exitcode() != 0:
            print "%s: exitcode = %s, message = %s" % (r.get_hostname(), r.get_exitcode(), r.get_stderr())
