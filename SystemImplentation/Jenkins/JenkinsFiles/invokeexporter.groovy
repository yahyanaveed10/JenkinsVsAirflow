#!/usr/bin/env groovy
import org.apache.commons.lang.StringUtils
import copyFunctions



def call (
        String location,
		String credentialsId,
		String server,
		String outputDir,
		String javaOpt="",
  		String numRetries = "5"
		) {
  
  	
	dir("${location}"){
      	def int trialNumber = 0
      
        retry (numRetries as int) {
          
			trialNumber += 1
			exportStatusCode = 0
			withCredentials([usernamePassword(credentialsId: credentialsId, passwordVariable: 'password', usernameVariable: 'username')]) {
				exportStatusCode = bat(returnStatus: true, script:/java ${javaOpt} -jar exporter.jar -s ${server}  -u %username% -p %password%  /)
				echo "StatusCode of export: ${exportStatusCode}"
			}
            if ((exportStatusCode != 0))
        	{
        		//Fail Step if export or Analysis Script reported Error
				echo "StatusCode export: ${exportStatusCode}" 
			
				if (trialNumber!=(numRetries as int))
				//Sleep 10 minutes to give export some time to recover
				sleep time: 10, unit: 'MINUTES'
            
          		error "StatusCode export: ${exportStatusCode}" 
        	} 
	
		}
	}        
	
}