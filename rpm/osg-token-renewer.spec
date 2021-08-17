Name:      osg-token-renewer
Summary:   oidc-agent token renewal service and timer
Version:   0.1
Release:   1%{?dist}
License:   ASL 2.0
URL:       http://www.opensciencegrid.org
BuildArch: noarch

Source0:   %{name}-%{version}.tar.gz

Requires:  oidc-agent

%define svc_acct osg-token-svc


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
install -m 755 %{name}.sh $RPM_BUILD_ROOT/%{_bindir}/%{name}.sh
install -m 600 config.ini $RPM_BUILD_ROOT/%{_sysconfdir}/osg/token-renewer
install -d $RPM_BUILD_ROOT/%{_unitdir}
install -m 644 %{name}.service $RPM_BUILD_ROOT/%{_unitdir}
install -m 644 %{name}.timer $RPM_BUILD_ROOT/%{_unitdir}

%pre
getent group  %svc_acct >/dev/null || groupadd -r %svc_acct
getent passwd %svc_acct >/dev/null || \
       useradd -r -g %svc_acct -c "OSG Token Renewal Service" \
       -s /sbin/nologin -d %{_localstatedir}/spool/%svc_acct %svc_acct

%post
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%systemd_post %{name}.service %{name}.timer
%preun
%systemd_preun %{name}.service %{name}.timer
%postun
%systemd_postun_with_restart %{name}.service %{name}.timer


%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_bindir}/%{name}.sh
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}.timer

%dir %{_sysconfdir}/osg/tokens
%config(noreplace) %{_sysconfdir}/osg/token-renewer/config.ini

%changelog
* Tue Aug 17 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.1-1
- Initial pre-release

