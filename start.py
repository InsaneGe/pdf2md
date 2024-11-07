import argparse
import paddleocr
import os
from tqdm import tqdm
from time import time
from pdf2md.parser import parse_file
from pdf2md.parser import parse_pic
from pdf2md.writer import Writer
from multiprocessing import Pool


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-type', '--type', help='file or dir or photo', required=True)
    parser.add_argument('-f', '--file', help='file path', required=False)
    parser.add_argument('-d', '--dir', help='dir path', required=False)
    parser.add_argument('-p', '--photo', help='photo path', required=False)
    args = parser.parse_args()
    return args


def parse_pdf(filename: str):
    blocks = parse_file(filename)
    writer = Writer(filename, blocks)
    writer.write_markdown()


def parse_photo(filename: str):
    blocks = parse_pic(filename)
    writer = Writer(filename, blocks)
    writer.write_markdown()

def start(args, processes=10):
    if args.type == 'photo':
        parse_photo(args.photo)
    elif args.type == 'dir':
        if not os.path.isdir(args.dir):
            raise Exception('not a dir')
        filenames = [os.path.join(args.file, i) for i in os.listdir(args.dir) if i.endswith('.pdf')]
        filenames = sorted(filenames, key=os.path.getsize)
        # https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool
        with Pool(processes) as p:
            list(tqdm(p.imap(parse_pdf, filenames), total=len(filenames)))
    elif args.type == 'file':
        if not args.file.endswith('.pdf'):
            raise Exception('not a pdf file')
        parse_pdf(args.file)
    else:
        raise Exception('type error')

def start_test(file: str, processes=10):
    if not file or not os.path.exists(file):
        raise Exception('file or folder does not exist')
    # justnow = time()
    if os.path.isfile(file):
        if not file.endswith('.pdf'):
            raise Exception('not a pdf file')
        parse_pdf(file)
        # print(f"this pdf runs {((time() - justnow) / 60):.3f} mins")

    elif os.path.isdir(file):
        # filenames = [os.path.join(file, i) for i in os.listdir(file) if (i.endswith('.pdf') and not os.path.exists(os.path.join(file,i.rsplit('.')[0]) ) ) ]
        filenames = [os.path.join(file, i) for i in os.listdir(file) if (i.endswith('.pdf'))]
        filenames = sorted(filenames, key=os.path.getsize)
        # https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool
        with Pool(processes) as p:
            list(tqdm(p.imap(parse_pdf, filenames), total=len(filenames)))


if __name__ == '__main__':
    print("paddleocr.__version__=", paddleocr.__version__)
    '''# test parsing single photo or pdf
    photo_path = ""
    parse_photo(photo_path)

    justnow = time()
    try:
        pdf_path = ""
        start_test("pdf_path", 5)
    except Exception as e:
        print("when start_test, exception=", e)
    print(f"these pdfs run {((time() - justnow) / 3600):.3f} hours")
    '''

    args = get_parser()
    start(args)
    try:
      start(args)
    except Exception as e:
      print("when start, exception =",e)
