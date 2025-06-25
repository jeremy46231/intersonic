from typing import TypedDict, Optional, Any, NotRequired

# Gemini 2.5 Pro helped generate this file based on an example `tailscale status --json` output
# Not fully accurate, but good enough for VSCode type hints :pf:


class BaseNode(TypedDict):
    """A base interface for common properties of all nodes."""

    ID: str
    PublicKey: str
    HostName: str
    DNSName: str
    OS: str
    UserID: int
    TailscaleIPs: list[str]
    AllowedIPs: list[str]
    CurAddr: str
    Relay: str
    RxBytes: int
    TxBytes: int
    Created: str  # ISO 8601 Date
    LastWrite: str  # ISO 8601 Date
    LastSeen: str  # ISO 8601 Date
    LastHandshake: str  # ISO 8601 Date
    Online: bool
    ExitNode: bool
    ExitNodeOption: bool
    Active: bool
    TaildropTarget: int
    NoFileSharingReason: str
    InNetworkMap: bool
    InMagicSock: bool
    InEngine: bool
    KeyExpiry: NotRequired[str]  # This key is not present on all nodes


class SelfNode(BaseNode):
    """Represents the local device's ("Self") specific node information."""

    Addrs: list[str]
    PeerAPIURL: list[str]
    Capabilities: list[str]
    # Note: The JSON keys with URLs/colons need to be handled during parsing
    # or you can use a library like Pydantic which supports field aliasing.
    # For TypedDict, we'll assume the data is transformed or live with a more
    # generic CapMap type if keys are not valid Python identifiers.
    CapMap: dict[str, Any]


class PeerNode(BaseNode):
    """Represents a peer device in the Tailscale network."""

    Addrs: Optional[list[str]]
    PeerAPIURL: Optional[list[str]]
    Tags: NotRequired[list[str]]
    PrimaryRoutes: NotRequired[list[str]]
    sshHostKeys: NotRequired[list[str]]
    CapMap: NotRequired[dict[str, Any]]
    ShareeNode: NotRequired[bool]
    AltSharerUserID: NotRequired[int]


class UserProfile(TypedDict):
    """Represents a user profile in the tailnet."""

    ID: int
    LoginName: str
    DisplayName: str
    ProfilePicURL: NotRequired[str]


class CurrentTailnet(TypedDict):
    """Represents the current tailnet information."""

    Name: str
    MagicDNSSuffix: str
    MagicDNSEnabled: bool


class ClientVersion(TypedDict):
    """Represents the client version status."""

    RunningLatest: bool


class TailscaleStatus(TypedDict):
    """The root interface for the Tailscale status object."""

    Version: str
    TUN: bool
    BackendState: str
    HaveNodeKey: bool
    AuthURL: str
    TailscaleIPs: list[str]
    Self: SelfNode
    Health: list[Any]
    MagicDNSSuffix: str
    CurrentTailnet: CurrentTailnet
    CertDomains: list[str]
    # The JSON keys are node keys, so the keys are strings
    Peer: dict[str, PeerNode]
    # The JSON keys are user IDs as strings
    User: dict[str, UserProfile]
    ClientVersion: ClientVersion
