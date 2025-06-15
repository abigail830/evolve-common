# 测试文件说明

本目录包含Evolve Common项目的测试文件。

## 测试脚本

### 1. 文档处理测试

#### 命令行测试工具 (`test_docling_conversion.py`)

这个脚本提供了一个简单的命令行工具，用于测试文档处理服务的转换功能。

**用法:**

```bash
# 基本用法
python ./tests/test_docling_conversion.py 文档路径.pdf

# 指定输出目录
python ./tests/test_docling_conversion.py 文档路径.pdf --output-dir /path/to/output
```

**参数:**
- `文档路径.pdf`: 要转换的PDF文档的路径
- `--output-dir`: (可选) 输出目录，默认为 `./test_output`

**功能:**
- 将指定的PDF文档转换为HTML格式
- 提取并保存文档中的图片资源
- 在HTML中正确引用这些资源
- 完成后尝试打开生成的HTML文件

#### PDF转HTML测试工具 (`test_pdf_conversion.py`)

这个脚本专门用于测试PDF转HTML并保存图片的功能，提供了更详细的日志和图片处理信息。

**用法:**

```bash
# 基本用法
python ./tests/test_pdf_conversion.py 文档路径.pdf

# 指定输出目录
python ./tests/test_pdf_conversion.py 文档路径.pdf --output-dir /path/to/output
```

**参数:**
- `文档路径.pdf`: 要转换的PDF文档的路径
- `--output-dir`: (可选) 输出目录，默认为 `./test_output`

**功能:**
- 将PDF文档转换为HTML格式
- 从文档中提取图片并保存到资源目录
- 处理HTML中的图片引用，包括base64编码的图片
- 处理CSS中的背景图片
- 提供详细的日志信息，便于调试
- 完成后显示资源目录中的文件列表并尝试打开生成的HTML文件

#### Word文档转HTML测试工具 (`test_docx_conversion.py`)

这个脚本专门用于测试Word文档转HTML并保存图片的功能，能够直接从Word文档中提取图片。

**用法:**

```bash
# 基本用法
python ./tests/test_docx_conversion.py 文档路径.docx

# 指定输出目录
python ./tests/test_docx_conversion.py 文档路径.docx --output-dir /path/to/output
```

**参数:**
- `文档路径.docx`: 要转换的Word文档路径(.docx或.doc)
- `--output-dir`: (可选) 输出目录，默认为 `./test_output`

**功能:**
- 首先测试直接从Word文档提取图片的功能
- 显示提取的图片信息，包括ID、路径和大小
- 然后测试完整的文档转HTML功能
- 检查资源目录内容，显示所有提取的图片
- 完成后尝试打开生成的HTML文件

#### 单元测试 (`test_document_processing.py`)

这个脚本包含用于自动化测试文档处理服务的单元测试。

**运行测试:**

```bash
# 运行所有测试
python -m unittest tests/test_document_processing.py

# 运行特定测试
python -m unittest tests.test_document_processing.TestDocumentProcessing.test_supported_formats
```

**测试用例:**
- `test_convert_file_with_sample_pdf`: 测试使用样本PDF文件进行转换
- `test_supported_formats`: 测试支持的文件格式检测

## 测试样本文件

测试样本文件应放置在 `tests/fixtures/` 目录下。

**推荐的测试文件:**
- `sample.pdf`: 一个包含文本和图片的PDF文件
- `sample.docx`: 一个包含文本和图片的Word文档
- `sample.pptx`: 一个包含文本和图片的PowerPoint演示文稿

如果没有这些样本文件，部分测试可能会被跳过。

## 测试文件结构

```
tests/
├── __init__.py
├── README.md
├── fixtures/                 # 测试用的样本文件
│   └── sample.pdf            # 用于测试的样本PDF文件
├── test_docling_conversion.py # 命令行测试工具
└── test_document_processing.py # 单元测试
```

## 添加测试文件

要添加样本PDF文件用于测试，请将文件放在 `tests/fixtures/` 目录下，并命名为 `sample.pdf`。 