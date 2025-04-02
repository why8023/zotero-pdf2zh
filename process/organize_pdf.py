import os
from pypdf import PdfReader, PdfWriter
from copy import deepcopy
from pathlib import Path
from itertools import chain


# 用于切割双栏pdf文件
def split_pdf(
    original_pdf: str, translated_pdf: str, output_pdf_path: str = None
) -> str:
    """
    将双列PDF拆分为单列PDF

    Args:
        original_pdf (str): 原始PDF文件路径
        translated_pdf (str): 翻译后的PDF文件路径
        output_pdf_path (str, optional): 输出PDF文件路径。如果不指定，将在原文件同目录下创建

    Returns:
        str: 输出PDF文件路径
    """
    if not os.path.exists(original_pdf):
        raise FileNotFoundError(f"输入文件不存在: {original_pdf}")

    if not os.path.exists(translated_pdf):
        raise FileNotFoundError(f"输入文件不存在: {translated_pdf}")

    # 如果输出路径为空
    if output_pdf_path is None:
        # 在原文件名后添加compare后缀
        base_name = Path(original_pdf).stem
        output_pdf_path = str(Path(original_pdf).parent / f"{base_name}.compare.pdf")

    original_reader = PdfReader(original_pdf)
    translated_reader = PdfReader(translated_pdf)

    assert len(original_reader.pages) == len(translated_reader.pages), (
        f"原始文件和翻译文件的页数不一致: {original_pdf}, {translated_pdf}"
    )
    writer = PdfWriter()

    for page in chain(*zip(original_reader.pages, translated_reader.pages)):
        writer.add_page(page)

    # 保存处理后的PDF
    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

    return output_pdf_path


# 用于切割pdf文件为单列, 适用于mobile
def split_pdf_for_mobile(
    original_pdf: str, translated_pdf: str, output_pdf_path: str = None
) -> str:
    """
    将PDF文件拆分为单列

    Args:
        original_pdf (str): 原始PDF文件路径
        translated_pdf (str): 翻译后的PDF文件路径
        output_pdf_path (str, optional): 输出PDF文件路径。如果不指定，将在原文件同目录下创建

    Returns:
        str: 输出PDF文件路径
    """
    if not os.path.exists(original_pdf):
        raise FileNotFoundError(f"输入文件不存在: {original_pdf}")

    if not os.path.exists(translated_pdf):
        raise FileNotFoundError(f"输入文件不存在: {translated_pdf}")

    if output_pdf_path is None:
        # 在原文件名后添加.compare.slim后缀
        base_name = Path(original_pdf).stem
        output_pdf_path = str(
            Path(original_pdf).parent / f"{base_name}.compare.slim.pdf"
        )

    original_reader = PdfReader(original_pdf)
    translated_reader = PdfReader(translated_pdf)

    assert len(original_reader.pages) == len(translated_reader.pages), (
        f"原始文件和翻译文件的页数不一致: {original_pdf}, {translated_pdf}"
    )

    writer = PdfWriter()

    for original_page, translated_page in zip(
        original_reader.pages, translated_reader.pages
    ):
        # 创建新的页面
        original_left_page = deepcopy(original_page)
        original_left_page.mediabox.upper_right = (
            original_page.mediabox.upper_right[0] / 2,
            original_page.mediabox.upper_right[1],
        )
        original_right_page = deepcopy(original_page)
        original_right_page.mediabox.lower_left = (
            original_page.mediabox.upper_right[0] / 2,
            original_page.mediabox.lower_left[1],
        )
        translated_left_page = deepcopy(translated_page)
        translated_left_page.mediabox.upper_right = (
            translated_page.mediabox.upper_right[0] / 2,
            translated_page.mediabox.upper_right[1],
        )
        translated_right_page = deepcopy(translated_page)
        translated_right_page.mediabox.lower_left = (
            translated_page.mediabox.upper_right[0] / 2,
            translated_page.mediabox.lower_left[1],
        )
        writer.add_page(original_left_page)
        writer.add_page(translated_left_page)
        writer.add_page(original_right_page)
        writer.add_page(translated_right_page)
    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

    return output_pdf_path


if __name__ == "__main__":
    # 测试代码
    original_pdf = r"process/translated/peters_2018_deep_contextualized_word_representations.pdf"  # 替换为实际的PDF文件路径
    translated_pdf = r"process/translated/peters_2018_deep_contextualized_word_representations.zh.mono.pdf"  # 替换为实际的PDF文件路径
    compare_pdf = split_pdf(original_pdf, translated_pdf)
    compare_slim_pdf = split_pdf_for_mobile(original_pdf, translated_pdf)

    print(f"PDF处理完成，输出文件：{compare_pdf}, {compare_slim_pdf}")
