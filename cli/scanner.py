# ============================================================
# scanner.py — 通用题型分类引擎
# ============================================================
import re

VALID_L1_KEYWORDS = [
    "阅读", "文言文", "古诗", "诗歌", "诗词", "词阅读",
    "语言文字", "写作", "作文", "默写", "名句", "基础知识",
    "现代文", "古代诗文", "古代诗歌",
]

def _is_valid_l1_header(text):
    for kw in VALID_L1_KEYWORDS:
        if kw in text:
            return True
    if re.search(r'[（(]\d+分[）)]', text):
        return True
    if re.search(r'^第[一二三四五六七八九十百]+[部分卷大题]', text):
        return True
    return False

PATTERN_L2 = re.compile(r'^[（(][一二三四五六七八九十百]+[）)]')

TYPE_KEYWORDS = {
    "论述类文本": [
        "（一）现代文阅读Ⅰ", "（一）现代文阅读I", "（一）现代文阅读1",
        "（一）阅读Ⅰ", "（一）阅读I", "（一）阅读1",
        "现代文阅读Ⅰ（19分）", "现代文阅读I（19分）",
        "论述类", "信息类", "论述文",
    ],
    "文学类文本": [
        "（二）现代文阅读Ⅱ", "（二）现代文阅读II", "（二）现代文阅读2",
        "（二）阅读Ⅱ", "（二）阅读II", "（二）阅读2",
        "现代文阅读Ⅱ（16分）", "现代文阅读II（16分）",
        "文学类", "文学",
    ],
    "文言文阅读": [
        "（一）文言文阅读", "（一）文言文",
        "文言文阅读", "文言文", "课外文言文",
        "（三）阅读Ⅲ", "（三）阅读III",
        "（一）古代诗文阅读", "古代诗文阅读Ⅰ",
    ],
    "古诗词阅读": [
        "（二）古代诗歌阅读", "（二）古代诗歌",
        "古代诗歌阅读", "古代诗歌鉴赏", "古诗阅读",
        "诗歌阅读", "诗歌鉴赏", "古诗词", "古代诗歌",
        "课外古代诗歌",
        "（四）阅读Ⅳ", "（四）阅读IV",
        "（二）古代诗文阅读", "古代诗文阅读Ⅱ",
    ],
}

NON_TARGET_KEYWORDS = [
    "名篇名句默写", "名句默写", "古诗文默写",
    "语言文字运用", "语用",
    "作文", "写作", "作文题",
    "课内基础知识", "课内知识", "基础知识",
    "课内文言知识", "课内文言文知识", "课内文言基础", "课内文言",
    "文言常识", "文言文常识", "文言文知识",
    "课内古诗文阅读", "课内古诗文",
    "表达题", "表达",
    "（三）古代诗文阅读", "古代诗文阅读Ⅲ",
]

CLASSICAL_WORDS = set("之乎者也矣焉哉欤耶兮尔乃其以于而则虽然苟倘盍曷诸旃")

INSTRUCTION_PATTERNS = [
    "阅读下面的文字，完成下面小题",
    "阅读下面的文字，完成小题",
    "阅读下面的文言文，完成下面小题",
    "阅读下面的诗歌，完成下面小题",
    "阅读下面的材料，完成下面小题",
    "阅读下面的文字，完成各小题",
    "阅读下面的古诗文，完成下面小题",
    "阅读下面的词，完成下面小题",
    "阅读下面这首",
    "阅读下面两首",
]

MATERIAL_PATTERNS = [
    re.compile(r'^材料[一二三四五六七八九十\d]'),
    re.compile(r'^文本[一二三四五六七八九十\d]'),
]


def _extract_headers(doc):
    l1_list = []
    l2_list = []
    PATTERN_L1 = re.compile(r'^[一二三四五六七八九十百]+[、.．]')
    PATTERN_L2 = re.compile(r'^[（(][一二三四五六七八九十百]+[）)]')

    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if not t:
            continue

        if PATTERN_L1.match(t):
            if not _is_valid_l1_header(t):
                continue
            l1_list.append((i, t))
            remaining = t
            l1_match = PATTERN_L1.match(t)
            if l1_match:
                remaining = t[l1_match.end():]
            while True:
                l2_embedded = re.search(r'[（(][一二三四五六七八九十百]+[）)]', remaining)
                if not l2_embedded:
                    break
                l2_start = l2_embedded.start()
                l2_end = l2_embedded.end()
                l2_num = remaining[l2_start:l2_end]
                l2_text = l2_num
                rest_after = remaining[l2_end:].strip()
                next_l2 = re.search(r'[（(][一二三四五六七八九十百]+[）)]', rest_after)
                if next_l2:
                    l2_text += rest_after[:next_l2.start()].strip()
                else:
                    l2_text += rest_after
                l2_list.append((i, l2_text))
                remaining = remaining[l2_end:]

        elif PATTERN_L2.match(t):
            t_rest = t[PATTERN_L2.match(t).end():].strip()
            if t_rest:
                l2_list.append((i, t))

    return l1_list, l2_list


