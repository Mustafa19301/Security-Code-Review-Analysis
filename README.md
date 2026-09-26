# Analyzing Code Review Dataset for Security Vulnerability Detection

## Team Members
- Mustafa Ahmed
- Murtaza Ahmed

## Project Overview

This project analyzes code review data to investigate how security related issues can be identified from code review discussions.

The project focuses on extracting and analyzing security related comments from a large scale code review dataset, develpping labeled data for security classification and evaluating machine learning models for distinguishing security related comments from non security related comments.

The project includes data preporcessing, manual validation, weak labeling, exploratory data abalysis, machine learning classification, cross-validation, model comparison, feature analysis, error analysis and model disagreement analysis.

## Project Objectives

The main objectives of this project are to:

- Analyze patterns in code review discussions related to software security
- Identify comments that may be related to security vulnerabilities
- Develop a labeled dataset for security related comment classification
- Investigate the impact of class imbalance on machine learning performance
- Apply machine learning techniqyes to classify security related comments
- Compare multiple classification models using consistent evaluation metrics
- Analyze classification errors and model disagreements to better understand the challenges of detecting security related comments

## Code Review Data

The project uses a large scale dataset containing GitHub pull request and code review comments.

The raw dataset contains approxixmately **82 million rows** and is approixmately **17.5GB** in size. Due to its size, the raw dataset is processed than being loaded entirely into memory.

The dataset contains information including:
- Comment ID
- Comment text
- Repository
- Programming language
- Pull request ID
- Author information
- Commit date

Github Pull Requests are the primary code review platform presented in the dataset. Gerrit was also considered as another example of a code review platform relevant to this project.

> **Note:** The raw dataset is not included in this repo due to its size

## Data Processing and Labeling

There are multiple stages where we needed to prepare the code review comments for analysis and machine learning

### Data Processing

The original dataset is processed to identify relevant comments and reduce unnecessary duplication. Processed datasets are stored under `data/processed`

Because the original dataset is very large, the project uses memory conscious processing techniques to work with the data on a personal computer with limited memory

### Manual Validation

A manually reviewed sample was created to validate whether comments were related to software security

The manual validation dataset contains three labels:
| Label | Description |
| --- | --- |
| `0` | Not security related |
| `1` | Clearly security related |
| `2` | Possibly security related / uncertain |

Tha manually validated sample contains 600 comments

### Candidate Extraction and Weak Labeling

Additional security related candidate comments were extracted from the larger dataset and labeled using a weak labeling approach

These labels are treated as **weak labels** and are not considered equivalent to the manually validated annotations

The resulting final dataset contains **9,230 comments** with the following labels:
| Label | Description |
| --- | --- |
| `0` | Not security related |
| `1` | Clearly security related |
| `2` | Possibly security related / uncertain |

For the binary machine learning experiments, uncertain comments (`label = 2`) are excluded. The resulting binary datasets contains **9,147 comments**

## Data Analysis

The project analyzes code review comments to investigate patterns associated with security related discussions

The analysis included:
- Security label distributions
- Programming lanaguage distributions
- Feature analysis
- Classification error analysis
- Category level error analysis
- Model disagreement analysis
- Examination of comments that are difficult for models to classify

These analyses are used to better understand how security related issues appear in code review discussions and where automated classification has limitations

## Machine Learning Methodology

### Text Representation

Code review comments are converted into numerical feature representations using **TD-IDF (Term Frequency Inverse Document Frequency)**

The TD-IDF configuration uses:
- Unigrams and bigrams
- English stop-word removal
- Minimum document frequency of 2
- Maximum document frequency of 95%
- Sublinear TF scaling

### Train/Test Split

The binary dataset is divided using an **80/20 stratified train/test split**

This preserves the relative class distribution between the training and testing sets

The resulting datasets contains:
- **7,317** training comments
- **1,830** testing comments

### Classification Models

Three machine learning models were used to evaluate:
- Logistic Regression
- Linear Support Vector Machine (Linear SVM)
- Random Forest

Class weighting is used for the Logistic Regression and Linear SVM models to account for class imbalance

### Cross Validation

The models are also evaluated using **5-fold stratified cross validation**

The following metrics were used:
- Accuracy
- Balanced Accuracy
- Precision
- Recall
- F1-score

## Model Results

The final test-set results are:

| Model | Accuracy | | Balanced Accuracy | Precision | | Recall | F1-score |
| ------------- | ------------- | | ------------- | ------------- | | ------------- | ------------- |
| Linear SVM  | 97.60%  | | 96.49%  | 99.47%  | | 93.23%  | 96.25%  |
| Logistic Regression  | 97.05%  | | 95.63%  | 99.64%  | | 91.42%  | 95.35%  |
| Random Forest | 96.83%  | | 95.26%  | 99.82%  | | 90.59%  | 94.98%  |

The models are evaluated using the same test set and evaluation metrics

## Additional Experiments and Analysis

### Cross Validation

Five fold stratified cross validation was used to examine model performance across multiple training and validation splits

### Error Analysis

Misclassified comments were examined to identify patterns in false positives and false negatives

### Feature Analysis

TF-IDF features were analyzed to investigate which terms and phrases were associated with classification results

### Category Error Analysis

Classification errors were examined across different comment categories to identify areas where the models had greater difficulty

## Model Disagreement Analysis

Predictions from the three models were compared to identify comments where the models produced different predictions

This analysis provides additional insight into cases where the classification decision is less consistent across models

## Technologies
- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Jupyter Notebook