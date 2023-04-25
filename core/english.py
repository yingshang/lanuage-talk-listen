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


def random_words(num):

    # Read the existing words from the file
    try:
        with open(word_filename, "r") as file:
            words = [line.strip() for line in file]
    except:
        return None
    # Select 10 random words from the list
    selected_words = random.sample(words, num)
    return selected_words


def read_write_words(word_list):

    # Check if the file exists, create it if it doesn't
    if not os.path.isfile(word_filename):
        with open(word_filename, "w") as file:
            pass

    # Read the existing words from the file and remove duplicates
    with open(word_filename, "r") as file:
        existing_words = set(line.strip() for line in file)

    # Add the new words to the existing set and write back to the file
    new_words = set(word_list) - existing_words
    with open(word_filename, "a") as file:
        for word in new_words:
            file.write(word + "\n")

    updated_words = existing_words | new_words
    total_words = len(updated_words)
    return len(new_words),total_words