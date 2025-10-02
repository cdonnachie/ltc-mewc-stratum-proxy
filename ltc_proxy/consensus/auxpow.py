from dataclasses import dataclass
from typing import Optional
from ..utils.hashers import dsha256
from .targets import bits_to_target, normalize_be_hex
import time, json, random

BACKOFF_INITIAL = 2
BACKOFF_MAX = 300
LOG_COALESCE = 10


@dataclass
class AuxJob:
    symbol: str
    url: str
    aux_hash: str
    target: Optional[str] = None
    chain_id: Optional[int] = None
    height: Optional[int] = None


def process_aux_target(target_hex: str) -> str:
    if not target_hex:
        return ""
    t = target_hex.lower().replace("0x", "").zfill(64)
    try:
        b = bytes.fromhex(t)
        be = b[::-1].hex()  # common LE->BE flip
        return normalize_be_hex(be)
    except Exception:
        return normalize_be_hex(t)


async def refresh_aux_job(
    state, session, aux_url: Optional[str], aux_address: str, force_update: bool = False
):
    if not aux_url or not aux_address or not aux_address.strip():
        state.aux_job = None
        state.aux_root = None
        state.mm_tree_size = 0
        state.aux_last_update = 0
        state.aux_backoff_secs = 0
        state.aux_next_try_at = 0
        state.aux_last_error = ""
        return

    now = int(time.time())

    if (
        not force_update
        and getattr(state, "aux_next_try_at", 0)
        and now < state.aux_next_try_at
    ):
        return

    if (
        not force_update
        and getattr(state, "aux_last_update", 0)
        and (now - state.aux_last_update) < 30
    ):
        return

    try:
        async with session.post(
            aux_url,
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "0",
                    "method": "createauxblock",
                    "params": [aux_address],
                }
            ),
        ) as resp:
            js = await resp.json()
    except Exception as e:
        _record_aux_error(state, f"MEWC RPC error: {e}")
        return

    if js.get("error"):
        err = js["error"]
        code = err.get("code")
        msg = str(err.get("message", "")).lower()
        if code == -10 or "download" in msg or "initial block download" in msg:
            _record_aux_error(state, f"MEWC not ready (IBD): {err}")
            return
        _record_aux_error(state, f"MEWC aux error: {err}")
        return

    # Success
    state.aux_backoff_secs = 0
    state.aux_next_try_at = 0
    state.aux_last_error = ""
    r = js["result"]

    bits_val = r.get("bits")
    if bits_val is not None:
        bits_hex = (
            f"{bits_val:08x}"
            if isinstance(bits_val, int)
            else str(bits_val).lstrip("0x")
        )
        t_int = bits_to_target(bits_hex)
        processed_target = normalize_be_hex(f"{t_int:x}")
    else:
        processed_target = process_aux_target(r.get("_target") or r.get("target") or "")

    state.aux_job = AuxJob(
        symbol="MEWC",
        url=aux_url,
        aux_hash=r["hash"],
        target=processed_target,
        chain_id=r.get("chainid"),
        height=r.get("height"),
    )
    state.aux_last_update = now

    # After updating MEWC job, rebuild the merged mining tree
    _rebuild_mm_tree(state)


def _record_aux_error(state, message: str):
    now = int(time.time())
    if (
        message != getattr(state, "aux_last_error", "")
        or (now - getattr(state, "aux_last_log_at", 0)) >= LOG_COALESCE
    ):
        state.logger.info(message)
        state.aux_last_error = message
        state.aux_last_log_at = now
    backoff = getattr(state, "aux_backoff_secs", 0)
    backoff = BACKOFF_INITIAL if backoff == 0 else min(backoff * 2, BACKOFF_MAX)
    jitter = int(backoff * 0.1)
    delay = backoff + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    delay = max(1, delay)
    state.aux_backoff_secs = backoff
    state.aux_next_try_at = now + delay
    state.aux_job = None
    state.aux_root = None
    state.mm_tree_size = 0


async def refresh_doge_job(
    state,
    session,
    doge_url: Optional[str],
    doge_address: str,
    force_update: bool = False,
):
    """Refresh Dogecoin auxiliary chain job"""
    if not doge_url or not doge_address or not doge_address.strip():
        state.doge_job = None
        state.doge_last_update = 0
        state.doge_backoff_secs = 0
        state.doge_next_try_at = 0
        state.doge_last_error = ""
        return

    now = int(time.time())

    if (
        not force_update
        and getattr(state, "doge_next_try_at", 0)
        and now < state.doge_next_try_at
    ):
        return

    if (
        not force_update
        and getattr(state, "doge_last_update", 0)
        and (now - state.doge_last_update) < 30
    ):
        return

    try:
        async with session.post(
            doge_url,
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "0",
                    "method": "createauxblock",
                    "params": [doge_address],
                }
            ),
        ) as resp:
            js = await resp.json()
    except Exception as e:
        _record_doge_error(state, f"DOGE RPC error: {e}")
        return

    if js.get("error"):
        err = js["error"]
        code = err.get("code")
        msg = str(err.get("message", "")).lower()
        if code == -10 or "download" in msg or "initial block download" in msg:
            _record_doge_error(state, f"DOGE not ready (IBD): {err}")
            return
        _record_doge_error(state, f"DOGE aux error: {err}")
        return

    # Success
    state.doge_backoff_secs = 0
    state.doge_next_try_at = 0
    state.doge_last_error = ""
    r = js["result"]

    bits_val = r.get("bits")
    if bits_val is not None:
        bits_hex = (
            f"{bits_val:08x}"
            if isinstance(bits_val, int)
            else str(bits_val).lstrip("0x")
        )
        t_int = bits_to_target(bits_hex)
        processed_target = normalize_be_hex(f"{t_int:x}")
    else:
        processed_target = process_aux_target(r.get("_target") or r.get("target") or "")

    state.doge_job = AuxJob(
        symbol="DOGE",
        url=doge_url,
        aux_hash=r["hash"],
        target=processed_target,
        chain_id=r.get("chainid"),
        height=r.get("height"),
    )
    state.doge_last_update = now

    # After updating DOGE job, rebuild the merged mining tree
    _rebuild_mm_tree(state)


