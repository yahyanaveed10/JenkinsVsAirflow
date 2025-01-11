import pandas as pd
from collections import defaultdict


class MigrationAnalysis:
    def __init__(self):
        self.sus_responses = {
            'jenkins_a': [3, 5, 4, 4, 3, 3, 2, 4, 4, 4],
            'jenkins_b': [4, 3, 2, 4, 3, 2, 2, 3, 4, 3],
            'airflow_a': [5, 3, 3, 3, 5, 2, 4, 2, 3, 5],
            'airflow_b': [4, 2, 4, 3, 4, 2, 4, 2, 2, 4]
        }

        self.nasa_responses = {
            'jenkins_a': {'mental': 17, 'rushed': 20, 'successful': 15, 'effort': 17, 'frustrated': 20},
            'jenkins_b': {'mental': 15, 'rushed': 15, 'successful': 15, 'effort': 15, 'frustrated': 5},
            'airflow_a': {'mental': 10, 'rushed': 10, 'successful': 17, 'effort': 10, 'frustrated': 5},
            'airflow_b': {'mental': 15, 'rushed': 15, 'successful': 15, 'effort': 10, 'frustrated': 5}
        }

        self.quotes = [
            "In my opinion Airflow is faster in applying changes. This helps to analyse problems faster. I´ve faced a problem with xcom. The logs helped me to identify the location of the problem very fast. However due to the time I wasn´t able to fix this problem",
            "Jenkins is using several programming languages. Airflow is using only Python which makes it easier in comparison to Jenkins.",
            "Both systems are showing the tasks in a different way. For me both ways are fine. I would´t say that some of them are better than the other",
            "Airflow uses ressources in a more efficient way.",
            "Understand the whole Jenkins system due to relatively high complexity. In Airflow get the understanding about the new infractructure (OpenShift).",
            "Airflow due to usage of OpenShift.",
            "Airflow offers a scalable solution which is quite easy to learn in comparison to Jenkins.",
            "The problems I encountered where related with the connection to other systems not Airflow specific. The logs helped to identified the problem and fixed the issue was matter of seconds.I found quite comfortable the \"Pipeline as code\" mechanism, which simplified the complexity of the development task. The \"Task 2\" was impossible to develop it in Jenkins without a system in between like a sharedfolder or something like that, what increased the complexity of the task being impossible to resolve it in 45min. On the other hand it was really simple to resolve the issue using Airflow and the XCom mechanism.",
            "In both cases the execution was smoothly. The biggest different between Jenkins and Airflow during configuring Splunk exporter was that in Jenkins you need like two levels of configuration, first in jenkins adding a new pipeline element and configuring it and then at the automation script level. It cost a lot of time to perform the setup for jenkins, however it took just a couple of minutes to create the setup for Airflow. At the End the better performance was for Airflow because the jenkins was way too slow creating working nodes and executing the task on them.",
            "In both systems was possible to monitor the status of the execution. Both logs are plenty with information and also Workflow Visibility is available in both systems.",
            "the main problems during peak times and scalability ware the way Jenkins was using the resources. It was way to slow assigning working nodes in comparison with Airflow. Airflow offered more task reliability and was faster",
            "In case of Jenkins, the use of something similar like XComs (Task2) was impossible to implement.To mention some implementation difficulties in Airflow, we increased the difficulty of task 5 and tried to connect of Airflow with another Kubernetes Cluster different from the one configured by Yahya during his Thesis. It was not really clear the steps to perform the connection but with some research and Airflow documentation was pretty easy to deploy an Image in BCR and use it in the a new Kubernetes Cluster. ",
            "Without any doubts Airflow is prepared for more complex task and scalabity challenges in combination with Opershift or Kubernetes. "
        ]

    def calculate_sus(self, responses):
        if len(responses) != 10:
            raise ValueError("SUS responses must have exactly 10 items.")

        score = 0
        for i, response in enumerate(responses):
            if (i + 1) % 2 == 1:  # Odd items (1, 3, 5, 7, 9)
                score += response - 1
            else:  # Even items (2, 4, 6, 8, 10)
                score += 5 - response

        return score * 2.5

    def calculate_all_sus(self):
        sus_scores = {}
        for system, responses in self.sus_responses.items():
            sus_scores[system] = self.calculate_sus(responses)

        jenkins_avg = (sus_scores['jenkins_a'] + sus_scores['jenkins_b']) / 2
        airflow_avg = (sus_scores['airflow_a'] + sus_scores['airflow_b']) / 2

        return {
            'individual_scores': sus_scores,
            'jenkins_average': jenkins_avg,
            'airflow_average': airflow_avg
        }

    def analyze_nasa_tlx(self):
        metrics = ['mental', 'rushed', 'successful', 'effort', 'frustrated']
        averages = {
            'jenkins': {},
            'airflow': {}
        }
        individual_scores = {
            'jenkins': defaultdict(list),
            'airflow': defaultdict(list)
        }

        for system in ['jenkins', 'airflow']:
            for metric in metrics:
                for resp in ['a', 'b']:
                    key = f'{system}_{resp}'
                    individual_scores[system][metric].append(self.nasa_responses[key][metric])

                averages[system][metric] = (self.nasa_responses[f'{system}_a'][metric] +
                                            self.nasa_responses[f'{system}_b'][metric]) / 2

        return {
            'individual_scores': individual_scores,
            'averages': averages
        }

    def thematic_analysis(self):
        # 1. Familiarization and 2. Coding
        codes = defaultdict(list)
        for quote in self.quotes:
            if "Airflow" in quote:
                codes["Airflow"].append(quote)
            if "Jenkins" in quote:
                codes["Jenkins"].append(quote)
            if "faster" in quote or "slow" in quote:
                codes["Speed"].append(quote)
            if "easier" in quote or "difficult" in quote or "easier in comparison" in quote or "easy to learn" in quote:
                codes["Ease of Use"].append(quote)
            if "logs" in quote or "identify" in quote or "monitor" in quote or "xcom" in quote or "XCom" in quote or "XComs" in quote:
                codes["Troubleshooting"].append(quote)
            if "resources" in quote or "efficient" in quote:
                codes["Resource Efficiency"].append(quote)
            if "complex" in quote or "complexity" in quote or "difficult" in quote:
                codes["Complexity"].append(quote)
            if "OpenShift" in quote or "Kubernetes" in quote:
                codes["Scalability"].append(quote)
            if "connection" in quote or "configure" in quote or "configuration" in quote or "setup" in quote:
                codes["Configuration"].append(quote)
            if "task" in quote or "pipeline" in quote:
                codes["Task/Pipeline"].append(quote)
            if "execution" in quote:
                codes["Execution"].append(quote)

        # 3. & 4. Searching for, Defining, and Naming Themes
        themes = {
            "Ease of Use and Learning Curve": {
                "codes": ["Ease of Use", "Complexity", "Airflow", "Jenkins", "Scalability"],
                "description": "Perceptions of how easy or difficult it was to learn and use each system, including the impact of the programming languages used and the underlying infrastructure.",
                "evidence": codes["Ease of Use"] + codes["Complexity"] + codes["Airflow"] + codes["Jenkins"] + codes["Scalability"]
            },
            "Troubleshooting and Debugging": {
                "codes": ["Troubleshooting", "Airflow", "Jenkins"],
                "description": "Experiences with identifying and resolving errors in each system, focusing on the effectiveness of logs, specific debugging tools (like XCom), and the speed of applying changes.",
                "evidence": codes["Troubleshooting"] + codes["Airflow"] + codes["Jenkins"]
            },
            "Performance and Resource Efficiency": {
                "codes": ["Speed", "Resource Efficiency", "Airflow", "Jenkins"],
                "description": "Observations about how each system performed, including speed of execution, resource utilization, and task reliability, especially under load.",
                "evidence": codes["Speed"] + codes["Resource Efficiency"] + codes["Airflow"] + codes["Jenkins"]
            },
            "Configuration and Deployment": {
                "codes": ["Configuration", "Airflow", "Jenkins", "Task/Pipeline"],
                "description": "Experiences related to setting up, configuring, and deploying pipelines in each system, including challenges and time taken for initial setup.",
                "evidence": codes["Configuration"] + codes["Airflow"] + codes["Jenkins"] + codes["Task/Pipeline"]
            },
            "Execution and Monitoring": {
                "codes": ["Execution", "Monitoring"],
                "description": "Experiences related to the execution and monitoring in each system.",
                "evidence": codes["Execution"] + codes["Monitoring"]
            }
        }

        return themes

    def generate_integrated_report(self):
        sus_results = self.calculate_all_sus()
        nasa_results = self.analyze_nasa_tlx()
        themes = self.thematic_analysis()

        report = {
            "quantitative_results": {
                "sus": sus_results,
                "nasa_tlx": nasa_results
            },
            "qualitative_results": themes,
            "key_findings": {
                "usability": {
                    "finding": "Airflow demonstrates better usability, likely due to its Python-based configuration and easier debugging.",
                    "evidence": {
                        "quantitative": f"SUS score difference: {sus_results['airflow_average'] - sus_results['jenkins_average']:.2f}",
                        "qualitative": themes["Ease of Use and Learning Curve"]["evidence"]
                    }
                },
                "workload": {
                    "finding": "Airflow imposes a lower cognitive and emotional workload on developers compared to Jenkins",
                    "evidence": {
                        "quantitative": f"Mental demand difference: {nasa_results['averages']['jenkins']['mental'] - nasa_results['averages']['airflow']['mental']:.2f}, Frustration difference: {nasa_results['averages']['jenkins']['frustrated'] - nasa_results['averages']['airflow']['frustrated']:.2f}",
                        "qualitative": themes["Troubleshooting and Debugging"]["evidence"] +
                                       themes["Performance and Resource Efficiency"]["evidence"]
                    }
                },
                "Performance": {
                    "finding": "Airflow is faster in terms of execution, especially under heavy loads.",
                    "evidence": {
                        "quantitative": "Refer to performance analysis section",
                        "qualitative": themes["Performance and Resource Efficiency"]["evidence"]
                    }
                },
                "Configuration": {
                    "finding": "Airflow is easier and faster to set up than Jenkins.",
                    "evidence": {
                        "quantitative": "Refer to performance analysis section",
                        "qualitative": themes["Configuration and Deployment"]["evidence"]
                    }
                },
                "Execution": {
                    "finding": "Developer found no difference in monitoring, but did notice that execution was smoother in both",
                    "evidence": {
                        "quantitative": "Refer to performance analysis section",
                        "qualitative": themes["Execution and Monitoring"]["evidence"]
                    }
                }
            }
        }

        return report


# Usage
analysis = MigrationAnalysis()
report = analysis.generate_integrated_report()

# Print formatted results
print("\nSUS Scores:")
print("Individual Scores:", report['quantitative_results']['sus']['individual_scores'])
print(f"Jenkins Average: {report['quantitative_results']['sus']['jenkins_average']:.2f}")
print(f"Airflow Average: {report['quantitative_results']['sus']['airflow_average']:.2f}")

print("\nNASA-TLX Results:")
print("Individual Scores:", report['quantitative_results']['nasa_tlx']['individual_scores'])
print("Averages:", report['quantitative_results']['nasa_tlx']['averages'])

print("\nKey Themes:")
for theme, data in report['qualitative_results'].items():
    print(f"\n{theme}:")
    print("Description:", data['description'])
    print("Evidence:", data['evidence'])

print("\nKey Findings:")
for finding, data in report['key_findings'].items():
    print(f"\n{finding.capitalize()}:")
    print("Finding:", data['finding'])
    print("Evidence:")
    print("- Quantitative:", data['evidence']['quantitative'])
    print("- Qualitative:", data['evidence']['qualitative'])