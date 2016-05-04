# Backend-Implemention

## File Tree

            ├── backend
            │   ├── factory.py
            │   ├── protocols.py
            │   ├── websocket.py
            │  
            ├── decorators.py
            ├── middleware.py

- protocols.py: implemention of websocket protocol
- factory.py: websocket connection factory class for creating websocket protocol instance
- websocket.py: websocket connection class, including server api like `read` `write` `close`

- decorators.py: add specific decorator for view function if it is a websocket connection
- middleware.py: handshake of websocket connection

## Request Handle

> 请求处理使用了middleware,主要用于websocket连接的建立握手,拦截无效或断开的连接

- 通过对使用websocket请求的view方法添加decorator,并在decorator中使用`decorator_from_middleware(middleware)`引入middle类

```python
# code of view
@accept_websocket
def view(request):
    # ... ...

```

```python
# code of decorator
def accept_request(function):
    decorator_from_middleware(middlewareClass)
```

### Middleware

- process_request: 拦截request,判断是不是一个websocket请求,如果是,生成一个protocol实例
- process_view: 在执行view方法之前,完成handshake
- process\_response 和 process_exception: 处理连接断开的情况和异常


### Read Message

Websocket.py中是一个Websocket class,每一个实例都对应着一个websocket连接

```python
# __init__方法
def __init__(self, protocol):
    self.protocol = protocol
    self.closed = False
    self._message_queue = collections.deque()
```

class中除了实现一些`read/write message` `close` api之外,还重写了\__iter__()方法,所以
Webscoket class的实例是一个可迭代的对象, 只需要`for x in reuqest.websocket`就能取到message.
同时iter方法中简单地使用了yield作为返回.

```python
# __iter__
def __iter__(self):
    while True:
        message = self.wait() # To read message from socket
        yield message
        if message is None:
            break
```

`wait()`方法通过socket IO获取message,IO方面使用了多路复用的模型,使用了python自带的selector模块.

```python
    try:
        import selectors
    except ImportError:
        import selectors34 as selectors

    selector = selectors.DefaultSelector()

    self.selector.register(self.sock, selectors.EVENT_READ)
    events = self.selector.select()
    self.selector.unregister(self.sock)
```






