# LLM Plagiarism Checker

This project provides two Streamlit-based web applications that analyze input text for patterns commonly associated with AI-generated content. The tools use metrics such as perplexity and burstiness to detect whether a piece of text is likely written by a human or a language model.

## Features

### 1. Language Model Text Analysis (app.py)
- Calculates Perplexity using a bigram model trained on the Brown corpus
- Measures Burstiness Score for repetition patterns
- Detects whether the text is likely AI-generated
- Visualizes:
  - Most common words
  - Repeated words
- Clean and interactive Streamlit UI

### 2. Plagiarism Patrol (test.py)
- Uses GPT-2 model to calculate perplexity
- Computes burstiness from token repetition
- Visualizes top repeated words using Plotly
- Displays a side-by-side layout with input, analysis results, and charts
- Includes disclaimer for human oversight in AI plagiarism detection

## Installation

### 1. Clone the Repository
```bash
git https://github.com/satyamshivam13/GPT_Shield_AI_Plagiarism_Detector.git
cd GPT_Shield_AI_Plagiarism_Detector
