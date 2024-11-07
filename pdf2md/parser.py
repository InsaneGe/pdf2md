import fitz
from fitz import Matrix, Page, Rect
from paddleocr import PPStructure
from tqdm import tqdm
from .area import Area
from .block import FigureBlock, TabelBlock, TextBlock, is_same_table_continued
import cv2
import traceback

HEADER_STEP = 5
EXPANDING = 10


def get_page_areas(page: Page) -> list[Area]:
    # https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-increase-image-resolution
    mat = Matrix(5.0, 5.0)  # 设定zoom(缩放)比例,具体差别可以通过pix.save保存成图片后放大查看
    pix = page.get_pixmap(matrix=mat, alpha=False)  # pix类型为Pixmap
    img = pix.tobytes()  # 类型是字节串bytes
    engine = PPStructure(use_gpu=True, show_log=False)
    areas = []
    im_list = engine(img)
    # ("\nlen(im_list)=", len(im_list))
    for i_dic in im_list:
        '''
        i_dic记录了type,bbox,img,res,img_idx; types种类有['title','text','figure','figure_caption','reference','header','footer','table_caption']
        i_dic['res']根据type的不同有如下两种形式
            type=table: 一个dict，有字段html: 表格的HTML字符串。
            type为其它时: 一个包含各个单行文字的检测坐标和识别结果的元组。
        '''
        print("i_dic['type']=", i_dic['type'])
        # if i_dic['type'] == 'table':
        #   print("i_dic['res']['html']=",i_dic['res']['html'])
        if i_dic['res'] != []:
            area = Area(i_dic)
            area.parse()
            areas.append(area)
    print("len(areas)=", len(areas), f'     另有{len(im_list) - len(areas)}个area中的res无效')
    return areas


def get_page_blocks(page: Page) -> list:
    is_scanned = is_scanned_page(page)
    blocks = []
    areas = get_page_areas(page)

    # 如下是针对PPStructure对英文的文档版pdf识别完整度非常差劲的特例处理
    if not is_scanned:
        text_dict = page.get_text('blocks')
        d = {'type': 'text',
             'rect': page.rect,
             'level': -1,
             'lines': []}
        d['lines'] = [{'rect': Rect(line[0], line[1], line[2], line[3]),
                       'text': line[4]} for line in text_dict]
        # https://pymupdf.readthedocs.io/en/latest/rect.html#rect
        d['lines'].sort(key = lambda l:(l['rect'].y0,l['rect'].x0)) # 直接识别一页此时d['lines']中容易出现上下顺序不对应问题，故加d['lines']的排序
        block = TextBlock(d)
        blocks.append(block)

    # for area in areas:
    #     if area.is_table:
    #         d = area.get_table_dict()
    #         block = TabelBlock(d)
    #     elif area.is_figure:
    #         d = area.get_figure_dict()
    #         block = FigureBlock(d)
    #     elif area.is_title:
    #         d = area.get_title_dict()
    #         block = TextBlock(d)
    #     else:
    #         d = area.get_text_dict()
    #         """
    #         如下处理逻辑在测试时发现对于下述测试用例会导致效果奇差。
    #         对于英文的文档版pdf，PPStructure的识别完整度非常差，即area的rect_没有包含全有效文字区域，故根据area的rect_去进行page.get_text提取不全有效文本。
    #         """
    #         if not is_scanned:  # 不是扫描版则扩充范围后直接用fitz中的page.get_text获取信息
    #             text_dict = page.get_text('blocks')
    #             print("text_dict=", text_dict)
    #             clip = Rect(area.rect_.x0 - EXPANDING, area.rect_.y0 - EXPANDING, area.rect_.x1 + EXPANDING,
    #                         area.rect_.y1 + EXPANDING)
    #             # https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text
    #             text_dict = page.get_text('blocks', clip=clip)
    #             print("text_dict=", text_dict)
    #             d['lines'] = [{'rect': Rect(line[0], line[1], line[2], line[3]),
    #                            'text': line[4]} for line in text_dict]
    #         block = TextBlock(d)
    #     blocks.append(block)

    blocks.sort(key=lambda b: (b.rect_.y0, b.rect_.x0))
    return blocks


def get_pic_blocks(img) -> list:
    engine = PPStructure(use_gpu=True, show_log=False)
    areas = []
    im_list = engine(img)
    for i_dic in im_list:
        if i_dic['res'] != []:
            area = Area(i_dic)
            area.parse()
            areas.append(area)
    blocks = []
    for area in areas:
        if area.is_table:
            d = area.get_table_dict()
            block = TabelBlock(d)
        elif area.is_figure:
            d = area.get_figure_dict()
            block = FigureBlock(d)
        elif area.is_title:
            d = area.get_title_dict()
            block = TextBlock(d)
        else:
            d = area.get_text_dict()
            block = TextBlock(d)
        blocks.append(block)
    blocks.sort(key=lambda x: (x.rect_.y0, x.rect_.x0))
    return blocks


def add_title_level(blocks: list):
    # titles中每个元素指向的地址和blocks中的一致，所以对titles中的元素的属性值的修改可以作用到blocks上
    titles = [i for i in blocks if i.type_ == 'title']
    if not titles:
        return
    titles.sort(key=lambda x: -x.rect_.height)
    level = 1
    end_h = titles[0].rect_.height

    for title in titles:
        if end_h - title.rect_.height > HEADER_STEP:
            end_h = title.rect_.height
            level += 1
        title.level_ = level if level <= 6 else 6


def merge_spanning_tables(blocks):  # 合并跨页的表格
    merged_tables = []
    previous_table = None

    for current_table in blocks:
        if previous_table is not None and current_table is not None:
            if previous_table.is_table and current_table.is_table:
                if is_same_table_continued(previous_table, current_table):
                    previous_table.merge_with(current_table)
                    continue

        merged_tables.append(current_table)
        previous_table = current_table

    return merged_tables


# 删除已经在大block中识别过的小block,但在测试过程中未检测到会有这种识别情形。此逻辑可删去。
def vertically_merge_block(blocks: list) -> list:
    if blocks == []:
        return []
    res = [blocks[0]]
    times = 1
    for block in blocks[1:]:
        if not res[-1].rect_.contains(block.rect_):
            res.append(block)
            print(f"small block duplicate exists {times} times")
            times += 1
    return res


def is_scanned_page(page: Page):
    # https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text
    has_text_layer = page.get_text("text")
    if not has_text_layer:
        return True
    return False


def parse_file(filename: str) -> list:
    doc = fitz.open(filename)
    # print("------\ntype(doc)", type(doc))  # <class 'fitz.Document'>
    # print("type(doc[0])", type(doc[0]))  # <class 'fitz.Page'>
    print(f"len of {filename.rsplit('/', maxsplit=1)[1]}=", len(doc))

    blocks = []
    for page in tqdm(doc):
        # print("page.rect=", page.rect)
        block = get_page_blocks(page)
        blocks.extend(block)
        # locate the page number resulting Exception
        # try:
        #     block = get_page_blocks(page)
        #     blocks.extend(block)
        # except Exception as e:
        #     print(f"len of {filename.rsplit('/', maxsplit=1)[1]}=", len(doc))
        #     print(f"page.number = {page.number}")
        #     traceback.print_exc() # print detailed information about e

    doc.close()

    add_title_level(blocks)
    blocks = merge_spanning_tables(blocks)

    return blocks


def parse_pic(filename: str) -> list:
    img = cv2.imread(filename)
    blocks = get_pic_blocks(img)
    add_title_level(blocks)
    blocks = merge_spanning_tables(blocks)
    return blocks
