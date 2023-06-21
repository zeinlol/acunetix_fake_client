from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.classes.target import AcunetixTarget


@dataclass
class ClientWatcher:
    uuid: str
    last_time_request: datetime = None

    def update_last_request_time(self):
        self.last_time_request = datetime.now()

    @property
    def is_no_requests(self) -> bool:
        return (datetime.now() - self.last_time_request) > timedelta(minutes=5)


@dataclass
class ClientTarget:
    address: str
    target_id: str = None
    order: int = None
    watchers: list[ClientWatcher] = field(default_factory=list)

    @property
    def watchers_amount(self) -> int:
        return len(self.watchers)

    def add_watcher(self, watcher: ClientWatcher):
        if not next(
            filter(lambda _watcher: _watcher.uuid == watcher.uuid, self.watchers),
            None,
        ):
            self.watchers.append(watcher)

    def remove_watcher(self, watcher: ClientWatcher):
        print('removing watcher')
        print(watcher)
        self.watchers = list(filter(lambda _watcher: _watcher.uuid != watcher.uuid, self.watchers))

class TargetsQueue:
    def __init__(self):
        self.targets: list[ClientTarget] = []
        self.watchers: list[ClientWatcher] = []

    @staticmethod
    def _init_target(target: dict) -> ClientTarget:
        return ClientTarget(
            address=target['address'],
        )

    def get_watcher(self, client_uuid: str) -> ClientWatcher:
        return next(filter(lambda watcher: watcher.uuid == client_uuid, self.watchers), None,
        ) or self._init_watcher(client_uuid=client_uuid)


    def _init_watcher(self, client_uuid: str) -> ClientWatcher:
        watcher = ClientWatcher(uuid=client_uuid)
        watcher.update_last_request_time()
        self.watchers.append(watcher)
        return watcher

    def _find_target(self, target: ClientTarget) -> ClientTarget | None:
        return next(filter(lambda item: item.address == target.address, self.targets), None)


    def check_target(self, target: dict, watcher: ClientWatcher) -> ClientTarget:
        self.remove_old_watchers()
        print('self.targets: before checking')
        print(self.targets)
        _target = self._init_target(target=target)
        queue_target = self._find_target(target=_target)
        if not queue_target:
            self.targets.append(_target)
            queue_target = _target
        print('self.targets: after checking')
        print(self.targets)
        queue_target.order = self.targets.index(queue_target)
        queue_target.add_watcher(watcher=watcher)
        return queue_target

    def delete_target(self, target: dict, watcher: ClientWatcher) -> bool:
        self.remove_old_watchers()
        is_target_was_removed = False
        print('self.targets: before deleting')
        print(self.targets)
        _target = self._find_target(target=self._init_target(target=target))
        _target.remove_watcher(watcher=watcher)
        if _target.watchers_amount <=0:
            self.targets = list(filter(lambda item: item.address != _target.address, self.targets))
            is_target_was_removed = True
        print('self.targets: after deleting')
        print(self.targets)
        return is_target_was_removed

    def fill_current_targets(self, targets: list["AcunetixTarget"]):
        for target in targets:
            self.targets.append(ClientTarget(address=target.address, target_id=target.target_id))

    def remove_old_watchers(self):
        for _client_target in self.targets:
            for watcher in _client_target.watchers:
                if watcher.is_no_requests:
                    _client_target.remove_watcher(watcher=watcher)
            if _client_target.watchers_amount <=0:
                self.targets = list(filter(lambda item: item.address != _client_target.address, self.targets))