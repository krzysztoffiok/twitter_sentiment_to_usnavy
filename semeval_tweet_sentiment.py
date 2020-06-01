import pandas as pd
import numpy as np
from sklearn.metrics import classification_report
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.naive_bayes import BernoulliNB, GaussianNB
import sklearn
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
import xgboost as xgb
import random
import shap
import datatable as dt
import argparse
import _utils
import matplotlib.pyplot as plt


"""
Machine Learning based on previously extracted features. Example use:
python3 semeval_tweet_sentiment.py

For SHAP model explenations:
python3 semeval_tweet_sentiment.py --shap=SEANCE
"""

parser = argparse.ArgumentParser(description='Classify data')
parser.add_argument('--fold', required=False, type=int, default=0)
parser.add_argument('--shap', required=False, default=None, help='If argument is passed, SHAP explanations for'
                                                                 ' a selected LM will be computed. Possible values'
                                                                 'include e.g. SEANCE, LIWC, Term Frequency')
parser.add_argument('--samples', required=False, type=int, default=200,
                    help="number of samples of data to explain by SHAP")
parser.add_argument('--estimators', required=False, type=int, default=250,
                    help="number of estimators in machine learning classification models")

args = parser.parse_args()
_fold = args.fold
_shap = args.shap
_estimators = args.estimators
_shap_samples = args.samples

# choose the dataset
dataset = "semeval"

# <H1> Preparing data split: 5 fold cross validation </H1>
# <h3> The procedure is identical as when splitting data for the purpose of training selected Language Models

# read original data file
if dataset == "semeval":
    df_semtest = dt.fread("./semeval_data/source_data/semtest.csv").to_pandas()
    df_semtrain = dt.fread("./semeval_data/source_data/semtrain.csv").to_pandas()  
    df = pd.concat([df_semtrain, df_semtest], ignore_index=True)

# define number of folds
fold_number = 5

# create data splits for Deep Learning Language Models trained with Flair framework
train_indexes = {}
test_indexes = {}

# train sets for Machine Learning
train_ml = {}
test_ml = {}
i = 0

# Since in SEMEVAL only a single train and test split were given, the five fold cross validation
# is carried out only when training split i divided into train and val for Flair and training
# of DL models. Here, we repeat 5 times the same train and test splits, however DL models for each
# fold were previously separately trained.
indexes = list(range(0, len(df)))
for fold in range(fold_number):
    # first 6000 rows are training instances, rest is for testing. The difference in folds comes from
    # different train/val splits when DL trainable models were concerned
    test_ml[i] = df[6000:].index
    train_ml[i] = df[:6000].index
    i += 1


# <h1>Reading data: tweets encoded by various Language Models
# <h3> Linguistic Inquiry and Word Count (LIWC) feature file
dfliwctrain = dt.fread(f"./{dataset}_data/embeddings/LIWC2015_semeval_train.csv").to_pandas()
dfliwctest = dt.fread(f"./{dataset}_data/embeddings/LIWC2015_semeval_test.csv").to_pandas()
dfliwc = pd.concat([dfliwctrain, dfliwctest], ignore_index=True)

# rename columns to get unique names
dfliwc.rename(columns={'C': 'text_liwc', "B": 'liwc_sent'}, inplace=True)

# define LIWC features names
liwcfeatures = ['WC', 'Analytic', 'Clout', 'Authentic', 'Tone', 'WPS', 'Sixltr', 'Dic', 'function', 'pronoun', 'ppron',
                'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'auxverb', 'adverb', 'conj', 'negate',
                'verb', 'adj', 'compare', 'interrog', 'number', 'quant', 'affect', 'posemo', 'negemo', 'anx', 'anger',
                'sad', 'social', 'family', 'friend', 'female', 'male', 'cogproc', 'insight', 'cause', 'discrep',
                'tentat', 'certain', 'differ', 'percept', 'see', 'hear', 'feel', 'bio', 'body', 'health', 'sexual',
                'ingest', 'drives', 'affiliation', 'achieve', 'power', 'reward', 'risk', 'focuspast', 'focuspresent',
                'focusfuture', 'relativ', 'motion', 'space', 'time', 'work', 'leisure', 'home', 'money', 'relig',
                'death', 'informal', 'swear', 'netspeak', 'assent', 'nonflu', 'filler', 'AllPunc', 'Period', 'Comma',
                'Colon', 'SemiC', 'QMark', 'Exclam', 'Dash', 'Quote', 'Apostro', 'Parenth', 'OtherP']

