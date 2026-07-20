# Task 7 Fix Report

## 修复范围

为三个实验脚本增加共享启动辅助模块，使 `python experiments/<name>.py`
在仓库根目录执行时将项目根目录加入 `sys.path`。模块入口
`python -m experiments.<name>` 保持可运行。三个实验的循环逻辑不变。

同时，三个脚本使用同一摘要输出，包含 `steps=`、`status=`、`score=`、
`stop_reason=` 和 `scores=` 字段。

## 实际验证命令与输出

解释器：`C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`

### 完整 pytest

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
..................................                                       [100%]
34 passed in 2.50s
```

### 直接脚本入口

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\basic_loop.py
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.25, 0.5, 1.0]
```

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\retry_loop.py
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.0, 0.5, 1.0]
```

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\repair_loop.py
steps=1
status=STOPPED
score=0.0
stop_reason=Reached maximum steps: 1
scores=[0.0]
```

### 模块入口复核

以下命令也都以退出码 0 完成：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m experiments.basic_loop
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m experiments.retry_loop
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m experiments.repair_loop
```
