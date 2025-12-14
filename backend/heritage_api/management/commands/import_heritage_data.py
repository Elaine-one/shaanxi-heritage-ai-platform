import os
import sys
import json
import re
import shutil
from pypinyin import pinyin, Style # 导入pypinyin
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from heritage_api.models import Heritage, HeritageImage

# 文件路径配置 (相对于项目根目录)
# 注意：JS_DATA_FILE 路径现在相对于 manage.py 所在目录 (backend)
JS_DATA_FILE = '../frontend/js/data/heritage-data.js'
IMAGES_FOLDER = '../frontend/images/heritage-items' # 前端图片文件夹
MEDIA_ROOT_HERITAGE = os.path.join(settings.MEDIA_ROOT, 'heritage_images') # Django媒体根目录下的子目录

def extract_js_data(file_path):
    """从JS文件中提取数据，改进解析逻辑"""
    print(f"正在从 {file_path} 提取数据...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件未找到 {file_path}")
        return []

    pattern = r'const\s+heritageData\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("无法在JS文件中找到 heritageData 数组")
        return []

    data_str = match.group(1).strip()
    data_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', data_str)
    data_str = re.sub(r',\s*([}\]])', r'\1', data_str)

    try:
        data_json = f"[{data_str}]"
        data = json.loads(data_json)
        print(f"成功提取 {len(data)} 条数据记录")
        return data
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("请检查JS数据文件的格式或脚本中的解析逻辑。")
        return []

# get_folder_name 函数已移除，使用 pinyin_name

def create_media_folders():
    """创建媒体文件夹"""
    os.makedirs(MEDIA_ROOT_HERITAGE, exist_ok=True)
    print(f"确保媒体文件夹存在: {MEDIA_ROOT_HERITAGE}")

def migrate_images(heritage): # 接收 Heritage 对象
    """迁移图片到媒体文件夹，并返回图片信息列表"""
    # 使用 Heritage 对象的 pinyin_name 字段
    folder_name = heritage.pinyin_name
    if not folder_name:
        print(f"警告: 项目 '{heritage.name}' (ID: {heritage.id}) 没有 pinyin_name，无法迁移图片。")
        return []
    source_folder = os.path.join(IMAGES_FOLDER, folder_name)
    # 目标路径使用 Django 的 MEDIA_ROOT 下的 heritage_images 子目录，以拼音名称命名
    target_folder_relative = os.path.join('heritage_images', folder_name) # 使用 pinyin_name
    target_folder_absolute = os.path.join(settings.MEDIA_ROOT, target_folder_relative)

    os.makedirs(target_folder_absolute, exist_ok=True)

    if not os.path.exists(source_folder):
        print(f"警告: 源图片文件夹不存在: {source_folder}")
        return []

    images_info = []
    image_index = 0

    # 处理 main.jpg
    main_image_source = os.path.join(source_folder, 'main.jpg')
    if os.path.exists(main_image_source):
        image_index += 1
        target_filename = f"{image_index}.jpg"
        target_path_absolute = os.path.join(target_folder_absolute, target_filename)
        shutil.copy2(main_image_source, target_path_absolute)
        # 存储相对路径，用于数据库 (heritage_images/pinyin_name/1.jpg)
        image_relative_path = os.path.join('heritage_images', folder_name, target_filename).replace('\\', '/')
        images_info.append({'path': image_relative_path, 'is_main': True})

    # 处理其他图片 1.jpg, 2.jpg ...
    for i in range(1, 10): # 假设最多9张其他图片
        source_filename = f"{i}.jpg"
        source_path = os.path.join(source_folder, source_filename)
        if os.path.exists(source_path):
            image_index += 1
            target_filename = f"{image_index}.jpg"
            target_path_absolute = os.path.join(target_folder_absolute, target_filename)
            shutil.copy2(source_path, target_path_absolute)
            # 存储相对路径，用于数据库 (heritage_images/pinyin_name/N.jpg)
            image_relative_path = os.path.join('heritage_images', folder_name, target_filename).replace('\\', '/')
            # 如果没有主图，则将第一张图设为主图
            is_main = (image_index == 1 and not any(img['is_main'] for img in images_info))
            images_info.append({'path': image_relative_path, 'is_main': is_main})

    # 如果处理完所有图片仍没有主图，将第一张标记为主图
    if images_info and not any(img['is_main'] for img in images_info):
        images_info[0]['is_main'] = True

    print(f"为项目 '{heritage.name}' (ID: {heritage.id}) 迁移了 {len(images_info)} 张图片到 {target_folder_absolute}")
    return images_info

class Command(BaseCommand):
    help = '从JS文件导入非遗数据到数据库，并迁移图片'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始导入非遗数据...'))

        # 提取数据
        data = extract_js_data(JS_DATA_FILE)
        if not data:
            self.stderr.write(self.style.ERROR('数据提取失败，终止导入。'))
            return

        # 创建媒体文件夹
        create_media_folders()

        # 清空现有数据（可选，谨慎使用）
        self.stdout.write(self.style.WARNING('正在清空现有 Heritage 和 HeritageImage 数据...'))
        HeritageImage.objects.all().delete()
        Heritage.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('现有数据已清空'))

        # 导入数据
        imported_count = 0
        skipped_count = 0
        for item in data:
            try:
                # 创建非遗项目记录
                heritage = Heritage.objects.create(
                    id=item['id'],
                    name=item['name'],
                    category=item.get('category', '未知类别'),
                    region=item.get('region', '未知地区'),
                    batch=item.get('batch'), # 批次，允许为空
                    description=item.get('description', ''),
                    history=item.get('history', ''),
                    features=item.get('features', ''),
                    value=item.get('value', ''),
                    status=item.get('status', ''),
                    protection_measures=item.get('protection_measures', ''),
                    inheritors=item.get('inheritors', ''),
                    related_works=item.get('related_works', ''),
                    level=item.get('level', '未知级别'),
                    latitude=item.get('lat'),
                    longitude=item.get('lng')
                )

                # 生成并保存拼音名称
                try:
                    pinyin_list = pinyin(heritage.name, style=Style.NORMAL)
                    heritage.pinyin_name = "".join([item[0] for item in pinyin_list])
                    heritage.save() # 保存 pinyin_name
                except Exception as pinyin_err:
                    self.stderr.write(self.style.ERROR(f"为 '{heritage.name}' 生成拼音时出错: {pinyin_err}"))
                    heritage.pinyin_name = None # 或设置默认值
                    heritage.save()

                # 迁移图片并创建图片记录 (传入 heritage 对象)
                images_info = migrate_images(heritage)
                for img_info in images_info:
                    HeritageImage.objects.create(
                        heritage=heritage,
                        image=img_info['path'], # 存储相对路径
                        is_main=img_info['is_main']
                    )

                imported_count += 1
                self.stdout.write(f"成功导入: {item['name']} (ID: {item['id']})", ending=' ')
                self.stdout.write(self.style.SUCCESS(f"并关联了 {len(images_info)} 张图片"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"导入项目 '{item.get('name', '未知名称')}' (ID: {item.get('id', '未知')}) 时出错: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n导入完成！成功导入 {imported_count} 条记录，跳过 {skipped_count} 条记录。'))