# <h3> Sentiment Analysis and Cognition Engine (SEANCE) feature file
# read SEANCE features
seance_train = dt.fread(f"./{dataset}_data/embeddings/seance_semeval_train.csv").to_pandas()
seance_train = seance_train.sort_values(["filename"])
seance_test = dt.fread(f"./{dataset}_data/embeddings/seance_semeval_test.csv").to_pandas()
seance_test = seance_test.sort_values(["filename"])
dfseance = pd.concat([seance_train, seance_test], ignore_index=True)

dfseance.drop(["filename"], axis=1, inplace=True)
# create a list of seance features
seancefeatures = dfseance.columns.to_list()
# make seance feature names unique
seancefeatures = [f"S_{x}" for x in seancefeatures]
dfseance.columns = seancefeatures
dfseance.index = [x for x in range(len(dfseance))]

# <h3> Vector representations (embeddings) created by selected Deep Learning Language Models trained previously
# on here addressed task
# define which embedding files to read
embeddings = [("FastText_lstm", "fasttext"), ("Roberta_lstm", "roberta_lstm"), ("Roberta_CLS", "roberta_ft")]

# instantiate list of data frames with features and a list of feature names for each df
dfemblist = []

# Initialize a dictionary with all features used later on in Machine Learning
allFeatures = {}

# read embedding files and define corresponding feature names (lists of names)
for emname, embedding in embeddings:
    embfeaturedict = {}
    for fold in range(fold_number):
        # read encoded sentences by the selected language model
        train = dt.fread(f"./{dataset}_data/embeddings/{embedding}_encoded_sentences_{fold}train.csv").\
            to_pandas()
        test = dt.fread(f"./{dataset}_data/embeddings/{embedding}_encoded_sentences_{fold}test.csv").\
            to_pandas()
        dfemb = pd.concat([train, test], ignore_index=True)

        embfeatures = [f"{emname}{fold}row"]

        # define number of feature columns (columns - 3)
        number_of_feature_columns = len(dfemb.columns) - 3

        # create unique feature (column) names
        embfeatures.extend([f"{emname}{fold}{x}" for x in range(number_of_feature_columns)])
        embfeatures.extend([f"{emname}{fold}_sentiment_", f"{emname}{fold}_dummy_id_"])
        dfemb.columns = embfeatures

        # append features from each language model in tuple ((model_name,fold), [features])
        embfeaturedict[fold] = [f"{emname}{fold}{x}" for x in range(number_of_feature_columns)]

        # append encoded sentences by the selected language model to a list of data frames
        dfemblist.append(dfemb)

    # create entry in dictionary with all features for each trained language model
    allFeatures[emname] = embfeaturedict


# <h3> Vector representations (embeddings) created by selected pre-trained Deep Learning Language Models.
# No special training was carried out for here addressed task
# read pooled embeddings and Universal Sentence Encoder (USE) embeddings
pooled_embeddings = [["Pooled FastText", "fasttext"], ["Pooled RoBERTa", "roberta"],
                     ["Universal Sentence Encoder", "USE"]]

for emname, embedding in pooled_embeddings:
    # two options due to naming convention
    if emname != "Universal Sentence Encoder":
        train = dt.fread(f"./{dataset}_data/embeddings/{embedding}_encoded_sentences_pooledtrain.csv").to_pandas()
        test = dt.fread(f"./{dataset}_data/embeddings/{embedding}_encoded_sentences_pooledtest.csv").to_pandas()
    else:
        train = dt.fread(f"./{dataset}_data/embeddings/USE_encoded_sentencestrain.csv").to_pandas()
        test = dt.fread(f"./{dataset}_data/embeddings/USE_encoded_sentencestest.csv").to_pandas()
    dfemb = pd.concat([train, test], ignore_index=True)

    embfeatures = [f"{emname}row"]

    # define number of feature columns (columns - 3)
    number_of_feature_columns = len(dfemb.columns) - 3

    # create unique feature (column) names
    embfeatures.extend([f"{emname}{x}" for x in range(number_of_feature_columns)])
    embfeatures.extend([f"{emname}_sentiment_", f"{emname}_dummy_id_"])
    dfemb.columns = embfeatures

    # add features from each fold to a local dictionary
    embfeaturedict = {}
    for fold in range(fold_number):
        embfeaturedict[fold] = [f"{emname}{x}" for x in range(number_of_feature_columns)]

    # append encoded sentences by the selected language model to a list of data frames
    dfemblist.append(dfemb)

    # create entry in dictionary with all features for each language model
    allFeatures[emname] = embfeaturedict

