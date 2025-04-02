from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
import argparse
import os
import subprocess
from pathlib import Path
import logging
# from organize_pdf import split_pdf, split_pdf_for_mobile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# 用于切割双栏pdf文件, 适用于babeldoc翻译
def split_and_merge_pdf_babeldoc(input_pdf, output_pdf, compare=False):
    writer = PdfWriter()
    if "dual" in input_pdf:
        readers = [PdfReader(input_pdf) for _ in range(4)]
        for i in range(0, len(readers[0].pages)):
            original_media_box = readers[0].pages[i].mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page_1 = readers[0].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                # 参数(0, 0, width / 4, height)表示一个矩形区域的坐标：
                # 前两个参数(0, 0)是左下角的x和y坐标
                # 后两个参数(width / 4, height)是右上角的x和y坐标
                # 这里设置页面的box属性为原始宽度的1/4，即截取PDF页面的左侧四分之一部分
                setattr(left_page_1, box, RectangleObject((0, 0, width / 4, height)))

            left_page_2 = readers[1].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(
                    left_page_2,
                    box,
                    RectangleObject((width / 2, 0, width / 2 + width / 4, height)),
                )

            right_page_1 = readers[2].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(
                    right_page_1,
                    box,
                    RectangleObject((width / 4, 0, width / 2, height)),
                )

            right_page_2 = readers[3].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(
                    right_page_2,
                    box,
                    RectangleObject((width * 3 / 4, 0, width, height)),
                )

            if compare:
                blank_page_1 = writer.add_blank_page(width / 2, height)
                blank_page_1.merge_transformed_page(left_page_1, (1, 0, 0, 1, 0, 0))
                blank_page_1.merge_transformed_page(
                    left_page_2, (1, 0, 0, 1, -width / 4, 0)
                )
                blank_page_2 = writer.add_blank_page(width / 2, height)
                # merge_transformed_page方法的第二个参数是变换矩阵，格式为(a, b, c, d, e, f)
                # 其中(a, b, c, d)控制缩放和旋转，(e, f)控制平移
                # (1, 0, 0, 1, 0, 0)表示不缩放不旋转，不平移，即原样放置
                # (1, 0, 0, 1, width / 2, 0)表示不缩放不旋转，但在x轴方向平移width/2，即向右移动半页宽度
                blank_page_2.merge_transformed_page(
                    right_page_1, (1, 0, 0, 1, -width / 4, 0)
                )
                blank_page_2.merge_transformed_page(
                    right_page_2, (1, 0, 0, 1, -width / 2, 0)
                )
            else:
                writer.add_page(left_page_1)
                writer.add_page(left_page_2)
                writer.add_page(right_page_1)
                writer.add_page(right_page_2)
    else:
        readers = [PdfReader(input_pdf) for _ in range(2)]
        # 使用两个reader中页数的最小值，防止索引越界
        num_pages = min(len(readers[0].pages), len(readers[1].pages))
        for i in range(num_pages):
            page = readers[0].pages[i]
            original_media_box = page.mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page = readers[0].pages[i]
            left_page.mediabox = RectangleObject((0, 0, width / 2, height))
            right_page = readers[1].pages[i]
            right_page.mediabox = RectangleObject((width / 2, 0, width, height))

            writer.add_page(left_page)
            writer.add_page(right_page)

    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)


