from PySide6.QtCore import Signal, QObject


class WorkerSignals(QObject):
    """Defining signals for Worker threads"""
    status_updated = Signal(str)
    progress_updated = Signal(int)
    conversion_finished = Signal(str, int)
    conversion_failed = Signal(str)
