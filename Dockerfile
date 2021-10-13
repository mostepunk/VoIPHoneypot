FROM alpine
#
# Include dist
#
# Get and install dependencies & packages
COPY OSfooler /OSfooler-ng
COPY generate_https_certs.py requirements.txt /home/cowrie/
COPY cowrie /code/cowrie
COPY cowrie/requirements.txt /home/cowrie/cowrie/
COPY cowrie /home/cowrie/cowrie
COPY package.json yarn.lock /home/cowrie/
ADD dist/ /root/dist/

RUN apk --no-cache -U add \
            bash \
            build-base \
            gmp-dev \
            gcc \
            libcap \
            libffi-dev \
            mpc1-dev \
            mpfr-dev \
            openssl \
            openssl-dev \
            python3 \
            python3-dev \
            py3-bcrypt \
            py3-mysqlclient \
            py3-requests \
            py3-setuptools \
            py3-pip \
            # <OS-fooler>
            python2 \
            python2-dev \
            libnetfilter_queue-dev \
            sudo \
            iptables \
            # </OS-fooler>
            # used to generate ssl certs for cowrie with 1040-bytes length
            openssh-keygen \
            # used to generate ssl certs for https service
            libressl-dev musl-dev \
            # Nodejs better-sqlite3 build dependency
            npm \
            # used to run nodejs http(s) + (tcp) servers (busybox emulators)
            nodejs yarn && \
            ln -snf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
            echo Europe/Moscow > /etc/timezone && \
#
# Setup user
    addgroup -g 2000 cowrie && \
    adduser -S -s /bin/bash -u 2000 -D -g 2000 cowrie && \
    rm -rfv /var/lib/apt/lists/* && \
#
# <OS-fooler>
    python2 -m ensurepip && \
    python2 -m pip install --no-cache-dir NetfilterQueue && \
    cd OSfooler-ng && \
    python2 setup.py install && \
# </OS-fooler>
#
#
# <Router>
#WORKDIR /home/cowrie
    cd /home/cowrie && \
    pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir pyOpenSSL && \
    python3 generate_https_certs.py && \
    pip3 uninstall -y pyOpenSSL && \
    pip3 install --no-cache-dir -r requirements.txt && \
    rm -R /root/.cache && \
#
#WORKDIR /code/cowrie
    cd /code/cowrie && \
    pip3 install --no-cache-dir . && \
# </Router>
#
# Install cowrie
#WORKDIR /home/cowrie/cowrie
    cd /home/cowrie/cowrie && \
    mkdir -p /temp/cowrie/data/log/tty /temp/cowrie/data/downloads /temp/cowrie/data/keys  && \
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --ignore-installed -r requirements.txt && \
    ssh-keygen -t rsa -b 1040 -f /temp/cowrie/data/keys/ssh_host_rsa_key && \
#
#
# <Nodejs dependencies installation>
#WORKDIR /home/cowrie
    cd /home/cowrie && \
    yarn && yarn cache clean && \
# </Nodejs dependencies installation>
#
# Setup configs
    chmod -R 777 /temp/ && export PYTHON_DIR=$(python3 --version | tr '[A-Z]' '[a-z]' | tr -d ' ' | cut -d '.' -f 1,2 ) && \
    setcap cap_net_bind_service=+ep /usr/bin/$PYTHON_DIR && \
    setcap cap_net_bind_service=+ep /usr/bin/node && \
    cp /root/dist/cowrie.cfg /home/cowrie/cowrie/cowrie.cfg && \
    chown cowrie:cowrie -R /home/cowrie/* /usr/lib/$PYTHON_DIR/site-packages/twisted/plugins && \
    chmod -R 777 /home/cowrie/cowrie && \
#
# Start Cowrie once to prevent dropin.cache errors upon container start caused by read-only filesystem
    su - cowrie -c "export PYTHONPATH=/home/cowrie/cowrie:/home/cowrie/cowrie/src && \
                    cd /home/cowrie/cowrie && \
                    /usr/bin/twistd --uid=2000 --gid=2000 -y cowrie.tac --pidfile cowrie.pid cowrie &" && \
    sleep 10 && \
#
# Clean up
    apk del --purge build-base \
                    gmp-dev \
                    libcap \
                    libffi-dev \
                    mpc1-dev \
                    mpfr-dev \
                    openssl-dev \
                    python3-dev \
                    py3-mysqlclient \
                    # Cowrie ssl certs generator
                    openssh-keygen \
                    # Nodejs packet manager
                    yarn \
                    # Nodejs better-sqlite3 build dependency
                    npm \
                    # <OS-Fooler>
                    python2-dev \
                    # </OS-Fooler>
                    && \
    rm -rf /root/* /tmp/* && \
    rm -rf /var/cache/apk/* && \
    rm -rf /home/cowrie/cowrie/cowrie.pid && \
    unset PYTHON_DIR

WORKDIR /home/cowrie
RUN chmod -R 777 /temp/cowrie/data/log 
#
# Start cowrie
ENV PYTHONPATH /home/cowrie/cowrie:/home/cowrie/cowrie/src

USER root

COPY . /home/cowrie
COPY node /home/node/data/

ENV interface eth0

ENTRYPOINT [ "./start.sh" ]
