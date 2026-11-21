#!/usr/bin/env bash
# greeting-card 格式判分脚本：退出码 0 = PASS，非 0 = FAIL
# 检查项（均来自 references/tone-guide.md 的硬性规则）：
#   1. 输出非空且不超过 80 个字符（中文贺卡长度上限）
#   2. 恰好一个 emoji，且位于消息末尾（容忍末尾的变体选择符 FE0F）
#   3. 不含 markdown 符号（# * ` [ ] >）
#   4. 不以 Dear / 亲爱的 开头
#   5. 整段不被引号包裹
# 输入：环境变量 EVAL_FINAL_MESSAGE（Agent 最终回复）
set -euo pipefail

msg="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$msg" ]; then
  echo "FAIL: EVAL_FINAL_MESSAGE 为空"
  exit 1
fi

export EVAL_MSG="$msg"

perl -Mutf8 -MEncode=decode -e '
binmode STDOUT, ":encoding(UTF-8)";
my $m = decode("UTF-8", $ENV{EVAL_MSG} // "");
$m =~ s/\A\s+//;
$m =~ s/\s+\z//;
my @errs;

# 1. 长度上限 80 字符
my $len = length($m);
push @errs, "长度为 $len 字符，超过 80 字上限" if $len > 80;

# 2. 恰好一个 emoji 且在末尾
my @emo = ($m =~ /\p{Extended_Pictographic}/g);
if (@emo != 1) {
  push @errs, "emoji 数量为 " . scalar(@emo) . "，应为恰好 1 个";
} else {
  (my $tail = $m) =~ s/[\x{FE0F}\x{20E3}]+\z//;
  my $last = substr($tail, -1);
  push @errs, "emoji 未出现在消息末尾" unless $last =~ /\p{Extended_Pictographic}/;
}

# 3. 不含 markdown 符号
push @errs, "包含 markdown 符号（# * \` [ ] >）" if $m =~ /[#*`\[\]>]/;

# 4. 不以 Dear / 亲爱的 开头
push @errs, "以 Dear/亲爱的 开头" if $m =~ /\A\s*(Dear|亲爱的)/i;

# 5. 整段不被引号包裹
push @errs, "整段被引号包裹" if $m =~ /\A\s*["\x{201C}].*["\x{201D}]\s*\z/s;

if (@errs) {
  print "FAIL: $_\n" for @errs;
  exit 1;
}
print "PASS: 格式检查全部通过\n";
exit 0;
'
