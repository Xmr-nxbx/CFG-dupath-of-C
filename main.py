import traceback
import graph_gen
import os

def main():
    c_files = list(filter(lambda x: len(x) > 1 and x.find('.c') == len(x) - 2, os.listdir('.')))
    print('选择当前目录下的c语言文件（输入数字）：')
    for index, name in enumerate(c_files):
        print(index, '->', name)
    index = int(input(''))
    try:
        graph_gen.build_graph(c_files[index], c_files[index].split('.')[0])
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()