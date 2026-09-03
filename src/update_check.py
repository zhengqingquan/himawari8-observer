"""检查 GitHub Releases 是否有新版本。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto

import requests

from src.metadata.soft_info import (
    GITHUB_API_LATEST,
    PROGRAM_NAME,
    SOFTWARE_VERSION,
)

_REQUEST_TIMEOUT_SEC = 10


class UpdateStatus(Enum):
    """检查更新结果状态。"""

    UP_TO_DATE = auto()
    UPDATE_AVAILABLE = auto()
    FAILED = auto()


@dataclass(frozen=True)
class UpdateCheckResult:
    """检查更新结果。

    Attributes:
        status: 是否最新 / 有更新 / 失败。
        current_version: 本地版本字符串。
        latest_version: 远端最新 tag；失败时可为 ``None``。
    """

    status: UpdateStatus
    current_version: str
    latest_version: str | None = None


def normalize_version(version: str) -> tuple[int, ...]:
    """去掉前导 ``v``/``V`` 后按 ``.`` 拆成整数元组。

    Args:
        version: 如 ``v1.3.1`` 或 ``1.3.1``。

    Returns:
        版本分量元组。

    Raises:
        ValueError: 无法解析为非空整数分量时。
    """
    text = version.strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    if not text:
        raise ValueError(f"empty version: {version!r}")
    parts = text.split(".")
    try:
        numbers = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"invalid version: {version!r}") from exc
    if not numbers:
        raise ValueError(f"invalid version: {version!r}")
    return numbers


def compare_versions(current: str, latest: str) -> int:
    """比较两个版本字符串。

    Args:
        current: 本地版本。
        latest: 远端版本。

    Returns:
        ``-1`` 本地落后，``0`` 相同，``1`` 本地更新。
    """
    current_parts = normalize_version(current)
    latest_parts = normalize_version(latest)
    length = max(len(current_parts), len(latest_parts))
    padded_current = current_parts + (0,) * (length - len(current_parts))
    padded_latest = latest_parts + (0,) * (length - len(latest_parts))
    if padded_current < padded_latest:
        return -1
    if padded_current > padded_latest:
        return 1
    return 0


def fetch_latest_release_tag(
    session: requests.Session | None = None,
) -> str:
    """从 GitHub Releases API 读取最新 release 的 ``tag_name``。

    Args:
        session: 可选可复用会话；未提供时使用临时 ``GET``。

    Returns:
        最新 tag 字符串。

    Raises:
        requests.RequestException: 网络或 HTTP 错误。
        ValueError: 响应无法解析出 ``tag_name``。
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{PROGRAM_NAME}/{SOFTWARE_VERSION}",
    }
    client = session or requests
    response = client.get(
        GITHUB_API_LATEST,
        headers=headers,
        timeout=_REQUEST_TIMEOUT_SEC,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("latest release response is not an object")
    tag_name = payload.get("tag_name")
    if not isinstance(tag_name, str) or not tag_name.strip():
        raise ValueError("latest release missing tag_name")
    return tag_name.strip()


def check_for_update(
    current_version: str = SOFTWARE_VERSION,
    session: requests.Session | None = None,
) -> UpdateCheckResult:
    """检查本地版本相对 GitHub 最新 release 的关系。

    Args:
        current_version: 本地版本，默认 ``SOFTWARE_VERSION``。
        session: 可选可复用会话。

    Returns:
        结构化检查结果；网络/解析失败时 ``status`` 为 ``FAILED``。
    """
    try:
        latest = fetch_latest_release_tag(session=session)
        cmp = compare_versions(current_version, latest)
    except (OSError, ValueError, requests.RequestException):
        logging.exception("Failed to check for updates")
        return UpdateCheckResult(
            status=UpdateStatus.FAILED,
            current_version=current_version,
        )

    if cmp < 0:
        status = UpdateStatus.UPDATE_AVAILABLE
    else:
        status = UpdateStatus.UP_TO_DATE
    return UpdateCheckResult(
        status=status,
        current_version=current_version,
        latest_version=latest,
    )