def _build_hierarchy(l1_list, l2_list, total_paras):
    hierarchy = []

    for li, (l1_idx, l1_text) in enumerate(l1_list):
        l1_end = l1_list[li + 1][0] - 1 if li + 1 < len(l1_list) else total_paras - 1

        children = []
        for ci, (l2_idx, l2_text) in enumerate(l2_list):
            if not (l1_idx <= l2_idx < l1_end):
                continue
            next_l2_idx = l2_list[ci + 1][0] if ci + 1 < len(l2_list) else l1_end + 1
            l2_end = next_l2_idx - 1
            if l2_end > l1_end:
                l2_end = l1_end
            actual_start = l2_idx + 1 if l2_idx == l1_idx else l2_idx
            children.append((l2_idx, l2_text, actual_start, l2_end))

        if children and children[0][0] > l1_idx + 1:
            pre_end = children[0][0] - 1
            if pre_end >= l1_idx + 1:
                first = children[0]
                cleaned_l1 = re.sub(r'^[一二三四五六七八九十百]+[、.．]\s*', '', l1_text)
                merged = (first[0], f"（前）{cleaned_l1}", l1_idx + 1, first[3])
                children[0] = merged

        hierarchy.append({
            "l1_idx": l1_idx,
            "l1_text": l1_text,
            "l1_start": l1_idx,
            "l1_end": l1_end,
            "children": children,
        })

    return hierarchy


def _get_text_in_range(doc, start, end, max_paras=50):
    texts = []
    for i in range(start, min(end + 1, start + max_paras)):
        t = doc.paragraphs[i].text.strip()
        if t:
            texts.append(t)
    return "\n".join(texts)


def _detect_wenyan(text):
    if not text:
        return 0.0
    total = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    if total == 0:
        return 0.0
    classical_count = sum(1 for c in text if c in CLASSICAL_WORDS)
    return classical_count / total


def _detect_poem(text):
    if not text:
        return 0.0
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return 0.0
    filtered = []
    for line in lines:
        is_instruction = False
        for pat in INSTRUCTION_PATTERNS:
            if pat in line:
                is_instruction = True
                break
        if not is_instruction:
            filtered.append(line)
    if not filtered:
        return 0.0
    poem_lines = 0
    for line in filtered:
        clean = re.sub(r'[\s，。！？、；：""''「」『』（）、]', '', line)
        if 4 <= len(clean) <= 14:
            if '，' in line or '。' in line or '？' in line:
                poem_lines += 1
    return poem_lines / len(filtered)


def _detect_essay_type(text):
    if not text:
        return None
    lunshu_markers = [
        "材料1", "材料一", "材料2", "材料二", "材料3", "材料三",
        "下列对原文相关内容的理解和分析",
        "下列对材料", "根据原文内容",
        "下列说法不正确", "下列说法正确",
        "下列关于原文", "下列说法有误",
    ]
    wenxue_markers = [
        "下列对文本相关内容和艺术特色的分析",
        "下列对小说", "下列关于文本",
        "叙事", "小说", "散文", "主人公",
        "描写", "刻画", "形象", "艺术特色",
    ]
    lunshu_score = sum(1 for m in lunshu_markers if m in text)
    wenxue_score = sum(1 for m in wenxue_markers if m in text)
    if lunshu_score >= 1 and lunshu_score >= wenxue_score:
        return "lunshu"
    if wenxue_score >= 1 and wenxue_score >= lunshu_score:
        return "wenxue"
    return None


