Name:		ksc
Version:	0.9.18
Release:	1%{?dist}
Epoch:		1
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
* Tue Sep 6 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.18-1
- Resolves: #1373208

* Tue Aug 16 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.17-1
- Add -y option to provide path to the Module.symvers file
- Resolves: #1367085

* Fri Jul 15 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.16-3
- Fix requires
- Resolves: #1356946

* Thu May 26 2016 Stanislav Kozina <skozina@redhat.com> - 0.9.16-1
- always load whitelist file from kernel-abi-whitelists package, remove the attached files
- always load Module.symvers file from kernel-devel package, remove attached files
- Resolves: #1335513

* Tue Aug 12 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.14-1
- Resolves #1128166

* Thu Aug 07 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.13-1
- Resolves #1126846

* Fri Aug 01 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.12-1
- Resolves #1124706

* Thu Apr 24 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.11-1
- Initial package update
- Resolves #1085004
