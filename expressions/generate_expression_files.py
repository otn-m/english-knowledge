from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REVIEW_DIR = ROOT / "review"

FIELDNAMES = [
    "id",
    "category",
    "source_id",
    "evidence_level",
    "expression",
    "meaning_ja",
    "pattern",
    "situation",
    "example_en",
    "prompt_ja",
    "answer_en",
    "source_note",
]

CATEGORY_TARGETS = {
    "日常会話": 70,
    "仕事・メール": 90,
    "説明・意見": 70,
    "高頻度コロケーション": 70,
}

SOURCE_CATALOG = {
    "PHRASE_STYLE": {
        "level": "B",
        "label": "PHRASE List 型の高頻度定型表現",
        "note": "Martinez & Schmitt のPHRASE Listを主な基準に、丸写しせず発信用に代表用法へ落とした表現。",
    },
    "PHAVE_EXISTING": {
        "level": "A",
        "label": "PHaVE List / 既存PHaVE素材",
        "note": "PHaVE Listと既存ノートを参照した句動詞・句動詞型表現。",
    },
    "EVP_FUNCTION": {
        "level": "B",
        "label": "English Profile 型の機能表現",
        "note": "English Vocabulary Profileのように、CEFR・実用機能・学習優先度で扱われる発信用表現。",
    },
    "AFL_DISCOURSE": {
        "level": "B",
        "label": "Academic/formulaic discourse marker",
        "note": "Academic Formulas List系の発想で選んだ説明・意見・論理展開の定型表現。",
    },
    "CORPUS_COLLOCATION": {
        "level": "B",
        "label": "コーパスベース辞書・word sketch型コロケーション",
        "note": "COBUILD、Oxford/Longman系、Sketch Engine/SKELL型のコーパス参照で自然性を重視した高頻度コロケーション。",
    },
    "BUSINESS_CORPUS_REF": {
        "level": "B",
        "label": "ビジネス英語コーパス参照型",
        "note": "Cambridge Business English Corpusやビジネスメール教材で重視される機能を、一般的な仕事発信向けに整理。",
    },
    "PRAGMATIC_HIGH_UTILITY": {
        "level": "C",
        "label": "高実用だが頻度順位未確認",
        "note": "発信で有用なため採用。ただし頻度順位や特定コーパス由来は主張しない。",
    },
}

PHAVE_PATTERNS = {
    "got caught up",
    "ended up",
    "turned out",
    "catch up",
    "get back",
    "follow up",
    "move up",
    "come up with",
    "reach out",
    "pay off",
}

EXPLICIT_LOW_EVIDENCE = {
    "My bad",
    "I am in",
    "I am up for it",
    "Keep me posted",
}