def _record_doge_error(state, message: str):
    """Record error for Dogecoin auxiliary chain"""
    now = int(time.time())
    if (
        message != getattr(state, "doge_last_error", "")
        or (now - getattr(state, "doge_last_log_at", 0)) >= LOG_COALESCE
    ):
        state.logger.info(message)
        state.doge_last_error = message
        state.doge_last_log_at = now
    backoff = getattr(state, "doge_backoff_secs", 0)
    backoff = BACKOFF_INITIAL if backoff == 0 else min(backoff * 2, BACKOFF_MAX)
    jitter = int(backoff * 0.1)
    delay = backoff + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    delay = max(1, delay)
    state.doge_backoff_secs = backoff
    state.doge_next_try_at = now + delay
    state.doge_job = None


def _rebuild_mm_tree(state):
    """
    Rebuild the merged mining Merkle tree from available auxiliary chains.
    Supports 1, 2, or more auxiliary chains.
    """
    # Collect all active aux jobs with their chain IDs
    aux_chains = []

    if state.doge_job and state.doge_job.aux_hash:
        chain_id = (
            state.doge_job.chain_id if state.doge_job.chain_id is not None else 0x0062
        )  # Dogecoin default
        aux_chains.append((chain_id, state.doge_job))

    if state.aux_job and state.aux_job.aux_hash:
        chain_id = (
            state.aux_job.chain_id if state.aux_job.chain_id is not None else 0x0001
        )  # Meowcoin default
        aux_chains.append((chain_id, state.aux_job))

    if not aux_chains:
        # No auxiliary chains available
        state.aux_root = None
        state.mm_tree_size = 0
        state.mm_nonce = 0
        state.aux_chain_positions = {}
        return

    if len(aux_chains) == 1:
        # Single auxiliary chain - no tree needed
        chain_id, job = aux_chains[0]
        state.aux_root = bytes.fromhex(job.aux_hash)[::-1]  # Reverse to LE
        state.mm_tree_size = 1
        state.mm_nonce = int(time.time()) & 0xFFFFFFFF
        state.aux_chain_positions = {job.symbol: (0, [])}  # (index, merkle_branch)
        return

    # Multiple auxiliary chains - build Merkle tree
    # Sort by chain ID to ensure consistent ordering
    aux_chains.sort(key=lambda x: x[0])

    # Build list of hashes (in LE)
    hashes = [bytes.fromhex(job.aux_hash)[::-1] for chain_id, job in aux_chains]

    # Build Merkle tree
    tree = build_merkle_tree(hashes)
    root = tree[-1][0]  # Root is the last level, single element

    # Store positions and branches for each chain
    positions = {}
    for idx, (chain_id, job) in enumerate(aux_chains):
        branch = get_merkle_branch(tree, idx)
        positions[job.symbol] = (idx, branch)

    state.aux_root = root
    state.mm_tree_size = len(aux_chains)
    state.mm_nonce = int(time.time()) & 0xFFFFFFFF
    state.aux_chain_positions = positions


def build_merkle_tree(hashes: list) -> list:
    """
    Build a Merkle tree from a list of hashes.
    Returns a list of levels, where each level is a list of hashes.
    Level 0 is the leaves, and the last level contains only the root.
    """
    if not hashes:
        return []

    levels = [list(hashes)]

    while len(levels[-1]) > 1:
        current_level = levels[-1]
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]
            # If odd number of elements, duplicate the last one
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            parent = dsha256(left + right)
            next_level.append(parent)

        levels.append(next_level)

    return levels


def get_merkle_branch(tree: list, index: int) -> list:
    """
    Get the Merkle branch (proof) for a leaf at the given index.
    Returns a list of sibling hashes needed to verify the path to the root.
    """
    branch = []
    current_index = index

    # Iterate through levels (except the root level)
    for level in tree[:-1]:
        # Find the sibling index
        if current_index % 2 == 0:
            # We're a left child, sibling is to the right
            sibling_index = current_index + 1
        else:
            # We're a right child, sibling is to the left
            sibling_index = current_index - 1

        # Add sibling to branch if it exists
        if sibling_index < len(level):
            branch.append(level[sibling_index])
        else:
            # Odd number of nodes, duplicate our hash
            branch.append(level[current_index])

        # Move to parent index in next level
        current_index = current_index // 2

    return branch
