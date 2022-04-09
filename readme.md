# CFG-dupath of C
## 功能(Feature)
生成c语言代码的CFG和dupath  

generate c language file control flow graph and define-use path

## 环境(Environment)
python  
pycparser  
graphviz  
gcc  

fake_libc_include 是 `gcc -I fake_libc_include` 指定头文件路径。此外，需要修改[代码836行](./graph_gen.py#L836)cpp_path=gcc安装目录。

fake_libc_include is the path of the header specified in the command `gcc -I fake_libc_include`. In addition, the [code](./graph_gen.py#L836) needs to be modified for the gcc installation directory.

## 使用(Use)
在main.py目录下，放入想要生成的 .c后缀文件，运行main.py，选择想生成的文件，/tmp文件夹会存放处理后的c文件（去除注释和`#include`），并生成相应文件名称文件以及pdf文件。

In the current directory, save the .c suffix file, run main.py and choose the index. The /tmp folder holds the processed c files and pdf files.


## 限制(Limit)
暂不支持struct在c的使用，可能不支持部分表达式或者类型节点的解析。

The use of struct in c is not supported, and may not support partial expressions or type node.


## 其他(Other)
test1~4是从网上随便找的代码，用于基本的测试。  

test1.c - test4.c is the test for generation.

- buct课程作业参考
- University homework
