from loguru import logger # type: ignore

logger.remove()  # Remove the default configuration (file handler)
logger.add(lambda msg: print(msg, end=''), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO", diagnose=False)


xor = lambda x, y: bytes(i ^ j for i, j in zip(x, y))
