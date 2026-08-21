"""Agent 自测系统 —— 用例库(可持续扩充)。

每条用例 = 一个会话内依次发送的若干轮,每轮带断言。
断言字段(expect dict,均可选):
  intent        : 意图等于该值(find_person/knowledge_qa/edit/chat/unclear)
  card_type     : 确认卡类型(profile/review/content);None 表示不应出卡
  contains      : [关键词] 回答或卡片文本中命中任意一个
  not_contains  : [关键词] 回答与卡片中不得出现(防编造/防误伤)
  card_contains : [关键词] 确认卡内容必须全部包含
  continuation  : True/False 是否走零 LLM 续接通道
  honest_empty  : True 要求诚实空答且无推荐卡片
  answer_has    : [关键词] 回答正文必须包含(如电话号码)
"""
from __future__ import annotations

CASES: list[dict] = [
    # ============ 找人:明确责任/概念检索 ============
    {"name": "正式责任-DNS", "category": "找人/正式责任",
     "session": [{"q": "谁负责DNS与域名管理",
                  "expect": {"intent": "find_person", "contains": ["湛宇瑞", "红涵浩", "殷瑶杰", "饶思言"]}}]},
    {"name": "英文别名-hadoop", "category": "找人/别名",
     "session": [{"q": "谁负责hadoop",
                  "expect": {"intent": "find_person", "contains": ["林凡然", "方墨川", "阮川宇"]}}]},
    {"name": "英文别名大小写-LLM KEY", "category": "找人/别名",
     "session": [{"q": "申请LLM KEY找谁",
                  "expect": {"intent": "find_person", "contains": ["储安奕", "郝子夏"]}}]},
    {"name": "中文泛词前缀-食堂", "category": "找人/前缀",
     "session": [{"q": "谁负责食堂",
                  "expect": {"intent": "find_person", "contains": ["茅泽婉"]}}]},
    {"name": "办理式问法-出入境", "category": "找人/前缀",
     "session": [{"q": "办理出入境找谁",
                  "expect": {"intent": "find_person", "contains": ["徐轩", "茅泽婉"]}}]},
    {"name": "归并概念-反欺诈", "category": "找人/归并",
     "session": [{"q": "反欺诈谁在做",
                  "expect": {"intent": "find_person", "contains": ["干雪诺", "魏哲若", "梅桐文"]}}]},
    {"name": "技能找人-模型微调", "category": "找人/技能",
     "session": [{"q": "谁懂模型微调",
                  "expect": {"intent": "find_person", "contains": ["邬俊桐", "蓝远", "裘曦", "颜知琪"]}}]},
    {"name": "兴趣找人-篮球", "category": "找人/兴趣",
     "session": [{"q": "谁喜欢打篮球",
                  "expect": {"intent": "find_person", "contains": ["茅泽婉"]}}]},
    {"name": "联系方式", "category": "找人/联系方式",
     "session": [{"q": "茅泽婉的电话是多少",
                  "expect": {"intent": "find_person", "answer_has": ["123312312313"]}}]},
    {"name": "诊断式-服务器资源", "category": "找人/诊断",
     "session": [{"q": "服务器资源不足找谁",
                  "expect": {"intent": "find_person", "contains": ["汪雨宇", "双哲远", "空源怡", "红思嫣"]}}]},

    # ============ 找人:子序列缺字匹配(会议申请→会议室申请) ============
    {"name": "子序列缺字-会议申请", "category": "找人/子序列",
     "session": [{"q": "会议申请找谁", "expect": {"contains": ["茅泽婉"]}}]},

    # ============ 写操作:资料/画像/发布 ============
    {"name": "改联系方式", "category": "写/资料",
     "session": [{"q": "修改我的联系方式为13900000000",
                  "expect": {"card_type": "profile", "card_contains": ["13900000000"]}}]},
    {"name": "改自画像-覆盖", "category": "写/资料",
     "session": [{"q": "修改我的自画像为热爱技术的工程师",
                  "expect": {"card_type": "profile", "card_contains": ["热爱技术的工程师"]}}]},
    {"name": "自画像新增-长句", "category": "写/资料",
     "session": [{"q": "在我的自画像后面新增 米哈游十年老员工",
                  "expect": {"card_type": "profile", "card_contains": ["米哈游十年老员工"]}}]},
    {"name": "自我标签", "category": "写/资料",
     "session": [{"q": "给我自己添加标签：烘焙",
                  "expect": {"card_type": "profile", "card_contains": ["烘焙"]}}]},
    {"name": "负责领域变更", "category": "写/资料",
     "session": [{"q": "我现在负责图数据库",
                  "expect": {"card_type": "profile", "card_contains": ["图数据库"]}}]},
    {"name": "口语化改电话", "category": "写/刁钻",
     "session": [{"q": "我电话换了 换成13911112222",
                  "expect": {"card_type": "profile", "card_contains": ["13911112222"]}}]},
    {"name": "他人画像", "category": "写/画像",
     "session": [{"q": "给徐轩增加标签：量子计算",
                  "expect": {"card_type": "review", "card_contains": ["徐轩", "量子计算"]}}]},
    {"name": "帮我给人打标签", "category": "写/刁钻",
     "session": [{"q": "帮我给徐轩打个标签：靠谱",
                  "expect": {"card_type": "review", "card_contains": ["徐轩", "靠谱"]}}]},
    {"name": "名录无人-张总", "category": "写/刁钻",
     "session": [{"q": "给张总打个标签：负责",
                  "expect": {"no_card": True, "answer_has": ["名录"]}}]},  # 查无此人应澄清,不出卡不指人
    {"name": "发布内容", "category": "写/发布",
     "session": [{"q": "发布一篇文章《投产变更窗口规范》",
                  "expect": {"card_type": "content", "card_contains": ["投产变更窗口规范"]}}]},
    {"name": "发布带正文-标题是", "category": "写/发布",
     "session": [{"q": "我想发布一篇内容标题是rag的介绍， RAG（检索增强生成）是一种把检索和生成结合起来的大模型技术框架。传统大模型依赖训练时固化的参数知识，容易出现信息过时、幻觉和无法引用私有数据的问题。RAG的思路是：在回答前，先从外部知识库中检索出与问题最相关的片段，再把这些片段作为上下文喂给大模型，让它基于真实资料生成答案。",
                  "expect": {"card_type": "content",
                             "card_contains": ["rag的介绍", "检索增强生成", "外部知识库"]}}]},
    {"name": "发布带正文-书名号", "category": "写/发布",
     "session": [{"q": "帮我发一篇文章《变更发布检查单》，正文：变更前必须完成三件事：一是确认回滚方案，二是通知值班同学，三是检查监控告警规则是否生效。",
                  "expect": {"card_type": "content",
                             "card_contains": ["变更发布检查单", "回滚方案", "监控告警"]}}]},

    # ============ 多轮:续接与意图继承 ============
    {"name": "三连追加自画像", "category": "多轮/续接",
     "session": [
         {"q": "把我的自画像改为喜欢玩原神", "expect": {"card_type": "profile", "card_contains": ["喜欢玩原神"]}},
         {"q": "再加一句 也玩崩铁", "expect": {"card_type": "profile", "continuation": True,
                                               "card_contains": ["喜欢玩原神", "也玩崩铁"]}},
         {"q": "再加一局 还有绝区零", "expect": {"card_type": "profile", "continuation": True,
                                                "card_contains": ["绝区零"]}},
     ]},
    {"name": "联系方式替换追问", "category": "多轮/续接",
     "session": [
         {"q": "修改我的联系方式为13800000000", "expect": {"card_type": "profile"}},
         {"q": "换成13900000001", "expect": {"card_type": "profile", "continuation": True,
                                            "card_contains": ["13900000001"]}},
     ]},
    {"name": "他人画像续加标签", "category": "多轮/续接",
     "session": [
         {"q": "给徐轩增加标签：落户管理", "expect": {"card_type": "review", "card_contains": ["落户管理"]}},
         {"q": "再加一个标签 出入境管理", "expect": {"card_type": "review", "continuation": True,
                                                    "card_contains": ["出入境管理"]}},
     ]},
    {"name": "追问补全人名", "category": "多轮/记忆",
     "session": [
         {"q": "徐轩是谁", "expect": {"intent": "find_person"}},
         {"q": "他的电话呢", "expect": {"intent": "find_person"}},
     ]},
    {"name": "防误续接-新话题", "category": "多轮/防误伤",
     "session": [
         {"q": "把我的自画像改为喜欢打球", "expect": {"card_type": "profile"}},
         {"q": "谁负责hadoop", "expect": {"intent": "find_person", "continuation": False,
                                          "contains": ["林凡然", "方墨川", "阮川宇"]}},
     ]},

    # ============ 边界:闲聊与诚实空答 ============
    {"name": "问候", "category": "边界",
     "session": [{"q": "你好", "expect": {"intent": "chat", "answer_has": ["首问必答"]}}]},
    {"name": "无关问题", "category": "边界",
     "session": [{"q": "今天天气怎么样", "expect": {"intent": "chat", "no_card": True}}]},
    {"name": "不存在领域", "category": "边界/诚实空答",
     "session": [{"q": "谁负责量子计算机维修",
                  "expect": {"intent": "find_person", "honest_empty": True}}]},
]
