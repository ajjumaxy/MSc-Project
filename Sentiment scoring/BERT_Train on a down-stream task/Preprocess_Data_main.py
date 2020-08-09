# import libraries and settings
from argparse import ArgumentParser
import pandas as pd
import torch
import transformers
from transformers import BertTokenizer

from Preprocess_Data import PrepareData

# parameters
parser = ArgumentParser()

parser.add_argument(
    '--pretrained_model_name',
    default='bert-base-cased'
)
parser.add_argument(
    '--data_path',
    default='/mnt/c/Data/UCL/@MSc Project - Data and sources/Sentiment training/train.csv'
)
parser.add_argument(
    '--torch_path',
    default='/mnt/c/Data/UCL/@MSc Project - Data and sources/Sentiment training/'
)
parser.add_argument(
    '--columns',
    default='positives | negatives | overall'
)

args = parser.parse_args()
args.columns = [column.strip() for column in args.columns.split('|')]


def main():
    data_loader = PrepareData(args.pretrained_model_name)
    data_loader.run(args.data_path, args.columns, args.torch_path)

if __name__=='__main__':
    main()