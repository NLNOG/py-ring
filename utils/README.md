utils
=====

This directory contains utilities using the `ringtools` library.

ring-ping
---------
The `ring-ping` tool performs ping commands from a selection of ring nodes towards one specific destination and prints the results. Example:

    % ./ring-ping.py -c 10 ring.nlnog.net
    ring-ping v0.1 written by Teun Vink <teun@teun.tv>

    pinging ring.nlnog.net from 10 nodes:
    nforce01 (NL):                 7.07ms   
    is01 (NL):                     7.86ms   
    coloclue01 (NL):               8.46ms   
    jump01 (GB):                  14.31ms   
    obenetwork01 (SE):            26.07ms   
    indit01 (SE):                 26.50ms   
    dataoppdrag01 (NO):           38.83ms   
    backbone02 (IS):              51.61ms   
    merit01 (US):                121.97ms   
    dcsone01 (SG):               279.77ms   

    10 nodes ok (58.25ms avg), 0 nodes failed to ping, 0 nodes failed to connect.

Using commandline arguments specific hosts, networks or countries can be included, excluded or required. This example pings from 3 hosts at most including at least one in the Netherlands (`-o nl`) and at least one in the Atrato network (`-w atrato`):

    % ./ring-ping.py -c 3 -o nl -w atrato ring.nlnog.net
    ring-ping v0.1 written by Teun Vink <teun@teun.tv>

    pinging ring.nlnog.net from 3 nodes:
    totaalnet01 (NL):             28.86ms   
    atrato02 (US):                83.27ms   
    bigwells01 (US):             120.19ms 

Forcing all nodes to be in Japan (`-oo jp`) and using IPv6 (`-6`):

    % ./ring-ping.py -6 -oo jp ring.nlnog.net
    ring-ping v0.1 written by Teun Vink <teun@teun.tv>

    pinging ring.nlnog.net from 2 nodes:
    iij01 (JP):                  260.38ms   
    amazon04 (JP):               268.55ms   

2 nodes ok (264.47ms avg), 0 nodes failed to ping, 0 nodes failed to connect.

The quiet version (`-q`):

    % ./ring-ping.py -q ring.nlnog.net
    196 nodes ok (69.41ms avg), 9 nodes failed to ping, 2 nodes failed to connect.

Information about the nodes failing to ping can be printed using the `-e` flag. In this example we pick some nodes with known problems using the `-n` flag:

    % ./ring-ping.py -e -c 4 -n occaid01,xlshosting01,infomaniak01,bluezonejordan01 8.8.8.8
    ring-ping v0.1 written by Teun Vink <teun@teun.tv>

    pinging 8.8.8.8 from 4 nodes:

    connection failures:
    infomaniak01 (CH):           '[Errno 111] Connection refused'
    xlshosting01 (NL):           'timed out'
    bluezonejordan01 (JO):       '[Errno 113] No route to host'

    command execution problems:
    occaid01 (US):               exitcode = 2, message: connect: Network is unreachable

    0 nodes ok (0.00ms avg), 1 nodes failed to ping, 3 nodes failed to connect.
