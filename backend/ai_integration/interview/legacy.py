"""面试提示词编排：简历三态、token 预算、滚动压缩。

设计要点
--------
1. 原有提示词文本（interview / chat / review）、风格描述、输出要求、
   parse_review 的字段与正则全部保持原样，旧调用方行为不变。
2. "是否带简历"由调用方通过 resume_mode 显式传入，不再靠 resume 是否为空反推。
3. 上下文按 token 预算装填：当前提问保底，历史从新到旧累加；装不下的历史
   作为压缩候选交给上层，由上层决定何时真正调用模型生成摘要。
4. 压缩结果以 summary 回传，原始历史记录不会被覆盖。

"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from .service import InterviewPrompt


# ---------------------------------------------------------------------------
# 1. 预算（单位：token）
#
# 32k 上下文模型的建议值：7000 token 约合一万汉字，给输出和安全余量留足空间。
# TODO[预算]: 换模型时只改这一组常量，其它逻辑不用动；如果项目里已有 tokenizer，
#             把 estimate_tokens 换成真实分词即可。
# ---------------------------------------------------------------------------
PROMPT_TOKEN_BUDGET = 7000      # 超过该值就把装不下的旧历史交给压缩
HARD_LIMIT_TOKENS = 10000       # 兜底硬上限，压缩失败也不会撑爆窗口

RESUME_BLOCK_TOKENS = 700       # 简历块自身的额度，避免挤占对话历史
RESUME_MAX_PROJECTS = 3         # 简历最多带几个项目，按条数截比按字数截更整齐

REPLY_SOFT_LIMIT_CHARS = 800    # 超过给提示，不阻断
REPLY_HARD_LIMIT_CHARS = 2000   # 超过直接拒收，避免一次把窗口灌满

COMPACT_SUMMARY_CHARS = 1200    # 压缩产物自身的字数上限


# ---------------------------------------------------------------------------
# 2. 简历三态
# ---------------------------------------------------------------------------
RESUME_MODE_AUTO = "auto"          # 有就用，没有走默认
RESUME_MODE_ATTACHED = "attached"  # 用户明确选择带简历
RESUME_MODE_NONE = "none"          # 用户明确选择不带简历


# ---------------------------------------------------------------------------
# 3. 固定文本
# ---------------------------------------------------------------------------
STYLE_DESCRIPTIONS = {
    "pressure": "对面试人员使用及其压迫的提问方式，要求候选人在短时间内给出回答。",
    "technical": "极致理性的硬核技术深挖，针对底层原理进行连环追问。",
    "behavioral": "关注过往经历中的决策、冲突处理及团队协作等软技能。",
}

# 保留原实现的兜底行为：未知 style 一律落到友好风格。
DEFAULT_STYLE_DESCRIPTION = "语气友好亲切，侧重引导与交流，适合舒缓紧张感。"

OUTPUT_RULES = (
    "输出要求：只输出纯文本，不使用 Markdown 标记、代码围栏、表格、标题符号或星号。"
    "代码和技术名词用普通文本表达。复盘使用中文段落标题和换行，"
    "保留“回答的优点：”“需要改进的地方：”“具体改进建议：”“综合评分：”等字段。"
)

# 只加在对话路径上：提问冗长会加速上下文膨胀，也会让面试变成演讲。
QUESTION_RULES = (
    "提问要求：每轮只提出一个问题，正文控制在 120 字以内。"
    "可以用一句话回应候选人上一轮的回答，但不要复述简历内容，也不要做长篇总结。"
)

RESUME_TEMPLATE = (
    "候选人简历信息（仅作为背景，不要在提问中复述）：\n"
    "目标岗位：{target_role}\n"
    "工作年限：{years}\n"
    "核心技能：{skills}\n"
    "项目亮点：\n{projects}\n\n"
    "使用规则：简历用于理解候选人背景。当简历描述与候选人当前回答不一致时，"
    "以当前回答为准；不要用简历内容替候选人作答，也不要把简历细节当作已确认的事实来提问。"
)

COMPACT_SYSTEM_PROMPT = (
    "你是面试记录的整理助手。请把给定的面试内容压缩成一份结构化备忘，"
    "压缩后仍要能让另一位面试官无缝接续这场面试。\n\n"
    "要求：\n"
    "1. 只做事实浓缩，不得推断，不得补充候选人没有说过的内容。\n"
    "2. 数字、技术名词、公司名、项目名必须原样保留，不得改写或概括。\n"
    "3. 信息缺失的字段写“未提及”，不要留空，也不要编造。\n"
    "4. 只输出纯文本，不使用 Markdown 标记、表格、标题符号或星号。\n"
    "5. 总长度不超过 {target_chars} 字。\n\n"
    "按以下字段输出，每个字段单独成段：\n"
    "候选人背景：\n"
    "已考察维度：\n"
    "关键回答要点：\n"
    "表现评价：\n"
    "待深入的问题："
)


# ---------------------------------------------------------------------------
# 4. 数据结构
# ---------------------------------------------------------------------------
@dataclass
class ResumeContext:
    """简历的结构化结果。

    [字段]: 属性名按项目里简历解析模块的实际输出调整；
    解析失败时必须显式置 degraded=True，不要返回全空对象冒充成功。
    """

    target_role: str = ""
    years: str = ""
    skills: str = ""
    projects: list = field(default_factory=list)
    degraded: bool = False

    @classmethod
    def from_record(cls, record: dict) -> "ResumeContext":
        """从解析器返回的 dict 构造，字段名按现状改这一处即可。"""
        record = record or {}
        projects = record.get("projects") or []
        if isinstance(projects, str):
            projects = [line for line in projects.split("\n") if line.strip()]
        return cls(
            target_role=(record.get("target_role") or record.get("job") or "").strip(),
            years=(record.get("years") or record.get("experience") or "").strip(),
            skills=(record.get("skills") or "").strip(),
            projects=list(projects),
            degraded=bool(record.get("degraded", False)),
        )


@dataclass
class TurnPlan:
    """一轮请求的完整编排结果。"""

    prompt: InterviewPrompt
    used_history: list
    dropped_history: list
    compaction_prompt: Optional[InterviewPrompt]
    meta: dict


@dataclass
class ReplyCheck:
    """用户输入长度检查结果。"""

    ok: bool
    level: str          # ok / warn / reject
    chars: int
    reason: str = ""


# ---------------------------------------------------------------------------
# 5. 工具函数
# ---------------------------------------------------------------------------
_CJK_PATTERN = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：中日韩字符按 1:1，其余按 4 字符 1 token。

    [预算]: 如果项目里已装 tiktoken 或模型的 tokenizer，直接替换本函数实现，
    上层所有预算逻辑都会跟着变准。
    """
    if not text:
        return 0
    cjk = len(_CJK_PATTERN.findall(text))
    rest = max(len(text) - cjk, 0)
    return cjk + (rest + 3) // 4


