# 红楼梦文本处理综合报告

生成时间: 2025-07-22 21:02:03
输入文件: data/raw/hongloumeng_80.md
处理步骤: text_preprocessing, chapter_splitting, tokenization, entity_recognition

---

## 处理统计概览

### 文本预处理
- 总字符数: 590,050
- 总行数: 2,084
- 段落数: 160
- 对话数: 0
- 对话比例: 0.00%

### 章节分割
- 总章节数: 80
- 平均章节长度: 7,345字

### 分词分析
- 总词数: 410,675
- 独特词汇数: 36,491
- 发现的自定义词汇: 16009个
- 发现的古典词汇: 3025个

### 实体识别
- 总文本长度: 590,050字

#### 实体统计
- persons: 12880个
- locations: 489个
- objects: 34个
- titles: 5488个
- classical: 1742个

#### 实体密度（每千字）
- persons: 21.83
- locations: 0.83
- objects: 0.06
- titles: 9.3
- classical: 2.95

#### 最频繁实体
- persons: 宝玉 (出现2642次)
- locations: 怡红院 (出现68次)
- objects: 诗词 (出现13次)
- titles: 太太 (出现1059次)
- classical: 宝钗 (出现688次)


---

## 输出文件

- **preprocessed_text**: `data/processed/preprocessed_text.txt`
- **chapters_dir**: `data/processed/chapters`
- **chapters_metadata**: `data/processed/chapters/metadata.json`
- **tokenization_result**: `data/processed/tokenization_result.json`
- **word_frequency**: `data/processed/word_frequency.json`
- **extracted_entities**: `data/processed/extracted_entities.json`
- **entity_recognition_result**: `data/processed/entity_recognition_result.json`
- **character_co_occurrence**: `data/processed/character_co_occurrence.json`


---

## 处理建议

1. **章节分析**: 可以进一步分析各章节的主题和人物出现频率
2. **人物关系**: 建议深入分析人物共现关系，构建人物关系网络
3. **文风分析**: 可以基于分词结果进行文风特征提取
4. **知识图谱**: 基于实体识别结果构建红楼梦知识图谱

---

*报告由红楼梦AI续写系统自动生成*
