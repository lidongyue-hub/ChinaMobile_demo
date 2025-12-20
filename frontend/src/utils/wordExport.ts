/**
 * Word文档导出工具
 * 将Markdown格式的报告转换为Word文档
 */

import { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, AlignmentType } from 'docx'
// @ts-ignore - file-saver 没有类型定义
import { saveAs } from 'file-saver'

/**
 * 解析Markdown内容并转换为Word文档段落
 */
function parseMarkdownToParagraphs(markdown: string): (Paragraph | Table)[] {
  const elements: (Paragraph | Table)[] = []
  const lines = markdown.split('\n')
  
  let i = 0
  while (i < lines.length) {
    const line = lines[i].trim()
    
    // 跳过空行
    if (!line) {
      i++
      continue
    }
    
    // 处理表格
    if (line.startsWith('|')) {
      const table = parseTable(lines, i)
      if (table) {
        elements.push(table.table)
        i = table.nextIndex
        continue
      }
    }
    
    // 处理标题
    if (line.startsWith('# ')) {
      elements.push(new Paragraph({
        text: line.slice(2),
        heading: HeadingLevel.HEADING_1,
        spacing: { after: 200 }
      }))
    } else if (line.startsWith('## ')) {
      elements.push(new Paragraph({
        text: line.slice(3),
        heading: HeadingLevel.HEADING_2,
        spacing: { after: 180 }
      }))
    } else if (line.startsWith('### ')) {
      elements.push(new Paragraph({
        text: line.slice(4),
        heading: HeadingLevel.HEADING_3,
        spacing: { after: 160 }
      }))
    } else if (line.startsWith('#### ')) {
      elements.push(new Paragraph({
        text: line.slice(5),
        heading: HeadingLevel.HEADING_4,
        spacing: { after: 140 }
      }))
    } else if (line.startsWith('##### ')) {
      elements.push(new Paragraph({
        text: line.slice(6),
        heading: HeadingLevel.HEADING_5,
        spacing: { after: 120 }
      }))
    } else if (line.startsWith('###### ')) {
      elements.push(new Paragraph({
        text: line.slice(7),
        heading: HeadingLevel.HEADING_6,
        spacing: { after: 100 }
      }))
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      // 无序列表
      const listItems: string[] = []
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        listItems.push(lines[i].trim().slice(2))
        i++
      }
      listItems.forEach(item => {
        elements.push(new Paragraph({
          text: `• ${item}`,
          spacing: { after: 100 }
        }))
      })
      continue
    } else if (/^\d+\.\s/.test(line)) {
      // 有序列表
      const listItems: string[] = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ''))
        i++
      }
      listItems.forEach((item, idx) => {
        elements.push(new Paragraph({
          text: `${idx + 1}. ${item}`,
          spacing: { after: 100 }
        }))
      })
      continue
    } else if (line.startsWith('```')) {
      // 代码块
      const codeLines: string[] = []
      i++ // 跳过开始标记
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      if (codeLines.length > 0) {
        elements.push(new Paragraph({
          text: codeLines.join('\n'),
          spacing: { before: 200, after: 200 }
        }))
      }
    } else {
      // 普通段落
      const paragraph = parseInlineFormatting(line)
      if (paragraph) {
        elements.push(paragraph)
      }
    }
    
    i++
  }
  
  return elements
}

/**
 * 解析内联格式（粗体、斜体、代码等）
 */
