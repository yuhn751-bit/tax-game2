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
            return f"{amount_in_millions / 100:,.0f}억원"
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
    def __init__(self, name, grade_num, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost)
        self.grade_num = grade_num
        self.hp = hp
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
        self.real_case_desc = real_case_desc # (개선) 교육 정보 강화됨
        self.revenue = revenue
        self.operating_income = operating_income
        self.tax_target = tax_target
        self.team_hp_damage = team_hp_damage
        self.current_collected_tax = 0
        self.tactics = tactics
        self.defense_actions = defense_actions

class Artifact:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect

# --- 2. 게임 데이터베이스 (DB) ---

# --- [수정됨] 조사관 DB (신규 2명 추가, 상태 정보 제거) ---
TAX_MAN_DB = {
    # 기존 인물 (상태 정보 제거)
    "lim": TaxManCard(name="임향수", grade_num=4, description="국세청의 핵심 요직을 두루 거친 '조사통의 대부'. 굵직한 대기업 비자금, 불법 증여 조사를 지휘한 경험이 풍부하다.", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10, ability_name="[기획 조사]", ability_desc="전설적인 통찰력. 매 턴 집중력 +1. 팀의 '분석', '데이터' 스탯에 비례해 '비용', '자본' 카드 피해량 증가."),
    "han": TaxManCard(name="한중히", grade_num=5, description="국제조세 분야에서 잔뼈가 굵은 전문가. OECD 파견 경험으로 국제 공조 및 BEPS 프로젝트에 대한 이해가 깊다.", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9, ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시, 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", grade_num=5, description="세제실 경험을 바탕으로 국세행정 시스템 발전에 기여한 '세제 전문가'. TIS, NTIS 등 과학세정 인프라 구축에 밝다.", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7, ability_name="[TIS 분석]", ability_desc="시스템을 꿰뚫는 힘. '금융거래 분석', '빅데이터 분석' 등 '데이터' 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", grade_num=6, description="서울청장 시절 변칙 상속/증여 조사를 강력하게 지휘했던 경험 많은 조사 전문가. 대기업 조사에 정통하다.", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7, ability_name="[대기업 저격]", ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대지", grade_num=5, description="국세청의 주요 보직을 역임하며 전략적인 세정 운영 능력을 보여준 전문가. 데이터 기반의 대규모 조사 경험이 있다.", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10, ability_name="[부동산 투기 조사]", ability_desc="팀의 '데이터' 스탯이 50 이상일 경우, 턴 시작 시 '금융거래 분석' 카드를 1장 생성하여 손에 넣습니다."),
    "lee_hd": TaxManCard(name="이현동", grade_num=5, description="강력한 추진력으로 조사 분야에서 성과를 낸 '조사통'. 특히 지하경제 양성화와 역외탈세 추적에 대한 의지가 강하다.", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8, ability_name="[지하경제 양성화]", ability_desc="'고의적 누락(Intentional)' 혐의에 대한 모든 공격의 최종 피해량 +20%."),
    "kim": TaxManCard(name="김철주", grade_num=6, description="서울청 조사4국에서 '지하경제 양성화' 관련 조사를 다수 수행한 현장 전문가.", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5, ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거(아티팩트)' 추가 획득."),
    "oh": TaxManCard(name="전필성", grade_num=7, description="TIS 구축 초기 멤버로 시스템 이해도가 높다. PG사, 온라인 플랫폼 등 신종 거래 분석에 능한 데이터 전문가.", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8, ability_name="[데이터 마이닝]", ability_desc="기본 적출액 70억원 이상인 '데이터' 관련 카드(자금출처조사 등)의 피해량 +15."),
    "jo": TaxManCard(name="조용규", grade_num=7, description="교육원에서 후배 양성에 힘쓴 경험이 있는 '세법 이론가'. 법리 해석과 판례 분석이 뛰어나다.", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7, ability_name="[세법 교본]", ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우)가 2배로 적용."),
    "park": TaxManCard(name="박지연", grade_num=8, description="세무사/CPA 동시 합격 후 특채 입직. 방대한 세법 지식을 바탕으로 날카로운 법리 검토 능력을 보여주는 '세법 신동'.", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7, ability_name="[법리 검토]", ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이철수", grade_num=7, description="갓 임용된 7급 공채 신입. 열정은 넘치지만 아직 경험이 부족하다. 기본기에 충실하며 기초 자료 분석을 담당.", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5, ability_name="[기본기]", ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드의 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원구", grade_num=6, description="서울청 조사국 등에서 대기업 비자금 등 굵직한 특수 조사를 다룬 경험이 풍부한 '특수 조사의 귀재'.", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6, ability_name="[특수 조사]", ability_desc="'현장 압수수색', '차명계좌 추적' 카드의 비용 -1. (최소 0)"),
    "yoo_jj": TaxManCard(name="유재준", grade_num=6, description="서울청 조사2국에서 대기업 정기 세무조사 및 상속/증여세 조사를 담당하는 관리자. 꼼꼼한 분석과 설득이 강점.", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7, ability_name="[정기 조사 전문]", ability_desc="'단순 오류(Error)' 유형의 혐의 공격 시, 팀 '설득(Persuasion)' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태호", grade_num=6, description="중부청 조사1국에서 대기업/중견기업 심층 기획조사 및 국제거래 조사를 담당. 증거 확보와 데이터 분석 능력이 탁월하다.", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8, ability_name="[심층 기획 조사]", ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거(Evidence)' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전진", grade_num=7, description="중부청 조사1국 실무 과장. 조사 현장 지휘 경험이 풍부하며, 팀원들의 능력을 끌어내는 데 능숙하다.", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6, ability_name="[실무 지휘]", ability_desc="턴 시작 시, 무작위 아군 팀원 1명의 다음 카드 사용 비용 -1. (본인 제외)"),

    # --- [신규] 캐릭터 2명 추가 ---
    "kang_ms": TaxManCard(name="강민수", grade_num=5, description="서울지방국세청장. 조사, 법인 등 다양한 분야의 실무와 정책 경험을 겸비. 빅데이터 분석 활용에 능하다.", cost=0, hp=95, focus=3, analysis=8, persuasion=8, evidence=7, data=10, ability_name="[빅데이터 활용]", ability_desc="'빅데이터 분석' 카드 사용 시, 2장 중 1장을 선택하여 가져옵니다."),
    "kim_cg": TaxManCard(name="김창기", grade_num=4, description="현 국세청장. 세제실과 국세청의 주요 보직을 거치며 정책과 실무 모두에 정통. 공정과 상식에 기반한 세정 운영을 강조한다.", cost=0, hp=110, focus=3, analysis=9, persuasion=9, evidence=9, data=9, ability_name="[공정 과세]", ability_desc="전투 승리 시, 목표 세액 초과분의 10%만큼 추가로 팀 체력을 회복합니다."),
}


# [과세논리 카드 DB] (이전과 동일)
LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(name="단순 자료 대사", cost=0, base_damage=5, tax_type=[TaxType.VAT, TaxType.CORP], attack_category=[AttackCategory.COMMON], description="매입/매출 자료 단순 비교.", text="자료 대사 기본 습득."),
    "c_tier_02": LogicCard(name="법령 재검토", cost=0, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 1장 뽑기.", text="관련 법령 재검토.", special_effect={"type": "draw", "value": 1}),
    "util_01": LogicCard(name="초과근무", cost=1, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 2장 뽑기.", text="밤샘 근무로 단서 발견!", special_effect={"type": "draw", "value": 2}),
    "basic_01": LogicCard(name="기본 경비 적정성 검토", cost=1, base_damage=10, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="기본 비용 처리 적정성 검토.", text="법인세법 비용 조항 분석."),
    "basic_02": LogicCard(name="단순 경비 처리 오류 지적", cost=1, base_damage=12, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="증빙 미비 경비 지적.", text="증빙 대조 기본 습득."),
    "b_tier_04": LogicCard(name="세금계산서 대사", cost=1, base_damage=15, tax_type=[TaxType.VAT], attack_category=[AttackCategory.REVENUE, AttackCategory.COST], description="매입/매출 세금계산서 합계표 대조.", text="합계표 불일치 확인."),
    "c_tier_03": LogicCard(name="가공 증빙 수취 분석", cost=2, base_damage=15, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.COST], description="실물 거래 없이 세금계산서만 수취한 정황을 분석합니다.", text="가짜 세금계산서 흐름 파악."),
    "corp_01": LogicCard(name="접대비 한도 초과", cost=2, base_damage=25, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="법정 한도를 초과한 접대비를 비용으로 처리한 부분을 지적합니다.", text="법인세법 접대비 조항 습득."),
    "b_tier_03": LogicCard(name="판례 제시", cost=2, base_damage=22, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="유사한 탈루 또는 오류 사례에 대한 과거 판례를 제시하여 설득합니다.", text="대법원 판례 제시.", special_bonus={'target_method': MethodType.ERROR, 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}),
    "b_tier_05": LogicCard(name="인건비 허위 계상", cost=2, base_damage=30, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="실제 근무하지 않는 친인척 등에게 급여를 지급한 것처럼 꾸며 비용 처리한 것을 적발합니다.", text="급여대장-근무 내역 불일치 확인."),
    "util_02": LogicCard(name="빅데이터 분석", cost=2, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="적 혐의 유형과 일치하는 카드 1장 서치.", text="TIS 빅데이터 패턴 발견!", special_effect={"type": "search_draw", "value": 1}),
    "corp_02": LogicCard(name="업무 무관 자산 비용 처리", cost=3, base_damage=35, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="대표이사 개인 차량 유지비, 가족 해외여행 경비 등 업무와 관련 없는 비용을 법인 비용으로 처리한 것을 적발합니다.", text="벤츠 운행일지 확보!", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
    "b_tier_01": LogicCard(name="금융거래 분석", cost=3, base_damage=45, tax_type=[TaxType.CORP], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="의심스러운 자금 흐름을 추적하여 숨겨진 수입이나 부당한 자본 거래를 포착합니다.", text="FIU 분석 기법 습득."),
    "b_tier_02": LogicCard(name="현장 압수수색", cost=3, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="조사 현장을 방문하여 장부와 실제 재고, 자산 등을 대조하고 숨겨진 자료를 확보합니다.", text="재고 불일치 확인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_02": LogicCard(name="차명계좌 추적", cost=3, base_damage=50, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.REVENUE], description="타인 명의로 개설된 계좌를 통해 수입 금액을 은닉한 정황을 포착하고 자금 흐름을 추적합니다.", text="차명계좌 흐름 파악.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_01": LogicCard(name="자금출처조사", cost=4, base_damage=90, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="고액 자산가의 자산 형성 과정에서 불분명한 자금의 출처를 소명하도록 요구하고, 탈루 혐의를 조사합니다.", text="수십 개 차명계좌 흐름 파악."),
    "s_tier_01": LogicCard(name="국제거래 과세논리", cost=4, base_damage=65, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="이전가격 조작, 고정사업장 회피 등 국제거래를 이용한 조세회피 전략을 분석하고 과세 논리를 개발합니다.", text="BEPS 보고서 이해.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "s_tier_02": LogicCard(name="조세피난처 역외탈세", cost=5, base_damage=130, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="조세피난처에 설립된 특수목적회사(SPC) 등을 이용하여 해외 소득을 은닉한 역외탈세 혐의를 조사합니다.", text="BVI, 케이맨 SPC 실체 규명.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
}

# --- [수정됨] 조사도구 DB (신규 2개 추가) ---
ARTIFACT_DB = {
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "vest": Artifact(name="🛡️ 방탄 조끼", description="전투 시작 시 보호막 +30.", effect={"type": "on_battle_start", "value": 30, "subtype": "shield"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]}),
    # --- [신규] 아티팩트 2개 ---
    "analysis_report": Artifact(name="📑 압수물 분석 보고서", description="팀 '분석(Analysis)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_analysis"}),
    "expert_advice": Artifact(name="👨‍⚖️ 외부 전문가 자문", description="턴 시작 시 20% 확률로 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus_chance", "chance": 0.2})
}


# --- [수정됨] 기업 DB (교육 정보 강화) ---
COMPANY_DB = [
    Company(
        name="(주)가나푸드", size="소규모",
        revenue=5000, operating_income=500, tax_target=5, team_hp_damage=(5, 10),
        description="중소 유통업체. 사장 SNS는 슈퍼카와 명품 사진 가득.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 업무 무관 경비 및 증빙 관리]**\n"
            "법인이 사업과 직접 관련 없이 지출한 비용(예: 대표 개인 물품 구매, 가족 경비)은 법인세법상 손금(비용)으로 인정되지 않습니다(법인세법 제27조). "
            "해당 지출액은 대표자의 소득(상여)으로 간주되어 소득세가 추가 과세될 수 있습니다(소득세법 제20조).\n"
            "**조사 착안 사항:** 법인 신용카드 사용 내역 중 개인적 사용이 의심되는 항목(백화점, 골프장, 해외 사용 등), 차량 운행 일지, 접대비 지출 증빙 등을 면밀히 검토합니다. "
            "모든 비용 지출은 적격 증빙(세금계산서, 계산서, 신용카드 매출전표, 현금영수증 등)을 구비해야 하며(법인세법 제116조), 증빙이 없거나 사실과 다른 경우 비용 불인정 및 가산세가 부과될 수 있습니다."
        ),
        tactics=[
            EvasionTactic("사주 개인적 사용", "대표가 배우자 명의 외제차 리스료 월 500만원 법인 처리, 주말 골프 비용, 자녀 학원비 등 법인카드로 결제.", 3, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("증빙 미비 경비", "실제 거래 없이 서류상 거래처 명절 선물 1천만원 꾸미고, 관련 증빙(세금계산서, 입금표) 제시 못함.", 2, tax_type=[TaxType.CORP, TaxType.VAT], method_type=MethodType.ERROR, tactic_category=AttackCategory.COST)
        ],
        defense_actions=["담당 세무사가 시간 끌기.", "대표가 '사실무근' 주장.", "경리 직원이 '실수' 변명."]
    ),
    Company(
        name="㈜넥신 (Nexin)", size="중견기업",
        revenue=100000, operating_income=10000, tax_target=20, team_hp_damage=(10, 25),
        description="급성장 게임/IT 기업. 복잡한 지배구조와 관계사 거래.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 부가가치세 과세/면세 및 부당행위계산부인]**\n"
            "IT 용역은 제공하는 서비스의 실질에 따라 부가가치세 과세 여부가 달라질 수 있습니다(부가가치세법 제26조 등 참조). 일반적으로 SW 개발 및 유지보수 용역은 과세 대상이나, 수출 등 특정 요건 충족 시 영세율 적용 가능성은 있습니다. 과세 대상을 면세로 잘못 신고하면 부가세 추징 및 가산세 대상입니다.\n"
            "특수관계인과의 거래에서 조세 부담을 부당하게 감소시킨 것으로 인정되면 '부당행위계산부인' 규정(법인세법 제52조)이 적용됩니다. 시가보다 현저히 높거나 낮은 대가로 거래하는 경우, 정상가격을 기준으로 소득금액을 재계산하여 과세합니다.\n"
            "**조사 착안 사항:** 용역 계약서 내용, 실제 제공된 서비스 내역, 대금 수수 증빙, 특수관계법인의 실체(페이퍼컴퍼니 여부), 거래 가격의 적정성(시가 평가) 등을 집중 검토합니다."
        ),
        tactics=[
            EvasionTactic("과면세 오류", "과세 대상 'SW 유지보수' 용역 매출 5억원을 면세 'SW 개발'로 위장 신고하여 부가세 누락.", 8, tax_type=TaxType.VAT, method_type=MethodType.ERROR, tactic_category=AttackCategory.REVENUE),
            EvasionTactic("관계사 부당 지원", "대표 아들 소유 페이퍼컴퍼니에 '경영 자문' 명목으로 시가(월 500)보다 높은 월 3천만원 지급.", 12, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["회계법인이 '정상 거래' 주장.", "자료가 '서버 오류'로 삭제 주장 (팀 집중력 -1).", "실무자가 '모른다'며 비협조."]
    ),
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업",
        revenue=50000, operating_income=-1000, tax_target=30, team_hp_damage=(15, 30),
        description="전형적인 '자료상'. 가짜 석유 유통, 허위 세금계산서 발행.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 허위 세금계산서 수수 (자료상)]**\n"
            "실물 거래 없이 세금계산서만을 발급하거나 수취하는 행위는 '자료상 행위'로 간주됩니다. 이는 부가가치세 매입세액 부당 공제, 법인세 비용 과다 계상 등의 탈루로 이어지며, 조세 질서를 심각하게 훼손하는 중범죄입니다(조세범처벌법 제10조).\n"
            "**조사 착안 사항:** 거래의 실재성 여부(실물 이동 증빙, 대금 지급 방식 등), 폭탄업체 연루 여부, 관련 계좌 추적을 통한 자금 흐름 분석이 핵심입니다. 허위 세금계산서 수수 사실이 밝혀지면 관련 세액 추징은 물론, 공급가액에 따른 높은 가산세가 부과되며, 관련자는 형사 고발될 수 있습니다. 차명계좌, 대포폰 사용 등 증거 인멸 시도가 많으므로 초기 증거 확보가 중요합니다."
        ),
        tactics=[
            EvasionTactic("허위 세금계산서 발행", "실물 없이 폭탄업체로부터 받은 허위 세금계산서(가짜 석유) 수십억 원어치를 최종 소비자에게 발행하여 매입세액 부당 공제.", 20, tax_type=TaxType.VAT, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("가공 매출 누락", "대포통장 등 차명계좌로 매출 대금 수백억원 수령 후, 세금계산서 미발행으로 부가세/법인세 소득 누락.", 10, tax_type=[TaxType.CORP, TaxType.VAT], method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.REVENUE)
        ],
        defense_actions=["대표 해외 도피 (추적 난이도 상승 - 효과 미구현).", "사무실 텅 빔 (페이퍼컴퍼니).", "대포폰/대포통장 외 단서 없음."]
    ),
     Company(
        name="㈜삼숭물산 (Samsoong)", size="대기업",
        revenue=50_000_000, operating_income=2_000_000, tax_target=1000, team_hp_damage=(20, 40),
        description="대한민국 최고 대기업. 복잡한 순환출자, 경영권 승계 이슈.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 일감 몰아주기 및 불공정 자본거래]**\n"
            "대기업 집단 내에서 총수 일가가 지배하는 계열사에 부당하게 이익을 제공하는 '일감 몰아주기'는 편법 증여 수단으로 활용될 수 있습니다. 이는 상속세 및 증여세법상 증여의제 규정(상증세법 제45조의3) 또는 법인세법상 부당행위계산부인 규정(법인세법 제52조)의 적용 대상이 될 수 있습니다.\n"
            "계열사 간 합병 시 합병 비율을 불공정하게 산정하여 특정 주주에게 이익을 분여하는 행위 역시 과세 대상입니다(상증세법 제38조, 법인세법 제44조 등).\n"
            "**조사 착안 사항:** 특수관계법인과의 거래 조건(가격, 수의계약 여부 등), 정상적인 제3자 거래와의 비교, 합병 비율 산정 근거, 주식 가치 평가의 적정성 등을 검토합니다. 고도의 법률 및 회계 지식이 요구되며, 대형 로펌의 조력이 예상됩니다."
        ),
        tactics=[
            EvasionTactic("일감 몰아주기", "총수 2세 지분 100% 비상장 'A사'에 그룹 SI 용역을 수의계약으로 고가 발주, 연 수천억원 이익 몰아줌.", 500, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL),
            EvasionTactic("가공 세금계산서 수취", "실거래 없는 유령 광고대행사로부터 수백억 원대 가짜 세금계산서 받아 비용 부풀리고 부가세 부당 환급.", 300, tax_type=TaxType.VAT, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.COST),
            EvasionTactic("불공정 합병", "총수 일가 유리하도록 계열사 합병 비율 조작, 편법으로 경영권 승계 및 이익 증여.", 200, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["최고 로펌 '김&장' 대응팀 꾸림.", "로펌 '정상 경영 활동' 의견서 제출.", "언론에 '과도한 세무조사' 여론전 (팀 체력 -5).", "정치권 통해 조사 중단 압력 (팀 집중력 -2)."]
    ),
    Company(
        name="구갈 코리아(유) (Googal)", size="외국계",
        revenue=2_000_000, operating_income=300_000, tax_target=800, team_hp_damage=(15, 30),
        description="다국적 IT 기업 한국 지사. '이전가격(TP)' 조작 통한 소득 해외 이전 혐의.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 이전가격(TP) 조작 및 고정사업장 회피]**\n"
            "다국적 기업은 국외 특수관계자와의 거래 가격(이전가격)을 조작하여 국내 소득을 국외로 이전시키는 방식으로 조세를 회피할 수 있습니다. 이는 '국제조세조정에 관한 법률'(국조법)에 따라 정상가격 과세 대상입니다(국조법 제4조). 정상가격 산출 방법(비교가능 제3자 가격법 등) 적용 및 비교 대상 선정이 핵심 쟁점입니다.\n"
            "국내에 서버 등 실질적인 사업 활동을 수행하는 장소가 있음에도 이를 '고정사업장'으로 신고하지 않아 국내 발생 소득에 대한 법인세를 회피하는 경우도 있습니다(법인세법 제94조, 한-미 조세조약 등).\n"
            "**조사 착안 사항:** 국외 특수관계자와의 거래 내용(계약서, 용역 제공 내역), 이전가격 산출 근거, 비교 대상 기업 정보, 국내 사업 활동의 실질(서버 위치, 인력 규모 등)을 파악합니다. 본사 자료 확보의 어려움, 조세조약 해석 등 국제조세 전문성이 요구됩니다. 상호합의절차(MAP) 신청 가능성도 염두에 두어야 합니다."
        ),
        tactics=[
            EvasionTactic("이전가격(TP) 조작", "버뮤다 페이퍼컴퍼니 자회사에 국내 매출 상당 부분을 'IP 사용료' 명목으로 지급하여 국내 이익 축소.", 500, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.CAPITAL),
            EvasionTactic("고정사업장 미신고", "국내 서버팜 운영하며 광고 수익 창출함에도 '단순 지원 용역'으로 위장, 고정사업장 신고 회피.", 300, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.REVENUE)
        ],
        defense_actions=["미 본사 '영업 비밀' 이유로 자료 제출 거부.", "조세 조약 근거 상호 합의(MAP) 신청 압박.", "자료 영어로만 제출, 번역 지연 (다음 턴 드로우 -1, 효과 미구현).", "집중력 감소 유도 (효과 미구현)"]
    ),
    Company(
        name="(주)씨엔해운 (C&)", size="대기업",
        revenue=10_000_000, operating_income=500_000, tax_target=1500, team_hp_damage=(25, 45),
        description="'선박왕' 운영 해운사. 조세피난처 페이퍼컴퍼니 이용 탈루 혐의.",
        # (개선) 교육 정보 강화
        real_case_desc=(
            "**[교육: 조세피난처 SPC를 이용한 역외탈세]**\n"
            "조세 부담이 없거나 현저히 낮은 국가(조세피난처)에 명목상의 회사(SPC)를 설립하고, 이를 통해 국내 소득을 이전하거나 자산을 은닉하는 행위는 대표적인 역외탈세 유형입니다. 선박, 항공기 등 고가 자산 거래나 지식재산권 사용료 지급 등에 자주 이용됩니다.\n"
            "특정외국법인(CFC) 유보소득 과세 제도(국조법 제17조)나 실질과세 원칙 등을 적용하여 과세할 수 있습니다.\n"
            "**조사 착안 사항:** 조세피난처 SPC의 실체(인적/물적 설비), 자금 흐름(국내→SPC→제3국 등), 이면 계약 존재 여부, SPC 설립 및 운영 관련 내부 문서 확보가 중요합니다. 국제 정보 교환, 해외 금융계좌 신고 정보(FATCA/CRS) 등을 활용한 추적이 필요합니다. 해외 법률 및 현지 정보 부족으로 조사가 어려울 수 있습니다."
        ),
        tactics=[
            EvasionTactic("역외탈세 (SPC)", "파나마, BVI 등 페이퍼컴퍼니(SPC) 명의로 선박 운용, 국내 리스료 수입 수천억원 은닉.", 1000, tax_type=TaxType.CORP, method_type=MethodType.CAPITAL_TX, tactic_category=AttackCategory.REVENUE),
            EvasionTactic("선박 취득가액 조작", "노후 선박 해외 SPC에 저가 양도 후, SPC가 고가로 제3자 매각, 양도 차익 수백억원 은닉.", 500, tax_type=TaxType.CORP, method_type=MethodType.INTENTIONAL, tactic_category=AttackCategory.CAPITAL)
        ],
        defense_actions=["해외 법인 대표 연락 두절.", "이면 계약서 존재 첩보 (핵심 카드 강제 폐기 시도 - 효과 미구현).", "국내 법무팀 '해외 법률 검토 필요' 대응 지연.", "조사 방해 시도 (팀 체력 -10)."]
    ),
]


# --- 3. 게임 상태 초기화 및 관리 ---
# (이전과 동일)
def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    """
    (이전과 동일) 드래프트에서 선택된 리더/유물로 게임을 초기화합니다.
    (이전과 동일) 팀원 수를 3명으로 고정하고, 직급 구분 없이 랜덤 구성합니다.
    """

    seed = st.session_state.get('seed', 0)
    if seed != 0:
        random.seed(seed)
        st.toast(f"ℹ️ RNG 시드 {seed}로 고정됨.")
    else:
        random.seed()

    team_members = []
    team_members.append(chosen_lead) # 1. 드래프트에서 선택한 리더

    # 2. 나머지 2명은 전체 인물 풀에서 랜덤 선택 (리더 제외, 중복 제외)
    all_members = list(TAX_MAN_DB.values())
    remaining_pool = [m for m in all_members if m != chosen_lead] # 리더 제외

    # (수정) 중복 방지 - 이미 sample은 중복 없이 뽑음. Pool 자체는 중복 없을 것.
    # 단, 샘플 개수가 Pool 크기보다 작거나 같아야 함
    num_to_sample = min(2, len(remaining_pool))
    if num_to_sample > 0:
        team_members.extend(random.sample(remaining_pool, num_to_sample))

    st.session_state.player_team = team_members

    # 이하 로직은 이전과 동일
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
        # (수정) 신규 아티팩트 효과 반영
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "stat_evidence":
                st.session_state.team_stats["evidence"] += artifact.effect["value"]
            elif artifact.effect["subtype"] == "stat_persuasion":
                st.session_state.team_stats["persuasion"] += artifact.effect["value"]
            elif artifact.effect["subtype"] == "stat_analysis": # 신규
                st.session_state.team_stats["analysis"] += artifact.effect["value"]

    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None
    st.session_state.bonus_draw = 0

    st.session_state.company_order = random.sample(COMPANY_DB, len(COMPANY_DB))
    st.session_state.game_state = "MAP"

    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0

# --- 4. 게임 로직 함수 ---
# (이하 로직 함수들은 이전 버전과 거의 동일, 일부 능력 로직/아티팩트 로직 추가)

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
        # (수정) 확률 기반 집중력 증가 아티팩트
        elif artifact.effect["type"] == "on_turn_start" and artifact.effect["subtype"] == "focus_chance":
            if random.random() < artifact.effect.get("chance", 0): # chance 키 없으면 0%
                st.session_state.player_focus_current += artifact.effect["value"]
                log_message(f"✨ {artifact.name} 효과 발동! 집중력 +{artifact.effect['value']}!", "info")


    st.session_state.player_focus_max = st.session_state.player_focus_current

    if "김대지" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"] >= 50:
        if 'kim_dj_effect_used' not in st.session_state or st.session_state.kim_dj_effect_used == False:
            new_card = copy.deepcopy(LOGIC_CARD_DB["b_tier_01"]) # 금융거래 분석 (복사본)
            new_card.just_created = True # 드로우 효과 즉시 발동 방지 플래그
            st.session_state.player_hand.append(new_card)
            log_message("✨ [부동산 투기 조사] '금융거래 분석' 카드 1장 획득!", "info")
            st.session_state.kim_dj_effect_used = True

    if "전진" in [m.name for m in st.session_state.player_team]:
        eligible_members = [m for m in st.session_state.player_team if m.name != "전진"]
        if eligible_members:
            target_member = random.choice(eligible_members)
            st.session_state.cost_reduction_target = target_member.name
            log_message(f"✨ [실무 지휘] '{target_member.name}' 팀원의 다음 카드 비용 -1!", "info")
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

# (draw_cards, check_draw_cards_in_hand, select_card_to_play, execute_search_draw, cancel_card_selection, calculate_card_cost, execute_attack, end_player_turn, enemy_turn, check_battle_end 이전과 거의 동일 - 캐릭터 능력 로직 포함됨)
# ... (이전 코드와 동일한 긴 로직 함수들 생략) ...
# --- [수정됨] start_battle (기업 특화 카드 추가 로직) ---
def start_battle(company_template):
    company = copy.deepcopy(company_template); st.session_state.current_battle_company = company; st.session_state.game_state = "BATTLE"
    st.session_state.battle_log = [f"--- {company.name} ({company.size}) 조사 시작 ---"]

    # (개선) 조사 시작 시 혐의 요약 및 교육 로그 추가
    log_message(f"🏢 **{company.name}**의 주요 탈루 혐의는 다음과 같습니다:", "info")
    tactic_types = set()
    has_capital_tx = False # 자본 거래 혐의 플래그
    for tactic in company.tactics:
        tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
        log_message(f"- **{tactic.name}** ({'/'.join(tactic_tax_types)}, {tactic.method_type.value}, {tactic.tactic_category.value})", "info")
        tactic_types.add(tactic.method_type)
        if tactic.tactic_category == AttackCategory.CAPITAL:
            has_capital_tx = True

    log_message("---", "info") # 구분선
    guidance = "[조사 가이드] "
    if MethodType.INTENTIONAL in tactic_types:
        guidance += "고의적 탈루 혐의가 의심됩니다. 결정적 증거 확보와 압박이 중요합니다. "
    if has_capital_tx or company.size in ["대기업", "외국계"]:
        guidance += "복잡한 자본 거래나 국제 거래가 예상됩니다. 자금 흐름과 관련 법규를 면밀히 분석해야 합니다. "
    if MethodType.ERROR in tactic_types and MethodType.INTENTIONAL not in tactic_types:
        guidance += "단순 실수나 착오일 가능성이 있습니다. 관련 규정과 판례를 제시하며 설득하는 것이 효과적일 수 있습니다. "
    if not guidance == "[조사 가이드] ":
        log_message(guidance, "warning")
    else:
        log_message("[조사 가이드] 기업의 특성과 혐의 유형을 고려하여 전략적으로 접근하십시오.", "warning")
    log_message("---", "info") # 구분선


    st.session_state.team_shield = 0; st.session_state.bonus_draw = 0

    for artifact in st.session_state.player_artifacts:
        log_message(f"✨ [조사도구] '{artifact.name}' 효과 준비.", "info")
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "shield":
                shield_gain = artifact.effect["value"]; st.session_state.team_shield += shield_gain; log_message(f"✨ {artifact.name} 보호막 +{shield_gain}!", "info")
            elif artifact.effect["subtype"] == "draw":
                st.session_state.bonus_draw += artifact.effect["value"]
            # 스탯 증가는 initialize에서 처리됨

    # (개선) 기업 특화 카드 추가 로직
    temp_deck = st.session_state.player_deck + st.session_state.player_discard # 현재 덱 + 버린 덱
    if has_capital_tx:
        # 자본 거래 혐의가 있으면 '자금출처조사' 카드를 1장 임시 추가
        capital_card = LOGIC_CARD_DB.get("a_tier_01") # 자금출처조사
        if capital_card:
            temp_deck.append(capital_card)
            log_message("✨ [기업 특성 감지] 복잡한 자금 흐름에 대비해 '자금출처조사' 카드를 임시로 덱에 추가합니다.", "info")

    # 임시 카드가 포함된 덱을 섞어서 전투 시작
    st.session_state.player_deck = random.sample(temp_deck, len(temp_deck))
    st.session_state.player_discard = []; st.session_state.player_hand = []; start_player_turn()

# (log_message, go_to_next_stage 이전과 동일)
def log_message(message, level="normal"):
    color_map = {"normal": "", "success": "green", "warning": "orange", "error": "red", "info": "blue"}
    if level != "normal": message = f":{color_map[level]}[{message}]"
    st.session_state.battle_log.insert(0, message)
    if len(st.session_state.battle_log) > 30: st.session_state.battle_log.pop()

def go_to_next_stage(add_card=None, heal_amount=0):
    if add_card:
        # 전투 중 임시로 추가된 카드가 아닌 경우에만 덱에 영구 추가
        # (여기서는 간단하게, 다음 전투 시작 시 덱을 재구성하므로 별도 제거 로직 불필요)
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

# --- [수정됨] show_main_menu (리더 후보 4명) ---
def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---"); st.header("국세청에 오신 것을 환영합니다.")
    st.write("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    st.image("https://cphoto.asiae.co.kr/listimglink/1/2021071213454415883_1626065144.jpg",
             caption="국세청(세종청사) 전경",
             width=400)

    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="0이 아닌 값을 입력하면 동일한 팀 구성과 보상으로 테스트할 수 있습니다.")

    if st.button("🚨 조사 시작 (신규 게임)", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0)
        if seed != 0: random.seed(seed)

        all_members = list(TAX_MAN_DB.values())
        # (수정) 리더 후보 4명 제시
        st.session_state.draft_team_choices = random.sample(all_members, min(len(all_members), 4))

        # (수정) 신규 아티팩트 포함하여 3개 제시
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
    st.subheader("1. 팀 리더를 선택하세요:")

    selected_lead_index = st.radio(
        "리더 후보",
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
                # (개선) 강화된 교육 정보 표시
                st.info(f"**[교육 정보]**\n{company.real_case_desc}"); st.markdown("---"); st.markdown("**주요 탈루 혐의**")
                for tactic in company.tactics:
                    tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
                    st.markdown(f"- **{tactic.name}** (`{', '.join(tactic_tax_types)}`, `{tactic.method_type.value}`, `{tactic.tactic_category.value}`): _{tactic.description}_")

            if st.button(f"🚨 {company.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(company); st.rerun()
    else:
        st.success("🎉 모든 기업 조사 완료! (데모 종료)"); st.balloons()
        if st.button("🏆 다시 시작"): st.session_state.game_state = "MAIN_MENU"; st.rerun()

# (show_battle_screen 이전과 동일)
def show_battle_screen():
    if not st.session_state.current_battle_company: st.error("오류: 기업 정보 없음."); st.session_state.game_state = "MAP"; st.rerun(); return

    company = st.session_state.current_battle_company
    st.title(f"⚔️ {company.name} 조사 중..."); st.markdown("---")

    col_company, col_log_action, col_hand = st.columns([1.6, 2.0, 1.4])

    with col_company: # 기업 정보
        st.subheader(f"🏢 {company.name} ({company.size})")
        st.progress(min(1.0, company.current_collected_tax/company.tax_target), text=f"💰 목표 세액: {company.current_collected_tax:,}/{company.tax_target:,} (억원)")
        st.markdown("---"); st.subheader("🧾 탈루 혐의 목록")

        is_card_selected = st.session_state.get("selected_card_index") is not None
        if is_card_selected:
            selected_card = st.session_state.player_hand[st.session_state.selected_card_index]
            st.info(f"**'{selected_card.name}'** 카드로 공격할 혐의 선택:")

        if not company.tactics: st.write("(모든 혐의 적발!)")

        tactic_container = st.container(height=450)
        with tactic_container:
            for i, tactic in enumerate(company.tactics):
                tactic_cleared = tactic.exposed_amount >= tactic.total_amount
                with st.container(border=True):
                    tactic_tax_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]
                    st.markdown(f"**{tactic.name}** (`{', '.join(tactic_tax_types)}`/`{tactic.method_type.value}`/`{tactic.tactic_category.value}`)")
                    st.caption(f"_{tactic.description}_")

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

    with col_log_action: # 로그, 행동
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

    with col_hand: # 손패
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")
        if not st.session_state.player_hand: st.write("(손패 없음)")
        is_card_selected = st.session_state.get("selected_card_index") is not None

        hand_container = st.container(height=600)

        with hand_container:
            for i, card in enumerate(st.session_state.player_hand):
                if i >= len(st.session_state.player_hand): continue
                if card.cost == 0 and card.special_effect and card.special_effect.get("type") == "draw": continue

                temp_member_name = st.session_state.get('cost_reduction_target')
                cost_to_pay = calculate_card_cost(card, member_name=temp_member_name)

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
                        select_card_to_play(i)

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
                        # 덱과 버린 덱 모두에서 해당 이름의 첫 번째 카드 제거
                        removed = False
                        for deck in [st.session_state.player_deck, st.session_state.player_discard]:
                             try:
                                 card_to_remove = next(c for c in deck if c.name == name)
                                 deck.remove(card_to_remove)
                                 removed = True
                                 st.toast(f"[{name}] 1장 제거!", icon="🗑️")
                                 go_to_next_stage()
                                 return # 제거 성공 시 즉시 종료
                             except (StopIteration, ValueError):
                                 continue # 다른 덱에서 계속 탐색
                        if not removed:
                             st.error("오류: 카드를 찾을 수 없어 제거하지 못했습니다.")

                    except Exception as e:
                        st.error(f"오류 발생: {e}")


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

# --- [수정됨] show_player_status_sidebar (직급 표시 제거) ---
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
             # (수정) 직급 표시 제거
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
        # 전투 중일 때만 버린 덱 보기 제공
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {}
                for card in st.session_state.player_discard: discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not discard_counts: st.write("(버린 카드 없음)")
                for name in sorted(discard_counts.keys()): st.write(f"- {name} x {discard_counts[name]}")


        st.markdown("---"); st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts: st.write("(없음)")
        else:
             for artifact in st.session_state.player_artifacts: st.success(f"- {artifact.name}: {artifact.description}")

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

    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER", "GAME_SETUP_DRAFT"] and 'player_team' in st.session_state:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
