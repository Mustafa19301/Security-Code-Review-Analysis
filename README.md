# Analyzing Code Review Dataset for Security Vulnerability Detection

## Team Members
- Mustafa Ahmed
- Murtaza Ahmed

## Project Overview

This project analyzes code review data to investigate how security related issues can be identified from code review discussions and associated code changes.

The project focuses primarily on GitHub Pull Requests and code review comments. We have two complementary datasets to investigate security related code review instances:

- A comment based dataset containing security labeled code review comments
- A patch dataset containing code review comments linked to their associated code changes

The project includes data preprocessing, manual validation, weak labeling, exploratory data analysis, machine learning classification, cross validation, model comparison, feature analysis, error analysis and model disagreement analysis.

## Project Objectives

The main objectives of this project are to:

- Analyze patterns in code review discussions related to software security
- Identify comments that may be related to security vulnerabilities
- Develop a labeled dataset for security related comment classification
- Investigate the impact of class imbalance on machine learning performance
- Investigate whether associated code changes provide additional information beyond review comments
- Apply machine learning techniques to classify security related code review instances
- Compare multiple classification models using consistent evaluation metrics
- Analyze classification errors and model disagreements to better understand the challenges of detecting security related comments

## Code Review Data

The project uses a large scale GitHub Pull Request and code review data.

The raw dataset contains approxixmately **82 million rows** and is approixmately **17.5GB** in size. Due to its size, the raw dataset is processed than being loaded entirely into memory.

The dataset contains information including:
- Comment ID
- Comment text
- Repository
- Programming language
- Pull request ID
- Author information
- Commit date

Github Pull Requests are the primary code review platform presented in the dataset. Other code review platforms such as Gerrit was considered an examples of platforms relevant to the broader project scope, but the current dataset and experiments focus on GitHub Pull Request/code review comments.

> **Note:** The raw dataset is not included in this repo due to its size

## Datasets

The project uses two datasets for the machine learning and data analysis experiements

### Comment Based Security Dataset

`final_security.csv`

This dataset contains security labeled code review comments derived from the original large scale dataset

The dataset was constructed through multiple processing and labeling stages, including manual validation and weak labeling. It is primarily used to analyze what information can be obtained from the text of code review comments.

The final dataset contains **9,230 comments** with the following labels:

| Label | Description |
| --- | --- |
| `0` | Not security related |
| `1` | Clearly security related |
| `2` | Possibly security related / uncertain |

For the binary machine learning experiments, uncertain comments (`label = 2`) are excluded. The resulting binary datasets contains **9,147 comments**

### Patch Security Dataset

`final_security_patch.csv`

This dataset contains about **5,000 GitHub Pull Request review comments**, with each review comment linked to its associated code patch/diff hunk

The dataset contains both the review discussion and the code change being reviewed, allowing the project to investigate three representations:

- **Comment only**: review comment text
- **Patch only**: associated code patch/diff hunk
- **Comment + Patch**: review comment combined with its associated code patch

The manually assigned labels are:

| Label | Description |
| --- | --- |
| `0` | Not security related |
| `1` | Clearly security related |
| `2` | Possibly security related / uncertain |

The dataset contains:

- **2,930** not security related
- **1,073** clearly security related
- **997** uncertain or ambigious

For the binary machine learning experiments, uncertain comments (`label = 2`) are excluded. The resulting in **4,003 binary labeled**

## Data Processing and Labeling

There are multiple stages where we needed to prepare the code review comments for analysis and machine learning

### Data Processing

The original dataset is processed to identify relevant comments and reduce unnecessary duplication. Processed datasets are stored under `data/processed`

Because the original dataset is very large, the project uses memory conscious processing techniques to work with the data on a personal computer with limited memory

### Candidate Extraction and Weak Labeling

Additional security related candidate comments were extracted from the larger dataset and labeled using a weak labeling approach

