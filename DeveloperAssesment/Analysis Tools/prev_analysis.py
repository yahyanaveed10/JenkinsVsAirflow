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

    def calculate_sus(self, responses):
        if len(responses) != 10:
            return None

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

        for metric in metrics:
            jenkins_avg = (self.nasa_responses['jenkins_a'][metric] +
                           self.nasa_responses['jenkins_b'][metric]) / 2
            airflow_avg = (self.nasa_responses['airflow_a'][metric] +
                           self.nasa_responses['airflow_b'][metric]) / 2

            averages['jenkins'][metric] = jenkins_avg
            averages['airflow'][metric] = airflow_avg

        return averages

    def thematic_analysis(self):
        # Phase 1 & 2: Familiarize and Generate Codes
        codes = {
            "resource_management": {
                "quotes": [
                    "Jenkins was way too slow creating working nodes",
                    "Airflow uses ressources in a more efficient way"
                ],
                "frequency": 4
            },
            "system_complexity": {
                "quotes": [
                    "Understand the whole Jenkins system due to relatively high complexity",
                    "two levels of configuration"
                ],
                "frequency": 3
            },
            "learning_curve": {
                "quotes": [
                    "quite easy to learn in comparison to Jenkins",
                    "using only Python which makes it easier"
                ],
                "frequency": 3
            },
            "monitoring": {
                "quotes": [
                    "both logs are plenty with information",
                    "both ways are fine"
                ],
                "frequency": 2
            }
        }

        # Phase 3 & 4: Identify and Review Themes
        themes = {
            "System Usability": {
                "codes": ["learning_curve", "system_complexity"],
                "evidence": [
                    "easier in comparison to Jenkins",
                    "using only Python which makes it easier"
                ],
                "relation_to_metrics": {
                    "sus": "Supports higher SUS scores for Airflow",
                    "nasa_tlx": "Correlates with lower mental demand"
                }
            },
            "Performance": {
                "codes": ["resource_management"],
                "evidence": [
                    "faster with Airflow",
                    "uses ressources in a more efficient way"
                ],
                "relation_to_metrics": {
                    "nasa_tlx": "Supports lower effort scores for Airflow"
                }
            },
            "Operational Aspects": {
                "codes": ["monitoring"],
                "evidence": [
                    "both logs are plenty with information",
                    "both ways are fine"
                ],
                "relation_to_metrics": {
                    "nasa_tlx": "Similar frustration levels for monitoring"
                }
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
                    "finding": "Airflow demonstrates better usability",
                    "evidence": {
                        "quantitative": f"SUS score difference: {sus_results['airflow_average'] - sus_results['jenkins_average']:.2f}",
                        "qualitative": themes["System Usability"]["evidence"]
                    }
                },
                "workload": {
                    "finding": "Lower cognitive load with Airflow",
                    "evidence": {
                        "quantitative": f"Mental demand difference: {nasa_results['jenkins']['mental'] - nasa_results['airflow']['mental']:.2f}",
                        "qualitative": themes["Performance"]["evidence"]
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
print(f"Jenkins Average: {report['quantitative_results']['sus']['jenkins_average']:.2f}")
print(f"Airflow Average: {report['quantitative_results']['sus']['airflow_average']:.2f}")

print("\nNASA-TLX Results:")
print("Jenkins:", report['quantitative_results']['nasa_tlx']['jenkins'])
print("Airflow:", report['quantitative_results']['nasa_tlx']['airflow'])

print("\nKey Themes:")
for theme, data in report['qualitative_results'].items():
    print(f"\n{theme}:")
    print("Evidence:", data['evidence'])