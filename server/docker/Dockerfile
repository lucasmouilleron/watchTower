#####################################################
FROM alpine:3.2

#####################################################
MAINTAINER Lucas Mouilleron <lucas.mouilleron@me.com>

#####################################################
#####################################################
# BASE INSTALL
#####################################################
#####################################################

#####################################################
# ENVS
#####################################################
ENV USER root
ENV HOME /root
ENV BASE_FOLDER /root
#####################################################
ENV HB_FOLDER $BASE_FOLDER/heartBeat
ENV HB_PORT 4443
ENV HB_REPO https://github.com/lucasmouilleron/heartBeat.git

#####################################################
# INTERFACE
#####################################################
EXPOSE $HB_PORT
WORKDIR $HB_FOLDER

#####################################################
# BASE PACKAGES
#####################################################
RUN echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update
RUN apk add python3 openssh-client git

#####################################################
# SSH KEYS
#####################################################
RUN ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa
RUN ssh-keyscan github.com >> ~/.ssh/known_hosts

#####################################################
# SCRITPS
#####################################################
RUN mkdir $BASE_FOLDER/scripts
COPY scripts/* $BASE_FOLDER/scripts/
RUN chmod -R a+x $BASE_FOLDER/scripts
ENV PATH $BASE_FOLDER/scripts:$PATH

#####################################################
# WORK SOURCES
#####################################################
# PREFETCH
RUN git clone --verbose --progress --depth=1 $HB_REPO $HB_FOLDER
# PREINSTALL
RUN $BASE_FOLDER/scripts/install
# CONFIGURE
COPY config/ $HB_FOLDER/server/config/

#####################################################
#####################################################
# RUN
#####################################################
#####################################################
CMD $BASE_FOLDER/scripts/buildAndRun