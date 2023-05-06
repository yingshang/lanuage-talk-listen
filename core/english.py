from openpyxl import load_workbook
from core.models import insert_toefl_independent


def toefl_load_independent_file(file):
    # 加载Excel文件
    workbook = load_workbook(file)

    # 选择第一个工作表
    worksheet = workbook.worksheets[0]

    # 读取第一列（A列）从第二行开始的数据
    data = []
    for row in worksheet.iter_rows(min_row=2, min_col=1, values_only=True):
        cell_value = row[0]
        insert_toefl_independent(cell_value)



