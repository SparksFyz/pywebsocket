# Protocol Implemention

- Protocol Implemention has two parts:
    - HandShake
    - Data Framing

[File Link]()

## HandShake

> handshake过程中,client发送一个改进(upgrade)后的http请求,server接收通过哈希和base64加密后生成key返回

### websocket URLs

> 对应http和https,websocket分别有"ws"和"wss"两种URL.

|                       URL                        | Protocol | default port |
|--------------------------------------------------|----------|--------------|
| "ws:" "//" host [ ":" port ] path [ "?" query ]  | http     |           80 |
| "wss:" "//" host [ ":" port ] path [ "?" query ] | https    |          443 |

### Accept Connection

- 检查request headers
    - 根据`HTTP_SEC_WEBSOCKET_VERSION`来获取websocket的version,根据version new相应的class.(目前只实现version13)
    - 确认headers中是否包含`HTTP_SEC_WEBSOCKET_KEY`和`HTTP_SEC_WEBSOCKET_VERSION`这两项
    - 检查是否包含`Sec-WebSocket-Protocol`
        - 如果包含则加入到response headers
- 生成`Sec-WebSocket-Accept`
    - 使用hashlib.sha1().update()将`HTTP_SEC_WEBSOCKET_KEY`和一段固定的string拼接起来
    - 最后使用base64.encoding

    ```python
        # code
        sha1 = hashlib.sha1()
        sha1.update(key)
        sha1.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")  # Magic value
        return base64.b64encode(sha1.digest())
    ```

- 返回response,response_headers中字符流结尾需要换行`\r\n`,需要包含以下fields:

    |          field           |              value               | required or optional |
    |--------------------------|----------------------------------|----------------------|
    | response code            | HTTP/1.1 101 Switching Protocols | required             |
    | Upgrade                  | websocket                        | required             |
    | Connection               | Upgrade                          | required             |
    | Sec-WebSocket-Accept     | s3pPLMBiTxaQ9kYGzzhZRbK+xOo=     | required             |
    | Sec-WebSocket-Protocol   |                                  | optional             |
    | Sec-WebSocket-Extensions |                                  | optional             |

> If client and server finish handshake, then the websocket connection is in the OPEN state.
At this point, the server may begin sending and receiving data.

PS: `Sec-WebSocket-Protocol`是个optional的fields,用来表示client优先使用哪个版本的协议,目前都是13,还存在75,76两个版本.


## Data & Control Framing

> rfc-6455中将帧分为控制帧和非控制帧(数据帧)

                      0                   1                   2                   3
                      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                     +-+-+-+-+-------+-+-------------+-------------------------------+
                     |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
                     |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
                     |N|V|V|V|       |S|             |   (if payload len==126/127)   |
                     | |1|2|3|       |K|             |                               |
                     +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
                     |     Extended payload length continued, if payload len == 127  |
                     + - - - - - - - - - - - - - - - +-------------------------------+
                     |                               |Masking-key, if MASK set to 1  |
                     +-------------------------------+-------------------------------+
                     | Masking-key (continued)       |          Payload Data         |
                     +-------------------------------- - - - - - - - - - - - - - - - +
                     :                     Payload Data continued ...                :
                     + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
                     |                     Payload Data continued ...                |
                     +---------------------------------------------------------------+

### Read Frame

> 使用struct.unpack()将字节流转换为python Integer

- Fin: 1 bit
    - fin 在第一个字节的最高位,用于表示消息是否结束,如果为1则该消息为消息尾部,如果为0则还有后续数据包

- Opcode: 4 bits
    - operation code 在第一个字节的低四位,表示消息的类型,消息类型一共有15种,包括预留设置
    - 在实现过程中主要用到以下几种:

        | opcode |      type     |  Interpretation  |
        |--------|---------------|------------------|
        | 0x8    | control frame | connection close |
        | 0x9    | control frame | ping             |
        | 0xA    | control frame | pong             |
        | 0x1    | data frame    | text             |
        | 0x2    | data frame    | binary           |

- Mask: 1 bit
    - mask 在第二个字节的最高位,表示是否需要掩码处理

- Payload length: 7 / 7 + 16 / 7 + 64 bits
    - payload length表示消息长度,第二个字节中只有7位,7位最多只能表示127,所以按长度分为三种情况:
        - 如果消息长度小于125,就直接用这7位表示消息长度
        - 如果消息的长度大于125,按需求可以使用后面的2-8个字节表示消息长度,如果等于126,则使用后面2个字节,如果等于127,则使用8个字节.

- Masking-key: 4 bytes
    - 如果前面的Mask为1,则在payload len后面的这四个字节表示掩码

- Payload Data:
    - 根据前面得到的payload length获取相应长度的data


### Read function

- 在server和client不断开的情况下,server会根据opcode做出相应的回应:
    - Data Frame(包括text和binary),返回data,继续往后传递.
    - Control Frame
        - 如果是ping,则返回pong
        - 如果是close connection,则需要判断data长度,如果长度大于2,则前两位是close\_code, 剩余的是close_reason
    - 如果不满足这两种情况,抛异常,断开websocket连接

### Write Frame

> 使用struct.pack()将python Integer转换为字节流

- write frame 即为read frame的逆过程,根据相应部分的长度转换为字节流拼接在一起,最后判断是否需要掩码处理.

### Masking function(client to server)

- 将masked-data 和 masking-key转成byte数组
- `data = data[i] ^ masking_key[i % 4]`

```python
#code
masking_key = array.array("B", masking_key)
data = array.array("B", data)
for i in range(len(data)):
    data = data[i] ^ masking_key[i % 4]
```







