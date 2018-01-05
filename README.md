This repository provides all the support code required to deploy a "Developer
Ceph Storage" and "A Customer Demo".

# Ceph packages

The Ceph packages are from the default repository of the Linux distribution you use. 
Because the Ceph packages are added by the majority of Linux distribution provider.

In case that some distributions do not add ceph packages, you may add the ceph repository 
from the ceph community or its mirrors according to below link.

http://docs.ceph.com/docs/master/install/get-packages/

And of course you may build your own Ceph packages and create and add your own repository.

# Reference Architecture

It can be eithier a cluster of virtual machines for your development purpose or a group of 
phisical nodes for deploying a customer demo.

# Pre-requisites


1. All the servers are supposed to have CentOS or Debian installed and they are supposed to
have networking configured in a way that they can see/resolve each other's names.

1. The nodes that will be used as Ceph OSDs need to have at least one extra harddrive for Ceph.

1. The Ceph OSD node should have 2 NICs connected. One is used for public network and 
the other is used for private network (cluster network).

# Configuration

Some example configuration files are provided in this repo as example, go through them and
generate the equivalent ones for your particular deployment:

    hosts.example
    site.yml.example
    deployment-vars.example


Ensure to use host names, instead of ips to avoid some known deployment issues.

The playbook provide 2 deployment cases. Below take a cluster of virtual machines as an example.

# The deployment

1) Monitors are deployed and the cluster bootstrapmd:


       ansible-playbook -K -v -i ./virtual_machine/hosts ./site-virtual-machine.yml --tags ceph-mon

Check that the cluster is up and running by connecting to one of the monitors
and checking:

    ssh vm-a
    ceph daemon mon.vm-a mon_status

2) OSDs assume a full hard drive is dedicated to Ceph at least. A default
configuration if all the servers that will be OSDs have the same HD layout
can be spedified in virtual_machine/deployment-vars as follows:

```
ceph_host_osds:
  - vdb
  - vdc
  - vdd
```

If some server has a different configuration, this will be specified in the
hostvars folder, in a file with the name of your server. For example:

```
$ cat virtual_machine/host_vars/vm-b

ceph_host_osds:
  - vdb
  - vdc
```

After configuring, the OSDs are deployed as follows:

    ansible-playbook -K -v -i ./virtual_machine/hosts ./site-virtual-machine.yml --tags ceph-osd

2.1) In the case of setting up a cluster from scratch where ceph has been installed
previously, there is an option to force the resetting of all the disks (this
option WILL DELETE all the data on the OSDs). This option is not
idempotent, use at your own risk. It is safe to use if you have cleanly deployed
the machine and the disk to be used as OSD had a previously installed Ceph:

    --extra-vars 'ceph_force_prepare=true'

3) deploy ceph-radosgw

    ansible-playbook -K -v -i ./virtual_machine/hosts ./site-virtual-machine.yml --tags ceph-radosgw
