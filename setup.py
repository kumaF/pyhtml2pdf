import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyhtml2pdf", # Replace with your own username
    version="0.0.9",
    author="Kumara Fernando",
    author_email="mklmfernando@gmail.com",
    description="Simple python wrapper to convert HTML to PDF with headless Chrome via selenium.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kumaF/pyhtml2pdf",
    packages=setuptools.find_packages(),
    install_requires=[            # I get to this in a second
          'selenium',
          'webdriver-manager',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)