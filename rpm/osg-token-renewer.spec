Name:      osg-token-renewer
Summary:   oidc-agent token renewal service and timer
Version:   0.1
Release:   0%{?dist}
License:   ASL 2.0
URL:       http://www.opensciencegrid.org
BuildArch: noarch

Source0:   %{name}-%{version}.tar.gz

Requires:  oidc-agent


%description
%summary

%prep
%setup -q

%build

%install
install -d $RPM_BUILD_ROOT/%{_bindir}
install -dm700 $RPM_BUILD_ROOT/%{_sysconfdir}/osg/tokens
install -dm700 $RPM_BUILD_ROOT/%{_sysconfdir}/osg/token-renewer
install -m 755 %{name}.py $RPM_BUILD_ROOT/%{_bindir}/%{name}
install -m 600 config.ini $RPM_BUILD_ROOT/%{_sysconfdir}/osg/token-renewer


%files
%defattr(-,root,root,-)
%{_bindir}/%{name}

%dir %{_sysconfdir}/osg/tokens
%config(noreplace) %{_sysconfdir}/osg/token-renewer/config.ini

%changelog
* Thu Aug 05 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.1-1
- Initial release

