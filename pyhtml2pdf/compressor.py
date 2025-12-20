import logging
import os
import platform
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Literal, Union

from .utils import _pdf_has_suspicious_content

MAX_BYTES = 25 * 1024 * 1024

logger = logging.getLogger(__name__)


def compress(
    source: str | os.PathLike | _TemporaryFileWrapper,
    target: str | os.PathLike,
    power: int = 0,
    ghostscript_command: Union[Literal["gs", "gswin64c", "gswin32c"], None] = None,
    max_pdf_size: int = MAX_BYTES,
    timeout: int = 10,
    force_process: bool = False,
) -> None:
    """

    :param source: Source PDF file
    :param target: Target location to save the compressed PDF
    :param power: Power of the compression. Default value is 0. This can be
                    0: default,
                    1: prepress,
                    2: printer,
                    3: ebook,
                    4: screen
    :param ghostscript_command: The name of the ghostscript executable. If set to the default value None, is attempted
                                to be inferred from the OS.
                                If the OS is not Windows, "gs" is used as executable name.
                                If the OS is Windows, and it is a 64-bit version, "gswin64c" is used. If it is a 32-bit
                                version, "gswin32c" is used.
    :param max_pdf_size: Maximum allowed size for the PDF in bytes. Default is 25 MB.
    :param timeout: Timeout in seconds
    :param force_process: Whether to process even if suspicious content is found (Be extra careful with this setting).
    """
    quality = {0: "/default", 1: "/prepress", 2: "/printer", 3: "/ebook", 4: "/screen"}

    if ghostscript_command is None:
        if platform.system() == "Windows":
            if platform.machine().endswith("64"):
                ghostscript_command = "gswin64c"
            else:
                ghostscript_command = "gswin32c"
        else:
            ghostscript_command = "gs"

    if isinstance(source, _TemporaryFileWrapper):
        source = source.name

    source = Path(source)
    target = Path(target)

    if not source.is_file():
        raise FileNotFoundError("Source file does not exist")

    if source.suffix.lower() != ".pdf":
        raise ValueError("Source file is not a PDF")

    issues = _pdf_has_suspicious_content(source, max_pdf_size)

    if issues:
        logger.warning(
            "Warning: The PDF file has been flagged for suspicious content.\n\n- %s\n\nProcessing has been skipped to avoid potential security risks.\n\n"
            "If you believe this is an error, you can set force_process=True to override this behavior. Proceed with caution!\n",
            "\n- ".join(issues),
        )

        if not force_process:
            logger.error(
                "PDF file flagged for suspicious content. Process aborted.\n\n"
            )
            raise RuntimeError(
                "PDF file flagged for suspicious content. Process aborted."
            )

    try:
        subprocess.call(
            [
                ghostscript_command,
                "-dSAFER",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS={}".format(quality[power]),
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-sOutputFile={}".format(target.as_posix()),
                source.as_posix(),
            ],
            shell=platform.system() == "Windows",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error(
            "PDF processing took too long (DoS protection triggered). If you believe this is an error, try increasing the timeout parameter."
        )

        raise TimeoutError


def _compress(
    result: bytes,
    target: str | os.PathLike,
    power: int,
    timeout: int,
    ghostscript_command: Union[Literal["gs", "gswin64c", "gswin32c"], None] = None,
):
    with NamedTemporaryFile(
        suffix=".pdf", delete=platform.system() != "Windows"
    ) as tmp_file:
        tmp_file.write(result)

        # Ensure minimum timeout of 20 seconds for compression when call from converter.py
        _timeout: int = max(timeout, 20)

        compress(
            source=tmp_file,
            target=target,
            power=power,
            ghostscript_command=ghostscript_command,
            max_pdf_size=Path(tmp_file.name).stat().st_size + 1_000_000,
            timeout=_timeout,
        )
