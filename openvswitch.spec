%global _hardened_build 1

# Uncomment these for snapshot releases:
# snapshot is the date YYYYMMDD of the snapshot
# snap_git is the 8 git sha digits of the last commit
# You must edit configure.ac and downgrade the version from
# the development one to the stable one to not confuse RPM
# during future upgrades.
# Steps:
# 1. Checkout the git branch
# 2. Change version in configure.ac to be <stable version>-git<8sha>
# 3. Run: ./boot.sh
# 4. Run: ./configure.sh
# 5. Run: make dist
%define snapshot .git20150113
%define snap_gitsha -git3282e51

# If wants to run tests while building, specify the '--with check'
# option. For example:
# rpmbuild -bb --with check openvswitch.spec

Name: openvswitch
Version: 2.3.1
Release: 2%{?snapshot}%{?dist}
Summary: Open vSwitch daemon/database/utilities

# Nearly all of openvswitch is ASL 2.0.  The bugtool is LGPLv2+, and the
# lib/sflow*.[ch] files are SISSL
# datapath/ is GPLv2 (although not built into any of the binary packages)
# python/compat is Python (although not built into any of the binary packages)
License: ASL 2.0 and LGPLv2+ and SISSL
URL: http://openvswitch.org
Source0: http://openvswitch.org/releases/%{name}-%{version}%{?snap_gitsha}.tar.gz

ExcludeArch: ppc

BuildRequires: autoconf
BuildRequires: systemd-units openssl openssl-devel
BuildRequires: python python-twisted-core python-zope-interface PyQt4
BuildRequires: desktop-file-utils
BuildRequires: groff graphviz

Requires: openssl iproute module-init-tools
#Upstream kernel commit 4f647e0a3c37b8d5086214128614a136064110c3
Requires: kernel >= 3.15.0-0

Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Obsoletes: openvswitch-controller <= 0:2.1.0-1

%bcond_with check

%description
Open vSwitch provides standard network bridging functions and
support for the OpenFlow protocol for remote per-flow control of
traffic.

%package -n python-openvswitch
Summary: Open vSwitch python bindings
License: ASL 2.0
BuildArch: noarch
Requires: python

%description -n python-openvswitch
Python bindings for the Open vSwitch database

%package test
Summary: Open vSwitch testing utilities
License: ASL 2.0
BuildArch: noarch
Requires: python-openvswitch = %{version}-%{release}
Requires: python python-twisted-core python-twisted-web

%description test
Utilities that are useful to diagnose performance and connectivity
issues in Open vSwitch setup.

%package devel
Summary: Open vSwitch OpenFlow development package (library, headers)
License: ASL 2.0
Provides: openvswitch-static = %{version}-%{release}

%description devel
This provides static library, libopenswitch.a and the openvswitch header
files needed to build an external application.


%prep
%setup -q -n %{name}-%{version}%{?snap_gitsha}

%build
%configure --enable-ssl --with-pkidir=%{_sharedstatedir}/openvswitch/pki
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch

install -p -D -m 0644 \
        rhel/usr_share_openvswitch_scripts_systemd_sysconfig.template \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/openvswitch
install -p -D -m 0644 \
        rhel/usr_lib_systemd_system_openvswitch.service \
        $RPM_BUILD_ROOT%{_unitdir}/openvswitch.service
install -p -D -m 0644 \
        rhel/usr_lib_systemd_system_openvswitch-nonetwork.service \
        $RPM_BUILD_ROOT%{_unitdir}/openvswitch-nonetwork.service

install -m 0755 rhel/etc_init.d_openvswitch \
        $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/openvswitch.init

install -p -D -m 0644 rhel/etc_logrotate.d_openvswitch \
        $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/openvswitch

install -m 0644 vswitchd/vswitch.ovsschema \
        $RPM_BUILD_ROOT/%{_datadir}/openvswitch/vswitch.ovsschema

install -d -m 0755 $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifdown-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifup-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs

