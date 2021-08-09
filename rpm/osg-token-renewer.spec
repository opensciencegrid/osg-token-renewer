Name:      osg-token-renewer
Summary:   oidc-agent token renewal service and timer
Version:   0.1
Release:   0%{?dist}
License:   ASL 2.0
URL:       http://www.opensciencegrid.org

Source0: %{name}-%{version}.tar.gz

Requires: oidc-agent


%description
%summary

%prep
%setup -q

%build

%install
install -d $RPM_BUILD_ROOT/%{_bindir}
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/osg/tokens
install -m 755 %{name}.py $RPM_BUILD_ROOT/%{_bindir}/%{name}
install -m 600 renewer.ini $RPM_BUILD_ROOT/%{_sysconfdir}/osg/tokens


%files
%defattr(-,root,root,-)
%{_bindir}/%{name}

%config(noreplace) %{_sysconfdir}/osg/tokens/renewer.ini

%changelog
* Thu Aug 05 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.1-1
- Initial release

