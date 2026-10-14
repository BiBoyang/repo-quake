#!/bin/bash
# 校验贺卡输出的格式不变量：1-3 句、长度合规、恰好一个 emoji 且位于末尾、
# 无 markdown、无包裹引号、不以称呼开头、无越权承诺。
# 约定：退出码 0 = PASS，非 0 = FAIL；被测输出经 $EVAL_FINAL_MESSAGE 注入。
set -u

msg="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$msg" ]; then
  echo "FAIL: empty output"
  exit 1
fi

trimmed=$(printf '%s' "$msg" | sed 's/[[:space:]]*$//')

# emoji 判定：取常用 emoji 码点区间（象形文字、杂项符号、箭头符等）。
emoji_re='[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{2190}-\x{21FF}]'

# 1) 全文恰好一个 emoji，且必须位于消息末尾。
emoji_count=$(printf '%s' "$msg" | perl -CS -ne "print scalar(() = /$emoji_re/g)")
if [ "$emoji_count" != "1" ]; then
  echo "FAIL: expected exactly 1 emoji, got $emoji_count"
  exit 1
fi
last_is_emoji=$(printf '%s' "$trimmed" | perl -CS -ne "chomp; print substr(\$_, -1) =~ /$emoji_re/ ? 1 : 0")
if [ "$last_is_emoji" != "1" ]; then
  echo "FAIL: emoji must be the last character"
  exit 1
fi

# 2) 句数为 1-3 句（按句末标点计数）。
sent_count=$(printf '%s' "$msg" | perl -CS -ne 'print scalar(() = /[\x{3002}\x{FF01}\x{FF1F}!?]|\.(?=\s|$)/g)')
if [ "$sent_count" -lt 1 ] || [ "$sent_count" -gt 3 ]; then
  echo "FAIL: expected 1-3 sentences, got $sent_count"
  exit 1
fi

# 3) 长度：中文为主（CJK 占比 >= 30%）时不超过 80 字，否则不超过 60 词。
cjk_ratio=$(printf '%s' "$msg" | perl -CS -ne 'my $c = () = /[\x{4e00}-\x{9fff}]/g; my $t = length; print $t ? int($c * 100 / $t) : 0')
if [ "$cjk_ratio" -ge 30 ]; then
  char_count=$(printf '%s' "$msg" | perl -CS -ne 'chomp; print length')
  if [ "$char_count" -gt 80 ]; then
    echo "FAIL: Chinese card exceeds 80 chars (got: $char_count)"
    exit 1
  fi
else
  word_count=$(printf '%s' "$msg" | wc -w | tr -d ' ')
  if [ "$word_count" -gt 60 ]; then
    echo "FAIL: English card exceeds 60 words (got: $word_count)"
    exit 1
  fi
fi

# 4) 不使用 markdown：标题、加粗、删除线、代码符、引用块、链接。
if printf '%s' "$msg" | grep -qE '(^#{1,6}[[:space:]]|\*\*|__|~~|`|^[[:space:]]*>|\]\()'; then
  echo "FAIL: markdown formatting detected"
  exit 1
fi

# 5) 不用引号包裹整段文字。
wrapped=$(printf '%s' "$trimmed" | perl -CS -ne '
  chomp;
  my $f = substr($_, 0, 1); my $l = substr($_, -1);
  my %pair = ("\"" => "\"", "\x{201C}" => "\x{201D}", "\x{2018}" => "\x{2019}", "\x{300C}" => "\x{300D}", "\x{300E}" => "\x{300F}", "'"'"'" => "'"'"'");
  print(exists $pair{$f} && $pair{$f} eq $l ? 1 : 0)')
if [ "$wrapped" = "1" ]; then
  echo "FAIL: whole output wrapped in quotes"
  exit 1
fi

# 6) 不以称呼/问候开头（贺卡只输出正文）。
if printf '%s' "$trimmed" | grep -qE '^(亲爱的|Dear|dear|Hi |Hey |您好|你好)'; then
  echo "FAIL: starts with a salutation or greeting"
  exit 1
fi

# 7) 不替用户做未来承诺。
if printf '%s' "$msg" | grep -qE '我会一直|我会永远|我永远|I will always|always be there'; then
  echo "FAIL: promises future actions on behalf of the user"
  exit 1
fi

echo "PASS: card format checks passed"
exit 0
