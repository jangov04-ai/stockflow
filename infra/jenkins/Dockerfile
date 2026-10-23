# Jenkins LTS + herramientas del pipeline de StockFlow:
#   Python 3 (build/tests), Node.js (ESLint), Chromium + chromedriver (Selenium)
FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      nodejs npm \
      chromium chromium-driver fonts-liberation \
 && rm -rf /var/lib/apt/lists/*
USER jenkins

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/opt/casc/casc.yaml
COPY casc.yaml /opt/casc/casc.yaml
