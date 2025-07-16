#2025-7-16 之前生成10个差不多有7，8个不杀，现在基本10个上全杀了，要生成多一点测试。有必要的话抽时间改进。
# bypass360QVM

添加图标以及版本信息，实现自动化bypass360QVM

主要逻辑参考了大佬T4y1oR的https://github.com/T4y1oR/RingQ/tree/main/QVM250

**改进：**

1、减小了生成的图标的扰动，与母版图标肉眼基本分辨不出区别（方便钓鱼用）

2、添加的随机版本信息中文件描述、公司名称、文件名等有一定可读性

**使用方法：**

首先安装依赖库

```bat
python -m pip install -r requirements.txt
```

```bat
python 360QVM.py <exe文件> <生成数量>
```

![image](https://github.com/user-attachments/assets/f1dc2303-1f27-4d78-89a6-429464f30923)

**文件说明：**

**char_company.pkl**和**word_company.pkl**是基于**kaggle**的[7+ Million Company Dataset](https://www.kaggle.com/datasets/peopledatalabssf/free-7-million-company-dataset?select=companies_sorted.csv)筛选出来的科技软件公司名为语料生成的马尔可夫模型（Markov Model）

**lda_dict.pkl**和**lda_model.pkl**以及**file_description_model.json**是基于Win11系统目录PE文件的文件描述为语料生成的LDA主题模型和马尔可夫模型（Markov Model）

**file_name.pkl**是基于我电脑上所有exe文件名为语料的马尔可夫模型（Markov Model）

**train** 目录模型训练脚本

**tools**目录遍历文件名和PE版本信息等的脚本

**其他：**

做成模型是为了生成的时候加速，Markov Model不能增量训练，大家可以自行搜集一个大的语料库再次训练。

LDA主题模型可以增量训练。

train目录里的脚本是上面三部分模型的训练脚本，其中train_file_description_models.py是文件描述训练的LDA主题模型可以直接用来增量训练。

注意，训练用到了 spaCy 的英文模型 en_core_web_sm 需要安装  python -m spacy download en_core_web_sm，不训练这个就不用装了，这个有点大也可以手动[下载whl包](https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl)安装

免杀效果大家自测吧，我就不王婆卖瓜了。

其实还有很大改进空间，欢迎大佬们批评指正。

觉得有用的话希望大家能给个Star。
