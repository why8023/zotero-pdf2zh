from flask import Flask, request, jsonify
import os
import base64
import subprocess
import copy
from flask import Flask, send_file, abort
from pypdf import PdfWriter, PdfReader
from pypdf.generic import RectangleObject
import sys

######################################## 默认配置 ########################################
port_num = 8888                     # 设置端口号: 默认为8888
pdf2zh = "pdf2zh"                   # 设置pdf2zh指令: 默认为'pdf2zh'

######### 可以在Zotero偏好设置中配置以下参数, Zotero配置会覆盖本文件中的配置参数 #########
thread_num = 4                      # 设置线程数: 默认为4
service = 'bing'                    # 设置翻译服务: 默认为bing
translated_dir = "./translated/"    # 设置翻译文件的输出路径(临时路径, 可以在翻译后删除)
config_path = './config.json'       # 设置PDF2zh配置文件路径
babeldoc = True                     # 是否使用babeldoc

source_languages = 'en'             # 设置源语言
target_languages = 'zh'             # 设置目标语言

global_translated_dir = translated_dir
##########################################################################################

class Config:
    def __init__(self, request):
        self.thread_num = request.get_json().get('threadNum')
        if self.thread_num == None or self.thread_num == "":
            self.thread_num = thread_num

        self.service = request.get_json().get('engine')
        if self.service == None or self.service == "":
            self.service = service

        self.translated_dir = request.get_json().get('outputPath')
        if self.translated_dir == None or self.translated_dir == "":
            self.translated_dir = translated_dir
        self.translated_dir = get_absolute_path(self.translated_dir)
        os.makedirs(self.translated_dir, exist_ok=True)

        self.config_path = request.get_json().get('configPath')
        if self.config_path == None or self.config_path == "":
            self.config_path = config_path
        self.config_path = get_absolute_path(self.config_path)

        self.babeldoc = babeldoc
        # self.babeldoc = request.get_json().get('babeldoc')
        # if self.babeldoc == None or self.babeldoc == "":
        #     self.babeldoc = babeldoc

        self.mono_cut = request.get_json().get('mono_cut')
        self.dual_cut = request.get_json().get('dual_cut')
        self.compare = request.get_json().get('compare')

        self.source_languages = request.get_json().get('sourceLanguages')
        if self.source_languages == None or self.source_languages == "":
            self.source_languages = source_languages

        self.target_languages = request.get_json().get('targetLanguages')
        if self.target_languages == None or self.target_languages == "":
            self.target_languages = target_languages
        
        print("outputPath: ", self.translated_dir)
        print("configPath: ", self.config_path)

        global global_translated_dir
        global_translated_dir = self.translated_dir

def get_absolute_path(path):
    if os.path.isabs(path):
        return path 
    else:
        return os.path.abspath(path)

def get_file_from_request(request): 
    config = Config(request)
    data = request.get_json()
    path = data.get('filePath')
    print("filePath: ", path)
    path = path.replace('\\', '/') 
    file_content = data.get('fileContent')
    input_path = os.path.join(config.translated_dir, os.path.basename(path))
    input_path = get_absolute_path(input_path)
    print("input path: ", input_path)
    if file_content:
        if file_content.startswith('data:application/pdf;base64,'): # 移除 Base64 编码中的前缀(如果有)
            file_content = file_content[len('data:application/pdf;base64,'):]
        file_data = base64.b64decode(file_content) # 解码 Base64 内容
        with open(input_path, 'wb') as f:
            f.write(file_data)
    return input_path, config

