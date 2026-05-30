from .base import (
    EXAM_ORDER_KEYWORDS,
    BaseFormatter,
    _classify_text,
    _exam_num_map,
    _exam_sort_key,
    add_run_with_font,
    add_shading,
)

FORMATTER_MAP = {
    "论述类文本": BaseFormatter,
    "文学类文本": BaseFormatter,
    "文言文阅读": BaseFormatter,
    "古诗词阅读": BaseFormatter,
}

__all__ = [
    "BaseFormatter",
    "FORMATTER_MAP",
    "add_run_with_font",
    "add_shading",
    "_classify_text",
    "EXAM_ORDER_KEYWORDS",
    "_exam_sort_key",
    "_exam_num_map",
]
