Name:		ksc
Version:	0.11.0
Release:	1%{?dist}
Summary:	Kernel source code checker
Group:		Development/Tools
AutoReqProv:	no
License:	GPLv2+
URL:		http://www.redhat.com/
Source0:	ksc-%{version}.tar.gz
BuildArch:	noarch
Requires:	python
Requires:	python-pycurl
Requires:	kernel-abi-whitelists
Requires:	binutils
Requires:	kernel-devel
Requires:	python-magic
Requires:	python-requests
BuildRequires:	python
BuildRequires:	python-setuptools

%description
A kernel module source code checker to find usage of non whitelist symbols

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root %{buildroot}
install -D ksc.1 %{buildroot}%{_mandir}/man1/ksc.1

%files
%doc README COPYING PKG-INFO
%{_bindir}/ksc
%{_datadir}/ksc
%{_mandir}/man1/ksc.*
%config(noreplace) %{_sysconfdir}/ksc.conf
%{python_sitelib}/ksc-%{version}*.egg-info

%changelog
* Wed Jan 2 2019 Čestmír Kalina <ckalina@redhat.com> - 0.11.0-1
- Resolves: rhbz#1657406 - Backport RHEL8 ksc bugfixes into RHEL7

* Fri Sep 7 2018 Cestmir Kalina <ckalina@redhat.com> - 0.10.0-1
- Resolves: #1623320

* Wed Dec 13 2017 Martin Lacko <mlacko@redhat.com> - 0.9.22-1
- Resolves: #1524779

* Tue Dec 5 2017 Martin Lacko <mlacko@redhat.com> - 0.9.21-1
- Resolves: #1520224

* Tue Nov 28 2017 Martin Lacko <mlacko@redhat.com> - 0.9.20-1
- Resolves: #1502930

* Tue Nov 7 2017 Stanislav Kozina <skozina@redhat.com> - 0.9.19-1
- Resolves: #1432864
- Resolves: #1500383
- Resolves: #1502930
- Resolves: #1503526
- Resolves: #1503603
- Resolves: #1503964
- Resolves: #1499249
- Resolves: #1441455
- Resolves: #1481310
- Resolves: #1456140

* Mon Sep 5 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.18-1
- Resolves: #1373120

* Mon Aug 15 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.17-1
- Add -y option to provide path to the Module.symvers file
- Resolves: #1366929
- Resolves: #1366952

* Fri Jul 15 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.16-3
- Fix requires
- Resolves: #1356905

* Wed May 04 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.16-1
- embed python-bugzilla interface to get rid of the package dependency
- Resolves: #1332810

* Tue Apr 26 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.15-1
- always load whitelist file from kernel-abi-whitelists package, remove the attached files
- always load Module.symvers file from kernel-devel package, remove attached files
- use python-bugzilla instead of private bz_xmlrpc package
- Resolves: #1328384
- Resolves: #906664
- Resolves: #906659
- Resolves: #1272348

* Tue Feb 25 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.11-1
- Resolves: #1066162

* Fri Jan 10 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.10-1
- Resolves: #1051506

* Fri Jan 10 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.9-2
- added binutils cpp file dependencies
- Resolves: #1051411

* Thu Jan 09 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.9-1
- updating to version 0.9.9
- Resolves: #881654
- Resolves: #1028410
- Resolves: #1045025
- Resolves: #1045368
- Resolves: #1045388

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.9.8-2
- Mass rebuild 2013-12-27

* Mon Nov 18 2013 Jiri Olsa <jolsa@redhat.com> - 0.9.8-1
- updating to version 0.9.8
- Resolves: #1028410

* Tue Aug 20 2013 Jiri Olsa <jolsa@redhat.com> - 0.9.5-1
- updating to version 0.9.5

* Fri Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-3
- removing kabi-whitelists dependency

* Fri Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-2
- spec file updates

* Fri Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-1
- new version with license info updated

* Tue Nov 20 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.2-1
- initial
