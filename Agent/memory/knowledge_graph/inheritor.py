# -*- coding: utf-8 -*-
"""
传承人 Mixin — 正则解析 / 节点创建 / 关系构建 / 批量同步
负责从半结构化 inheritors 文本中抽取传承人数据并写入知识图谱
"""

import re
from typing import Dict, Any, List
from loguru import logger


class InheritorMixin:
    """传承人实体与解析器的写操作"""

    driver: object = None

    # ──────────────────────────────
    # 解析常量
    # ──────────────────────────────

    # 非法师傅名（常见动词/名词/亲属称谓误匹配）
    _INVALID_TEACHERS = {
        '培养', '教授', '学习', '从事', '担任', '负责', '曾赴',
        '自幼', '自幼师', '骨干', '启蒙',
        '父亲', '母亲', '伯父', '祖父', '外祖母', '姥姥', '家人',
        '多人', '多名',
    }

    # 非人名词（误匹配的代际标签、角色描述等）
    _NON_PERSON_NAMES = {
        '第一代', '第二代', '第三代', '第四代', '第五代',
        '早期传承人', '传承方式', '传统谱系', '另有',
        '艺术大师', '代表性传', '传承人',
    }

    # ──────────────────────────────
    # 解析主入口
    # ──────────────────────────────

    @staticmethod
    def parse_inheritors_from_text(text: str) -> List[Dict[str, Any]]:
        """从 inheritors 文本中解析结构化传承人数据，纯正则实现

        支持格式:
          - 姓名(生年—卒年) 如: 曹怀荣(1939—)
          - 姓名(生年—卒年,性别,级别) 如: 刘延河(1960—,男,国家级)
          - 师从关系: 师从XXX / XXX弟子 / XXX之子女
          - 链式谱系: A→B→C 连环师承
          - 集体传承检测: 自动识别 9 种集体传承模式
        """
        if not text or not text.strip():
            return []

        original = text.strip()
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('；', ';')

        # 集体传承检测
        collective_patterns = [
            r'以.*集体传承.*为主',
            r'无特定的代表性传承人认定',
            r'以班社集体传承为主',
            r'以村社和社火队集体传承为主',
            r'以集体传承为主',
            r'以家庭传承和餐饮业传承为主',
            r'以乐社集体传承为主要方式',
            r'尚未有公布国家级或省级代表性传承人',
            r'采用院团集体传承与师徒个体传承相结合',
            r'传承人众多',
        ]
        if any(re.search(p, original) for p in collective_patterns):
            return []

        # 截断尾部描述（"另有..."、"早期传承人:"等）
        tail_cut = re.search(
            r'[。;；](?:另有|其中|传统班社|全县|'
            r'各社均|历代传承谱系|历史谱系|'
            r'历史上|家族传承谱系|传承方式|'
            r'早期传承人)', text)
        if tail_cut:
            text = text[:tail_cut.start()]

        # 用栈匹配括号，处理嵌套
        entries = []
        for m in re.finditer(r'([一-鿿･]{2,4})\(', text):
            name = m.group(1)
            if name in InheritorMixin._NON_PERSON_NAMES:
                continue
            if name.endswith('等'):
                continue
            if re.search(r'[村社系]', name):
                continue
            if re.match(r'^第[一二三四五六七八九十\d]', name):
                continue

            start = m.end() - 1
            depth = 0
            end = start
            for i in range(start, len(text)):
                if text[i] == '(':
                    depth += 1
                elif text[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end > start:
                entries.append((name, text[start + 1:end]))

        # 历史谱系链
        hist_entries = []
        hist_match = re.search(
            r'(?:历代传承谱系|历史谱系|历史上)[:：]\s*(.+?)(?:[。]|$)',
            original)
        if hist_match:
            for m in re.finditer(r'([一-鿿･]{2,4})\(([^)]+)\)', hist_match.group(1)):
                hname, hbio = m.group(1), m.group(2)
                if hname not in InheritorMixin._NON_PERSON_NAMES:
                    hist_entries.append((hname, hbio))

        # 链式师承 A→B→C
        chain_teachers = {}
        if hist_match:
            chain_names = re.findall(r'[一-鿿･]{2,4}(?=\(|→|$)', hist_match.group(1))
            for i in range(len(chain_names) - 1):
                chain_teachers[chain_names[i + 1]] = chain_names[i]

        # ── 解析辅助函数 ──

        def _extract_level(bio):
            if re.search(r'国家级(?:代表性)?传承人', bio):
                return '国家级'
            if re.search(r'省级(?:代表性)?传承人', bio):
                return '省级'
            if re.search(r'市级(?:非遗)?代表性传承人|'
                         r'西安市(?:非遗)?代表性传承人|'
                         r'延安市级非遗', bio):
                return '市级'
            if re.search(r'县级(?:代表性)?传承人', bio):
                return '县级'
            if re.search(r'新一代传承人|传承人|老艺人|'
                         r'著名画家|[第第].*传人', bio):
                return '未定级'
            return ''

        def _extract_birth_year(bio):
            m = re.search(r'(\d{4})年生', bio)
            if m:
                y = int(m.group(1))
                if 1900 <= y <= 2020:
                    return (y, None)
            m = re.search(r'(?:^|[,\s])(\d{4})-(\d{4})(?:$|[,\s)])', bio)
            if m:
                return (int(m.group(1)), int(m.group(2)))
            return (None, None)

        def _extract_gender(bio):
            if re.search(r'(?:^|[,\s])女(?:$|[,\s,;])', bio):
                return '女'
            if re.search(r'(?:^|[,\s])男(?:$|[,\s,;])', bio):
                return '男'
            return ''

        def _extract_generation(bio):
            m = re.search(r'第([一二三四五六七八九十\d]+)代(?:\s*传人|\s*代表性传承人)?', bio)
            if not m:
                m = re.search(r'第([一二三四五六七八九十\d]+)代(?:$|[,\s;])', bio)
            if m:
                g = m.group(1)
                gen_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                           '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                           '十一': 11, '十二': 12, '十八': 18,
                           '十九': 19, '二十': 20}
                return gen_map.get(g, int(g) if g.isdigit() else None)
            return None

        def _is_valid_teacher(t, name=''):
            if t == name:
                return False
            for inv in InheritorMixin._INVALID_TEACHERS:
                if inv in t:
                    return False
            if t.endswith(('学', '和', '的', '了', '是', '等')):
                return False
            return len(t) >= 2

        def _extract_teacher(bio, name=''):
            m = re.search(r'师从([一-鿿･]{2,3})', bio)
            if m and _is_valid_teacher(m.group(1), name):
                return m.group(1)
            m = re.search(r'([一-鿿･]{2,3})弟子', bio)
            if m and _is_valid_teacher(m.group(1), name):
                return m.group(1)
            m = re.search(r'(?<![一-鿿･])([一-鿿･]{2,3})之(?:子|女|侄|孙)', bio)
            if m and _is_valid_teacher(m.group(1), name):
                return m.group(1)
            m = re.search(r'随(?:祖父|父亲|外祖母|伯父|'
                          r'外祖父|家人|母亲|姥姥|和|的)?'
                          r'([一-鿿･]{2,3})(?:学艺|学习|学)', bio)
            if m and _is_valid_teacher(m.group(1), name):
                return m.group(1)
            return None

        # ── 合并解析 ──
        all_entries = entries + hist_entries
        seen_names = set()
        results = []

        for name, bio_text in all_entries:
            if name in seen_names:
                for r in results:
                    if r['name'] == name and bio_text and bio_text not in r['bio']:
                        r['bio'] += '; ' + bio_text
                continue
            seen_names.add(name)

            birth_year, death_year = _extract_birth_year(bio_text)
            teacher = _extract_teacher(bio_text, name)
            if not teacher and name in chain_teachers:
                teacher = chain_teachers[name]

            results.append({
                'name': name.strip(),
                'level': _extract_level(bio_text),
                'birth_year': birth_year,
                'death_year': death_year,
                'status': '已故' if ('已故' in bio_text or '逝世' in bio_text or death_year) else '健在',
                'gender': _extract_gender(bio_text),
                'generation': _extract_generation(bio_text),
                'bio': bio_text.strip(),
                'teacher': teacher,
            })

        return results

    # ──────────────────────────────
    # Inheritor 节点
    # ──────────────────────────────

    def create_inheritor_node(self, name: str, level: str = '',
                               birth_year: int = None, death_year: int = None,
                               status: str = '', gender: str = '',
                               generation: int = None, bio: str = '') -> bool:
        """创建传承人节点（MERGE 保证幂等）"""
        return self._merge_node('Inheritor', 'name',
                                name=name, level=level,
                                birth_year=birth_year, death_year=death_year,
                                status=status, gender=gender,
                                generation=generation, bio=bio)

    # ──────────────────────────────
    # Inheritor 关系
    # ──────────────────────────────

    def create_heritage_inheritor_relation(self, heritage_id: int,
                                            inheritor_name: str) -> bool:
        """创建 Heritage -[HAS_INHERITOR]-> Inheritor 关系"""
        return self._merge_relation('Heritage', heritage_id,
                                    'HAS_INHERITOR', 'Inheritor', inheritor_name)

    def create_studied_under_relation(self, student_name: str,
                                       teacher_name: str) -> bool:
        """创建 Inheritor -[STUDIED_UNDER]-> Inheritor 师承关系"""
        if not student_name or not teacher_name:
            return False
        if student_name == teacher_name:
            return False
        return self._merge_relation('Inheritor', student_name,
                                    'STUDIED_UNDER', 'Inheritor', teacher_name)

    # ──────────────────────────────
    # 批量同步
    # ──────────────────────────────

    def sync_inheritors_from_heritage_list(self, heritage_list: List[Dict]) -> Dict[str, int]:
        """从 heritage 列表同步传承人到知识图谱，返回统计信息"""
        inheritor_count = 0
        relation_count = 0
        teacher_count = 0

        for heritage in heritage_list:
            hid = heritage.get('id')
            text = heritage.get('inheritors', '')
            if not text:
                continue

            inheritors = self.parse_inheritors_from_text(text)
            for inh in inheritors:
                if not inh['name']:
                    continue
                if self.create_inheritor_node(
                    name=inh['name'],
                    level=inh['level'],
                    birth_year=inh['birth_year'],
                    death_year=inh['death_year'],
                    status=inh['status'],
                    gender=inh['gender'],
                    generation=inh['generation'],
                    bio=inh['bio'],
                ):
                    inheritor_count += 1

                if self.create_heritage_inheritor_relation(hid, inh['name']):
                    relation_count += 1

                if inh.get('teacher') and self.create_studied_under_relation(inh['name'], inh['teacher']):
                    teacher_count += 1

        logger.info(
            f"传承人同步完成: "
            f"{inheritor_count} 个节点, "
            f"{relation_count} 条 HAS_INHERITOR, "
            f"{teacher_count} 条 STUDIED_UNDER"
        )
        return {
            'inheritor_nodes': inheritor_count,
            'has_inheritor_relations': relation_count,
            'studied_under_relations': teacher_count,
        }
