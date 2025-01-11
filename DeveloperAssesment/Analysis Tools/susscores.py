def calculate_sus_score(responses):
    """Calculate SUS score from 10 responses (1-5 scale)"""
    if len(responses) != 10:
        raise ValueError("SUS requires exactly 10 responses")

    score = 0
    for i, response in enumerate(responses, 1):
        # Odd numbered questions
        if i % 2 == 1:
            score += (response - 1) * 2.5
        # Even numbered questions
        else:
            score += (5 - response) * 2.5

    return score


def calculate_nasa_tlx(mental, rush, success, effort, frustration):
    """Calculate NASA TLX metrics (1-20 scale)"""
    return {
        'Mental Demand': mental,
        'Time Pressure': rush,
        'Success Rate': success,
        'Effort': effort,
        'Frustration': frustration
    }


# Example usage
jenkins_a = calculate_sus_score([3, 5, 4, 4, 3, 3, 2, 4, 4, 4])  # Pedro
jenkins_b = calculate_sus_score([4, 3, 2, 4, 3, 2, 2, 3, 4, 3])  # Dennis
airflow_a = calculate_sus_score([5, 3, 3, 3, 5, 2, 4, 2, 3, 5])
airflow_b = calculate_sus_score([4, 2, 4, 3, 4, 2, 4, 2, 2, 4])

print("\nSUS Scores:")
print(f"Jenkins A: {jenkins_a}")
print(f"Jenkins B: {jenkins_b}")
print(f"Airflow A: {airflow_a}")
print(f"Airflow B: {airflow_b}")

# Calculate NASA-TLX
jenkins_tlx_a = calculate_nasa_tlx(17, 20, 15, 17, 20)
jenkins_tlx_b = calculate_nasa_tlx(15, 15, 15, 15, 5)
airflow_tlx_a = calculate_nasa_tlx(10, 10, 17, 10, 5)
airflow_tlx_b = calculate_nasa_tlx(15, 15, 15, 10, 5)

print("\nNASA-TLX Scores:")
print("Jenkins A:", jenkins_tlx_a)
print("Jenkins B:", jenkins_tlx_b)
print("Airflow A:", airflow_tlx_a)
print("Airflow B:", airflow_tlx_b)