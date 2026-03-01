import json
import threading
from datetime import datetime
from pathlib import Path

from async_context_engine.models import TaskRecord
from async_context_engine.store import TaskStore


class FileTaskStore(TaskStore):
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, default=str, indent=2))

    def _to_record(self, d: dict) -> TaskRecord:
        return TaskRecord(
            task_id=d["task_id"],
            thread_id=d["thread_id"],
            status=d["status"],
            description=d["description"],
            result=d.get("result"),
            error=d.get("error"),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )

    def _from_record(self, record: TaskRecord) -> dict:
        return {
            "task_id": record.task_id,
            "thread_id": record.thread_id,
            "status": record.status,
            "description": record.description,
            "result": record.result,
            "error": record.error,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    def create_task(self, record: TaskRecord) -> None:
        with self._lock:
            data = self._read()
            data[record.task_id] = self._from_record(record)
            self._write(data)

    def update_task(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            data = self._read()
            entry = data[task_id]
            entry["status"] = status
            if result is not None:
                entry["result"] = result
            if error is not None:
                entry["error"] = error
            entry["updated_at"] = datetime.now().isoformat()
            self._write(data)

    def get_task(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            data = self._read()
            entry = data.get(task_id)
            if entry is None:
                return None
            return self._to_record(entry)

    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]:
        with self._lock:
            data = self._read()
            return [
                self._to_record(e)
                for e in data.values()
                if e["thread_id"] == thread_id
            ]

    def get_tasks_by_status(self, thread_id: str, status: str) -> list[TaskRecord]:
        with self._lock:
            data = self._read()
            return [
                self._to_record(e)
                for e in data.values()
                if e["thread_id"] == thread_id and e["status"] == status
            ]
