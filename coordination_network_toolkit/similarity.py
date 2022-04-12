import regex
from typing import Callable, Pattern
import re
import jieba


###### CHINESE-LANGUAGE TEXT PROCESSOR ######
## Chinese-language tokenizer

def chinese_tokenizers(context) -> str:
    # or thulac package
    tokenized = " ".join(list(jieba.cut(context, cut_all = True)))
    return tokenized


def chinese_social_media_cleaner(context: str):
        # ref: https://chenyuzuoo.github.io/posts/28001/
    
    # remove links
    context = re.sub("http://[a-zA-z./\d]*","",context)
    
    # remove emoji
    # ref: https://stackoverflow.com/a/58356570
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
#         u"\U00002500-\U00002BEF"  # chinese char
#         u"\U00002702-\U000027B0"
#         u"\U00002702-\U000027B0"
#         u"\U000024C2-\U0001F251"
#         u"\U0001f926-\U0001f937"
#         u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    context = re.sub(emoj,"",context)
    
    # remove hashtags
    # tags = re.findall("#(.{0,30})#",context)
    # context = re.sub("#.{0,30}#"," ",context)
    
    # extract and remove @someone (need to be fixed)
    # e.g., 1) @XX it is a good day @xx
    # e.g., 2) @XX @XXX it is a good day
    at = re.findall(r"(回复)?(//)?\s*@\S*?\s*(:| |$|：)", context)
    context = re.sub(r"(回复)?(//)?\s*@\S*?\s*(:| |$|：)"," ", context)
    at += re.findall('@[^\s]+', context)
    context = re.sub('@[^\s]+',"", context)
    
    # remove English characters
    english = re.findall("[a-z]+",context)
    context = re.sub("[a-z]+","",context)
    
    # remove puntuation
    context = re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", " ",context)
    context = re.sub("[【】╮╯▽╰╭★→「」]+"," ",context)
    context = re.sub("[！，❤。～《》：（）【】「」？”“；：、·]+"," ",context)
    
    
#     # remove space
#     context = re.sub("\s","",context)
    
    # remove digits
#     context = re.sub("\d","",context)
    
    # remove ...
    context = re.sub("\.*","",context)
    
    return context

def chinese_preprocessor(text: str):
    return chinese_tokenizers(chinese_social_media_cleaner(text))

    





#############################################








word_tokenizer = regex.compile(
    # Note this handles 'quoted' words a little weirdly: 'orange' is tokenised
    # as ["orange", "'"] I'd prefer to tokenise this as ["'", "orange", "'"]
    # but the regex library behaves weirdly. So for now phrase search for
    # quoted strings won't work.
    r"\b\p{Word_Break=WSegSpace}*'?",
    flags=regex.WORD | regex.UNICODE | regex.V1,
)


social_media_cleaner = regex.compile(
    # Find strings that start with @ (ie, mentions)
    # And grab everything from the trailing slash up to but not including the next
    # whitespace character or end of text
    r"@.*?(?=(?:\s|$))"
)


def message_preprocessor(text: str):
    """A default preprocessing function for social media strings.

    This transforms the text to make the matching process invariant to
    some non-semantic transformations.

    This default:

    - strips @mentions
    - normalises some whitespace
    - lowercases the text

    """
    return " ".join(social_media_cleaner.sub("", text.lower()).split())


def tokenize(text: str, tokenizer: Pattern = word_tokenizer) -> str:
    words = sorted(
        set(t for t in tokenizer.split(social_media_cleaner.sub("", text.lower())) if t)
    )
    tokenized = " ".join(words)

    return tokenized


def similarity(tokens_1, tokens_2):
    set_1 = set(tokens_1.split())
    set_2 = set(tokens_2.split())
    return len(set_1 & set_2) / len(set_1 | set_2)


class MinDocSizeSimilarity:
    """
    A callable class for document similarity that discards short documents.

    This is designed to avoid considering extremely short documents (such as a tweet
    containing only a single mention and hashtag) as similar in any way.

    Note that this is a callable class rather than a function to make future parallel
    processing easier.
    """

    def __init__(self, min_tokens=5):
        self.min_tokens = min_tokens

    def __call__(self, tokens_1, tokens_2) -> float:

        set_1 = set(tokens_1.split())
        if len(set_1) < self.min_tokens:
            return 0

        set_2 = set(tokens_2.split())
        if len(set_2) < self.min_tokens:
            return 0

        return len(set_1 & set_2) / len(set_1 | set_2)


def get_similarity_fn_from_min_size(min_document_size_similarity) -> Callable:
    if min_document_size_similarity > 0:
        return MinDocSizeSimilarity(min_document_size_similarity)
    else:
        return similarity