RAW_ROWS = [
    ("日常会話", "It happens", "そういうこともある", "It happens.", "失敗や予想外の出来事を軽く受け止める", "It happens, so let us try again tomorrow."),
    ("日常会話", "No worries", "気にしなくていい", "No worries.", "謝罪や依頼への軽い返答", "No worries, I can wait a few more minutes."),
    ("日常会話", "That makes sense", "それは筋が通っている", "That makes sense.", "説明を聞いて納得する", "That makes sense now that you explained the reason."),
    ("日常会話", "I see what you mean", "言いたいことは分かる", "I see what you mean.", "相手の意図を理解したことを示す", "I see what you mean, but I still have one concern."),
    ("日常会話", "I am not sure", "よく分からない、自信がない", "I am not sure.", "答えに確信がない", "I am not sure, so I will check it later."),
    ("日常会話", "I am not sure if", "...かどうか分からない", "I am not sure if + clause", "条件や事実に確信がない", "I am not sure if the store is still open."),
    ("日常会話", "Do you mean", "...という意味ですか", "Do you mean + clause?", "相手の発言を確認する", "Do you mean we should leave earlier?"),
    ("日常会話", "What do you mean by", "...とはどういう意味ですか", "What do you mean by + noun?", "単語や発言の意味を尋ねる", "What do you mean by flexible schedule?"),
    ("日常会話", "Let me think", "少し考えさせて", "Let me think.", "すぐに答えず考える時間を取る", "Let me think before I answer that."),
    ("日常会話", "Give me a second", "少し待って", "Give me a second.", "短い待ち時間を頼む", "Give me a second, and I will find the file."),
    ("日常会話", "I was wondering if", "...していただけないかと思って", "I was wondering if + clause", "丁寧に依頼や質問を切り出す", "I was wondering if you could help me with this."),
    ("日常会話", "Could you do me a favor", "お願いしてもいいですか", "Could you do me a favor?", "頼みごとを切り出す", "Could you do me a favor and check this message?"),
    ("日常会話", "Would you mind", "...していただけますか", "Would you mind + V-ing?", "丁寧に行動を依頼する", "Would you mind opening the window?"),
    ("日常会話", "Let me know", "知らせてください", "Let me know + wh/if clause", "相手から情報をもらう", "Let me know if you need anything."),
    ("日常会話", "Keep me posted", "随時知らせて", "Keep me posted.", "進捗や状況を継続的に知りたい", "Keep me posted on how it goes."),
    ("日常会話", "Sounds good", "よさそうです", "Sounds good.", "提案に同意する", "Sounds good. Let us meet at six."),
    ("日常会話", "That works for me", "それで大丈夫です", "That works for me.", "予定や方法に同意する", "Tuesday afternoon works for me."),
    ("日常会話", "I am in", "参加します、乗ります", "I am in.", "誘いや案に参加する意思を示す", "If you are going hiking, I am in."),
    ("日常会話", "I am up for it", "やってみたい、乗り気です", "I am up for it.", "活動への前向きな気持ちを示す", "A late dinner sounds fun. I am up for it."),
    ("日常会話", "I have plans", "予定があります", "I have plans.", "誘いを断る理由を述べる", "I have plans tonight, but maybe next week."),
    ("日常会話", "Maybe next time", "また今度", "Maybe next time.", "今回は断って次回に回す", "I cannot join today. Maybe next time."),
    ("日常会話", "I will pass", "今回は遠慮します", "I will pass.", "提案を短く断る", "Thanks for asking, but I will pass this time."),
    ("日常会話", "I cannot make it", "行けない、間に合わない", "I cannot make it.", "予定に参加できない", "I am sorry, but I cannot make it to dinner."),
    ("日常会話", "I am running late", "遅れています", "I am running late.", "到着が遅れることを伝える", "I am running late, but I will be there soon."),
    ("日常会話", "I got caught up", "手が離せなくなった", "I got caught up in + noun", "別件で遅れた理由を説明する", "I got caught up in a call and missed the train."),
    ("日常会話", "I am on my way", "向かっています", "I am on my way.", "移動中であることを伝える", "I am on my way and should arrive in ten minutes."),
    ("日常会話", "I am almost there", "もうすぐ着きます", "I am almost there.", "到着直前であることを伝える", "I am almost there, so please wait inside."),
    ("日常会話", "Thanks for having me", "招いてくれてありがとう", "Thanks for having me.", "訪問や食事のあとに感謝する", "Thanks for having me. I had a great time."),
    ("日常会話", "I appreciate it", "感謝しています", "I appreciate it.", "やや丁寧に感謝する", "You helped me a lot, and I appreciate it."),
    ("日常会話", "That is kind of you", "ご親切にありがとう", "That is kind of you.", "相手の親切に反応する", "That is kind of you to offer me a ride."),
    ("日常会話", "Sorry about that", "それはすみません", "Sorry about that.", "軽いミスや迷惑を謝る", "Sorry about that. I sent the wrong link."),
    ("日常会話", "My bad", "私のミスです", "My bad.", "くだけた場面で自分のミスを認める", "My bad. I forgot to bring the tickets."),
    ("日常会話", "It is up to you", "あなた次第です", "It is up to you.", "決定を相手に委ねる", "We can eat out or cook at home. It is up to you."),
    ("日常会話", "Either way is fine", "どちらでも大丈夫", "Either way is fine.", "二つの選択肢のどちらでもよい", "We can meet before or after lunch. Either way is fine."),
    ("日常会話", "I do not mind", "構いません", "I do not mind + noun/V-ing", "不満がないことを示す", "I do not mind walking if the weather is nice."),
    ("日常会話", "I would rather", "むしろ...したい", "I would rather + verb", "好みを控えめに述べる", "I would rather stay home tonight."),
    ("日常会話", "I feel like", "...したい気がする、...のように感じる", "I feel like + noun/V-ing/clause", "気分や印象を述べる", "I feel like taking a short walk."),
    ("日常会話", "I am into", "...にハマっている", "I am into + noun", "興味や趣味を述べる", "I am into podcasts about history."),
    ("日常会話", "I am not into", "...はあまり好きではない", "I am not into + noun", "好みでないことを柔らかく言う", "I am not into horror movies."),
    ("日常会話", "I am looking forward to", "...を楽しみにしている", "I am looking forward to + noun/V-ing", "予定への期待を述べる", "I am looking forward to seeing you next week."),
    ("日常会話", "I cannot wait to", "...するのが待ちきれない", "I cannot wait to + verb", "強い楽しみを表す", "I cannot wait to try the new restaurant."),
    ("日常会話", "I am used to", "...に慣れている", "I am used to + noun/V-ing", "慣れた状態を述べる", "I am used to working from home."),
    ("日常会話", "I am getting used to", "...に慣れてきている", "I am getting used to + noun/V-ing", "慣れる途中であることを述べる", "I am getting used to the new schedule."),
    ("日常会話", "I tend to", "...しがちです", "I tend to + verb", "自分の傾向を述べる", "I tend to wake up early on weekends."),
    ("日常会話", "I am supposed to", "...することになっている", "I am supposed to + verb", "予定や義務を述べる", "I am supposed to call my parents tonight."),
    ("日常会話", "I meant to", "...するつもりだった", "I meant to + verb", "意図はあったが実行できなかったことを述べる", "I meant to reply earlier, but I forgot."),
    ("日常会話", "I forgot to", "...するのを忘れた", "I forgot to + verb", "未実行の忘れ物を述べる", "I forgot to charge my phone."),
    ("日常会話", "I ended up", "結局...した", "I ended up + V-ing", "予定と違う結果を述べる", "I ended up staying home all day."),
    ("日常会話", "It turned out", "結果として...だと分かった", "It turned out + clause", "後で判明した結果を述べる", "It turned out that we had the same idea."),
    ("日常会話", "I ran into", "...に偶然会った", "I ran into + person", "偶然の出会いを述べる", "I ran into an old friend at the station."),
    ("日常会話", "I came across", "...を偶然見つけた", "I came across + thing", "情報や物を偶然見つける", "I came across an interesting article this morning."),
    ("日常会話", "It depends", "場合によります", "It depends.", "条件次第で答えが変わる", "It depends. I need to check my schedule first."),
    ("日常会話", "It depends on", "...次第です", "It depends on + noun/wh clause", "依存する条件を示す", "It depends on how much time we have."),
    ("日常会話", "As far as I know", "私の知る限りでは", "As far as I know, + clause", "限定付きで情報を伝える", "As far as I know, the shop closes at eight."),
    ("日常会話", "To be honest", "正直に言うと", "To be honest, + clause", "率直な意見を前置きする", "To be honest, I was a little nervous."),
    ("日常会話", "Honestly", "正直なところ", "Honestly, + clause", "率直さや驚きを出す", "Honestly, I did not expect such a quick reply."),
    ("日常会話", "Actually", "実は、実際には", "Actually, + clause", "訂正や追加情報を出す", "Actually, I have already seen that movie."),
    ("日常会話", "In that case", "それなら", "In that case, + clause", "前の情報を受けて判断する", "In that case, let us take a taxi."),
    ("日常会話", "By the way", "ところで", "By the way, + clause/question", "話題を切り替える", "By the way, did you call Lisa?"),
    ("日常会話", "Speaking of", "...と言えば", "Speaking of + noun", "関連話題へ移る", "Speaking of lunch, have you tried that cafe?"),
    ("日常会話", "That reminds me", "それで思い出した", "That reminds me, + clause", "思い出した用件を出す", "That reminds me, I need to book a hotel."),
    ("日常会話", "Before I forget", "忘れないうちに", "Before I forget, + clause", "忘れそうな情報を先に言う", "Before I forget, here is your charger."),
    ("日常会話", "Long story short", "手短に言うと", "Long story short, + clause", "詳しい経緯を省いて結論を言う", "Long story short, we missed the last train."),
    ("日常会話", "I get the point", "要点は分かります", "I get the point.", "相手の主張を理解したと伝える", "I get the point, but I disagree with the solution."),
    ("日常会話", "I am not following", "話についていけていません", "I am not following.", "説明が理解できないことを伝える", "I am not following. Could you explain that part again?"),
    ("日常会話", "Could you say that again", "もう一度言ってもらえますか", "Could you say that again?", "聞き取れなかったときに頼む", "Could you say that again? The connection was bad."),
    ("日常会話", "Could you slow down", "ゆっくり話してもらえますか", "Could you slow down?", "相手の話す速度を下げてもらう", "Could you slow down a little? I am still learning."),
    ("日常会話", "What are you up to", "何しているの、最近どう", "What are you up to?", "近況や今の予定を尋ねる", "What are you up to this weekend?"),
    ("日常会話", "How did it go", "どうだった", "How did it go?", "結果や感想を尋ねる", "How did it go with your interview?"),
    ("日常会話", "Let us catch up", "近況を話そう", "Let us catch up.", "久しぶりに話す約束をする", "Let us catch up over coffee next week."),
    ("仕事・メール", "Please find attached", "添付をご確認ください", "Please find attached + noun", "メールで添付ファイルを送る", "Please find attached the updated proposal."),
    ("仕事・メール", "I am writing to", "...するためにご連絡しています", "I am writing to + verb", "メール冒頭で目的を述べる", "I am writing to confirm our meeting time."),
    ("仕事・メール", "I wanted to ask about", "...について伺いたいです", "I wanted to ask about + noun", "丁寧に質問を切り出す", "I wanted to ask about the timeline for this project."),
    ("仕事・メール", "I wanted to follow up on", "...についてフォローアップしたいです", "I wanted to follow up on + noun", "以前の件を再確認する", "I wanted to follow up on the budget discussion."),
    ("仕事・メール", "Just following up on", "...について再度確認します", "Just following up on + noun", "短いフォローアップメールを送る", "Just following up on my email from last week."),
    ("仕事・メール", "Thank you for reaching out", "ご連絡ありがとうございます", "Thank you for reaching out.", "問い合わせや連絡への返信", "Thank you for reaching out. I would be happy to help."),
    ("仕事・メール", "Thanks for the update", "更新ありがとうございます", "Thanks for the update.", "進捗共有への返答", "Thanks for the update. I will review it today."),
    ("仕事・メール", "I will look into it", "調べてみます", "I will look into + noun", "問題や質問を調査する", "I will look into it and get back to you."),
    ("仕事・メール", "I will get back to you", "折り返し連絡します", "I will get back to you + time", "確認後に返事を約束する", "I will get back to you by tomorrow morning."),
    ("仕事・メール", "Could you clarify", "明確にしていただけますか", "Could you clarify + noun/wh clause?", "不明点を確認する", "Could you clarify what you mean by final version?"),
    ("仕事・メール", "Could you confirm", "確認していただけますか", "Could you confirm + noun/if clause?", "事実や予定を確認する", "Could you confirm the meeting location?"),
    ("仕事・メール", "Could you send over", "送っていただけますか", "Could you send over + noun?", "資料や情報を依頼する", "Could you send over the latest numbers?"),
    ("仕事・メール", "Could you take a look at", "見ていただけますか", "Could you take a look at + noun?", "レビューや確認を依頼する", "Could you take a look at this draft?"),
    ("仕事・メール", "Please let me know if", "...なら知らせてください", "Please let me know if + clause", "条件付きで連絡を求める", "Please let me know if you have any questions."),
    ("仕事・メール", "Let me check", "確認します", "Let me check + noun", "すぐ確認する意思を示す", "Let me check the calendar and get back to you."),
    ("仕事・メール", "Let me double-check", "念のため確認します", "Let me double-check + noun", "誤り防止の確認をする", "Let me double-check the numbers before we send this."),
    ("仕事・メール", "I will keep you updated", "随時共有します", "I will keep you updated.", "進捗の継続共有を約束する", "I will keep you updated as the situation changes."),
    ("仕事・メール", "I will share the details", "詳細を共有します", "I will share the details + time", "後で詳しい情報を送る", "I will share the details after the meeting."),
    ("仕事・メール", "For your reference", "ご参考までに", "For your reference, + clause", "参考情報を添える", "For your reference, I attached last quarter's report."),
    ("仕事・メール", "For your review", "レビュー用に", "For your review, + clause", "確認してほしい資料を送る", "For your review, I added comments to the document."),
    ("仕事・メール", "As discussed", "話し合った通り", "As discussed, + clause", "会議や会話の内容を受ける", "As discussed, we will start with a small test."),
    ("仕事・メール", "As mentioned earlier", "先ほど述べた通り", "As mentioned earlier, + clause", "前に伝えた内容を参照する", "As mentioned earlier, the deadline is Friday."),
    ("仕事・メール", "Based on our conversation", "話し合いに基づいて", "Based on our conversation, + clause", "会話を踏まえた結論を述べる", "Based on our conversation, I revised the proposal."),
    ("仕事・メール", "Regarding", "...に関して", "Regarding + noun", "件名や話題を示す", "Regarding the invoice, we need one small correction."),
    ("仕事・メール", "With regard to", "...に関して", "With regard to + noun", "ややフォーマルに話題を示す", "With regard to the schedule, we have two options."),
    ("仕事・メール", "As for", "...については", "As for + noun", "他の話題と分けて述べる", "As for the design, I will ask the team."),
    ("仕事・メール", "In terms of", "...の観点では", "In terms of + noun", "観点や尺度を示す", "In terms of cost, this option is better."),
    ("仕事・メール", "On my end", "私の側では", "On my end, + clause", "自分側の状況を伝える", "Everything looks good on my end."),
    ("仕事・メール", "From my side", "私の側からは", "From my side, + clause", "自分の担当範囲から述べる", "From my side, there are no major concerns."),
    ("仕事・メール", "From your perspective", "あなたの観点では", "From your perspective, + question/clause", "相手の見方を尋ねる", "From your perspective, what is the biggest risk?"),
    ("仕事・メール", "We need to align on", "...について認識を合わせる必要がある", "We need to align on + noun", "方針や条件をそろえる", "We need to align on the scope before we start."),
    ("仕事・メール", "Let us align on", "...について認識を合わせましょう", "Let us align on + noun", "合意形成を提案する", "Let us align on the next steps in today's meeting."),
    ("仕事・メール", "I agree with", "...に賛成です", "I agree with + noun/person", "意見に同意する", "I agree with your suggestion."),
    ("仕事・メール", "I am aligned with", "...と認識が一致しています", "I am aligned with + noun/person", "方針や見解の一致を伝える", "I am aligned with the current direction."),
    ("仕事・メール", "That works on my end", "私の側ではそれで大丈夫です", "That works on my end.", "予定や案を承認する", "That works on my end. Please send the invite."),
    ("仕事・メール", "Does that work for you", "それで都合はよいですか", "Does that work for you?", "相手の都合を確認する", "We can meet at three. Does that work for you?"),
    ("仕事・メール", "What is your availability", "ご都合はいかがですか", "What is your availability + time?", "会議可能な時間を尋ねる", "What is your availability next Tuesday?"),
    ("仕事・メール", "Are you available for", "...に対応可能ですか", "Are you available for + noun/time?", "会議や作業の可否を尋ねる", "Are you available for a quick call tomorrow?"),
    ("仕事・メール", "Let us schedule", "予定を入れましょう", "Let us schedule + noun", "会議や作業時間を設定する", "Let us schedule a follow-up meeting."),
    ("仕事・メール", "Let us reschedule", "予定を変更しましょう", "Let us reschedule + noun", "日程を組み直す", "Let us reschedule the meeting for next week."),
    ("仕事・メール", "Let us push back", "後ろ倒しにしましょう", "Let us push back + noun", "期限や予定を遅らせる", "Let us push back the launch by one week."),
    ("仕事・メール", "Let us move up", "前倒しにしましょう", "Let us move up + noun", "予定を早める", "Let us move up the review to Monday."),
    ("仕事・メール", "The deadline is approaching", "締切が近づいています", "The deadline is approaching.", "締切が近いことを伝える", "The deadline is approaching, so we need a final check."),
    ("仕事・メール", "We are on track", "予定通り進んでいます", "We are on track.", "進捗が計画通りである", "We are on track to finish by Friday."),
    ("仕事・メール", "We are behind schedule", "予定より遅れています", "We are behind schedule.", "進捗遅れを共有する", "We are behind schedule because testing took longer."),
    ("仕事・メール", "We are ahead of schedule", "予定より進んでいます", "We are ahead of schedule.", "進捗が早いことを共有する", "We are ahead of schedule, so we can start the review."),
    ("仕事・メール", "There is a blocker", "障害があります", "There is a blocker.", "進行を止める問題を報告する", "There is a blocker with the approval process."),
    ("仕事・メール", "We need to prioritize", "優先順位をつける必要がある", "We need to prioritize + noun", "やることを絞る", "We need to prioritize the tasks for this week."),
    ("仕事・メール", "The main priority is", "最優先事項は...です", "The main priority is + noun", "重要度の高い事項を示す", "The main priority is fixing the login issue."),
    ("仕事・メール", "To move this forward", "これを前に進めるために", "To move this forward, + clause", "次の行動を促す", "To move this forward, we need approval today."),
    ("仕事・メール", "Next steps are", "次のステップは...です", "Next steps are + noun/list", "会議後やメールで次の行動を整理する", "Next steps are testing the feature and sharing feedback."),
    ("仕事・メール", "Action items", "対応事項", "Action items: + list", "会議後のタスクを列挙する", "Action items are listed at the bottom of the notes."),
    ("仕事・メール", "I will take care of", "...を対応します", "I will take care of + noun", "自分が対応することを伝える", "I will take care of the booking."),
    ("仕事・メール", "I will handle", "...を担当します", "I will handle + noun", "作業や問題を引き受ける", "I will handle the client communication."),
    ("仕事・メール", "Could you own", "...を担当してもらえますか", "Could you own + noun?", "責任者として任せる", "Could you own the testing plan?"),
    ("仕事・メール", "Who is responsible for", "...の責任者は誰ですか", "Who is responsible for + noun?", "担当や責任範囲を確認する", "Who is responsible for the final approval?"),
    ("仕事・メール", "I am responsible for", "...を担当しています", "I am responsible for + noun", "自分の担当範囲を述べる", "I am responsible for the weekly report."),
    ("仕事・メール", "I will make sure", "必ず...します", "I will make sure + clause", "確実に実行すると伝える", "I will make sure everyone receives the update."),
    ("仕事・メール", "Please make sure", "必ず...してください", "Please make sure + clause", "相手に確認や実行を依頼する", "Please make sure the file name is correct."),
    ("仕事・メール", "It would be helpful if", "...していただけると助かります", "It would be helpful if + clause", "丁寧に依頼する", "It would be helpful if you could send examples."),
    ("仕事・メール", "It would be great if", "...していただけるとありがたいです", "It would be great if + clause", "前向きに依頼する", "It would be great if we could decide today."),
    ("仕事・メール", "At your earliest convenience", "ご都合がつき次第", "At your earliest convenience", "フォーマルに早めの対応を頼む", "Please reply at your earliest convenience."),
    ("仕事・メール", "By end of day", "今日中に", "By end of day", "当日中の期限を示す", "Please send the numbers by end of day."),
    ("仕事・メール", "By close of business", "業務終了時までに", "By close of business", "営業日の終業までの期限を示す", "We need the approval by close of business."),
    ("仕事・メール", "No later than", "遅くとも...までに", "No later than + time/date", "厳しめの期限を示す", "Please submit the form no later than Friday."),
    ("仕事・メール", "As soon as possible", "できるだけ早く", "As soon as possible", "早急な対応を求める", "Please let us know as soon as possible."),
    ("仕事・メール", "Whenever you have a chance", "お時間のあるときに", "Whenever you have a chance", "急がない依頼をする", "Could you review this whenever you have a chance?"),
    ("仕事・メール", "No rush", "急ぎません", "No rush.", "相手に急がなくてよいと伝える", "No rush, but please send it this week."),
    ("仕事・メール", "Thanks in advance", "先にお礼申し上げます", "Thanks in advance.", "依頼メールの結びに使う", "Thanks in advance for your help."),
    ("仕事・メール", "I appreciate your help", "ご協力に感謝します", "I appreciate your help.", "支援への感謝を述べる", "I appreciate your help with this issue."),
    ("仕事・メール", "Sorry for the inconvenience", "ご不便をおかけしてすみません", "Sorry for the inconvenience.", "相手に迷惑がかかったことを謝る", "Sorry for the inconvenience caused by the delay."),
    ("仕事・メール", "Thank you for your patience", "お待ちいただきありがとうございます", "Thank you for your patience.", "待たせた相手に感謝する", "Thank you for your patience while we investigate this."),
    ("仕事・メール", "I apologize for the delay", "遅れて申し訳ありません", "I apologize for the delay.", "返信や作業の遅れを謝る", "I apologize for the delay in getting back to you."),
    ("仕事・メール", "There was a misunderstanding", "誤解がありました", "There was a misunderstanding.", "認識違いを説明する", "There was a misunderstanding about the deadline."),
    ("仕事・メール", "To avoid confusion", "混乱を避けるために", "To avoid confusion, + clause", "誤解防止の説明をする", "To avoid confusion, I summarized the decision below."),
    ("仕事・メール", "To clarify", "明確にすると", "To clarify, + clause", "補足説明や訂正をする", "To clarify, the price does not include tax."),
    ("仕事・メール", "Just to confirm", "確認ですが", "Just to confirm, + clause/question", "念のため確認する", "Just to confirm, the meeting starts at ten."),
    ("仕事・メール", "Just to be clear", "はっきりさせると", "Just to be clear, + clause", "誤解を防いで明示する", "Just to be clear, this is not the final version."),
    ("仕事・メール", "Please note that", "...にご注意ください", "Please note that + clause", "重要な注意点を伝える", "Please note that the office will be closed Monday."),
    ("仕事・メール", "A quick heads-up", "念のため事前共有です", "A quick heads-up: + clause", "事前に軽く知らせる", "A quick heads-up: the schedule may change."),
    ("仕事・メール", "We are currently working on", "現在...に取り組んでいます", "We are currently working on + noun", "進行中の作業を共有する", "We are currently working on the final design."),
    ("仕事・メール", "We are planning to", "...する予定です", "We are planning to + verb", "計画を共有する", "We are planning to release the update next month."),
    ("仕事・メール", "We are considering", "...を検討しています", "We are considering + noun/V-ing", "候補や案を検討中である", "We are considering a simpler pricing model."),
    ("仕事・メール", "We decided to", "...することに決めました", "We decided to + verb", "決定事項を共有する", "We decided to postpone the launch."),
    ("仕事・メール", "We are expected to", "...する見込みです", "We are expected to + verb", "見込みや予定を述べる", "We are expected to finish the review by Friday."),
    ("仕事・メール", "The issue has been resolved", "問題は解決済みです", "The issue has been resolved.", "問題解決を報告する", "The issue has been resolved, and the service is back online."),
    ("仕事・メール", "The issue is still ongoing", "問題はまだ継続中です", "The issue is still ongoing.", "未解決の問題を報告する", "The issue is still ongoing, but we found the cause."),
    ("仕事・メール", "I will escalate this", "この件を上位にエスカレーションします", "I will escalate this + time", "上位者や別チームに回す", "I will escalate this to the support team."),
    ("仕事・メール", "I looped in", "...を話に入れました", "I looped in + person", "関係者をメールや会話に加える", "I looped in Maria because she owns the data."),
    ("仕事・メール", "I have cc'd", "...をCCに入れました", "I have cc'd + person", "メールで関係者をCCに入れる", "I have cc'd Ken for visibility."),
    ("説明・意見", "In my opinion", "私の意見では", "In my opinion, + clause", "自分の意見を述べる", "In my opinion, this plan is realistic."),
    ("説明・意見", "I would say", "私なら...と言います", "I would say + clause", "控えめに判断を述べる", "I would say the first option is safer."),
    ("説明・意見", "I would argue that", "...だと主張したい", "I would argue that + clause", "論理的に主張する", "I would argue that the benefits outweigh the risks."),
    ("説明・意見", "It seems to me that", "私には...のように思える", "It seems to me that + clause", "見解を柔らかく述べる", "It seems to me that we need more data."),
    ("説明・意見", "I suppose", "...だと思います", "I suppose + clause", "やや控えめな推測を述べる", "I suppose we could start with a small test."),
    ("説明・意見", "I assume", "...だと想定しています", "I assume + clause", "前提や仮定を述べる", "I assume the price includes shipping."),
    ("説明・意見", "I guess", "...だと思う", "I guess + clause", "くだけた推測や判断を述べる", "I guess we should leave soon."),
    ("説明・意見", "I am convinced that", "...だと確信しています", "I am convinced that + clause", "強い確信を述べる", "I am convinced that this approach will work."),
    ("説明・意見", "I am not convinced that", "...だとは納得していません", "I am not convinced that + clause", "疑いを丁寧に述べる", "I am not convinced that this solves the root problem."),
    ("説明・意見", "There is no doubt that", "...であることは疑いない", "There is no doubt that + clause", "強い確実性を述べる", "There is no doubt that demand is increasing."),
    ("説明・意見", "It is likely that", "...である可能性が高い", "It is likely that + clause", "高い可能性を述べる", "It is likely that prices will rise again."),
    ("説明・意見", "It is unlikely that", "...である可能性は低い", "It is unlikely that + clause", "低い可能性を述べる", "It is unlikely that we can finish today."),
    ("説明・意見", "It is possible that", "...の可能性がある", "It is possible that + clause", "可能性を中立的に述べる", "It is possible that the data is incomplete."),
    ("説明・意見", "It is worth noting that", "...は注目に値する", "It is worth noting that + clause", "重要な補足点を出す", "It is worth noting that the sample size is small."),
    ("説明・意見", "The point is that", "要するに...ということです", "The point is that + clause", "中心となる主張を示す", "The point is that we need a simpler process."),
    ("説明・意見", "The key point is", "重要な点は...です", "The key point is + noun/clause", "最重要点を示す", "The key point is customer trust."),
    ("説明・意見", "The main reason is", "主な理由は...です", "The main reason is + noun/clause", "理由の中心を述べる", "The main reason is the lack of time."),
    ("説明・意見", "One reason is that", "一つの理由は...です", "One reason is that + clause", "理由を一つ挙げる", "One reason is that the tool is easy to use."),
    ("説明・意見", "Another factor is", "もう一つの要因は...です", "Another factor is + noun/clause", "追加の要因を示す", "Another factor is the cost of maintenance."),
    ("説明・意見", "This is because", "これは...だからです", "This is because + clause", "直前の内容の理由を述べる", "This is because users prefer a faster process."),
    ("説明・意見", "That is why", "だから...なのです", "That is why + clause", "理由から結論へつなぐ", "That is why we changed the schedule."),
    ("説明・意見", "As a result", "その結果", "As a result, + clause", "結果を述べる", "As a result, the team saved two hours a week."),
    ("説明・意見", "As a consequence", "結果として", "As a consequence, + clause", "やや硬く結果を述べる", "As a consequence, the cost increased."),
    ("説明・意見", "For this reason", "この理由で", "For this reason, + clause", "理由を受けて結論を述べる", "For this reason, we recommend the second option."),
    ("説明・意見", "In other words", "言い換えると", "In other words, + clause", "別の表現で説明する", "In other words, we need more time."),
    ("説明・意見", "To put it simply", "簡単に言うと", "To put it simply, + clause", "分かりやすく言い換える", "To put it simply, the system is too slow."),
    ("説明・意見", "Put another way", "別の言い方をすると", "Put another way, + clause", "別角度から言い換える", "Put another way, we are solving the wrong problem."),
    ("説明・意見", "What I mean is", "私が言いたいのは...です", "What I mean is + clause", "意図を明確にする", "What I mean is that the timing matters."),
    ("説明・意見", "For example", "例えば", "For example, + clause", "例を出す", "For example, we could start with new users."),
    ("説明・意見", "For instance", "例えば", "For instance, + clause", "例を出す", "For instance, the app loads faster on Wi-Fi."),
    ("説明・意見", "Such as", "...のような", "such as + noun", "具体例を名詞で挙げる", "We need basic information such as name and email."),
    ("説明・意見", "In particular", "特に", "In particular, + clause/noun", "特定の点を強調する", "In particular, the onboarding flow needs work."),
    ("説明・意見", "Especially when", "特に...の場合", "Especially when + clause", "条件付きで強調する", "This matters especially when users are in a hurry."),
    ("説明・意見", "In general", "一般的に", "In general, + clause", "一般論を述べる", "In general, shorter emails are easier to read."),
    ("説明・意見", "Generally speaking", "一般的に言えば", "Generally speaking, + clause", "大まかな傾向を述べる", "Generally speaking, people prefer simple choices."),
    ("説明・意見", "In many cases", "多くの場合", "In many cases, + clause", "よくある傾向を述べる", "In many cases, the first version is not perfect."),
    ("説明・意見", "In some cases", "場合によっては", "In some cases, + clause", "限定的な場合を示す", "In some cases, a phone call is faster."),
    ("説明・意見", "On the one hand", "一方では", "On the one hand, + clause", "対比の片側を示す", "On the one hand, the tool is powerful."),
    ("説明・意見", "On the other hand", "他方では", "On the other hand, + clause", "対比のもう片側を示す", "On the other hand, it is hard to learn."),
    ("説明・意見", "By contrast", "対照的に", "By contrast, + clause", "強めの対比を示す", "By contrast, the second option is much cheaper."),
    ("説明・意見", "In contrast", "対照的に", "In contrast, + clause", "違いを述べる", "In contrast, last year's results were stable."),
    ("説明・意見", "Compared with", "...と比べて", "Compared with + noun", "比較対象を示す", "Compared with last year, sales are higher."),
    ("説明・意見", "Similar to", "...と似ている", "Similar to + noun", "類似点を示す", "This issue is similar to the one we saw in May."),
    ("説明・意見", "Unlike", "...とは違って", "Unlike + noun", "違いを示す", "Unlike the old version, this one works offline."),
    ("説明・意見", "Even though", "...だけれども", "Even though + clause", "事実を認めつつ対比する", "Even though it is expensive, it saves time."),
    ("説明・意見", "Although", "...ではあるが", "Although + clause", "譲歩を示す", "Although the idea is good, the timing is difficult."),
    ("説明・意見", "Despite", "...にもかかわらず", "Despite + noun/V-ing", "名詞句で譲歩を示す", "Despite the delay, the team stayed calm."),
    ("説明・意見", "In spite of", "...にもかかわらず", "In spite of + noun/V-ing", "やや強く譲歩を示す", "In spite of the risk, they accepted the plan."),
    ("説明・意見", "Regardless of", "...に関係なく", "Regardless of + noun", "条件に左右されないことを示す", "Regardless of the result, we should document the process."),
    ("説明・意見", "As long as", "...する限り", "As long as + clause", "条件を示す", "As long as we start early, we can finish today."),
    ("説明・意見", "Unless", "...でない限り", "Unless + clause", "否定条件を示す", "Unless we get approval, we cannot release it."),
    ("説明・意見", "If possible", "可能であれば", "If possible, + clause", "柔らかく希望条件を示す", "If possible, I would like to meet before noon."),
    ("説明・意見", "If necessary", "必要であれば", "If necessary, + clause", "条件付きの対応を示す", "If necessary, we can add another review step."),
    ("説明・意見", "Depending on", "...によっては", "Depending on + noun", "結果が条件で変わることを示す", "Depending on the feedback, we may change the design."),
    ("説明・意見", "In this case", "この場合", "In this case, + clause", "今のケースに限定して述べる", "In this case, the simplest answer is best."),
    ("説明・意見", "In that sense", "その意味では", "In that sense, + clause", "ある観点で評価する", "In that sense, the experiment was successful."),
    ("説明・意見", "To some extent", "ある程度は", "To some extent, + clause", "部分的な同意や評価を示す", "To some extent, I agree with that view."),
    ("説明・意見", "In a way", "ある意味では", "In a way, + clause", "限定的な見方を示す", "In a way, this mistake helped us learn."),
    ("説明・意見", "More or less", "だいたい", "More or less", "おおよその一致や完了を示す", "The plan is more or less finished."),
    ("説明・意見", "At least", "少なくとも", "At least + clause/number", "最低限の範囲を示す", "At least we know what caused the problem."),
    ("説明・意見", "In short", "要するに", "In short, + clause", "短く結論をまとめる", "In short, we need a clearer goal."),
    ("説明・意見", "To sum up", "まとめると", "To sum up, + clause", "最後に要点をまとめる", "To sum up, the project is on track."),
    ("説明・意見", "Overall", "全体として", "Overall, + clause", "総合評価を述べる", "Overall, the feedback was positive."),
    ("説明・意見", "The problem is", "問題は...です", "The problem is + noun/clause", "問題点を明示する", "The problem is that the instructions are unclear."),
    ("説明・意見", "The challenge is", "課題は...です", "The challenge is + noun/clause", "難所や課題を示す", "The challenge is keeping the process simple."),
    ("説明・意見", "The benefit is", "利点は...です", "The benefit is + noun/clause", "メリットを説明する", "The benefit is that users can start faster."),
    ("説明・意見", "The downside is", "欠点は...です", "The downside is + noun/clause", "デメリットを説明する", "The downside is the extra setup time."),
    ("説明・意見", "It comes down to", "結局...に尽きる", "It comes down to + noun", "本質的な要因に絞る", "It comes down to time and budget."),
    ("説明・意見", "It depends on whether", "...かどうかによる", "It depends on whether + clause", "条件分岐を述べる", "It depends on whether the client accepts the change."),
    ("説明・意見", "What matters is", "重要なのは...です", "What matters is + noun/clause", "重要点を強調する", "What matters is whether people actually use it."),
    ("高頻度コロケーション", "make a decision", "決定する", "make a decision", "選択肢から決める", "We need to make a decision by Friday."),
    ("高頻度コロケーション", "make a mistake", "間違える", "make a mistake", "ミスをする", "It is okay to make a mistake while learning."),
    ("高頻度コロケーション", "make progress", "進歩する、進捗を出す", "make progress", "作業や学習が前に進む", "We made good progress this week."),
    ("高頻度コロケーション", "make sense", "意味をなす、筋が通る", "make sense", "説明や案が理解できる", "Your explanation makes sense to me."),
    ("高頻度コロケーション", "make an effort", "努力する", "make an effort to + verb", "意識して取り組む", "I will make an effort to speak more clearly."),
    ("高頻度コロケーション", "make a difference", "違いを生む、効果がある", "make a difference", "行動が良い影響を与える", "Small changes can make a big difference."),
    ("高頻度コロケーション", "take responsibility", "責任を取る", "take responsibility for + noun", "担当や結果に責任を持つ", "She took responsibility for the final report."),
    ("高頻度コロケーション", "take action", "行動を起こす", "take action", "問題に対して動く", "We need to take action before it gets worse."),
    ("高頻度コロケーション", "take advantage of", "...を活用する、利用する", "take advantage of + noun", "機会や制度をうまく使う", "You should take advantage of the free trial."),
    ("高頻度コロケーション", "take into account", "...を考慮に入れる", "take + noun + into account", "判断時に要素を考慮する", "We should take user feedback into account."),
    ("高頻度コロケーション", "take place", "行われる、起こる", "take place", "イベントや出来事が発生する", "The meeting will take place online."),
    ("高頻度コロケーション", "take time", "時間がかかる", "take time", "完了まで時間を要する", "Learning a language takes time."),
    ("高頻度コロケーション", "take notes", "メモを取る", "take notes", "会議や授業で記録する", "I always take notes during meetings."),
    ("高頻度コロケーション", "take a break", "休憩する", "take a break", "作業を一時停止して休む", "Let us take a break after this section."),
    ("高頻度コロケーション", "take care of", "...の世話をする、対応する", "take care of + noun", "人やタスクを扱う", "I will take care of the reservation."),
    ("高頻度コロケーション", "have a chance", "機会がある", "have a chance to + verb", "何かをする機会がある", "I finally had a chance to read your article."),
    ("高頻度コロケーション", "have trouble", "苦労する", "have trouble + V-ing", "うまくできず困る", "I had trouble finding the right file."),
    ("高頻度コロケーション", "have access to", "...にアクセスできる", "have access to + noun", "資料や場所を使える状態にある", "Do you have access to the shared folder?"),
    ("高頻度コロケーション", "have an impact on", "...に影響を与える", "have an impact on + noun", "結果や人に影響する", "This change will have an impact on our timeline."),
    ("高頻度コロケーション", "have a conversation", "会話する、話し合う", "have a conversation with + person", "人と話して確認する", "We should have a conversation with the client."),
    ("高頻度コロケーション", "do research", "調査する", "do research on + noun", "情報を集めて調べる", "I need to do research on the market."),
    ("高頻度コロケーション", "do business", "取引する", "do business with + company/person", "企業や人と商取引する", "We do business with several local suppliers."),
    ("高頻度コロケーション", "do your best", "最善を尽くす", "do your best", "できる限り頑張る", "Just do your best and learn from the result."),
    ("高頻度コロケーション", "get permission", "許可を得る", "get permission to + verb", "何かをする承認を得る", "We need to get permission before using the logo."),
    ("高頻度コロケーション", "get approval", "承認を得る", "get approval for + noun", "上位者や関係者から承認される", "We need to get approval for the budget."),
    ("高頻度コロケーション", "get feedback", "フィードバックを得る", "get feedback on + noun", "意見や評価を受け取る", "I want to get feedback on the first draft."),
    ("高頻度コロケーション", "get started", "始める", "get started", "作業を開始する", "Let us get started with the first question."),
    ("高頻度コロケーション", "get ready", "準備する", "get ready for + noun", "予定や活動に備える", "We need to get ready for the presentation."),
    ("高頻度コロケーション", "give advice", "助言する", "give advice on + noun", "相手に助言を与える", "Can you give me advice on my resume?"),
    ("高頻度コロケーション", "give feedback", "フィードバックする", "give feedback on + noun", "評価や改善点を伝える", "Please give feedback on the new layout."),
    ("高頻度コロケーション", "give a presentation", "プレゼンをする", "give a presentation", "人前で発表する", "She will give a presentation at the conference."),
    ("高頻度コロケーション", "give someone a hand", "人を手伝う", "give + person + a hand", "相手を手助けする", "Could you give me a hand with these boxes?"),
    ("高頻度コロケーション", "pay attention to", "...に注意を払う", "pay attention to + noun", "重要な点に意識を向ける", "Pay attention to the wording in this email."),
    ("高頻度コロケーション", "pay for", "...の代金を払う", "pay for + noun", "支払い対象を示す", "I will pay for lunch today."),
    ("高頻度コロケーション", "pay off", "報われる、効果が出る", "pay off", "努力や投資が成果につながる", "Your hard work will pay off eventually."),
    ("高頻度コロケーション", "keep in mind", "...を覚えておく、考慮する", "keep + noun + in mind", "判断時に注意点を保持する", "Please keep the deadline in mind."),
    ("高頻度コロケーション", "keep track of", "...を把握し続ける", "keep track of + noun", "変化や数を管理する", "We need to keep track of all expenses."),
    ("高頻度コロケーション", "keep an eye on", "...を見守る、監視する", "keep an eye on + noun", "状況を注意して見る", "Can you keep an eye on the progress?"),
    ("高頻度コロケーション", "stay in touch", "連絡を取り続ける", "stay in touch", "関係を保つ", "Let us stay in touch after the project ends."),
    ("高頻度コロケーション", "stay focused", "集中し続ける", "stay focused", "注意をそらさず作業する", "It is hard to stay focused with so many notifications."),
    ("高頻度コロケーション", "stay up to date", "最新情報を把握している", "stay up to date with + noun", "新しい情報を追い続ける", "I read newsletters to stay up to date."),
    ("高頻度コロケーション", "come up with", "...を思いつく", "come up with + idea/solution", "案や解決策を出す", "We need to come up with a better name."),
    ("高頻度コロケーション", "come to a conclusion", "結論に達する", "come to a conclusion", "検討の末に結論を出す", "After the discussion, we came to a conclusion."),
    ("高頻度コロケーション", "reach a decision", "決定に至る", "reach a decision", "正式に判断を下す", "The committee reached a decision yesterday."),
    ("高頻度コロケーション", "reach out to", "...に連絡する", "reach out to + person", "人に連絡を取る", "I will reach out to the support team."),
    ("高頻度コロケーション", "meet a deadline", "締切に間に合う", "meet a deadline", "期限までに完了する", "We worked late to meet the deadline."),
    ("高頻度コロケーション", "miss a deadline", "締切に遅れる", "miss a deadline", "期限に間に合わない", "We cannot afford to miss another deadline."),
    ("高頻度コロケーション", "set a goal", "目標を設定する", "set a goal", "達成したい目標を決める", "Set a clear goal before you start studying."),
    ("高頻度コロケーション", "set a deadline", "締切を設定する", "set a deadline", "完了期限を決める", "Let us set a deadline for the first draft."),
    ("高頻度コロケーション", "set expectations", "期待値を調整する", "set expectations", "事前に見込みや範囲を伝える", "We should set expectations with the client early."),
    ("高頻度コロケーション", "raise a question", "疑問を提起する", "raise a question", "検討すべき質問を出す", "This result raises an important question."),
    ("高頻度コロケーション", "raise awareness", "認知を高める", "raise awareness of/about + noun", "問題や活動を知ってもらう", "The campaign raised awareness of food waste."),
    ("高頻度コロケーション", "address an issue", "問題に対処する", "address an issue", "問題を取り上げて対応する", "We need to address the issue before launch."),
    ("高頻度コロケーション", "solve a problem", "問題を解決する", "solve a problem", "解決策を実行する", "This feature solves a common problem."),
    ("高頻度コロケーション", "cause a problem", "問題を引き起こす", "cause a problem", "悪い結果の原因になる", "The last-minute change caused a problem."),
    ("高頻度コロケーション", "face a challenge", "課題に直面する", "face a challenge", "難しい状況に向き合う", "Many teams face the same challenge."),
    ("高頻度コロケーション", "play a role", "役割を果たす", "play a role in + noun", "結果や状況に関わる", "Timing played a role in our success."),
    ("高頻度コロケーション", "play an important part", "重要な役割を果たす", "play an important part in + noun", "大きく貢献する", "User feedback played an important part in the redesign."),
    ("高頻度コロケーション", "build trust", "信頼を築く", "build trust", "関係の中で信頼を作る", "Clear communication helps build trust."),
    ("高頻度コロケーション", "build a relationship", "関係を築く", "build a relationship with + person/company", "人や組織との関係を作る", "It takes time to build a strong relationship."),
    ("高頻度コロケーション", "save time", "時間を節約する", "save time", "必要な時間を減らす", "Templates can save time for repeated tasks."),
    ("高頻度コロケーション", "save money", "お金を節約する", "save money", "費用を減らす", "Buying in bulk can save money."),
    ("高頻度コロケーション", "spend time", "時間を使う", "spend time + V-ing/on noun", "活動に時間を費やす", "I spend time reviewing expressions every morning."),
    ("高頻度コロケーション", "waste time", "時間を無駄にする", "waste time + V-ing/on noun", "価値の低いことに時間を使う", "Do not waste time worrying about small mistakes."),
    ("高頻度コロケーション", "reduce costs", "コストを削減する", "reduce costs", "費用を下げる", "Automation can reduce costs over time."),
    ("高頻度コロケーション", "increase sales", "売上を増やす", "increase sales", "販売量や売上を上げる", "The new campaign helped increase sales."),
    ("高頻度コロケーション", "improve quality", "品質を向上させる", "improve quality", "成果物の質を上げる", "Regular reviews improve quality."),
    ("高頻度コロケーション", "provide support", "支援を提供する", "provide support for/to + noun", "人や活動を支援する", "The team provides support for new users."),
    ("高頻度コロケーション", "offer a solution", "解決策を提示する", "offer a solution", "問題への解決案を出す", "This service offers a simple solution."),
    ("高頻度コロケーション", "achieve a goal", "目標を達成する", "achieve a goal", "設定した目標に到達する", "You need a clear plan to achieve a goal."),
]


