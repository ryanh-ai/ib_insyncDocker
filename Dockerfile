FROM ubuntu:18.04
MAINTAINER Ryan Hoium (canada4663@gmail.com)

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y locales \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
RUN apt-get install -y tzdata
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata

ENV LANG en_US.utf8

RUN echo '2' | apt-get install -y \
	unzip \
	curl \
	socat \
	xvfb \
	libxtst6 \
	libxrender1 \
	libxi6
 
RUN apt-get install -y python3-pip python3-dev \
  	&& cd /usr/local/bin \
 	&& ln -s /usr/bin/python3 python \
  	&& pip3 install --upgrade pip

# Set env vars for IBG/IBC
ENV IBG_VERSION=972-stable \
IBC_VERSION=3.7.5 \
IBC_INI=/root/config.ini \
IBC_PATH=/opt/ibc \
TWS_PATH=/root/Jts \
TWS_CONFIG_PATH=/root/Jts \
LOG_PATH=/opt/ibc/logs

# Install IBG
RUN curl --fail --output /tmp/ibgateway-standalone-linux-x64.sh https://s3.amazonaws.com/ib-gateway/ibgateway-${IBG_VERSION}-standalone-linux-x64.sh \
	&& chmod u+x /tmp/ibgateway-standalone-linux-x64.sh \
	&& echo 'n' | sh /tmp/ibgateway-standalone-linux-x64.sh \ 
	&& rm -f /tmp/ibgateway-standalone-linux-x64.sh

# Install IBC
RUN curl --fail --silent --location --output /tmp/IBC.zip https://github.com/ibcalpha/ibc/releases/download/${IBC_VERSION}/IBCLinux-${IBC_VERSION}.zip \
	&& unzip /tmp/IBC.zip -d ${IBC_PATH} \
	&& chmod -R u+x ${IBC_PATH}/*.sh \
	&& chmod -R u+x ${IBC_PATH}/scripts/*.sh \
	&& apt-get remove -y unzip \
	&& rm -f /tmp/IBC.zip

# Install ib_insync
RUN apt-get install -y git \
	&& pip install ib_insync \
	#&& pip install git+https://github.com/canada4663/ib_insync \
	&& pip install psutil \
	&& apt-get remove -y git
    

# Add xvfb/vnc/bin scripts
ENV DISPLAY=:0
COPY init /etc/init.d
COPY root /root
RUN chmod u+x /etc/init.d/* \
	&& chmod u+x /root/*

# expose ibg and vnc port
EXPOSE 4003

#ENTRYPOINT ["/usr/local/bin/python", "/root/ibcStart_docker.py"]
CMD ["/root/start.sh"]
