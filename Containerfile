FROM golang:1.21 AS cue-builder

WORKDIR /build
RUN GO111MODULE=on GOPATH=/build go get cuelang.org/go/cmd/cue@v0.3.2

FROM ubuntu:24.04 AS cue-definition-generator

ARG VERSION=wallaby

COPY defaults.py /defaults.py
COPY generator.py /generator.py
COPY namespaces.yml /namespaces.yml
COPY requirements.txt /requirements.txt

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        apt-transport-https \
        python3-pip \
        software-properties-common \
    && add-apt-repository cloud-archive:${VERSION} \
    && apt-get install --no-install-recommends -y \
        python3-barbican \
        python3-ceilometer \
        python3-cinder \
        python3-glance \
        python3-keystone \
        python3-neutron \
    && pip3 install --no-cache-dir -r /requirements.txt \
    && mkdir /output \
    && python3 /defaults.py \
    && python3 /generator.py

FROM alpine:3.18
COPY --from=cue-builder /build/bin/cue /bin/cue
COPY --from=cue-definition-generator /output /definitions

LABEL "org.opencontainers.image.documentation"="https://docs.osism.tech" \
      "org.opencontainers.image.licenses"="ASL 2.0" \
      "org.opencontainers.image.source"="https://github.com/osism/openstack-configuration-validator" \
      "org.opencontainers.image.url"="https://www.osism.tech" \
      "org.opencontainers.image.vendor"="OSISM GmbH"
