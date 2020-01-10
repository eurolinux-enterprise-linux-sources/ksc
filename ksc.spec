Name:		ksc
Version:	0.9.5
Release:	1%{?dist}
Summary:	Kernel source code checker
Group:		Development/Tools
AutoReqProv:	no
License:	GPLv2+
URL:		http://www.redhat.com/
Source0:	ksc-%{version}.tar.gz
BuildArch:	noarch
Requires:	python
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
* Tue Aug 20 2013 Jiri Olsa <jolsa@redhat.com> - 0.9.5-1
- updating to version 0.9.5

* Tue Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-3
- removing kabi-whitelists dependency

* Fri Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-2
- spec file updates

* Fri Nov 30 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.3-1
- new version with license info updated

* Thu Nov 20 2012 Jiri Olsa <jolsa@redhat.com> - 0.9.2-1
- initial