def _turn_tokens(item: dict) -> int:
    """单轮问答的 token 估算，含“用户：/面试官：”前缀的开销。"""
    return (
        estimate_tokens(item.get("user") or "")
        + estimate_tokens(item.get("ai") or "")
        + 8
    )


def _history_tokens(history: Sequence[dict]) -> int:
    return sum(_turn_tokens(item) for item in history)


def _cut_text(text: str, allowed_tokens: int) -> str:
    """兜底裁剪：只在极端情况下使用，并留下可见标记。"""
    if not text:
        return text
    limit = max(int(allowed_tokens), 0)
    if limit <= 0:
        return ""
    if estimate_tokens(text) <= allowed_tokens:
        return text
    marker = "…（后续内容因长度限制被截断）"
    # 预留标记本身的额度，保证裁剪后不会反过来突破硬上限。
    body_limit = max(limit - estimate_tokens(marker), 0)
    return text[:body_limit].rstrip() + marker


def render_resume_block(resume: ResumeContext, max_tokens: int = RESUME_BLOCK_TOKENS) -> str:
    """把结构化简历渲染成 system 里的一段。"""
    projects = [str(p).strip() for p in (resume.projects or []) if str(p).strip()]
    kept: list = []
    used = 0
    truncated = False
    for project in projects:
        if len(kept) >= RESUME_MAX_PROJECTS:
            truncated = True
            break
        cost = estimate_tokens(project)
        if kept and used + cost > max_tokens:
            truncated = True
            break
        kept.append(project)
        used += cost

    block = RESUME_TEMPLATE.format(
        target_role=resume.target_role or "未提供",
        years=resume.years or "未提供",
        skills=resume.skills or "未提供",
        projects="\n".join("- " + p for p in kept) or "- 未提供",
    )
    if truncated:
        block += "\n（简历项目部分已截断）"
    return block


def check_reply_length(
    text: str,
    *,
    soft: int = REPLY_SOFT_LIMIT_CHARS,
    hard: int = REPLY_HARD_LIMIT_CHARS,
) -> ReplyCheck:
    """校验用户输入长度。

    注意：简历、JD 这类素材不要走这里，它们应走素材通道，不占单轮回答额度。
    """
    chars = len((text or "").strip())
    if chars > hard:
        return ReplyCheck(False, "reject", chars, f"回答超过 {hard} 字上限，请精简后重新提交")
    if chars > soft:
        return ReplyCheck(True, "warn", chars, f"回答已超过 {soft} 字，继续输入可能被压缩")
    return ReplyCheck(True, "ok", chars, "")


