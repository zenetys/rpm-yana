| Package&nbsp;name | Supported&nbsp;targets |
| :--- | :--- |
| yana | el8, el9 |
<br/>

## Build:

The package can be built easily using the rpmbuild-docker script provided
in this repository. In order to use this script, _**a functional Docker
environment is needed**_, with ability to pull Rocky Linux (el9) images
from internet if not already downloaded.

```
$ ./rpmbuild-docker -d el8
$ ./rpmbuild-docker -d el9
```

## Prebuilt packages:

Builds of these packages are available on ZENETYS yum repositories:<br/>
https://packages.zenetys.com/latest/redhat/

## Setup:

**Requirements**

```
# dnf -y install epel-release
# crb enable

# cd /etc/yum.repos.d
# curl -OL https://packages.zenetys.com/latest/redhat/zenetys.repo
```

On el8, enable nodejs:16 or nodejs:18 module stream because the default version of nodejs is too old:

```
# dnf -y module enable nodejs:16
```

The yana package, as is, will most likely not work with SELinux enforcing, make sure it is disabled or permissive.

**Installation**

```
# dnf --setopt install_weak_deps=False install yana httpd mod_ssl
```

**API server**

```
# systemctl restart yana-core
# systemctl enable yana-core
```

**Nscan**

Edit nscan configuration `/etc/yana/nscan-default.conf`; this file is only created at first installation of the package. It should work by default but will probably not give much result, or with little detail. Some documentation about the credentials definition can be found in [ztools/nscan](https://github.com/zenetys/ztools/tree/master/nscan).

There can be any number of `nscan-<entity>.conf` in the directory, each will be available under a different entity in YaNA web interface.

In this package nscan runs as user yana. If the BASH_CMD variable is used to perform a scan from a remote host, ssh will thus look for client keys into `~yana/.ssh/` by default.

A cron task to run scans twice a day is installed in `/etc/cron.d/yana`. To run the scan(s) immediately:

```
# sudo -u yana /opt/yana/bin/run-nscan
```

Scan may take time to run; last log per entity is available in `/var/log/yana/nscan-<entity>.lastlog`, which can be followed in live with the tail command.

**Web server**

Here is a quick way of getting started using apache to serve the web interface, content will be available under /yana:

```
# ln -s /opt/yana/share/configs/yana.httpd.conf /etc/httpd/conf.d/60-yana.conf
# htpasswd -c -5 /etc/httpd/auth.htpasswd admin
# chmod 400 /etc/httpd/auth.htpasswd
# chown apache:root /etc/httpd/auth.htpasswd

# cat > /etc/httpd/conf.d/65-auth.conf <<"EOF"
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{REMOTE_ADDR} !=127.0.0.1
RewriteRule (.*) https://%{HTTP_HOST}$1 [R=302,L]
<Location />
    AuthType basic
    AuthName "Authentification required"
    AuthBasicProvider file
    AuthUserFile /etc/httpd/auth.htpasswd
    Require valid-user
    RequestHeader set X-Remote-User expr=%{REMOTE_USER}
</Location>
EOF

# systemctl restart httpd
# systemctl enable httpd
```
