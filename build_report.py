"""Tạo báo cáo PDF/DOCX từ kết quả thực nghiệm đã chạy trong code/ket_qua."""
from pathlib import Path
import csv
import html
import re
import textwrap

import numpy as np
import pymupdf as fitz
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'bao_cao'
OUT.mkdir(exist_ok=True)
NAME = '23020761_NguyenVanQuan'
doc = Document()
section = doc.sections[0]
section.page_height, section.page_width = Cm(29.7), Cm(21)
section.top_margin = section.bottom_margin = Cm(2)
section.left_margin, section.right_margin = Cm(3), Cm(2)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Times New Roman', Pt(12)
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.line_spacing = 1.2
parts = []
tex_parts = []
body_mode = False
main_headings = []
heading_group = False
REPO = 'https://github.com/quansystems/compress_image'

def tex(s):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(c, c) for c in s)

def para(s):
    parts.append('<p>' + html.escape(s) + '</p>')
    doc.add_paragraph(s)
    close_heading_group()
    if body_mode:
        tex_parts.append(tex(s) + '\n\n')

def heading(s, level=1):
    global heading_group
    if not heading_group:
        parts.append('<div class="keep">')
        heading_group = True
    parts.append(f'<h{level}>{html.escape(s)}</h{level}>')
    doc.add_heading(s, level=level)
    if body_mode:
        tex_parts.append('\\' + ('section' if level == 1 else 'subsection') + '{' + tex(re.sub(r'^\d+(?:\.\d+)*\.? ', '', s)) + '}\n')
        if level == 1:
            main_headings.append(s)

def close_heading_group():
    global heading_group
    if heading_group:
        parts.append('</div>')
        heading_group = False

def page():
    parts.append('<div style="page-break-before:always"></div>')
    doc.add_page_break()
    if body_mode:
        tex_parts.append('\\clearpage\n')

def image(path, caption, width=17):
    parts.append(f'<div class="figure"><img src="{path}" width="450"><p class="caption">{html.escape(caption)}</p></div>')
    doc.add_picture(str(ROOT / path), width=Cm(min(width, 16)))
    doc.add_paragraph(caption, style='Caption')
    close_heading_group()
    if body_mode:
        tex_parts.append('\\begin{figure}[!htbp]\n\\centering\n\\includegraphics[width=\\linewidth]{../' + path + '}\n\\caption{' + tex(re.sub(r'^Hình \d+\. ', '', caption)) + '}\n\\end{figure}\n\\FloatBarrier\n')

def code(s):
    wrapped = '\n'.join('\n'.join(textwrap.wrap(line, 94, subsequent_indent='    ', replace_whitespace=False, drop_whitespace=False)) if len(line)>94 else line for line in s.splitlines())
    parts.append('<pre style="page-break-inside:avoid">' + html.escape(wrapped) + '</pre>')
    close_heading_group()
    p = doc.add_paragraph()
    run = p.add_run(wrapped)
    run.font.name, run.font.size = 'Consolas', Pt(8)
    p.paragraph_format.line_spacing = 1
    if body_mode:
        tex_parts.append('\\begin{Verbatim}[fontsize=\\scriptsize]\n' + wrapped + '\n\\end{Verbatim}\n')

