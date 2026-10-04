"""" The bus.py distributes the event from the adapter to all of the subscribers (functions) according to their event_type. """
import asyncio
import logging
import inspect
from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Union, Literal
from .schema import Event, BusMessage

# Using logger if something goes wrong with the subscriber to log it.
logger = logging.getLogger(__name__)

EventType = Literal["llm_call", "tool_call"]

SyncCallback = Callable[[Event], None]      # syncrhonous Subscriber(function) that accepts Event and returns None
AsyncCallback = Callable[[Event] , Awaitable[None]]     # async Subscriber returns Awaitable
Callback = Union[SyncCallback , AsyncCallback]  # Subscriber is either async or sync.

@dataclass # rather than writing def __init__()
class Subscription:
    callback : Callback # Actual function
    event_type : EventType | None = None
    is_async : bool = False


class EventBus:
    def __init__(self , trajectory_id: str) -> None:
        self.trajectory_id = trajectory_id
        self.subscribers = list[Subscription] = []

    # Register a function using subscribe to receive future events.
    def subscribe(self , callback: Callback , event_type: Optional[str] = None) -> None :
        # check if a func is asynchronous
        is_async = inspect.iscoroutinefunction(callback)
        self.subscribers.append(Subscription(callback=callback , event_type=event_type ,is_async=is_async))

    # Removes a subscriber.
    def unsubscribe(self , callback: Callback) -> None :
        self.subscribers = [ sub for sub in self.subscribers if sub.callback is not callback]

    # Both Event and ProposedAction can travel through EventBus if they follow BusMessage Protocol:
    def publish(self , message: BusMessage):
        for subscriber in self.subscribers :
            if subscriber.event_type is not None and subscriber.event_type != message.event_type :
                continue

            if subscriber.is_async :
                asyncio.create_task(self.run_async(subscriber.callback, message))
            else :
                self.run_sync(subscriber.callback, message)

    def run_sync(self, callback: SyncCallback , event: Event) -> None:
        try :
            callback(event)

        except Exception:
            logger.exception("Subscriber %r raised while handling event %s", callback, event.event_id,)

    async def run_async(self, callback: AsyncCallback, event: Event) -> None:
        try :
            await callback(event)

        except Exception:
            logger.exception("Async Subscriber %r raised while handling event %s", callback, event.event_id,)
