# 蒙多中式美学系统 — 代码之道，源于东方

> "无画处皆成妙境。" — 清·笪重光《画筌》
> "计白当黑，奇趣乃出。" — 清·邓艺孙《书法精论》

---

## 一、中式美学十则

### 1. 留白 (Negative Space)

**美学原理**：留白不是空无，是"无中生有"。马远《寒江独钓图》，一叶扁舟，满纸皆水。

**代码映射**：
```python
# 坏：密不透风，令人窒息
def process(data):
    result=[]
    for i in data:
        if i>0:
            result.append(i*2)
        else:
            result.append(i)
    return result

# 好：留白有致，意境深远
def process(data: list[int]) -> list[int]:
    """处理数据：正数翻倍，负数保持"""
    
    result = []
    
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(item)
    
    return result
```

**美学准则**：
- 函数之间留一个空行，如山水画中的云雾
- 逻辑块之间留白，如书法中的"气口"
- 不要为了省行数而压缩可读性

---

### 2. 虚实相生 (Void and Solid)

**美学原理**：虚中有实，实中有虚。老子曰："有无相生"。

**代码映射**：
```python
# 虚：接口是虚，定义契约
class DataProcessor(Protocol):
    """数据处理器接口 — 虚"""
    
    def process(self, data: DataFrame) -> DataFrame: ...


# 实：实现是实，具体逻辑
class CsvProcessor:
    """CSV处理器 — 实"""
    
    def process(self, data: DataFrame) -> DataFrame:
        return data.dropna().reset_index(drop=True)
```

**美学准则**：
- 接口为虚，实现为实
- 抽象为虚，具体为实
- 配置为虚，代码为实
- 虚实相生，方成妙境

---

### 3. 写意 (Freehand Spirit)

**美学原理**：不求形似，重在神韵。齐白石画虾，寥寥数笔，活灵活现。

**代码映射**：
```python
# 坏：拘泥于形，失去神韵
def calculate_the_sum_of_two_numbers_added_together(a, b):
    return a + b

# 好：写意之笔，神韵自现
def add(a: int, b: int) -> int:
    """加法"""
    return a + b
```

**美学准则**：
- 命名求神韵，不求字数多
- 函数求意境，不求功能杂
- 注释求点睛，不求长篇大论

---

### 4. 中和 (Harmony)

**美学原理**：不偏不倚，平衡和谐。《中庸》曰："致中和，天地位焉，万物育焉。"

**代码映射**：
```python
# 坏：过度设计，失之中和
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=SingletonMeta):
    def __init__(self):
        self._data = {}
    def get(self, key, default=None):
        return self._data.get(key, default)
    def set(self, key, value):
        self._data[key] = value

# 好：中和之道，恰到好处
_config: dict[str, Any] = {}

def get_config(key: str, default: Any = None) -> Any:
    """获取配置"""
    return _config.get(key, default)
```

**美学准则**：
- 简洁与可读性平衡
- 性能与优雅平衡
- 抽象与具体平衡
- 过犹不及，恰到好处

---

### 5. 含蓄 (Subtlety)

**美学原理**：言有尽而意无穷。李商隐诗，朦胧含蓄，意蕴深长。

**代码映射**：
```python
# 坏：直白无味，毫无余韵
def is_user_old(user):
    if user.age > 60:
        return True
    else:
        return False

# 好：含蓄有致，意在言外
def is_senior(user: User) -> bool:
    """是否为长者"""
    return user.age > 60
```

**美学准则**：
- 命名含蓄而精准
- 逻辑简洁而深邃
- 不过度解释，让代码自己说话

---

### 6. 气韵生动 (Vitality)

**美学原理**：气韵生动，乃为上品。谢赫《古画品录》六法之首。