def assign_source(category: str, expression: str) -> tuple[str, str, str]:
    lowered = expression.lower()
    if expression in EXPLICIT_LOW_EVIDENCE:
        source_id = "PRAGMATIC_HIGH_UTILITY"
    elif any(pattern in lowered for pattern in PHAVE_PATTERNS):
        source_id = "PHAVE_EXISTING"
    elif category == "説明・意見":
        source_id = "AFL_DISCOURSE"
    elif category == "高頻度コロケーション":
        source_id = "CORPUS_COLLOCATION"
    elif category == "仕事・メール":
        source_id = "BUSINESS_CORPUS_REF"
    elif category == "日常会話":
        source_id = "PHRASE_STYLE"
    else:
        source_id = "PRAGMATIC_HIGH_UTILITY"

    source = SOURCE_CATALOG[source_id]
    return source_id, source["level"], source["note"]


def build_rows() -> list[dict[str, str]]:
    rows = []
    for index, (category, expression, meaning, pattern, situation, example) in enumerate(RAW_ROWS, start=1):
        source_id, evidence_level, source_note = assign_source(category, expression)
        rows.append(
            {
                "id": f"E{index:03d}",
                "category": category,
                "source_id": source_id,
                "evidence_level": evidence_level,
                "expression": expression,
                "meaning_ja": meaning,
                "pattern": pattern,
                "situation": situation,
                "example_en": example,
                "prompt_ja": f"{situation}で「{meaning}」と言いたい。",
                "answer_en": expression,
                "source_note": source_note,
            }
        )

    counts = Counter(row["category"] for row in rows)
    if len(rows) != 300:
        raise ValueError(f"Expected 300 rows, got {len(rows)}")
    if dict(counts) != CATEGORY_TARGETS:
        raise ValueError(f"Unexpected category counts: {dict(counts)}")
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def escape_md(value: str) -> str:
    return value.replace("|", "\\|")


