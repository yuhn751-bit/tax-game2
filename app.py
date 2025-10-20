import streamlit as st
import random
import copy # 기업 객체 복사를 위해 추가
from enum import Enum # Enum 사용을 위해 추가

# --- 0. Enum(열거형) 정의 ---
# (이전과 동일)
class TaxType(str, Enum):
    CORP = "법인세"
    VAT = "부가세"
    COMMON = "공통"

class AttackCategory(str, Enum):
    COST = "비용"
    REVENUE = "수익"
    CAPITAL = "자본"
    COMMON = "공통"

class MethodType(str, Enum):
    INTENTIONAL = "고의적 누락"
    ERROR = "단순 오류"
    CAPITAL_TX = "자본 거래"

# --- 헬퍼 함수: 가독성 개선 ---
def format_krw(amount_in_millions):
    """
    (이전과 동일) 백만원 단위를 '조', '억' 단위의 읽기 쉬운 문자열로 변환합니다.
    """
    if amount_in_millions is None:
        return "N/A"
    try:
        # 1조 (1,000,000 백만원) 이상
        if abs(amount_in_millions) >= 1_000_000:
            return f"{amount_in_millions / 1_000_000:,.1f}조원"
        # 100억 (10,000 백만원) 이상
        elif abs(amount_in_millions) >= 10_000:
            return f"{amount_in_millions / 10_000:,.0f}억원"
        # 1억 (100 백만원) 이상
        elif abs(amount_in_millions) >= 100:
            return f"{amount_in_millions / 100:,.0f}억원" # 이전 오류 수정됨
        # 1억 미만은 백만원 단위로
        else:
            return f"{amount_in_millions:,.0f}백만원"
    except Exception as e:
        return f"{amount_in_millions} (Format Error)"


# --- 1. 기본 데이터 구조 정의 ---
# (이전과 동일)
class Card:
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost

class TaxManCard(Card):
    # (수정) HP 하향 조정됨
    def __init__(self, name, grade_num, position, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost)
        self.grade_num = grade_num
        self.position = position
        self.hp = hp # (개선) 기본 HP 수치 하향 조정
        self.max_hp = hp
        self.focus = focus
        self.analysis = analysis
        self.persuasion = persuasion
        self.evidence = evidence
        self.data = data
        self.ability_name = ability_name
        self.ability_desc = ability_desc
        grade_map = {4: "S", 5: "S", 6: "A", 7: "B", 8: "C", 9: "C"}
        self.grade = grade_map.get(self.grade_num, "C")

class LogicCard(Card):
    def __init__(self, name, description, cost, base_damage, tax_type: list[TaxType], attack_category: list[AttackCategory], text, special_effect=None, special_bonus=None):
        super().__init__(name, description, cost)
        self.base_damage = base_damage
        self.tax_type = tax_type
        self.attack_category = attack_category
        self.text = text
        self.special_effect = special_effect
        self.special_bonus = special_bonus

class EvasionTactic:
    def __init__(self, name, description, total_amount, tax_type: TaxType | list[TaxType], method_type: MethodType, tactic_category: AttackCategory):
        self.name = name
        self.description = description
        self.total_amount = total_amount
        self.exposed_amount = 0
        self.tax_type = tax_type
        self.method_type = method_type
        self.tactic_category = tactic_category
        self.is_cleared = False

class Company:
    def __init__(self, name, size, description, real_case_desc, revenue, operating_income, tax_target, team_hp_damage, tactics, defense_actions):
        self.name = name
        self.size = size
        self.description = description
        self.real_case_desc = real_case_desc
        self.revenue = revenue
        self.operating_income = operating_income
        self.tax_target = tax_target
        self.team_hp_damage = team_hp_damage
        self.current_collected_tax = 0
        self.tactics = tactics
        self.defense_actions = defense_actions # (개선) 더 까다로운 저항 추가

class Artifact:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect

# --- 2. 게임 데이터베이스 (DB) ---

