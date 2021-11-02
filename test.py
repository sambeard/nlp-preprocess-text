from text_preprocess import process_rhyme_score, process_emotions
from phoneme_features import get_styles
import re
import text2emotion as te
import sqlite3
import os
from aitextgen import aitextgen
from consts import TITLE, DELIM

poem_regex = re.compile(r"^Poem:")
form_regex = re.compile(r"^Form: (.*)")
allit_regex = re.compile(r"^Alliteration: (.*)")
ass_regex = re.compile(r"^Assonance: (.*)")
emo_regex = re.compile(r"^Emotions: (.*)")
meter_regex = re.compile(r"^Meter: (.*)")

def get_metadata_poem(poem):
	splitted = poem.splitlines()
	re_map = {
		"text": poem_regex,
		"form": form_regex,
		"alliteration": allit_regex,
		"assonance": ass_regex,
		"emotion": emo_regex,
		"meter": meter_regex
	}
	result = {}
	done = False
	for i, line in enumerate(splitted):
		for key, reg in re_map.items():
			match = reg.match(line)
			if match:
				if key != "text":
					result[key] = match.group(1)
					re_map.pop(key)
					break
				else:
					result["text"] = "\n".join(splitted[i:])
					re_map.pop(key)
					done = True
					break
	if "text" not in result or not result["text"]:
		result["text"] = "\n".join(splitted)
	result['rhyme'] = {
		"alliteration": result['alliteration'] if "alliteration" in result else "",
		"assonance": result['assonance'] if "assonance" in result else ""
	}
	required = ['emotion', 'form', 'meter']
	for req in required:
		if req not in result:
			result[req] = None
	return result

def get_test_metadata(poem_text):
	styles = get_styles(poem_text)
	emotion = process_emotions(te.get_emotion(poem_text))
	alliteration = process_rhyme_score(styles['rhyme']['alliteration'])
	assonance = process_rhyme_score(styles['rhyme']['assonance'])
	return {
		"styles": styles,
		"emotion": emotion,
		"alliteration": alliteration,
		"assonance": assonance
	}

def test_emotion(gen, test):
	if not gen:
		return None
	split_gen = gen.split(",")
	split_test = test.split(",")
	total_gen = len(split_gen)
	total_test = len(split_test)
	gen_set = set()
	test_set = set()
	for emo in split_gen:
		gen_set.add(emo.strip())
	for emo in split_test:
		test_set.add(emo.strip())
	union = gen_set.union(test_set)
	sect = gen_set.intersection(test_set)
	if len(union) == total_test:
		return 1.0 # 100% of the generated set is correct
	counter = 0
	for item in union:
		if item not in sect:
			counter += 1
	return counter / total_gen # x out of y of the generated set is correct

def test_meter(gen, test):
	if not gen:
		return None
	if gen.strip() == "-":
		gen_style = None
		gen_count = None
	else:
		gen_style, gen_count = gen.split(" ")
	if not test or test.strip() == "-":
		test_style = None
		test_count = None
	else:
		test_style, test_count = test.split(" ")
	style_val = 1.0 if gen_style == test_style else 0.0 # This could be expanded into how far off it got
	count_val = 1.0 if gen_count == test_count else 0.0
	return {
		"style": style_val,
		"count": count_val,
		"avg": (style_val + count_val) / 2
	}

def test_form(gen, test):
	if not gen:
		return None
	return 1.0 if (gen == "Haiku" and test['is_haiku']) or (gen == "-" and not test['is_haiku']) else 0.0

def test_assonance(gen, test):
	if not gen:
		return None
	return 1.0 if gen == test else 0.0 # This could be expanded for better values

def test_alliteration(gen, test):
	if not gen:
		return None
	return 1.0 if gen == test else 0.0

def test_poem(poem):
	gen_metadata = get_metadata_poem(poem)
	test_metadata = get_test_metadata(gen_metadata['text'])
	results = {
		'emotion': test_emotion(gen_metadata['emotion'], test_metadata['emotion']),
		'meter': test_meter(gen_metadata['meter'], test_metadata['styles']['meter']['main']),
		'form': test_form(gen_metadata['form'], test_metadata['styles']['form']),
		'assonance': test_assonance(gen_metadata['rhyme']['assonance'], test_metadata['assonance']),
		'alliteration': test_alliteration(gen_metadata['rhyme']['alliteration'], test_metadata['alliteration'])
	}
	count = 0
	for key, value in results.items():
		if value:
			if key == 'meter':
				count += value['avg']
			else:
				count += value
	results['total'] = count / 5
	return results

def store_result(conn, results):
	cur = conn.cursor()
	sql = '''INSERT INTO results (total, emotion, meter, form, assonance, alliteration) VALUES (?, ?, ?, ?, ?, ?)'''
	values = [
		results['total'],
		results['emotion'],
		results['meter'] if not results['meter'] else results['meter']['avg'],
		results['form'],
		results['assonance'],
		results['alliteration']
	]
	cur.execute(sql, values)
	conn.commit()

def create_conn(path="results.db"):
	conn = sqlite3.connect(path)
	if not os.path.isfile(path):
		curr = conn.cursor()
		curr.execute("""CREATE TABLE results (id INTEGER PRIMARY KEY,
			total INTEGER NOT NULL,
			emotion REAL,
			meter REAL,
			form REAL,
			assonance REAL,
			alliteration REAL);
			""")
		conn.commit()
	return conn



def run_tests(n=10000, batch=100, conn=None):
	print("Loading model")
	ai = aitextgen(model_folder="trained_model", to_gpu=True)
	tmpfile = "tmp.file"
	print("Starting generation")
	ai.generate_to_file(n=n, batch_size=batch, destination_path=tmpfile, sample_delim=DELIM, prompt=TITLE)
	print("Done generating")
	data = ""
	with open(tmpfile, "r") as f:
		data = f.read()
	poems = data.split(DELIM)
	results = []
	for poem in poems:
		if poem:
			result = test_poem(poem)
			results.append(result)
			if conn:
				store_result(conn, result)

if __name__ == '__main__':
	conn = create_conn()
	run_tests(conn=conn)
	conn.close()