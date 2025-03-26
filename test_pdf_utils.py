from pypdf import PdfWriter, PdfReader
from pypdf.generic import RectangleObject

# 工具函数, 用于切割双栏pdf文件
def split_and_merge_pdf(input_pdf, output_pdf, compare=False):
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


if __name__ == "__main__":
    split_and_merge_pdf("translated/peters_2018_deep_contextualized_word_representations.pdf", "translated/test_split.pdf", compare=True)

