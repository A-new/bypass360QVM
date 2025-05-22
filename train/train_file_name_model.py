import pickle

def build_char_markov_chain(data, order=3):
    chain = {}
    for name in data:
        padded_name = '^' * order + name.lower() + '$'
        for i in range(len(padded_name) - order):
            state = padded_name[i:i+order]
            next_char = padded_name[i+order]
            if state not in chain:
                chain[state] = {}
            chain[state][next_char] = chain[state].get(next_char, 0) + 1
    return chain

def split_name_suffix(name):
    # 分割文件名主干和后缀，返回主干
    if '.' in name:
        parts = name.rsplit('.', 1)
        return parts[0]
    else:
        return name

def load_file_names(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

if __name__ == '__main__':
    file_names = load_file_names('file_names.txt')

    main_names = [split_name_suffix(n) for n in file_names]

    order = 3
    main_chain = build_char_markov_chain(main_names, order)

    with open('file_name.pkl', 'wb') as f:
        pickle.dump({'main_chain': main_chain, 'order': order}, f)

    print("训练完成，模型保存为 file_name.pkl")
