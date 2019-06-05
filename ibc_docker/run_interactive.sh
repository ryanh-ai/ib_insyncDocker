docker rm ibg
docker run -e IB_USER=${IB_USER} -e IB_PASSWORD=${IB_PASSWORD} -e TWS_LIVE_PAPER=${TWS_LIVE_PAPER} \
	   -it --publish 127.0.0.1:4003:4003 --name ibg ibc /bin/bash