def table(headers, rows):
    parts.append('<div class="keep"><table><tr>' + ''.join('<th>'+html.escape(str(x))+'</th>' for x in headers) + '</tr>' + ''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</table></div>')
    close_heading_group()
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    for c, value in zip(t.rows[0].cells, headers):
        c.text = str(value)
    for row in rows:
        for c, value in zip(t.add_row().cells, row):
            c.text = str(value)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    if body_mode:
        spec = '|'+ '|'.join(f'p{{{(15.2-0.5*len(headers))/len(headers):.2f}cm}}' for _ in headers)+'|'
        tex_parts.append('\\begin{center}\n\\small\\renewcommand{\\arraystretch}{1.3}\n\\begin{tabular}{' + spec + '}\\hline\n' + ' & '.join('\\textbf{'+tex(str(x))+'}' for x in headers) + r' \\ \hline' + '\n' + '\n'.join(' & '.join(tex(str(x)) for x in row)+r' \\ \hline' for row in rows) + '\n\\end{tabular}\n\\end{center}\n')

def link(label, url):
    parts.append(f'<p class="repo"><a href="{html.escape(url)}">{html.escape(label)}</a></p>')
    close_heading_group()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), 'F5F7FA')
    p._p.get_or_add_pPr().append(shading)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), p.part.relate_to(url, RT.HYPERLINK, is_external=True))
    run = OxmlElement('w:r')
    props = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '0000FF')
    props.append(color)
    run.append(props)
    text = OxmlElement('w:t')
    text.text = label
    run.append(text)
    hyperlink.append(run)
    p._p.append(hyperlink)
    tex_parts.append('\\noindent\\href{' + url + '}{\\nolinkurl{' + label + '}}\\par\n')

def matrix(path, decimals=0):
    a = np.loadtxt(ROOT / path)
    code('\n'.join(' '.join(f'{x:8.{decimals}f}' for x in row) for row in a))

