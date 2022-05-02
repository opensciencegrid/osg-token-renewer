Name:      osg-token-renewer
Summary:   oidc-agent token renewal service and timer
Version:   0.8.2
Release:   1%{?dist}
License:   ASL 2.0
URL:       http://www.opensciencegrid.org
BuildArch: noarch

Source0:   %{name}-%{version}.tar.gz

Requires:  oidc-agent

%define svc_acct osg-token-svc

%define __python /usr/bin/python3


%description
%summary

%prep
%setup -q

%build

%install
find . -type f -exec \
    sed -ri '1s,^#!\s*(/usr)?/bin/(env *)?python.*,#!%{__python},' '{}' +

install -d $RPM_BUILD_ROOT/%{_sbindir}
install -d $RPM_BUILD_ROOT/%{_libexecdir}/%{name}
install -dm700 $RPM_BUILD_ROOT/%{_sysconfdir}/osg/tokens
install -dm750 $RPM_BUILD_ROOT/%{_sysconfdir}/osg/token-renewer
install -m 755 %{name}.py $RPM_BUILD_ROOT/%{_libexecdir}/%{name}/%{name}
install -m 755 %{name}.sh $RPM_BUILD_ROOT/%{_libexecdir}/%{name}/%{name}.sh
install -m 755 %{name}-setup.sh $RPM_BUILD_ROOT/%{_sbindir}/%{name}-setup
install -m 640 config.ini $RPM_BUILD_ROOT/%{_sysconfdir}/osg/token-renewer
install -d $RPM_BUILD_ROOT/%{_unitdir}
install -m 644 %{name}.service $RPM_BUILD_ROOT/%{_unitdir}
install -m 644 %{name}.timer $RPM_BUILD_ROOT/%{_unitdir}
install -d -m 700 $RPM_BUILD_ROOT/%{_localstatedir}/spool/%svc_acct

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
%{_libexecdir}/%{name}/%{name}
%{_libexecdir}/%{name}/%{name}.sh
%{_sbindir}/%{name}-setup
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}.timer

%dir %{_sysconfdir}/osg/tokens
%attr(-,root,%svc_acct) %config(noreplace) %{_sysconfdir}/osg/token-renewer/config.ini
%attr(-,%svc_acct,%svc_acct) %dir %{_localstatedir}/spool/%svc_acct

%doc README.md


%changelog
* Thu Apr 28 2022 Carl Edquist <edquist@cs.wisc.edu> - 0.8.2-1
- Increase renewal frequency to ensure continual validity (SOFTWARE-5137)

* Mon Mar 14 2022 Brian Lin <blin@cs.wisc.edu> - 0.8.1-1
- Add the --pw-store option to the invocation of oidc-add and add a default
  scope of blank if no scopes are configured.  These are needed for the
  CILogon issuer (SOFTWARE-4983).

* Fri Feb 25 2022 Brian Lin <blin@cs.wisc.edu> - 0.8.0-1
- Add support for manual client registration (SOFTWARE-4983)

* Fri Oct 01 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.7.2-1
- Move scripts out of harm's way (SOFTWARE-4719)

* Thu Sep 30 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.7.1-1
- Fix indentation bug with zero or multiple tokens (SOFTWARE-4719)

* Tue Sep 28 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.7-1
- Fix exit status for main service script (SOFTWARE-4719)

* Tue Sep 28 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.6-2
- Drop .sh suffix on setup script

* Wed Sep 22 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.6-1
- Set AmbientCapabilities in systemd unit, for child processes (SOFTWARE-4719)

* Mon Sep 20 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.5-1
- Fixes for example config and setup script (SOFTWARE-4719)

* Mon Sep 20 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.4-3
- Fix ownership of service home dir (SOFTWARE-4719)

* Mon Sep 20 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.4-2
- Create service home dir in packaging but not in %pre (SOFTWARE-4719)

* Fri Sep 17 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.4-1
- Have user interact with oidc-gen via setup command (SOFTWARE-4719)

* Thu Sep 16 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.3-1
- Fix capabilities config in systemd unit (#3)

* Fri Sep 10 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.2-1
- Address code review comments (SOFTWARE-4719)
  - Improve config validation & error messages
  - Improve error handling; continue on errors
  - Increase the systemd timer frequency
- Add README leftovers from usage doc (SOFTWARE-4763)

* Tue Aug 17 2021 Carl Edquist <edquist@cs.wisc.edu> - 0.1-1
- Initial pre-release

