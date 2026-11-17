# Derived from the pinned upstream image only to guarantee a
# Python 3 interpreter for Hadoop Streaming tasks on the
# NodeManager and the client. Nothing else changes.
# The pinned upstream image is CentOS 7 based (yum; there is no
# apt) and CentOS 7 is end of life: mirror.centos.org is retired,
# so the repos are pointed at vault.centos.org before installing.
# This yields Python 3.6.8 in task containers (DECISIONS.md D4).
FROM apache/hadoop:3.5.0
USER root
RUN sed -i -e 's/mirror.centos.org/vault.centos.org/g' \
        -e 's/^mirrorlist/#mirrorlist/g' \
        -e 's/^#baseurl/baseurl/g' /etc/yum.repos.d/CentOS-*.repo \
 && yum install -y python3 \
 && yum clean all \
 && rm -rf /var/cache/yum
