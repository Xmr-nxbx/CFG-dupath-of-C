import os
import traceback

import graph_gen


def main(path='.'):
    c_files = list(filter(lambda x: len(x) > 1 and x.find('.c') == len(x) - 2, os.listdir(path)))
    print('选择位于目录(%s) c语言文件索引：' % path)
    for index, name in enumerate(c_files):
        print(index, '->', name)
    index = int(input(''))
    try:
        graph_gen.build_graph(c_files[index], c_files[index].split('.')[0])
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