**代码映射**：
```python
# 坏：死气沉沉，毫无生气
def f(x):
    a = x[0]
    b = x[1]
    c = a + b
    d = a - b
    e = c * d
    return e

# 好：气韵生动，行云流水
def calculate_expression(numbers: tuple[int, int]) -> int:
    """计算 (a+b) * (a-b)"""
    
    first, second = numbers
    sum_result = first + second
    diff_result = first - second
    
    return sum_result * diff_result
```

**美学准则**：
- 变量命名有生命力
- 函数流程有节奏感
- 代码结构有呼吸感

---

### 7. 天人合一 (Unity of Heaven and Man)

**美学原理**：人法地，地法天，天法道，道法自然。

**代码映射**：
```python
# 坏：违背自然，强行硬编码
def get_season(month):
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

# 好：顺应自然，配置驱动
SEASONS = {
    (12, 1, 2): "winter",
    (3, 4, 5): "spring",
    (6, 7, 8): "summer",
    (9, 10, 11): "autumn",
}

def get_season(month: int) -> str:
    """获取季节"""
    for months, season in SEASONS.items():
        if month in months:
            return season
    raise ValueError(f"无效月份: {month}")
```

**美学准则**：
- 代码要符合业务逻辑的自然规律
- 命名要符合人类的直觉
- 结构要符合问题的本质

---

### 8. 线条之美 (Beauty of Lines)

**美学原理**：中国书法，线条为骨。王羲之《兰亭序》，线条流畅，一波三折。

**代码映射**：
```python
# 坏：线条杂乱，毫无美感
def process(data,threshold=0.5,normalize=True,sort=True,limit=100):
    result=[x for x in data if x>threshold]
    if normalize: result=[x/max(result) for x in result]
    if sort: result=sorted(result,reverse=True)
    return result[:limit]

# 好：线条流畅，一波三折
def process(
    data: list[float],
    threshold: float = 0.5,
    normalize: bool = True,
    sort: bool = True,
    limit: int = 100,
) -> list[float]:
    """处理数据：过滤、归一化、排序"""
    
    result = [x for x in data if x > threshold]
    
    if normalize and result:
        max_val = max(result)
        result = [x / max_val for x in result]
    
    if sort:
        result = sorted(result, reverse=True)
    
    return result[:limit]
```

**美学准则**：
- 长参数列表要换行，如书法中的顿笔
- 逻辑块要清晰，如书法中的起承转合
- 缩进要一致，如书法中的中锋用笔

---

### 9. 墨分五色 (Five Shades of Ink)

**美学原理**：焦、浓、重、淡、清。一种墨色，五种层次。

**代码映射**：
```python
# 坏：只有一种"墨色"，毫无层次
def handle_error(error):
    print(error)
    return None

# 好：墨分五色，层次分明
def handle_error(error: Exception) -> Never:
    """处理错误 — 墨分五色"""
    
    # 焦：致命错误，立即崩溃
    if isinstance(error, SystemExit):
        logger.critical(f"系统退出: {error}")
        raise
    
    # 浓：严重错误，记录并抛出
    if isinstance(error, (MemoryError, OverflowError)):
        logger.error(f"严重错误: {error}")
        raise
    
    # 重：业务错误，记录并返回
    if isinstance(error, ValueError):
        logger.warning(f"业务错误: {error}")
        return None
    
    # 淡：可忽略错误，静默记录
    if isinstance(error, (TimeoutError, ConnectionError)):
        logger.info(f"临时错误: {error}")
        return None
    
    # 清：未知错误，记录详情
    logger.debug(f"未知错误: {error}")
    return None
```

**美学准则**：
- 错误处理要有层次
- 日志级别要分明
- 代码结构要有深浅

---

### 10. 计白当黑 (White as Black)

**美学原理**：空白也是设计的一部分。邓艺孙曰："计白当黑，奇趣乃出。"

