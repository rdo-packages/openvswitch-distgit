#!/bin/bash
#
# This script is only used to create snapshot tarball from the git tree.
#

echo "Warning: for unreleased code, the original version might be
the unreleased next one.  In that case, downgrade to the previous
released version so that we have: stable + fixes."
basever="2.4.0"

echo "Using version ${basever} while the code has"
grep "bugs@openvswitch.org" configure.ac

snap_gitsha=`git log --pretty=oneline -n1|cut -c1-8`
prefix=openvswitch-${basever}-git${snap_gitsha}
archive=${prefix}.tar.gz

echo "Creating ${archive}"
git archive --prefix=${prefix}/ HEAD  | gzip -9 > ${archive}
