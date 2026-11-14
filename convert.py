import re
import json
import os

# Thuật toán bóc tách nội dung trong cặp ngoặc nhọn {...} xử lý ngoặc lồng nhau
def parse_brackets(text, start_pos):
    idx = text.find('{', start_pos)
    if idx == -1: return "", -1
    level = 0
    for i in range(idx, len(text)):
        if text[i] == '{': level += 1
        elif text[i] == '}':
            level -= 1
            if level == 0:
                return text[idx+1:i], i+1
    return "", -1

def convert_extest_to_html(tex_file, template_file, output_file):
    # Đọc file LaTeX
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    html_questions = []
    ans_mc, ans_tf, ans_sa = {}, {}, {}
    
    # Tìm tất cả các môi trường \begin{ex} ... \end{ex}
    ex_blocks = re.findall(r'\\begin\{ex\}(.*?)\\end\{ex\}', content, re.DOTALL)
    
    for i, block in enumerate(ex_blocks):
        q_num = i + 1
        q_id = f"q{q_num}"
        
        # 1. Bóc tách Lời giải (\loigiai)
        loigiai_text = ""
        lg_pos = block.find(r'\loigiai')
        if lg_pos != -1:
            loigiai_text, _ = parse_brackets(block, lg_pos)
            block = block[:lg_pos] # Cắt bỏ phần lời giải khỏi block đề bài
            
        # 2. Xử lý Phần I: \choice (Trắc nghiệm 4 lựa chọn)
        if r'\choice' in block and r'\choiceTF' not in block:
            ch_pos = block.find(r'\choice')
            question_text = block[:ch_pos].strip()
            
            options = []
            pos = ch_pos
            for _ in range(4):
                opt, pos = parse_brackets(block, pos)
                options.append(opt)
                
            html = f'<div class="question"><p><b>Câu {q_num}:</b> {question_text}</p>'
            labels = ["A", "B", "C", "D"]
            for idx, opt in enumerate(options):
                if r'\True' in opt:
                    ans_mc[q_id] = labels[idx]
                    opt = opt.replace(r'\True', '').strip()
                html += f'<label class="opt-label"><input type="radio" name="{q_id}" value="{labels[idx]}"> <b>{labels[idx]}.</b> {opt}</label>'
            
            html += f'<div class="explanation"><h4>Lời giải:</h4>{loigiai_text}</div></div>'
            html_questions.append(html)

        # 3. Xử lý Phần II: \choiceTF (Đúng/Sai)
        elif r'\choiceTF' in block:
            ch_pos = block.find(r'\choiceTF')
            question_text = block[:ch_pos].strip()
            
            options = []
            pos = ch_pos
            for _ in range(4):
                opt, pos = parse_brackets(block, pos)
                options.append(opt)
                
            html = f'<div class="question"><p><b>Câu {q_num}:</b> {question_text}</p>'
            html += f'<table class="tf-table"><tr><th>Mệnh đề</th><th>Đúng</th><th>Sai</th></tr>'
            
            labels = ["a", "b", "c", "d"]
            ans_tf[q_id] = {}
            for idx, opt in enumerate(options):
                is_true = r'\True' in opt
                ans_tf[q_id][labels[idx]] = "D" if is_true else "S"
                opt_clean = opt.replace(r'\True', '').strip()
                
                html += f'<tr><td>{labels[idx]}) {opt_clean}</td>'
                html += f'<td><label><input type="radio" name="{q_id}_{labels[idx]}" value="D"></label></td>'
                html += f'<td><label><input type="radio" name="{q_id}_{labels[idx]}" value="S"></label></td></tr>'
            
            html += f'</table><div class="explanation"><h4>Lời giải:</h4>{loigiai_text}</div></div>'
            html_questions.append(html)

        # 4. Xử lý Phần III: \shortans (Trả lời ngắn)
        elif r'\shortans' in block:
            sa_pos = block.find(r'\shortans')
            question_text = block[:sa_pos].strip()
            
            ans_text, _ = parse_brackets(block, sa_pos)
            ans_sa[q_id] = ans_text.replace(',', '.').strip()
            
            html = f'<div class="question"><p><b>Câu {q_num}:</b> {question_text}</p>'
            html += f'<div style="margin:10px 0;">Đáp án: <input type="text" class="sa-input" name="{q_id}" placeholder="Nhập số..."></div>'
            html += f'<div class="explanation"><h4>Lời giải:</h4>{loigiai_text}</div></div>'
            html_questions.append(html)

    # Đóng gói dữ liệu JSON
    full_html = "\n".join(html_questions)
    json_code = f"const correctAnswersMC = {json.dumps(ans_mc)};\n"
    json_code += f"        const correctAnswersTF = {json.dumps(ans_tf)};\n"
    json_code += f"        const correctAnswersSA = {json.dumps(ans_sa)};"

    # Đọc file template.html
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()

    # Bơm dữ liệu vào giao diện
    output = template.replace('<!-- {NOI_DUNG_CAU_HOI} -->', full_html)
    output = output.replace('/* {JSON_DAP_AN} */', json_code)

    # TỰ ĐỘNG TẠO THƯ MỤC NẾU CHƯA TỒN TẠI
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Ghi ra file HTML thành phẩm
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
        
    print(f"✅ Đã tạo web thành công: {output_file} ({len(ex_blocks)} câu hỏi)")

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN CHẠY THỰC TẾ CỦA THẦY
# ==========================================
if __name__ == "__main__":
    convert_extest_to_html(
        tex_file="Khoi12/OnTN2027/TDMT01.tex", 
        template_file="template.html", 
        output_file="Khoi12/OnTN2027/OnTN27_01.html"
    )