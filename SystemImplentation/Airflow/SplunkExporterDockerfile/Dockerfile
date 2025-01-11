# Use a specific version of Ubuntu
FROM ubuntu:20.04

ENV  ARGUMENTS=""
USER root


###
RUN apt-get update && apt-get -y install --no-install-recommends \
openjdk-17-jre-headless \
python3 \
python3-pip \
    dos2unix \
&& apt-get install -y curl \
&& apt-get install -y bash \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
WORKDIR /app

COPY Splunk_Exporters /app/Splunk_Exporters
COPY exports.txt .
COPY script.sh .
COPY send_to_splunk.py .


### Exporting relvant modules to run the scipts ### -> if new modules needed to be added you can add it there
RUN pip3 install --no-cache-dir -r exports.txt

### Give permissions to the user ###
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

### Prepare the script ##
RUN chmod +x exporter.py
RUN dos2unix /app/script.sh
RUN chmod +x script.sh

### Define ENV'S ####

ENV SERVER=""
ENV USERNAME=""
ENV PASSWORD=""
ENV JAVA_OPT=""
ENV NUM_RETRIES="3"
ENV OUTPUT_DIR="/app/output"
ENV BUILD_TAG="your_build_tag"
RUN chmod +x script.sh
RUN mkdir -p /app/random && chmod -R 777 /app/random
WORKDIR /app
RUN chmod -R 777 /app



CMD ["./script.sh"]