def translate_pdf(input_path, config):
    print("\n############# Translating #############")
    print("## translate file path ## : ", input_path)
    if not os.path.exists(input_path):
        raise Exception("[translate_pdf()]: input file path not found", input_path)
    
    # 执行pdf2zh翻译, 用户可以自定义命令内容:
    command = [
        pdf2zh,
        input_path,
        '-t', str(config.thread_num),
        '--output', config.translated_dir,
        '--service', config.service,
        '--lang-in', config.source_languages, 
        '--lang-out', config.target_languages 
    ]
    if os.path.exists(config.config_path):
        command.append('--config')
        command.append(config.config_path)
    if config.babeldoc:
        command.append('--babeldoc')
    subprocess.run(command, check=False)

    # 构建单语言和双语言输出文件路径
    mono = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '-mono.pdf'))
    dual = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '-dual.pdf'))
    if config.babeldoc:
        mono = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '.zh.mono.pdf'))
        dual = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '.zh.dual.pdf'))
    if not os.path.exists(mono) or not os.path.exists(dual):
        raise Exception("[Failed to generate translated files]: ", mono, dual)
    if config.babeldoc:
        # 如果目标文件已存在，先删除它，然后再重命名
        target_mono = mono.replace('.zh.mono.pdf', '-mono.pdf')
        target_dual = dual.replace('.zh.dual.pdf', '-dual.pdf')
        if os.path.exists(target_mono):
            os.remove(target_mono)
        if os.path.exists(target_dual):
            os.remove(target_dual)
        os.rename(mono, target_mono)
        os.rename(dual, target_dual)
        mono = mono.replace('.zh.mono.pdf', '-mono.pdf')
        dual = dual.replace('.zh.dual.pdf', '-dual.pdf')
    print("[mono file generated]: ", mono)
    print("[dual file generated]: ", dual)
    return mono, dual

app = Flask(__name__)
@app.route('/translate', methods=['POST'])
def translate():
    input_path, config = get_file_from_request(request)
    try:
        mono, dual = translate_pdf(input_path, config)
        if config.mono_cut and config.mono_cut == "true":
            path = mono.replace('-mono.pdf', '-mono-cut.pdf')
            if config.babeldoc:
                split_and_merge_pdf_babeldoc(mono, path, compare = False)
            else:
                split_and_merge_pdf(mono, path, compare = False)
            if not os.path.exists(path):
                raise Exception("[Failed to generate cutted files]: ", path)
            print("[mono-cut file generated]: ", path)
        if config.dual_cut and config.dual_cut == "true":
            path = dual.replace('-dual.pdf', '-dual-cut.pdf')
            if config.babeldoc:
                split_and_merge_pdf_babeldoc(dual, path, compare = False)
            else:
                split_and_merge_pdf(dual, path, compare = False)
            if not os.path.exists(path):
                raise Exception("[Failed to generate cutted files]: ", path)
            print("[dual-cut file generated]: ", path)
        if config.compare and config.compare == "true":
            path = dual.replace('.pdf', '-compare.pdf')
            if config.babeldoc:
                split_and_merge_pdf_babeldoc(dual, path, compare=True)
            else:
                split_and_merge_pdf(dual, path, compare=True)
            if not os.path.exists(path):
                raise Exception("[Failed to generate compare files]: ", path)
            print("[compare file generated]: ", path)
        if not os.path.exists(mono) or not os.path.exists(dual):
            raise Exception("[Pdf2zh failed to generate translated files]: ", mono, dual)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"[translate() Error]: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/translatedFile/<filename>')
def download(filename):
    print("\n############# Downloading #############")
    file_path = os.path.join(get_absolute_path(global_translated_dir), filename)
    if not os.path.isfile(file_path):
        print("[Download File not found]: ", file_path)
        return "[Download File not found]: " + file_path, 404
    print("[Download file]: ", file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)