install -d -m 0755 $RPM_BUILD_ROOT%{python_sitelib}
mv $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/* \
   $RPM_BUILD_ROOT%{python_sitelib}
rmdir $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/

install -d -m 0755 $RPM_BUILD_ROOT/%{_sharedstatedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openvswitch
install -p -D -m 0644 include/openvswitch/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch
install -p -D -m 0644 config.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openvswitch/lib
install -p -D -m 0644 lib/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch/lib

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openflow
install -p -D -m 0644 include/openflow/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openflow

touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/conf.db
touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/system-id.conf

%check
%if %{with check}
    if make check TESTSUITEFLAGS='%{_smp_mflags}' ||
       make check TESTSUITEFLAGS='--recheck'; then :;
    else
        cat tests/testsuite.log
        exit 1
    fi
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%preun
%if 0%{?systemd_preun:1}
    %systemd_preun %{name}.service
%else
    if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
        /bin/systemctl --no-reload disable %{name}.service >/dev/null 2>&1 || :
        /bin/systemctl stop %{name}.service >/dev/null 2>&1 || :
    fi
%endif


%post
%if 0%{?systemd_post:1}
    %systemd_post %{name}.service
%else
    # Package install, not upgrade
    if [ $1 -eq 1 ]; then
        /bin/systemctl daemon-reload >dev/null || :
    fi
%endif

# Package with native systemd unit file is installed for the first time
%triggerun -- %{name} < 1.9.0-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply openvswitch
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save %{name} >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del %{name} >/dev/null 2>&1 || :
/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :

%postun
%if 0%{?systemd_postun_with_restart:1}
    %systemd_postun_with_restart %{name}.service
%else
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
    if [ "$1" -ge "1" ] ; then
    # Package upgrade, not uninstall
        /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
    fi
%endif


%files -n python-openvswitch
%{python_sitelib}/ovs
%doc COPYING

%files test
%{_bindir}/ovs-test
%{_bindir}/ovs-vlan-test
%{_bindir}/ovs-l3ping
%{_mandir}/man8/ovs-test.8*
%{_mandir}/man8/ovs-vlan-test.8*
%{_mandir}/man8/ovs-l3ping.8*
%{python_sitelib}/ovstest

%files devel
%{_libdir}/*.a
%{_libdir}/*.la
%{_includedir}/openvswitch/*
%{_includedir}/openflow/*

%files
%defattr(-,root,root)
%dir %{_sysconfdir}/openvswitch
%config %ghost %{_sysconfdir}/openvswitch/conf.db
%config %ghost %{_sysconfdir}/openvswitch/system-id.conf
%config(noreplace) %{_sysconfdir}/sysconfig/openvswitch
%config(noreplace) %{_sysconfdir}/logrotate.d/openvswitch
%{_unitdir}/openvswitch.service
%{_unitdir}/openvswitch-nonetwork.service
%{_datadir}/openvswitch/scripts/openvswitch.init
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%{_datadir}/openvswitch/bugtool-plugins/
%{_datadir}/openvswitch/scripts/ovs-bugtool-*
%{_datadir}/openvswitch/scripts/ovs-check-dead-ifs
%{_datadir}/openvswitch/scripts/ovs-lib
%{_datadir}/openvswitch/scripts/ovs-vtep
%{_datadir}/openvswitch/scripts/ovs-ctl
%config %{_datadir}/openvswitch/vswitch.ovsschema
%config %{_datadir}/openvswitch/vtep.ovsschema
%{_bindir}/ovs-appctl
#%{_bindir}/ovs-docker
%{_bindir}/ovs-dpctl
%{_bindir}/ovs-dpctl-top
%{_bindir}/ovs-ofctl
%{_bindir}/ovs-vsctl
%{_bindir}/ovsdb-client
%{_bindir}/ovsdb-tool
#%{_bindir}/ovs-testcontroller
%{_bindir}/ovs-pki
%{_bindir}/vtep-ctl
%{_sbindir}/ovs-bugtool
%{_sbindir}/ovs-vswitchd
%{_sbindir}/ovsdb-server
%{_mandir}/man1/ovs-benchmark.1*
%{_mandir}/man1/ovs-pcap.1*
%{_mandir}/man1/ovs-tcpundump.1*
%{_mandir}/man1/ovsdb-client.1*
%{_mandir}/man1/ovsdb-server.1*
%{_mandir}/man1/ovsdb-tool.1*
%{_mandir}/man5/ovs-vswitchd.conf.db.5*
%{_mandir}/man5/vtep.5*
%{_mandir}/man8/vtep-ctl.8*
%{_mandir}/man8/ovs-appctl.8*
%{_mandir}/man8/ovs-bugtool.8*
%{_mandir}/man8/ovs-ctl.8*
%{_mandir}/man8/ovs-dpctl.8*
%{_mandir}/man8/ovs-dpctl-top.8*
%{_mandir}/man8/ovs-ofctl.8*
%{_mandir}/man8/ovs-pki.8*
%{_mandir}/man8/ovs-vsctl.8*
%{_mandir}/man8/ovs-vswitchd.8*
%{_mandir}/man8/ovs-parse-backtrace.8*
#%{_mandir}/man8/ovs-testcontroller.8*
%doc COPYING DESIGN INSTALL.SSL NOTICE README WHY-OVS
%doc FAQ NEWS INSTALL.DPDK rhel/README.RHEL
/var/lib/openvswitch
/var/log/openvswitch
%exclude %{_bindir}/ovs-benchmark
%exclude %{_bindir}/ovs-parse-backtrace
%exclude %{_bindir}/ovs-pcap
%exclude %{_bindir}/ovs-tcpundump
%exclude %{_sbindir}/ovs-vlan-bug-workaround
%exclude %{_mandir}/man1/ovs-benchmark.1.gz
%exclude %{_mandir}/man1/ovs-pcap.1.gz
%exclude %{_mandir}/man1/ovs-tcpundump.1.gz
%exclude %{_mandir}/man8/ovs-vlan-bug-workaround.8.gz
%exclude %{_datadir}/openvswitch/scripts/ovs-save

%changelog
* Wed Jan 14 2015 Flavio Leitner - 2.3.1-2.git20150113
- updated to 2.3.1-git3282e51

* Fri Dec 05 2014 Flavio Leitner - 2.3.1-1
- updated to 2.3.1

* Fri Nov 07 2014 Flavio Leitner - 2.3.0-3.git20141107
- updated to 2.3.0-git39ebb203

* Thu Oct 23 2014 Flavio Leitner - 2.3.0-2
- fixed to own conf.db and system-id.conf in /etc/openvswitch.
  (#1132707)

* Tue Aug 19 2014 Flavio Leitner - 2.3.0-1
- updated to 2.3.0

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jun 12 2014 Flavio Leitner - 2.1.2-4
- moved README.RHEL to be in the standard doc dir.
- added FAQ and NEWS files to the doc list.
- excluded PPC arch

* Thu Jun 12 2014 Flavio Leitner - 2.1.2-3
- removed ovsdbmonitor packaging

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Mar 25 2014 Flavio Leitner - 2.1.2-1
- updated to 2.1.2

* Tue Mar 25 2014 Flavio Leitner - 2.1.0-1
- updated to 2.1.0
- obsoleted openvswitch-controller package
- requires kernel 3.15.0-0 or newer
  (kernel commit 4f647e0a3c37b8d5086214128614a136064110c3
   openvswitch: fix a possible deadlock and lockdep warning)
- ovs-lib: allow non-root users to check service status
  (upstream commit 691e47554dd03dd6492e00bab5bd6d215f5cbd4f)
- rhel: Add Patch Port support to initscripts
  (upstream commit e2bcc8ef49f5e51f48983b87ab1010f0f9ab1454)

* Mon Jan 27 2014 Flavio Leitner - 2.0.1-1
- updated to 2.0.1

* Mon Jan 27 2014 Flavio Leitner - 2.0.0-6
- create a -devel package
  (from Chris Wright <chrisw@redhat.com>)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-5
- Enable DHCP support for internal ports
  (upstream commit 490db96efaf89c63656b192d5ca287b0908a6c77)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-4
- disabled ovsdbmonitor packaging
  (upstream has removed the component)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-3
- fedora package: fix systemd ordering and deps.
  (upstream commit b49c106ef00438b1c59876dad90d00e8d6e7b627)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-2
- util: use gcc builtins to better check array sizes
  (upstream commit 878f1972909b33f27b32ad2ded208eb465b98a9b)

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 2.0.0-1
- updated to 2.0.0 (#1023184)

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-8
- applied upstream commit 7b75828bf5654c494a53fa57be90713c625085e2
  rhel: Option to create tunnel through ifcfg scripts.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-7
- applied upstream commit 32aa46891af5e173144d672e15fec7c305f9a4f3
  rhel: Set STP of a bridge during bridge creation.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-6
- applied upstream commit 5b56f96aaad4a55a26576e0610fb49bde448dabe
  rhel: Prevent duplicate ifup calls.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-5
- applied upstream commit 79416011612541d103a1d396d888bb8c84eb1da4
  rhel: Return an exit value of 0 for ifup-ovs.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-4
- applied upstream commit 2517bad92eec7e5625bc8b248db22fdeaa5fcde9
  Added RHEL ovs-ifup STP option handling

* Tue Oct 1 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-3
- don't use /var/lock/subsys with systemd (#1006412)

* Thu Sep 19 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-2
- ovsdbmonitor package is optional

* Thu Aug 29 2013 Thomas Graf <tgraf@redhat.com> - 1.11.0-1
- Update to 1.11.0

* Tue Aug 13 2013 Flavio Leitner <fbl@redhat.com> - 1.10.0-7
- Fixed openvswitch-nonetwork to start openvswitch.service (#996804)

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 1.10.0-6
- Perl 5.18 rebuild

* Tue Jul 23 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-5
- Typo

* Tue Jul 23 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-4
- Spec file fixes
- Maintain local copy of sysconfig.template

* Thu Jul 18 2013 Petr Pisar <ppisar@redhat.com> - 1.10.0-3
- Perl 5.18 rebuild

* Mon Jul 01 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-2
- Enable PIE (#955181)
- Provide native systemd unit files (#818754)

* Thu May 02 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-1
- Update to 1.10.0 (#958814)

* Thu Feb 28 2013 Thomas Graf <tgraf@redhat.com> - 1.9.0-1
- Update to 1.9.0 (#916537)

* Tue Feb 12 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-8
- Fix systemd service dependency loop (#818754)

* Fri Jan 25 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-7
- Auto-start openvswitch service on ifup/ifdown (#818754)
- Add OVSREQUIRES to allow defining OpenFlow interface dependencies

* Thu Jan 24 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-6
- Update to Open vSwitch 1.7.3

* Tue Nov 20 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-6
- Increase max fd limit to support 256 bridges (#873072)

* Thu Nov  1 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-5
- Don't create world writable pki/*/incomming directory (#845351)

* Thu Oct 25 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-4
- Don't add iptables accept rule for -p GRE as GRE tunneling is unsupported

* Tue Oct 16 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-3
- require systemd instead of systemd-units to use macro helpers (#850258)

* Tue Oct  9 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-2
- make ovs-vsctl timeout if daemon is not running (#858722)

* Mon Sep 10 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1.-1
- Update to 1.7.1

* Fri Sep  7 2012 Thomas Graf <tgraf@redhat.com> - 1.7.0.-3
- add controller package containing ovs-controller

* Thu Aug 23 2012 Tomas Hozza <thozza@redhat.com> - 1.7.0-2
- fixed SPEC file so it comply with new systemd-rpm macros guidelines (#850258)

* Fri Aug 17 2012 Tomas Hozza <thozza@redhat.com> - 1.7.0-1
- Update to 1.7.0
- Fixed openvswitch-configure-ovskmod-var-autoconfd.patch because
  openvswitch kernel module name changed in 1.7.0
- Removed Source8: ovsdbmonitor-move-to-its-own-data-directory.patch
- Patches merged:
  - ovsdbmonitor-move-to-its-own-data-directory-automaked.patch
  - openvswitch-rhel-initscripts-resync.patch

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Mar 15 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-5
- fix ovs network initscripts DHCP address acquisition (#803843)

* Tue Mar  6 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-4
- make BuildRequires openssl explicit (needed on f18/rawhide now)

* Tue Mar  6 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-3
- use glob to catch compressed manpages

* Thu Mar  1 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-2
- Update License comment, use consitent macros as per review comments bz799171

* Wed Feb 29 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-1
- Initial package for Fedora
