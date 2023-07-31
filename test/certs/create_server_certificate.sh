#!/bin/bash
set -u
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ "$#" -eq 0 ]]; then
	cat <<-EOF

	To generate a server certificate, provide the domain name as a parameter:
	    $(basename $0) www.my-domain.tdl
	    $(basename $0) www.my-domain.tdl alternate.domain.tld

	You can also create certificates for wildcard domains:
	    $(basename $0) '*.my-domain.tdl'

	EOF
	exit 0
else
	DOMAIN="$1"
	ALTERNATE_DOMAINS="DNS:$( echo "$@" | sed 's/ /,DNS:/g')"
fi


###############################################################################
# Create a nginx container (which conveniently provides the `openssl` command)
###############################################################################

CONTAINER=$(docker run -d -v $DIR:/work -w /work -e SAN="$ALTERNATE_DOMAINS" nginx:1.25.1)
# Configure openssl
docker exec $CONTAINER bash -c '
	mkdir -p /ca/{certs,crl,private,newcerts} 2>/dev/null
	echo 1000 > /ca/serial
	touch /ca/index.txt
	cat > /ca/openssl.cnf <<-"OESCRIPT"
		[ ca ]
		# `man ca`
		default_ca = CA_default

		[ CA_default ]
		# Directory and file locations.
		dir               = /ca
		certs             = $dir/certs
		crl_dir           = $dir/crl
		new_certs_dir     = $dir/newcerts
		database          = $dir/index.txt
		serial            = $dir/serial
		RANDFILE          = $dir/private/.rand

		# The root key and root certificate.
		private_key       = /work/ca-root.key
		certificate       = /work/ca-root.crt

		# SHA-1 is deprecated, so use SHA-2 instead.
		default_md        = sha256

		name_opt          = ca_default
		cert_opt          = ca_default
		default_days      = 10000
		preserve          = no
		policy            = policy_loose

		[ policy_loose ]
		countryName             = optional
		stateOrProvinceName     = optional
		localityName            = optional
		organizationName        = optional
		organizationalUnitName  = optional
		commonName              = supplied
		emailAddress            = optional

		[ req ]
		# Options for the `req` tool (`man req`).
		default_bits        = 2048
		distinguished_name  = req_distinguished_name
		string_mask         = utf8only

		# SHA-1 is deprecated, so use SHA-2 instead.
		default_md          = sha256

		# Extension to add when the -x509 option is used.
		x509_extensions     = v3_ca

		[ req_distinguished_name ]
		# See <https://en.wikipedia.org/wiki/Certificate_signing_request>.
		countryName                     = Country Name (2 letter code)
		stateOrProvinceName             = State or Province Name
		localityName                    = Locality Name
		0.organizationName              = Organization Name
		organizationalUnitName          = Organizational Unit Name
		commonName                      = Common Name
		emailAddress                    = Email Address

		[ v3_ca ]
		# Extensions for a typical CA (`man x509v3_config`).
		subjectKeyIdentifier = hash
		authorityKeyIdentifier = keyid:always,issuer
		basicConstraints = critical, CA:true
		keyUsage = critical, digitalSignature, cRLSign, keyCertSign

		[ server_cert ]
		# Extensions for server certificates (`man x509v3_config`).
		basicConstraints = CA:FALSE
		nsCertType = server
		nsComment = server certificate generated for test purpose (nginx-proxy test suite)
		subjectKeyIdentifier = hash
		authorityKeyIdentifier = keyid,issuer:always
		keyUsage = critical, digitalSignature, keyEncipherment
		extendedKeyUsage = serverAuth

		[ san_env ]
		subjectAltName=${ENV::SAN}
	OESCRIPT
'

# shortcut for calling `openssl` inside the container
function openssl {
	docker exec $CONTAINER openssl "$@"
}

function exitfail {
		echo
		echo ERROR: "$@"
		docker rm -f $CONTAINER
		exit 1
}


###############################################################################
# Setup Certificate authority
###############################################################################

if ! [[ -f "$DIR/ca-root.key" ]]; then
	echo
	echo "> Create a Certificate Authority root key: $DIR/ca-root.key"
	openssl genrsa -out ca-root.key 2048
	[[ $? -eq 0 ]] || exitfail failed to generate CA root key
fi

# Create a CA root certificate
if ! [[ -f "$DIR/ca-root.crt" ]]; then
	echo
	echo "> Create a CA root certificate: $DIR/ca-root.crt"
	openssl req -config /ca/openssl.cnf \
	-key ca-root.key \
	-new -x509 -days 3650 -subj "/O=nginx-proxy test suite/CN=www.nginx-proxy.tld" -extensions v3_ca \
	-out ca-root.crt
	[[ $? -eq 0 ]] || exitfail failed to generate CA root certificate

	# Verify certificate
	openssl x509 -noout -text -in ca-root.crt
fi


###############################################################################
# create server key and certificate signed by the certificate authority
###############################################################################

echo
echo "> Create a host key: $DIR/$DOMAIN.key"
openssl genrsa -out "$DOMAIN.key" 2048

echo
echo "> Create a host certificate signing request"

SAN="$ALTERNATE_DOMAINS" openssl req -config /ca/openssl.cnf \
	-key "$DOMAIN.key" \
	-new -out "/ca/$DOMAIN.csr" -days 1000 -extensions san_env -subj "/CN=$DOMAIN"
	[[ $? -eq 0 ]] || exitfail failed to generate server certificate signing request

echo
echo "> Create server certificate: $DIR/$DOMAIN.crt"
SAN="$ALTERNATE_DOMAINS" openssl ca -config /ca/openssl.cnf -batch \
		-extensions server_cert \
		-extensions san_env \
		-in "/ca/$DOMAIN.csr" \
		-out "$DOMAIN.crt"
	[[ $? -eq 0 ]] || exitfail failed to generate server certificate


# Verify host certificate
#openssl x509 -noout -text -in "$DOMAIN.crt"


docker rm -f $CONTAINER >/dev/null
