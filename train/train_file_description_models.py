import os
import pickle
import markovify
import spacy
from gensim import corpora
from gensim.models.ldamulticore import LdaMulticore

# 配置路径和参数
CORPUS_PATH = "FileDescription.txt"
NEW_CORPUS_PATH = "NewFileDescription.txt"  # 增量训练新语料
DICT_PATH = "lda_dict.pkl"
LDA_MODEL_PATH = "lda_model.pkl"
MARKOV_MODEL_PATH = "file_description_model.json"

NUM_TOPICS = 5
NUM_PASSES = 10
NUM_WORKERS = 3
STATE_SIZE = 2

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

def preprocess_text(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]

def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def train_lda(corpus_path=CORPUS_PATH):
    with open(corpus_path, encoding="utf-8") as f:
        text = f.read()
    # 分行处理，避免只有一个长文本
    texts = [preprocess_text(line) for line in text.split("\n") if line.strip()]
    
    print(f"[DEBUG] 文档数量: {len(texts)}")
    for i, t in enumerate(texts[:3]):
        print(f"[DEBUG] 文档 {i} 词数: {len(t)} 内容示例: {t[:10]}")

    dictionary = corpora.Dictionary(texts)
    # 过滤，改成更宽松或注释掉试试
    dictionary.filter_extremes(no_below=1, no_above=1.0)
    print(f"[DEBUG] 字典大小: {len(dictionary)}")
    if len(dictionary) == 0:
        raise ValueError("字典为空，无法训练LDA。请检查语料和预处理逻辑。")

    corpus = [dictionary.doc2bow(text) for text in texts]
    if not any(len(doc) > 0 for doc in corpus):
        raise ValueError("语料BOW为空，无法训练LDA。请检查语料和预处理逻辑。")

    lda_model = LdaMulticore(
        corpus=corpus,
        id2word=dictionary,
        num_topics=NUM_TOPICS,
        passes=NUM_PASSES,
        workers=NUM_WORKERS,
        random_state=42
    )
    save_pickle(dictionary, DICT_PATH)
    save_pickle(lda_model, LDA_MODEL_PATH)
    print("[*] LDA模型训练完成并保存。")
    return lda_model, dictionary

def incremental_lda_train(new_corpus_path=NEW_CORPUS_PATH):
    if not os.path.exists(DICT_PATH) or not os.path.exists(LDA_MODEL_PATH):
        print("[!] 缺少基础LDA模型，先执行train_lda。")
        return None, None

    dictionary = pickle.load(open(DICT_PATH, "rb"))
    old_lda_model = pickle.load(open(LDA_MODEL_PATH, "rb"))

    with open(new_corpus_path, encoding="utf-8") as f:
        new_text = f.read()
    new_tokens = preprocess_text(new_text)

    dictionary.add_documents([new_tokens])
    new_corpus = [dictionary.doc2bow(new_tokens)]

    lda_model = LdaMulticore(
        corpus=new_corpus,
        id2word=dictionary,
        num_topics=old_lda_model.num_topics,
        passes=NUM_PASSES,
        workers=NUM_WORKERS,
        random_state=42
    )
    save_pickle(dictionary, DICT_PATH)
    save_pickle(lda_model, LDA_MODEL_PATH)
    print("[*] LDA模型增量训练完成并保存。")
    return lda_model, dictionary

def train_markov(corpus_path=CORPUS_PATH):
    import json
    with open(corpus_path, encoding="utf-8") as f:
        text = f.read()
    model = markovify.Text(text, state_size=STATE_SIZE)
    with open(MARKOV_MODEL_PATH, "w", encoding="utf-8") as f:
        json.dump(model.to_json(), f)
    print("[*] Markov模型训练完成并保存。")
    return model

if __name__ == "__main__":
    # 训练示范
    train_lda()
    train_markov()
    # 如需增量训练：
    # incremental_lda_train()
