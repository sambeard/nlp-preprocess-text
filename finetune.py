from consts import DELIM, TITLE
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("Going to import aitextgen")
from aitextgen import aitextgen
print("Done")

SIZES = ["124M", "335M", "774M"]
SIZE_INDEX = 0
CORPUS = "out/processed_cut.txt"

print("Loading model")
ai = aitextgen(tf_gpt2=SIZES[SIZE_INDEX], to_gpu=True)

print("Starting training")
ai.train(CORPUS,
         line_by_line=False,
         from_cache=False,
         num_steps=50000,
         generate_every=1000,
         save_every=1000,
         save_gdrive=False,
         learning_rate=1e-3,
         fp16=False,
         batch_size=1,
         )
print("Done, example generation:")

ai.generate(prompt=TITLE)
