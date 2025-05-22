import hashlib
import os
import random
import string
import subprocess
import sys
import time
import pickle
import json
import re
import markovify
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# ================== 常量区 ==================
ICO_DIR = "icon"
RANDOMICO_DIR = "random"
OUT_DIR = "out"
RCEDIT_PATH = "rcedit-x64.exe"
RESOURCE_HACKER_PATH = "ResourceHacker.exe"
FILE_NAME_MODEL_PATH = "file_name.pkl"
CHAR_COMPANY_PATH = "char_company.pkl"
WORD_COMPANY_PATH = "word_company.pkl"
DICT_PATH = "lda_dict.pkl"
LDA_MODEL_PATH = "lda_model.pkl"
MARKOV_MODEL_PATH = "file_description_model.json"
TOPIC_ID = 4
MIN_WORD_LEN = 10
MAX_TRIES = 200

# ================== 工具函数 ==================
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def safe_remove(path):
    if os.path.isfile(path):
        os.remove(path)

def clean_dir(path):
    if os.path.exists(path):
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            safe_remove(file_path)
    else:
        os.makedirs(path)

# ================== 模型加载区 ==================
def load_file_name_model():
    with open(FILE_NAME_MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    return data['main_chain'], data['order']

def load_company_models():
    with open(CHAR_COMPANY_PATH, 'rb') as f:
        char_chain = pickle.load(f)
    with open(WORD_COMPANY_PATH, 'rb') as f:
        word_chain = pickle.load(f)
    return char_chain, word_chain

def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def load_markov_model(path=MARKOV_MODEL_PATH):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        model_json = json.load(f)
    return markovify.Text.from_json(model_json)

# ================== 生成函数区 ==================
def generate_name_part(chain, order, max_length=15):
    state = '^' * order
    result = []
    while True:
        if state not in chain:
            break
        next_chars = chain[state]
        total = sum(next_chars.values())
        r = random.uniform(0, total)
        cum_sum = 0
        next_char = None
        for char, count in next_chars.items():
            cum_sum += count
            if r <= cum_sum:
                next_char = char
                break
        if next_char == '$' or len(result) >= max_length:
            break
        result.append(next_char)
        state = (state + next_char)[-order:]
    return ''.join(result)

def generate_file_name(main_chain, order, fixed_suffixes=None):
    main_part = generate_name_part(main_chain, order)
    if not main_part:
        main_part = 'file'
    if fixed_suffixes:
        suffix = random.choice(fixed_suffixes)
    else:
        suffix = '.txt'
    return main_part + suffix

def generate_file_name_no_suffix(main_chain, order):
    name = generate_file_name(main_chain, order, fixed_suffixes=['.exe'])
    return os.path.splitext(name)[0]

# 公司名生成
prefixes = [
    'Bright', 'Quantum', 'Nex', 'Tech', 'Future', 'Smart', 'Core', 'Sky', 'Dynamic', 'Innovate',
    'Cyber', 'Nano', 'AI', 'Cloud', 'Bio', 'Data', 'Neo', 'Vortex', 'Ion', 'Pulse',
    'Nova', 'Fusion', 'Digital', 'Intelli', 'Code', 'Neural', 'Optic', 'Spark', 'Gizmo', 'Byte',
    'Aero', 'Synth', 'Holo', 'Prism', 'Zeta', 'Omni', 'Alpha', 'Beta', 'Zero', 'Infinity',
    'Pixel', 'Vector', 'Nexus', 'Sync', 'Wave', 'Flux', 'Grid', 'Orbit', 'Techne',
    'Astral', 'Cosmo', 'Photon', 'Arc', 'Velo', 'Chrono', 'Luna', 'Star', 'Zephyr',
    'Hyper', 'Giga', 'Tera', 'Meta', 'Cryo', 'Apex', 'Blaze', 'Echo', 'Vibe', 'Synthia',
    'Eon', 'Quark', 'Nebula', 'Aether', 'Krypto', 'Lumin', 'Axiom', 'Cypher', 'Helix',
    'QuantumLeap', 'Deep', 'Cogni', 'Synthos', 'Holograph', 'Nexlify', 'Techno', 'Vivid',
    'AeroWave', 'BioSpark', 'CloudPeak', 'DataMesh', 'HyperCore', 'NanoTech', 'Starlight',
    'TeraByte', 'Ultra', 'Vantage', 'Xenon', 'Zentra', 'Crypto', 'IntelliCore', 'Neura',
    'QuantumCore', 'Synapse', 'Vita', 'Think', 'Edge', 'Flow', 'Circuit', 'HoloTech',
    'AIWave', 'Cryon', 'Zentron', 'Fluxion', 'Neon', 'Synthix', 'Grok', 'QuantumBit',
    'BioFlux', 'DataWave', 'Neuro', 'TechBit', 'OmniTech', 'Zest', 'VortexAI', 'Lumora',
    'CogniTech', 'DeepMind', 'Gene', 'BioCore', 'QuantumSync', 'HyperNet', 'Nextron',
    'AIForge', 'DataFlux', 'NeuraLink', 'SynthCore', 'CryoTech', 'Zentrix', 'VitaTech',
    'QuantumEdge', 'HoloCore', 'BitWave', 'NanoCore', 'TechVibe', 'StarCore'
]
adjectives = ['Smart', 'Advanced', 'NextGen', 'Pro', 'Elite', 'Prime', '', '', '', '']
roots = ['Solutions', 'Systems', 'Labs', 'Ventures', 'Technologies', 'Analytics', 'Group', 'Partners', 'Corp']
suffixes = ['Inc', 'LLC', 'Co', 'Ltd', 'Tech', 'AI', '']
word_pairs = [
    ['Cloud', 'flare'], ['Snow', 'flake'], ['Data', 'dog'], ['Bright', 'Labs'],
    ['Quantum', 'Ventures'], ['Nex', 'Gen'], ['Tech', 'Analytics'], ['Future', 'Systems']
]
generated_names = set()
def generate_core_name(char_chain, order=2, max_length=10):
    current_state = '^' * order
    name = []
    while len(name) < max_length:
        if current_state not in char_chain:
            break
        next_chars = char_chain[current_state]
        total = sum(next_chars.values())
        r = random.uniform(0, total)
        cumsum = 0
        for char, count in next_chars.items():
            cumsum += count
            if r <= cumsum:
                if char == '$':
                    break
                name.append(char)
                current_state = (current_state + char)[-order:]
                break
    result = ''.join(name).capitalize()
    if not result or len(result) < 4 or not result[0].isalpha() or sum(c in 'aeiou' for c in result.lower()) < 2:
        return generate_core_name(char_chain, order, max_length)
    return result
def generate_word_core(word_chain, max_words=2):
    current = random.choice(list(word_chain.keys()))
    name = [current]
    for _ in range(max_words - 1):
        if current not in word_chain or '$' in word_chain[current]:
            break
        next_words = word_chain[current]
        total = sum(next_words.values())
        r = random.uniform(0, total)
        cumsum = 0
        for word, count in next_words.items():
            cumsum += count
            if r <= cumsum:
                if word == '$':
                    break
                name.append(word)
                current = word
                break
    return ' '.join(name).capitalize()
def generate_tech_company_name(char_chain, word_chain, order=2, subsector=None):
    subsector_prefixes = {
        'AI': ['AI', 'Neural', 'Cogni', 'Deep', 'Neura', 'Intelli', 'Quantum', 'AIWave', 'CogniTech', 'DeepMind', 'NeuraLink'],
        'Biotech': ['Bio', 'Gene', 'Vita', 'BioSpark', 'BioFlux', 'BioCore', 'VitaTech'],
        'Fintech': ['Crypto', 'Krypto', 'Data', 'QuantumEdge', 'BitWave'],
        'Quantum': ['Quantum', 'QuantumLeap', 'QuantumCore', 'QuantumBit', 'QuantumSync']
    }
    if subsector is None:
        allowed_prefixes = prefixes
    elif subsector == 'All':
        all_prefixes = set()
        for v in subsector_prefixes.values():
            all_prefixes.update(v)
        allowed_prefixes = list(set(prefixes).union(all_prefixes))
    else:
        allowed_prefixes = subsector_prefixes.get(subsector, prefixes)
    structure = random.choice([
        'prefix_adjective_core_suffix',
        'prefix_core_suffix',
        'core_suffix',
        'prefix_core',
        'word_core_suffix'
    ])
    if structure == 'word_core_suffix':
        core = generate_word_core(word_chain)
    else:
        core = generate_core_name(char_chain, 2) if random.random() < 0.5 else random.choice(roots)
    if structure == 'prefix_adjective_core_suffix':
        prefix = random.choice(allowed_prefixes)
        adjective = random.choice(adjectives)
        suffix = random.choice(suffixes)
        name = f"{prefix} {adjective} {core} {suffix}".strip()
    elif structure == 'prefix_core_suffix':
        prefix = random.choice(allowed_prefixes)
        suffix = random.choice(suffixes)
        name = f"{prefix} {core} {suffix}".strip()
    elif structure == 'core_suffix':
        suffix = random.choice(suffixes)
        name = f"{core} {suffix}".strip()
    elif structure == 'prefix_core':
        prefix = random.choice(allowed_prefixes)
        name = f"{prefix} {core}".strip()
    else:
        suffix = random.choice(suffixes)
        name = f"{core} {suffix}".strip()
    if name in generated_names:
        return generate_tech_company_name(char_chain, word_chain, 2, subsector)
    generated_names.add(name)
    return name

def get_topic_keywords(lda_model, topic_id, topn=30):
    return [word for word, _ in lda_model.show_topic(topic_id, topn=topn)]
def contains_topic_keyword(sentence, keywords_set):
    words = re.findall(r'\w+', sentence.lower())
    return any(word in keywords_set for word in words)
def generate_sentence_with_filters(model, keywords_set, min_words=MIN_WORD_LEN, max_tries=MAX_TRIES):
    for _ in range(max_tries):
        sentence = model.make_sentence()
        if sentence:
            if len(sentence.split()) >= min_words and contains_topic_keyword(sentence, keywords_set):
                sentence = re.sub(r'\s([,.!?])', r'\1', sentence)
                return sentence.capitalize()
    return None
def generate_file_description():
    if not (os.path.exists(LDA_MODEL_PATH) and os.path.exists(DICT_PATH) and os.path.exists(MARKOV_MODEL_PATH)):
        return "File description"
    lda_model = load_pickle(LDA_MODEL_PATH)
    markov_model = load_markov_model()
    if markov_model is None:
        return "File description"
    topic_keywords = get_topic_keywords(lda_model, TOPIC_ID)
    topic_keywords_set = set(topic_keywords)
    sentence = generate_sentence_with_filters(markov_model, topic_keywords_set)
    if sentence:
        return sentence
    else:
        return "File description"

# ================== 图标处理区 ==================
def disturb_pixels(image, disturb_ratio=1.0):
    pixel_data = list(image.getdata())
    total_pixels = len(pixel_data)
    disturb_count = int(total_pixels * disturb_ratio)
    disturb_indices = set(random.sample(range(total_pixels), disturb_count))
    modified_pixel_data = []
    for i, (r, g, b, a) in enumerate(pixel_data):
        if i in disturb_indices:
            modified_pixel_data.append((
                max(0, min(255, r + random.randint(-3, 3))),
                max(0, min(255, g + random.randint(-3, 3))),
                max(0, min(255, b + random.randint(-3, 3))),
                a
            ))
        else:
            modified_pixel_data.append((r, g, b, a))
    disturbed_image = Image.new("RGBA", image.size)
    disturbed_image.putdata(modified_pixel_data)
    return disturbed_image

def creatico():
    clean_dir(RANDOMICO_DIR)
    ensure_dir(RANDOMICO_DIR)
    for filename in os.listdir(ICO_DIR):
        if filename.lower().endswith('.ico'):
            source_path = os.path.join(ICO_DIR, filename)
            try:
                with Image.open(source_path) as image:
                    image = image.convert("RGBA")
                    pixel_data = list(image.getdata())
                    modified_pixel_data = [
                        (
                            max(0, min(255, r + random.randint(-3, 3))),
                            max(0, min(255, g + random.randint(-3, 3))),
                            max(0, min(255, b + random.randint(-3, 3))),
                            a
                        )
                        for (r, g, b, a) in pixel_data
                    ]
                    modified_image = Image.new("RGBA", image.size)
                    modified_image.putdata(modified_pixel_data)
                    hash_value = hashlib.md5(str(random.random()).encode()).hexdigest()
                    new_filename = os.path.join(RANDOMICO_DIR, f"{hash_value}.ico")
                    modified_image.save(new_filename, format='ICO')
                    fake_time = random.randint(0, int(time.time()))
                    os.utime(new_filename, (fake_time, fake_time))
            except Exception as e:
                print(f"处理 {filename} 时出错: {e}")

# ================== 版本信息处理区 ==================
def generate_random_version(parts=4):
    version_parts = [str(random.randint(0, 99)) for _ in range(parts)]
    return '.'.join(version_parts)

def set_version_info(exe_path, main_chain, order, char_chain, word_chain, info):
    file_description = info['file_description']
    company_name = info['company_name']
    legal_copyright = info['legal_copyright']
    product_name = info['product_name']
    internal_name = info['internal_name']
    original_name = info['original_name']
    version = info['version']
    file_version = version
    product_version = '.'.join(version.split('.')[:-1])
    command = [
        RCEDIT_PATH,
        exe_path,
        "--set-version-string", "FileDescription", file_description,
        "--set-version-string", "InternalName", internal_name,
        "--set-version-string", "OriginalFilename", original_name,
        "--set-version-string", "CompanyName", company_name,
        "--set-version-string", "LegalCopyright", legal_copyright,
        "--set-version-string", "ProductName", product_name,
        "--set-file-version", file_version,
        "--set-product-version", product_version
    ]
    result = subprocess.run(command, capture_output=True, text=True)

def add_random_icons(exename, i, info):
    savaname = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    icon_files = os.listdir(RANDOMICO_DIR)
    random_icofiles = random.sample(icon_files, 2)
    randomico1 = random_icofiles[0]
    randomico2 = random_icofiles[1]
    while not os.path.isfile(f"{RANDOMICO_DIR}/{randomico1}") or not os.path.isfile(f"{RANDOMICO_DIR}/{randomico2}"):
        random_icofiles = random.sample(icon_files, 2)
        randomico1 = random_icofiles[0]
        randomico2 = random_icofiles[1]
    out1_path = f"{OUT_DIR}/output{i}.exe"
    out2_path = f"{OUT_DIR}/{savaname}.exe"
    icon_group_id1 = random.randint(10000, 99999)
    icon_group_id2 = random.randint(10000, 99999)
    try:
        command1 = [
            RESOURCE_HACKER_PATH,
            "-open", exename,
            "-save", out1_path,
            "-action", "addskip",
            "-res", f"{RANDOMICO_DIR}/{randomico1}",
            "-mask", f"ICONGROUP,{icon_group_id1}"
        ]
        result1 = subprocess.run(command1, capture_output=True, text=True)
    except Exception as e:
        print("[ERROR] ResourceHacker(1) exception:", e)
    try:
        command2 = [
            RESOURCE_HACKER_PATH,
            "-open", out1_path,
            "-save", out2_path,
            "-action", "addskip",
            "-res", f"{RANDOMICO_DIR}/{randomico2}",
            "-mask", f"ICONGROUP,{icon_group_id2}"
        ]
        result2 = subprocess.run(command2, capture_output=True, text=True)
    except Exception as e:
        print("[ERROR] ResourceHacker(2) exception:", e)
    set_version_info(out2_path, None, None, None, None, info)
    safe_remove(out1_path)
    return savaname

# ================== 主流程区 ==================
def generate_all_info(main_chain, order, char_chain, word_chain):
    file_name = generate_file_name_no_suffix(main_chain, order)
    company_name = generate_tech_company_name(char_chain, word_chain)
    file_description = generate_file_description()
    version = generate_random_version()
    return {
        "internal_name": file_name,
        "original_name": file_name,
        "product_name": file_name,
        "company_name": company_name,
        "file_description": file_description,
        "legal_copyright": f"Copyright (C) 2024 {company_name}",
        "version": version
    }

def banner():
    print('''
           +-+ +-+ +-+ +-+ +-+ +-+
           |3| |6| |0| |Q| |V| |M|
           +-+ +-+ +-+ +-+ +-+ +-+

    Github: https://github.com/A-new/bypass360QVM
        使用方法: python3 360QVM.py input.exe 10
            生成10个到out目录，icon目录为图标资源，可以放自己的图标
''')

def main():
    banner()
    if len(sys.argv) < 3:
        print("用法: python 360QVM.py <exe文件> <生成数量>")
        exit()
    exename = sys.argv[1]
    gennum = int(sys.argv[2])
    ensure_dir(OUT_DIR)
    main_chain, order = load_file_name_model()
    char_chain, word_chain = load_company_models()
    start_time = time.time()
    for i in range(gennum):
        print(f"------------------------------{i + 1}------------------------------")
        try:
            creatico()
            info = generate_all_info(main_chain, order, char_chain, word_chain)
            savaname = add_random_icons(exename, i, info)
            if not os.path.isfile(f"{OUT_DIR}/{savaname}.exe"):
                print("[-] 生成失败！ 请重新尝试~ ")
            else:
                print("[+] 伪造资源成功！")
                print(f"[+] Enjoy! {savaname}.exe")
        except Exception as e:
            print(e)
            pass
    print(f"------------------------------生成完毕------------------------------")
    end_time = time.time()
    print(f"消耗时间: {end_time - start_time}秒")

if __name__ == '__main__':
    main()
