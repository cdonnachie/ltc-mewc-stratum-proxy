from dataclasses import dataclass
import os


@dataclass
class Settings:
    # Initialize with None to force reading from environment in __post_init__
    ip: str = "0.0.0.0"
    port: int = 0
    rpcip: str = ""
    rpcport: int = 0
    rpcuser: str = ""
    rpcpass: str = ""
    aux_rpcip: str = ""
    aux_rpcport: int = 0
    aux_rpcuser: str = ""
    aux_rpcpass: str = ""
    aux_address: str = ""
    proxy_signature: str = ""
    use_easier_target: bool = False
    testnet: bool = False
    jobs: bool = False
    verbose: bool = False
    debug_shares: bool = False
    enable_zmq: bool = False
    ltc_zmq_endpoint: str = ""
    mewc_zmq_endpoint: str = ""
    share_difficulty_divisor: float = 1000.0

    def __post_init__(self):
        """Load settings from environment variables at instance creation time"""
        self.port = int(os.getenv("STRATUM_PORT", "54321"))
        self.rpcip = os.getenv("LTC_RPC_HOST", os.getenv("LTC_RPC_IP", "litecoin"))
        self.rpcport = int(os.getenv("LTC_RPC_PORT", "9332"))
        self.rpcuser = os.getenv("LTC_RPC_USER", "")
        self.rpcpass = os.getenv("LTC_RPC_PASS", "")
        self.aux_rpcip = os.getenv(
            "MEWC_RPC_HOST", os.getenv("MEWC_RPC_IP", "meowcoin")
        )
        self.aux_rpcport = int(os.getenv("MEWC_RPC_PORT", "8766"))
        self.aux_rpcuser = os.getenv("MEWC_RPC_USER", "")
        self.aux_rpcpass = os.getenv("MEWC_RPC_PASS", "")
        self.aux_address = os.getenv("MEWC_WALLET_ADDRESS", "")
        self.proxy_signature = os.getenv("PROXY_SIGNATURE", "/ltc-mewc-stratum-proxy/")
        self.use_easier_target = (
            os.getenv("USE_EASIER_TARGET", "true").lower() == "true"
        )
        self.testnet = os.getenv("TESTNET", "false").lower() == "true"
        self.jobs = os.getenv("SHOW_JOBS", "false").lower() == "true"
        self.verbose = os.getenv("VERBOSE", "false").lower() == "true"
        self.debug_shares = os.getenv("DEBUG_SHARES", "false").lower() == "true"
        # ZMQ Configuration - read at instance creation time
        self.enable_zmq = os.getenv("ENABLE_ZMQ", "true").lower() == "true"
        self.ltc_zmq_endpoint = os.getenv("LTC_ZMQ_ENDPOINT", "tcp://litecoin:28332")
        self.mewc_zmq_endpoint = os.getenv("MEWC_ZMQ_ENDPOINT", "tcp://meowcoin:28433")
        # Share difficulty divisor: share_diff = network_diff / divisor
        # Higher value = easier shares = more frequent submissions
        # 1.0 = only blocks, 1000.0 = balanced, 10000.0 = very frequent
        self.share_difficulty_divisor = float(
            os.getenv("SHARE_DIFFICULTY_DIVISOR", "1000.0")
        )

    @property
    def node_url(self) -> str:
        return f"http://{self.rpcuser}:{self.rpcpass}@{self.rpcip}:{self.rpcport}"

    @property
    def aux_url(self) -> str | None:
        if (
            self.aux_rpcuser
            and self.aux_rpcpass
            and self.aux_rpcip
            and self.aux_rpcport
        ):
            return f"http://{self.aux_rpcuser}:{self.aux_rpcpass}@{self.aux_rpcip}:{self.aux_rpcport}"
        return None
