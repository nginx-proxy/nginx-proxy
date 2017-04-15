create_server_certificate.sh
============================

`create_server_certificate.sh` is a script helping with issuing server certificates that can be used to provide TLS on web servers.

It also creates a Certificate Authority (CA) root key and certificate. This CA root certificate can be used to validate the server certificates it generates.

For instance, with _curl_:

    curl --cacert /somewhere/ca-root.crt https://www.example.com/

or with _wget_:

    wget --certificate=/somewhere/ca-root.crt https://www.example.com/

or with the python _requests_ module:

    import requests
    r = requests.get("https://www.example.com", verify="/somewhere/ca-root.crt")

Usage
-----

### Simple domain

Create a server certificate for domain `www.example.com`:

    ./create_server_certificate.sh www.example.com

Will produce:
 - `www.example.com.key`
 - `www.example.com.crt`


### Multiple domains 

Create a server certificate for main domain `www.example.com` and alternative domains `example.com`, `foo.com` and `bar.com`:

    ./create_server_certificate.sh www.example.com foo.com bar.com

Will produce:
 - `www.example.com.key`
 - `www.example.com.crt`
 
### Wildcard domain

Create a server certificate for wildcard domain `*.example.com`:

    ./create_server_certificate.sh "*.example.com"

Note that you need to use quotes around the domain string or the shell would expand `*`.

Will produce:
 - `*.example.com.key`
 - `*.example.com.crt`

Again, to prevent your shell from expanding `*`, use quotes. i.e.: `cat "*.example.com.crt"`.

Such a server certificate would be valid for domains:
- `foo.example.com` 
- `bar.example.com`

but not for domains:
- `example.com`
- `foo.bar.example.com`


### Wildcard domain on multiple levels

While you can technically create a server certificate for wildcard domain `*.example.com` and alternative name `*.*.example.com`, client implementations generally do not support multiple wildcards in a domain name.

For instance, a python script using urllib3 would fail to validate domain `foo.bar.example.com` presenting a certificate with name `*.*.example.com`. It is advised to stay away from producing such certificates.

If you want to give it a try:

    ./create_server_certificate.sh "*.example.com" "*.*.example.com"

Such a server certificate would be valid for domains:
- `foo.example.com` 
- `bar.example.com`
- `foo.bar.example.com`
