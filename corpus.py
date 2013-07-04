import os
import itertools
import nltk
from nltk.util import tokenwrap
from nltk.corpus import wordnet as wn

from nltk_custom import CorpusText
from utils import *
from config import *

def format_matrix(matrix):
    def invis(x):
        ## might want to approach whitespace alternatively
        ## http://www.qtcentre.org/threads/27245-Printing-white-spaces-in-QPlainTextEdit-the-QtCreator-way
        return '&nbsp;'*len(x)

    def bold(x):
        return '<b>' + x + '</b>'

    def identity(x):
        return x

    tokens = []
    for word_list in matrix:

        row_tokens = []
        dist = get_dist_in_english(word_list)
        for word in word_list:
            if word.isalpha() and is_rare_by_threshold(word):
                row_tokens.append(bold(word))
            else:
                row_tokens.append(identity(word))

        tokens.append(row_tokens)
    return tokens

def matrix_to_str(matrix):
    formatted = format_matrix(matrix)
    
    result = ''
    for row in formatted:
        result += tokenwrap(row) + '\n'
    return result


## this shoudl eat format_matrix
## should eat matrix_to_str
class Display(object):
    ## get a matrix

    ## apply filters

    ## apply formatting

    ## return string
    pass
        
class Library(object):
    corpora = []

    def __new__(cls, *args, **kwargs):
        if not cls.corpora:
            cls.load_corpora()
        return super(Library, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def load_corpora(cls):
        print 'Loading corpora.....'
        for corpus_name, corpus in CORPORA.iteritems():
            print 'Loading.....', corpus_name
            cls.corpora.append(Corpus(corpus_name, corpus))
    
    @classmethod
    def word_lookup(cls, word):
        return cls.hit_corpora('word_lookup', word)
    
    @classmethod
    def related_words(cls, word):
        return cls.hit_corpora('related_words', word)

    @classmethod
    def hit_corpora(cls, corpus_func, word):
        all_matches = []
        for corpus in cls.get_health()[:MAX_CORPORA]:

            func = getattr(corpus, corpus_func)
            corpus_rec = func(word)
            if corpus_rec:
                all_matches.append(corpus_rec)
        
        return ''.join(x+'\n' for x in all_matches)


    @classmethod
    def get_health(cls):
        return sorted([corpus for corpus in cls.corpora],
                          reverse=True,
                          key = lambda x:x.get_health())

    @classmethod
    def __str__(cls):
        return ''.join(str(corpus)+' ' for corpus in cls.corpora)

    @staticmethod
    def synonyms(word):
        ## to-do: maybe this should not be in Library
        results = []
        for synset in wn.synsets(word):
            results.extend(synset.lemma_names)

        result_set = set(results)        

        if word in result_set:
            result_set.remove(word)

        return tokenwrap(result_set)

    
class Corpus(object):

    def __init__(self, corpus_name, corpus):
        self.corpus_name = corpus_name
        self.text = self.load_corpus(corpus)
        self.last_rec = ''
        self.health = []

        ##build indices before the gui renders
        self.text.concordance('blah')
        self.text.similar('blah')
        
    def load_corpus(self, corpus):
        tokens = self.corpus_to_tokens(corpus)
        return CorpusText(tokens)

    def corpus_to_tokens(self, corpus):
        ## this is sketchy.... fix this
        if isinstance(corpus, str):
            with open(os.path.join(CORPORA_FOLDER, corpus), 'r') as f:
                raw = f.read()
                tokens = nltk.wordpunct_tokenize(raw)
        elif isinstance(corpus, nltk.corpus.reader.util.ConcatenatedCorpusView):
            tokens = list(itertools.chain(*corpus))
        elif isinstance(corpus, nltk.corpus.reader.util.StreamBackedCorpusView):
            tokens = corpus
        else:
            raise NotImplemented
        return tokens
    
    def update_health(self, word):
        if word.lower() in self.last_rec.lower():
            self.health.append(word) ## +health for having it in the recommendation
        else:
            self.health.append(None)
    
    def word_lookup(self, word):
        self.update_health(word)
        
        neighbors = self.text.get_adjacent_tokens(word)
        rec = matrix_to_str(neighbors)
        
        if rec:
            self.last_rec = rec
            self.health.append(word) ## +health for having it in the corpus
        else:
            self.health.append(None)
        return rec        

    def get_health(self):
        return 1 - self.health.count(None) / float(len(self.health) + 1)
        
    def related_words(self, word):
        return self.text.similar(word)

    def generate(self, context=[]):
        """
        context := list of strings of nearby context upon which to generate
                    e.g ['Mighty', 'fine', 'day', 'we', 'have', 'here']
        """
        return self.text.generate(context=context)

    def __str__(self):
        return self.corpus_name
