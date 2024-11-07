import os
from mdutils.mdutils import MdUtils


class Writer(object):

    def __init__(self, filename: str, blocks: list) -> None:
        '''
        description:
        param {str} filename: filename of pdf document
        param {list} blocks: list of Blocks
        '''
        self.blocks_ = blocks

        # root_dir
        self.root_dir_ = os.path.splitext(filename)[0]
        if not os.path.exists(self.root_dir_):
            os.makedirs(self.root_dir_)

        # md_file
        basename, _ = os.path.splitext(os.path.basename(filename))
        md_name = os.path.join(self.root_dir_, basename)
        self.md_file_ = MdUtils(file_name=md_name)
        # self.md_file_ = MdUtils(file_name=md_name, title=basename)

    def gen_markdown(self, has_footer: bool = True):
        '''
        description:
        param {bool} has_footer: whether to write footer or not
        '''
        img_id = 0

        for block in self.blocks_:
            syntax = ''

            if block.is_figure:
                syntax = block.gen_image_syntax(self.root_dir_, img_id)
                img_id += 1

            elif block.is_table:
                try:
                    syntax = block.gen_table_syntax() + '\n'
                except Exception as e:
                    print(f"Error when gen_table_syntax: {e}", "syntax remains '',pass this part")

            elif block.is_paragraph:
                syntax = block.gen_paragraph_syntax(has_footer)

            self.md_file_.write(syntax)

    def write_markdown(self):
        self.gen_markdown()
        self.md_file_.create_md_file()
