# Supported targets: el9 (nodejs 16 or 18 via module)

%{!?yana_core_version: %define yana_core_version 1.2.2}
#define yana_core_revision 1234567
%{!?yana_wui_version: %define yana_wui_version 1.2.2}
#define yana_wui_revision 1234567
%{!?ztools_version: %define ztools_version 1.0.4}
#define ztools_revision 1234567

%define zenetys_git_source() %{lua:
    local version_source = 'https://github.com/zenetys/%s/archive/refs/tags/v%s.tar.gz#/%s-%s.tar.gz'
    local revision_source = 'http://git.zenetys.loc/data/projects/%s.git/snapshot/%s.tar.gz#/%s-%s.tar.gz'
    local name = rpm.expand("%{1}")
    local iname = name:gsub("%W", "_")
    local version = rpm.expand("%{"..iname.."_version}")
    local revision = rpm.expand("%{?"..iname.."_revision}")
    if revision == '' then print(version_source:format(name, version, name, version))
    else print(revision_source:format(name, revision, name, revision)) end
}

Name: yana
Version: %{yana_core_version}
Release: 1%{?yana_core_revision:.git%{yana_core_revision}}%{?dist}.zenetys
Summary: YaNA network analyzer
Group: Applications/System
License: MIT
URL: https://github.com/zenetys/yana-core

Source0: %zenetys_git_source yana-core
Source1: %zenetys_git_source yana-wui
Source2: %zenetys_git_source ztools

Patch0: yana-core-swspecs-config.patch

Source10: nscan.conf.sample
Source11: yana-core.service
Source12: yana-core.sysconfig
Source13: yana.httpd
Source14: yana.logrotate
Source15: yana.cron
Source20: oui.json
Source21: snmp-oid.json
Source30: logfile
Source31: run-nscan

BuildArch: noarch

# standard
BuildRequires: nodejs >= 1:16
BuildRequires: sed
BuildRequires: systemd
# epel
BuildRequires: yarnpkg

# standard
Requires: bash
Requires: bind-utils
Requires: curl
Requires: grep
Requires: net-snmp-utils
Requires: nodejs >= 1:16
Requires: procps-ng
Requires: sed
# epel
Requires: fping

%description
YaNA stands for "Yet another Network Analyzer" and is composed of:
- nscan, a scanner written in Bash to discover and gather informations
  about devices seen on the network;
- yana-core, a server written in Node.js that parses scan files produced
  by nscan and provides an API to query data from scans;
- yana-wui, a web frontend written in Vue.js to view data from scans.

%prep
%setup -c -T

# yana-core
mkdir yana-core
tar xvzf %{SOURCE0} --strip-components 1 -C yana-core
cd yana-core
%patch0 -p1
cd ..

# yana-wui
mkdir yana-wui
tar xvzf %{SOURCE1} --strip-components 1 -C yana-wui

# ztools
mkdir ztools
tar xvzf %{SOURCE2} --strip-components 1 -C ztools

%build
# yana-wui
cd yana-wui
node_bin_sig=$(node -e 'process.stdout.write("node_" +
    process.version.replace(/^v([0-9]+).*/, "$1") + "_" +
    process.arch)')
node_modules_sig="modules_$(md5sum package.json |awk '{print $1}')"
node_modules_cache_file="${node_bin_sig}_${node_modules_sig}.tar.xz"
if [ -f "%_sourcedir/$node_modules_cache_file" ]; then
    tar xvJf "%{_sourcedir}/$node_modules_cache_file"
else
    yarn
    tar cJf "%{_sourcedir}/$node_modules_cache_file" node_modules yarn.lock
fi
yarn build
cd ..

%install
install -d -m 0755 %{buildroot}/opt/yana/share
cp -RT yana-core %{buildroot}/opt/yana/share/core
cp -RT yana-wui/dist %{buildroot}/opt/yana/share/wui
cp -RT ztools/nscan %{buildroot}/opt/yana/share/nscan

install -d -m 0750 %{buildroot}/%{_localstatedir}/lib/yana{,/core,/nscan}
install -d -m 0750 %{buildroot}/%{_localstatedir}/log/yana