**代码映射**：
```python
# 坏：没有留白，密不透风
class UserManager:
    def __init__(self, db):
        self.db = db
    def get_user(self, id):
        return self.db.query(User).filter(User.id == id).first()
    def create_user(self, data):
        user = User(**data)
        self.db.add(user)
        self.db.commit()
        return user
    def update_user(self, id, data):
        user = self.get_user(id)
        for key, value in data.items():
            setattr(user, key, value)
        self.db.commit()
        return user

# 好：计白当黑，空白有致
class UserManager:
    """用户管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: int) -> User | None:
        """获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, data: dict) -> User:
        """创建用户"""
        user = User(**data)
        self.db.add(user)
        self.db.commit()
        return user
    
    def update_user(self, user_id: int, data: dict) -> User:
        """更新用户"""
        user = self.get_user(user_id)
        
        for key, value in data.items():
            setattr(user, key, value)
        
        self.db.commit()
        return user
```

**美学准则**：
- 类的方法之间要有空白
- 逻辑块之间要有空白
- 空白是代码呼吸的空间

---

## 二、中式美学代码规范

### 命名规范

| 中式美学 | 命名原则 | 示例 |
|---------|---------|------|
| 写意 | 求神韵，不求字数 | `add` 优于 `calculate_the_sum_of_two_numbers` |
| 含蓄 | 精准而有深度 | `is_senior` 优于 `is_user_old_age_greater_than_60` |
| 天人合一 | 符合直觉 | `calculate_area` 优于 `calc_a` |

### 结构规范

| 中式美学 | 结构原则 | 示例 |
|---------|---------|------|
| 留白 | 函数间留空行 | 函数之间空一行 |
| 计白当黑 | 逻辑块留白 | 不同逻辑块之间空一行 |
| 线条之美 | 参数列表换行 | 超过3个参数就换行 |

### 层次规范

| 中式美学 | 层次原则 | 示例 |
|---------|---------|------|
| 墨分五色 | 错误处理分层 | critical/error/warning/info/debug |
| 虚实相生 | 接口与实现分离 | Protocol 为虚，实现为实 |
| 中和 | 平衡简洁与可读 | 不过度设计，也不过于简陋 |

---

## 三、中式美学检查清单

在写代码前，问自己：

### 留白
- [ ] 函数之间是否有空行？
- [ ] 逻辑块之间是否有留白？
- [ ] 代码是否有"呼吸感"？

### 虚实相生
- [ ] 接口与实现是否分离？
- [ ] 抽象层次是否清晰？
- [ ] 虚实是否平衡？

### 写意
- [ ] 命名是否有神韵？
- [ ] 函数是否有意境？
- [ ] 是否不拘泥于形似？

### 中和
- [ ] 简洁与可读是否平衡？
- [ ] 性能与优雅是否平衡？
- [ ] 是否过犹不及？

### 含蓄
- [ ] 命名是否含蓄而精准？
- [ ] 逻辑是否简洁而深邃？
- [ ] 是否让代码自己说话？

### 气韵生动
- [ ] 变量命名是否有生命力？
- [ ] 函数流程是否有节奏感？
- [ ] 代码结构是否有呼吸感？

### 天人合一
- [ ] 代码是否符合业务逻辑？
- [ ] 命名是否符合人类直觉？
- [ ] 结构是否符合问题本质？

### 线条之美
- [ ] 长参数列表是否换行？
- [ ] 逻辑块是否清晰？
- [ ] 缩进是否一致？

### 墨分五色
- [ ] 错误处理是否有层次？
- [ ] 日志级别是否分明？
- [ ] 代码结构是否有深浅？

### 计白当黑
- [ ] 类的方法之间是否有空白？
- [ ] 逻辑块之间是否有空白？
- [ ] 空白是否是代码呼吸的空间？

---

## 四、蒙多中式美学宣言

> "代码之道，源于东方。
> 留白有致，虚实相生。
> 写意传神，中和为美。
> 含蓄深邃，气韵生动。
> 天人合一，线条流畅。
> 墨分五色，计白当黑。
> 
> 蒙多，以中式美学，写现代代码。"

---

*THE EMPEROR has spoken.*
*蒙多已言。*