# --- [수정됨] 조사관 DB (신규 3명 추가, 설명/HP 수정) ---
TAX_MAN_DB = {
    # 기존 팀장급 (HP 하향, 설명 수정)
    "lim": TaxManCard(name="임향수", grade_num=4, position="팀장", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10,
                    description="국세청의 핵심 요직을 두루 거친 '조사통의 대부'. 굵직한 대기업 비자금, 불법 증여 조사를 지휘한 경험이 풍부하다.",
                    ability_name="[기획 조사]",
                    ability_desc="전설적인 통찰력. 매 턴 집중력 +1. 팀의 '분석', '데이터' 스탯에 비례해 '비용', '자본' 카드 피해량 증가."),
    "han": TaxManCard(name="한중히", grade_num=5, position="팀장", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9,
                    description="국제조세 분야에서 잔뼈가 굵은 전문가. OECD 파견 경험으로 국제 공조 및 BEPS 프로젝트에 대한 이해가 깊다.",
                    ability_name="[역외탈세 추적]",
                    ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시, 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", grade_num=5, position="팀장", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7,
                    description="세제실 경험을 바탕으로 국세행정 시스템 발전에 기여한 '세제 전문가'. TIS, NTIS 등 과학세정 인프라 구축에 밝다.",
                    ability_name="[TIS 분석]",
                    ability_desc="시스템을 꿰뚫는 힘. '금융거래 분석', '빅데이터 분석' 등 '데이터' 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", grade_num=6, position="팀장", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7,
                    description="서울청장 시절 변칙 상속/증여 조사를 강력하게 지휘했던 경험 많은 조사 전문가. 대기업 조사에 정통하다.",
                    ability_name="[대기업 저격]",
                    ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대지", grade_num=5, position="팀장", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10,
                    description="국세청의 주요 보직을 역임하며 전략적인 세정 운영 능력을 보여준 전문가. 데이터 기반의 대규모 조사 경험이 있다.",
                    ability_name="[부동산 투기 조사]",
                    ability_desc="팀의 '데이터' 스탯이 50 이상일 경우, 턴 시작 시 '금융거래 분석' 카드를 1장 생성하여 손에 넣습니다."),
    "lee_hd": TaxManCard(name="이현동", grade_num=5, position="팀장", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8,
                    description="강력한 추진력으로 조사 분야에서 성과를 낸 '조사통'. 특히 지하경제 양성화와 역외탈세 추적에 대한 의지가 강하다.",
                    ability_name="[지하경제 양성화]",
                    ability_desc="'고의적 누락(Intentional)' 혐의에 대한 모든 공격의 최종 피해량 +20%."),

    # 기존 반장/조사관 (HP 하향, 설명 수정)
    "kim": TaxManCard(name="김철주", grade_num=6, position="조사반장", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5,
                    description="서울청 조사4국에서 '지하경제 양성화' 관련 조사를 다수 수행한 현장 전문가.",
                    ability_name="[압수수색]",
                    ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거(아티팩트)' 추가 획득."),
    "oh": TaxManCard(name="전필성", grade_num=7, position="조사반장", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8,
                    description="[가상] TIS 구축 초기 멤버로 시스템 이해도가 높다. PG사, 온라인 플랫폼 등 신종 거래 분석에 능한 데이터 전문가.",
                    ability_name="[데이터 마이닝]",
                    ability_desc="기본 적출액 70억원 이상인 '데이터' 관련 카드(자금출처조사 등)의 피해량 +15."),
    "jo": TaxManCard(name="조용규", grade_num=7, position="조사반장", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7,
                    description="교육원에서 후배 양성에 힘쓴 경험이 있는 '세법 이론가'. 법리 해석과 판례 분석이 뛰어나다.",
                    ability_name="[세법 교본]",
                    ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우)가 2배로 적용."),
    "park": TaxManCard(name="박지연", grade_num=8, position="일반조사관", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7,
                    description="[가상] 세무사/CPA 동시 합격 후 특채 입직. 방대한 세법 지식을 바탕으로 날카로운 법리 검토 능력을 보여주는 '세법 신동'.",
                    ability_name="[법리 검토]",
                    ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이철수", grade_num=7, position="일반조사관", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5,
                    description="[가상] 갓 임용된 7급 공채 신입. 열정은 넘치지만 아직 경험이 부족하다. 기본기에 충실하며 기초 자료 분석을 담당.",
                    ability_name="[기본기]",
                    ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드의 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원구", grade_num=6, position="조사반장", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6,
                    description="서울청 조사국 등에서 대기업 비자금 등 굵직한 특수 조사를 다룬 경험이 풍부한 '특수 조사의 귀재'.",
                    ability_name="[특수 조사]",
                    ability_desc="'현장 압수수색', '차명계좌 추적' 카드의 비용 -1. (최소 0)"),

    # --- [신규] 현직 기반 캐릭터 3명 ---
    "yoo_jj": TaxManCard(name="유재준", grade_num=6, position="조사반장", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7,
                    description="[현직] 서울청 조사2국에서 대기업 정기 세무조사 및 상속/증여세 조사를 담당하는 관리자. 꼼꼼한 분석과 설득이 강점.",
                    ability_name="[정기 조사 전문]",
                    ability_desc="'단순 오류(Error)' 유형의 혐의 공격 시, 팀 '설득(Persuasion)' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태호", grade_num=6, position="조사반장", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8,
                    description="[현직] 중부청 조사1국에서 대기업/중견기업 심층 기획조사 및 국제거래 조사를 담당. 증거 확보와 데이터 분석 능력이 탁월하다.",
                    ability_name="[심층 기획 조사]",
                    ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거(Evidence)' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전진", grade_num=7, position="일반조사관", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6,
                    description="[현직] 중부청 조사1국 실무 과장. 조사 현장 지휘 경험이 풍부하며, 팀원들의 능력을 끌어내는 데 능숙하다.",
                    ability_name="[실무 지휘]",
                    ability_desc="턴 시작 시, 무작위 아군 조사관 1명의 다음 카드 사용 비용 -1. (본인 제외)")
}

# [과세논리 카드 DB] (이전과 동일)
LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(name="단순 자료 대사", cost=0, base_damage=5, tax_type=[TaxType.VAT, TaxType.CORP], attack_category=[AttackCategory.COMMON], description="매입/매출 자료 단순 비교.", text="자료 대사 기본 습득."),
    "c_tier_02": LogicCard(name="법령 재검토", cost=0, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 1장 뽑기.", text="관련 법령 재검토.", special_effect={"type": "draw", "value": 1}),
    "util_01": LogicCard(name="초과근무", cost=1, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 2장 뽑기.", text="밤샘 근무로 단서 발견!", special_effect={"type": "draw", "value": 2}),
    "basic_01": LogicCard(name="기본 경비 적정성 검토", cost=1, base_damage=10, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="기본 비용 처리 적정성 검토.", text="법인세법 비용 조항 분석."),
    "basic_02": LogicCard(name="단순 경비 처리 오류 지적", cost=1, base_damage=12, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="증빙 미비 경비 지적.", text="증빙 대조 기본 습득."),
    "b_tier_04": LogicCard(name="세금계산서 대사", cost=1, base_damage=15, tax_type=[TaxType.VAT], attack_category=[AttackCategory.REVENUE, AttackCategory.COST], description="매입/매출 세금계산서 합계표 대조.", text="합계표 불일치 확인."),
    "c_tier_03": LogicCard(name="가공 증빙 수취 분석", cost=2, base_damage=15, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.COST], description="실물 없는 증빙 수취 분석.", text="가짜 세금계산서 흐름 파악."),
    "corp_01": LogicCard(name="접대비 한도 초과", cost=2, base_damage=25, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="법정 한도 초과 접대비 손금불산입.", text="법인세법 접대비 조항 습득."),
    "b_tier_03": LogicCard(name="판례 제시", cost=2, base_damage=22, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="유사 오류 판례 제시.", text="대법원 판례 제시.", special_bonus={'target_method': MethodType.ERROR, 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}),
    "b_tier_05": LogicCard(name="인건비 허위 계상", cost=2, base_damage=30, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="미근무 친인척 인건비 처리.", text="급여대장-근무 내역 불일치 확인."),
    "util_02": LogicCard(name="빅데이터 분석", cost=2, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="적 혐의 유형과 일치하는 카드 1장 서치.", text="TIS 빅데이터 패턴 발견!", special_effect={"type": "search_draw", "value": 1}),
    "corp_02": LogicCard(name="업무 무관 자산 비용 처리", cost=3, base_damage=35, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="대표 개인 차량 유지비 등 적발.", text="벤츠 운행일지 확보!", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
    "b_tier_01": LogicCard(name="금융거래 분석", cost=3, base_damage=45, tax_type=[TaxType.CORP], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="의심 자금 흐름 추적.", text="FIU 분석 기법 습득."),
    "b_tier_02": LogicCard(name="현장 압수수색", cost=3, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="현장 방문, 장부-실물 대조.", text="재고 불일치 확인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_02": LogicCard(name="차명계좌 추적", cost=3, base_damage=50, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.REVENUE], description="타인 명의 계좌 수입 추적.", text="차명계좌 흐름 파악.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_01": LogicCard(name="자금출처조사", cost=4, base_damage=90, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="고액 자산가 불분명 자금 출처 추적.", text="수십 개 차명계좌 흐름 파악."),
    "s_tier_01": LogicCard(name="국제거래 과세논리", cost=4, base_damage=65, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="TP 조작, 역외탈세 적발.", text="BEPS 보고서 이해.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "s_tier_02": LogicCard(name="조세피난처 역외탈세", cost=5, base_damage=130, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="SPC 이용 해외 소득 은닉 적발.", text="BVI, 케이맨 SPC 실체 규명.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
}

# [조사도구 DB] (이전과 동일)
ARTIFACT_DB = {
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "vest": Artifact(name="🛡️ 방탄 조끼", description="전투 시작 시 보호막 +30.", effect={"type": "on_battle_start", "value": 30, "subtype": "shield"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]})
}

# --- [수정됨] 기업 DB (까다로운 저항 추가) ---
COMPANY_DB = [
    Company(
        name="(주)가나푸드", size="소규모",
        revenue=5000, operating_income=500, # 50억원 / 5억원
        tax_target=5, team_hp_damage=(5, 10), # 목표 5억원
        description="중소 유통업체. 사장 SNS는 슈퍼카와 명품 사진 가득.",
        real_case_desc="[교육] 소규모 법인은 대표가 법인 자금을 개인 돈처럼 쓰는 경우가 빈번합니다. 법인카드로 명품 구매, 개인 차량 유지비 처리 등은 '업무 무관 비용'으로 손금 불인정되고, 대표 상여 처리되어 소득세가 추가 과세될 수 있습니다.",
        tactics=[
            EvasionTactic("사주 개인적 사용", "...", 3, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("증빙 미비 경비", "...", 2, tax_type=[TaxType.CORP, TaxType.VAT], method_type=MethodType.ERROR, tactic_category=AttackCategory.COST)
        ],
        defense_actions=["담당 세무사가 시간 끌기.", "대표가 '사실무근' 주장.", "경리 직원이 '실수' 변명."]
    ),
    Company(
        name="㈜넥신 (Nexin)", size="중견기업",
        revenue=100000, operating_income=10000, # 1,000억원 / 100억원
        tax_target=20, team_hp_damage=(10, 25), # 목표 20억원
        description="급성장 게임/IT 기업. 복잡한 지배구조와 관계사 거래.",
        real_case_desc="[교육] 2001.7.1. 이후 SW 개발·유지보수 용역은 원칙적으로 과세(10%)입니다. 다만 개별 사안(예: 수출 해당 여부)에 따라 과세·면세 판정 쟁점이 존재하므로 실무 검토가 필요합니다. 또한 특수관계법인(페이퍼컴퍼니)에 용역비를 과다 지급하는 것은 '부당행위계산부인' 대상입니다.",
        tactics=[
            EvasionTactic("과면세 오류", "...", 8, tax_type=TaxType.VAT, method_type=MethodType.ERROR, tactic_category=AttackCategory.REVENUE),
            EvasionTactic("관계사 부당 지원", "...", 12, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["회계법인이 '정상 거래' 주장.", "자료가 '서버 오류'로 삭제 주장 (팀 집중력 -1).", "실무자가 '모른다'며 비협조."] # 집중력 감소
    ),
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업",
        revenue=50000, operating_income=-1000, # 500억원 / -10억원
        tax_target=30, team_hp_damage=(15, 30), # 목표 30억원
        description="전형적인 '자료상'. 가짜 석유 유통, 허위 세금계산서 발행.",
        real_case_desc="[교육] '자료상'은 폭탄업체, 중간 유통 등 여러 단계를 거쳐 허위 세금계산서를 유통시킵니다. 부가세 부당 공제, 가공 경비 계상 등으로 세금을 탈루하며 조세범처벌법상 중범죄입니다.",
        tactics=[
            EvasionTactic("허위 세금계산서 발행", "...", 20, tax_type=TaxType.VAT, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("가공 매출 누락", "...", 10, tax_type=[TaxType.CORP, TaxType.VAT], method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.REVENUE)
        ],
        defense_actions=["대표 해외 도피 (추적 난이도 상승 - 효과 미구현).", "사무실 텅 빔 (페이퍼컴퍼니).", "대포폰/대포통장 외 단서 없음."]
    ),
     Company(
        name="㈜삼숭물산 (Samsoong)", size="대기업",
        revenue=50_000_000, operating_income=2_000_000, # 50조원 / 2조원
        tax_target=1000, team_hp_damage=(20, 40), # 목표 1,000억원
        description="대한민국 최고 대기업. 복잡한 순환출자, 경영권 승계 이슈.",
        real_case_desc="[교육] 대기업 경영권 승계 시 '일감 몰아주기'는 단골 탈루 유형입니다. 총수 일가 보유 비상장 계열사에 이익을 몰아주어 편법 증여합니다. '불공정 합병'으로 지배력을 강화하며 세금 없는 부의 이전을 꾀하기도 합니다.",
        tactics=[
            EvasionTactic("일감 몰아주기", "...", 500, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL),
            EvasionTactic("가공 세금계산서 수취", "...", 300, tax_type=TaxType.VAT, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("불공정 합병", "...", 200, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["최고 로펌 '김&장' 대응팀 꾸림.", "로펌 '정상 경영 활동' 의견서 제출.", "언론에 '과도한 세무조사' 여론전 (팀 체력 -5).", "정치권 통해 조사 중단 압력 (팀 집중력 -2)."] # 체력/집중력 감소 추가
    ),
    Company(
        name="구갈 코리아(유) (Googal)", size="외국계",
        revenue=2_000_000, operating_income=300_000, # 2조원 / 3,000억원
        tax_target=800, team_hp_damage=(15, 30), # 목표 800억원
        description="다국적 IT 기업 한국 지사. '이전가격(TP)' 조작 통한 소득 해외 이전 혐의.",
        real_case_desc="[교육] 다국적 IT 기업은 조세 조약 및 세법 허점을 이용한 공격적 조세회피(ATP) 전략을 사용합니다. 저세율국 자회사에 '경영자문료', '라이선스비' 명목으로 이익을 이전시키는 '이전가격(TP)' 조작이 대표적입니다. OECD 'BEPS 프로젝트' 등 국제 공조로 대응 중입니다.",
        tactics=[
            EvasionTactic("이전가격(TP) 조작", "...", 500, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL),
            EvasionTactic("고정사업장 미신고", "...", 300, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.REVENUE)
        ],
        defense_actions=["미 본사 '영업 비밀' 이유로 자료 제출 거부.", "조세 조약 근거 상호 합의(MAP) 신청 압박.", "자료 영어로만 제출, 번역 지연 (다음 턴 드로우 -1, 효과 미구현)."] # 카드 드로우 방해 추가
    ),
    Company(
        name="(주)씨엔해운 (C&)", size="대기업",
        revenue=10_000_000, operating_income=500_000, # 10조원 / 5,000억원
        tax_target=1500, team_hp_damage=(25, 45), # 목표 1,500억원
        description="'선백왕' 운영 해운사. 조세피난처 페이퍼컴퍼니 이용 탈루 혐의.",
        real_case_desc="[교육] 선박 등 고가 자산 산업은 조세피난처(Tax Haven) SPC를 이용한 역외탈세가 빈번합니다. BVI 등에 페이퍼컴퍼니를 세우고 리스료 수입 등을 빼돌려 국내 세금을 회피합니다. 국제거래조사국의 주요 대상입니다.",
        tactics=[
            EvasionTactic("역외탈세 (SPC)", "...", 1000, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.REVENUE),
            EvasionTactic("선박 취득가액 조작", "...", 500, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["해외 법인 대표 연락 두절.", "이면 계약서 존재 첩보 (핵심 카드 강제 폐기 시도 - 효과 미구현).", "국내 법무팀 '해외 법률 검토 필요' 대응 지연."] # 카드 폐기 시도 추가
    ),
]

# --- 3. 게임 상태 초기화 및 관리 ---
# (이전과 동일)
def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    """
    (이전과 동일) 드래프트에서 선택된 팀장/유물로 게임을 초기화합니다.
    (이전과 동일) 팀원 수를 3명으로 고정합니다.
    """

    seed = st.session_state.get('seed', 0)
    if seed != 0:
        random.seed(seed)
        st.toast(f"ℹ️ RNG 시드 {seed}로 고정됨.")
    else:
        random.seed()

    team_members = []
    team_members.append(chosen_lead)

    # (수정) 신규 캐릭터들이 랜덤 풀에 포함됨
    chief_candidates = [m for m in TAX_MAN_DB.values() if 6 <= m.grade_num <= 7 and "반장" in m.position]
    officer_candidates = [m for m in TAX_MAN_DB.values() if 7 <= m.grade_num <= 8 and "조사관" in m.position]
    remaining_pool = chief_candidates + officer_candidates

    remaining_pool = [m for m in remaining_pool if m not in team_members]

    team_members.extend(random.sample(remaining_pool, min(2, len(remaining_pool))))
    st.session_state.player_team = team_members

    start_deck = [LOGIC_CARD_DB["basic_01"]] * 4 + [LOGIC_CARD_DB["basic_02"]] * 3 + [LOGIC_CARD_DB["b_tier_04"]] * 3 + [LOGIC_CARD_DB["c_tier_03"]] * 2 + [LOGIC_CARD_DB["c_tier_02"]] * 2
    st.session_state.player_deck = random.sample(start_deck, len(start_deck))
    st.session_state.player_hand = []
    st.session_state.player_discard = []

    st.session_state.player_artifacts = [chosen_artifact]

    st.session_state.team_max_hp = sum(member.hp for member in team_members)
    st.session_state.team_hp = st.session_state.team_max_hp
    st.session_state.team_shield = 0

    st.session_state.player_focus_max = sum(member.focus for member in team_members)
    st.session_state.player_focus_current = st.session_state.player_focus_max

    st.session_state.team_stats = {
        "analysis": sum(m.analysis for m in team_members),
        "persuasion": sum(m.persuasion for m in team_members),
        "evidence": sum(m.evidence for m in team_members),
        "data": sum(m.data for m in team_members)
    }
    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "stat_evidence":
                st.session_state.team_stats["evidence"] += artifact.effect["value"]
            elif artifact.effect["subtype"] == "stat_persuasion":
                st.session_state.team_stats["persuasion"] += artifact.effect["value"]

    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None
    st.session_state.bonus_draw = 0

    st.session_state.company_order = random.sample(COMPANY_DB, len(COMPANY_DB))
    st.session_state.game_state = "MAP"

    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0

# --- 4. 게임 로직 함수 ---
# (이하 로직 함수들은 이전 버전과 거의 동일, 일부 능력 로직 수정)

def start_player_turn():
    base_focus = sum(member.focus for member in st.session_state.player_team)
    st.session_state.player_focus_current = base_focus

    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current += 1
        log_message("✨ [기획 조사] 효과로 집중력 +1!", "info")

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_turn_start" and artifact.effect["subtype"] == "focus":
            st.session_state.player_focus_current += artifact.effect["value"]
            log_message(f"✨ {artifact.name} 효과로 집중력 +{artifact.effect['value']}!", "info")

    st.session_state.player_focus_max = st.session_state.player_focus_current

    # (수정) '김대지' 능력 적용 (카드 생성)
    if "김대지" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"] >= 50:
        if 'kim_dj_effect_used' not in st.session_state or st.session_state.kim_dj_effect_used == False:
            st.session_state.player_hand.append(copy.deepcopy(LOGIC_CARD_DB["b_tier_01"])) # 금융거래 분석 (복사본 추가)
            log_message("✨ [부동산 투기 조사] '금융거래 분석' 카드 1장 획득!", "info")
            st.session_state.kim_dj_effect_used = True # 턴당 1회

    # (수정) '전진' 능력 적용 (비용 감소 버프)
    if "전진" in [m.name for m in st.session_state.player_team]:
        eligible_members = [m for m in st.session_state.player_team if m.name != "전진"]
        if eligible_members:
            target_member = random.choice(eligible_members)
            st.session_state.cost_reduction_target = target_member.name # 버프 대상 저장
            log_message(f"✨ [실무 지휘] '{target_member.name}' 조사관의 다음 카드 비용 -1!", "info")
        else:
            st.session_state.cost_reduction_target = None


    cards_to_draw = 4 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0) > 0:
        log_message(f"✨ {ARTIFACT_DB['plan'].name} 효과로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info")
        st.session_state.bonus_draw = 0

    draw_cards(cards_to_draw)
    check_draw_cards_in_hand()
    log_message("--- 플레이어 턴 시작 ---")
    st.session_state.turn_first_card_played = True
    st.session_state.selected_card_index = None

def draw_cards(num_to_draw):
    drawn_cards = []
    for _ in range(num_to_draw):
        if not st.session_state.player_deck:
            if not st.session_state.player_discard:
                log_message("경고: 더 이상 뽑을 카드가 없습니다!", "error")
                break
            log_message("덱이 비어, 버린 카드를 섞습니다.")
            st.session_state.player_deck = random.sample(st.session_state.player_discard, len(st.session_state.player_discard))
            st.session_state.player_discard = []
            if not st.session_state.player_deck:
                log_message("경고: 덱과 버린 덱이 모두 비었습니다!", "error")
                break
        if not st.session_state.player_deck:
             log_message("경고: 카드를 뽑으려 했으나 덱이 비었습니다!", "error")
             break
        card = st.session_state.player_deck.pop()
        drawn_cards.append(card)
    st.session_state.player_hand.extend(drawn_cards)

def check_draw_cards_in_hand():
    cards_to_play_indices = []
    for i, card in enumerate(st.session_state.player_hand):
        # 방금 생성된 카드(예: 김대지 능력)가 바로 뽑히는 오류 방지
        if hasattr(card, 'just_created') and card.just_created:
            card.just_created = False # 플래그 해제
            continue
        if card.cost == 0 and card.special_effect and card.special_effect.get("type") == "draw":
            cards_to_play_indices.append(i)

    cards_to_play_indices.reverse()

    total_draw_value = 0
    for index in cards_to_play_indices:
        if index < len(st.session_state.player_hand):
            card_to_play = st.session_state.player_hand.pop(index)
            st.session_state.player_discard.append(card_to_play)
            log_message(f"✨ [{card_to_play.name}] 효과 발동! 카드 {card_to_play.special_effect.get('value', 0)}장을 뽑습니다.", "info")
            draw_value = card_to_play.special_effect.get('value', 0)

            if "조용규" in [m.name for m in st.session_state.player_team] and card_to_play.name == "법령 재검토":
                 log_message("✨ [세법 교본] 효과로 카드 1장 추가 드로우!", "info")
                 draw_value *= 2

            total_draw_value += draw_value
        else:
             log_message(f"경고: 드로우 카드 처리 중 인덱스 오류 발생 (index: {index})", "error")

    if total_draw_value > 0:
        draw_cards(total_draw_value)

def select_card_to_play(card_index):
    if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 유효하지 않은 카드입니다.", icon="🚨")
        return

    card = st.session_state.player_hand[card_index]
    cost_to_pay = calculate_card_cost(card) # 비용 계산 먼저

    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        return

    if card.special_effect and card.special_effect.get("type") == "search_draw":
        # 사용 즉시 효과 발동
        st.session_state.player_focus_current -= cost_to_pay # 비용 지불
        execute_search_draw(card_index) # 카드 효과 실행 및 손패/버린덱 처리
        st.rerun()
    else:
        # 일반 공격/효과 카드는 선택 상태로 변경
        st.session_state.selected_card_index = card_index
        st.rerun()

def execute_search_draw(card_index):
   # 검색 카드 사용 로직 (비용 지불은 select_card_to_play에서 처리)
   if card_index is None or card_index >= len(st.session_state.player_hand): return

   card = st.session_state.player_hand[card_index] # 사용된 카드 정보
   # 비용 지불 로직은 제거 (select_card_to_play에서 이미 처리)

   st.session_state.turn_first_card_played = False # 첫 카드 사용 플래그

   enemy_tactic_categories = list(set([t.tactic_category for t in st.session_state.current_battle_company.tactics if t.exposed_amount < t.total_amount]))

   if not enemy_tactic_categories:
        log_message("ℹ️ [빅데이터 분석] 분석할 적 혐의가 남아있지 않습니다.", "info")
        # 카드를 버린 덱으로 이동
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        return # 함수 종료

   search_pool = st.session_state.player_deck + st.session_state.player_discard
   random.shuffle(search_pool)

   found_card = None
   for pool_card in search_pool:
        # 이미 손패에 있는 카드는 제외 (무한 루프 방지)
        if pool_card in st.session_state.player_hand: continue

        if pool_card.cost > 0 and AttackCategory.COMMON not in pool_card.attack_category:
             if any(cat in enemy_tactic_categories for cat in pool_card.attack_category):
                 found_card = pool_card
                 break

   if found_card:
        log_message(f"📊 [빅데이터 분석] 적 혐의({', '.join([c.value for c in enemy_tactic_categories])})와 관련된 '{found_card.name}' 카드를 찾았습니다!", "success")
        # 찾은 카드를 손패에 추가
        found_card.just_created = True # 바로 뽑히는 효과 방지용 임시 플래그
        st.session_state.player_hand.append(found_card)
        # 덱 또는 버린 덱에서 찾은 카드 제거
        try: st.session_state.player_deck.remove(found_card)
        except ValueError:
             try: st.session_state.player_discard.remove(found_card)
             except ValueError: log_message("경고: 빅데이터 분석 카드 제거 중 오류 발생", "error")
   else: log_message("ℹ️ [빅데이터 분석] 관련 카드를 찾지 못했습니다...", "info")

   # 사용한 '빅데이터 분석' 카드를 버린 덱으로 이동
   st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))

   # 혹시 새로 뽑은 카드 중에 즉시 발동 드로우 카드가 있는지 확인
   check_draw_cards_in_hand()

def cancel_card_selection():
    st.session_state.selected_card_index = None
    st.rerun()

def calculate_card_cost(card, member_name=None): # (수정) 특정 멤버 대상 여부 확인
    cost_to_pay = card.cost

    # 멤버별 비용 감소 효과
    if "백용호" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name or AttackCategory.CAPITAL in card.attack_category):
        cost_to_pay = max(0, cost_to_pay - 1)

    card_type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name or AttackCategory.COMMON in card.attack_category)
    if "박지연" in [m.name for m in st.session_state.player_team] and st.session_state.get('turn_first_card_played', True) and card_type_match:
        cost_to_pay = max(0, cost_to_pay - 1)

    if "안원구" in [m.name for m in st.session_state.player_team] and card.name in ['현장 압수수색', '차명계좌 추적']:
        cost_to_pay = max(0, cost_to_pay - 1)

    # (수정) '전진' 능력 적용 (버프 대상 멤버가 이 카드를 사용할 경우)
    cost_reduction_target = st.session_state.get('cost_reduction_target')
    # member_name 인자가 주어졌을 때만 적용 (실제 사용 시 멤버 특정 필요)
    if member_name and cost_reduction_target == member_name:
        original_cost = cost_to_pay
        cost_to_pay = max(0, cost_to_pay - 1)
        if cost_to_pay < original_cost:
             log_message(f"✨ [실무 지휘] {member_name}의 카드 비용 -1!", "info")
             st.session_state.cost_reduction_target = None # 버프 사용됨


    # 아티팩트 비용 감소 효과
    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_cost_calculate":
            if card.name in artifact.effect["target_cards"]:
                cost_to_pay = max(0, cost_to_pay + artifact.effect["value"])

    return cost_to_pay


def execute_attack(card_index, tactic_index):
    # --- (중요) '전진' 능력 적용을 위한 수정 ---
    # 카드 사용 시 어떤 멤버의 버프를 사용할지 결정해야 함.
    # 여기서는 가장 간단하게, 현재 선택된 카드 비용 계산 시
    # 버프 대상자의 이름을 임시로 전달하는 방식을 사용.
    # 실제로는 UI에서 멤버를 선택하거나, 자동으로 할당하는 로직 필요.
    # 지금은 임시로 '전진' 버프가 적용된 비용을 다시 계산
    card = st.session_state.player_hand[card_index]
    target_member_name = st.session_state.get('cost_reduction_target')
    cost_to_pay = calculate_card_cost(card, member_name=target_member_name) # 버프 대상자 이름 전달

    # --- 이하 기존 로직 (cost_to_pay 사용 부분만 수정됨) ---
    if card_index is None or card_index >= len(st.session_state.player_hand) or tactic_index >= len(st.session_state.current_battle_company.tactics):
        st.toast("오류: 공격 실행 중 오류가 발생했습니다.", icon="🚨")
        st.session_state.selected_card_index = None
        st.rerun(); return

    # card = st.session_state.player_hand[card_index] # 위에서 이미 정의
    tactic = st.session_state.current_battle_company.tactics[tactic_index]
    company = st.session_state.current_battle_company

    is_tax_match = False
    if TaxType.COMMON in card.tax_type:
        is_tax_match = True
    elif isinstance(tactic.tax_type, list):
        is_tax_match = any(tt in card.tax_type for tt in tactic.tax_type)
    else:
        is_tax_match = tactic.tax_type in card.tax_type

    if not is_tax_match:
        tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
        log_message(f"❌ [세목 불일치!] '{card.name}'(은)는 '{', '.join(tactic_tax_types)}' 혐의에 부적절합니다! (팀 체력 -10)", "error")
        st.session_state.team_hp -= 10
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return

    is_category_match = False
    if AttackCategory.COMMON in card.attack_category:
        is_category_match = True
    else:
        is_category_match = tactic.tactic_category in card.attack_category

    if not is_category_match:
        log_message(f"🚨 [유형 불일치!] '{card.name}'(은)는 '{tactic.tactic_category.value}' 혐의({tactic.name})에 맞지 않는 조사 방식입니다! (팀 체력 -5)", "error")
        st.session_state.team_hp -= 5
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return

    # cost_to_pay = calculate_card_cost(card) # 위에서 이미 계산됨
    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠"); st.session_state.selected_card_index = None; st.rerun(); return

    st.session_state.player_focus_current -= cost_to_pay
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False

    damage = card.base_damage
    team_stats = st.session_state.team_stats # 팀 스탯 참조

    team_bonus = 0
    if any(cat in [AttackCategory.COST, AttackCategory.COMMON] for cat in card.attack_category):
        team_bonus += int(team_stats["analysis"] * 0.5)
    if any(cat == AttackCategory.CAPITAL for cat in card.attack_category):
        team_bonus += int(team_stats["data"] * 1.0)
    if '판례' in card.name:
        team_bonus += int(team_stats["persuasion"] * 1.0)
    if '압수' in card.name:
        team_bonus += int(team_stats["evidence"] * 1.5)

    if team_bonus > 0:
        log_message(f"📈 [팀 스탯 보너스] +{team_bonus}!", "info")
    damage += team_bonus

    # 멤버별 고정 피해 증가
    if "이철수" in [m.name for m in st.session_state.player_team] and card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]:
        damage += 8; log_message("✨ [기본기] +8!", "info")

    if "임향수" in [m.name for m in st.session_state.player_team] and ('분석' in card.name or '자료' in card.name or '추적' in card.name or AttackCategory.CAPITAL in card.attack_category):
        bonus = int(team_stats["analysis"] * 0.1 + team_stats["data"] * 0.1)
        damage += bonus
        log_message(f"✨ [기획 조사] 스탯 비례 피해 +{bonus}!", "info")

    # (수정) '유재준' 능력 적용
    if "유재준" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.ERROR:
         bonus = int(team_stats["persuasion"] / 10)
         if bonus > 0:
              damage += bonus
              log_message(f"✨ [정기 조사 전문] 설득 기반 피해 +{bonus}!", "info")

    # (수정) '김태호' 능력 적용
    if "김태호" in [m.name for m in st.session_state.player_team] and AttackCategory.CAPITAL in card.attack_category:
        bonus = int(team_stats["evidence"] * 0.1)
        if bonus > 0:
            damage += bonus
            log_message(f"✨ [심층 기획 조사] 증거 기반 피해 +{bonus}!", "info")


    # 피해 배율 계산
    bonus_multiplier = 1.0
    if card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        bonus_multiplier = card.special_bonus.get('multiplier', 1.0)
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시":
            bonus_multiplier *= 2; log_message("✨ [세법 교본] '판례 제시' 2배!", "info")
        else:
            log_message(f"🔥 [정확한 지적!] '{card.name}'(이)가 '{tactic.method_type.value}' 유형에 정확히 적중!", "warning")

    if "한중히" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or tactic.method_type == MethodType.CAPITAL_TX):
        bonus_multiplier *= 1.3; log_message("✨ [역외탈세 추적] +30%!", "info")

    if "서영택" in [m.name for m in st.session_state.player_team] and (company.size == "대기업" or company.size == "외국계") and TaxType.CORP in card.tax_type:
        bonus_multiplier *= 1.25; log_message("✨ [대기업 저격] +25%!", "info")

    if "이현동" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.INTENTIONAL:
        bonus_multiplier *= 1.2; log_message("✨ [지하경제 양성화] +20%!", "info")

    final_damage = int(damage * bonus_multiplier)

    # 오버킬 및 세액 계산
    remaining_tactic_hp = tactic.total_amount - tactic.exposed_amount
    damage_to_tactic = min(final_damage, remaining_tactic_hp)
    overkill_damage = final_damage - damage_to_tactic
    overkill_contribution = int(overkill_damage * 0.5)

    tactic.exposed_amount += damage_to_tactic
    company.current_collected_tax += (damage_to_tactic + overkill_contribution)

    # 로그 출력
    if bonus_multiplier >= 2.0: log_message(f"💥 [치명타!] '{card.name}'(이)가 **{final_damage}억원**의 피해를 입혔습니다!", "success")
    elif bonus_multiplier > 1.0: log_message(f"👍 [효과적!] '{card.name}'(이)가 **{final_damage}억원**의 피해를 입혔습니다.", "success")
    else: log_message(f"▶️ [적중] '{card.name}'(이)가 **{final_damage}억원**의 피해를 입혔습니다.", "success")

    if overkill_damage > 0:
        log_message(f"ℹ️ [초과 데미지] {overkill_damage} 중 {overkill_contribution} (50%)만 총 세액에 반영.", "info")

    if tactic.exposed_amount >= tactic.total_amount and not tactic.is_cleared:
        tactic.is_cleared = True; log_message(f"🔥 [{tactic.name}] 혐의를 완전히 적발했습니다! ({tactic.total_amount}억원)", "warning")
        if "벤츠" in card.text: log_message("💬 [현장] 법인소유 벤츠 발견!", "info")
        if "압수수색" in card.name: log_message("💬 [현장] 비밀장부 확보!", "info")

    # 카드 사용 완료 처리
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
    st.session_state.selected_card_index = None
    check_battle_end()
    st.rerun()


def end_player_turn():
    # 턴 종료 시 '김대지', '전진' 효과 플래그 초기화
    if 'kim_dj_effect_used' in st.session_state:
        st.session_state.kim_dj_effect_used = False
    if 'cost_reduction_target' in st.session_state:
        st.session_state.cost_reduction_target = None

    st.session_state.player_discard.extend(st.session_state.player_hand); st.session_state.player_hand = []; st.session_state.selected_card_index = None
    log_message("--- 기업 턴 시작 ---"); enemy_turn()
    if not check_battle_end(): start_player_turn(); st.rerun()

# (enemy_turn, check_battle_end, start_battle, log_message, go_to_next_stage 이전과 동일)
def enemy_turn():
    company = st.session_state.current_battle_company; action_desc = random.choice(company.defense_actions)
    min_dmg, max_dmg = company.team_hp_damage; damage = random.randint(min_dmg, max_dmg)
    damage_to_shield = min(st.session_state.get('team_shield', 0), damage); damage_to_hp = damage - damage_to_shield
    st.session_state.team_shield -= damage_to_shield; st.session_state.team_hp -= damage_to_hp
    log_prefix = "◀️ [기업]"
    if company.size in ["대기업", "외국계"] and "로펌" in action_desc: log_prefix = "◀️ [로펌]"

    # TODO: action_desc 텍스트에 따라 실제 추가 효과(집중력 감소 등) 구현 필요
    # 예: if "집중력 -1" in action_desc: st.session_state.player_focus_max -= 1 ...

    if damage_to_shield > 0: log_message(f"{log_prefix} {action_desc} (🛡️-{damage_to_shield}, ❤️-{damage_to_hp}!)", "error")
    else: log_message(f"◀️ {log_prefix} {action_desc} (팀 사기 저하 ❤️-{damage}!)", "error")

def check_battle_end():
    company = st.session_state.current_battle_company
    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(f"🎉 [조사 승리] 목표 {company.tax_target:,}억원 달성!", "success"); log_message(f"💰 초과 추징 {bonus:,}억원 획득!", "success")
        st.session_state.total_collected_tax += company.current_collected_tax; st.session_state.game_state = "REWARD"
        if st.session_state.player_discard: last_card_text = st.session_state.player_discard[-1].text; st.toast(f"승리! \"{last_card_text}\"", icon="🎉")
        return True
    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0; log_message("‼️ [조사 중단] 팀 체력 소진...", "error"); st.session_state.game_state = "GAME_OVER"; return True
    return False

def start_battle(company_template):
    company = copy.deepcopy(company_template); st.session_state.current_battle_company = company; st.session_state.game_state = "BATTLE"
    st.session_state.battle_log = [f"--- {company.name} ({company.size}) 조사 시작 ---"]

    st.session_state.team_shield = 0; st.session_state.bonus_draw = 0

    for artifact in st.session_state.player_artifacts:
        log_message(f"✨ [조사도구] '{artifact.name}' 효과 준비.", "info")
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "shield":
                shield_gain = artifact.effect["value"]; st.session_state.team_shield += shield_gain; log_message(f"✨ {artifact.name} 보호막 +{shield_gain}!", "info")
            elif artifact.effect["subtype"] == "draw":
                st.session_state.bonus_draw += artifact.effect["value"]

    st.session_state.player_deck.extend(st.session_state.player_discard); st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck))
    st.session_state.player_discard = []; st.session_state.player_hand = []; start_player_turn()

def log_message(message, level="normal"):
    color_map = {"normal": "", "success": "green", "warning": "orange", "error": "red", "info": "blue"}
    if level != "normal": message = f":{color_map[level]}[{message}]"
    st.session_state.battle_log.insert(0, message)
    if len(st.session_state.battle_log) > 30: st.session_state.battle_log.pop()

def go_to_next_stage(add_card=None, heal_amount=0):
    if add_card:
        st.session_state.player_deck.append(add_card)
        st.toast(f"[{add_card.name}] 덱에 추가!", icon="🃏")

    if heal_amount > 0:
        st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount)
        st.toast(f"팀 휴식 (체력 +{heal_amount})", icon="❤️")

    if 'reward_cards' in st.session_state:
        del st.session_state.reward_cards

    st.session_state.game_state = "MAP"
    st.session_state.current_stage_level += 1
    st.rerun()

# --- 5. UI 화면 함수 ---

# (show_main_menu 이전과 동일)
def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---"); st.header("국세청에 오신 것을 환영합니다.")
    st.write("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    # 이미지 URL은 올바르나, 환경에 따라 표시되지 않을 수 있음
    st.image("https://cphoto.asiae.co.kr/listimglink/1/2021071213454415883_1626065144.jpg",
             caption="국세청(세종청사) 전경",
             width=400)

    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="0이 아닌 값을 입력하면 동일한 팀 구성과 보상으로 테스트할 수 있습니다.")

    if st.button("🚨 조사 시작 (신규 게임)", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0)
        if seed != 0: random.seed(seed)

        # (수정) 신규 팀장들이 드래프트 풀에 포함됨
        lead_candidates = [m for m in TAX_MAN_DB.values() if "팀장" in m.position]
        st.session_state.draft_team_choices = random.sample(lead_candidates, min(len(lead_candidates), 3))

        artifact_keys = list(ARTIFACT_DB.keys())
        chosen_artifact_keys = random.sample(artifact_keys, min(len(artifact_keys), 3))
        st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_artifact_keys]

        st.session_state.game_state = "GAME_SETUP_DRAFT"
        st.rerun()

    with st.expander("📖 게임 방법 (필독!)", expanded=True):
        st.markdown("""
        **1. 🎯 게임 목표**
        - 무작위 팀(3명)으로 기업들을 조사하여 **'목표 추징 세액'** 을 달성하면 승리.
        **2. ⚔️ 전투 방식**
        - ❤️ **팀 체력:** 0 되면 패배 (주의: 이전보다 낮아짐!). / 🧠 **집중력:** 카드 사용 자원 (매우 적음).
        **3. ⚠️ 패널티 시스템 (중요!)**
        - **1. 세목 불일치:** `법인세` 카드로 `부가세` 혐의 공격 시 실패, **팀 체력 -10**.
        - **2. 유형 불일치:** `비용` 카드로 `수익` 혐의 공격 시 실패, **팀 체력 -5**.
        - 공격 버튼 `⚠️ (불일치)` 경고 주의! (클릭 불가)
        **4. ✨ 유형 보너스**
        - 혐의에는 `고의적 누락`, `단순 오류`, `자본 거래` 등 **'탈루 유형'** 이 있음.
        - `현장 압수수색`은 '고의적 누락'에 2배, `판례 제시`는 '단순 오류'에 2배.
        """)

