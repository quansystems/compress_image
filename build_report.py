"""Tạo báo cáo PDF/DOCX từ kết quả thực nghiệm đã chạy trong code/ket_qua."""
from pathlib import Path
import csv
import html
import platform
import re
import textwrap

import cv2
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
section.top_margin, section.bottom_margin = Cm(2.5), Cm(3)
section.left_margin, section.right_margin = Cm(3), Cm(2)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Times New Roman', Pt(12)
normal.paragraph_format.space_after = Pt(6)
parts = []
tex_parts = []
body_mode = False
main_headings = []
REPO = 'https://github.com/quansystems/compress_image'

def tex(s):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(c, c) for c in s)

def para(s):
    parts.append('<p>' + html.escape(s) + '</p>')
    doc.add_paragraph(s)
    if body_mode:
        tex_parts.append(tex(s) + '\n\n')

def heading(s, level=1):
    parts.append(f'<h{level}>{html.escape(s)}</h{level}>')
    doc.add_heading(s, level=level)
    if body_mode:
        tex_parts.append('\\' + ('section' if level == 1 else 'subsection') + '{' + tex(re.sub(r'^\d+(?:\.\d+)*\.? ', '', s)) + '}\n')
        if level == 1:
            main_headings.append(s)

def page():
    parts.append('<div style="page-break-before:always"></div>')
    doc.add_page_break()
    if body_mode:
        tex_parts.append('\\clearpage\n')

def image(path, caption, width=17):
    parts.append(f'<div class="figure"><img src="{path}" width="450"><p class="caption">{html.escape(caption)}</p></div>')
    doc.add_picture(str(ROOT / path), width=Cm(min(width, 16)))
    doc.add_paragraph(caption, style='Caption')
    if body_mode:
        tex_parts.append('\\begin{figure}[!htbp]\n\\centering\n\\includegraphics[width=\\linewidth]{../' + path + '}\n\\caption{' + tex(re.sub(r'^Hình \d+\. ', '', caption)) + '}\n\\end{figure}\n\\FloatBarrier\n')

def code(s):
    wrapped = '\n'.join('\n'.join(textwrap.wrap(line, 94, subsequent_indent='    ', replace_whitespace=False, drop_whitespace=False)) if len(line)>94 else line for line in s.splitlines())
    parts.append('<pre>' + html.escape(wrapped) + '</pre>')
    p = doc.add_paragraph()
    run = p.add_run(wrapped)
    run.font.name, run.font.size = 'Consolas', Pt(8)
    p.paragraph_format.line_spacing = 1
    if body_mode:
        tex_parts.append('\\begin{Verbatim}[fontsize=\\scriptsize]\n' + wrapped + '\n\\end{Verbatim}\n')