def _classify_by_content(doc, start, end):
    text = _get_text_in_range(doc, start, end)
    if not text:
        return None

    for i in range(start, min(end + 1, start + 5)):
        t = doc.paragraphs[i].text.strip()
        if not t:
            continue
        if "补写出" in t or "补写下列" in t:
            return None
        if "文言文" in t:
            return "文言文阅读"
        if "这首" in t and any(kw in t for kw in ["诗", "词", "曲"]):
            return "古诗词阅读"
        if any(kw in t for kw in ["诗歌", "古诗", "词阅读", "这首词", "这首诗"]):
            return "古诗词阅读"

    if _detect_poem(text) > 0.3:
        return "古诗词阅读"

    if _detect_wenyan(text) > 0.05:
        has_wenyan_marker = any(
            any(kw in doc.paragraphs[i].text for kw in
                ["参考译文", "全文译文", "阅读下面的文言文"])
            for i in range(start, end + 1)
        )
        if has_wenyan_marker:
            return "文言文阅读"
        return None

    etype = _detect_essay_type(text)
    if etype == "lunshu":
        return "论述类文本"
    if etype == "wenxue":
        return "文学类文本"

    return None


def _classify_by_keywords(name_text):
    for typ, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in name_text:
                return typ
    return None


def _find_all_instructions(doc, start, end):
    positions = []
    for i in range(start, end + 1):
        t = doc.paragraphs[i].text.strip()
        for pat in INSTRUCTION_PATTERNS:
            if pat in t:
                positions.append(i)
                break
    return positions


def _split_section_by_content(doc, start, end):
    instructions = _find_all_instructions(doc, start, end)

    if len(instructions) >= 2:
        parts = []
        prev = start
        for inst_pos in instructions:
            if inst_pos > prev:
                parts.append((prev, inst_pos - 1))
            inst_text = doc.paragraphs[inst_pos].text.strip()
            has_content = False
            for pat in INSTRUCTION_PATTERNS:
                if pat in inst_text:
                    after_inst = inst_text[inst_text.index(pat) + len(pat):].strip()
                    if len(after_inst) > 20:
                        has_content = True
                    break
            if has_content:
                prev = inst_pos
            else:
                prev = inst_pos + 1
        if prev <= end:
            parts.append((prev, end))
        return parts

    if len(instructions) == 1:
        inst = instructions[0]
        if inst > start + 3:
            return [(start, inst - 1), (inst, end)]
        else:
            return [(start, end)]

    material_positions = []
    for i in range(start, end + 1):
        t = doc.paragraphs[i].text.strip()
        for mp in MATERIAL_PATTERNS:
            if mp.match(t):
                material_positions.append(i)
                break

    if len(material_positions) >= 3:
        parts = []
        prev = start
        for mp in sorted(material_positions):
            if mp - prev > 5:
                parts.append((prev, mp - 1))
            prev = mp
        if prev <= end:
            parts.append((prev, end))
        return parts if len(parts) > 1 else [(start, end)]

    return [(start, end)]


def _try_classify_sub_regions(doc, start, end):
    sub_parts = _split_section_by_content(doc, start, end)

    if len(sub_parts) <= 1:
        typ = _classify_by_content(doc, start, end)
        return {typ: (start, end)} if typ else None

    result = {}
    for s, e in sub_parts:
        text_sample = _get_text_in_range(doc, s, min(s + 5, e))
        typ = _classify_by_content(doc, s, e)
        if typ:
            if typ in result:
                old_s, old_e = result[typ]
                if e >= old_e - 2 and s <= old_s + 2:
                    result[typ] = (min(s, old_s), max(e, old_e))
                else:
                    result[typ] = (s, e)
            else:
                result[typ] = (s, e)

    return result if result else None


