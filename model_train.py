import pandas as pd
import os
import argparse
import sys
import flair
import torch

# select device
flair.device = torch.device('cuda')
# flair.device = torch.device('cpu')
# torch.cuda.empty_cache()

"""
Example use:

# to train FastText model with 2-layer biLSTM
python3 model_train.py --k_folds=5 --test_run=fasttext

# to train RoBERTa large scalar mix of 4 last layers model with 2-layer biLSTM
python3 model_train.py --k_folds=5--test_run=roberta_lstm

# to fine-tune RoBERTa large model and use CLS token output
python3 model_train.py --k_folds=5--test_run=roberta_ft --fine_tune=True
"""

parser = argparse.ArgumentParser(description='Classify data')

parser.add_argument('--k_folds', required=False, type=int, default=1)
parser.add_argument('--epochs', required=False, type=int, default=1000)
parser.add_argument('--model', required=False, type=str, default="sentiment",
                    help="sentiment or subject_category")
parser.add_argument('--block_print', required=False, default=False,
                    action='store_true', help='Block printable output')
parser.add_argument('--fine_tune', required=False, default=False,
                    action='store_true', help='Fine tune pre-trained LM')
parser.add_argument('--test_run', required=True, type=str, default='fasttext')

args = parser.parse_args()
k_folds = args.k_folds
epochs = args.epochs
model_type = str(args.model)
test_run = args.test_run
path2 = []
results_path = "./flair_training_time_results/{}".format(test_run)
fine_tune = args.fine_tune

# disable printing out
block_print = args.block_print

if block_print:
    sys.stdout = open(os.devnull, 'w')

# prepare paths for results
try:
    os.makedirs(results_path)
except FileExistsError:
    print("A test run with that name was already carried out. Try another name.")
    quit()

# prepare paths for loading data for k fold training
for i in range(k_folds):
    path2.append("./data/model_{}_{}/".format(model_type, str(i)))
    try:
        os.mkdir('./data/model_{}_{}'.format(model_type, str(i)))
    except FileExistsError:
        continue

# k folds training
for i in range(k_folds):
    # imports should be done repeatedly because of not investigated Flair issue
    import flair.datasets
    from flair.embeddings import WordEmbeddings, DocumentRNNEmbeddings, TransformerDocumentEmbeddings, RoBERTaEmbeddings
    from flair.models import TextClassifier
    from flair.trainers import ModelTrainer
    from pathlib import Path
    import torch
    from flair.data import FlairDataset

    # load training data
    corpus: flair.data.Corpus = flair.datasets.ClassificationCorpus(Path(os.path.join(path2[i])),
                                                                    test_file='test_.tsv',
                                                                    dev_file='dev.tsv',
                                                                    train_file='train.tsv'
                                                                    )

    if test_run == "fasttext":
        word_embeddings = [WordEmbeddings('en-twitter')]
    elif test_run == "roberta_lstm":
        word_embeddings = [RoBERTaEmbeddings(pretrained_model_name_or_path="roberta-large", layers="21,22,23,24",
                                             pooling_operation="first", use_scalar_mix=True)]
    else:
        print("You need to define proper model name in the code"
              " or choose from two predefined options: --test_run=fasttext or --test_run=roberta_lstm")
        break

    # Case 1: Use selected word_embeddings model fed to an RNN
    if not fine_tune:
        # define the RNN model
        document_embeddings = DocumentRNNEmbeddings(word_embeddings,
                                                    hidden_size=512,
                                                    reproject_words=True,
                                                    reproject_words_dimension=256,
                                                    rnn_type="LSTM",
                                                    bidirectional=True,
                                                    rnn_layers=2,
                                                    )

    # Case 2: fine-tune transformer model and use CLS output
    else:
        transformer_model = "roberta-large"
        document_embeddings = TransformerDocumentEmbeddings(model=transformer_model, fine_tune=True)

    # define the neural classifier
    classifier = TextClassifier(document_embeddings,
                                label_dictionary=corpus.make_label_dictionary(),
                                multi_label=False)

    # define the training regime for model+RNN
    if not fine_tune:
        # train model
        trainer = ModelTrainer(classifier, corpus)

        trainer.train(base_path="{}".format(path2[i]),
                      max_epochs=epochs,
                      learning_rate=0.1,
                      mini_batch_size=32,
                      anneal_factor=0.5,
                      patience=10,
                      embeddings_storage_mode='gpu',
                      shuffle=True,
                      min_learning_rate=0.01,
                      )

    # define the training regime for Fine-Tuning
    else:
        # train model
        trainer = ModelTrainer(classifier, corpus, optimizer=torch.optim.Adam)

        trainer.train(
            "{}".format(path2[i]),
            learning_rate=3e-5,  # low learning rate as per BERT paper
            mini_batch_size=32,  # set this high if yo have lots of data, otherwise low
            # mini_batch_chunk_size=24, # set this low if you experience memory errors
            max_epochs=4,  # very few epochs of fine-tuning
            min_learning_rate=3e-6,  # lower the min learning rate
            embeddings_storage_mode='gpu',
            shuffle=True,
        )

    # rename the model files to fit test_run case
    os.rename(src="{}best-model.pt".format(path2[i]), dst="{}{}_best-model.pt".format(path2[i], test_run))
    os.remove("{}final-model.pt".format(path2[i]))