function parseInlineFormatting(text: string): Paragraph {
  const runs: TextRun[] = []
  
  // 匹配粗体 **text** 或 __text__
  const boldRegex = /\*\*(.*?)\*\*|__(.*?)__/g
  // 匹配斜体 *text* 或 _text_
  const italicRegex = /(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.*?)(?<!_)_(?!_)/g
  // 匹配行内代码 `code`
  const codeRegex = /`([^`]+)`/g
  
  // 先处理代码（优先级最高）
  const parts: Array<{ text: string; type: 'normal' | 'bold' | 'italic' | 'code' }> = []
  let lastIndex = 0
  let match
  
  // 处理代码
  codeRegex.lastIndex = 0
  while ((match = codeRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ text: text.slice(lastIndex, match.index), type: 'normal' })
    }
    parts.push({ text: match[1], type: 'code' })
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), type: 'normal' })
  }
  
  // 如果没有代码，处理粗体和斜体
  if (parts.length === 0 || parts.every(p => p.type === 'normal')) {
    parts.length = 0
    lastIndex = 0
    
    // 处理粗体
    boldRegex.lastIndex = 0
    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ text: text.slice(lastIndex, match.index), type: 'normal' })
      }
      parts.push({ text: match[1] || match[2], type: 'bold' })
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < text.length) {
      parts.push({ text: text.slice(lastIndex), type: 'normal' })
    }
    
    // 如果没有粗体，处理斜体
    if (parts.length === 0 || parts.every(p => p.type === 'normal')) {
      parts.length = 0
      lastIndex = 0
      
      italicRegex.lastIndex = 0
      while ((match = italicRegex.exec(text)) !== null) {
        if (match.index > lastIndex) {
          parts.push({ text: text.slice(lastIndex, match.index), type: 'normal' })
        }
        parts.push({ text: match[1] || match[2], type: 'italic' })
        lastIndex = match.index + match[0].length
      }
      if (lastIndex < text.length) {
        parts.push({ text: text.slice(lastIndex), type: 'normal' })
      }
    }
  }
  
  // 构建TextRun数组
  if (parts.length === 0) {
    runs.push(new TextRun(text))
  } else {
    parts.forEach(part => {
      if (part.text) {
        runs.push(new TextRun({
          text: part.text,
          bold: part.type === 'bold',
          italics: part.type === 'italic',
          font: part.type === 'code' ? 'Courier New' : undefined,
          size: part.type === 'code' ? 20 : undefined
        }))
      }
    })
  }
  
  return new Paragraph({
    children: runs.length > 0 ? runs : [new TextRun(text)],
    spacing: { after: 120 }
  })
}

/**
 * 解析Markdown表格
 */
function parseTable(lines: string[], startIndex: number): { table: Table; nextIndex: number } | null {
  const tableLines: string[] = []
  let i = startIndex
  
  // 收集表格行（直到遇到空行或非表格行）
  while (i < lines.length) {
    const line = lines[i].trim()
    if (!line || !line.startsWith('|')) {
      break
    }
    tableLines.push(line)
    i++
  }
  
  if (tableLines.length < 2) return null
  
  // 解析表头（第一行）
  const headerCells = tableLines[0]
    .split('|')
    .map(c => c.trim())
    .filter(c => c && c.length > 0)
  
  if (headerCells.length === 0) return null
  
  // 找到分隔行（第二行通常是 |---|---|）
  const separatorIndex = tableLines.findIndex((line, idx) => idx > 0 && /^[\s|:-]+$/.test(line))
  if (separatorIndex === -1) return null
  
  // 解析数据行（分隔行之后）
  const dataRows = tableLines
    .slice(separatorIndex + 1)
    .map(line => 
      line.split('|')
        .map(c => c.trim())
        .filter(c => c && c.length > 0)
    )
    .filter(row => row.length > 0)
  
  // 构建Word表格
  const tableRows: TableRow[] = []
  
  // 表头行
  tableRows.push(new TableRow({
    children: headerCells.map(cell => new TableCell({
      children: [new Paragraph({
        text: cell,
        heading: HeadingLevel.HEADING_4
      })],
      shading: { fill: 'E7E6E6' }
    }))
  }))
  
  // 数据行
  dataRows.forEach(row => {
    // 确保列数匹配（如果数据行列数不足，用空字符串填充）
    const cells = [...row]
    while (cells.length < headerCells.length) {
      cells.push('')
    }
    
    tableRows.push(new TableRow({
      children: cells.slice(0, headerCells.length).map(cell => new TableCell({
        children: [new Paragraph({
          text: cell || '-'
        })]
      }))
    }))
  })
  
  return {
    table: new Table({
      rows: tableRows,
      width: { size: 100, type: WidthType.PERCENTAGE }
    }),
    nextIndex: i
  }
}

/**
 * 导出Markdown内容为Word文档
 */
export async function exportToWord(markdown: string, filename: string = '寻源比价报告.docx'): Promise<void> {
  try {
    // 解析Markdown并转换为Word元素
    const elements = parseMarkdownToParagraphs(markdown)
    
    // 创建Word文档
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          // 标题
          new Paragraph({
            text: '寻源比价报告',
            heading: HeadingLevel.TITLE,
            alignment: AlignmentType.CENTER,
            spacing: { after: 400 }
          }),
          // 生成时间
          new Paragraph({
            text: `生成时间：${new Date().toLocaleString('zh-CN')}`,
            alignment: AlignmentType.CENTER,
            spacing: { after: 600 }
          }),
          // 内容
          ...elements
        ]
      }]
    })
    
    // 生成并下载文档
    const blob = await Packer.toBlob(doc)
    saveAs(blob, filename)
  } catch (error) {
    console.error('导出Word文档失败:', error)
    throw new Error(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
}

