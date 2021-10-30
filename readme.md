# Poetry Generation with GPT-2

Code to generate the General Poetry Transformer designed for our final NLP project.

## Install

Install the required libraries with `pip install -r requirements.txt`. If you want to use your NVidia GPU for training, make sure CUDA is installed (see tenserflow documentation for more info).

## Used Libraries

- `aitextgen` (https://github.com/minimaxir/aitextgen)
- `text2emotion` (https://github.com/aman2656/text2emotion-library)
- `pronouncing` (https://pypi.org/project/pronouncing/)
- `prosodic` (https://github.com/quadrismegistus/prosodic)

## Dataset
Data set was acquired from: https://www.kaggle.com/tgdivy/poetry-foundation-poems

### Preprocessing

To preprocess the dataset, run the `text_preprocess.py` script. It will create an output file in `./out/processed.txt` which will have the preprocessed data.

### Training the Model

After having preprocessed the dataset, run `finetune.py` to train the model. This will take a while and may require a lot of ram (up to 88GB). It is recommended to do this on a \*Nix system so you can use SWAP.

### Generating Poems

Once you have a trained model, you can run the `generate.py` script to start an interactive prompt to easily generate poems.

## Poetry Analysis

As part of the preprocessing, we created a number of functions to analyze the poems. These functions are found in `phoneme_features.py` and may prove interesting outside of the scope of this project. Feel free to have a look.

