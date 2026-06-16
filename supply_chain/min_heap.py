"""Custom min-heap priority queue for Dijkstra node tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class _HeapEntry:
    """Internal heap node storing priority and payload.

    Attributes:
        priority: Sort key (lower is higher priority for min-heap).
        payload: Arbitrary associated data (e.g., vertex name).
        index: Current position in the heap array for O(log n) decrease-key.
    """

    priority: float
    payload: Any
    index: int = -1


class MinHeap:
    """Binary min-heap priority queue implemented from scratch.

    Supports insert, extract-min, peek-min, and decrease-key operations
    required by Dijkstra's algorithm with lazy deletion for stale entries.

    Attributes:
        _heap: Array representation of the binary heap.
        _position: Maps payload -> heap index for decrease-key lookups.
    """

    def __init__(self) -> None:
        """Initialize an empty min-heap.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        self._heap: List[_HeapEntry] = []
        self._position: Dict[Any, int] = {}

    def __len__(self) -> int:
        """Return number of elements currently in the heap."""
        return len(self._heap)

    def is_empty(self) -> bool:
        """Return True if the heap contains no elements.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        return len(self._heap) == 0

    def insert(self, priority: float, payload: Any) -> None:
        """Insert a new element or decrease-key if payload already exists.

        Args:
            priority: Numeric priority (smaller = higher priority).
            payload: Hashable identifier tracked by the heap.

        Time Complexity:
            O(log n) for sift-up after append.

        Space Complexity:
            O(1) additional space per element.
        """
        if payload in self._position:
            self.decrease_key(payload, priority)
            return

        entry = _HeapEntry(priority=priority, payload=payload, index=len(self._heap))
        self._heap.append(entry)
        self._position[payload] = entry.index
        self._sift_up(entry.index)

    def decrease_key(self, payload: Any, new_priority: float) -> None:
        """Lower the priority of an existing payload if it improves.

        Args:
            payload: Identifier to update.
            new_priority: New (lower or equal) priority value.

        Time Complexity:
            O(log n) sift-up when priority improves.

        Space Complexity:
            O(1).
        """
        if payload not in self._position:
            self.insert(new_priority, payload)
            return

        index = self._position[payload]
        entry = self._heap[index]
        if new_priority >= entry.priority:
            return

        entry.priority = new_priority
        self._sift_up(index)

    def extract_min(self) -> Tuple[float, Any]:
        """Remove and return the minimum-priority element.

        Returns:
            Tuple of (priority, payload).

        Raises:
            IndexError: If the heap is empty.

        Time Complexity:
            O(log n) sift-down after replacing root.

        Space Complexity:
            O(1).
        """
        if self.is_empty():
            raise IndexError("extract_min from empty heap")

        root = self._heap[0]
        last = self._heap.pop()
        del self._position[root.payload]

        if self._heap:
            last.index = 0
            self._heap[0] = last
            self._position[last.payload] = 0
            self._sift_down(0)

        return root.priority, root.payload

    def peek_min(self) -> Tuple[float, Any]:
        """Return the minimum element without removing it.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        if self.is_empty():
            raise IndexError("peek_min from empty heap")
        entry = self._heap[0]
        return entry.priority, entry.payload

    def _parent_index(self, index: int) -> int:
        """Return parent index for a given heap index."""
        return (index - 1) // 2

    def _left_child_index(self, index: int) -> int:
        """Return left child index for a given heap index."""
        return 2 * index + 1

    def _right_child_index(self, index: int) -> int:
        """Return right child index for a given heap index."""
        return 2 * index + 2

    def _swap(self, i: int, j: int) -> None:
        """Swap two heap entries and update position map.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._heap[i].index = i
        self._heap[j].index = j
        self._position[self._heap[i].payload] = i
        self._position[self._heap[j].payload] = j

    def _sift_up(self, index: int) -> None:
        """Restore min-heap property by bubbling an element upward.

        Time Complexity:
            O(log n) — height of binary heap.

        Space Complexity:
            O(1) iterative implementation.
        """
        while index > 0:
            parent = self._parent_index(index)
            if self._heap[index].priority >= self._heap[parent].priority:
                break
            self._swap(index, parent)
            index = parent

    def _sift_down(self, index: int) -> None:
        """Restore min-heap property by pushing an element downward.

        Time Complexity:
            O(log n) — height of binary heap.

        Space Complexity:
            O(1) iterative implementation.
        """
        size = len(self._heap)
        while True:
            smallest = index
            left = self._left_child_index(index)
            right = self._right_child_index(index)

            if left < size and self._heap[left].priority < self._heap[smallest].priority:
                smallest = left
            if right < size and self._heap[right].priority < self._heap[smallest].priority:
                smallest = right

            if smallest == index:
                break
            self._swap(index, smallest)
            index = smallest