def scan_paper(doc, fname, verbose=False):
    total = len(doc.paragraphs)
    l1_list, l2_list = _extract_headers(doc)

    if not l1_list:
        if verbose:
            print(f"  [verbose] [{fname[:30]}...] 未检测到 L1 标题")
        return None

    if verbose:
        print(f"  [verbose] [{fname[:30]}...] L1 headers:")
        for idx, text in l1_list:
            print(f"      P{idx}: {text[:60]}")
        print("  [verbose] L2 headers:")
        for idx, text in l2_list:
            print(f"      P{idx}: {text[:60]}")

    hierarchy = _build_hierarchy(l1_list, l2_list, total)

    if verbose:
        print("  [verbose] Hierarchy nodes:")
        for node in hierarchy:
            if node["children"]:
                for l2_idx, l2_text, l2_start, l2_end in node["children"]:
                    print(f"      L2: P{l2_start}-P{l2_end}  {l2_text[:60]}")
            else:
                print(f"      L1: P{node['l1_start']}-P{node['l1_end']}  {node['l1_text'][:60]}")

    leaf_sections = []

    for node in hierarchy:
        l1_text = node["l1_text"]
        if node["children"]:
            for l2_idx, l2_text, l2_start, l2_end in node["children"]:
                is_other = any(kw in l2_text for kw in NON_TARGET_KEYWORDS)
                leaf_sections.append({
                    "name": l2_text,
                    "start": l2_start,
                    "end": l2_end,
                    "is_other": is_other,
                })
        else:
            is_other = any(kw in l1_text for kw in NON_TARGET_KEYWORDS)
            leaf_sections.append({
                "name": l1_text,
                "start": node["l1_start"],
                "end": node["l1_end"],
                "is_other": is_other,
            })

    result = {}
    unclassified = []
    others = []

    for sect in leaf_sections:
        if sect["is_other"]:
            others.append(sect)
            if verbose:
                print(f"  [verbose]  其他(跳过): P{sect['start']}-P{sect['end']}  {sect['name'][:60]}")
            continue
        typ = _classify_by_keywords(sect["name"])
        if typ:
            result[typ] = (sect["start"], sect["end"])
            if verbose:
                print(f"  [verbose]  关键词→{typ}: P{sect['start']}-P{sect['end']}  {sect['name'][:60]}")
        else:
            unclassified.append(sect)

    still_unclassified = []
    for sect in unclassified:
        typ_result = _try_classify_sub_regions(doc, sect["start"], sect["end"])
        if typ_result:
            for typ, (s, e) in typ_result.items():
                if typ in result:
                    old_s, old_e = result[typ]
                    if s <= old_e + 1 and e >= old_s - 1:
                        result[typ] = (min(s, old_s), max(e, old_e))
                else:
                    result[typ] = (s, e)
            if verbose:
                for typ, (s, e) in typ_result.items():
                    print(f"  [verbose]  内容→{typ}: P{s}-P{e}")
        else:
            still_unclassified.append(sect)
            if verbose:
                print(f"  [verbose]  未分类: P{sect['start']}-P{sect['end']}  {sect['name'][:60]}")

    if still_unclassified:
        assigned_types = list(result.keys())
        all_types = ["论述类文本", "文学类文本", "文言文阅读", "古诗词阅读"]
        missing_types = [t for t in all_types if t not in assigned_types]

        if missing_types and still_unclassified:
            if verbose:
                print(f"  [verbose]  未分类→缺少题型分配 ({missing_types})")
            for i, sect in enumerate(still_unclassified):
                if i < len(missing_types):
                    result[missing_types[i]] = (sect["start"], sect["end"])
                    if verbose:
                        print(f"      →{missing_types[i]}: P{sect['start']}-P{sect['end']}")

    if len(result) >= 2:
        l1_indices = set(idx for idx, _ in l1_list)
        sorted_types = sorted(result.keys(), key=lambda t: result[t][0])
        for ti in range(len(sorted_types) - 1):
            curr = sorted_types[ti]
            next_t = sorted_types[ti + 1]
            gap_start = result[curr][1] + 1
            gap_end = result[next_t][0] - 1
            if gap_start <= gap_end:
                l2_indices = set(idx for idx, _ in l2_list)
                contains_l1 = any(l1_idx for l1_idx in l1_indices if gap_start <= l1_idx <= gap_end)
                contains_l2 = any(l2_idx for l2_idx in l2_indices if gap_start <= l2_idx <= gap_end)
                if not contains_l1 and not contains_l2:
                    old_end = result[curr][1]
                    result[curr] = (result[curr][0], gap_end)
                    if verbose:
                        print(f"  [verbose]  gap-fill {curr}: P{result[curr][0]}-{old_end} → P{result[curr][0]}-{gap_end}  (吞并 P{gap_start}-{gap_end})")
                elif verbose:
                    reason = "L1" if contains_l1 else "L2"
                    print(f"  [verbose]  gap-skip {curr}: 缺口 P{gap_start}-{gap_end} 含 {reason} 标题，不扩张")

    if "论述类文本" in result and "文学类文本" in result:
        if result["论述类文本"] == result["文学类文本"]:
            ds, de = result["论述类文本"]
            sub_result = _try_classify_sub_regions(doc, ds, de)
            if sub_result:
                for typ, (s, e) in sub_result.items():
                    result[typ] = (s, e)
                if verbose:
                    print(f"  [verbose]  分裂合并类型 {result['论述类文本']} → {list(sub_result.keys())}")

    detected_count = len(result)
    if detected_count < 3:
        print(f"  [!] [{fname[:30]}...] 仅检测到 {detected_count}/4 种题型: {list(result.keys())}")

    if verbose:
        print("  [verbose] 最终结果:")
        for typ in sorted(result, key=lambda t: result[t][0]):
            print(f"      {typ}: P{result[typ][0]}-P{result[typ][1]}")

    return result if result else None


