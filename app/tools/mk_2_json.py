import json
import re

"""
格式转换说明实例：

From
### 学习计划大纲

**第1天**

* 学习内容: Python基础语法与变量
* 学习知识点:

1. Python的安装与环境配置
2. 打印输出（`print()`函数）
3. 变量与数据类型（整数、浮点数、字符串、布尔值）
4. 基本运算符（算术、比较、逻辑）
5. 简单的用户输入（`input()`函数）

To 

{
    "学习主题": "Python基础到简单脚本编写",
    "学习计划描述": "这是一个为期5天的Python学习计划，适合零基础但希望快速掌握Python基础并能够编写简单脚本的学习者。计划从Python基础语法开始，逐步过渡到函数、文件操作和简单脚本编写，确保每天的学习内容适量且循序渐进。",
    "学习计划大纲": [
        {
            "天数": 1,
            "学习内容": "Python基础语法与变量",
            "学习知识点": [
                "Python的安装与环境配置",
                "打印输出（`print()`函数）",
                "变量与数据类型（整数、浮点数、字符串、布尔值）",
                "基本运算符（算术、比较、逻辑）",
                "简单的用户输入（`input()`函数）"
            ]
        },
    ]
}

"""


def markdown_to_json(markdown_text):
    # 初始化结果字典
    result = {
        "title": "",
        "content": "",
        "daily_plans": []
    }
    # 分割行
    if "\\n" in markdown_text:
        lines = markdown_text.split('\\n')
    else:
        lines = markdown_text.split('\n')
    # 提取学习主题
    for line in lines:
        if line.startswith("### 学习主题:"):
            result["title"] = line.split(":")[1].strip()
            break

    # 提取学习计划描述
    desc_start = False
    description = []
    for line in lines:
        if line.startswith("### 学习计划描述"):
            desc_start = True
            continue
        if line.startswith("### 学习计划大纲"):
            desc_start = False
            break
        if desc_start and line.strip():
            description.append(line.strip())
    result["content"] = " ".join(description)

    # 提取学习计划大纲
    current_day = None
    plan_start = False
    for line in lines:
        if line.startswith("### 学习计划大纲"):
            plan_start = True
        if not plan_start:
            continue
        # 匹配天数标题
        day_match = re.match(r'^\*\*第(\d+)天\*\*$', line.strip())
        if day_match:
            current_day = {
                "day": int(day_match.group(1)),
                "topic": "",
                "key_points": []
            }
            result["daily_plans"].append(current_day)
            continue

        # 匹配学习内容
        if line.strip().startswith("* 学习内容:"):
            if current_day:
                current_day["topic"] = line.split(":")[1].strip()
            continue

        # 匹配学习知识点
        if line.strip().startswith("* 学习知识点:"):
            continue

        # 收集知识点
        if current_day and line.strip().startswith("1. "):
            # 移除数字和点
            knowledge_point = re.sub(r'^\d+\.\s*', '', line.strip())
            current_day["key_points"].append(knowledge_point)

    return json.dumps(result, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    s = """### 学习主题: Java编程入门  \\n### 学习计划描述:  \\n本计划为零基础学习者设计，通过90天系统学习掌握Java基础语法、面向对象编程核心概念，最终能独立完成简单项目。每天安排1-2小时学习，注重实践与理论结合，逐步构建编程思维。  \\n\\n### 学习计划大纲  \\n\\n**第1天**  \\n* 学习内容: Java开发环境搭建与基础概念  \\n* 学习知识点:  \\n1. Java语言特点与应用场景  \\n2. JDK安装与环境变量配置  \\n3. 使用记事本编写第一个HelloWorld程序  \\n4. 理解编译与执行过程  \\n\\n**第2天**  \\n* 学习内容: Java基础语法结构  \\n* 学习知识点:  \\n1. 标识符与关键字规则  \\n2. 基本数据类型（int/double/char/boolean）  \\n3. 变量的声明与初始化  \\n4. 简单的System.out输出  \\n\\n**第3天**  \\n* 学习内容: 运算符与表达式  \\n* 学习知识点:  \\n1. 算术运算符（+ - * / %）  \\n2. 关系运算符（> < == !=）  \\n3. 逻辑运算符（&& || !）  \\n4. 赋值运算符与复合赋值  \\n\\n**第4天**  \\n* 学习内容: 用户输入与流程控制  \\n* 学习知识点:  \\n1. 使用Scanner获取键盘输入  \\n2. if-else条件语句  \\n3. 三元运算符的简化条件判断  \\n4. 代码调试基础（打印中间值）  \\n\\n**第5天**  \\n* 学习内容: 循环结构  \\n* 学习知识点:  \\n1. while循环语法与应用场景  \\n2. for循环语法与计数器控制  \\n3. break和continue关键字  \\n4. 循环嵌套打印简单图形  \\n\\n**第6天**  \\n* 学习内容: 数组基础  \\n* 学习知识点:  \\n1. 一维数组的声明与初始化  \\n2. 数组遍历（for循环增强版）  \\n3. 数组越界异常处理  \\n4. 查找数组最大值/最小值  \\n\\n**第7天**  \\n* 学习内容: 方法定义与调用  \\n* 学习知识点:  \\n1. 方法的定义语法（返回类型、参数列表）  \\n2. 形参与实参的区别  \\n3. 方法重载的概念  \\n4. 递归方法初步理解  \\n\\n**第8天**  \\n* 学习内容: 字符串处理  \\n* 学习知识点:  \\n1. String类的常用方法（length/charAt/substring）  \\n2. 字符串拼接与比较（equals vs ==）  \\n3. StringBuilder高效字符串操作  \\n4. 用户登录模拟练习  \\n\\n**第9天**  \\n* 学习内容: 面向对象基础  \\n* 学习知识点:  \\n1. 类与对象的关系  \\n2. 类的定义（属性+方法）  \\n3. 构造方法的作用  \\n4. 创建第一个对象并调用方法  \\n\\n**第10天**  \\n* 学习内容: 封装与访问控制  \\n* 学习知识点:  \\n1. private关键字与getter/setter  \\n2. this关键字的使用场景  \\n3. 标准JavaBean规范  \\n4. 银行账户类封装练习  \\n\\n（因篇幅限制，仅展示前10天示例。后续计划将逐步涵盖：继承与多态、异常处理、集合框架、IO流、多线程基础，最终以\\"学生管理系统\\"项目整合所有知识点。如需完整90天计划可告知继续输出。）" """
    k = markdown_to_json(s)
    print(k)
