import datetime
import importlib.metadata

try:
    __version__ = importlib.metadata.version("busker")
except importlib.metadata.PackageNotFoundError:
    __version__ = datetime.date.today().strftime("%Y.%m.%d") + "+local"

