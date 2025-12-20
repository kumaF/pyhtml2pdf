from pyhtml2pdf import converter

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Test PDF</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a test PDF generated from HTML content.</p>
</body>
</html>
"""

# Convert HTML content to PDF
pdf_path = "./output.pdf"
converter.convert(source=html_content, target=pdf_path, compress=True, power=2)
