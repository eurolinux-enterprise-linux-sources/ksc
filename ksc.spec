Name:		ksc
Version:	0.9.14
Release:	1%{?dist}
Epoch:		1
Summary:	Kernel source code checker
Group:		Development/Tools
AutoReqProv:	no
License:	GPLv2+
URL:		http://www.redhat.com/
Source0:	ksc-%{version}.tar.gz
BuildArch:	noarch
Requires:	python python-pycurl kernel-abi-whitelists binutils cpp file
BuildRequires:	python

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
%doc README
%{_bindir}/ksc
%{_datadir}/ksc
%{_mandir}/man1/ksc.*
%config(noreplace) %{_sysconfdir}/ksc.conf
%{python_sitelib}/ksc-%{version}*.egg-info

%changelog
* Tue Aug 12 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.14-1
- Resolves #1128166

* Thu Aug 07 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.13-1
- Resolves #1126846

* Fri Aug 01 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.12-1
- Resolves #1124706

* Thu Apr 24 2014 Jiri Olsa <jolsa@redhat.com> - 0.9.11-1
- Initial package update
- Resolves #1085004
