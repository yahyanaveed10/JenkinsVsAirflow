import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
def analyze_pipeline_performance(df):
    """
    Performs statistical analysis comparing pipeline execution times between Airflow and Jenkins.

    Args:
        df: Pandas DataFrame with pipeline execution data. The DataFrame should have at least
            the following columns:  s'.
            - 'pipeline_name': The name of the pipeline.
            - 'avg_execution_time_seconds': The average execution time in seconds.

    Returns:
        A dictionary containing the results of the statistical analysis.
    """
    common_pipelines = df.groupby('pipeline_name')['platform'].nunique() == 2
    common_pipelines = common_pipelines[common_pipelines].index
    df = df[df['pipeline_name'].isin(common_pipelines)]

    df_pivot = df.pivot(index='pipeline_name', columns='platform', values='avg_execution_time_seconds')
    df_pivot.reset_index(inplace=True)

    df_pivot['diff'] = df_pivot['Jenkins'] - df_pivot['Airflow']

    shapiro_test = stats.shapiro(df_pivot['diff'])

    if shapiro_test.pvalue > 0.05:
        t_test = stats.ttest_rel(df_pivot['Jenkins'], df_pivot['Airflow'])
        paired_test_statistic = t_test.statistic
        paired_test_pvalue = t_test.pvalue
        test_used = 'Paired t-test'
    else:
        wilcoxon_test = stats.wilcoxon(df_pivot['Jenkins'], df_pivot['Airflow'])
        paired_test_statistic = wilcoxon_test.statistic
        paired_test_pvalue = wilcoxon_test.pvalue
        test_used = 'Wilcoxon Signed-Rank Test'

    def cohens_d(group1, group2):
        diff = group1.mean() - group2.mean()
        n1, n2 = len(group1), len(group2)
        var1 = group1.var()
        var2 = group2.var()
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        pooled_std = pooled_var ** 0.5
        return diff / pooled_std

    d = cohens_d(df_pivot['Jenkins'], df_pivot['Airflow'])

    interpretation = ""
    if test_used == 'Paired t-test':
        if t_test.pvalue < 0.05:
            interpretation += "There is a statistically significant difference in average execution times between Jenkins and Airflow.\n"
        else:
            interpretation += "There is no statistically significant difference in average execution times between Jenkins and Airflow.\n"
    else:
        if wilcoxon_test.pvalue < 0.05:
            interpretation += "There is a statistically significant difference in average execution times between Jenkins and Airflow.\n"
        else:
            interpretation += "There is no statistically significant difference in average execution times between Jenkins and Airflow.\n"

    if d >= 0.8:
        interpretation += "The effect size is large (d >= 0.8)."
    elif d >= 0.5:
        interpretation += "The effect size is medium (0.5 <= d < 0.8)."
    else:
        interpretation += "The effect size is small (d < 0.5)."

    return {
        "shapiro_test_statistic": shapiro_test.statistic,
        "shapiro_test_pvalue": shapiro_test.pvalue,
        "paired_test_statistic": paired_test_statistic,
        "paired_test_pvalue": paired_test_pvalue,
        "test_used": test_used,
        "cohens_d": d,
        "interpretation": interpretation
    }

def load_data_from_csv(file_path):
    """Loads data from a CSV file and performs basic data cleaning."""
    try:
        df = pd.read_csv(file_path)
        # Assuming your CSV has columns like 'platform', 'pipeline_name', 'avg_execution_time_seconds'
        # Rename columns if necessary to match the expected column names
        df = df.rename(columns={
            'platform': 'platform',
            'pipeline_name': 'pipeline_name',
            'avg_execution_time_seconds': 'avg_execution_time_seconds'  # Make sure this matches your CSV
            # Add other columns if needed
        })
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading data from CSV: {e}")
        return None

# Example usage:
file_path = "data_grafana/GCM1formatted.csv"  # Replace with the actual path to your CSV file
#df = load_data_from_csv(file_path)
def visualize_execution_times(file_path):
    # Read the CSV file with semicolon separator
    df = pd.read_csv(file_path, sep=';')

    # Create the figure and axis
    plt.figure(figsize=(10, 6))

    # Create bar plot of average execution times
    sns.barplot(x='pipeline_name', y='avg_execution_time_seconds',
                hue='platform', data=df,
                errorbar=None)  # Removes error bars

    # Customize the plot
    plt.title('Average Execution Times by Pipeline and Platform', fontsize=15)
    plt.xlabel('Pipeline Name', fontsize=12)
    plt.ylabel('Average Execution Time (seconds)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the plot
    plt.savefig('average_execution_times.png', dpi=300)
    plt.close()

    print("Bar chart saved as average_execution_times.png")


# Usage
visualize_execution_times(file_path)
df = pd.read_csv(file_path, sep=';')
if df is not None:
    results = analyze_pipeline_performance(df)
    print(f"Shapiro-Wilk Test: Statistic={results['shapiro_test_statistic']:.4f}, p-value={results['shapiro_test_pvalue']:.4f}")
    print(f"{results['test_used']}: Statistic={results['paired_test_statistic']:.4f}, p-value={results['paired_test_pvalue']:.4f}")
    print(f"Cohen's d: {results['cohens_d']:.4f}")
    print(f"\nInterpretation:\n{results['interpretation']}")  # Removed extra '.'