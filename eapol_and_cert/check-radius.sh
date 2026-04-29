#!/usr/bin/env bash
CA_CHAIN_FILENAME=`mktemp`
EAPOL_RETURN=`/usr/local/bin/eapol_test -c eapol_test/peap-mschapv2.conf -a127.0.0.1 -p1812 -slocalhostradiussecret -t 9 -o $CA_CHAIN_FILENAME | tail -n 1 | sed 's/SUCCESS/0/'|sed 's/FAILURE/1/'`

if [ 0 -eq $EAPOL_RETURN ]; then

	# split cert
	grep -v "^/.*=.*/.*=.*$" < $CA_CHAIN_FILENAME | grep -v '^$' | csplit -sz -f $CA_CHAIN_FILENAME- - '/-----BEGIN CERTIFICATE-----/' '{*}'

	one_ex=1;
	for file in $CA_CHAIN_FILENAME-*; do
		if ! openssl x509 -noout -checkend $((24*60*60*20)) -in $file 1>/dev/null; then one_ex=0; fi
	done

	rm $CA_CHAIN_FILENAME*

	if [ 0 -eq $one_ex ]; then
		echo "RADIUS WARNING Certificate expires soon"
		exit 1
	else
		echo "RADIUS OK"
		exit 0
	fi
else
	echo "RADIUS CRITICAL Problem with Authentication"
	exit 2
fi

