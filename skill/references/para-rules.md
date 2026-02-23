# P.A.R.A. Classification Rules

## Category Definitions

### 00_Inbox (收件箱)
- **Purpose**: Temporary holding area for unprocessed information
- **Rule**: Default destination when no clear category match
- **Action**: Should be emptied daily

### 10_Projects (当前项目)
- **Purpose**: Active tasks with clear deadlines and completion criteria
- **Indicators**: TODO, deadline, milestone, sprint, delivery date
- **Rule**: Must have a "done" state. Learning a course, planning a trip = project
- **Lifecycle**: Active → Completed → Archive to `90_Archives`

### 20_Areas (长期责任)
Ongoing responsibilities requiring continuous maintenance:

| Subfolder | Purpose | Keywords |
|-----------|---------|----------|
| 21_Health | 健康管理 | 体检、健身、饮食、医疗 |
| 22_Finance | 财务自由 | 投资、交易、股票、税务、银行 |
| 23_Development | 个人成长 | 学习、复盘、习惯、年度计划 |
| 24_SocialNet | 人脉管理 | 联系人、社交、关系 |
| 25_Other | 行政杂务 | 证件、合同、保修 |

### 30_Resources (能力与知识)
Reference material organized by topic (your library):

| Subfolder | Topics |
|-----------|--------|
| 31_Hard_Skills | 编程、技术、工具、语言学习 |
| 32_Soft_Skills | 沟通、谈判、演讲、领导力 |
| 33_Philosophy | 哲学、逻辑、思考 |
| 34_Inspiration | 灵感、创意、感悟 |
| 35_Psychoanalysis | 精神分析 |
| 36_Socio_logic | 社会学、商业逻辑 |

### 40_Assets (个人资产)
Personal output and reusable artifacts:
- Templates, SOPs, code snippets
- Speeches, videos, articles you created
- Proxy configs, scripts

### 90_Archives (归档)
Museum for completed projects and inactive content:
- `91-94_YYYY_Projects` — by year
- `99_Legacy_Resources` — deprecated reference material

## Naming Convention
Format: `编号_描述_日期/状态`  
Example: `11_项目A_周会记录_20231025.md`

## Maintenance Protocol
- **Daily**: Empty Inbox
- **Weekly**: Review Projects
- **Quarterly**: Archive completed projects