parts.append('<div class="cover">')
para('ĐẠI HỌC QUỐC GIA HÀ NỘI')
para('TRƯỜNG ĐẠI HỌC CÔNG NGHỆ')
parts.append('<p><img src="BaoCaoTemplate/figures/UET_logo.jpg" width="90"></p>')
doc.add_picture(str(ROOT / 'BaoCaoTemplate/figures/UET_logo.jpg'), width=Cm(3))
heading('BÁO CÁO THỰC HÀNH SỐ 8')
heading('MÔ PHỎNG NÉN ẢNH XÁM', 2)
para('Chia khối 8×8 – Biến đổi DCT – Lượng tử hóa')
para('Sinh viên thực hiện: Nguyễn Văn Quân')
para('Mã sinh viên: 23020761')
para('Học phần: Xử lí ảnh và thị giác')
para('Người hướng dẫn 1: PGS. Hoàng Văn Xiêm')
para('Người hướng dẫn 2: ThS. Bùi Đình Đăng')
para('HÀ NỘI - 2026')
parts.append('</div>')
page()
parts.clear()
heading_group = False
toc_title = doc.add_heading('MỤC LỤC', level=1)
toc_paragraph = doc.add_paragraph()
toc_field = OxmlElement('w:fldSimple')
toc_field.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
toc_paragraph._p.append(toc_field)
doc.add_page_break()
body_mode = True
heading('1. Câu 1 – Chia ảnh thành khối 8×8')
heading('1.1. Cách thực hiện', 2)
para('Đọc ảnh RaceHorses_416x240_frame001.png ở chế độ ảnh xám. Ảnh có chiều cao 240 và chiều rộng 416 điểm ảnh, kiểu uint8. Trong báo cáo, kích thước được viết theo thứ tự chiều cao × chiều rộng.')
para('Hàm split_blocks(image) chia ảnh thành các khối 8×8, lấy từ trái sang phải rồi từ trên xuống dưới. Hàm trả về blocks là mảng (N, 8, 8), original_shape là kích thước ảnh ban đầu và padded_shape là kích thước sau đệm. N là số khối.')
para('Nếu kích thước chưa chia hết cho 8, chương trình thêm hàng ở dưới và cột ở bên phải bằng cách lặp lại giá trị điểm ảnh biên. Số hàng thêm là (-H) mod 8, số cột thêm là (-W) mod 8. Việc đệm dùng np.pad với mode="edge".')
heading('1.2. Kết quả', 2)
table(['Ảnh', 'Trước đệm H × W', 'Sau đệm H × W', 'Số khối', 'blocks.shape'], [
    ['Đầy đủ', '240 × 416', '240 × 416', '1.560', '(1560, 8, 8)'],
    ['Cắt', '13 × 19', '16 × 24', '6', '(6, 8, 8)'],
])
para('Ảnh đầy đủ không cần đệm vì cả hai chiều đều chia hết cho 8. Để thử trường hợp cần đệm, lấy vùng 13×19 ở góc trên bên trái bằng image[:13, :19]. Ảnh cắt được thêm 3 hàng và 5 cột, thành 16×24 và chia được 6 khối.')
image('code/ket_qua/cau1/chia_khoi.png', 'Hình 1. Ảnh gốc, lưới khối 8×8 và ảnh cắt sau đệm.')
para('Chọn khối số 0 ở góc trên bên trái làm khối mẫu. Ma trận điểm ảnh của khối này là:')
matrix('code/ket_qua/cau1/khoi_mau.txt')
heading('2. Câu 2 – Biến đổi DCT')
heading('2.1. Cách thực hiện', 2)
para('Hàm dct_blocks(blocks) chuyển từng khối sang float32, trừ 128 rồi gọi cv2.dct. Cần đổi kiểu dữ liệu trước khi trừ để các giá trị âm được tính đúng. Kết quả là mảng hệ số DCT có cùng kích thước (N, 8, 8), kiểu float32.')
page()
heading('2.2. Kết quả của khối mẫu', 2)
para('Dùng lại khối số 0 ở Câu 1. Ma trận DCT nhận được là:')
matrix('code/ket_qua/cau2/dct_khoi_mau.txt', 2)
para('Hệ số DC ở vị trí (0, 0) bằng 201,375. Hệ số này thể hiện độ sáng trung bình của khối sau khi trừ 128. Với khối 8×8, DC = 8 × (trung bình khối − 128). Trung bình của khối mẫu là 153,171875.')
para('63 hệ số còn lại là AC, thể hiện sự thay đổi độ sáng trong khối theo chiều ngang và chiều dọc. Các vị trí gần góc trên bên trái là tần số thấp, thường mô tả vùng sáng thay đổi chậm. Các vị trí xa góc này là tần số cao, thường mô tả chi tiết nhỏ và đường biên.')
image('code/ket_qua/cau2/dct.png', 'Hình 2. Khối mẫu và ảnh màu log(1 + |DCT|), kèm thang màu.')
para('Trong khối mẫu, DC có độ lớn lớn nhất. Một số AC gần góc trên bên trái cũng khá lớn, như F[1,1] ≈ −22,75 và F[3,0] ≈ −22,10. Nhiều hệ số ở góc dưới bên phải nhỏ hơn, như F[6,6] ≈ 0,14 và F[7,7] ≈ −0,88. Như vậy, các hệ số lớn chủ yếu nằm ở vùng tần số thấp. Cách vẽ log giúp nhìn rõ cả những hệ số nhỏ.')
heading('3. Câu 3 – Lượng tử hóa và dựng lại ảnh')
heading('3.1. Cách lượng tử hóa', 2)
para('Hàm quantize(coefficients, quant_scale) nhận các hệ số DCT và mức lượng tử quant_scale > 0. Bảng Q được tính theo từng phần tử như sau:')
code('Q0[u, v] = 8 + 4 × (u + v), với u, v từ 0 đến 7\nQ = max(1, round(Q0 × quant_scale))\nquantized = round(coefficients / Q)')
para('Hàm trả về quantized là mảng số nguyên int32 kích thước (N, 8, 8), và Q là bảng float32 kích thước 8×8. Có thể hiểu lượng tử hóa là chia mỗi hệ số DCT cho giá trị tương ứng trong Q rồi làm tròn. Q càng lớn thì các hệ số nhỏ càng dễ trở thành 0.')
page()
heading('3.2. Kết quả tại quant_scale = 1,0', 2)
para('Bảng Q tại mức 1,0:')
matrix('code/ket_qua/cau3/anh_day_du_Q.txt')
para('Khối mẫu sau lượng tử hóa:')
matrix('code/ket_qua/cau3/anh_day_du_khoi_luong_tu.txt')
para('Ví dụ, DC được tính bằng round(201,375 / 8) = 25. Với toàn ảnh, tỉ lệ hệ số bằng 0 tại mức 1,0 là 81,146%. Tỉ lệ này được tính bằng số hệ số bằng 0 chia cho tổng số hệ số, rồi nhân 100%.')
heading('3.3. Mã hóa, dựng lại ảnh và cách đo', 2)
para('Dùng nguyên mã hỗ trợ trong jpeg_support.py của đề bài để mã hóa bằng Zigzag, RLE và Huffman. Khi dựng lại ảnh, chương trình giải mã, nhân lại Q, dùng IDCT, cộng 128 rồi ghép các khối. Cuối cùng, bỏ phần đệm và đưa điểm ảnh về kiểu uint8, trong khoảng 0–255.')
para('MSE là trung bình bình phương chênh lệch giữa điểm ảnh gốc và điểm ảnh dựng lại. MSE càng nhỏ thì ảnh dựng lại càng gần ảnh gốc. MSE chỉ được tính trên vùng ảnh ban đầu, sau khi bỏ phần đệm.')
para('Số bit dữ liệu là độ dài chuỗi Huffman, chưa gồm bảng mã, Q và thông tin đi kèm. Đây không phải dung lượng file JPEG chuẩn. Các ảnh PNG chỉ dùng để quan sát kết quả.')
for prefix, title in [('anh_day_du', '3.4. Kết quả ảnh đầy đủ 240 × 416'), ('anh_cat_13x19', '3.5. Kết quả ảnh cắt 13 × 19')]:
    heading(title, 2)
    with (ROOT / f'code/ket_qua/cau3/{prefix}_ket_qua.csv').open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    table(['Scale', 'MSE', 'Số bit dữ liệu', 'Hệ số bằng 0 (%)'], [[r['quant_scale'], f"{float(r['MSE']):.4f}", f"{int(r['so_bit_du_lieu']):,}", f"{100*float(r['ti_le_he_so_0']):.3f}"] for r in rows])
    number = 3 if prefix == 'anh_day_du' else 4
    image(f'code/ket_qua/cau3/{prefix}_so_sanh.png', f'Hình {number}. Từ trái sang phải: ảnh gốc và ảnh dựng lại ở mức 0,5; 1,0; 3,0.')
    if prefix == 'anh_day_du':
        para('Ở mức 0,5, ảnh giữ được nhiều chi tiết nhất trong ba mức thử, MSE là 12,34 và số bit là 166.471. Ở mức 1,0, một số chi tiết nhỏ giảm đi, MSE tăng lên 30,47 và số bit còn 108.113. Ở mức 3,0, ảnh mờ hơn, mất nhiều chi tiết hơn; MSE tăng lên 97,46 và số bit còn 47.347.')
        para('Khi tăng mức lượng tử, số hệ số bằng 0 tăng từ khoảng 70,8% lên 91,9%. Nhiều số 0 giúp bước mã hóa cần ít bit hơn. Kết quả cho thấy phải đánh đổi giữa chất lượng ảnh và số bit dữ liệu.')
    else:
        para('Ảnh cắt cũng cho kết quả tương tự: khi tăng mức lượng tử từ 0,5 lên 3,0, MSE tăng từ 16,04 lên 77,62, còn số bit giảm từ 480 xuống 63. Tỉ lệ hệ số bằng 0 tăng từ khoảng 74,0% lên 96,4%.')
        para('Ảnh cắt được đệm thành 16×24 để xử lí. Khi dựng lại, chương trình bỏ phần đệm để trả về đúng 13×19. MSE được tính trên 247 điểm ảnh ban đầu; số bit và tỉ lệ hệ số bằng 0 tính trên toàn bộ 6 khối sau đệm.')