def get_school_name(fname):
    for kw in ['厦门一中', '厦门二中', '厦门三中', '厦门六中',
               '厦门外国语学校', '厦门外国语',
               '厦门大学附属科技中学', '科技中学',
               '厦门实验中学', '厦门实验',
               '厦门市双十中学', '双十中学', '双十',
               '翔安第一中学', '翔安一中',
               '海沧实验中学',
               '厦门湖滨中学', '湖滨中学',
               '同安一中', '福州一中', '福州三中', '师大附中']:
        if kw in fname:
            return kw
    return None


def get_exam_type(fname):
    for kw in ['第二次月考', '第一次月考', '月考', '期中', '期末']:
        if kw in fname:
            return kw
    return '考试'


def scan_with_fallback(doc, fname, manual_ranges=None):
    if manual_ranges and fname in manual_ranges:
        return manual_ranges[fname]
    print(f"  [.] [{fname[:30]}...] 算法扫描检测...")
    return scan_paper(doc, fname)


_SCHOOL_KWS = ['厦门一中', '厦门二中', '厦门三中', '厦门六中',
               '厦门外国语学校', '厦门外国语',
               '厦门大学附属科技中学', '科技中学',
               '厦门实验中学', '厦门实验',
               '厦门市双十中学', '双十中学', '双十',
               '翔安第一中学', '翔安一中',
               '海沧实验中学',
               '厦门湖滨中学', '湖滨中学',
               '同安一中', '福州一中', '福州三中', '师大附中']


def _find_title_para(doc):
    """从 doc 前几个段落中找到第一个像考试标题的段落。"""
    for p in doc.paragraphs[:5]:
        t = p.text.strip()
        if not t or len(t) < 6:
            continue
        if re.match(r'[一二三四五六七八九十]+[、．.]', t):
            continue
        if t in ('参考答案', '参考答案及解析', '语文试题', '语文 试题'):
            continue
        return t
    return None


def _extract_year(text):
    m = re.search(r'(\d{4})-(\d{4})', text or '')
    return m.group(0) if m else None


def _extract_grade(text):
    m = re.search(r'(高一|高二|高三)[（(]?([上下])[）)]?(学期)?', text or '')
    return m.group(0) if m else None


def _extract_exam_type(text):
    for kw in ['第二次月考', '第一次月考', '月考', '期中', '期末']:
        if kw in (text or ''):
            return kw
    return None


def _extract_school(text):
    for kw in _SCHOOL_KWS:
        if kw in (text or ''):
            return kw
    return None


def _extract_region(text):
    """从文本提取市级区域，如 '福建省厦门市' → '厦门市'"""
    m = re.search(r'福建省(\w+市)', text or '')
    if m:
        return m.group(1)
    m = re.search(r'(\w+市)', text or '')
    return m.group(1) if m else None


def extract_exam_meta(doc, filename, exam_map=None):
    """从文档标题和文件名中智能提取元数据。

    策略：文档前段标题优先，文件名兜底，各字段独立回退。
    返回: {school, exam_type, year, grade_label, title}
    """
    title = _find_title_para(doc)
    school = _extract_school(title) or get_school_name(filename) or "未知学校"
    exam_type = _extract_exam_type(title) or get_exam_type(filename) or "考试"
    if exam_map and exam_type == "月考":
        m = re.search(r'[（(]?(\d{1,2})\s*[月份]+[）)]?', (title or '') + filename)
        if m and m.group(1) in exam_map:
            exam_type = exam_map[m.group(1)]
    year = _extract_year(title) or _extract_year(filename) or ""
    grade = _extract_grade(title) or _extract_grade(filename) or ""

    if title and len(title) >= 8 and not any(
            t in title for t in ('参考答案', '语文试题', '语文 试题')):
        grade_label = title
    else:
        parts = [p for p in (school, year, grade, exam_type) if p]
        grade_label = "".join(parts) if parts else school

    if not year:
        m = re.search(r'\d{4}-\d{4}', grade_label or '')
        year = m.group(0) if m else ''

    return {
        'school': school,
        'exam_type': exam_type,
        'year': year,
        'grade_label': grade_label,
        'title': title if (title and len(title) >= 8) else None,
    }
