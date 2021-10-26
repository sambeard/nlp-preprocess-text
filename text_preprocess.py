import csv
import re
import text2emotion as te

START = "[START POEM]"
DELIM = "====================================="

def remove_trailing_whitespace(text):
	return "\n".join(re.findall(r"^\s*\b(.*?)\s*$", text, flags=re.MULTILINE))

def remove_excessive_newlines(text):
	return re.sub(r'[\r\n]{3}',"", text)

with open('PoetryFoundationData.csv', newline='', encoding='utf8') as csvfile:
	reader = csv.DictReader(csvfile)
	out = open("Processed_2.txt", "w")
	i = 0
	final_string = ""
	for line in reader:
		print("Working on: " + str(i))
		i += 1
		text = remove_excessive_newlines(line['Poem'])
		metadata = {}
		emotion = te.get_emotion(text)
		metadata['poet'] = line['Poet']
		metadata['emotion'] = emotion
		metadata['tags'] = line['Tags']
		metadata['title'] = remove_trailing_whitespace(remove_excessive_newlines(line['Title']))
		final_string += str(metadata)
		final_string += "\n"
		final_string += START
		final_string += "\n"
		final_string += text
		final_string += "\n\n"
		final_string += DELIM
		final_string += "\n\n"
	out.write(final_string)
	out.close()


