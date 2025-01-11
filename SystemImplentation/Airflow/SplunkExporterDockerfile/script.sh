#!/bin/bash

# Set environment variables
export SERVER="${SERVER:-}"

export USERNAME="${USERNAME:-}"
export PASSWORD="${PASSWORD:-}"
export JAVA_OPT="${JAVA_OPT:-}"
export NUM_RETRIES="${NUM_RETRIES:-2}"
export OUTPUT_DIR="${OUTPUT_DIR:-}"
export BUILD_TAG="${BUILD_TAG:-}"
export LOCATION="${LOCATION:-}"


echo "Arguments passed to the script:"
echo "$@"

# Display all environment variables
echo "Environment Variables:"
printenv
# Check if the jar file exists
if [ ! -f "Splunk_Exporters/exporter.jar" ]; then
    echo "Error: exporter.jar not found!"
    exit 1
fi
 ### Not necessary, Just to make sure the arguments are reaching correctly
java_command="java $JAVA_OPT -jar /app/Splunk_Exporters/exporter.jar -s "$SERVER"  -u "$USERNAME" -p "$PASSWORD"" "
echo "Executing command: $java_command"
#sleep 10000000
#
## Run the java command and capture the output###
#output=$(eval $java_command)

## Echo the output
#echo "Response from java command:"
#echo "$output"
cd /app/random

### Running the Java Command Line (Duplication of the Original Groovy/Pipeline in Jenkins)
for (( trial=1; trial<=NUM_RETRIES; trial++ ))
do
    java $JAVA_OPT -jar /app/Splunk_Exporters/exporter.jar -s "$SERVER"  -u "$USERNAME" -p "$PASSWORD"" 

    Exporter_STATUS_CODE=$?

    echo "StatusCode of export: $Exporter_STATUS_CODE"

    # If the Java command is successful, copy files
    if [ $Exporter_STATUS_CODE -eq 0 ]; then
      echo "Exported Data successfully to app/random"
#        echo "export command succeeded. Copying files to the PVC volume..."
#
#        # Create the PVC mount directory if it doesn't exist
#        if [ ! -d "$PVC_VOLUME_PATH" ]; then
#            echo "PVC mount directory $PVC_VOLUME_PATH does not exist. Creating it..."
#            mkdir -p "$PVC_VOLUME_PATH"
#
#            if [ $? -eq 0 ]; then
#                echo "Successfully created $PVC_VOLUME_PATH."
#            else
#                echo "Failed to create $PVC_VOLUME_PATH. Exiting..."
#                exit 1
#            fi
#        fi
#
        #echo "Permission given to $PVC_VOLUME_PATH"
        #chmod 777 "$PVC_VOLUME_PATH"
        #ls -ld $PVC_VOLUME_PATH
        echo "Verifying the data is there.."
        ls /app/random
      fi
    done
        # Copy files from /app/random to the PVC volume
        #echo "Copying Files"
        #cp -r /app/random/* "$PVC_VOLUME_PATH/"
#
#        if [ $? -eq 0 ]; then
#            echo "Files successfully copied to PVC volume at $PVC_VOLUME_PATH."
#        else
#            echo "Failed to copy files to PVC volume."
#            exit 1
#        fi
#echo "Current http_proxy: $http_proxy"
#echo "Current https_proxy: $https_proxy"
#
# Unset proxy
unset http_proxy
unset https_proxy

echo "Proxy after unsetting:"
echo "http_proxy: $http_proxy"
echo "https_proxy: $https_proxy"
# Now run the curl command to check the Splunk HEC
echo "Checking Splunk HEC health..."
curl -k https://<splunk_instance/services/collector -H "Authorization: Splunk <token>"

# Optional: Check the exit status of the curl command
if [ $? -eq 0 ]; then
    echo "Splunk HEC is reachable and healthy."
else
    echo "Failed to connect to Splunk HEC."
fi
        echo "Sending the Data to Splunk..."
        python3 /app/send_to_splunk.py
        sleep 100

        break
    else
        echo "Error: StatusCode $Exporter_STATUS_CODE"
        if [ $trial -lt $NUM_RETRIES ]; then
            echo "Retrying in 10 minutes..."
            sleep 600
        else
            exit 1
        fi
    fi
done