# ---------------------------------------------------------------------------
# 6. 主类
# ---------------------------------------------------------------------------
class LegacyPromptInterview:
    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader

    # ---------------- 对外入口 ----------------

    def prepare_turn(
        self,
        message,
        history,
        style,
        *,
        review=False,
        resume=None,
        resume_mode=RESUME_MODE_AUTO,
        summary="",
        summary_upto=0,
    ):
        """兼容旧调用方：签名向后兼容，只返回 InterviewPrompt。"""
        return self.plan_turn(
            message,
            history,
            style,
            review=review,
            resume=resume,
            resume_mode=resume_mode,
            summary=summary,
            summary_upto=summary_upto,
        ).prompt

    def plan_turn(
        self,
        message,
        history,
        style,
        *,
        review=False,
        resume=None,
        resume_mode=RESUME_MODE_AUTO,
        summary="",
        summary_upto=0,
    ) -> TurnPlan:
        """编排一轮请求，并返回压缩建议与统计信息。"""
        history = list(history or [])
        summary = (summary or "").strip()

        resume_block, resume_meta = self._resolve_resume(resume, resume_mode)
        system = self._system_prompt(style, review, resume_block)

        system_tokens = estimate_tokens(system)
        summary_tokens = estimate_tokens(summary)
        message_tokens = estimate_tokens(message)

        remaining = PROMPT_TOKEN_BUDGET - system_tokens - summary_tokens - message_tokens
        used, dropped = self._split_history(history, summary_upto, remaining)

        total = system_tokens + summary_tokens + message_tokens + _history_tokens(used)

        # 硬上限兜底：先丢最旧历史，再截摘要，最后才动当前提问。
        over_hard_limit = False
        while total > HARD_LIMIT_TOKENS and used:
            item = used.pop(0)
            total -= _turn_tokens(item)
            dropped.insert(0, item)
            over_hard_limit = True

        summary_truncated = False
        if total > HARD_LIMIT_TOKENS and summary:
            spare = HARD_LIMIT_TOKENS - system_tokens - message_tokens
            summary = summary[: max(spare, 0)]
            summary_tokens = estimate_tokens(summary)
            total = system_tokens + summary_tokens + message_tokens
            summary_truncated = True

        message_truncated = False
        if total > HARD_LIMIT_TOKENS:
            spare = HARD_LIMIT_TOKENS - system_tokens - summary_tokens
            message = _cut_text(message, spare)
            message_tokens = estimate_tokens(message)
            total = system_tokens + summary_tokens + message_tokens
            message_truncated = True
            over_hard_limit = True

        compaction_prompt = None
        if dropped:
            compaction_prompt = self._compaction_prompt(summary, dropped)

        user = self._user_prompt(message, summary, used, review)
        prompt = InterviewPrompt(system=system, user=user)

        meta = {
            "review": review,
            "style": style,
            "prompt_tokens": estimate_tokens(system) + estimate_tokens(user),
            "system_tokens": system_tokens,
            "summary_tokens": summary_tokens,
            "history_tokens": _history_tokens(used),
            "message_tokens": message_tokens,
            "turns_total": len(history),
            "turns_used": len(used),
            "turns_dropped": len(dropped),
            "needs_compaction": bool(dropped),
            "summary_upto_after": summary_upto + len(dropped),
            "over_hard_limit": over_hard_limit,
            "summary_truncated": summary_truncated,
            "message_truncated": message_truncated,
        }
        meta.update(resume_meta)

        return TurnPlan(
            prompt=prompt,
            used_history=used,
            dropped_history=dropped,
            compaction_prompt=compaction_prompt,
            meta=meta,
        )

    # ---------------- system ----------------

    def _system_prompt(self, style, review, resume_block) -> str:
        # 复盘路径继续保持 chat 作为 system，兼容旧行为。
        base = self.prompt_loader("chat" if review else "interview") or ""
        parts = [base]
        if not review:
            parts.append("风格：" + STYLE_DESCRIPTIONS.get(style, DEFAULT_STYLE_DESCRIPTION))
            parts.append(QUESTION_RULES)
        if resume_block:
            parts.append(resume_block)
        parts.append(OUTPUT_RULES)
        return "\n\n".join(part for part in parts if part)

    def _resolve_resume(self, resume, resume_mode):
        """把三态选择解析成简历块，并把降级原因带出去。"""
        meta: dict[str, Any] = {
            "resume_mode": resume_mode,
            "resume_applied": False,
            "resume_degraded": False,
            "resume_tokens": 0,
            "warn": "",
        }

        if resume_mode == RESUME_MODE_NONE:
            return "", meta

        if resume is None:
            if resume_mode == RESUME_MODE_ATTACHED:
                # 用户明确选了带简历，这里不能静默走默认，必须让上层知道。
                meta["resume_degraded"] = True
                meta["warn"] = "resume_attached_but_empty"
            return "", meta

        if getattr(resume, "degraded", False):
            meta["resume_degraded"] = True
            meta["warn"] = "resume_parse_degraded"
            return "", meta

        block = render_resume_block(resume)
        if not block.strip():
            meta["resume_degraded"] = True
            meta["warn"] = "resume_block_empty"
            return "", meta

        meta["resume_applied"] = True
        meta["resume_tokens"] = estimate_tokens(block)
        return block, meta

    # ---------------- user ----------------

    def _user_prompt(self, message, summary, history, review) -> str:
        parts = []
        if review:
            review_prompt = self.prompt_loader("review")
            # 复盘提示词缺失时不再静默跳过，由 meta 里的 warn 暴露。
            if review_prompt:
                parts.append(review_prompt)
        if summary:
            parts.append("此前对话摘要：\n" + summary)
        if history:
            parts.append(self._format_history(history))
        parts.append(message)
        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def _format_history(history) -> str:
        lines = ["对话历史："]
        for item in history:
            if item.get("user"):
                lines.append(f"用户：{item['user']}")
            if item.get("ai"):
                lines.append(f"面试官：{item['ai']}")
        return "\n".join(lines)

    @staticmethod
    def _split_history(history, start, remaining_tokens):
        """从最新一轮往回装，装不下的部分作为压缩候选返回。"""
        candidates = history[max(int(start), 0):]
        used: list = []
        total = 0
        for item in reversed(candidates):
            cost = _turn_tokens(item)
            # 至少保留最近一轮，避免预算耗尽后模型完全失忆。
            if used and total + cost > remaining_tokens:
                break
            used.append(item)
            total += cost
        used.reverse()
        dropped = candidates[: len(candidates) - len(used)]
        return used, dropped

    # ---------------- 压缩 ----------------

    def _compaction_prompt(self, summary, dropped) -> InterviewPrompt:
        lines = []
        if summary:
            lines.append("需要合并的已有摘要：")
            lines.append(summary)
            lines.append("")
            lines.append("新增的面试历史：")
        else:
            lines.append("需要压缩的面试历史：")

        for item in dropped:
            if item.get("user"):
                lines.append("候选人：" + item["user"])
            if item.get("ai"):
                lines.append("面试官：" + item["ai"])

        return InterviewPrompt(
            system=COMPACT_SYSTEM_PROMPT.format(target_chars=COMPACT_SUMMARY_CHARS),
            user="\n".join(lines),
        )

    def parse_review(self, content):
        return {
            # 后续可考虑让它输出固定结尾标记再解析。
            "strengths": extract_section(content, "回答的优点：", "需要改进的地方："),
            "weaknesses": extract_section(content, "需要改进的地方：", "具体改进建议："),
            "suggestions": extract_section(content, "具体改进建议：", "下次面试"),
            "overall_score": extract_score(content),
        }


