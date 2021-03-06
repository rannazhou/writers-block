from nltk.util import tokenwrap
from nltk.corpus import wordnet as wn

from corpus import Corpus
from utils import *

NUM_WORDS_GENERATED = 50
MAX_SYNONYMS_TO_RETURN = 5
MAX_ROWS_DISPLAYED = 10


## todo: this class should prob get moved to its own file. 
class CEO(object):
    corpora = [] 
    corpora_health = []
    last_word = ''

    def __new__(cls, *args, **kwargs):
        """
        Uses class variable so that corpora are only read in once
        """
        if not cls.corpora:
            cls.load_corpora()
            cls.corpora_health = [0]*len(cls.corpora)
        return super(CEO, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def load_corpora(cls):
        """
        One-time load of the corpora specified in the config file.
        """
        print 'Loading corpora.....'
        for corpus_name, corpus in get_corpora().iteritems():
            print 'Loading.....', corpus_name
            cls.corpora.append(Corpus(corpus_name, corpus))
        
    @classmethod
    def get_corpora_names(cls):
        return [c.corpus_name for c in cls.corpora]

    @classmethod
    def get_corpora_health(cls):
        """
        Return a list of (health, corpus_name) tuples sorted with highest health first
        """
        zipped = zip(cls.get_corpora_names(), cls.corpora_health)
        zipped.sort(reverse=True, key=lambda x:x[1])
        return zipped

    @classmethod
    def grep(cls, word):
        """
        Gives word to corpora. Each corpus generates a result matrix.
        Gives result matrices to manager.... which generates a string
        """
        ## hit the corpora
        ## get token matrix from each corpus
        results = [corpus.grep(word) for corpus in cls.corpora]

        ## pass the results to the manager
        manager = GrepManager()
        string_repr = manager.process_results(results)

        ## update the last_word that was looked up
        cls.last_word = word
        return string_repr

    @staticmethod
    def synonyms(word):
        ## todo: this should move because we want to cache the results so we can calculate health!!
        results = []
        for synset in wn.synsets(word):
            results.extend(synset.lemma_names)

        result_set = set(results)        
        if word in result_set:
            result_set.remove(word)

        ### todo: stopped here... should filter these down to some reasonable thing
        ############ todo:check if the above needs to be cached somewhere (maybe it is cached by wn.synsets?)
        results = list(result_set)
        results = results[:MAX_SYNONYMS_TO_RETURN]

        return tokenwrap(results)

    @classmethod
    def generate(cls, word):
        """
        Return the text generated from the best corpus by health
        """
        ## todo: may want to use multiple corpora

        ind = cls.corpora_health.index(max(cls.corpora_health))
        return cls.corpora[ind].generate(word, NUM_WORDS_GENERATED)

##        results = [corpus.generate(word) for corpus in cls.corpora]
##        return tokenwrap(results)


    @classmethod
    def sandwich(cls, word):
        """
        """
        results = [corpus.sandwich(word) for corpus in cls.corpora]
        return tokenwrap(results)
    
    @classmethod
    def update_corpora_health(cls, word):
        """
        Given the user's new word, queries against each corpus' last returned matrix
        to see if it had offered the suggestion.

        Increments cls.corpora_health with the number of occurences
        """
        ## todo: can we generate a meaningful percentage?
        if not cls.last_word:
            return

        def count_occurences(word, matrix):
            return sum(row.count(word) for row in matrix)
    
        results = [corpus.grep(cls.last_word) for corpus in cls.corpora]
        counts = [count_occurences(word, r.matrix) for r in results]

        ## todo: this is weighted towards large corpora. we should scale this by runtime of the corpora.
        for i, count in enumerate(counts):
            cls.corpora_health[i] += count


##class SynonymsManager(object):
##    def __init__(self, num_entries):
##        self.num_entries = num_entries


class GrepManager(object):

    def __init__(self, num_entries=MAX_ROWS_DISPLAYED):
        ## maximum number of rows to return
        self.num_entries = num_entries 

    def process_results(self, results):
        ## filter results to get rows sorted by score
        matrix = GrepManager.filter_results(results, self.num_entries)
        print 'result', matrix

        ## choose a formatting function that decorates words
        formatted = GrepManager.format_matrix(matrix, color_map_rare_words) #bold_rare_words) 
        
        ## return a string result
        return GrepManager.matrix_to_str(formatted)

    @staticmethod
    def filter_results(results, num_entries):
        """
        Returns the best num_results of rows as ordered by their self-assigned rankings
        """
        rows = smush( r.matrix for r in results )
        scores = smush( r.get_scores() for r in results )

        zipped = zip(scores, rows)
        zipped.sort(reverse=True)

        ordered_rows = [row for (score, row) in zipped]

        ## return only the best num_results of rows
        if len(ordered_rows) < num_entries:
            return ordered_rows
        return ordered_rows[:num_entries]

    @staticmethod
    def format_matrix(matrix, word_format_func):
        """
        Creates a new matrix with word_format_func applied to each token in a matrix
        """
        tokens = []
        for word_list in matrix:
            row_tokens = []
            for word in word_list:
                row_tokens.append(word_format_func(word))

            tokens.append(row_tokens)
            
        return tokens
    
    @staticmethod
    def matrix_to_str(matrix):
        """
        Creates string repr of the formatted matrix if it DNE
        Returns string repr in all cases
        """
        ##TODO: this might be slow because strings are immutable
        result = ''
        for row in matrix:
#            result += tokenwrap(row) + '<br>'
            result += safe_wrap(row) + '<br>'

        return result