heading('3.6. Bước làm mất thông tin', 2)
para('Lượng tử hóa là bước chính làm mất thông tin. Khi chia rồi làm tròn, nhiều giá trị khác nhau trở thành cùng một số nguyên. Vì vậy, nhân lại với Q không lấy lại được chính xác giá trị ban đầu. Ví dụ, DC của khối mẫu là 201,375; sau lượng tử hóa được 25, nhân lại Q chỉ được 200.')
para('Zigzag, RLE và Huffman không làm mất các hệ số nguyên đã lượng tử hóa. DCT và IDCT có sai số tính toán nhỏ. Việc làm tròn và giới hạn điểm ảnh về 0–255 khi xuất ảnh cũng có thể tạo thêm sai số.')
heading('3.7. Kiểm tra kích thước ảnh dựng lại', 2)
table(['Ảnh', 'Kích thước gốc', 'Dựng lại ở cả 3 mức', 'Kiểu dữ liệu'], [
    ['Đầy đủ', '240 × 416', '240 × 416', 'uint8'],
    ['Cắt có đệm', '13 × 19', '13 × 19', 'uint8'],
])
para('Cả 6 trường hợp đều trả về đúng kích thước và kiểu dữ liệu của ảnh đầu vào. Kiểm tra thêm cho thấy các hệ số nguyên trước mã hóa và sau giải mã giống nhau hoàn toàn.')
heading('4. Mã nguồn')
link(REPO, REPO)