install -d -m 0755 %{buildroot}/opt/yana/share/configs
echo 'This directory contains sample or default configuration files' \
    > %{buildroot}/opt/yana/share/configs/README

install -D -m 0644 %{SOURCE10} %{buildroot}/opt/yana/share/configs/nscan.conf
install -D -m 0644 %{SOURCE13} %{buildroot}/opt/yana/share/configs/yana.httpd.conf
mv %{buildroot}/opt/yana/share/{wui/config.json,configs/yana-wui.json}
mv %{buildroot}/opt/yana/share/{core/config.json,configs/yana-core.json}

sed -i -r \
    -e 's@"(API_BASE_URL)":\s*"([^"]+)"@"\1": "./core"@' \
    -e 's@"(BACKUP_API_BASE_URL)":\s*"([^"]+)"@"\1": "/zrancid"@' \
    -e 's@"(TTYD_URL)":\s*"([^"]+)"@"\1": "/zrancid/ttyd"@' \
    %{buildroot}/opt/yana/share/configs/yana-wui.json

sed -i -r \
    -e '2i\    "dataDir": "%{_localstatedir}/lib/yana/core",' \
    -e '2i\    "ouiFile": "%{_localstatedir}/lib/yana/core/oui.json",' \
    -e '2i\    "snmpOidFile": "%{_localstatedir}/lib/yana/core/snmp-oid.json",' \
    %{buildroot}/opt/yana/share/configs/yana-core.json

install -d -m 0755 %{buildroot}/%{_sysconfdir}/yana
cp %{buildroot}{/opt/yana/share/configs/yana-wui.json,%{_sysconfdir}/yana/yana-wui.json}
cp %{buildroot}{/opt/yana/share/configs/yana-core.json,%{_sysconfdir}/yana/yana-core.json}

install -D -m 0644 %{SOURCE11} %{buildroot}/%{_unitdir}/yana-core.service
install -D -m 0644 %{SOURCE12} %{buildroot}/%{_sysconfdir}/sysconfig/yana-core
install -D -m 0644 %{SOURCE14} %{buildroot}/%{_sysconfdir}/logrotate.d/yana
install -D -m 0644 %{SOURCE15} %{buildroot}/%{_sysconfdir}/cron.d/yana
install -D -m 0644 %{SOURCE20} %{buildroot}/%{_localstatedir}/lib/yana/core/oui.json
install -D -m 0644 %{SOURCE21} %{buildroot}/%{_localstatedir}/lib/yana/core/snmp-oid.json
install -D -m 0755 %{SOURCE30} %{buildroot}/opt/yana/bin/logfile
install -D -m 0755 %{SOURCE31} %{buildroot}/opt/yana/bin/run-nscan

%pre
if ! getent group yana >/dev/null; then
    groupadd -r yana
fi
if ! getent passwd yana >/dev/null; then
    useradd -r -g yana -d %{_localstatedir}/lib/yana \
        -s /sbin/nologin yana
fi

%post
%systemd_post yana-core.service
# add nscan configuration for a default entity on first install
if [ $1 -eq 1 ] && ! [ -e %{_sysconfdir}/yana/nscan-default.conf ]; then
    cp /opt/yana/share/configs/nscan.conf %{_sysconfdir}/yana/nscan-default.conf
fi

%preun
%systemd_preun yana-core.service

%postun
%systemd_postun_with_restart yana-core.service

%posttrans
cat <<"EOF"
%{name}: Note this RPM does not require httpd; a sample apache configuration
%{name}: is available in /opt/yana/share/configs/yana.httpd.conf.
EOF

%files
%config(noreplace) %{_sysconfdir}/cron.d/yana
%config(noreplace) %{_sysconfdir}/logrotate.d/yana
%config(noreplace) %{_sysconfdir}/sysconfig/yana-core
%dir %{_sysconfdir}/yana
%config(noreplace) %{_sysconfdir}/yana/yana-core.json
%config(noreplace) %{_sysconfdir}/yana/yana-wui.json
%{_unitdir}/yana-core.service
/opt/yana
%attr(-, yana, yana) %{_localstatedir}/lib/yana
%attr(-, yana, yana) %dir %{_localstatedir}/log/yana
