import random
import pickle

def build_char_markov_chain(data, order=2):
    chain = {}
    for name in data:
        name = '^' * order + name.lower() + '$'
        for i in range(len(name) - order):
            current_state = name[i:i+order]
            next_char = name[i+order]
            if current_state not in chain:
                chain[current_state] = {}
            chain[current_state][next_char] = chain[current_state].get(next_char, 0) + 1
    return chain

def build_word_markov_chain(data):
    chain = {}
    for words in data:
        for i in range(len(words)):
            current = words[i]
            next_word = words[i + 1] if i + 1 < len(words) else '$'
            if current not in chain:
                chain[current] = {}
            chain[current][next_word] = chain[current].get(next_word, 0) + 1
    return chain

# 读取公司名列表（或用默认）
try:
    with open('tech_company_names.txt', encoding="utf-8") as f:
        tech_company_names = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    tech_company_names = [
        "Google", "Microsoft", "Amazon", "Apple", "Tesla", "Facebook", "IBM",
        "Intel", "Oracle", "Cisco", "Nvidia", "Adobe", "Salesforce", "Netflix",
        "Airbnb", "Uber", "Lyft", "SpaceX", "PayPal", "Twitter", "Snapchat",
        "Zoom", "Stripe", "Slack", "Palantir", "Atlassian", "Square", "Robinhood",
        "Asana", "Epicor", "Shopify", "Datadog", "Snowflake", "Cloudflare", "Twilio"
    ]

# 词级马尔可夫链示例数据
word_pairs = [
    ['Cloud', 'flare'], ['Snow', 'flake'], ['Data', 'dog'], ['Bright', 'Labs'],
    ['Quantum', 'Ventures'], ['Nex', 'Gen'], ['Tech', 'Analytics'], ['Future', 'Systems']
]

# 构建模型
char_markov_chain = build_char_markov_chain(tech_company_names, order=2)
word_markov_chain = build_word_markov_chain(word_pairs)

# 保存模型到文件
with open('char_company.pkl', 'wb') as f:
    pickle.dump(char_markov_chain, f)

with open('word_company.pkl', 'wb') as f:
    pickle.dump(word_markov_chain, f)

print("模型已保存！")
