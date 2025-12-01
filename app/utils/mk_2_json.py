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
        "total_days": 0,
        "specific_goals": "",
        "daily_plans": []
    }
    # 分割行
    if "\\n" in markdown_text:
        lines = markdown_text.split('\\n')
    else:
        lines = markdown_text.split('\n')
    # 提取学习主题 学习天数 学习目标
    goals = False
    goals_text = []
    for line in lines:
        if line.startswith("### 学习主题:"):
            result["title"] = line.split(":")[1].strip()
            continue
        if line.startswith("### 学习天数:"):
            result["total_days"] = line.split(":")[1].strip()
            continue
        if line.startswith("### 学习目标:"):
            goals_text.append(line.split(":")[1].strip())
            goals = True
            continue
        if goals and line.startswith("###"):
            result["specific_goals"] = "".join(goals_text)
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
        if current_day and line.strip().startswith("1"):
            # 移除数字和点
            knowledge_point = re.sub(r'^\d+[\.]{0,1}\s*', '', line.strip())
            current_day["key_points"].append(knowledge_point)

    return json.dumps(result, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    s = """### 学习主题: PMP认证考试准备
### 学习天数: 15天
### 学习目标: 通过PMP的认证考试
### 学习计划描述:
总体学习概述：本计划为零基础学习者设计，涵盖PMP考试的核心知识领域，包括项目管理的五大过程组和十大知识领域。每天的学习内容循序渐进，结合理论学习与实践练习，确保学习者能够掌握考试所需的关键概念、工具和技术，并最终通过认证考试。

### 学习计划大纲
**第1天**
* 学习内容: 项目管理基础与PMP考试介绍
* 学习知识点:
1 项目管理的基本概念与价值
2 PMP认证考试的结构与要求
3 项目、项目集与项目组合的区别
4 项目管理生命周期与过程组简介

**第2天**
* 学习内容: 项目启动过程组
* 学习知识点:
1 项目章程的制定与作用
2 识别相关方及其需求
3 商业论证与项目选择方法
4 启动过程组的输入、工具与技术、输出

**第3天**
* 学习内容: 项目规划过程组 - 范围管理
* 学习知识点:
1 收集需求的方法与技术
2 定义范围与创建WBS（工作分解结构）
3 范围基准的确认与控制
4 范围管理计划的重要性

**第4天**
* 学习内容: 项目规划过程组 - 时间管理
* 学习知识点:
1 活动定义与排序
2 估算活动持续时间的方法
3 制定进度计划（关键路径法、敏捷方法）
4 进度基准与控制

**第5天**
* 学习内容: 项目规划过程组 - 成本管理
* 学习知识点:
1 成本估算技术与工具
2 制定预算与确定成本基准
3 挣值管理（EVM）基础
4 成本控制与预测方法

**第6天**
* 学习内容: 项目规划过程组 - 质量管理
* 学习知识点:
1 质量规划与标准
2 质量保证与控制质量
3 常用质量管理工具（如帕累托图、控制图）
4 持续改进理念

**第7天**
* 学习内容: 项目资源与沟通管理
* 学习知识点:
1 规划资源管理（团队与实物资源）
2 估算与获取资源
3 沟通管理计划与 stakeholder engagement
4 冲突解决与团队建设技巧

**第8天**
* 学习内容: 项目风险管理
* 学习知识点:
1 风险识别与定性/定量分析
2 规划风险应对策略
3 实施风险应对与控制风险
4 风险登记册的使用

**第9天**
* 学习内容: 项目采购与相关方管理
* 学习知识点:
1 采购规划与合同类型
2 实施采购与控制采购
3 识别与管理相关方期望
4 相关方参与计划

**第10天**
* 学习内容: 项目执行过程组
* 学习知识点:
1 指导与管理项目工作
2 管理项目知识
3 实施质量保证与资源分配
4 团队管理与沟通执行

**第11天**
* 学习内容: 项目监控过程组
* 学习知识点:
1 监控项目工作与绩效
2 整体变更控制流程
3 风险与问题监控
4 报告绩效与更新项目文件

**第12天**
* 学习内容: 项目收尾过程组
* 学习知识点:
1 项目或阶段收尾流程
2 最终产品、服务或成果的移交
3 经验教训总结与归档
4 合同收尾与资源释放

**第13天**
* 学习内容: 敏捷与混合项目管理方法
* 学习知识点:
1 敏捷原则与核心价值观
2 常用敏捷框架（Scrum、Kanban）
3 混合方法在PMP中的应用
4 适应性与变更驱动型生命周期

**第14天**
* 学习内容: PMP考试模拟与题型分析
* 学习知识点:
1 模拟考试练习与时间管理
2 常见题型分析与解题技巧
3 重点知识回顾与弱项强化
4 考试策略与心态准备

**第15天**
* 学习内容: 总复习与考前准备
* 学习知识点:
1 所有知识领域的快速回顾
2 关键公式、术语与概念记忆
3 最后模拟测试与错误分析
4 考试日准备与注意事项"""
    k = markdown_to_json(s)
    print(k)
