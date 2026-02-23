"""P.A.R.A. classification engine.

Rule-based classifier that analyzes note title/content and suggests
the best P.A.R.A. category placement.
"""

import re
from dataclasses import dataclass


@dataclass
class Classification:
    category: str
    suggested_path: str
    confidence: float
    reason: str


# P.A.R.A. category definitions with keyword heuristics
_AREA_KEYWORDS = {
    "21_Health": ["健康", "体检", "健身", "饮食", "医疗", "症状", "配镜", "运动", "睡眠"],
    "22_Finance": [
        "财务", "投资", "交易", "股票", "期权", "资产", "税务", "银行",
        "trading", "finance", "期货", "基金", "收益", "量化",
    ],
    "23_Development": ["成长", "学习", "技能", "复盘", "习惯", "计划", "年度"],
    "24_SocialNet": ["人脉", "联系人", "社交", "关系", "networking"],
    "25_Other": ["证件", "合同", "保修", "行政", "护照", "签证"],
}

_RESOURCE_KEYWORDS = {
    "31_Hard_Skills/编程与技术": [
        "编程", "技术", "框架", "算法", "API", "代码", "架构", "部署",
        "python", "javascript", "rust", "docker", "kubernetes",
    ],
    "31_Hard_Skills/工具使用手册": ["工具", "手册", "教程", "配置", "obsidian", "vscode"],
    "31_Hard_Skills/语言": ["英语", "IELTS", "雅思", "语法", "词汇"],
    "32_Soft_Skills/沟通与谈判": ["沟通", "谈判", "说服", "对话"],
    "32_Soft_Skills/演讲与写作": ["演讲", "写作", "表达", "presentation"],
    "32_Soft_Skills/领导力与管理": ["领导", "管理", "团队", "决策"],
    "33_Philosophy": ["哲学", "思考", "逻辑", "存在", "认识论"],
    "34_Inspiration": ["灵感", "创意", "想法", "感悟"],
    "35_Psychoanalysis": ["心理", "精神分析", "拉康", "弗洛伊德", "潜意识"],
    "36_Socio_logic": ["社会", "商业逻辑", "互联网", "经济"],
}

_PROJECT_KEYWORDS = [
    "TODO", "todo", "deadline", "截止", "进度", "里程碑", "sprint",
    "任务", "目标", "计划", "交付", "版本", "发布",
]

_ASSET_KEYWORDS = ["模板", "SOP", "脚本", "snippet", "作品", "演讲稿", "视频"]


class PARAClassifier:
    def classify(self, title: str, content: str) -> list[Classification]:
        """Analyze title + content and return ranked P.A.R.A. suggestions."""
        text = f"{title}\n{content}".lower()
        suggestions: list[Classification] = []

        # Check Projects
        project_score = self._keyword_score(text, _PROJECT_KEYWORDS)
        if project_score > 0.15:
            suggestions.append(Classification(
                category="10_Projects",
                suggested_path=f"10_Projects/{self._safe_name(title)}",
                confidence=min(project_score, 0.95),
                reason=self._matched_keywords(text, _PROJECT_KEYWORDS),
            ))

        # Check Areas
        for sub_key, keywords in _AREA_KEYWORDS.items():
            score = self._keyword_score(text, keywords)
            if score > 0.15:
                suggestions.append(Classification(
                    category=f"20_Areas/{sub_key}",
                    suggested_path=f"20_Areas/{sub_key}/{self._safe_name(title)}.md",
                    confidence=min(score, 0.95),
                    reason=self._matched_keywords(text, keywords),
                ))

        # Check Resources
        for sub_key, keywords in _RESOURCE_KEYWORDS.items():
            score = self._keyword_score(text, keywords)
            if score > 0.15:
                suggestions.append(Classification(
                    category=f"30_Resources/{sub_key}",
                    suggested_path=f"30_Resources/{sub_key}/{self._safe_name(title)}.md",
                    confidence=min(score, 0.95),
                    reason=self._matched_keywords(text, keywords),
                ))

        # Check Assets
        asset_score = self._keyword_score(text, _ASSET_KEYWORDS)
        if asset_score > 0.15:
            suggestions.append(Classification(
                category="40_Assets",
                suggested_path=f"40_Assets/{self._safe_name(title)}.md",
                confidence=min(asset_score, 0.95),
                reason=self._matched_keywords(text, _ASSET_KEYWORDS),
            ))

        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        # Default: Inbox
        if not suggestions:
            suggestions.append(Classification(
                category="00_Inbox",
                suggested_path=f"00_Inbox/{self._safe_name(title)}.md",
                confidence=0.5,
                reason="No strong category match, defaulting to Inbox",
            ))

        return suggestions[:5]

    def _keyword_score(self, text: str, keywords: list[str]) -> float:
        if not keywords:
            return 0.0
        matches = sum(1 for k in keywords if k.lower() in text)
        return min(matches / max(len(keywords) * 0.3, 1), 1.0)

    def _matched_keywords(self, text: str, keywords: list[str]) -> str:
        matched = [k for k in keywords if k.lower() in text]
        if matched:
            return f"Matched keywords: {', '.join(matched[:5])}"
        return "No keyword matches"

    def _safe_name(self, name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        return name.strip()[:100]
