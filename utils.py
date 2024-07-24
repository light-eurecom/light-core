from loguru import logger # type: ignore
import gzip
import io

logger.remove()  # Remove the default configuration (file handler)
logger.add(lambda msg: print(msg, end=''), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO", diagnose=False)


xor = lambda x, y: bytes(i ^ j for i, j in zip(x, y))


def compress_chunk(chunk):
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
        f.write(chunk)
    return buffer.getvalue()