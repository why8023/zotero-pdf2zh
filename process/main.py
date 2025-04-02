import argparse
import os
import subprocess
from pathlib import Path
import logging
from organize_pdf import split_pdf, split_pdf_for_mobile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
    input_file = Path(args.input)
    mono_file = Path(args.output) / (input_file.stem + ".zh.mono.pdf")
    dual_file = Path(args.output) / (input_file.stem + ".zh.dual.pdf")
    compare_file = Path(args.output) / (input_file.stem + ".compare.pdf")
    compare_slim_file = Path(args.output) / (input_file.stem + ".compare.slim.pdf")
    # 如果存在, 则删除
    if mono_file.exists():
        os.remove(mono_file)
    if dual_file.exists():
        os.remove(dual_file)
    if compare_file.exists():
        os.remove(compare_file)
    if compare_slim_file.exists():
        os.remove(compare_slim_file)

    # 执行 pdf2zh 命令
    subprocess.run(pdf2zh_command, check=False)

    # 如果文件不存在, 则抛出异常
    if not mono_file.exists() or not dual_file.exists():
        raise Exception(
            f"Failed to generate translated files: {str(mono_file)}, {str(dual_file)}"
        )
    logging.info("Splitting and merging PDF files for split mode")
    split_pdf(str(input_file), str(mono_file), str(compare_file))
    logging.info("Splitting and merging PDF files for slim mode")
    split_pdf_for_mobile(str(input_file), str(mono_file), str(compare_slim_file))

    # 删除非结果文件
    if mono_file.exists():
        os.remove(mono_file)
    if dual_file.exists():
        os.remove(dual_file)
