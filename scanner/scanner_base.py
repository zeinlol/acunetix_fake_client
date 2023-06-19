from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.classes.target import AcunetixTarget


@dataclass
class ClientTarget:
    address: str
    target_id: str = None
    order: int = None
    watchers_amount: int = 0

class TargetsQueue:
    def __init__(self):
        self.targets: list[ClientTarget] = []

    @staticmethod
    def _init_target(target: dict) -> ClientTarget:
        return ClientTarget(
            address=target['address'],
        )

    def _find_target(self, target: ClientTarget) -> ClientTarget | None:
        return next(filter(lambda item: item.address == target.address, self.targets), None)


    def check_target(self, target: dict) -> ClientTarget:
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
        # TODO: rework watchers to understand who is requesting to remove duplicate requests
        queue_target.watchers_amount += 1
        print('self.targets: after updating element')
        print(self.targets)
        return queue_target

    def delete_target(self, target: dict) -> bool:
        is_target_was_removed = False
        print('self.targets: before deleting')
        print(self.targets)
        _target = self._find_target(target=self._init_target(target=target))
        # TODO: rework watchers to understand who is requesting to remove duplicate requests
        _target.watchers_amount -= 1
        if _target.watchers_amount <=0:
            self.targets = list(filter(lambda item: item.address != _target.address, self.targets))
            is_target_was_removed = True
        print('self.targets: after deleting')
        print(self.targets)
        return is_target_was_removed

    def fill_current_targets(self, targets: list["AcunetixTarget"]):
        for target in targets:
            self.targets.append(ClientTarget(address=target.address, target_id=target.target_id))