css = '''
@font-face {font-family: Times; src: url(times.ttf);}
@font-face {font-family: Times; src: url(timesbd.ttf); font-weight: bold;}
@font-face {font-family: Mono; src: url(consola.ttf);}
body {font-family: Times; font-size: 12pt; line-height: 1.2; color: black;}
h1 {font-size:16pt; margin-top:10pt; margin-bottom:6pt; page-break-after:avoid;}
h2 {font-size:13pt; margin-top:7pt; margin-bottom:4pt; page-break-after:avoid;}
p {margin-top:2pt; margin-bottom:4pt; text-align:justify;}
table {border-collapse:collapse; width:100%; margin-top:5pt; margin-bottom:6pt; font-size:10pt;}
td,th {border:0.5pt solid #a4b5c5; padding:4pt;}
th {font-weight:bold;}
pre {font-family:Mono; font-size:7.5pt; line-height:1.25; margin:6pt 0;}
.caption {font-size:10pt; text-align:center;}
.figure {page-break-inside:avoid;}
.keep {page-break-inside:avoid;}
.repo {font-size:11pt; text-align:center; padding:8pt; border:0.5pt solid #a4b5c5; background-color:#f5f7fa;}
.cover {text-align:center; padding-top:45pt;}
.cover p {text-align:center; margin-bottom:22pt;}
.cover h1 {font-size:22pt; margin-top:32pt;}
.cover h2 {font-size:19pt;}
'''
archive = fitz.Archive(str(ROOT))
archive.add('C:/Windows/Fonts')
rect = fitz.Rect(0, 0, 595.276, 841.89)
content = fitz.Rect(85.04, 56.69, 538.58, 785.20)
story = fitz.Story(html=''.join(parts), user_css=css, archive=archive)
body_pdf = story.write_with_links(lambda *_: (rect, content, None))
pdf = fitz.open()
cover = pdf.new_page(width=rect.width, height=rect.height)
cover.draw_rect(fitz.Rect(87.48, 50.4, rect.width-50.4, rect.height-50.4), width=3)
fontfiles = {'regular': 'times.ttf', 'bold': 'timesbd.ttf'}
for key, filename in fontfiles.items():
    cover.insert_font(fontname=key, fontfile='C:/Windows/Fonts/'+filename)
def cover_text(text, y, size=12, bold=False):
    cover.insert_textbox(fitz.Rect(95, y, 537, y+60), text, fontname='bold' if bold else 'regular', fontsize=size, align=1)
