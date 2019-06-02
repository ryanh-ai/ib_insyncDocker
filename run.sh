docker rm ibg
docker run -d -e IB_USER=${IB_USER} -e IB_PASSWORD=${IB_PASSWORD} -e TWS_LIVE_PAPER=${TWS_LIVE_PAPER} \
	   --publish 127.0.0.1:4003:4003 --name ibg ibc