def table(headers, rows):
    parts.append('<table><tr>' + ''.join('<th>'+html.escape(str(x))+'</th>' for x in headers) + '</tr>' + ''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</table>')
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    for c, value in zip(t.rows[0].cells, headers):
        c.text = str(value)
    for row in rows:
        for c, value in zip(t.add_row().cells, row):
            c.text = str(value)
    if body_mode:
        spec = '|'+ '|'.join(f'p{{{(15.2-0.5*len(headers))/len(headers):.2f}cm}}' for _ in headers)+'|'
        tex_parts.append('\\begin{center}\n\\small\\renewcommand{\\arraystretch}{1.3}\n\\begin{tabular}{' + spec + '}\\hline\n' + ' & '.join('\\textbf{'+tex(str(x))+'}' for x in headers) + r' \\ \hline' + '\n' + '\n'.join(' & '.join(tex(str(x)) for x in row)+r' \\ \hline' for row in rows) + '\n\\end{tabular}\n\\end{center}\n')

def link(label, url):
    parts.append(f'<p class="repo"><a href="{html.escape(url)}">{html.escape(label)}</a></p>')
    p = doc.add_paragraph()
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
toc_title = doc.add_heading('MỤC LỤC', level=1)
toc_paragraph = doc.add_paragraph()
toc_field = OxmlElement('w:fldSimple')
toc_field.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
toc_paragraph._p.append(toc_field)
doc.add_page_break()
body_mode = True
heading('1. Mục tiêu và tổ chức thực nghiệm')
para('Bài thực hành xây dựng ba module chia khối, DCT và lượng tử hóa để mô phỏng nén ảnh xám. Mã Zigzag, RLE, Huffman, giải mã, giải lượng tử, IDCT và ghép khối được dùng từ phần A của đề bài, giữ nguyên thuật toán. Kết quả gồm ảnh dựng lại, sai số MSE, độ dài chuỗi bit Huffman và tỉ lệ hệ số bằng 0.')
para('Ảnh đầu vào: RaceHorses_416x240_frame001.png, đọc ở chế độ xám uint8. Trong báo cáo, kích thước luôn viết theo H × W: 240 × 416. Khối mẫu là khối số 0 ở góc trên bên trái. Ảnh kiểm tra đệm là vùng image[:13, :19].')
table(['Thành phần', 'Nội dung'], [
    ['cau1_chia_khoi.py', 'split_blocks; đọc ảnh, lưới khối, thử đệm'],
    ['cau2_dct.py', 'dct_blocks; dịch mức và biểu diễn DCT'],
    ['cau3_luong_tu_hoa.py', 'quantize; chạy 3 mức, lưu ảnh và CSV'],
    ['jpeg_support.py', 'Mã hỗ trợ cho sẵn trong đề bài'],
])
para(f'Môi trường thực nghiệm: Python {platform.python_version()}, NumPy {np.__version__}, OpenCV {cv2.__version__}. Chạy cả ba chương trình với tùy chọn --no-show; số liệu được đọc trực tiếp từ CSV kết quả.')
heading('2. Câu 1 – Chia ảnh thành khối 8×8')
para('Với ảnh H × W, số hàng cần đệm là (-H) mod 8 và số cột cần đệm là (-W) mod 8. Dùng np.pad với mode="edge" để sao chép điểm ảnh biên xuống phía dưới và sang phải. Sắp xếp reshape → transpose → reshape tạo các khối theo thứ tự từ trái sang phải, từ trên xuống dưới.')
table(['Ảnh', 'Trước đệm H × W', 'Sau đệm H × W', 'Số khối', 'blocks.shape'], [
    ['Đầy đủ', '240 × 416', '240 × 416', '1.560', '(1560, 8, 8)'],
    ['Cắt', '13 × 19', '16 × 24', '6', '(6, 8, 8)'],
])
para('Ảnh đầy đủ chia hết cho 8 nên không cần đệm. Ảnh cắt thêm 3 hàng và 5 cột; vùng đệm không được tính vào MSE sau khi ảnh giải mã được cắt về 13 × 19.')
image('code/ket_qua/cau1/chia_khoi.png', 'Hình 1. Ảnh gốc, lưới khối 8×8 và ảnh cắt sau đệm.')
heading('2.1. Ma trận khối mẫu', 2)
matrix('code/ket_qua/cau1/khoi_mau.txt')
page()
heading('3. Câu 2 – Biến đổi DCT')
para('Mỗi khối được chuyển từ uint8 sang float32 trước khi trừ 128 để tránh tràn số. Sau đó cv2.dct tính DCT hai chiều trực chuẩn. Kết quả có kích thước (N, 8, 8), kiểu float32. Dịch mức đưa miền [0, 255] về [-128, 127].')
para('Hệ số DC nằm ở (0, 0): F[0,0] = 8 × (trung bình khối − 128). Khối mẫu có trung bình 153,171875 nên DC = 201,375. Các hệ số AC còn lại mô tả biến thiên theo tần số dọc u và ngang v; chỉ số càng lớn tương ứng dao động càng nhanh.')
heading('3.1. Ma trận DCT của khối mẫu', 2)
matrix('code/ket_qua/cau2/dct_khoi_mau.txt', 2)
image('code/ket_qua/cau2/dct.png', 'Hình 2. Khối mẫu và độ lớn log(1 + |DCT|), kèm thang màu.')
para('DC = 201,375 có độ lớn vượt trội. Một số AC đáng kể gồm F[1,1] ≈ −22,75 và F[3,0] ≈ −22,10, nằm gần vùng tần số thấp. Nhiều hệ số phía dưới bên phải có độ lớn nhỏ, chẳng hạn F[6,6] ≈ 0,14 và F[7,7] ≈ −0,88. Biểu diễn log giúp nhìn thấy cả các AC nhỏ. Sự tập trung năng lượng phụ thuộc nội dung từng khối; khối có biên hoặc kết cấu mạnh vẫn có thể có AC tần số cao đáng kể.')
heading('4. Câu 3 – Lượng tử hóa và dựng lại ảnh')
para('Tạo Q0[u,v] = 8 + 4 × (u + v), với u,v = 0,…,7. Với scale s > 0, tính Q = max(1, round(Q0 × s)) theo từng phần tử, lưu float32. Các hệ số được lượng tử hóa theo quantized = round(coefficients / Q), lưu int32. np.rint làm tròn về số chẵn gần nhất khi đúng nửa đơn vị.')
para('Q tăng theo tần số, nên cùng độ lớn hệ số, các thành phần tần số cao dễ trở thành 0 hơn. Ở scale 1,0, bảng Q tăng từ 8 tại DC đến 64 tại góc dưới bên phải.')
heading('4.1. Bảng Q tại scale = 1,0', 2)
matrix('code/ket_qua/cau3/anh_day_du_Q.txt')
heading('4.2. Khối mẫu sau lượng tử hóa tại scale = 1,0', 2)
matrix('code/ket_qua/cau3/anh_day_du_khoi_luong_tu.txt')
para('DC được làm tròn từ 201,375 / 8 thành 25, giải lượng tử cho 200. Khối mẫu còn 7 hệ số khác 0 trên tổng 64 hệ số, tức 89,0625% bằng 0. Đây là tỉ lệ riêng khối mẫu; tỉ lệ toàn ảnh tại scale 1,0 là khoảng 81,1%.')
heading('4.3. Quy trình mã hóa và chỉ tiêu đánh giá', 2)
para('Quy trình: ảnh xám → chia khối/đệm → trừ 128 → DCT → lượng tử hóa → Zigzag → RLE → Huffman. Giải mã thực hiện các phép ngược, nhân Q, IDCT, cộng 128, ghép khối, cắt bỏ phần đệm, làm tròn và giới hạn về uint8.')
para('MSE = tổng (I[y,x] − Î[y,x])² / (H × W), tính trên ảnh sau khi cắt phần đệm. Tỉ lệ hệ số 0 = số phần tử quantized bằng 0 / (N × 64). Số bit dữ liệu = len(bits), chỉ tính chuỗi Huffman; chưa tính bảng mã, Q và metadata. Các ảnh PNG lưu ra chỉ để quan sát ảnh dựng lại, không biểu diễn dung lượng tệp nén của bộ mô phỏng.')
for prefix, title in [('anh_day_du', '4.4. Kết quả ảnh đầy đủ 240 × 416'), ('anh_cat_13x19', '4.5. Kết quả ảnh cắt 13 × 19')]:
    page()
    heading(title, 2)
    with (ROOT / f'code/ket_qua/cau3/{prefix}_ket_qua.csv').open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    table(['Scale', 'MSE', 'Số bit dữ liệu', 'Hệ số bằng 0 (%)'], [[r['quant_scale'], f"{float(r['MSE']):.4f}", f"{int(r['so_bit_du_lieu']):,}", f"{100*float(r['ti_le_he_so_0']):.3f}"] for r in rows])
    image(f'code/ket_qua/cau3/{prefix}_so_sanh.png', 'Ảnh gốc và ảnh dựng lại tại scale 0,5; 1,0; 3,0 (cùng thang xám 0–255).')
    if prefix == 'anh_day_du':
        para('Tại scale 0,5, ảnh giữ lại nhiều chi tiết hơn, MSE 12,34 và 70,8% hệ số bằng 0. Tại scale 1,0, MSE tăng lên 30,47 và khoảng 81,1% hệ số bằng 0. Tại scale 3,0, MSE đạt 97,46 và khoảng 91,9% hệ số bằng 0; các chi tiết nhỏ và kết cấu bị làm mượt mạnh hơn.')
        para('Từ scale 0,5 đến 3,0, số bit giảm từ 166.471 xuống 47.347 (giảm khoảng 71,6%), trong khi MSE tăng khoảng 7,9 lần. Scale 1,0 là mức trung gian trong ba cấu hình thử nghiệm; lựa chọn thực tế tùy yêu cầu chất lượng và dung lượng.')
    else:
        para('Ảnh cắt có 6 khối sau đệm thành 16 × 24. Ở cả ba mức, ảnh dựng lại đều có kích thước 13 × 19 và kiểu uint8. MSE được đo trên 247 điểm ảnh gốc, còn số bit và tỉ lệ hệ số 0 bao gồm 384 hệ số của các khối sau đệm. Vì vậy không so sánh trực tiếp số bit tuyệt đối của ảnh cắt với ảnh đầy đủ để kết luận hiệu quả nén.')
        para('MSE tăng từ 16,04 lên 77,62 khi tăng scale; số bit giảm từ 480 xuống 63. Tại scale 3,0, 96,4% hệ số bằng 0. Ảnh cắt chứa ít nội dung và nhiều điểm ảnh đệm lặp lại nên có phân bố hệ số khác ảnh đầy đủ.')
heading('4.6. Bước làm mất thông tin và kiểm tra tính đúng', 2)
para('Lượng tử hóa là bước chủ yếu gây mất thông tin: nhiều giá trị DCT khác nhau cùng được làm tròn về một số nguyên, nên nhân lại Q không thể khôi phục chính xác hệ số ban đầu. DCT/IDCT chỉ có sai số tính toán số thực; thao tác làm tròn và cắt về [0,255] khi xuất ảnh cũng có thể bổ sung sai số. Zigzag, RLE và Huffman bảo toàn chính xác các hệ số nguyên đã lượng tử hóa.')
para('Kiểm tra bổ sung đối chiếu hệ số trước mã hóa và sau giải mã bằng np.array_equal; kiểm tra thứ tự ghép khối và giá trị đệm; kiểm tra DCT/IDCT trước lượng tử hóa. Với cả ảnh đầy đủ và ảnh cắt, ở cả ba scale, ảnh dựng lại có đúng kích thước và kiểu dữ liệu yêu cầu. Nhật ký kiểm tra được lưu tại bao_cao/kiem_tra.json.')
page()
heading('5. Kết luận và cách chạy lại')
para('Ba module đáp ứng chuỗi xử lí theo đề bài. Trên dữ liệu thực nghiệm, tăng scale làm tăng tỉ lệ hệ số bằng 0 và giảm độ dài chuỗi Huffman, đồng thời làm tăng MSE. Kiểm tra ảnh cắt xác nhận cơ chế đệm biên và cắt bỏ phần đệm khi giải mã hoạt động đúng. Bộ chương trình mô phỏng các bước nén ảnh xám, không tạo tệp JPEG chuẩn.')
code('python -m pip install -r code/requirements.txt\npython code/cau1_chia_khoi.py --no-show\npython code/cau2_dct.py --no-show\npython code/cau3_luong_tu_hoa.py --no-show')
heading('6. Mã nguồn và tài liệu sử dụng')
para('Toàn bộ mã nguồn, ảnh đầu vào, thư viện cần cài đặt và kết quả thực nghiệm được lưu trong kho GitHub dưới đây. Ba module tự viết là cau1_chia_khoi.py, cau2_dct.py và cau3_luong_tu_hoa.py; jpeg_support.py chứa mã hỗ trợ phần A của đề bài. README hướng dẫn cài đặt và chạy từng câu. Có thể tải toàn bộ kho bằng nút Code → Download ZIP hoặc dùng git clone.')
link(REPO, REPO)
link(REPO + '/tree/main/code', REPO + '/tree/main/code')
para('Kho còn chứa verify_results.py để kiểm tra dữ liệu và build_report.py để tạo lại báo cáo. Nguồn LaTeX theo mẫu nằm trong BaoCaoTemplate/main.tex và BaoCaoTemplate/chapter/08_NenAnh.tex.')
para('Tài liệu sử dụng: Đề bài.pdf, Bài thực hành số 8, gồm yêu cầu Câu 1–3 và mã hỗ trợ phần A. Các bảng, ma trận và hình trong báo cáo được tạo từ ảnh đầu vào có sẵn trong thư mục code.')

css = '''
@font-face {font-family: Times; src: url(times.ttf);}
@font-face {font-family: Times; src: url(timesbd.ttf); font-weight: bold;}
@font-face {font-family: Mono; src: url(consola.ttf);}
body {font-family: Times; font-size: 12pt; line-height: 1.3; color: black;}
h1 {font-size:16pt; margin-top:16pt; margin-bottom:9pt; page-break-after:avoid;}
h2 {font-size:13pt; margin-top:12pt; margin-bottom:7pt; page-break-after:avoid;}
p {margin-top:5pt; margin-bottom:8pt; text-align:justify;}
table {border-collapse:collapse; width:100%; margin-top:8pt; margin-bottom:12pt; font-size:10pt;}
td,th {border:0.5pt solid #a4b5c5; padding:5pt;}
th {font-weight:bold;}
pre {font-family:Mono; font-size:7.5pt; line-height:1.25; margin:8pt 0;}
.caption {font-size:10pt; text-align:center;}
.figure {page-break-inside:avoid;}
.repo {font-size:10pt;}
.cover {text-align:center; padding-top:45pt;}
.cover p {text-align:center; margin-bottom:22pt;}
.cover h1 {font-size:22pt; margin-top:32pt;}
.cover h2 {font-size:19pt;}
'''
archive = fitz.Archive(str(ROOT))
archive.add('C:/Windows/Fonts')
rect = fitz.Rect(0, 0, 595.276, 841.89)
content = fitz.Rect(85.04, 70.87, 538.58, 756.85)
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
        p.insert_text((305, 795), 'i' if index == 1 else str(index-1), fontsize=10)
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
