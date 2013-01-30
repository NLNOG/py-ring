#! /usr/bin/env python

from ringtools import ring

# number of nodes in the ring
print "unique nodes: %d" % len(ring.get_ring_nodes())

# number of unique networks in the ring
print "unique networks: %d" % len(ring.get_ring_networks())

# number of unique countries in the ring
print "unique countries: %d" % len(ring.get_ring_countries())

# determine if a name is a node
print "bit01 is a ringnode: %s" % ring.is_ring_node('bit01')
print "bit02 is a ringnode: %s" % ring.is_ring_node('bit02')

# all nodes in France
print "all French nodes: %s" % ", ".join(ring.get_ring_nodes('fr'))

# get the country for node nautile01
print "country for nautile01: %s"  % ring.get_node_country('nautile01')