def cloze_for(row: dict[str, str]) -> str:
    expression = row["expression"]
    pattern = row["pattern"]
    if expression in pattern:
        cloze = pattern.replace(expression, "___", 1)
    else:
        cloze = f"___ / 型: {pattern}"
    return f"{cloze} / {row['meaning_ja']} / 場面: {row['situation']}"


def write_main_markdown(rows: list[dict[str, str]]) -> None:
    lines = [
        "# 日常仕事頻出表現300",
        "",
        "日常会話、仕事・メール、説明・意見、高頻度コロケーションを、発信で使うことを目的にまとめた表現データベースです。",
        "",
        "覚える単位は `表現単体` ではなく、`型 / 場面 / 例文 / 自作文用プロンプト` です。復習では英語を見て訳すより、状況から英語を出す練習を優先します。",
        "",
    ]

    for category in CATEGORY_TARGETS:
        category_rows = [row for row in rows if row["category"] == category]
        lines.extend(
            [
                f"## {category}",
                "",
                "| ID | 根拠 | 表現 | 意味 | 型 | 場面 | 例文 | 自作文用プロンプト |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in category_rows:
            lines.append(
                "| {id} | {evidence}:{source} | *{expression}* | {meaning} | `{pattern}` | {situation} | {example} | {prompt} |".format(
                    id=row["id"],
                    evidence=escape_md(row["evidence_level"]),
                    source=escape_md(row["source_id"]),
                    expression=escape_md(row["expression"]),
                    meaning=escape_md(row["meaning_ja"]),
                    pattern=escape_md(row["pattern"]),
                    situation=escape_md(row["situation"]),
                    example=escape_md(row["example_en"]),
                    prompt=escape_md(row["prompt_ja"]),
                )
            )
        lines.append("")

    (ROOT / "日常仕事頻出表現300.md").write_text("\n".join(lines), encoding="utf-8")


def write_review_files(rows: list[dict[str, str]]) -> None:
    situation_rows = [
        {
            "id": row["id"],
            "category": row["category"],
            "source_id": row["source_id"],
            "evidence_level": row["evidence_level"],
            "prompt_ja": row["prompt_ja"],
            "answer_en": row["answer_en"],
        }
        for row in rows
    ]
    write_csv(
        REVIEW_DIR / "状況から英語を出す.csv",
        ["id", "category", "source_id", "evidence_level", "prompt_ja", "answer_en"],
        situation_rows,
    )

    cloze_rows = [
        {
            "id": row["id"],
            "category": row["category"],
            "source_id": row["source_id"],
            "evidence_level": row["evidence_level"],
            "question": cloze_for(row),
            "answer_en": row["answer_en"],
        }
        for row in rows
    ]
    write_csv(
        REVIEW_DIR / "穴埋めテスト.csv",
        ["id", "category", "source_id", "evidence_level", "question", "answer_en"],
        cloze_rows,
    )

    meaning_rows = [
        {
            "id": row["id"],
            "category": row["category"],
            "source_id": row["source_id"],
            "evidence_level": row["evidence_level"],
            "expression": row["expression"],
            "example_en": row["example_en"],
            "meaning_ja": row["meaning_ja"],
        }
        for row in rows
    ]
    write_csv(
        REVIEW_DIR / "英語から意味確認.csv",
        ["id", "category", "source_id", "evidence_level", "expression", "example_en", "meaning_ja"],
        meaning_rows,
    )


def write_weekly_test(rows: list[dict[str, str]]) -> None:
    lines = [
        "# 週間テスト",
        "",
        "300表現を12週間で回すためのテストです。各週25表現を対象に、状況から英語を出す、穴埋め、短文作成を行います。",
        "",
        "採点は厳密な和訳ではなく、自然な場面で表現を使えるかを基準にします。",
        "",
    ]

    for week_index in range(12):
        chunk = rows[week_index * 25 : (week_index + 1) * 25]
        lines.extend(
            [
                f"## Week {week_index + 1:02d}: {chunk[0]['id']} - {chunk[-1]['id']}",
                "",
                "### 対象表現",
                "",
                "| ID | 根拠 | 表現 | 意味 |",
                "|---|---|---|---|",
            ]
        )
        for row in chunk:
            lines.append(
                f"| {row['id']} | {row['evidence_level']}:{row['source_id']} | *{escape_md(row['expression'])}* | {escape_md(row['meaning_ja'])} |"
            )

        lines.extend(["", "### A. 状況から英語", ""])
        for number, row in enumerate(chunk[:10], start=1):
            lines.append(f"{number}. {row['id']}: {row['prompt_ja']}")

        lines.extend(["", "### B. 穴埋め", ""])
        for number, row in enumerate(chunk[10:20], start=1):
            lines.append(f"{number}. {row['id']}: {cloze_for(row)}")

        lines.extend(["", "### C. 短文作成", ""])
        for number, row in enumerate(chunk[20:], start=1):
            lines.append(f"{number}. {row['id']}: *{row['expression']}* を使って、自分が実際に言いそうな英文を1文作る。")

        lines.extend(["", "### 解答", ""])
        for row in chunk:
            lines.append(f"- {row['id']}: {row['expression']}")
        lines.append("")

    (ROOT / "週間テスト.md").write_text("\n".join(lines), encoding="utf-8")


def write_source_policy() -> None:
    lines = [
        "# 素材選定方針",
        "",
        "この表現リストは、Web上の任意の「便利フレーズ集」をそのまま採用しない。優先するのは、頻度、コーパス、学術的説明、学習者向け妥当性のいずれかが確認できる素材です。",
        "",
        "## 根拠レベル",
        "",
        "| レベル | 意味 | 扱い |",
        "|---|---|---|",
        "| A | コーパスベースの学術リスト、または既存PHaVE素材で優先順位・代表義が説明されている | 最優先で採用 |",
        "| B | コーパスベース辞書、English Profile型の学習者コーパス/CEFR資料、または学術リストの基準に沿って発信用に再構成 | 採用可。ただし頻度順位そのものとは言わない |",
        "| C | 発信用には有用だが、特定コーパス順位や学術リストでの確認が弱い | 明示して少量だけ採用 |",
        "",
        "## 主な参照先",
        "",
        "- PHaVE List: Garnier & Schmitt, *The PHaVE List: A pedagogical list of phrasal verbs and their most frequent meaning senses*. 句動詞は既存の `phrasal_verb/PHaVE句動詞150.md` とPDFを基礎にする。https://journals.sagepub.com/doi/abs/10.1177/1362168814559798",
        "- PHRASE List: Martinez & Schmitt, *A Phrasal Expressions List*. 多語表現を頻度・非透明性・学習価値で扱う発想を、日常表現の選定基準として使う。https://doi.org/10.1093/applin/ams010",
        "- English Profile / English Vocabulary Profile: CEFR、学習者コーパス、実用機能で語・句・句動詞・イディオムを扱う参照枠として使う。https://www.englishprofile.org/english-vocabulary-profile",
        "- Academic Formulas List 系の研究: 説明、意見、論理展開でよく使う定型表現を選ぶ基準として使う。https://doi.org/10.1093/applin/amp058",
        "- Sketch Engine / SKELL 型のコーパス参照: コロケーションと自然な例文確認の補助として使う。https://skell.sketchengine.eu/",
        "",
        "## 採用しない素材",
        "",
        "- 出典や作成方法がないSEO記事のフレーズ集。",
        "- ことわざ、文学的表現、古い慣用句が多いイディオム集。",
        "- 単語頻度リストだけを根拠にした表現リスト。",
        "- 例文や文型がなく、実際にどう使うか分からないリスト。",
        "",
        "## 順序の扱い",
        "",
        "この300表現は、複数ジャンルを混ぜた厳密な全体頻度順ではありません。全体を一つの頻度順位にすると、会話、メール、説明文、コロケーションのコーパス条件が混ざって不正確になるためです。",
        "",
        "代わりに、各カテゴリ内で `発信での汎用性 / 頻度根拠の強さ / 文型の生産性 / 日本語話者にとっての有用性` を基準に並べています。根拠が弱いものは `evidence_level=C` として明示します。",
        "",
        "## このリストの立場",
        "",
        "この教材は、学術リストや辞書の項目を丸写ししたものではありません。著作権のあるリストの複製を避け、出典で確認できる選定思想に基づいて、日常・仕事の発信に使いやすい代表用法へ再構成しています。",
        "",
        "## Source ID",
        "",
        "| source_id | level | 内容 |",
        "|---|---|---|",
    ]

    for source_id, source in SOURCE_CATALOG.items():
        lines.append(f"| {source_id} | {source['level']} | {source['label']}: {source['note']} |")

    (ROOT / "素材選定方針.md").write_text("\n".join(lines), encoding="utf-8")


def write_guide() -> None:
    guide = """# 運用ガイド

## 目的

このシステムの目的は、表現を「見れば分かる」状態で止めず、日常・仕事の発信で自然に出せる状態にすることです。訳語の暗記より、場面から英語を出す練習を優先します。

素材の選び方は `素材選定方針.md` にまとめています。`evidence_level=A/B/C` を見れば、頻度・コーパス根拠の強さを確認できます。

## 毎日20分

1. 既習復習 7分
   - `review/状況から英語を出す.csv` を使い、日本語の状況から英語表現を出す。
   - 即答できないものは `迷う` として扱い、翌日も出す。
2. 新規投入 6分
   - `日常仕事頻出表現300.md` から3-5件を読む。
   - 型、場面、例文を確認し、表現単体ではなく使う文脈で覚える。
3. 自作文 5分
   - 今日の新規表現から3件選び、自分が実際に言いそうな英文を作る。
   - 仕事・生活・英語学習のどれかに接続すると定着しやすい。
4. 間違い分類 2分
   - 動詞を間違えた
   - 前置詞・副詞を間違えた
   - 意味は分かるが場面が出ない
   - 型や目的語の置き方を間違えた

## 週次テスト

週末に `週間テスト.md` を1週分だけ解きます。対象は25表現です。

- A: 状況から英語を出す
- B: 穴埋めで型を確認する
- C: 自分の文を作る

採点は三段階にします。

- 即答: 3秒以内に出る
- 迷う: 意味は分かるが口や手が止まる
- 使えない: 表現や型が出ない

翌週は `迷う` と `使えない` を優先して復習します。

## 追加ルール

- 1表現につき、最初は代表用法を1つだけ覚える。
- 自分が使う場面が思いつかない表現は後回しでよい。
- 似た表現はまとめて覚えず、1つずつ使える文にする。
- `phrasal_verb/` と `preposition/` は、句動詞や前置詞の意味を深く確認したいときに参照する。
"""
    (ROOT / "運用ガイド.md").write_text(guide, encoding="utf-8")


def main() -> None:
    rows = build_rows()
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(ROOT / "表現データベース.csv", FIELDNAMES, rows)
    write_main_markdown(rows)
    write_review_files(rows)
    write_weekly_test(rows)
    write_guide()
    write_source_policy()
    counts = Counter(row["category"] for row in rows)
    print(f"Generated {len(rows)} expressions")
    for category, count in counts.items():
        print(f"- {category}: {count}")
    evidence_counts = Counter(row["evidence_level"] for row in rows)
    for level, count in sorted(evidence_counts.items()):
        print(f"- evidence {level}: {count}")


if __name__ == "__main__":
    main()
