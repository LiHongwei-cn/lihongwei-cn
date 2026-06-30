#!/usr/bin/env python3
"""蒙多知识库构建器 — 爬取编程知识并存储到 RAG 系统"""

import sys
import json
import time
from pathlib import Path

# 添加 MUNDO 路径
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_retriever import get_knowledge_retriever

# ═══════════════════════════════════════════════
# 知识定义 — 蒙多的底层架构
# ═══════════════════════════════════════════════

KNOWLEDGE_BASE = {
    # ─── Python 核心 ───
    "python_syntax": {
        "topic": "python",
        "category": "syntax",
        "items": [
            {
                "title": "Python 列表推导式",
                "content": """列表推导式是 Python 中创建列表的简洁语法：
[expression for item in iterable if condition]

示例：
squares = [x**2 for x in range(10)]  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
evens = [x for x in range(20) if x % 2 == 0]  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
words = [word.upper() for word in ['hello', 'world']]  # ['HELLO', 'WORLD']

嵌套推导：
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

字典推导：
squares_dict = {x: x**2 for x in range(5)}  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

集合推导：
unique_chars = {char for word in ['hello', 'world'] for char in word}  # {'h', 'e', 'l', 'o', 'w', 'r', 'd'}""",
                "importance": 9,
                "tags": ["python", "list", "comprehension", "syntax"]
            },
            {
                "title": "Python 装饰器",
                "content": """装饰器是 Python 的高级函数，用于修改或扩展函数行为：

基本装饰器：
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数调用前")
        result = func(*args, **kwargs)
        print("函数调用后")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

带参数的装饰器：
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello {name}!")

类装饰器：
class Timer:
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args, **kwargs):
        start = time.time()
        result = self.func(*args, **kwargs)
        end = time.time()
        print(f"{self.func.__name__} 耗时: {end-start:.2f}秒")
        return result

functools.wraps 保留原函数信息：
import functools

def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper""",
                "importance": 9,
                "tags": ["python", "decorator", "function", "advanced"]
            },
            {
                "title": "Python 生成器",
                "content": """生成器是惰性求值的迭代器，节省内存：

生成器函数：
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# 使用
fib = fibonacci()
next(fib)  # 0
next(fib)  # 1
next(fib)  # 1

生成器表达式：
squares = (x**2 for x in range(1000000))  # 不立即计算，惰性求值

send 方法：
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value

gen = accumulator()
next(gen)  # 启动生成器
gen.send(10)  # 10
gen.send(20)  # 30
gen.send(30)  # 60

yield from 委托：
def chain(*iterables):
    for it in iterables:
        yield from it

list(chain([1, 2], [3, 4], [5, 6]))  # [1, 2, 3, 4, 5, 6]""",
                "importance": 9,
                "tags": ["python", "generator", "iterator", "memory"]
            },
            {
                "title": "Python 异步编程",
                "content": """Python asyncio 异步编程：

基本异步函数：
import asyncio

async def fetch_data(url):
    print(f"开始获取 {url}")
    await asyncio.sleep(1)  # 模拟 IO 操作
    return f"{url} 的数据"

async def main():
    # 并发执行多个协程
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    print(results)

asyncio.run(main())

异步上下文管理器：
class AsyncResource:
    async def __aenter__(self):
        print("获取资源")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("释放资源")

异步迭代器：
class AsyncRange:
    def __init__(self, stop):
        self.stop = stop
        self.current = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.current >= self.stop:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)
        self.current += 1
        return self.current - 1

TaskGroup (Python 3.11+)：
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data("url1"))
        task2 = tg.create_task(fetch_data("url2"))
    # 所有任务完成后自动退出
    print(task1.result(), task2.result())""",
                "importance": 8,
                "tags": ["python", "async", "await", "concurrency"]
            },
            {
                "title": "Python 类型注解",
                "content": """Python 类型注解（Type Hints）：

基本类型：
def greet(name: str) -> str:
    return f"Hello {name}"

age: int = 25
height: float = 1.75
is_student: bool = False

容器类型：
from typing import List, Dict, Tuple, Set, Optional

names: List[str] = ["Alice", "Bob"]
scores: Dict[str, int] = {"Alice": 95, "Bob": 87}
point: Tuple[int, int] = (10, 20)
unique_ids: Set[int] = {1, 2, 3}

可选类型：
def find_user(user_id: int) -> Optional[str]:
    if user_id == 1:
        return "Alice"
    return None

Union 类型：
from typing import Union

def process(value: Union[int, str]) -> str:
    return str(value)

Python 3.10+ 新语法：
def process(value: int | str) -> str:
    return str(value)

def find_user(user_id: int) -> str | None:
    ...

TypeVar 泛型：
from typing import TypeVar, List

T = TypeVar('T')

def first(items: List[T]) -> T:
    return items[0]

Protocol（结构化子类型）：
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def draw_something(shape: Drawable) -> None:
    shape.draw()""",
                "importance": 8,
                "tags": ["python", "typing", "type-hints", "annotations"]
            }
        ]
    },
    
    # ─── Java 核心 ───
    "java_syntax": {
        "topic": "java",
        "category": "syntax",
        "items": [
            {
                "title": "Java 面向对象编程",
                "content": """Java OOP 四大特性：

1. 封装：
public class Person {
    private String name;
    private int age;
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) { 
        if (age >= 0) this.age = age; 
    }
}

2. 继承：
public class Student extends Person {
    private String school;
    
    public Student(String name, int age, String school) {
        super(name, age);
        this.school = school;
    }
    
    @Override
    public String toString() {
        return super.toString() + " studying at " + school;
    }
}

3. 多态：
Animal animal = new Dog();  // 向上转型
animal.speak();  // 调用 Dog 的 speak 方法

Dog dog = (Dog) animal;  // 向下转型
if (animal instanceof Cat) {  // 类型检查
    Cat cat = (Cat) animal;
}

4. 抽象：
public abstract class Shape {
    abstract double area();
    abstract double perimeter();
    
    public void describe() {
        System.out.println("Area: " + area());
    }
}

public class Circle extends Shape {
    private double radius;
    
    @Override
    double area() { return Math.PI * radius * radius; }
    
    @Override
    double perimeter() { return 2 * Math.PI * radius; }
}""",
                "importance": 9,
                "tags": ["java", "oop", "inheritance", "polymorphism"]
            },
            {
                "title": "Java 集合框架",
                "content": """Java 集合框架核心接口和实现：

List（有序集合）：
// ArrayList - 数组实现，随机访问快
List<String> arrayList = new ArrayList<>();
arrayList.add("Alice");
arrayList.add("Bob");
arrayList.get(0);  // "Alice"

// LinkedList - 链表实现，插入删除快
List<String> linkedList = new LinkedList<>();
linkedList.addFirst("First");
linkedList.addLast("Last");

Set（无重复集合）：
// HashSet - 哈希表实现，无序
Set<String> hashSet = new HashSet<>();
hashSet.add("Alice");
hashSet.contains("Alice");  // true

// TreeSet - 红黑树实现，有序
Set<Integer> treeSet = new TreeSet<>();
treeSet.add(3);
treeSet.add(1);
treeSet.add(2);
// 遍历顺序: 1, 2, 3

Map（键值对）：
// HashMap - 哈希表实现
Map<String, Integer> hashMap = new HashMap<>();
hashMap.put("Alice", 95);
hashMap.get("Alice");  // 95
hashMap.getOrDefault("Bob", 0);  // 0

// TreeMap - 红黑树实现，按键排序
Map<String, Integer> treeMap = new TreeMap<>();
treeMap.put("Charlie", 85);
treeMap.put("Alice", 95);
treeMap.put("Bob", 87);
// 遍历顺序: Alice, Bob, Charlie

Queue（队列）：
// PriorityQueue - 优先队列
Queue<Integer> pq = new PriorityQueue<>();
pq.offer(3);
pq.offer(1);
pq.offer(2);
pq.poll();  // 1 (最小值)

// Deque - 双端队列
Deque<String> deque = new ArrayDeque<>();
deque.offerFirst("First");
deque.offerLast("Last");
deque.pollFirst();  // "First" """,
                "importance": 9,
                "tags": ["java", "collections", "list", "set", "map"]
            },
            {
                "title": "Java Lambda 和 Stream",
                "content": """Java 8+ Lambda 表达式和 Stream API：

Lambda 表达式：
// 无参数
Runnable r = () -> System.out.println("Hello");

// 单参数
Consumer<String> printer = s -> System.out.println(s);

// 多参数
Comparator<String> comp = (a, b) -> a.length() - b.length();

// 方法引用
Consumer<String> printer = System.out::println;
Function<String, Integer> parser = Integer::parseInt;

Stream API：
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "David");

// 过滤
List<String> filtered = names.stream()
    .filter(name -> name.length() > 3)
    .collect(Collectors.toList());
// [Alice, Charlie, David]

// 映射
List<Integer> lengths = names.stream()
    .map(String::length)
    .collect(Collectors.toList());
// [5, 3, 7, 5]

// 归约
int totalLength = names.stream()
    .mapToInt(String::length)
    .sum();  // 20

// 分组
Map<Integer, List<String>> grouped = names.stream()
    .collect(Collectors.groupingBy(String::length));
// {3=[Bob], 5=[Alice, David], 7=[Charlie]}

// 排序
List<String> sorted = names.stream()
    .sorted(Comparator.comparing(String::length).reversed())
    .collect(Collectors.toList());
// [Charlie, Alice, David, Bob]

// 并行流
long count = names.parallelStream()
    .filter(name -> name.startsWith("A"))
    .count();""",
                "importance": 9,
                "tags": ["java", "lambda", "stream", "functional"]
            }
        ]
    },
    
    # ─── 编程基础 ───
    "programming_fundamentals": {
        "topic": "programming",
        "category": "fundamentals",
        "items": [
            {
                "title": "数据结构 - 数组和链表",
                "content": """数组（Array）：
- 连续内存存储
- O(1) 随机访问
- O(n) 插入/删除（需要移动元素）
- 固定大小（静态数组）或动态扩容（动态数组）

Python 实现：
class DynamicArray:
    def __init__(self):
        self.data = []
        self.size = 0
    
    def get(self, index):
        return self.data[index]
    
    def append(self, value):
        self.data.append(value)
        self.size += 1

链表（Linked List）：
- 非连续内存存储
- O(n) 随机访问
- O(1) 插入/删除（已知位置）
- 动态大小

Python 实现：
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, val):
        if not self.head:
            self.head = ListNode(val)
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = ListNode(val)
    
    def delete(self, val):
        if self.head and self.head.val == val:
            self.head = self.head.next
            return
        curr = self.head
        while curr.next and curr.next.val != val:
            curr = curr.next
        if curr.next:
            curr.next = curr.next.next

选择依据：
- 频繁随机访问 → 数组
- 频繁插入/删除 → 链表
- 内存受限 → 链表（无需连续空间）""",
                "importance": 10,
                "tags": ["data-structure", "array", "linked-list", "complexity"]
            },
            {
                "title": "数据结构 - 栈和队列",
                "content": """栈（Stack）- LIFO（后进先出）：
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        return self.items.pop()
    
    def peek(self):
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) == 0

应用场景：
- 函数调用栈
- 括号匹配
- 表达式求值
- 深度优先搜索（DFS）

队列（Queue）- FIFO（先进先出）：
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        self.items.append(item)
    
    def dequeue(self):
        return self.items.popleft()
    
    def front(self):
        return self.items[0]
    
    def is_empty(self):
        return len(self.items) == 0

应用场景：
- 任务调度
- 广度优先搜索（BFS）
- 缓存（LRU Cache）
- 消息队列

双端队列（Deque）：
class Deque:
    def __init__(self):
        self.items = deque()
    
    def add_front(self, item):
        self.items.appendleft(item)
    
    def add_rear(self, item):
        self.items.append(item)
    
    def remove_front(self):
        return self.items.popleft()
    
    def remove_rear(self):
        return self.items.pop()""",
                "importance": 10,
                "tags": ["data-structure", "stack", "queue", "deque"]
            },
            {
                "title": "算法 - 排序算法",
                "content": """常见排序算法：

1. 冒泡排序（Bubble Sort）- O(n²)：
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

2. 选择排序（Selection Sort）- O(n²)：
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

3. 插入排序（Insertion Sort）- O(n²)：
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i-1
        while j >= 0 and key < arr[j]:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr

4. 快速排序（Quick Sort）- O(n log n) 平均：
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

5. 归并排序（Merge Sort）- O(n log n)：
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result""",
                "importance": 10,
                "tags": ["algorithm", "sorting", "complexity", "divide-conquer"]
            },
            {
                "title": "算法 - 搜索算法",
                "content": """常见搜索算法：

1. 线性搜索（Linear Search）- O(n)：
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1

2. 二分搜索（Binary Search）- O(log n)：
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

递归版本：
def binary_search_recursive(arr, target, left, right):
    if left > right:
        return -1
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)

3. 深度优先搜索（DFS）：
def dfs(graph, node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    print(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

4. 广度优先搜索（BFS）：
from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    while queue:
        node = queue.popleft()
        print(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

选择依据：
- 无序数据 → 线性搜索
- 有序数据 → 二分搜索
- 图/树遍历 → DFS（栈）或 BFS（队列）""",
                "importance": 10,
                "tags": ["algorithm", "search", "binary-search", "dfs", "bfs"]
            },
            {
                "title": "设计模式 - 创建型",
                "content": """创建型设计模式：

1. 单例模式（Singleton）：
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

2. 工厂模式（Factory）：
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

class AnimalFactory:
    @staticmethod
    def create(animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        raise ValueError(f"Unknown animal: {animal_type}")

3. 建造者模式（Builder）：
class Computer:
    def __init__(self):
        self.cpu = None
        self.ram = None
        self.storage = None

class ComputerBuilder:
    def __init__(self):
        self.computer = Computer()
    
    def set_cpu(self, cpu):
        self.computer.cpu = cpu
        return self
    
    def set_ram(self, ram):
        self.computer.ram = ram
        return self
    
    def set_storage(self, storage):
        self.computer.storage = storage
        return self
    
    def build(self):
        return self.computer

使用：
computer = (ComputerBuilder()
    .set_cpu("Intel i7")
    .set_ram("16GB")
    .set_storage("512GB SSD")
    .build())

4. 原型模式（Prototype）：
import copy

class Prototype:
    def clone(self):
        return copy.deepcopy(self)""",
                "importance": 9,
                "tags": ["design-pattern", "singleton", "factory", "builder"]
            },
            {
                "title": "设计模式 - 结构型",
                "content": """结构型设计模式：

1. 适配器模式（Adapter）：
class EuropeanSocket:
    def voltage(self):
        return 230

class AmericanSocket:
    def voltage(self):
        return 120

class Adapter:
    def __init__(self, european_socket):
        self.european_socket = european_socket
    
    def voltage(self):
        return self.european_socket.voltage() * 0.52  # 转换

2. 装饰器模式（Decorator）：
class Coffee:
    def cost(self):
        return 5

class MilkDecorator:
    def __init__(self, coffee):
        self.coffee = coffee
    
    def cost(self):
        return self.coffee.cost() + 2

class SugarDecorator:
    def __init__(self, coffee):
        self.coffee = coffee
    
    def cost(self):
        return self.coffee.cost() + 1

使用：
coffee = Coffee()
coffee_with_milk = MilkDecorator(coffee)
coffee_with_milk_and_sugar = SugarDecorator(coffee_with_milk)
print(coffee_with_milk_and_sugar.cost())  # 8

3. 外观模式（Facade）：
class CPU:
    def process(self):
        return "Processing"

class Memory:
    def load(self):
        return "Loading"

class HardDrive:
    def read(self):
        return "Reading"

class ComputerFacade:
    def __init__(self):
        self.cpu = CPU()
        self.memory = Memory()
        self.hard_drive = HardDrive()
    
    def start(self):
        return f"{self.hard_drive.read()} -> {self.memory.load()} -> {self.cpu.process()}"

4. 代理模式（Proxy）：
class RealImage:
    def __init__(self, filename):
        self.filename = filename
        self.load_from_disk()
    
    def load_from_disk(self):
        print(f"Loading {self.filename}")
    
    def display(self):
        print(f"Displaying {self.filename}")

class ProxyImage:
    def __init__(self, filename):
        self.filename = filename
        self.real_image = None
    
    def display(self):
        if self.real_image is None:
            self.real_image = RealImage(self.filename)
        self.real_image.display()""",
                "importance": 9,
                "tags": ["design-pattern", "adapter", "decorator", "facade", "proxy"]
            }
        ]
    },
    
    # ─── RAG 技术 ───
    "rag_technology": {
        "topic": "rag",
        "category": "theory",
        "items": [
            {
                "title": "RAG 基本原理",
                "content": """RAG（Retrieval-Augmented Generation）基本原理：

核心思想：
将检索（Retrieval）与生成（Generation）结合，让 LLM 能够访问外部知识。

架构：
1. 索引阶段（Indexing）：
   - 文档分块（Chunking）
   - 向量化（Embedding）
   - 存储到向量数据库

2. 检索阶段（Retrieval）：
   - 用户查询向量化
   - 相似度搜索（余弦相似度、欧氏距离）
   - 返回 Top-K 相关文档

3. 生成阶段（Generation）：
   - 将检索到的文档作为上下文
   - 与用户查询一起输入 LLM
   - LLM 基于上下文生成回答

优势：
- 减少幻觉（Hallucination）
- 知识可更新（无需重新训练）
- 可追溯来源
- 节省训练成本

挑战：
- 检索质量影响生成质量
- 文档分块策略很重要
- 向量相似度不等于语义相似度
- 上下文窗口限制

应用场景：
- 知识库问答
- 文档对话
- 客服系统
- 研究助手""",
                "importance": 10,
                "tags": ["rag", "retrieval", "generation", "llm"]
            },
            {
                "title": "RAG 文档分块策略",
                "content": """RAG 文档分块（Chunking）策略：

1. 固定大小分块：
def fixed_size_chunk(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

2. 句子分块：
import nltk
nltk.download('punkt')

def sentence_chunk(text, max_chunk_size=500):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        if current_size + len(sentence) > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = len(sentence)
        else:
            current_chunk.append(sentence)
            current_size += len(sentence)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

3. 语义分块：
def semantic_chunk(text, similarity_threshold=0.8):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        similarity = compute_similarity(sentences[i-1], sentences[i])
        if similarity > similarity_threshold:
            current_chunk.append(sentences[i])
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

4. 递归分块：
def recursive_chunk(text, chunk_size=500, separators=["\n\n", "\n", " ", ""]):
    if len(text) <= chunk_size:
        return [text]
    
    for sep in separators:
        if sep in text:
            splits = text.split(sep)
            chunks = []
            current_chunk = []
            current_size = 0
            
            for split in splits:
                if current_size + len(split) > chunk_size:
                    chunks.append(sep.join(current_chunk))
                    current_chunk = [split]
                    current_size = len(split)
                else:
                    current_chunk.append(split)
                    current_size += len(split)
            
            if current_chunk:
                chunks.append(sep.join(current_chunk))
            return chunks
    
    return [text]

最佳实践：
- chunk_size: 500-1000 tokens
- overlap: 50-100 tokens
- 根据文档类型选择策略
- 保留元数据（标题、来源）""",
                "importance": 9,
                "tags": ["rag", "chunking", "text-splitting", "preprocessing"]
            },
            {
                "title": "RAG 向量检索",
                "content": """RAG 向量检索技术：

1. 向量化（Embedding）：
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["Hello world", "How are you?"])

2. 相似度计算：
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

3. 向量数据库：
# FAISS (Facebook AI Similarity Search)
import faiss

dimension = 384  # 向量维度
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)  # 添加向量

# 搜索
query_embedding = model.encode(["search query"])
distances, indices = index.search(query_embedding, k=5)  # Top-5

# ChromaDB
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_collection")

collection.add(
    documents=["doc1", "doc2"],
    embeddings=[embedding1, embedding2],
    ids=["id1", "id2"]
)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

4. 混合检索（Hybrid Retrieval）：
# BM25 + 向量检索
from rank_bm25 import BM25Okapi

def hybrid_retrieval(query, documents, query_embedding, doc_embeddings, alpha=0.5):
    # BM25 分数
    tokenized_docs = [doc.split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    bm25_scores = bm25.get_scores(query.split())
    
    # 向量相似度分数
    vector_scores = [cosine_similarity(query_embedding, doc_emb) 
                     for doc_emb in doc_embeddings]
    
    # 加权融合
    combined_scores = alpha * bm25_scores + (1 - alpha) * np.array(vector_scores)
    
    # 返回排序后的文档索引
    return np.argsort(combined_scores)[::-1]

最佳实践：
- 选择合适的 Embedding 模型
- 使用混合检索提高准确率
- 定期更新向量索引
- 缓存热门查询结果""",
                "importance": 9,
                "tags": ["rag", "embedding", "vector-db", "similarity-search"]
            }
        ]
    },
    
    # ─── 软件工程 ───
    "software_engineering": {
        "topic": "software_engineering",
        "category": "architecture",
        "items": [
            {
                "title": "SOLID 原则",
                "content": """SOLID 面向对象设计原则：

1. 单一职责原则（SRP）：
一个类应该只有一个引起它变化的原因。

# 违反 SRP
class User:
    def save_to_db(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# 遵循 SRP
class User: ...
class UserRepository:
    def save(self, user): ...
class EmailService:
    def send(self, user, message): ...
class ReportGenerator:
    def generate(self, user): ...

2. 开闭原则（OCP）：
对扩展开放，对修改关闭。

# 违反 OCP
def calculate_area(shape):
    if isinstance(shape, Circle):
        return 3.14 * shape.radius ** 2
    elif isinstance(shape, Rectangle):
        return shape.width * shape.height

# 遵循 OCP
class Shape(ABC):
    @abstractmethod
    def area(self): ...

class Circle(Shape):
    def area(self):
        return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def area(self):
        return self.width * self.height

3. 里氏替换原则（LSP）：
子类必须能够替换它的父类。

4. 接口隔离原则（ISP）：
客户端不应该依赖它不需要的接口。

# 违反 ISP
class Worker(ABC):
    @abstractmethod
    def work(self): ...
    @abstractmethod
    def eat(self): ...

# 遵循 ISP
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Eatable(ABC):
    @abstractmethod
    def eat(self): ...

class Robot(Workable):  # Robot 不需要 eat
    def work(self): ...

5. 依赖倒置原则（DIP）：
高层模块不应该依赖低层模块，两者都应该依赖抽象。

# 违反 DIP
class MySQLDatabase:
    def query(self): ...

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # 直接依赖具体实现

# 遵循 DIP
class Database(ABC):
    @abstractmethod
    def query(self): ...

class MySQLDatabase(Database): ...
class PostgreSQLDatabase(Database): ...

class UserService:
    def __init__(self, db: Database):  # 依赖抽象
        self.db = db""",
                "importance": 10,
                "tags": ["solid", "design-principle", "oop", "architecture"]
            },
            {
                "title": "RESTful API 设计",
                "content": """RESTful API 设计原则：

1. 资源命名：
# 使用名词，复数形式
GET    /users          # 获取用户列表
GET    /users/123      # 获取特定用户
POST   /users          # 创建用户
PUT    /users/123      # 更新用户（全量）
PATCH  /users/123      # 更新用户（部分）
DELETE /users/123      # 删除用户

# 嵌套资源
GET    /users/123/posts        # 获取用户的所有帖子
GET    /users/123/posts/456    # 获取用户的特定帖子

2. HTTP 方法语义：
- GET: 获取资源，幂等
- POST: 创建资源，非幂等
- PUT: 更新资源（全量），幂等
- PATCH: 更新资源（部分），非幂等
- DELETE: 删除资源，幂等

3. 状态码：
200 OK                    # 成功
201 Created               # 创建成功
204 No Content            # 删除成功
400 Bad Request           # 请求错误
401 Unauthorized          # 未认证
403 Forbidden             # 无权限
404 Not Found             # 资源不存在
409 Conflict              # 冲突
500 Internal Server Error # 服务器错误

4. 查询参数：
GET /users?page=1&limit=10          # 分页
GET /users?sort=name&order=asc      # 排序
GET /users?filter[role]=admin       # 过滤
GET /users?fields=name,email        # 字段选择

5. 版本控制：
# URL 路径版本
GET /api/v1/users
GET /api/v2/users

# Header 版本
GET /users
Accept: application/vnd.myapi.v1+json

6. 错误响应：
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": [
            {"field": "email", "message": "Invalid email format"}
        ]
    }
}

最佳实践：
- 使用 HTTPS
- 无状态（Stateless）
- 使用 HATEOAS（可选）
- 限流（Rate Limiting）
- 缓存（Cache-Control）""",
                "importance": 9,
                "tags": ["rest", "api", "http", "web-development"]
            },
            {
                "title": "微服务架构",
                "content": """微服务架构设计：

核心原则：
1. 单一职责：每个服务负责一个业务能力
2. 独立部署：服务可以独立部署和扩展
3. 去中心化治理：服务可以选择不同的技术栈
4. 故障隔离：一个服务故障不影响其他服务

架构组件：
1. API Gateway：
   - 路由请求
   - 负载均衡
   - 认证授权
   - 限流熔断

2. 服务注册与发现：
   - 服务注册中心（Consul, Eureka, Nacos）
   - 服务发现（客户端/服务端）

3. 配置中心：
   - 集中管理配置
   - 动态配置更新
   - 配置版本控制

4. 服务通信：
   - 同步：REST, gRPC
   - 异步：消息队列（Kafka, RabbitMQ）

5. 服务治理：
   - 熔断器（Circuit Breaker）
   - 限流（Rate Limiting）
   - 降级（Fallback）
   - 重试（Retry）

示例架构：
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────┐
│ API Gateway │
└──────┬──────┘
       │
┌──────▼──────┐
│ Service     │
│ Discovery   │
└──────┬──────┘
       │
┌──────┴──────┬──────────────┬──────────────┐
│             │              │              │
▼             ▼              ▼              ▼
User Service  Order Service  Product Service  Payment Service
│             │              │              │
▼             ▼              ▼              ▼
User DB       Order DB       Product DB     Payment DB

Python 实现（FastAPI）：
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service/users/{user_id}")
        return response.json()

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    async with httpx.AsyncClient() as client:
        order = await client.get(f"http://order-service/orders/{order_id}")
        user = await client.get(f"http://user-service/users/{order.json()['user_id']}")
        return {"order": order.json(), "user": user.json()}""",
                "importance": 9,
                "tags": ["microservices", "architecture", "distributed-system", "api-gateway"]
            }
        ]
    }
}

def build_knowledge_base():
    """构建蒙多知识库"""
    print("开始构建蒙多知识库...")
    
    retriever = get_knowledge_retriever()
    
    total_items = 0
    for category, data in KNOWLEDGE_BASE.items():
        topic = data["topic"]
        cat = data["category"]
        items = data["items"]
        
        print(f"\n正在加载 {topic}/{cat} ({len(items)} 项)...")
        
        for item in items:
            retriever.add_knowledge(
                content=item["content"],
                source=f"mundo-knowledge/{topic}/{cat}",
                category=f"{topic}_{cat}",
                metadata={
                    "topic": topic,
                    "category": cat,
                    "title": item["title"],
                    "importance": item["importance"],
                    "tags": item["tags"]
                }
            )
            total_items += 1
            print(f"  ✓ {item['title']}")
    
    # 保存到磁盘
    retriever.save_to_disk()
    
    print(f"\n知识库构建完成！共加载 {total_items} 项知识。")
    print(f"存储位置: ~/.hermes/mundo-agent/knowledge.json")

if __name__ == "__main__":
    build_knowledge_base()
