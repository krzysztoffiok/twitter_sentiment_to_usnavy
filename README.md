# Analysis of Twitter sentiment with various Language Models on narrow-scope data
This repository contains data, code and results for fine-grained sentiment analysis of tweets sent to @USNavy account

*"Analysis of sentiment in tweets sent to @USNavy account: comparison of model performance and explainability of predictions"*

Authors: Krzysztof Fiok1, Maciej Wilamowski2, Edgar Gutierrez-Franco1 and Waldemar Karwowski1


1 University of Central Florida, Department of Industrial Engineering & Management Systems, Orlando, Florida, USA </br>
2 University of Warsaw, Faculty of Economic Sciences, Warsaw, Poland
<br/>


The whole repository is published under MIT License (please refer to the [License file](https://github.com/krzysztoffiok/twitter_sentiment_to_usnavy/blob/master/LICENSE)).

In due course full description of usage will appear here.

The code is written in Python3 and requires GPU computing machine for achieving reasonable performance.

## Try how it works in google colaboratory:

[Train your own Deep Learning Language Models and embed our tweets in Google colaboratory](https://colab.research.google.com/drive/1K-XQJnauYvULdwUO3vELy9dJ1DHR_53b) </br>
Select the runtime type Python3 with GPU acceleration for reasonable performance.

[Carry out Machine Learning classification of sentiment in Google colaboratory](https://colab.research.google.com/drive/151uxuOLgsxHDravuN_9k_whn8imC-0dg) </br>
For this part CPU runtime is sufficient.

If you wish to try our code locally:
## Installation:
Please clone this repository and extract zipped files.

## How the code works:
You start with a labeled data set of 5000 tweets sent to @USNavy account. There are 5 sentiment classes (0-very negative, 1-negative, 2-neutral, 3-positive, 4-very positive).
1) In order to carry out classification, you need to train Language Models on the provided data. Preparing 5-fold cross validated data splits is carried out in Google Colaboratory in the first notebook or if you run locally, in Flair_data_splitter.ipynb (jupyter notebook). It creates proper directories and files.
2) For training of Deep Learning Language Models(DLLMs) we utilize [Flair](https://github.com/flairNLP/flair). Again, this is carried out in the first notebook in Google Colaboratory or if you run locally you need to execute model_train.py according to instructions provided in the very same script. For this stage, GPU is definitely required.
3) After training DLLMs it is time to use them to convert tweet texts into vector representations (embeddings). This is carried out again in the first notebook in Google Colaboratory or if you run locally you need to execute embed_sentences_flair.py according to instructions provided in the very same script. For this stage CPU is enough. Apart from models trained with Flair, we also create Universal Sentence Encoder embeddings which will run both with or without GPU.
4) Once the tweet texts are converted to embeddings Machine Learning classification can be carried out. The 2nd notebook on Google Colaboratory will be in use here or if you run locally please use tweet_sentiment.ipynb (jupyter notebook). Before the actuall Machine Learning classification is done, un the same scripts we also compute vectors by means of simple Term Frequency modelling. In the repo we also provided Linguistic Inquiery and Word Count (LIWC) features computed for all analyzed tweets. Once the selected classification models are trained it is also possible to visualize explanations of model predictions. This is carried out as well in the same scripts used to carry our Machine Learning classification.

## Citation:<br/>
If you decide to use here published code or our dataset please cite our work in the following manner:
(please contact us directly at this time since the paper is still in preparation).

