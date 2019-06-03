source build.sh
$(aws ecr get-login --no-include-email --region us-east-2)
docker tag ibc:latest 610953770981.dkr.ecr.us-east-2.amazonaws.com/ibc:latest
docker push 610953770981.dkr.ecr.us-east-2.amazonaws.com/ibc:latest
