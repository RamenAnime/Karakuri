"""Joint command bus: fixed binary frames with checksums at 1 kHz.

The frame layout works the same over CAN-FD hardware (MCP2518FD hats) or the
in-process mock transport the tests use, which is the point: the protocol is
proven on every machine, and the wire is an installation detail. Each frame
carries node id, sequence, position in centidegrees, velocity limit, flags,
and an XOR checksum; a corrupted frame decodes to None instead of a wrong
joint angle.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

_FMT = "<BHhhB"  # node, seq, pos_cdeg, vel_cdeg_s, flags
FRAME_SIZE = struct.calcsize(_FMT) + 1  # plus checksum byte

FLAG_ENABLE = 0x01
FLAG_BRAKE = 0x02
FLAG_SYNC = 0x80


@dataclass(frozen=True)
class JointFrame:
    node: int
    seq: int
    pos_deg: float
    vel_deg_s: float
    flags: int = FLAG_ENABLE


def _checksum(payload: bytes) -> int:
    x = 0
    for b in payload:
        x ^= b
    return x


def encode(frame: JointFrame) -> bytes:
    payload = struct.pack(
        _FMT,
        frame.node & 0xFF,
        frame.seq & 0xFFFF,
        int(round(frame.pos_deg * 100)),
        int(round(frame.vel_deg_s * 100)),
        frame.flags & 0xFF,
    )
    return payload + bytes([_checksum(payload)])


def decode(data: bytes) -> JointFrame | None:
    if len(data) != FRAME_SIZE or _checksum(data[:-1]) != data[-1]:
        return None
    node, seq, pos, vel, flags = struct.unpack(_FMT, data[:-1])
    return JointFrame(node=node, seq=seq, pos_deg=pos / 100.0, vel_deg_s=vel / 100.0, flags=flags)


@dataclass
class MockTransport:
    """In-process wire: what is sent is what arrives, unless tests corrupt it."""

    frames: list[bytes] = field(default_factory=list)

    def send(self, data: bytes) -> None:
        self.frames.append(data)

    def drain(self) -> list[bytes]:
        out, self.frames = self.frames, []
        return out


class JointBus:
    """Sequenced command stream for many joints plus a sync broadcast.

    ``sync`` is the frame every node latches on, which is how all joints
    apply the cycle's commands in the same microsecond-scale window instead
    of rippling down the chain.
    """

    def __init__(self, transport: MockTransport | None = None) -> None:
        self.transport = transport or MockTransport()
        self.seq = 0

    def command(self, node: int, pos_deg: float, vel_deg_s: float = 0.0, flags: int = FLAG_ENABLE) -> None:
        self.transport.send(encode(JointFrame(node, self.seq, pos_deg, vel_deg_s, flags)))

    def sync(self) -> None:
        self.transport.send(encode(JointFrame(0xFF, self.seq, 0.0, 0.0, FLAG_SYNC)))
        self.seq = (self.seq + 1) & 0xFFFF
