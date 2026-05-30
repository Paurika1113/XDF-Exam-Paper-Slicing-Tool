import re


def classify_global(text):
    """全局分类规则，所有题型共享。
    返回分类名，或 None（未命中全局规则，交给类型专用）。"""
    if not text.strip():
        return "empty"

    if text.startswith("【") and "】" in text and any(
            kw in text for kw in ["厦门", "考试", "月考", "期中", "期末"]):
        return "source_label"

    if re.match(r'^[一二三四五六七八九十百]+[、.．]', text):
        return "skip_header"
    if re.match(r'^[（(][一二三四五六七八九十百]+[）)]', text):
        if any(kw in text for kw in ['阅读', '默写', '诗歌', '文言', '古诗', '作文',
                                       '语言文字', '名句', '写作']):
            return "skip"
        return "other"

    if text.startswith("【答案】"):
        return "answer_marker"

    if text.startswith("【注】") or text.startswith("【注释】") or text.startswith("[注]"):
        return "annotation"

    if re.match(r'^【[\u4e00-\u9fff]{2,}】', text):
        return "explanation_marker"

    if text.startswith("阅读下面"):
        return "instruction"

    m = re.match(r'^(\d+[．.、])', text)
    if m:
        after_num = text[m.end():].lstrip()
        if "阅读" in after_num:
            return "instruction"

    if '本题考查' in text or text.startswith('【分析】'):
        return "explanation_auto"
    if re.match(r'^故选[A-D]', text):
        return "explanation_auto"
    if re.match(r'^故选：', text):
        return "explanation_auto"
    if re.match(r'^\d+[．.、]\s*本题考查', text):
        return "explanation_auto"
    if text.startswith("句意：") or text.startswith("①句意") or text.startswith("②句意"):
        return "explanation_auto"
    if any(text.startswith(p) for p in ["全文翻译", "参考译文", "译文", "全文译文"]):
        return "explanation_auto"

    if re.match(r'^\d+[．.、]', text):
        return "question"
    if re.match(r'^[（(]\d+[）)]', text) and not \
       any(kw in text for kw in ['月考', '期中', '期末', '考试']):
        return "question"
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', text):
        return "question_sub"

    if re.match(r'^[A-D][．.、)]', text):
        return "option"

    return None


def classify_gushici(text):
    """古诗词阅读专用分类。"""
    if '阅读下面' in text:
        return "instruction"
    if any(kw in text for kw in [
        '下列句子中，句式与其他三项不同的一项是',
        '下列加点字词的解释',
        '下列加点虚词的意义及用法',
        '下列有关文学常识的表述',
        '补写出下列句子中的空缺部分',
        '课内古诗文阅读',
    ]):
        return "skip_content"

    if re.match(r'^[\u4e00-\u9fff·\s]{2,10}$', text.strip()):
        if re.match(r'^[\u4e00-\u9fff]{2,3}$', text.strip()) and text.strip() in \
           ['李白', '杜甫', '白居易', '杜牧', '王维', '孟浩然', '李商隐', '王昌龄',
            '刘禹锡', '杜荀鹤', '苏轼', '李清照', '辛弃疾', '陆游', '王安石', '欧阳修',
            '陶渊明', '曹操', '王阳明', '黄庭坚', '杨万里', '范成大', '晏殊', '柳永',
            '温庭筠', '韦庄', '李贺', '贾岛', '孟郊', '张若虚', '高适', '岑参', '王之涣',
            '王勃', '骆宾王', '杨炯', '卢照邻', '陈子昂', '贺知章', '张九龄', '王湾',
            '常建', '刘长卿', '韦应物', '柳宗元', '元稹', '张籍', '李益', '卢纶',
            '李煜', '范仲淹', '秦观', '周邦彦', '姜夔', '马致远', '关汉卿', '王实甫',
            '纳兰性德', '龚自珍', '曹植', '屈原', '项羽', '刘邦', '岳飞', '文天祥',
            '于谦', '郑燮', '袁枚', '赵翼', '查慎行', '朱彝尊', '顾炎武', '黄宗羲',
            '王夫之', '归有光', '唐寅', '徐渭', '杨慎', '汤显祖', '孔尚任', '洪昇',
            '吴伟业', '陈维崧', '朱敦儒', '张孝祥', '陈亮', '刘过', '刘克庄',
            '吴文英', '王沂孙', '张炎', '蒋捷', '周密', '文天祥', '汪元量', '郑思肖',
            '林逋', '潘阆', '寇准', '林升', '叶绍翁', '翁卷', '赵师秀', '徐玑',
            '戴复古', '方岳', '谢枋得', '谢翱', '王冕', '刘基', '高启', '李梦阳',
            '何景明', '王世贞', '李攀龙', '谢榛', '徐祯卿', '边贡', '袁宏道', '袁中道',
            '袁宗道', '钟惺', '谭元春', '张岱', '夏完淳', '陈子龙', '屈大均',
            '毛奇龄']:
            return "poem_author"
        return "poem_title"
    clean = re.sub(r'[，。！？、；：\u201c\u201d\u2018\u2019《》（）\s]', '', text.strip())
    if 4 <= len(clean) <= 28 and len(clean) >= len(text.strip()) * 0.5:
        return "poem_text"
    if '，' in text and len(text.strip()) <= 40:
        comma_parts = text.strip().split('，')
        if all(3 <= len(p) <= 10 for p in comma_parts):
            return "poem_text"

    return "other"


def classify_nonpoem(text):
    """论述类文本/文学类文本/文言文阅读 专用分类。"""
    if len(text) > 30 and not (re.match(r'^[（(]?(摘编自|选自|节选自|摘自|有删改|有删节)', text) or \
           '有删改' in text or '有删节' in text):
        return "modern_text"
    if text.startswith("材料") or text.startswith("文本"):
        return "modern_text"
    return "other"