# 工具函数, 用于切割双栏pdf文件
def split_and_merge_pdf(input_pdf, output_pdf, compare=False):
    writer = PdfWriter()
    if "dual" in input_pdf:
        readers = [PdfReader(input_pdf) for _ in range(4)]
        for i in range(0, len(readers[0].pages), 2):
            original_media_box = readers[0].pages[i].mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page_1 = readers[0].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(left_page_1, box, RectangleObject((0, 0, width / 2, height)))

            left_page_2 = readers[1].pages[i + 1]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(left_page_2, box, RectangleObject((0, 0, width / 2, height)))

            right_page_1 = readers[2].pages[i]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(
                    right_page_1, box, RectangleObject((width / 2, 0, width, height))
                )

            right_page_2 = readers[3].pages[i + 1]
            for box in ["mediabox", "cropbox", "trimbox", "bleedbox", "artbox"]:
                setattr(
                    right_page_2, box, RectangleObject((width / 2, 0, width, height))
                )

            if compare == True:
                blank_page_1 = writer.add_blank_page(width, height)
                blank_page_1.merge_transformed_page(left_page_1, (1, 0, 0, 1, 0, 0))
                blank_page_1.merge_transformed_page(
                    left_page_2, (1, 0, 0, 1, width / 2, 0)
                )
                blank_page_2 = writer.add_blank_page(width, height)
                blank_page_2.merge_transformed_page(
                    right_page_1, (1, 0, 0, 1, -width / 2, 0)
                )
                blank_page_2.merge_transformed_page(right_page_2, (1, 0, 0, 1, 0, 0))
            else:
                writer.add_page(left_page_1)
                writer.add_page(left_page_2)
                writer.add_page(right_page_1)
                writer.add_page(right_page_2)
    else:
        readers = [PdfReader(input_pdf) for _ in range(2)]
        for i in range(len(readers[0].pages)):
            page = readers[0].pages[i]

            original_media_box = page.mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page = readers[0].pages[i]
            left_page.mediabox = RectangleObject((0, 0, width / 2, height))
            right_page = readers[1].pages[i]
            right_page.mediabox = RectangleObject((width / 2, 0, width, height))

            writer.add_page(left_page)
            writer.add_page(right_page)

    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDF files.")
    parser.add_argument("--input", type=str, help="Input PDF file path")
    parser.add_argument("--output", type=str, help="Output PDF file path")
    parser.add_argument(
        "--compare", action="store_true", default=True, help="Compare mode"
    )
    parser.add_argument(
        "--babeldoc", action="store_true", default=True, help="Babeldoc mode"
    )
    parser.add_argument("--thread_num", type=int, default=8, help="Thread number")
    parser.add_argument("--service", type=str, default="openai", help="Service")
    args = parser.parse_args()

    # 执行 pdf2zh 命令
    pdf2zh_command = ["pdf2zh"]
    pdf2zh_command.append(args.input)
    pdf2zh_command.append("-t")
    pdf2zh_command.append(str(args.thread_num))
    pdf2zh_command.append("--output")
    pdf2zh_command.append(args.output)
    pdf2zh_command.append("--service")
    pdf2zh_command.append(args.service)
    pdf2zh_command.append("--config")
    pdf2zh_command.append("config.json")
    if args.babeldoc:
        pdf2zh_command.append("--babeldoc")
    print(pdf2zh_command)

    # 输出文件为两个, 以.zh.mono.pdf和.zh.dual.pdf结尾
    mono_file = Path(args.output) / (Path(args.input).stem + ".zh.mono.pdf")
    dual_file = Path(args.output) / (Path(args.input).stem + ".zh.dual.pdf")
    dual_compare_file = dual_file.with_suffix(".compare.pdf")
    # 如果存在, 则删除
    if mono_file.exists():
        os.remove(mono_file)
    if dual_file.exists():
        os.remove(dual_file)
    if dual_compare_file.exists():
        os.remove(dual_compare_file)

    # 执行 pdf2zh 命令
    subprocess.run(pdf2zh_command, check=False)

    # 如果文件不存在, 则抛出异常
    if not mono_file.exists() or not dual_file.exists():
        raise Exception(
            f"Failed to generate translated files: {str(mono_file)}, {str(dual_file)}"
        )
    if args.babeldoc:
        logging.info("Splitting and merging PDF files for babeldoc mode")
        split_and_merge_pdf_babeldoc(
            str(dual_file), str(dual_compare_file), args.compare
        )
    else:
        logging.info("Splitting and merging PDF files for normal mode")
        split_and_merge_pdf(str(dual_file), str(dual_compare_file), args.compare)
