import csv
import time
import re
import text2emotion as te
import multiprocessing
from multiprocessing import Process, Queue, cpu_count
import sys
from phoneme_features import get_styles
import queue

MAX_LINES = 100
FORM = "Form:"
ALLITERATION = "Alliteration:"
ASSONANCE = "Assonance:"
TITLE = "Title:"
TAGS = "Tags:"
EMOTIONS = "Emotions:"
START = "Poem:"
DELIM = "====================================="

def remove_trailing_whitespace(text):
	return "\n".join(re.findall(r"^\s*\b(.*?)\s*$", text, flags=re.MULTILINE))

def remove_excessive_newlines(text):
	return re.sub(r'[\r\n]{3}',"", text)

def process_emotions(emotions):	
	emotion_to_adjective = {
		"Happy": "happy",
		"Sad": "sad",
		"Angry": "angry",
		"Surprise": "surprised",
		"Fear": "scared"
	}
	adjectives = []
	for (k,v) in emotions.items():
		if(v<0.2):
			pass
		elif (v<0.4):
			adjectives.append("{0} {1}".format("slightly", emotion_to_adjective[k]))
		elif (v < 0.6):
			adjectives.append("{0}".format(emotion_to_adjective[k]))
		else:
			adjectives.append("{0} {1}".format("very", emotion_to_adjective[k]))
	
	return ", ".join(adjectives)

def process_rhyme_score(score):
	if(score<0.1):
		return ""
	elif (score<0.3):
		return "Low"
	elif (score < 0.5):
		return "Medium"
	elif (score < 0.75):
		return "High"
	else:
		return "Very High"

def smth_or_none(txt):
	return txt if txt else "-"

def process_line(qin, qout):
	while(True):
		try:
			(i, line) = qin.get(block = False)
			if(i == -1):
				print("thread has finished")
				break			
			text = remove_excessive_newlines(line['Poem'])
			features = get_styles(text)
			lines = [
				"{0} {1}".format(TITLE,	smth_or_none(remove_trailing_whitespace(remove_excessive_newlines(line['Title'])))),
				"{0} {1}".format(FORM,	"Haiku" if features["form"]["is_haiku"] else "-"),
				"{0} {1}".format(ALLITERATION,	smth_or_none(process_rhyme_score(features["rhyme"]["alliteration"]))),
				"{0} {1}".format(ASSONANCE,	smth_or_none(process_rhyme_score(features["rhyme"]["assonance"]))),
				"{0} {1}".format(TAGS, smth_or_none(line['Tags'])),
				"{0} {1}".format(EMOTIONS, smth_or_none(process_emotions(te.get_emotion(text)))),
				START ,
				text + "\n",
				DELIM + "\n\n"
			]
			qout.put((i, "\n".join(lines)))
		except queue.Empty:
			time.sleep(.1)

def write_to_file(q, total):
	out = open("out\processed.txt", "w", encoding="utf8")
	count = 0
	while True:
		try:
			i, txt = q.get(block = False)
			count += 1
			if(count %10 == 0 and count != 0):
				sys.stdout.write("\rFinished line {0:7} of {1:7}".format(count,total))
				sys.stdout.flush()
			out.write(txt)
		except:
			if(count == total):
				print("writing thread finished")
				break
			else:
				time.sleep(.1)
	out.close()

def feed_lines(qin, nthreads):
	with open('PoetryFoundationData.csv', newline='', encoding='utf8') as csvfile:
		reader = csv.DictReader(csvfile)
		for (i,line) in enumerate(reader):
			qin.put((i,line))
		for (i) in range(nthreads):
			qin.put((-1, "stop"))

if __name__ == "__main__":
	nthreads = cpu_count()
	workerQueue = Queue()
	writerQueue = Queue()

	total = 0
	with open('PoetryFoundationData.csv', newline='', encoding='utf8') as csvfile:
		reader = csv.DictReader(csvfile)
		total = max(i for (i,line) in enumerate(reader))
	print("Will process {0} lines".format(total))
	print("============================")
	print("Starting...")

	feedProc = Process(target = feed_lines , args = (workerQueue,nthreads))
	calcProc = [Process(target = process_line , args = (workerQueue, writerQueue)) for i in range(nthreads)]
	writProc = Process(target = write_to_file, args = (writerQueue,total))


	feedProc.start()
	# wait for queue to fill
	for p in calcProc:
		p.start()
	writProc.start()

	writProc.join()
	feedProc.join()
	for p in calcProc:
		p.join()