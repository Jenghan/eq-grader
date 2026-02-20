'\n你是一位資深的國小EQ教育專家。請針對以下練習題,生成 1 個模擬國小學生作答的答案範例。\n\n

【練習題】\n
EQ 練功房:想法心手把\n
【說明】\n
在生活中難免會遇到讓人困擾的事件,此時可以運用「想法心手把」來幫助自己覺察情緒、找出背後的想法,並進一步提升想法的彈性,產生能讓自己感到平靜與希望的想法。\n
【指示】\n
使用情緒轉盤覺察多種情緒,找出背後想法,並培養平靜與希望的彈性思維。要練習找正面情緒，不能全部都是負面情緒。\n\n\n\n



【學生答題品質模擬：優秀】\n
這位學生非常認真作答：\n
- 完全理解題目要求\n
- 答案內容完整且有深度\n
- 展現自我反思能力\n
- 用詞恰當、表達清晰\n
- 能具體描述情境和感受\n\n

請根據上述學生特性來生成答案。答案應該真實反映這種程度學生的作答情況。\n\n

【生成要求】\n
1. 涵蓋國小學生常見的生活情境（校園、家庭、同儕互動等）\n
2. 每個答案的情境類型要不同,例如:\n
   - 同儕衝突（被欺負、吵架、被排擠）\n  
 - 學習挫折（考試成績、作業困難）\n 
  - 家庭互動（父母管教、手足衝突）\n  
 - 自我期許（比賽失利、表現不佳）\n  
 - 人際焦慮（交友、被誤解）\n
3. 情緒詞彙要符合國小學生程度\n
4. 語言要口語化、真實反映小學生的表達方式\n
5. 重要：答案品質必須符合「優秀」等級的特徵\n\n

【適齡要求】內容必須適合國小學生\n\n

請以JSON格式輸出,每個答案包含以下欄位:\n
- event: 事件 (必填)\n- emotion_slots: 情緒格子 (陣列, 8-8個項目)\n
  說明: 情緒轉盤的8個格子。第1-6格為情緒(顏色與情緒由AI生成，有正向、有負向)，第7格固定為綠色/平靜，第8格固定為黃色/希望\n  
每個項目必須是物件，包含以下欄位:\n  
  - color (text): 顏色 - 代表該情緒的顏色。第7格固定為綠色，第8格固定為黃色 [必填]\n 
   - emotion (text): 情緒 - 該顏色所代表的情緒名稱。第7格固定為平靜，第8格固定為希望 [必填]\n  
  - thought (text): 想法 - 該情緒背後的內在想法。第7格為能幫助自己回到平靜的想法，第8格為能產生希望感受的想法 [必填]\n   
 - slot_number (integer): 格子編號 - 1-8的編號 [必填]\n\n

【重要：答案分析欄位】\n
每個答案必須包含以下兩個獨立評價欄位。評價時請「完全忘記」這是用什麼品質等級生成的，只根據答案的實際內容來判斷：\n\n

1. student_self_reflection（學生自我反思）- 以寫出這份答案的小學生角度，看著自己的答案進行反思：\n  
 - confidence: 對自己答案的信心（很有信心/普通/不太確定/亂寫的）\n 
  - perceived_difficulty: 覺得哪裡最難寫\n
   - self_assessment: 用學生口吻評價自己寫得如何\n 
  - uncertain_parts: 自己覺得不確定的欄位名稱列表\n\n

2. teacher_feedback（老師專業評價）- 以專業老師角度，客觀評估這份答案：\n
   - overall_quality: 綜合評判（優秀/良好/普通/待加強/需重寫）\n 
  - scores: 各維度分數(1-5分)\n    
 - completeness: 完整性（是否完整回答所有欄位）\n    
 - correctness: 正確性（內容是否符合題意、欄位是否填對）\n    
 - depth: 深度（思考是否有深度、是否有自我反思）\n   
  - expression: 表達（描述是否清楚具體）\n    
 - appropriateness: 適切性（情緒和想法是否合理對應事件）\n   
- strengths: 答案的優點列表\n  
 - weaknesses: 答案的缺點列表\n   
- error_analysis: 具體錯誤分析（若無錯誤則寫「無明顯錯誤」）\n 
  - suggestions: 給學生的具體改進建議\n\n【

答案欄位範例】（請嚴格遵循此格式結構）\n
{\'event\': \'國語考試成績不理想\', \'emotion_slots\': [{\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 1}, {\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 2}, {\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 3}, {\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 4}, {\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 5}, {\'color\': \'{顏色}\', \'emotion\': \'{情緒}\', \'thought\': \'{想法}\', \'slot_number\': 6}, {\'color\': \'綠色\', \'emotion\': \'平靜\', \'thought\': \'{想法}\', \'slot_number\': 7}, {\'color\': \'黃色\', \'emotion\': \'希望\', \'thought\': \'{想法}\', \'slot_number\': 8}]}\n\n

【分析欄位範例】（每個答案都必須加上這兩個欄位）\n
{\n  
"student_self_reflection": {\n  
  "confidence": "不太確定",\n 
   "perceived_difficulty": "想法那邊不知道要寫什麼",\n 
   "self_assessment": "應該有寫對吧...但好像寫太少了",\n  
  "uncertain_parts": ["thought"]\n  },\n  
"teacher_feedback": {\n  
  "overall_quality": "待加強",\n 
   "scores": {\n    
  "completeness": 2,\n    
  "correctness": 3,\n    
  "depth": 1,\n   
   "expression": 2,\n  
    "appropriateness": 3\n 
   },\n  
  "strengths": ["能辨識出難過的情緒"],\n   
 "weaknesses": ["事件描述過於簡略"],\n 
   "error_analysis": "事件沒有說明具體情境",\n  
  "suggestions": "試著把事件寫得更具體"\n 
 }\n}\n\n


【最終輸出格式】\n
請將答案欄位與分析欄位合併，輸出為：\n
{\n  
"answers": [\n 
   {\n      
// 答案欄位（依照上方【答案欄位範例】的結構）\n 
     ...\n  
    // 分析欄位\n   
   "student_self_reflection": { ... },\n  
    "teacher_feedback": { ... }\n
    }\n
  ]\n
}\n\n

請直接輸出JSON,不要有任何其他說明文字。\n'
