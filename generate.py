# This is best done in the interactive prompt, so you don't have to keep reloading the model
# Still, script might be nice.
from consts import TITLE
try:
	import readline
except:
	pass

print("Going to import aitextgen")
from aitextgen import aitextgen
print("Done")

print("Loading model")
ai = aitextgen(model_folder="trained_model", to_gpu=True)
print("Done")

msg = """
Please give a number. Additional args are added with a space
Please choose one of the following options:
1. Generate (no prompt)
2. Generate ('Title:' prompt)
3. Generate with Title (needs args)
4. Generate with prompt (needs args)
5. Generate with previous prompt
6. Save previous
9. Show this prompt again
0. Quit
"""

def save_prev(prev):
	if not prev:
		print("Nothing was generated yet")
		return
	DELIM = "================="
	print("Saving...")
	out = open("interesting_results", "a")
	out.write(DELIM)
	out.write("\n\n")
	out.write(prev)
	if prev[-1] != "\n":
		out.write("\n")
		if prev[-2] != "\n":
			out.write("\n")
	out.close()
	print("Saved")

done = False
prev_args = ""
prev = ""
print(msg)
while not done:
	choice = input("> ").strip()
	num = choice[0]
	args = ""
	if len(choice) > 1:
		args = choice[1:]
		prev_args = args
	if num == "1":
		prev = ai.generate_one()
	if num == "2":
		prev = ai.generate_one(prompt=TITLE)
	if num == "3":
		prompt = TITLE + args + "\n"
		prev = ai.generate_one(prompt=prompt)
	if num == "4":
		prev = ai.generate_one(prompt=args)
	if num == "5":
		prev = ai.generate_one(prompt=prev_args)
	if num == "6":
		save_prev(prev)
		prev = ""
	if num == "9":
		print(msg)
	if num == "0":
		print("Goodbye")
		break
	if prev:
		print(prev)