# <h3> Vector representations (embeddings) created by Term Frequency Language Model
# Create a per-fold feature dictionary for Term Frequency model
dftf, allFeatures = _utils.term_frequency(train_ml=train_ml, dfliwc=dfliwc, df=df, allFeatures=allFeatures)

# Create per-fold feature dictionary for LIWC model.
foldLIWCfeatures = {}
for fold, rows in train_ml.items():
    foldLIWCfeatures[fold] = liwcfeatures.copy()

# add the LIWC language model key to dictionary with allFeatures from various language models
allFeatures["LIWC"] = foldLIWCfeatures

# Create per-fold feature dictionary for SEANCE model.
foldSEANCEfeatures = {}
for fold, rows in train_ml.items():
    foldSEANCEfeatures[fold] = seancefeatures.copy()

# add the SEANCE language model key to dictionary with allFeatures from various language models
allFeatures["SEANCE"] = foldSEANCEfeatures

# concat all Data Frames: liwc, TF, DL embedding into one df_ml that will be used in Machine Learning
dftemp = pd.concat([dfliwc, dftf, dfseance], axis=1)
for dfemb in dfemblist:
    dftemp = pd.concat([dftemp, dfemb], axis=1)
df_ml = dftemp

# define the target variable in the final df_ml data frame
df_ml["target_ml"] = df["sentiment"]

# <h1> Machine Learning part
# Define separate lists of names of trained and not trained language models that can be tested
all_language_models = ["Term Frequency", "LIWC", "SEANCE", "Pooled FastText", "Pooled RoBERTa",
                       "Universal Sentence Encoder", "FastText_lstm", "Roberta_lstm", "Roberta_CLS"]

if _shap is None:

    # instantiate dictionary for data frames with results
    allPreds = {}
    allTrues = {}

    # define which classification models to use
    models = [xgb.XGBClassifier(objective='multi:softprob', n_jobs=24, learning_rate=0.03, max_depth=10, subsample=0.7,
                                colsample_bytree=0.6, random_state=2020, n_estimators=_estimators,
                                tree_method='gpu_hist')]

    # use features from selected language models
    for language_model in all_language_models:
        # for training of selected classification models
        for classification_model in models:
            preds, trues = _utils.ML_classification(allFeatures=allFeatures, train_ml=train_ml, test_ml=test_ml,
                                                    df_ml=df_ml, classification_model=classification_model,
                                                    language_model=language_model, fold_number=fold_number)

            # save model predictions
            allPreds[f"{language_model}_{type(classification_model).__name__}"] = preds.copy()
            allTrues[f"{language_model}_{type(classification_model).__name__}"] = trues.copy()

    # save model predictions together with true sentiment labels
    pd.DataFrame(allPreds).to_csv(f"./{dataset}_data/predictions.csv")
    pd.DataFrame(allTrues).to_csv(f"./{dataset}_data/trues.csv")

    _utils.compute_metrics(dataset=dataset)

else:

    # prepare model for SHAP explanations
    shap_model, train_data, test_data = _utils.train_model_for_shap(allFeatures=allFeatures, train_ml=train_ml,
                                                                    test_ml=test_ml, df_ml=df_ml, classification_model=
                                                                    xgb.XGBClassifier(objective='multi:softprob',
                                                                                      n_jobs=24, learning_rate=0.03,
                                                                                      max_depth=10, subsample=0.7,
                                                                                      colsample_bytree=0.6,
                                                                                      random_state=2020,
                                                                                      n_estimators=_estimators,
                                                                                      tree_method='gpu_hist'),
                                                                    language_model=_shap, fold=_fold)

    fig = _utils.explain_model(model=shap_model, train_data=train_data, test_data=test_data, samples=_shap_samples)
    plt.savefig(f'./results/{dataset}_{_shap}_{_fold}_{_estimators}_summary_plot.png')
