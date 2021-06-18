# CFG-dupath of C
## 环境
python  
pycparser  
graphviz  
gcc 

项目中fake_libc_include存放的是pycparser和C语言编译器要求的文件，需要对[代码760行](./graph_gen.py#760)修改cpp_path=gcc安装目录。   

## 使用
在main.py目录下，放入想要生成的 .c后缀文件，运行main.py，选择想生成的文件，/tmp文件夹会存放处理后的c文件（去除注释和`#include`），并生成相应文件名称文件以及pdf文件。

## 限制
暂不支持struct在c的使用，不能总结每个变量的dupath，仍不支持部分表达式或者类型节点的解析。

## 其他
test1~4是从网上随便找的代码，用于基本的测试。  
- buct课程作业参考