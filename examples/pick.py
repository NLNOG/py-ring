#! /usr/bin/env python

# examples/pick.py
#
# show/test some uses of the pick_nodes() 

import sys

try:
    from ringtools import ring
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools import ring


# let's pick nodes
print "5 nodes: %s " % ring.pick_nodes(5) 
print "5 nodes, including bit01: %s" % ring.pick_nodes(5, inc_hosts="bit01") 
print "5 nodes, including one from amazon: %s" % ring.pick_nodes(5, inc_networks="amazon") 
print "5 nodes, including one in france: %s" % ring.pick_nodes(5, inc_countries="fr") 
print "5 nodes, all ipv6 only: %s " % ring.pick_nodes(5, support_ipv6_only=True) 
print "5 nodes, don't care about IPv6: %s " % ring.pick_nodes(5, support_ipv6_only=False) 
print "5 nodes, all dual stack: %s " % ring.pick_nodes(5, support_ipv4=True)
print "5 nodes, no IPv4 support: %s " % ring.pick_nodes(5, support_ipv4=False)
print "5 nodes, ipv6 only + dual stack: %s " % ring.pick_nodes(5, support_ipv4=True, support_ipv6_only=True)

