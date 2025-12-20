import os
import platform
import subprocess
import pikepdf
from typing import Union, Literal
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper

MAX_PDF_SIZE_MB = 25
MAX_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024


def __accept_pdf(
    path: str | Path,
    max_pdf_size: int
) -> bool:
    path = Path(path)

    # Basic size validation won't accept files that are too large or empty
    size = path.stat().st_size
    if size <= 0 or size > max_pdf_size:
        raise ValueError(
            f'Input PDF file size is larger than the maximum allowed size of {MAX_PDF_SIZE_MB} MB. Adjust the max_pdf_size parameter to increase the limit.')

    # Basic header validation using magic bytes check
    with path.open('rb') as f:
        if f.read(5) != b'%PDF-':
            raise ValueError('Input file failed PDF magic bytes validation.')

    # Structural validation
    try:
        with pikepdf.open(path) as pdf:
            if len(pdf.pages) <= 0:
                raise ValueError('Input PDF file has no pages.')
    except Exception as e:
        raise ValueError(f'Input file failed PDF structural validation due to: {str(e)}')

    return True


def compress(
    source: str | os.PathLike | _TemporaryFileWrapper,
    target: str | os.PathLike,
    power: int = 0,
    ghostscript_command: Union[Literal['gs', 'gswin64c', 'gswin32c'], None] = None,
    max_pdf_size: int = MAX_BYTES
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
    """
    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    if ghostscript_command is None:
        if platform.system() == 'Windows':
            if platform.machine().endswith('64'):
                ghostscript_command = 'gswin64c'
            else:
                ghostscript_command = 'gswin32c'
        else:
            ghostscript_command = 'gs'

    if isinstance(source, _TemporaryFileWrapper):
        source = source.name

    source = Path(source)
    target = Path(target)

    if not source.is_file():
        raise FileNotFoundError('invalid path for input PDF file')

    if source.suffix != '.pdf':
        raise ValueError('Input file must be a .pdf file')

    if __accept_pdf(source, max_pdf_size):

        subprocess.call([
            ghostscript_command,
            '-dSAFER', '-dBATCH', '-dNOPAUSE',
            '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS={}'.format(quality[power]),
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-sOutputFile={}'.format(target.as_posix()),
            source.as_posix()
        ], shell=platform.system() == 'Windows')


def _compress(result: bytes,
              target: str | os.PathLike,
              power: int,
              ghostscript_command: Union[Literal['gs', 'gswin64c', 'gswin32c'], None] = None):
    with NamedTemporaryFile(suffix='.pdf', delete=platform.system() != 'Windows') as tmp_file:
        tmp_file.write(result)

        compress(tmp_file, target, power, ghostscript_command)