# 工具函数, 用于切割双栏pdf文件, 适用于babeldoc翻译
def split_and_merge_pdf_babeldoc(input_pdf, output_pdf, compare=False):
    writer = PdfWriter()
    if 'dual' in input_pdf:
        readers = [PdfReader(input_pdf) for _ in range(4)]
        for i in range(0, len(readers[0].pages)):
            original_media_box = readers[0].pages[i].mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page_1 = readers[0].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                # 参数(0, 0, width / 4, height)表示一个矩形区域的坐标：
                # 前两个参数(0, 0)是左下角的x和y坐标
                # 后两个参数(width / 4, height)是右上角的x和y坐标
                # 这里设置页面的box属性为原始宽度的1/4，即截取PDF页面的左侧四分之一部分
                setattr(left_page_1, box, RectangleObject((0, 0, width / 4, height)))

            left_page_2 = readers[1].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(left_page_2, box, RectangleObject((width / 2, 0, width / 2 + width / 4, height)))

            right_page_1 = readers[2].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(right_page_1, box, RectangleObject((width / 4, 0, width / 2, height)))

            right_page_2 = readers[3].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(right_page_2, box, RectangleObject((width * 3 / 4, 0, width, height)))

            if compare:
                blank_page_1 = writer.add_blank_page(width/2, height)
                blank_page_1.merge_transformed_page(left_page_1, (1, 0, 0, 1, 0, 0))
                blank_page_1.merge_transformed_page(left_page_2, (1, 0, 0, 1, -width / 4, 0))
                blank_page_2 = writer.add_blank_page(width/2, height)
                # merge_transformed_page方法的第二个参数是变换矩阵，格式为(a, b, c, d, e, f)
                # 其中(a, b, c, d)控制缩放和旋转，(e, f)控制平移
                # (1, 0, 0, 1, 0, 0)表示不缩放不旋转，不平移，即原样放置
                # (1, 0, 0, 1, width / 2, 0)表示不缩放不旋转，但在x轴方向平移width/2，即向右移动半页宽度
                blank_page_2.merge_transformed_page(right_page_1, (1, 0, 0, 1, -width / 4, 0))
                blank_page_2.merge_transformed_page(right_page_2, (1, 0, 0, 1, -width / 2, 0))
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
    if 'dual' in input_pdf:
        readers = [PdfReader(input_pdf) for _ in range(4)]
        for i in range(0, len(readers[0].pages), 2):
            original_media_box = readers[0].pages[i].mediabox
            width = original_media_box.width
            height = original_media_box.height

            left_page_1 = readers[0].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(left_page_1, box, RectangleObject((0, 0, width/2, height)))

            left_page_2 = readers[1].pages[i+1]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(left_page_2, box, RectangleObject((0, 0, width/2, height)))

            right_page_1 = readers[2].pages[i]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(right_page_1, box, RectangleObject((width/2, 0, width, height)))

            right_page_2 = readers[3].pages[i+1]
            for box in ['mediabox', 'cropbox', 'trimbox', 'bleedbox', 'artbox']:
                setattr(right_page_2, box, RectangleObject((width/2, 0, width, height)))

            if compare == True:
                blank_page_1 = writer.add_blank_page(width, height)
                blank_page_1.merge_transformed_page(left_page_1, (1, 0, 0, 1, 0, 0))
                blank_page_1.merge_transformed_page(left_page_2, (1, 0, 0, 1, width / 2, 0))
                blank_page_2 = writer.add_blank_page(width, height)
                blank_page_2.merge_transformed_page(right_page_1, (1, 0, 0, 1, -width / 2, 0))
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

# 用于切割双栏pdf文件
@app.route('/cut', methods=['POST'])
def cut():
    print("\n############# Cutting #############")
    input_path, config = get_file_from_request(request)
    try:
        translated_path = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '-cut.pdf'))
        if config.babeldoc:
            split_and_merge_pdf_babeldoc(input_path, translated_path)
        else:
            split_and_merge_pdf(input_path, translated_path)

        if not os.path.exists(translated_path):
            raise Exception("[Failed to generate cut files]: ", translated_path)
        print("[Cut file generated]: ", translated_path)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"[Cut File Error]: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 用于生成中英对照文件
@app.route('/cut-compare', methods=['POST'])
def cut_compare():
    print("\n############# Comparing #############")
    input_path, config = get_file_from_request(request)
    try:
        if 'dual' in input_path:
            translated_path = os.path.join(config.translated_dir, os.path.basename(input_path).replace('.pdf', '-compare.pdf'))
            if config.babeldoc:
                split_and_merge_pdf_babeldoc(input_path, translated_path, compare=True)
            else:
                split_and_merge_pdf(input_path, translated_path, compare=True)
        else:
            _, dual = translate_pdf(input_path, config)
            translated_path = dual.replace('-dual.pdf', '-compare.pdf')
            if config.babeldoc:
                split_and_merge_pdf_babeldoc(dual, translated_path, compare=True)
            else:
                split_and_merge_pdf(dual, translated_path, compare=True)

        if not os.path.exists(translated_path):
            raise Exception("[Failed to generate cutted file]: ", translated_path)
        print("[Compare file generated]: ", translated_path)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"[cut_compare() Error]: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        port_num = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port_num)