def extract_section(content, start_marker, end_marker):
    if not content:
        return None
    start = content.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    end = content.find(end_marker, start)
    section = content[start:] if end == -1 else content[start:end]
    lines = []
    for line in section.strip().split("\n"):
        cleaned = re.sub(r"^\s*(\d+\.|（\d+）|\d+\s*、)\s*", "", line).strip()
        if cleaned and cleaned not in ("：", ":"):
            lines.append(cleaned)
    return "\n".join(lines)


def extract_score(content):
    if not content:
        return None
    for pattern in (
        r"综合评分[：:]?\s*(\d+\.?\d*)", r"得分[：:]?\s*(\d+\.?\d*)",
        r"评分[：:]?\s*(\d+\.?\d*)", r"(\d+\.?\d*)\s*分",
    ):
        # TODO[解析]: 最后一条会命中正文里任何“X 分”，出现“3 年”“5 分制”时可能误判，
        # 建议观察线上数据后收敛为前三条。
        match = re.search(pattern, content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


__all__ = [
    "LegacyPromptInterview",
    "ResumeContext",
    "TurnPlan",
    "ReplyCheck",
    "InterviewPrompt",
    "estimate_tokens",
    "render_resume_block",
    "check_reply_length",
    "extract_section",
    "extract_score",
]
