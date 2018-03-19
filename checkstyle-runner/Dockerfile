FROM java:8-jdk

WORKDIR /checkstyle

ADD tubs_checks.xml /checkstyle

ENV CHECKSTYLE_VERSION=7.6.1

RUN curl -sLO https://sourceforge.net/projects/checkstyle/files/checkstyle/${CHECKSTYLE_VERSION}/checkstyle-${CHECKSTYLE_VERSION}-all.jar && mv checkstyle-${CHECKSTYLE_VERSION}-all.jar checkstyle.jar

# gitlab runner does not use entrypoint like this
# https://docs.gitlab.com/runner/executors/docker.html#the-entrypoint
#ENTRYPOINT ["java","-jar","checkstyle.jar","-c","tubs_checks.xml"]

# default option, use file names to check
#CMD ["-v"]