These labels are treated as **weak labels** and are not considered equivalent to the manually validated annotations

This process produced the larger `final_security.csv` dataset

## Data Analysis

The project analyzes code review comments to investigate patterns associated with security related discussions

The analysis included:
- Security label distributions
- Programming lanaguage distributions
- Review comment characteristics
- Patch characteristics
- TF-IDF feature analysis
- Classification error analysis
- Category level error analysis
- Model disagreement analysis
- Comparison of comment only, patch only and comment with patch representations
- Examination of comments that are difficult for models to classify

These analyses are used to better understand how security related issues appear in code review discussions and where automated classification has limitations

## Machine Learning Methodology

### Text Representation

Code review comments are converted into numerical feature representations using **TF-IDF (Term Frequency Inverse Document Frequency)**

The TD-IDF configuration uses:
- Unigrams and bigrams
- English stop-word removal
- Minimum document frequency of 2
- Maximum document frequency of 95%
- Sublinear TF scaling

For the patch experiement, code diff hunks are cleaned before TF-IDF processing. Added, deleted and context lines are represented separately to preserver information about how the code changed

### Comment Dataset

The `final_security.csv` dataset uses an **80/20 stratified train/test split** for its primary machine learning experiment

The resulting datasets contains:
- **7,317** training comments
- **1,830** testing comments

Models are also evaluated using cross-validation

### Patch Dataset

The `final_security_patch.csv` dataset uses only binary labeled instances (`label = 0` or `label = 1`) for machine learning

Because multiple review comments can belong to the same Pull Request, the patch experiments use **grouped cross validation by Pull Request**. This prevents comments from the same Pull Request from being placed in different training and validation folds

The patch experiment evaluated three instances:
- Comment only
- Patch only
- Comment + Patch

### Classification Models

Three machine learning models were used to evaluate:
- Logistic Regression
- Linear Support Vector Machine (Linear SVM)
- Random Forest

Class weighting is used for the Logistic Regression and Linear SVM models to account for class imbalance

### Cross Validation

The models are also evaluated using **5-fold stratified cross validation**

For the patch dataset, **Stratified Group K-Fold cross validation** is used to preserve class balance while keeping comments from the same Pull Request within the same fold

The following metrics were used:
- Accuracy
- Balanced Accuracy
- Precision
- Recall
- F1-score

## Additional Experiments and Analysis

### Comment Only Analysis

Review comment text is used as the sole input to investigate how effectively security related instances can be classified from review discussions alone

### Patch Only Analysis

Associated code changes are used to as the input to investigate whether information contained in the code changes provides predictive information for security related classification

### Comment + Patch Analysis

Review comments and their associated code changes are combined into a single text representation

This experiement investigates whether combining the reviewers discussion with the code being reviewed provides additional information compared with using either representation independently

### Error Analysis

Misclassified comments were examined to identify patterns in false positives and false negatives

### Feature Analysis

TF-IDF features were analyzed to investigate which terms and phrases were associated with classification results

### Category Error Analysis

Classification errors were examined across different comment categories to identify areas where the models had greater difficulty

### Model Disagreement Analysis

Predictions from the three models were compared to identify comments where the models produced different predictions

This analysis provides additional insight into cases where the classification decision is less consistent across models

## Scope and Limitations

The project focuses on classifying security related code review instances from GitHub Pull Requests

The analysis considers both review discussion and, in the patch-aware experiments, the associated code changes

The labels represent whether a code review instance was considered security-related according to the project's labeling methodology. They should not be interpreted as definitive confirmation that an underlying source-code vulnerability exists

The larger final_security.csv dataset includes weakly labeled examples, while final_security_patch.csv uses labeled sample. Therefore, model performance should be interpreted in the context of the dataset construction and labeling methodology

The results demonstrate classification performance on the constructed datasets and should not be interpreted as definitive real world vulnerability detection performance

## Technologies
- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Jupyter Notebook