# (show_setup_draft_screen 이전과 동일)
def show_setup_draft_screen():
    st.title("👨‍💼 조사팀 구성")
    st.write("조사를 시작하기 전, 팀의 리더와 시작 도구를 선택하세요.")

    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state:
        st.error("드래프트 정보가 없습니다. 메인 메뉴에서 다시 시작해주세요.")
        if st.button("메인 메뉴로"):
            st.session_state.game_state = "MAIN_MENU"
            st.rerun()
        return

    team_choices = st.session_state.draft_team_choices
    artifact_choices = st.session_state.draft_artifact_choices

    st.markdown("---")
    st.subheader("1. 팀장을 선택하세요:")

    # (수정) 신규 팀장들이 선택지에 포함됨
    selected_lead_index = st.radio(
        "팀장 후보",
        options=range(len(team_choices)),
        format_func=lambda i: (
            f"**{team_choices[i].name} ({team_choices[i].grade}급)** | {team_choices[i].description}\n"
            f"   └ **{team_choices[i].ability_name}**: {team_choices[i].ability_desc}"
        ),
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.subheader("2. 시작 조사도구를 선택하세요:")

    selected_artifact_index = st.radio(
        "조사도구 후보",
        options=range(len(artifact_choices)),
        format_func=lambda i: f"**{artifact_choices[i].name}** | {artifact_choices[i].description}",
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True):
        chosen_lead_obj = team_choices[selected_lead_index]
        chosen_artifact_obj = artifact_choices[selected_artifact_index]

        initialize_game(chosen_lead_obj, chosen_artifact_obj)

        del st.session_state.draft_team_choices
        del st.session_state.draft_artifact_choices

        st.rerun()

# (show_map_screen 이전과 동일)
def show_map_screen():
    if 'current_stage_level' not in st.session_state:
        st.warning("게임 상태가 초기화되지 않았습니다. 메인 메뉴로 돌아갑니다.")
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()
        return

    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})"); st.write("조사할 기업 선택:")
    company_list = st.session_state.company_order

    if st.session_state.current_stage_level < len(company_list):
        company = company_list[st.session_state.current_stage_level]
        with st.container(border=True):
            st.subheader(f"🏢 {company.name} ({company.size})"); st.write(company.description)
            col1, col2 = st.columns(2)

            col1.metric("매출액", format_krw(company.revenue))
            col2.metric("영업이익", format_krw(company.operating_income))

            st.warning(f"**예상 턴당 데미지:** {company.team_hp_damage[0]}~{company.team_hp_damage[1]} ❤️")
            st.info(f"**목표 추징 세액:** {company.tax_target:,} 억원 💰")

            with st.expander("Click: 혐의 및 실제 사례 정보"):
                st.info(f"**[교육 정보]**\n{company.real_case_desc}"); st.markdown("---"); st.markdown("**주요 탈루 혐의**")
                for tactic in company.tactics:
                    tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
                    st.markdown(f"- **{tactic.name}** (`{', '.join(tactic_tax_types)}`, `{tactic.method_type.value}`, `{tactic.tactic_category.value}`)")

            if st.button(f"🚨 {company.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(company); st.rerun()
    else:
        st.success("🎉 모든 기업 조사 완료! (데모 종료)"); st.balloons()
        if st.button("🏆 다시 시작"): st.session_state.game_state = "MAIN_MENU"; st.rerun()

# --- [수정됨] show_battle_screen (레이아웃 변경, 팀 정보 제거) ---
def show_battle_screen():
    if not st.session_state.current_battle_company: st.error("오류: 기업 정보 없음."); st.session_state.game_state = "MAP"; st.rerun(); return

    company = st.session_state.current_battle_company
    st.title(f"⚔️ {company.name} 조사 중..."); st.markdown("---")

    # (개선) 레이아웃 변경: 3열 ([기업 정보], [로그/행동], [손패])
    col_company, col_log_action, col_hand = st.columns([1.6, 2.0, 1.4])

    # --- col_left (팀 정보) 제거됨 ---

    with col_company: # 기업 정보 (기존 col_mid)
        st.subheader(f"🏢 {company.name} ({company.size})")
        st.progress(min(1.0, company.current_collected_tax/company.tax_target), text=f"💰 목표 세액: {company.current_collected_tax:,}/{company.tax_target:,} (억원)")
        st.markdown("---"); st.subheader("🧾 탈루 혐의 목록")

        is_card_selected = st.session_state.get("selected_card_index") is not None
        if is_card_selected:
            selected_card = st.session_state.player_hand[st.session_state.selected_card_index]
            st.info(f"**'{selected_card.name}'** 카드로 공격할 혐의 선택:")

        if not company.tactics: st.write("(모든 혐의 적발!)")

        for i, tactic in enumerate(company.tactics):
            tactic_cleared = tactic.exposed_amount >= tactic.total_amount
            with st.container(border=True):
                tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
                st.markdown(f"**{tactic.name}** (`{', '.join(tactic_tax_types)}`/`{tactic.method_type.value}`/`{tactic.tactic_category.value}`)"); st.caption(f"_{tactic.description}_")

                if tactic_cleared: st.progress(1.0, text=f"✅ 적발 완료: {tactic.exposed_amount:,}/{tactic.total_amount:,} (억원)")
                else: st.progress(min(1.0, tactic.exposed_amount/tactic.total_amount), text=f"적발액: {tactic.exposed_amount:,}/{tactic.total_amount:,} (억원)")

                if is_card_selected and not tactic_cleared:
                    selected_card = st.session_state.player_hand[st.session_state.selected_card_index]

                    is_tax_match = False
                    if TaxType.COMMON in selected_card.tax_type: is_tax_match = True
                    elif isinstance(tactic.tax_type, list): is_tax_match = any(tt in selected_card.tax_type for tt in tactic.tax_type)
                    else: is_tax_match = tactic.tax_type in selected_card.tax_type

                    is_category_match = False
                    if AttackCategory.COMMON in selected_card.attack_category: is_category_match = True
                    else: is_category_match = tactic.tactic_category in selected_card.attack_category

                    button_label, button_type = f"🎯 **{tactic.name}** 공격", "primary"
                    help_text = "클릭하여 이 혐의를 공격합니다."

                    if not is_tax_match:
                        button_label, button_type = f"⚠️ (세목 불일치!) {tactic.name}", "secondary"
                        help_text = f"세목 불일치! 이 카드는 '{', '.join(tactic_tax_types)}' 혐의에 사용할 수 없습니다. (페널티: ❤️-10)"
                    elif not is_category_match:
                        button_label, button_type = f"⚠️ (유형 불일치!) {tactic.name}", "secondary"
                        help_text = f"유형 불일치! 이 카드는 '{tactic.tactic_category.value}' 혐의에 사용할 수 없습니다. (페널티: ❤️-5)"

                    is_disabled = not is_tax_match or not is_category_match

                    if st.button(button_label, key=f"attack_tactic_{i}", use_container_width=True, type=button_type, disabled=is_disabled, help=help_text):
                        execute_attack(st.session_state.selected_card_index, i)

    with col_log_action: # 로그, 행동 (기존 col_right 일부)
        st.subheader("📋 조사 기록 (로그)"); log_container = st.container(height=300, border=True)
        for log in st.session_state.battle_log: log_container.markdown(log)

        st.markdown("---"); st.subheader("🕹️ 행동")
        if st.session_state.get("selected_card_index") is not None:
            if st.button("❌ 공격 취소", use_container_width=True, type="secondary"): cancel_card_selection()
        else:
            if st.button("➡️ 턴 종료", use_container_width=True, type="primary"):
                if 'kim_dj_effect_used' in st.session_state:
                    st.session_state.kim_dj_effect_used = False
                if 'cost_reduction_target' in st.session_state:
                    st.session_state.cost_reduction_target = None
                end_player_turn(); st.rerun()

        # --- 덱/버린 덱 탭은 사이드바로 이동 ---

    # --- [신규] col_hand (손패 표시) ---
    with col_hand:
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")
        if not st.session_state.player_hand: st.write("(손패 없음)")
        is_card_selected = st.session_state.get("selected_card_index") is not None

        # 스크롤 가능한 컨테이너 사용 (손패가 많을 경우 대비)
        hand_container = st.container(height=600) # 높이 조절 가능

        with hand_container:
            for i, card in enumerate(st.session_state.player_hand):
                # 카드 표시 로직 (기존 tab1 내용과 동일)
                if i >= len(st.session_state.player_hand): continue
                if card.cost == 0 and card.special_effect and card.special_effect.get("type") == "draw": continue

                # (수정) '전진' 효과 적용 대상자인지 확인하여 임시 비용 계산
                temp_member_name = st.session_state.get('cost_reduction_target') if st.session_state.get('cost_reduction_target') else None
                cost_to_pay = calculate_card_cost(card, member_name=temp_member_name) # 임시 비용 표시용

                can_afford = st.session_state.player_focus_current >= cost_to_pay
                card_color = "blue" if can_afford else "red"
                is_this_card_selected = (st.session_state.get("selected_card_index") == i)

                with st.container(border=True):
                    card_title = f"**{card.name}** | :{card_color}[비용: {cost_to_pay} 🧠]"
                    if is_this_card_selected: card_title = f"🎯 {card_title} (선택됨)"

                    st.markdown(card_title)
                    card_tax_types = [t.value for t in card.tax_type]
                    card_atk_cats = [c.value for c in card.attack_category]
                    st.caption(f"세목: `{'`. `'.join(card_tax_types)}` | 유형: `{'`. `'.join(card_atk_cats)}`")

                    st.write(card.description)
                    st.write(f"**기본 적출액:** {card.base_damage} 억원")
                    if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")

                    button_label = f"선택: {card.name}"
                    if card.special_effect and card.special_effect.get("type") == "search_draw": button_label = f"사용: {card.name}"

                    button_disabled = (not can_afford or (is_card_selected and not is_this_card_selected))
                    button_help = None
                    if not can_afford:
                        button_help = f"집중력이 부족합니다! (필요: {cost_to_pay}, 현재: {st.session_state.player_focus_current})"
                    elif (is_card_selected and not is_this_card_selected):
                        button_help = "다른 카드가 이미 선택되었습니다. 먼저 '공격 취소'를 눌러주세요."

                    if st.button(button_label, key=f"play_card_{i}", use_container_width=True, disabled=button_disabled, help=button_help):
                        select_card_to_play(i) # 선택/사용 함수 호출


# (show_reward_screen, show_reward_remove_screen 이전과 동일)
def show_reward_screen():
    st.header("🎉 조사 승리!"); st.balloons(); company = st.session_state.current_battle_company
    st.success(f"**{company.name}** 조사 완료. 총 {company.current_collected_tax:,}억원 추징."); st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🃏 카드 획득 (택1)", "❤️ 팀 정비", "🗑️ 덱 정비"])

    with tab1:
        st.subheader("🎁 획득할 과세논리 카드 1장 선택")
        if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
            all_cards = list(LOGIC_CARD_DB.values()); reward_pool = [c for c in all_cards if not (c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw")]
            st.session_state.reward_cards = random.sample(reward_pool, min(len(reward_pool), 3))

        cols = st.columns(len(st.session_state.reward_cards))
        for i, card in enumerate(st.session_state.reward_cards):
            with cols[i]:
                with st.container(border=True):
                    card_tax_types = [t.value for t in card.tax_type]
                    card_atk_cats = [c.value for c in card.attack_category]
                    st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠"); st.caption(f"세목:`{'`,`'.join(card_tax_types)}`|유형:`{'`,`'.join(card_atk_cats)}`"); st.write(card.description);
                    st.info(f"**기본 적출액:** {card.base_damage} 억원")
                    if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")

                    if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                        go_to_next_stage(add_card=card)

    with tab2:
        st.subheader("❤️ 팀 체력 회복")
        st.write(f"현재 팀 체력: {st.session_state.team_hp}/{st.session_state.team_max_hp}")
        heal_amount = int(st.session_state.team_max_hp * 0.3)
        if st.button(f"팀 정비 (체력 +{heal_amount} 회복)", use_container_width=True):
            go_to_next_stage(heal_amount=heal_amount)

    with tab3:
        st.subheader("🗑️ 덱에서 기본 카드 1장 제거")
        st.write("덱을 압축하여 더 좋은 카드를 뽑을 확률을 높입니다.")
        st.info("제거 대상: '단순 자료 대사', '기본 경비 적정성 검토', '단순 경비 처리 오류 지적'")
        if st.button("기본 카드 제거하러 가기", use_container_width=True):
            st.session_state.game_state = "REWARD_REMOVE"
            st.rerun()

def show_reward_remove_screen():
    st.header("🗑️ 덱 정비 (카드 제거)")
    st.write("덱에서 제거할 기본 카드 1장을 선택하세요.")

    full_deck = st.session_state.player_deck + st.session_state.player_discard
    basic_card_names = ["단순 자료 대사", "기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]

    removable_cards = {}
    for card in full_deck:
        if card.name in basic_card_names and card.name not in removable_cards:
            removable_cards[card.name] = card

    if not removable_cards:
        st.warning("제거할 수 있는 기본 카드가 덱에 없습니다.")
        if st.button("맵으로 돌아가기"):
            go_to_next_stage()
        return

    cols = st.columns(len(removable_cards))
    for i, (name, card) in enumerate(removable_cards.items()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠")
                st.write(card.description)

                if st.button(f"제거: {card.name}", key=f"remove_{i}", use_container_width=True, type="primary"):
                    try:
                        card_to_remove = next(c for c in st.session_state.player_deck if c.name == name)
                        st.session_state.player_deck.remove(card_to_remove)
                        st.toast(f"덱에서 [{name}] 1장 제거!", icon="🗑️")
                        go_to_next_stage()
                        return
                    except (StopIteration, ValueError):
                        try:
                            card_to_remove = next(c for c in st.session_state.player_discard if c.name == name)
                            st.session_state.player_discard.remove(card_to_remove)
                            st.toast(f"버린 덱에서 [{name}] 1장 제거!", icon="🗑️")
                            go_to_next_stage()
                            return
                        except (StopIteration, ValueError):
                            st.error("오류: 카드를 제거하지 못했습니다.")

    st.markdown("---")
    if st.button("제거 취소 (맵으로 돌아가기)", type="secondary"):
        go_to_next_stage()

# (show_game_over_screen 이전과 동일)
def show_game_over_screen():
    st.header("... 조사 중단 ..."); st.error("팀 체력 소진.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원")
    st.metric("진행 스테이지", f"📍 {st.session_state.current_stage_level + 1}")

    st.image("https://images.unsplash.com/photo-1554224155-16954a151120?ixlib=rb-4.0.3&q=80&w=1080",
             caption="지친 조사관들...",
             width=400)
    if st.button("다시 도전", type="primary", use_container_width=True):
        st.session_state.game_state = "MAIN_MENU"; st.rerun()

# --- [수정됨] show_player_status_sidebar (모든 팀 정보 통합 표시) ---
def show_player_status_sidebar():
    """ 사이드바에 모든 플레이어/팀 상태 정보를 통합하여 표시합니다. """
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황")

        # 기본 상태
        st.metric("💰 총 추징 세액", f"{st.session_state.total_collected_tax:,} 억원")
        st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")
        if st.session_state.game_state == "BATTLE":
             st.metric("🛡️ 현재 팀 보호막", f"{st.session_state.get('team_shield', 0)}")
             st.metric("🧠 현재 집중력", f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}")


        st.markdown("---")

        # 팀 스탯 (Expander)
        with st.expander("📊 팀 스탯", expanded=False):
            stats = st.session_state.team_stats
            st.markdown(f"- **분석력:** {stats['analysis']}")
            st.markdown(f"- **설득력:** {stats['persuasion']}")
            st.markdown(f"- **증거력:** {stats['evidence']}")
            st.markdown(f"- **데이터:** {stats['data']}")

        # 팀원 정보 (Expander)
        st.subheader("👥 팀원 (3명)")
        for member in st.session_state.player_team:
             with st.expander(f"**{member.name}** ({member.grade}급)"):
                 st.write(f"HP:{member.hp}/{member.max_hp}, Focus:{member.focus}")
                 st.info(f"**{member.ability_name}**: {member.ability_desc}")
                 st.caption(f"({member.description})")

        st.markdown("---")

        # 덱 정보 (Expander)
        total_cards = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand)
        st.subheader(f"📚 보유 덱 ({total_cards}장)")
        with st.expander("덱 구성 보기"):
            deck_list = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand; card_counts = {}
            for card in deck_list: card_counts[card.name] = card_counts.get(card.name, 0) + 1
            for name in sorted(card_counts.keys()): st.write(f"- {name} x {card_counts[name]}")
        # 전투 중일 때만 버린 덱 보기 제공 (선택 사항)
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {}
                for card in st.session_state.player_discard: discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not discard_counts: st.write("(버린 카드 없음)")
                for name in sorted(discard_counts.keys()): st.write(f"- {name} x {discard_counts[name]}")


        st.markdown("---"); st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts: st.write("(없음)")
        else:
             for artifact in st.session_state.player_artifacts: st.success(f"- {artifact.name}: {artifact.description}") # 설명 추가

        st.markdown("---")
        if st.button("게임 포기 (메인 메뉴)", use_container_width=True):
            st.session_state.game_state = "MAIN_MENU"; st.rerun()

# --- 6. 메인 실행 로직 ---
# (이전과 동일)
def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")

    if 'game_state' not in st.session_state:
        st.session_state.game_state = "MAIN_MENU"

    running_states = ["MAP", "BATTLE", "REWARD", "REWARD_REMOVE"]
    if st.session_state.game_state in running_states and 'player_team' not in st.session_state:
        st.toast("⚠️ 세션이 만료되어 메인 메뉴로 돌아갑니다.")
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()
        return

    if st.session_state.game_state == "MAIN_MENU":
        show_main_menu()
    elif st.session_state.game_state == "GAME_SETUP_DRAFT":
        show_setup_draft_screen()
    elif st.session_state.game_state == "MAP":
        show_map_screen()
    elif st.session_state.game_state == "BATTLE":
        show_battle_screen()
    elif st.session_state.game_state == "REWARD":
        show_reward_screen()
    elif st.session_state.game_state == "REWARD_REMOVE":
        show_reward_remove_screen()
    elif st.session_state.game_state == "GAME_OVER":
        show_game_over_screen()

    # (수정) 모든 게임 상태에서 사이드바 표시 (메인 메뉴, 게임 오버 제외)
    # 단, 드래프트 화면에서는 표시할 정보가 아직 없으므로 제외
    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER", "GAME_SETUP_DRAFT"] and 'player_team' in st.session_state:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
