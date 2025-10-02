import asyncio
import zmq
import zmq.asyncio
from typing import Callable, Optional
import logging


class ZMQListener:
    """
    ZeroMQ listener for blockchain event notifications.

    Listens for block hash notifications from cryptocurrency nodes and triggers
    callbacks when new blocks are detected. Supports both LTC and MEWC nodes.
    """

    def __init__(self, name: str, zmq_endpoint: str, on_block_callback: Callable):
        """
        Initialize ZMQ listener.

        Args:
            name: Human-readable name for this listener (e.g., "LTC", "MEWC")
            zmq_endpoint: ZMQ endpoint URL (e.g., "tcp://127.0.0.1:28332")
            on_block_callback: Async function to call when new block is received
        """
        self.name = name
        self.zmq_endpoint = zmq_endpoint
        self.on_block_callback = on_block_callback
        self.context = None
        self.socket = None
        self.logger = logging.getLogger(f"ZMQ-{name}")
        self._running = False
        self._task = None

    async def start(self):
        """Start both ZMQ listeners"""
        self.logger.info("Starting dual ZMQ listeners...")

        # Start LTC listener if endpoint provided
        if self.ltc_endpoint and self.on_ltc_block:
            self.ltc_listener = ZMQListener("LTC", self.ltc_endpoint, self.on_ltc_block)
            self._tasks.append(asyncio.create_task(self.ltc_listener.start()))
            self.logger.info(f"Started LTC ZMQ listener: {self.ltc_endpoint}")

        # Start MEWC listener if endpoint provided
        if self.mewc_endpoint and self.on_mewc_block:
            self.mewc_listener = ZMQListener(
                "MEWC", self.mewc_endpoint, self.on_mewc_block
            )
            self._tasks.append(asyncio.create_task(self.mewc_listener.start()))
            self.logger.info(f"Started MEWC ZMQ listener: {self.mewc_endpoint}")

    async def _listen_loop(self):
        """Main listening loop for ZMQ messages"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self._running:
            try:
                # Receive multipart message: [topic, data, sequence]
                parts = await self.socket.recv_multipart()

                if len(parts) >= 2:
                    topic = parts[0]
                    block_hash = parts[1]
                    sequence = parts[2] if len(parts) > 2 else b""

                    if topic == b"hashblock":
                        block_hash_hex = block_hash.hex()
                        seq_num = int.from_bytes(sequence, "little") if sequence else 0

                        self.logger.info(
                            f"New {self.name} block received: {block_hash_hex} (seq: {seq_num})"
                        )

                        # Reset error counter on successful message
                        consecutive_errors = 0

                        # Trigger callback asynchronously
                        try:
                            await self.on_block_callback(block_hash_hex)
                        except Exception as callback_error:
                            self.logger.error(
                                f"Error in {self.name} block callback: {callback_error}"
                            )
                    else:
                        self.logger.debug(
                            f"Ignoring {self.name} ZMQ message with topic: {topic}"
                        )
                else:
                    self.logger.warning(f"Received malformed {self.name} ZMQ message")

            except zmq.Again:
                # Timeout - this is normal, just continue
                continue

            except zmq.ZMQError as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(
                        f"{self.name} ZMQ listener: Too many consecutive errors ({consecutive_errors}), stopping"
                    )
                    break
                else:
                    self.logger.warning(
                        f"{self.name} ZMQ error (attempt {consecutive_errors}/{max_consecutive_errors}): {e}"
                    )
                    await asyncio.sleep(
                        min(consecutive_errors * 0.5, 5.0)
                    )  # Exponential backoff

            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(
                        f"{self.name} ZMQ listener: Unexpected error, stopping: {e}"
                    )
                    break
                else:
                    self.logger.error(
                        f"{self.name} ZMQ unexpected error (attempt {consecutive_errors}/{max_consecutive_errors}): {e}"
                    )
                    await asyncio.sleep(min(consecutive_errors, 5.0))

        self.logger.info(f"{self.name} ZMQ listening loop ended")

    async def stop(self):
        """Stop both ZMQ listeners"""
        self.logger.info("Stopping dual ZMQ listeners...")

        # Stop LTC listener
        if self.ltc_listener:
            await self.ltc_listener.stop()

        # Stop MEWC listener
        if self.mewc_listener:
            await self.mewc_listener.stop()

    @property
    def is_running(self) -> bool:
        """Check if the listener is currently running"""
        return self._running and self._task and not self._task.done()

    def __repr__(self):
        return f"ZMQListener(name='{self.name}', endpoint='{self.zmq_endpoint}', running={self._running})"


class TripleZMQListener:
    """
    Manages LTC, DOGE, and MEWC ZMQ listeners for multi-chain mining.

    Coordinates listening to parent chain (LTC) and auxiliary chains (DOGE, MEWC)
    block notifications for optimal AuxPoW mining efficiency.
    """

    def __init__(
        self,
        ltc_endpoint: Optional[str],
        mewc_endpoint: Optional[str],
        doge_endpoint: Optional[str],
        on_ltc_block: Optional[Callable],
        on_mewc_block: Optional[Callable],
        on_doge_block: Optional[Callable],
    ):
        """
        Initialize triple ZMQ listener.

        Args:
            ltc_endpoint: LTC ZMQ endpoint URL (None to disable LTC listening)
            mewc_endpoint: MEWC ZMQ endpoint URL (None to disable MEWC listening)
            doge_endpoint: DOGE ZMQ endpoint URL (None to disable DOGE listening)
            on_ltc_block: Callback for LTC block notifications
            on_mewc_block: Callback for MEWC block notifications
            on_doge_block: Callback for DOGE block notifications
        """
        self.ltc_listener = None
        self.mewc_listener = None
        self.doge_listener = None
        self.logger = logging.getLogger("TripleZMQ")

        # Create listeners if endpoints are provided
        if ltc_endpoint and on_ltc_block:
            self.ltc_listener = ZMQListener("LTC", ltc_endpoint, on_ltc_block)

        if mewc_endpoint and on_mewc_block:
            self.mewc_listener = ZMQListener("MEWC", mewc_endpoint, on_mewc_block)

        if doge_endpoint and on_doge_block:
            self.doge_listener = ZMQListener("DOGE", doge_endpoint, on_doge_block)

        if not self.ltc_listener and not self.mewc_listener and not self.doge_listener:
            self.logger.warning("No ZMQ listeners configured")

    async def start(self):
        """Start all listeners concurrently"""
        tasks = []

        if self.ltc_listener:
            self.logger.info("Starting LTC ZMQ listener...")
            tasks.append(asyncio.create_task(self.ltc_listener.start()))

        if self.mewc_listener:
            self.logger.info("Starting MEWC ZMQ listener...")
            tasks.append(asyncio.create_task(self.mewc_listener.start()))

        if self.doge_listener:
            self.logger.info("Starting DOGE ZMQ listener...")
            tasks.append(asyncio.create_task(self.doge_listener.start()))

        if tasks:
            self.logger.info(f"Starting {len(tasks)} ZMQ listener(s)...")
            # Run both listeners concurrently, but handle exceptions independently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions that occurred
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    if i == 0 and self.ltc_listener:
                        listener_name = "LTC"
                    elif i == 1 and self.mewc_listener:
                        listener_name = "MEWC"
                    elif i == 2 and self.doge_listener:
                        listener_name = "DOGE"
                    else:
                        listener_name = "Unknown"
                    self.logger.error(f"{listener_name} ZMQ listener failed: {result}")
        else:
            self.logger.warning("No ZMQ listeners to start")

    async def stop(self):
        """Stop all listeners"""
        tasks = []

        if self.ltc_listener:
            tasks.append(asyncio.create_task(self.ltc_listener.stop()))

        if self.mewc_listener:
            tasks.append(asyncio.create_task(self.mewc_listener.stop()))

        if self.doge_listener:
            tasks.append(asyncio.create_task(self.doge_listener.stop()))

        if tasks:
            self.logger.info("Stopping ZMQ listeners...")
            await asyncio.gather(*tasks, return_exceptions=True)
            self.logger.info("All ZMQ listeners stopped")

    @property
    def is_running(self) -> bool:
        """Check if any listener is currently running"""
        ltc_running = self.ltc_listener.is_running if self.ltc_listener else False
        mewc_running = self.mewc_listener.is_running if self.mewc_listener else False
        doge_running = self.doge_listener.is_running if self.doge_listener else False
        return ltc_running or mewc_running or doge_running

    def get_status(self) -> dict:
        """Get status of all listeners"""
        return {
            "ltc": {
                "configured": self.ltc_listener is not None,
                "running": self.ltc_listener.is_running if self.ltc_listener else False,
                "endpoint": (
                    self.ltc_listener.zmq_endpoint if self.ltc_listener else None
                ),
            },
            "mewc": {
                "configured": self.mewc_listener is not None,
                "running": (
                    self.mewc_listener.is_running if self.mewc_listener else False
                ),
                "endpoint": (
                    self.mewc_listener.zmq_endpoint if self.mewc_listener else None
                ),
            },
            "doge": {
                "configured": self.doge_listener is not None,
                "running": (
                    self.doge_listener.is_running if self.doge_listener else False
                ),
                "endpoint": (
                    self.doge_listener.zmq_endpoint if self.doge_listener else None
                ),
            },
        }

    def __repr__(self):
        status = self.get_status()
        return f"TripleZMQListener(ltc_running={status['ltc']['running']}, mewc_running={status['mewc']['running']}, doge_running={status['doge']['running']})"
