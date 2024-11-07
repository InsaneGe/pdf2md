PDF文件，通常有两种类型：基于文本的（如由文字处理软件直接生成）和基于图像的（如通过扫描纸质文档得到）。

基于文本的PDF（文档版）：这类PDF文件内含真正的文本信息，每个字符都被编码并具有明确的位置、字体等属性。因此，它们具有文本图层，即可以直接访问和操作的文本数据。对于这类PDF，可以轻松地搜索、复制和编辑其中的文字内容，因为系统能识别并解析这些字符。

基于图像的PDF（扫描版）：这类PDF是将纸质文档扫描后以图像形式保存，没有独立的文本信息或文本图层。系统无法直接识别和解析这些“文字”，可尝试OCR从图像中提取文本。




通过fitz和paddleocr.PPStructure提取PDF中文本、图片和表格创建markdown，基于Python 3.10 64-bit。

# 安装依赖
`pip install -r requirements.txt`

安装GPU版本PaddlePaddle：

`pip install paddlepaddle-gpu==2.6.1 -i https://mirror.baidu.com/pypi/simple`

参考https://www.paddlepaddle.org.cn/documentation/docs/zh/install/pip/windows-pip.html

# 命令行参数

可通过`python start.py -h`查看

- `-f`:单个文件或一级文件夹路径。



# 效率

速度较慢，具体视pdf构成，预估需要7到12秒解析一页pdf

# 可处理类型
前提：无公式、矩阵的单列排版
文档版pdf
扫描版偏中文pdf（要偏中文是因为ppstructure对中文的识别效果更好）
英文pdf识别推荐https://github.com/vikparuchuri/marker


# 限制

- 仅支持每页为单栏布局横向排版的pdf。

对如下这种纵向排版的pdf支持较差，数据集中随机挑选下预估如下类型的pdf比例为1%，但mathpix对如下这种的识别效果也很差，应归属于无法解决类。

![origin2](images/origin2.png)

- PPStructure对于老式pdf的识别完整度有限，如下例。

红圈为PPStructure未识别区域

![origin1](images/origin1.png)

![res1](images/res1.png)

- PPStructure仅支持中英文；且可识别的中文布局版式为text、title、figure、figure_caption、table、table_caption、header、footer、reference、equation，不支持数学公式、矩阵等。



PPStructure源码中可查如下

```python
'PP-StructureV2': {
            'table': {
                'en': {
                    'url':
                    'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar',
                    'dict_path': 'ppocr/utils/dict/table_structure_dict.txt'
                },
                'ch': {
                    'url':
                    'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar',
                    'dict_path': 'ppocr/utils/dict/table_structure_dict_ch.txt'
                }
            },
            'layout': {
                'en': {
                    'url':
                    'https://paddleocr.bj.bcebos.com/ppstructure/models/layout/picodet_lcnet_x1_0_fgd_layout_infer.tar',
                    'dict_path':
                    'ppocr/utils/dict/layout_dict/layout_publaynet_dict.txt'
                },
                'ch': {
                    'url':
                    'https://paddleocr.bj.bcebos.com/ppstructure/models/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer.tar',
                    'dict_path':
                    'ppocr/utils/dict/layout_dict/layout_cdla_dict.txt'
                }
            }
```

其中layout_cdla_dict.txt内容如下

```txt
text
title
figure
figure_caption
table
table_caption
header
footer
reference
equation
```