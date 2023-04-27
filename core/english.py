import os
import random
import openpyxl
import shutil

cwd = os.getcwd()
file_path = os.path.join(cwd,'file')

word_filename = os.path.join(file_path,"words.txt")

independent_speak_filename = os.path.join(file_path,"independent_speak.xlsx")

def random_speak_title():
    if not os.path.exists(independent_speak_filename):
        source_file = os.path.join(os.path.join(cwd,'origin'),'independent_speak.xlsx')
        shutil.copy(source_file, independent_speak_filename)

    workbook = openpyxl.load_workbook(independent_speak_filename)
    # 选择工作表
    sheet = workbook['题目']
    first_column = sheet['A']
    # 遍历工作表并读取单元格值
    first_column_values = [cell.value for cell in sheet['A'][1:]]
    first_column_values = [value for value in first_column_values if value is not None]
    random_value = random.choice(first_column_values)
    return random_value




