"""演示文件：故意写得格式糟糕，用于触发 PostToolUse 的 ruff hook。

讲师操作：让 Claude 改这里的 calculate_total，hook 会捕获格式问题，AI 看到报错后自我修复。
"""

import os    # 故意：未使用的 import
import sys   # 故意：未使用的 import


def   calculate_total( items ):
    # 故意：函数名前后多空格、参数前后多空格、缩进混乱
    total=0
    for i in items :
        total = total+i
    return total


def   greet(name)   :
    print( "hello "+name )
