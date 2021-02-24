import random, nltk
import pandas as pd
import small_talk_config as config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
#from sklearn.svm import LinearSVC, SVC

stats = {'intent': 0, 'my': 0, 'generativ': 0, 'fails': 0}
log_file_name = 'small_talk_log.txt'

def log(file_name, text):
    log_file = open(file_name, 'a')
    log_file.write(text+'\n')
    log_file.close()

## by intent
def clear_text(text):
    text = text.lower()
    alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789- '
    result = ''
    for c in text:
        if c in alphabet:
            result += c
    return result

dataset = []

for intent, intent_data in config.BOT_CONFIG['intents'].items():
    for example in intent_data['examples']:
        example = clear_text(example)
        intent = intent.lower()
        if example:
            if([example, intent] not in dataset):
                dataset.append([example, intent])

corpus = [text for text, intent in dataset]
y = [intent for text, intent in dataset]

#vectorizer = TfidfVectorizer(analyzer = 'word')
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 3))
X = vectorizer.fit_transform(corpus)

#clf = LinearSVC()
#clf = SVC(probability=True)
clf = LogisticRegression()
clf.fit(X, y)
#print(clf.score(X, y))

def get_intent(text):
    text = clear_text(text)
    proba_list = clf.predict_proba(vectorizer.transform([text]))[0]
    max_proba = max(proba_list)
    max_index = list(proba_list).index(max_proba)
    #print(text, proba_list, clf.classes_, max_proba, proba_list.mean(), proba_list.mean()/max_proba, clf.classes_[max_index])
    log(log_file_name, 'text: {}, max_proba: {}, mean_proba: {}, rel: {}, intent: {}'.format(text, max_proba, proba_list.mean(), proba_list.mean()/max_proba, clf.classes_[max_index]))

    if (proba_list.mean()/max_proba < 0.2)&(max_proba > 0.05):
        #print(clf.classes_[max_index])
        return clf.classes_[max_index]
    
def get_responce_by_intent(intent):
    return random.choice(config.BOT_CONFIG['intents'][intent]['responses'])

## generatively
with open('dialogues.txt') as f:
    content = f.read()

blocks = content.split('\n\n')

dataset = []
questions = set()

for block in blocks:
    replicas = block.split('\n')[:2]
    if len(replicas) == 2:
        question = clear_text(replicas[0][2:])
        answer = replicas[1][2:]
        
        if question and answer and question not in questions:
            questions.add(question)
            dataset.append([question, answer])

search_dataset = {}
for question, answer in dataset:
    words = question.split(' ')
    for word in words:
        if word not in search_dataset:
            search_dataset[word] = []
        search_dataset[word].append([question, answer])

search_dataset = {
    word: word_dataset
    for word, word_dataset in search_dataset.items()
    if len(word_dataset) < 5000
}


def get_responce_generatively(text):
    text = clear_text(text)
    if not text:
        return
    words = text.split(' ')
    
    words_dataset = []
    for word in words:
        if word in search_dataset:
            words_dataset += search_dataset[word]

    scores = []
    
    for question, answer in words_dataset:
        if abs(len(text) - len(question))/len(question) < 0.35:
            distance = nltk.edit_distance(text, question)
            score = distance/len(question)
            if score < 0.35:
                log(log_file_name, 'text: {}, score: {}, question: {}, answer :{}'.format(text, score, question, answer))
                #print(score, question, answer)
                scores.append([score, question, answer])
                
    if scores:
        scores.sort(key = lambda s: s[0])
        return random.choice(scores[:5])[2]


##
def get_failure_phrase():
    return random.choice(config.BOT_CONFIG['failure_phrases'])

##
def get_responce(request):

    # NLU
    intent = get_intent(request)
    
    # Генерация ответа
    if intent:
        stats['intent'] += 1
        log(log_file_name, str(stats))
        return get_responce_by_intent(intent)

    response = get_responce_generatively(request)
    if response:
        stats['generativ'] += 1
        log(log_file_name, str(stats))
        return response

    stats['fails'] += 1
    log(log_file_name, str(stats))

    return get_failure_phrase()