cover_text('ĐẠI HỌC QUỐC GIA HÀ NỘI', 62, 12, True)
cover_text('TRƯỜNG ĐẠI HỌC CÔNG NGHỆ', 81, 12, True)
cover.insert_image(fitz.Rect(270, 155, 361, 246), filename=str(ROOT/'BaoCaoTemplate/figures/UET_logo.jpg'), keep_proportion=True)
cover_text('BÁO CÁO THỰC HÀNH SỐ 8\nMÔ PHỎNG NÉN ẢNH XÁM', 310, 17, True)
cover_text('Chia khối 8×8 – Biến đổi DCT – Lượng tử hóa', 367, 12)
for i, line in enumerate(['Sinh viên thực hiện: Nguyễn Văn Quân', 'Mã sinh viên: 23020761', 'Người hướng dẫn 1: PGS. Hoàng Văn Xiêm', 'Người hướng dẫn 2: ThS. Bùi Đình Đăng', 'Lớp: Xử lí ảnh và thị giác']):
    cover_text(line, 465+i*25, 13, True)
cover_text('HÀ NỘI - 2026', 745, 12, True)
toc = pdf.new_page(width=rect.width, height=rect.height)
toc.insert_font(fontname='regular', fontfile='C:/Windows/Fonts/times.ttf')
toc.insert_font(fontname='bold', fontfile='C:/Windows/Fonts/timesbd.ttf')
toc.insert_text((250, 100), 'MỤC LỤC', fontname='bold', fontsize=16)
pdf.insert_pdf(body_pdf)
entries = []
for title in main_headings:
    for i in range(2, len(pdf)):
        lines = pdf[i].get_text().replace('\u00a0', ' ').splitlines()
        if title in lines:
            entries.append((title, i))
            break
for j, (title, page_index) in enumerate(entries):
    y = 145+j*34
    toc = pdf[1]
    toc.insert_text((85, y), title, fontname='regular', fontsize=12)
    toc.insert_text((520, y), str(page_index-1), fontname='regular', fontsize=12)
    toc.insert_link({'kind': fitz.LINK_GOTO, 'from': fitz.Rect(85,y-14,535,y+5), 'page':page_index})
    cached = OxmlElement('w:r')
    cached_text = OxmlElement('w:t')
    cached_text.text = title
    cached.append(cached_text)
    toc_field.append(cached)
    linebreak = OxmlElement('w:r')
    linebreak.append(OxmlElement('w:br'))
    toc_field.append(linebreak)
pdf.set_toc([[1, title, i+1] for title, i in entries])
pdf.set_metadata({'title': 'Báo cáo thực hành số 8 – Mô phỏng nén ảnh xám', 'author': 'Nguyễn Văn Quân – 23020761'})
for index, p in enumerate(pdf):
    if index:
        p.insert_text((305, 810), 'i' if index == 1 else str(index-1), fontsize=10)
pdf.save(OUT / f'{NAME}.pdf', deflate=True)
for style in ['Title', 'Heading 1', 'Heading 2']:
    doc.styles[style].font.name = 'Times New Roman'
    doc.styles[style].font.color.rgb = RGBColor(0, 0, 0)
# Khung bìa chỉ áp dụng trang đầu, đúng bố cục Bia.tex.
borders = OxmlElement('w:pgBorders')
borders.set(qn('w:offsetFrom'), 'page')
borders.set(qn('w:display'), 'firstPage')
for side in ['top', 'left', 'bottom', 'right']:
    border = OxmlElement('w:'+side)
    for key, value in {'val':'single', 'sz':'24', 'space':'24', 'color':'000000'}.items():
        border.set(qn('w:'+key), value)
    borders.append(border)
section._sectPr.append(borders)
for p in doc.paragraphs:
    if p == toc_title:
        break
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p.text == 'HÀ NỘI - 2026':
        break
section.different_first_page_header_footer = True
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
number = OxmlElement('w:fldSimple')
number.set(qn('w:instr'), 'PAGE')
footer._p.append(number)
doc.save(OUT / f'{NAME}.docx')
(ROOT/'BaoCaoTemplate/chapter/08_NenAnh.tex').write_text(''.join(tex_parts).rstrip() + '\n', encoding='utf-8')
print(f'Created {NAME}.pdf ({len(pdf)} pages) and DOCX')
pdf.close()
