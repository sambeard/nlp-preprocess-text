# This is best done in the interactive prompt, so you don't have to keep reloading the model
# Still, script might be nice.
from consts import TITLE

print("Going to import aitextgen")
from aitextgen import aitextgen
print("Done")

ai = aitextgen(model_folder="trained_model", to_gpu=True)

ai.generate(prompt=TITLE)
