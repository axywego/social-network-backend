import zlib

def get_ordered_pair(id1, id2):
    return (id1, id2) if id1 < id2 else (id2, id1)

def compress_message(msg: str) -> bytes:
    return zlib.compress(msg.encode('utf-8'), level=6)

def decompress_message(bytes_msg: bytes) -> str:
    return zlib.decompress(bytes_msg).decode('utf-8')