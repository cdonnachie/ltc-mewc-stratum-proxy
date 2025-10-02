import base58
import os
import json
import logging
import asyncio

from aiorpcx import (
    RPCSession,
    JSONRPCConnection,
    JSONRPCv1,
    Request,
    handler_invocation,
    RPCError,
)
from ..state.template import TemplateState
from ..utils.enc import bech32_decode
from ..consensus.merkle import fold_branch_index0
from ..consensus.header import build_header80_le
from ..utils.hashers import dsha256, scrypt_pow
from aiohttp import ClientSession
from ..consensus.targets import (
    target_to_diff1,
)

logger = logging.getLogger(__name__)
hashratedict = {}


class StratumSession(RPCSession):
    def __init__(
        self,
        state: TemplateState,
        testnet: bool,
        verbose: bool,
        node_url: str,
        aux_url: str | None,
        debug_shares: bool,
        share_difficulty_divisor: float,
        transport,
    ):
        connection = JSONRPCConnection(JSONRPCv1)
        super().__init__(transport, connection=connection)
        import logging

        self._state = state
        self._testnet = testnet
        self._verbose = verbose
        self._debug_shares = debug_shares
        self._share_difficulty_divisor = share_difficulty_divisor
        self._client_addr = transport._remote_address
        self._transport = transport
        self._node_url = node_url
        self._aux_url = aux_url
        self._extranonce1 = None
        self.logger = logging.getLogger("Stratum-Proxy")
        self._keepalive_task = None  # Keepalive task reference
        self._last_activity = None  # Track last activity time

        self.handlers = {
            "mining.subscribe": self.handle_subscribe,
            "mining.authorize": self.handle_authorize,
            "mining.submit": self.handle_submit,
            "mining.configure": self.handle_configure,
            "eth_submitHashrate": self.handle_eth_submitHashrate,
        }

    async def handle_request(self, request):
        if isinstance(request, Request):
            handler = self.handlers.get(request.method, None)
            if not handler:
                return
        else:
            return
        return await handler_invocation(handler, request)()

    async def connection_lost(self):
        # Cancel keepalive task
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass

        try:
            wid = getattr(self, "_worker_id", None)
            if wid:
                from .session import hashratedict

                hashratedict.pop(wid, None)
        except Exception:
            pass

        self._state.new_sessions.discard(self)
        self._state.all_sessions.discard(self)

        try:
            await super().connection_lost()
        except TypeError:
            try:
                super().connection_lost()
            except Exception:
                pass

    async def handle_subscribe(self, *args):
        if self not in self._state.all_sessions:
            self._state.new_sessions.add(self)
        self._state.bits_counter += 1
        subscription_id = f"subscription_{self._state.bits_counter}"
        self._extranonce1 = self._state.bits_counter.to_bytes(4, "big").hex()
        extranonce2_size = 4
        return [
            [
                ["mining.set_difficulty", subscription_id],
                ["mining.notify", subscription_id],
            ],
            self._extranonce1,
            extranonce2_size,
        ]

    async def handle_authorize(self, username: str, password: str):
        self._worker_id = username
        address = username.split(".")[0]
        pub_h160 = None
        try:
            if address.startswith("ltc1") or address.startswith("tltc1"):
                if address.startswith("tltc1") and not self._testnet:
                    raise RPCError(
                        20, f"Testnet address {address} not allowed on mainnet"
                    )
                if address.startswith("ltc1") and self._testnet:
                    raise RPCError(
                        20, f"Mainnet address {address} not allowed on testnet"
                    )
                hrp, wit = bech32_decode(address)
                if hrp is None or wit is None:
                    raise RPCError(20, f"Invalid Bech32 address: {address}")
                expected = "tltc" if self._testnet else "ltc"
                if hrp != expected:
                    raise RPCError(20, f"Wrong network for address {address}")
                if len(wit) == 20:
                    pub_h160 = wit
                else:
                    raise RPCError(20, "Unsupported witness program length")
            else:
                addr_decoded = base58.b58decode_check(address)
                # Litecoin: 48='L', 111='m'(testnet); also accept 5='3' for P2SH
                expected_versions = [111] if self._testnet else [48, 5]
                if addr_decoded[0] not in expected_versions:
                    raise RPCError(20, f"Invalid address version")
                pub_h160 = addr_decoded[1:]
        except RPCError:
            raise
        except Exception as e:
            raise RPCError(20, f"Address validation failed: {address} - {str(e)}")
        if not self._state.pub_h160:
            self._state.pub_h160 = pub_h160
            # Store whether this is a witness (bech32) or legacy (base58) address
            self._state.is_witness_address = address.startswith(("ltc1", "tltc1"))

        # Register this session now
        self._state.all_sessions.add(self)
        self._state.new_sessions.discard(self)

        # Start keepalive task
        if not self._keepalive_task or self._keepalive_task.done():
            loop = asyncio.get_event_loop()
            self._last_activity = loop.time()
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
            if self._verbose:
                self.logger.debug("Started keepalive task for %s", username)

        # If a job exists, send it right away
        job = self._state.current_job_params()
        if job:
            difficulty = (
                target_to_diff1(int(self._state.target, 16))
                / self._share_difficulty_divisor
            )
            self._share_difficulty = difficulty
            await self.send_notification("mining.set_difficulty", (difficulty,))
            await self.send_notification("mining.notify", job)
            self._last_activity = (
                asyncio.get_event_loop().time()
            )  # Reset activity timer
            return True

    async def handle_configure(self, extensions):
        return {}

    async def _keepalive_loop(self):
        """Send periodic keepalive messages to prevent miner disconnection"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # If no activity for 45 seconds, send a notification
                loop = asyncio.get_event_loop()
                if self._last_activity and (loop.time() - self._last_activity > 45):
                    # Send a difficulty notification (same value, just to keep connection alive)
                    difficulty = getattr(self, "_share_difficulty", 1.0)
                    await self.send_notification("mining.set_difficulty", (difficulty,))
                    self._last_activity = loop.time()
                    if self._verbose:
                        self.logger.debug(
                            "Sent keepalive to %s",
                            getattr(self, "_worker_id", "unknown"),
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Keepalive error: %s", e)
                break

    async def handle_submit(
        self,
        worker: str,
        job_id: str,
        extranonce2_hex: str,
        ntime_hex: str,
        nonce_hex: str,
    ):
        # Reset activity timer on any submission
        loop = asyncio.get_event_loop()
        self._last_activity = loop.time()

        state = self._state

        # Snapshot for consistent parent_block_hash calculation
        aux_job_snapshot = state.aux_job
        coinbase1_nowit_snapshot = state.coinbase1_nowit
        coinbase2_nowit_snapshot = state.coinbase2_nowit
        merkle_branches_snapshot = list(state.merkle_branches)
        version_snapshot = state.version
        prevHash_be_snapshot = state.prevHash_be
        bits_le_snapshot = state.bits_le

        if job_id != hex(state.job_counter)[2:]:
            self.logger.error("Miner submitted unknown/old job %s", job_id)
            return False

        if not (
            state.coinbase1
            and state.coinbase2
            and state.coinbase1_nowit
            and state.coinbase2_nowit
        ):
            self.logger.error("Coinbase parts not ready")
            return False

        en1 = bytes.fromhex(self._extranonce1 or "")
        en2 = bytes.fromhex(extranonce2_hex)

        coinbase_wit = state.coinbase1 + en1 + en2 + state.coinbase2
        coinbase_nowit = coinbase1_nowit_snapshot + en1 + en2 + coinbase2_nowit_snapshot
        coinbase_txid_le = dsha256(coinbase_nowit)

        merkle_root_le = fold_branch_index0(
            coinbase_txid_le, [bytes.fromhex(x) for x in merkle_branches_snapshot]
        )

        ntime_le = bytes.fromhex(ntime_hex)[::-1]
        nonce_le = bytes.fromhex(nonce_hex)[::-1]
        header80 = build_header80_le(
            version_snapshot,
            prevHash_be_snapshot,
            merkle_root_le,
            ntime_le,
            bits_le_snapshot,
            nonce_le,
        )

        parent_block_hash_for_auxpow = dsha256(header80)[::-1]

        # Calculate Scrypt PoW hash - used for validation by BOTH chains
        scrypt_digest_le = scrypt_pow(header80)
        hnum = int.from_bytes(scrypt_digest_le, "little")

        # Check LTC target
        ltc_target_int = int(state.ltc_original_target or state.target, 16)
        is_ltc_block = hnum <= ltc_target_int

        # Check MEWC target (if available)
        is_mewc_block = False
        if state.aux_job and state.aux_job.target:
            mewc_target_int = int(state.aux_job.target, 16)
            is_mewc_block = hnum <= mewc_target_int

        sent_diff = getattr(self, "_share_difficulty", 1.0) or 1.0
        DIFF1 = int(
            "00000000ffff0000000000000000000000000000000000000000000000000000", 16
        )
        share_diff = DIFF1 / max(1, hnum)

        # Accept share if it meets either target or the miner difficulty
        is_block = is_ltc_block or is_mewc_block
        if not is_block and (share_diff / sent_diff) < 0.99:
            if self._debug_shares:
                self.logger.error(
                    "Low difficulty share: shareDiff=%.18f minerDiff=%.18f",
                    share_diff,
                    sent_diff,
                )
            return False

        block_msg_parts = []
        if is_ltc_block:
            block_msg_parts.append("LTC BLOCK!")
        if is_mewc_block:
            block_msg_parts.append("MEWC BLOCK!")
        block_msg = f" ({', '.join(block_msg_parts)})" if block_msg_parts else ""

        if self._verbose or is_block:
            # Convert targets to difficulty values for better readability
            ltc_difficulty = target_to_diff1(ltc_target_int)
            mewc_difficulty = (
                target_to_diff1(mewc_target_int)
                if state.aux_job and state.aux_job.target
                else 0.0
            )

            self.logger.info(
                "Share accepted by %s - shareDiff=%.6f%s LTC diff: %.6f MEWC diff: %.6f",
                worker,
                share_diff,
                block_msg,
                ltc_difficulty,
                mewc_difficulty,
            )

        # Submit to appropriate blockchain(s)
        if is_ltc_block or is_mewc_block:
            import time

            # Show which hash meets which target
            if state.aux_job:
                ltc_meets = "✓" if is_ltc_block else "✗"
                mewc_meets = "✓" if is_mewc_block else "✗"
                self.logger.info(
                    "Block qualification - LTC: %s, MEWC: %s",
                    ltc_meets,
                    mewc_meets,
                )

            submit_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

            async with ClientSession() as http:
                # Submit to LTC if it meets LTC target
                if is_ltc_block:
                    tx_count = len(state.externalTxs) + 1
                    if tx_count < 0xFD:
                        tx_count_hex = tx_count.to_bytes(1, "little").hex()
                    elif tx_count <= 0xFFFF:
                        tx_count_hex = "fd" + tx_count.to_bytes(2, "little").hex()
                    elif tx_count <= 0xFFFFFFFF:
                        tx_count_hex = "fe" + tx_count.to_bytes(4, "little").hex()
                    else:
                        tx_count_hex = "ff" + tx_count.to_bytes(8, "little").hex()

                    coinbase_nowit_full = (
                        state.coinbase1_nowit + en1 + en2 + state.coinbase2_nowit
                    )

                    block_hex = (
                        header80.hex()
                        + tx_count_hex
                        + coinbase_nowit_full.hex()
                        + "".join(state.externalTxs)
                    )

                    from ..rpc.ltc import submitblock

                    state.logger.info("Submitting to LTC")
                    state.logger.debug("LTC submit block: %s", block_hex)

                    js = await submitblock(http, self._node_url, block_hex)

                    if not os.path.exists("./submit_history"):
                        os.mkdir("./submit_history")

                    with open(
                        f"./submit_history/LTC_{state.height}_{state.job_counter}.txt",
                        "w",
                    ) as f:
                        dump = f"=== LTC BLOCK SUBMISSION ===\n"
                        dump += f"Submission Time: {submit_time}\n"
                        dump += f"Worker: {worker}\n"
                        dump += f"Job ID: {job_id}\n"
                        dump += f"Block Height: {state.height}\n"
                        dump += f"Block Hash (dsha256): {parent_block_hash_for_auxpow.hex()}\n"
                        dump += f"Extranonce1: {self._extranonce1}\n"
                        dump += f"Extranonce2: {extranonce2_hex}\n"
                        dump += f"Ntime: {ntime_hex}\n"
                        dump += f"Nonce: {nonce_hex}\n"
                        dump += f"Coinbase hex: {coinbase_nowit_full.hex()}\n"
                        dump += f"Scrypt Hash: {scrypt_digest_le.hex()}\n"
                        dump += f"Hash Number: {hnum}\n"
                        dump += f"LTC Target: {ltc_target_int:064x}\n"
                        dump += (
                            f'Target Source: {getattr(state, "target_source", "LTC")}\n'
                        )
                        dump += f"Meets LTC Target: {is_ltc_block}\n"
                        dump += f"Share Difficulty: {share_diff:.18f}\n"
                        dump += f"Header Hash: {header80.hex()}\n"
                        dump += f"Block Hex Length: {len(block_hex)} chars\n"
                        dump += f"Transaction Count: {len(state.externalTxs) + 1}\n\n"
                        dump += f"RPC Response:\n{json.dumps(js, indent=2)}\n\n"
                        dump += f"Full State:\n{state.__repr__()}\n\n"
                        dump += f"Block Hex:\n{block_hex}"
                        f.write(dump)

                    if js.get("error"):
                        self.logger.error("LTC submit error: %s", js["error"])
                    else:
                        self.logger.info("LTC submit result: %s", js.get("result"))

                # Submit to MEWC if it meets MEWC target and aux is configured
                if is_mewc_block and self._aux_url and aux_job_snapshot:
                    try:
                        from ..consensus.auxpow import AuxJob

                        # Minimal auxpow blob (coinbase proof, no aux-branch for single leaf)
                        def ser_varint(n: int):
                            if n < 0xFD:
                                return n.to_bytes(1, "little")
                            if n <= 0xFFFF:
                                return b"\xfd" + n.to_bytes(2, "little")
                            if n <= 0xFFFFFFFF:
                                return b"\xfe" + n.to_bytes(4, "little")
                            return b"\xff" + n.to_bytes(8, "little")

                        # IMPORTANT: Use snapshots to ensure consistency with aux_job_snapshot
                        coinbase_nowit_full = (
                            coinbase1_nowit_snapshot
                            + en1
                            + en2
                            + coinbase2_nowit_snapshot
                        )

                        # Build coinbase proof (merkle branch from coinbase to block merkle root)
                        coinbase_proof = (
                            ser_varint(
                                len(state.coinbase_branch)
                            )  # Number of merkle steps
                            + b"".join(state.coinbase_branch)  # Merkle branch hashes
                            + state.coinbase_index.to_bytes(
                                4, "little"
                            )  # Coinbase index in block
                        )

                        # Build branch proof (merkle branch in aux chain tree)
                        branch_proof = ser_varint(
                            0
                        ) + (  # Number of aux chain branches (0)
                            0
                        ).to_bytes(
                            4, "little"
                        )  # Aux chain index (0)

                        auxpow_data = (
                            coinbase_nowit_full  # Parent coinbase tx
                            + parent_block_hash_for_auxpow  # Parent block hash (from Litecoin block being submitted)
                            + coinbase_proof  # Coinbase merkle proof
                            + branch_proof  # Aux chain merkle proof
                            + header80  # Parent block header (80 bytes)
                        )
                        auxpow_hex = auxpow_data.hex()
                        from ..rpc.mewc import submitauxblock

                        # Check if aux job is recent enough
                        import time

                        current_time = int(time.time())
                        aux_age = current_time - getattr(state, "aux_last_update", 0)

                        state.logger.info("Submitting to MEWC")

                        # Warn if aux job might be stale
                        if aux_age > 60:  # More than 1 minute old
                            state.logger.warning(
                                "MEWC aux job is %d seconds old, may be stale", aux_age
                            )

                        js = await submitauxblock(
                            http, self._aux_url, aux_job_snapshot.aux_hash, auxpow_hex
                        )

                        # Log MEWC submission history to file with detailed auxpow information
                        if not os.path.exists("./submit_history"):
                            os.mkdir("./submit_history")

                        # Use MEWC height from aux job if available, otherwise fall back to LTC height
                        mewc_height = getattr(aux_job_snapshot, "height", state.height)

                        with open(
                            f"./submit_history/MEWC_{mewc_height}_{state.job_counter}.txt",
                            "w",
                        ) as f:
                            dump = f"=== MEWC AUXPOW SUBMISSION ===\n"
                            dump += f"Submission Time: {submit_time}\n"
                            dump += f"Worker: {worker}\n"
                            dump += f"Job ID: {job_id}\n"
                            dump += f"LTC Block Height: {state.height}\n"
                            dump += f"LTC Block Hash (dsha256): {parent_block_hash_for_auxpow.hex()}\n"
                            dump += f"MEWC Block Height: {mewc_height}\n"
                            dump += f"MEWC Aux Hash: {aux_job_snapshot.aux_hash}\n"
                            dump += f'MEWC Chain ID: {getattr(aux_job_snapshot, "chain_id", "unknown")}\n'
                            dump += f"Extranonce1: {self._extranonce1}\n"
                            dump += f"Extranonce2: {extranonce2_hex}\n"
                            dump += f"Ntime: {ntime_hex}\n"
                            dump += f"Nonce: {nonce_hex}\n"
                            dump += f"Scrypt Hash: {scrypt_digest_le.hex()}\n"
                            dump += f"Hash Number: {hnum}\n"
                            dump += f'MEWC Target: {aux_job_snapshot.target if aux_job_snapshot.target else "unknown"}\n'
                            dump += f"Meets MEWC Target: {is_mewc_block}\n"
                            dump += f"Share Difficulty: {share_diff:.18f}\n"
                            dump += f"Parent Header: {header80.hex()}\n"
                            dump += f"Parent Block Hash (for AuxPoW): {parent_block_hash_for_auxpow.hex()}\n"
                            dump += f"Coinbase Branch Length: {len(state.coinbase_branch)}\n"
                            dump += f"AuxPoW Hex Length: {len(auxpow_hex)} chars\n\n"
                            dump += f"RPC Response:\n{json.dumps(js, indent=2)}\n\n"
                            dump += f"Full State:\n{state.__repr__()}\n\n"
                            dump += f"AuxPoW Hex:\n{auxpow_hex}\n\n"
                            dump += (
                                f"Non-Witness Coinbase:\n{coinbase_nowit_full.hex()}"
                            )
                            f.write(dump)

                        if js.get("error"):
                            error_code = js["error"].get("code", 0)
                            error_msg = js["error"].get("message", "unknown")

                            if error_code == -8:  # Block hash unknown
                                self.logger.warning(
                                    "MEWC submitauxblock: aux hash expired (age: %ds, hash: %s) - refreshing for next share",
                                    aux_age,
                                    aux_job_snapshot.aux_hash,
                                )
                                # Immediately refresh aux job to get a fresh hash
                                from ..consensus.auxpow import refresh_aux_job
                                from ..config import Settings

                                try:
                                    settings = Settings()
                                    await refresh_aux_job(
                                        state,
                                        http,
                                        self._aux_url,
                                        settings.aux_address,
                                        force_update=True,
                                    )
                                    self.logger.info(
                                        "MEWC aux job refreshed after stale submission"
                                    )
                                except Exception as refresh_error:
                                    self.logger.error(
                                        "Failed to refresh MEWC aux job: %s",
                                        refresh_error,
                                    )
                            else:
                                self.logger.error(
                                    "MEWC submitauxblock error (code %d): %s",
                                    error_code,
                                    error_msg,
                                )
                        else:
                            result = js.get("result")
                            if result:
                                self.logger.info(
                                    "✓ MEWC BLOCK ACCEPTED! Result: %s", result
                                )
                            else:
                                # Log detailed info about why the submission was rejected
                                self.logger.warning(
                                    "MEWC submitauxblock returned false (rejected)"
                                )
                                self.logger.warning(
                                    "  Submitted aux_hash: %s",
                                    aux_job_snapshot.aux_hash,
                                )
                                self.logger.warning(
                                    "  Aux job age: %ds (created at height %s)",
                                    aux_age,
                                    getattr(aux_job_snapshot, "height", "unknown"),
                                )
                                self.logger.warning("  Possible causes:")
                                self.logger.warning(
                                    "    - MEWC found a new block, invalidating this aux_hash"
                                )
                                self.logger.warning(
                                    "    - Parent block hash mismatch in AuxPoW"
                                )
                                self.logger.warning(
                                    "    - Coinbase doesn't contain the aux_hash commitment"
                                )
                    except Exception as e:
                        self.logger.error("MEWC submit failed: %s", e)
        return True

    async def handle_eth_submitHashrate(self, hashrate: str, clientid: str):
        try:
            rate = int(hashrate, 16)
            worker = str(self).strip(">").split()[3]
            from math import isfinite

            hashratedict[worker] = rate
            total = sum(hashratedict.values())
            self.logger.info(
                "Reported hashrate: %.2f Mh/s (total: %.2f Mh/s)",
                rate / 1_000_000,
                total / 1_000_000,
            )
        except Exception:
            pass
        return True
