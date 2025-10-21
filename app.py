import streamlit as st
import random
import copy
from enum import Enum
import math

# --- 0. Enum(열거형) 정의 ---
class TaxType(str, Enum): CORP = "법인세"; VAT = "부가세"; COMMON = "공통"
class AttackCategory(str, Enum): COST = "비용"; REVENUE = "수익"; CAPITAL = "자본"; COMMON = "공통"
class MethodType(str, Enum): INTENTIONAL = "고의적 누락"; ERROR = "단순 오류"; CAPITAL_TX = "자본 거래"

# --- 헬퍼 함수 ---
def format_krw(amount):
    if amount is None: return "N/A"
    try:
        if abs(amount) >= 1_000_000: return f"{amount / 1_000_000:,.1f}조원"
        elif abs(amount) >= 10_000: return f"{amount / 10_000:,.0f}억원"
        elif abs(amount) >= 100: return f"{amount / 100:,.0f}억원"
        else: return f"{amount:,.0f}백만원"
    except Exception: return f"{amount} (Format Error)"

# --- 1. 기본 데이터 구조 ---
class Card:
    def __init__(self, name, description, cost): self.name = name; self.description = description; self.cost = cost;
class TaxManCard(Card):
    def __init__(self, name, grade_num, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost); self.grade_num=grade_num; self.hp=hp; self.max_hp=hp; self.focus=focus; self.analysis=analysis; self.persuasion=persuasion; self.evidence=evidence; self.data=data; self.ability_name=ability_name; self.ability_desc=ability_desc; grade_map={4:"S", 5:"S", 6:"A", 7:"B", 8:"C", 9:"C"}; self.grade=grade_map.get(self.grade_num, "C")
class LogicCard(Card):
    def __init__(self, name, description, cost, base_damage, tax_type: list[TaxType], attack_category: list[AttackCategory], text, special_effect=None, special_bonus=None):
        super().__init__(name, description, cost); self.base_damage=base_damage; self.tax_type=tax_type; self.attack_category=attack_category; self.text=text; self.special_effect=special_effect; self.special_bonus=special_bonus;
class EvasionTactic:
    def __init__(self, name, description, total_amount, tax_type: TaxType | list[TaxType], method_type: MethodType, tactic_category: AttackCategory):
        self.name=name; self.description=description; self.total_amount=total_amount; self.exposed_amount=0; self.tax_type=tax_type; self.method_type=method_type; self.tactic_category=tactic_category; self.is_cleared=False;
class Company:
    def __init__(self, name, size, description, real_case_desc, revenue, operating_income, tax_target, team_hp_damage, tactics, defense_actions):
        self.name=name; self.size=size; self.description=description; self.real_case_desc=real_case_desc; self.revenue=revenue; self.operating_income=operating_income; self.tax_target=tax_target; self.team_hp_damage=team_hp_damage; self.current_collected_tax=0; self.tactics=tactics; self.defense_actions=defense_actions;
class Artifact:
    def __init__(self, name, description, effect): self.name=name; self.description=description; self.effect=effect;

# --- 2. 게임 데이터베이스 (DB) ---
TAX_MAN_DB = { # ... (이전과 동일)
    "lim": TaxManCard(name="임향수", grade_num=4, description="국세청의 핵심 요직을 두루 거친 '조사통의 대부'. 굵직한 대기업 비자금, 불법 증여 조사를 지휘한 경험이 풍부하다.", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10, ability_name="[기획 조사]", ability_desc="전설적인 통찰력. 매 턴 집중력 +1. 팀의 '분석', '데이터' 스탯에 비례해 '비용', '자본' 카드 피해량 증가."),
    "han": TaxManCard(name="한중히", grade_num=5, description="국제조세 분야에서 잔뼈가 굵은 전문가. OECD 파견 경험으로 국제 공조 및 BEPS 프로젝트에 대한 이해가 깊다.", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9, ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시, 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", grade_num=5, description="세제실 경험을 바탕으로 국세행정 시스템 발전에 기여한 '세제 전문가'. TIS, NTIS 등 과학세정 인프라 구축에 밝다.", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7, ability_name="[TIS 분석]", ability_desc="시스템을 꿰뚫는 힘. '금융거래 분석', '빅데이터 분석' 등 '데이터' 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", grade_num=6, description="서울청장 시절 변칙 상속/증여 조사를 강력하게 지휘했던 경험 많은 조사 전문가. 대기업 조사에 정통하다.", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7, ability_name="[대기업 저격]", ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대지", grade_num=5, description="국세청의 주요 보직을 역임하며 전략적인 세정 운영 능력을 보여준 전문가. 데이터 기반의 대규모 조사 경험이 있다.", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10, ability_name="[부동산 투기 조사]", ability_desc="팀의 '데이터' 스탯이 50 이상일 경우, 턴 시작 시 '금융거래 분석' 카드를 1장 생성하여 손에 넣습니다."),
    "lee_hd": TaxManCard(name="이현동", grade_num=5, description="강력한 추진력으로 조사 분야에서 성과를 낸 '조사통'. 특히 지하경제 양성화와 역외탈세 추적에 대한 의지가 강하다.", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8, ability_name="[지하경제 양성화]", ability_desc="'고의적 누락(Intentional)' 혐의에 대한 모든 공격의 최종 피해량 +20%."),
    "kim": TaxManCard(name="김철주", grade_num=6, description="서울청 조사4국에서 '지하경제 양성화' 관련 조사를 다수 수행한 현장 전문가.", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5, ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거(아티팩트)' 추가 획득."),
    "oh": TaxManCard(name="전필성", grade_num=7, description="[가상] TIS 구축 초기 멤버로 시스템 이해도가 높다. PG사, 온라인 플랫폼 등 신종 거래 분석에 능한 데이터 전문가.", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8, ability_name="[데이터 마이닝]", ability_desc="기본 적출액 70억원 이상인 '데이터' 관련 카드(자금출처조사 등)의 피해량 +15."),
    "jo": TaxManCard(name="조용규", grade_num=7, description="교육원에서 후배 양성에 힘쓴 경험이 있는 '세법 이론가'. 법리 해석과 판례 분석이 뛰어나다.", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7, ability_name="[세법 교본]", ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우)가 2배로 적용."),
    "park": TaxManCard(name="박지연", grade_num=8, description="[가상] 세무사/CPA 동시 합격 후 특채 입직. 방대한 세법 지식을 바탕으로 날카로운 법리 검토 능력을 보여주는 '세법 신동'.", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7, ability_name="[법리 검토]", ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이철수", grade_num=7, description="[가상] 갓 임용된 7급 공채 신입. 열정은 넘치지만 아직 경험이 부족하다. 기본기에 충실하며 기초 자료 분석을 담당.", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5, ability_name="[기본기]", ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드의 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원구", grade_num=6, description="서울청 조사국 등에서 대기업 비자금 등 굵직한 특수 조사를 다룬 경험이 풍부한 '특수 조사의 귀재'.", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6, ability_name="[특수 조사]", ability_desc="'현장 압수수색', '차명계좌 추적' 카드의 비용 -1. (최소 0)"),
    "yoo_jj": TaxManCard(name="유재준", grade_num=6, description="[현직] 서울청 조사2국에서 대기업 정기 세무조사 및 상속/증여세 조사를 담당하는 관리자. 꼼꼼한 분석과 설득이 강점.", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7, ability_name="[정기 조사 전문]", ability_desc="'단순 오류(Error)' 유형의 혐의 공격 시, 팀 '설득(Persuasion)' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태호", grade_num=6, description="[현직] 중부청 조사1국에서 대기업/중견기업 심층 기획조사 및 국제거래 조사를 담당. 증거 확보와 데이터 분석 능력이 탁월하다.", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8, ability_name="[심층 기획 조사]", ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거(Evidence)' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전진", grade_num=7, description="[현직] 중부청 조사1국 실무 과장. 조사 현장 지휘 경험이 풍부하며, 팀원들의 능력을 끌어내는 데 능숙하다.", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6, ability_name="[실무 지휘]", ability_desc="턴 시작 시, **팀**의 다음 카드 사용 비용 -1. (조사관 무관)")
}
LOGIC_CARD_DB = { # ... (이전과 동일, 보호막 카드 제외)
    "c_tier_01": LogicCard(name="단순 자료 대사", cost=0, base_damage=5, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="매입/매출 자료 단순 비교.", text="자료 대사 기본 습득."),
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
    "cap_01": LogicCard(name="부당행위계산부인", cost=3, base_damage=40, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE], description="특수관계자와의 거래(자산 고가 매입, 저가 양도 등)에서 시가를 조작하여 이익을 분여한 혐의를 지적합니다.", text="계열사 간 저가 양수도 적발.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
    "b_tier_01": LogicCard(name="금융거래 분석", cost=3, base_damage=45, tax_type=[TaxType.CORP], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="의심스러운 자금 흐름을 추적하여 숨겨진 수입이나 부당한 자본 거래를 포착합니다.", text="FIU 분석 기법 습득."),
    "b_tier_02": LogicCard(name="현장 압수수색", cost=3, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="조사 현장을 방문하여 장부와 실제 재고, 자산 등을 대조하고 숨겨진 자료를 확보합니다.", text="재고 불일치 확인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_02": LogicCard(name="차명계좌 추적", cost=3, base_damage=50, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.REVENUE], description="타인 명의로 개설된 계좌를 통해 수입 금액을 은닉한 정황을 포착하고 자금 흐름을 추적합니다.", text="차명계좌 흐름 파악.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "cap_02": LogicCard(name="불공정 자본거래", cost=4, base_damage=80, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="합병, 증자, 감자 등 과정에서 불공정한 비율을 적용하여 주주(총수 일가)에게 이익을 증여한 혐의를 조사합니다.", text="상증세법상 이익의 증여.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "a_tier_01": LogicCard(name="자금출처조사", cost=4, base_damage=90, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="고액 자산가의 자산 형성 과정에서 불분명한 자금의 출처를 소명하도록 요구하고, 탈루 혐의를 조사합니다.", text="수십 개 차명계좌 흐름 파악."),
    "s_tier_01": LogicCard(name="국제거래 과세논리", cost=4, base_damage=65, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="이전가격 조작, 고정사업장 회피 등 국제거래를 이용한 조세회피 전략을 분석하고 과세 논리를 개발합니다.", text="BEPS 보고서 이해.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "s_tier_02": LogicCard(name="조세피난처 역외탈세", cost=5, base_damage=130, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="조세피난처에 설립된 특수목적회사(SPC) 등을 이용하여 해외 소득을 은닉한 역외탈세 혐의를 조사합니다.", text="BVI, 케이맨 SPC 실체 규명.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
}
ARTIFACT_DB = { # ... (이전과 동일, 보호막 아티팩트 제외)
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]})
}
COMPANY_DB = [ # ... (이전과 동일, 스탯 현실화, 설명 마크다운)
    Company(name="(주)가나푸드", size="소규모", revenue=8000, operating_income=800, tax_target=5, team_hp_damage=(5, 10), description="...", real_case_desc="...", tactics=[ EvasionTactic("사주 개인적 사용", "...", 3, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST), EvasionTactic("증빙 미비 경비", "...", 2, [TaxType.CORP, TaxType.VAT], MethodType.ERROR, AttackCategory.COST)], defense_actions=["..."]),
    Company(name="㈜넥신 (Nexin)", size="중견기업", revenue=150000, operating_income=15000, tax_target=80, team_hp_damage=(15, 30), description="...", real_case_desc="...", tactics=[ EvasionTactic("과면세 오류", "...", 8, TaxType.VAT, MethodType.ERROR, AttackCategory.REVENUE), EvasionTactic("관계사 부당 지원", "...", 12, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)], defense_actions=["..."]),
    Company(name="(주)한늠석유 (자료상)", size="중견기업", revenue=50000, operating_income=-1000, tax_target=100, team_hp_damage=(20, 35), description="...", real_case_desc="...", tactics=[ EvasionTactic("허위 세금계산서 발행", "...", 70, TaxType.VAT, MethodType.INTENTIONAL, AttackCategory.COST), EvasionTactic("가공 매출 누락", "...", 30, [TaxType.CORP, TaxType.VAT], MethodType.INTENTIONAL, AttackCategory.REVENUE)], defense_actions=["..."]),
     Company(name="㈜삼숭물산 (Samsoong)", size="대기업", revenue=50_000_000, operating_income=2_000_000, tax_target=1000, team_hp_damage=(20, 40), description="...", real_case_desc="...", tactics=[ EvasionTactic("일감 몰아주기", "...", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL), EvasionTactic("가공 세금계산서 수취", "...", 300, TaxType.VAT, MethodType.INTENTIONAL, AttackCategory.COST), EvasionTactic("불공정 합병", "...", 200, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)], defense_actions=["..."]),
    Company(name="구갈 코리아(유) (Googal)", size="외국계", revenue=2_000_000, operating_income=300_000, tax_target=800, team_hp_damage=(18, 35), description="...", real_case_desc="...", tactics=[ EvasionTactic("이전가격(TP) 조작", "...", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL), EvasionTactic("고정사업장 미신고", "...", 300, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE)], defense_actions=["..."]),
    Company(name="(주)씨엔해운 (C&)", size="대기업", revenue=10_000_000, operating_income=500_000, tax_target=1500, team_hp_damage=(25, 45), description="...", real_case_desc="...", tactics=[ EvasionTactic("역외탈세 (SPC)", "...", 1000, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.REVENUE), EvasionTactic("선박 취득가액 조작", "...", 500, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.CAPITAL)], defense_actions=["..."]),
]

# --- 3. 게임 상태 초기화 및 관리 ---
def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
    if seed != 0: st.toast(f"ℹ️ RNG 시드 {seed} 고정됨.")
    team_members = [chosen_lead]; all_mem = list(TAX_MAN_DB.values()); remain = [m for m in all_mem if m != chosen_lead]; team_members.extend(random.sample(remain, min(2, len(remain)))); st.session_state.player_team = team_members
    start_deck = [LOGIC_CARD_DB["basic_01"]]*3 + [LOGIC_CARD_DB["basic_02"]]*2 + [LOGIC_CARD_DB["b_tier_04"]]*2 + [LOGIC_CARD_DB["c_tier_02"]]*2 + [LOGIC_CARD_DB["c_tier_01"]]*5 # 14장
    st.session_state.player_deck = random.sample(start_deck, len(start_deck)); st.session_state.player_hand=[]; st.session_state.player_discard=[]
    st.session_state.player_artifacts=[chosen_artifact]
    st.session_state.team_max_hp=sum(m.hp for m in team_members); st.session_state.team_hp=st.session_state.team_max_hp
    st.session_state.player_focus_max=sum(m.focus for m in team_members); st.session_state.player_focus_current=st.session_state.player_focus_max
    st.session_state.team_stats={"analysis":sum(m.analysis for m in team_members),"persuasion":sum(m.persuasion for m in team_members),"evidence":sum(m.evidence for m in team_members),"data":sum(m.data for m in team_members)}
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_battle_start":
            if art.effect["subtype"]=="stat_evidence": st.session_state.team_stats["evidence"]+=art.effect["value"]
            elif art.effect["subtype"]=="stat_persuasion": st.session_state.team_stats["persuasion"]+=art.effect["value"]
    st.session_state.current_battle_company=None; st.session_state.battle_log=[]; st.session_state.selected_card_index=None; st.session_state.bonus_draw=0; st.session_state.company_order=random.sample(COMPANY_DB, len(COMPANY_DB)); st.session_state.game_state="MAP"; st.session_state.current_stage_level=0; st.session_state.total_collected_tax=0

# --- 4. 게임 로직 함수 ---

def start_player_turn():
    focus = sum(m.focus for m in st.session_state.player_team); st.session_state.player_focus_current=focus
    if "임향수" in [m.name for m in st.session_state.player_team]: st.session_state.player_focus_current+=1; log_message("✨ [기획 조사] 집중력 +1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_turn_start" and art.effect["subtype"]=="focus": st.session_state.player_focus_current+=art.effect["value"]; log_message(f"✨ {art.name} 집중력 +{art.effect['value']}!", "info")
    st.session_state.player_focus_max = st.session_state.player_focus_current
    if "김대지" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"]>=50 and not st.session_state.get('kim_dj_effect_used', False): new=copy.deepcopy(LOGIC_CARD_DB["b_tier_01"]); new.just_created=True; st.session_state.player_hand.append(new); log_message("✨ [부동산 조사] '금융거래 분석' 1장 획득!", "info"); st.session_state.kim_dj_effect_used=True
    st.session_state.cost_reduction_active = "전진" in [m.name for m in st.session_state.player_team];
    if st.session_state.cost_reduction_active: log_message("✨ [실무 지휘] 다음 카드 비용 -1!", "info")
    draw_n = 4 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0)>0: log_message(f"✨ {ARTIFACT_DB['plan'].name} 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info"); st.session_state.bonus_draw=0
    draw_cards(draw_n); check_draw_cards_in_hand(); log_message("--- 플레이어 턴 시작 ---"); st.session_state.turn_first_card_played=True; st.session_state.selected_card_index=None

def draw_cards(num):
    drawn = []
    for _ in range(num):
        if not st.session_state.player_deck:
            if not st.session_state.player_discard: log_message("경고: 더 뽑을 카드 없음!", "error"); break
            log_message("덱 리셔플."); st.session_state.player_deck = random.sample(st.session_state.player_discard, len(st.session_state.player_discard)); st.session_state.player_discard = []
            if not st.session_state.player_deck: log_message("경고: 덱/버린 덱 모두 비었음!", "error"); break
        if not st.session_state.player_deck: log_message("경고: 덱 비었음!", "error"); break
        card = st.session_state.player_deck.pop(); drawn.append(card)
    st.session_state.player_hand.extend(drawn)

def check_draw_cards_in_hand():
    indices = [i for i, c in enumerate(st.session_state.player_hand) if c.cost==0 and c.special_effect and c.special_effect.get("type")=="draw" and not getattr(c, 'just_created', False)]
    indices.reverse(); total_draw=0
    for idx in indices:
        if idx < len(st.session_state.player_hand):
            card = st.session_state.player_hand.pop(idx); st.session_state.player_discard.append(card); val = card.special_effect.get('value', 0); log_message(f"✨ [{card.name}] 효과! 카드 {val}장 뽑기.", "info")
            if "조용규" in [m.name for m in st.session_state.player_team] and card.name=="법령 재검토": log_message("✨ [세법 교본] +1장 추가!", "info"); val*=2
            total_draw += val
        else: log_message(f"경고: 드로우 처리 인덱스 오류 (idx: {idx})", "error")
    for card in st.session_state.player_hand:
        if hasattr(card, 'just_created'): card.just_created=False
    if total_draw > 0: draw_cards(total_draw)

def execute_utility_card(card_index):
    if card_index is None or card_index >= len(st.session_state.player_hand): return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); return
    st.session_state.player_focus_current -= cost
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False
    effect = card.special_effect.get("type")
    if effect == "search_draw":
        cats = list(set([t.tactic_category for t in st.session_state.current_battle_company.tactics if not t.is_cleared]))
        if not cats: log_message("ℹ️ [빅데이터 분석] 분석할 혐의 없음.", "info")
        else:
            pool=st.session_state.player_deck+st.session_state.player_discard; random.shuffle(pool)
            found = next((c for c in pool if c not in st.session_state.player_hand and c.cost>0 and AttackCategory.COMMON not in c.attack_category and not (c.special_effect and c.special_effect.get("type")=="draw") and any(cat in cats for cat in c.attack_category)), None)
            if found: log_message(f"📊 [빅데이터 분석] '{found.name}' 발견!", "success"); new=copy.deepcopy(found); new.just_created=True; st.session_state.player_hand.append(new);
            try: st.session_state.player_deck.remove(found)
            except ValueError:
                try: st.session_state.player_discard.remove(found)
                except ValueError: log_message("경고: 빅데이터 카드 제거 오류", "error")
            else: log_message("ℹ️ [빅데이터 분석] 관련 카드 없음...", "info")
    elif effect == "draw":
        val = card.special_effect.get("value", 0); log_message(f"✨ [{card.name}] 효과! 카드 {val}장 드로우!", "info"); draw_cards(val)
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None
    check_draw_cards_in_hand(); st.rerun()

def select_card_to_play(card_index):
    if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand): st.toast("오류: 유효 카드 아님.", icon="🚨"); return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); return
    if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: execute_utility_card(card_index)
    else: st.session_state.selected_card_index = card_index; st.rerun()

def cancel_card_selection(): st.session_state.selected_card_index = None; st.rerun()

def calculate_card_cost(card): # SyntaxError 수정됨
    cost = card.cost
    if "백용호" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name or AttackCategory.CAPITAL in card.attack_category):
        cost = max(0, cost - 1)
    is_first = st.session_state.get('turn_first_card_played', True);
    type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name or AttackCategory.COMMON in card.attack_category)
    if "박지연" in [m.name for m in st.session_state.player_team] and is_first and type_match:
        cost = max(0, cost - 1)
    if "안원구" in [m.name for m in st.session_state.player_team] and card.name in ['현장 압수수색', '차명계좌 추적']:
        cost = max(0, cost - 1)
    if st.session_state.get('cost_reduction_active', False):
        original_cost = cost
        cost = max(0, cost - 1)
        if cost < original_cost:
            st.session_state.cost_reduction_active = False
            log_message(f"✨ [실무 지휘] 카드 비용 -1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_cost_calculate" and card.name in art.effect["target_cards"]:
            cost = max(0, cost + art.effect["value"])
    return cost

def execute_attack(card_index, tactic_index): # SyntaxError 수정됨
    if card_index is None or card_index >= len(st.session_state.player_hand) or tactic_index >= len(st.session_state.current_battle_company.tactics): st.toast("오류: 공격 실행 오류.", icon="🚨"); st.session_state.selected_card_index = None; st.rerun(); return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    tactic = st.session_state.current_battle_company.tactics[tactic_index]; company = st.session_state.current_battle_company
    is_tax = (TaxType.COMMON in card.tax_type) or (isinstance(tactic.tax_type, list) and any(tt in card.tax_type for tt in tactic.tax_type)) or (tactic.tax_type in card.tax_type)
    if not is_tax: t_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value]; log_message(f"❌ [세목 불일치!] '{card.name}' -> '{', '.join(t_types)}' (❤️-10)", "error"); st.session_state.team_hp -= 10; st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return
    is_cat = (AttackCategory.COMMON in card.attack_category) or (tactic.tactic_category in card.attack_category)
    if not is_cat: log_message(f"🚨 [유형 불일치!] '{card.name}' -> '{tactic.tactic_category.value}' ({tactic.name}) (❤️-5)", "error"); st.session_state.team_hp -= 5; st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); st.session_state.selected_card_index = None; st.rerun(); return
    st.session_state.player_focus_current -= cost;
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False
    base = card.base_damage; ref = 500; scale = (company.tax_target / ref)**0.5 if company.tax_target > 0 else 0.5; capped = max(0.5, min(2.0, scale)); scaled = int(base * capped); scale_log = f" (기업 규모 보정: {base}→{scaled})" if capped != 1.0 else ""; damage = scaled
    team_stats = st.session_state.team_stats; team_bonus = 0
    if any(c in [AttackCategory.COST, AttackCategory.COMMON] for c in card.attack_category): team_bonus += int(team_stats["analysis"] * 0.5)
    if AttackCategory.CAPITAL in card.attack_category: team_bonus += int(team_stats["data"] * 1.0)
    if '판례' in card.name: team_bonus += int(team_stats["persuasion"] * 1.0)
    if '압수' in card.name: team_bonus += int(team_stats["evidence"] * 1.5)
    if team_bonus > 0: log_message(f"📈 [팀 스탯 보너스] +{team_bonus}!", "info"); damage += team_bonus
    if "이철수" in [m.name for m in st.session_state.player_team] and card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]: damage += 8; log_message("✨ [기본기] +8!", "info")
    if "임향수" in [m.name for m in st.session_state.player_team] and ('분석' in card.name or '자료' in card.name or '추적' in card.name or AttackCategory.CAPITAL in card.attack_category): bonus = int(team_stats["analysis"] * 0.1 + team_stats["data"] * 0.1); damage += bonus; log_message(f"✨ [기획 조사] +{bonus}!", "info")
    if "유재준" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.ERROR:
        bonus = int(team_stats["persuasion"] / 10)
        if bonus > 0: damage += bonus; log_message(f"✨ [정기 조사] +{bonus}!", "info")
    if "김태호" in [m.name for m in st.session_state.player_team] and AttackCategory.CAPITAL in card.attack_category:
        bonus = int(team_stats["evidence"] * 0.1)
        if bonus > 0: damage += bonus; log_message(f"✨ [심층 기획] +{bonus}!", "info")
    mult = 1.0; mult_log = ""
    if card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        m = card.special_bonus.get('multiplier', 1.0); mult *= m; mult_log += f"🔥[{card.special_bonus.get('bonus_desc')}] "
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시": mult *= 2; mult_log += "✨[세법 교본 x2] "
    if "한중히" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or tactic.method_type == MethodType.CAPITAL_TX): mult *= 1.3; mult_log += "✨[역외탈세 +30%] "
    if "서영택" in [m.name for m in st.session_state.player_team] and (company.size == "대기업" or company.size == "외국계") and TaxType.CORP in card.tax_type: mult *= 1.25; mult_log += "✨[대기업 +25%] "
    if "이현동" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.INTENTIONAL: mult *= 1.2; mult_log += "✨[지하경제 +20%] "
    final_dmg = int(damage * mult); remain = tactic.total_amount - tactic.exposed_amount; dmg_tactic = min(final_dmg, remain); overkill = final_dmg - dmg_tactic; overkill_contrib = int(overkill * 0.5); tactic.exposed_amount += dmg_tactic; company.current_collected_tax += (dmg_tactic + overkill_contrib)
    prefix = "▶️ [적중]" if mult <= 1.0 else ("💥 [치명타!]" if mult >= 2.0 else "👍 [효과적!]"); log_message(f"{prefix} '{card.name}' **{final_dmg}억원** 피해!{scale_log}{mult_log}", "success")
    if overkill > 0: log_message(f"ℹ️ [초과 데미지] {overkill} 중 {overkill_contrib} (50%)만 총 세액 반영.", "info")
    # --- SyntaxError 수정된 부분 ---
    if tactic.exposed_amount >= tactic.total_amount and not tactic.is_cleared:
        tactic.is_cleared = True
        log_message(f"🔥 [{tactic.name}] 혐의 완전 적발! ({tactic.total_amount}억원)", "warning")
        if "벤츠" in card.text: log_message("💬 [현장] 법인소유 벤츠 발견!", "info")
        if "압수수색" in card.name: log_message("💬 [현장] 비밀장부 확보!", "info")
    # --- ---
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun()

def execute_auto_attack():
    best_card = None; best_idx = -1; max_dmg = -1
    for i, card in enumerate(st.session_state.player_hand):
        if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: continue
        cost = calculate_card_cost(card);
        if st.session_state.player_focus_current >= cost and card.base_damage > max_dmg: max_dmg=card.base_damage; best_card=card; best_idx=i
    if best_card is None: st.toast("⚡ 사용할 수 있는 자동 공격 카드가 없습니다.", icon="⚠️"); return
    target_idx = -1; co = st.session_state.current_battle_company
    for i, t in enumerate(co.tactics):
        if t.is_cleared: continue
        is_tax = (TaxType.COMMON in best_card.tax_type) or (isinstance(t.tax_type, list) and any(tt in best_card.tax_type for tt in t.tax_type)) or (t.tax_type in best_card.tax_type)
        is_cat = (AttackCategory.COMMON in best_card.attack_category) or (t.tactic_category in best_card.attack_category)
        if is_tax and is_cat: target_idx = i; break
    if target_idx != -1: log_message(f"⚡ 자동 공격: '{best_card.name}' -> '{co.tactics[target_idx].name}'!", "info"); execute_attack(best_idx, target_idx)
    else: st.toast(f"⚡ '{best_card.name}' 카드로 공격 가능한 혐의가 없습니다.", icon="⚠️")

def end_player_turn():
    if 'kim_dj_effect_used' in st.session_state: st.session_state.kim_dj_effect_used = False
    if 'cost_reduction_active' in st.session_state: st.session_state.cost_reduction_active = False
    st.session_state.player_discard.extend(st.session_state.player_hand); st.session_state.player_hand = []; st.session_state.selected_card_index = None
    log_message("--- 기업 턴 시작 ---"); enemy_turn()
    if not check_battle_end(): start_player_turn(); st.rerun()

def enemy_turn():
    co = st.session_state.current_battle_company; act = random.choice(co.defense_actions); min_d, max_d = co.team_hp_damage; dmg = random.randint(min_d, max_d); st.session_state.team_hp -= dmg
    prefix = "◀️ [기업]" if not (co.size in ["대기업", "외국계"] and "로펌" in act) else "◀️ [로펌]"; log_message(f"{prefix} {act} (팀 사기 저하 ❤️-{dmg}!)", "error")

def check_battle_end(): # SyntaxError 수정됨
    company = st.session_state.current_battle_company
    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(f"🎉 [조사 승리] 목표 {company.tax_target:,}억원 달성! (초과 {bonus:,}억원)", "success")
        st.session_state.total_collected_tax += company.current_collected_tax
        st.session_state.game_state = "REWARD"
        if st.session_state.player_discard:
            st.toast(f"승리! \"{st.session_state.player_discard[-1].text}\"", icon="🎉")
        return True
    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀 체력 소진...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    return False

def start_battle(co_template): # SyntaxError 수정됨
    co = copy.deepcopy(co_template); st.session_state.current_battle_company = co; st.session_state.game_state = "BATTLE"; st.session_state.battle_log = [f"--- {co.name} ({co.size}) 조사 시작 ---"]
    log_message(f"🏢 **{co.name}** 주요 탈루 혐의:", "info"); t_types = set();
    for t in co.tactics: tax = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; log_message(f"- **{t.name}** ({'/'.join(tax)}, {t.method_type.value}, {t.tactic_category.value})", "info"); t_types.add(t.method_type)
    log_message("---", "info"); guide = "[조사 가이드] "; has_g = False
    if MethodType.INTENTIONAL in t_types: guide += "고의 탈루: 증거 확보, 압박 중요. "; has_g = True
    if MethodType.CAPITAL_TX in t_types or co.size in ["대기업", "외국계"]: guide += "자본/국제 거래: 자금 흐름, 법규 분석 필요. "; has_g = True
    if MethodType.ERROR in t_types and MethodType.INTENTIONAL not in t_types: guide += "단순 오류: 규정/판례 제시, 설득 효과적. "; has_g = True
    log_message(guide if has_g else "[조사 가이드] 기업 특성/혐의 고려, 전략적 접근.", "warning"); log_message("---", "info")
    st.session_state.bonus_draw = 0
    # --- SyntaxError 수정된 부분 ---
    for art in st.session_state.player_artifacts:
        log_message(f"✨ [조사도구] '{art.name}' 효과 준비.", "info")
        if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
            st.session_state.bonus_draw += art.effect["value"]
    # --- ---
    st.session_state.player_deck.extend(st.session_state.player_discard); st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck)); st.session_state.player_discard = []; st.session_state.player_hand = []; start_player_turn()

def log_message(message, level="normal"):
    color = {"success": "green", "warning": "orange", "error": "red", "info": "blue"}.get(level)
    msg = f":{color}[{message}]" if color else message; st.session_state.battle_log.insert(0, msg)
    if len(st.session_state.battle_log) > 50: st.session_state.battle_log.pop()

def go_to_next_stage(add_card=None, heal_amount=0):
    if add_card: st.session_state.player_deck.append(add_card); st.toast(f"[{add_card.name}] 덱 추가!", icon="🃏")
    if heal_amount > 0: st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount); st.toast(f"팀 휴식 (체력 +{heal_amount})", icon="❤️")
    if 'reward_cards' in st.session_state: del st.session_state.reward_cards
    st.session_state.game_state = "MAP"; st.session_state.current_stage_level += 1; st.rerun()

# --- 5. UI 화면 함수 --- (이하 동일)

def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---"); st.header("국세청에 오신 것을 환영합니다.")
    st.markdown("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")
    st.image("https://cphoto.asiae.co.kr/listimglink/1/2021071213454415883_1626065144.jpg", caption="국세청 전경", width=400)
    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="동일 시드로 반복 테스트 가능")
    if st.button("🚨 조사 시작", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
        members = list(TAX_MAN_DB.values()); st.session_state.draft_team_choices = random.sample(members, min(len(members), 3))
        artifacts = list(ARTIFACT_DB.keys()); chosen_keys = random.sample(artifacts, min(len(artifacts), 3)); st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_keys]
        st.session_state.game_state = "GAME_SETUP_DRAFT"; st.rerun()
    with st.expander("📖 게임 방법", expanded=True): st.markdown("""**1.🎯 목표**: 기업 조사 → **'목표 추징 세액'** 달성 시 승리.\n**2.⚔️ 전투**: ❤️ **팀 체력**(0 시 패배), 🧠 **집중력**(카드 비용).\n**3.⚠️ 패널티**: **세목 불일치**(❤️-10), **유형 불일치**(❤️-5).\n**4.✨ 보너스**: 혐의 유형(`고의`, `오류`, `자본`) 맞는 카드 사용 시 추가 피해!""")

def show_setup_draft_screen():
    st.title("👨‍💼 조사팀 구성"); st.markdown("팀 **리더**와 시작 **조사도구** 선택:")
    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state: st.error("드래프트 정보 없음..."); st.button("메인 메뉴로", on_click=lambda: st.session_state.update(game_state="MAIN_MENU")); return
    teams = st.session_state.draft_team_choices; arts = st.session_state.draft_artifact_choices
    st.markdown("---"); st.subheader("1. 팀 리더 선택:"); lead_idx = st.radio("리더", range(len(teams)), format_func=lambda i: f"**{teams[i].name} ({teams[i].grade}급)** | {teams[i].description}\n   └ **{teams[i].ability_name}**: {teams[i].ability_desc}", label_visibility="collapsed")
    st.markdown("---"); st.subheader("2. 시작 조사도구 선택:"); art_idx = st.radio("도구", range(len(arts)), format_func=lambda i: f"**{arts[i].name}** | {arts[i].description}", label_visibility="collapsed")
    st.markdown("---");
    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True): initialize_game(teams[lead_idx], arts[art_idx]); del st.session_state.draft_team_choices, st.session_state.draft_artifact_choices; st.rerun()

def show_map_screen():
    if 'current_stage_level' not in st.session_state: st.warning("게임 상태 초기화됨..."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return
    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})"); st.write("조사할 기업 선택:")
    companies = st.session_state.company_order
    if st.session_state.current_stage_level < len(companies):
        co = companies[st.session_state.current_stage_level]
        with st.container(border=True):
            st.subheader(f"🏢 {co.name} ({co.size})"); st.markdown(co.description)
            c1, c2 = st.columns(2); c1.metric("매출액", format_krw(co.revenue)); c2.metric("영업이익", format_krw(co.operating_income))
            st.warning(f"**예상 턴당 데미지:** {co.team_hp_damage[0]}~{co.team_hp_damage[1]} ❤️"); st.info(f"**목표 추징 세액:** {co.tax_target:,} 억원 💰")
            with st.expander("🔍 혐의 및 실제 사례 정보 보기"):
                st.markdown("---"); st.markdown("### 📚 실제 사례 기반 교육 정보"); st.markdown(co.real_case_desc)
                st.markdown("---"); st.markdown("### 📝 주요 탈루 혐의 분석")
                for t in co.tactics: t_types = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; st.markdown(f"**📌 {t.name}** (`{'/'.join(t_types)}`, `{t.method_type.value}`, `{t.tactic_category.value}`)\n> _{t.description}_")
            if st.button(f"🚨 {co.name} 조사 시작", type="primary", use_container_width=True): start_battle(co); st.rerun()
    else: st.success("🎉 모든 기업 조사 완료!"); st.balloons(); st.button("🏆 다시 시작", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"))

def show_battle_screen():
    if not st.session_state.current_battle_company: st.error("오류: 기업 정보 없음..."); st.session_state.game_state = "MAP"; st.rerun(); return
    co = st.session_state.current_battle_company; st.title(f"⚔️ {co.name} 조사 중..."); st.markdown("---")
    col_co, col_log, col_hand = st.columns([1.6, 2.0, 1.4])
    with col_co:
        st.subheader(f"🏢 {co.name} ({co.size})"); st.progress(min(1.0, co.current_collected_tax/co.tax_target), text=f"💰 목표 세액: {co.current_collected_tax:,}/{co.tax_target:,} (억원)"); st.markdown("---"); st.subheader("🧾 탈루 혐의 목록")
        is_sel = st.session_state.get("selected_card_index") is not None
        if is_sel: st.info(f"**'{st.session_state.player_hand[st.session_state.selected_card_index].name}'** 카드로 공격할 혐의 선택:")
        if not co.tactics: st.write("(모든 혐의 적발!)")
        tactic_cont = st.container(height=450)
        with tactic_cont:
            for i, t in enumerate(co.tactics):
                cleared = t.exposed_amount >= t.total_amount
                with st.container(border=True):
                    t_types = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; st.markdown(f"**{t.name}** (`{'/'.join(t_types)}`/`{t.method_type.value}`/`{t.tactic_category.value}`)\n*{t.description}*")
                    prog_txt = f"✅ 완료: {t.total_amount:,}억" if cleared else f"적발: {t.exposed_amount:,}/{t.total_amount:,}억"; st.progress(1.0 if cleared else min(1.0, t.exposed_amount/t.total_amount), text=prog_txt)
                    if is_sel and not cleared:
                        card = st.session_state.player_hand[st.session_state.selected_card_index]
                        is_tax = (TaxType.COMMON in card.tax_type) or (isinstance(t.tax_type, list) and any(tt in card.tax_type for tt in t.tax_type)) or (t.tax_type in card.tax_type)
                        is_cat = (AttackCategory.COMMON in card.attack_category) or (t.tactic_category in card.attack_category)
                        label, type, help = f"🎯 **{t.name}** 공격", "primary", "클릭하여 공격!"
                        if card.special_bonus and card.special_bonus.get('target_method') == t.method_type: label = f"💥 [특효!] **{t.name}** 공격"; help = f"클릭! ({card.special_bonus.get('bonus_desc')})"
                        disabled = False
                        if not is_tax: label, type, help, disabled = f"⚠️ (세목 불일치!) {t.name}", "secondary", f"세목 불일치! ... (❤️-10)", True
                        elif not is_cat: label, type, help, disabled = f"⚠️ (유형 불일치!) {t.name}", "secondary", f"유형 불일치! ... (❤️-5)", True
                        if st.button(label, key=f"attack_{i}", use_container_width=True, type=type, disabled=disabled, help=help): execute_attack(st.session_state.selected_card_index, i)
    with col_log:
        st.subheader("❤️ 팀 현황"); c1, c2 = st.columns(2); c1.metric("팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}"); c2.metric("현재 집중력", f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}")
        if st.session_state.get('cost_reduction_active', False): st.info("✨ [실무 지휘] 다음 카드 비용 -1"); st.markdown("---")
        st.subheader("📋 조사 기록 (로그)"); log_cont = st.container(height=300, border=True); [log_cont.markdown(log) for log in st.session_state.battle_log]
        st.markdown("---"); st.subheader("🕹️ 행동")
        if st.session_state.get("selected_card_index") is not None: st.button("❌ 공격 취소", on_click=cancel_card_selection, use_container_width=True, type="secondary")
        else: act_cols = st.columns(2); act_cols[0].button("➡️ 턴 종료", on_click=end_player_turn, use_container_width=True, type="primary"); act_cols[1].button("⚡ 자동 공격", on_click=execute_auto_attack, use_container_width=True, type="secondary", help="가장 강력하고 사용 가능한 카드로 첫 번째 유효 혐의 자동 공격.")
    with col_hand:
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")
        if not st.session_state.player_hand: st.write("(손패 없음)")
        for i, card in enumerate(st.session_state.player_hand):
            if i >= len(st.session_state.player_hand): continue
            cost = calculate_card_cost(card); afford = st.session_state.player_focus_current >= cost; color = "blue" if afford else "red"; selected = (st.session_state.get("selected_card_index") == i)
            with st.container(border=True):
                title = f"**{card.name}** | :{color}[비용: {cost} 🧠]" + (" (선택됨)" if selected else ""); st.markdown(title)
                c_types=[t.value for t in card.tax_type]; c_cats=[c.value for c in card.attack_category]; st.caption(f"세목:`{'`,`'.join(c_types)}`|유형:`{'`,`'.join(c_cats)}`"); st.markdown(card.description)
                if card.base_damage > 0: st.markdown(f"**기본 적출액:** {card.base_damage} 억원")
                if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")
                btn_label = f"선택: {card.name}"
                if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: btn_label = f"사용: {card.name}"
                disabled = not afford; help = f"집중력 부족! ({cost})" if not afford else None
                if st.button(btn_label, key=f"play_{i}", use_container_width=True, disabled=disabled, help=help): select_card_to_play(i)

def show_reward_screen():
    st.header("🎉 조사 승리!"); st.balloons(); co = st.session_state.current_battle_company; st.success(f"**{co.name}** 조사 완료. 총 {co.current_collected_tax:,}억원 추징."); st.markdown("---")
    t1, t2, t3 = st.tabs(["🃏 카드 획득 (택1)", "❤️ 팀 정비", "🗑️ 덱 정비"])
    with t1:
        st.subheader("🎁 획득할 카드 1장 선택")
        if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
            pool = [c for c in LOGIC_CARD_DB.values() if not (c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw")]
            opts = []; has_cap = any(t.method_type == MethodType.CAPITAL_TX for t in co.tactics)
            if has_cap: cap = [c for c in pool if AttackCategory.CAPITAL in c.attack_category and c not in opts]; if cap: opts.append(random.choice(cap)); st.toast("ℹ️ [보상 가중치] '자본' 카드 1장 포함!")
            remain = [c for c in pool if c not in opts]; num_add = 3 - len(opts); opts.extend(random.sample(remain, min(len(remain), num_add)))
            while len(opts) < 3 and len(pool) > 0: add = random.choice(pool); if add not in opts or len(pool) < 3: opts.append(add)
            st.session_state.reward_cards = opts
        cols = st.columns(len(st.session_state.reward_cards))
        for i, card in enumerate(st.session_state.reward_cards):
            with cols[i]:
                with st.container(border=True):
                    types=[t.value for t in card.tax_type]; cats=[c.value for c in card.attack_category]; st.markdown(f"**{card.name}**|비용:{card.cost}🧠"); st.caption(f"세목:`{'`,`'.join(types)}`|유형:`{'`,`'.join(cats)}`"); st.markdown(card.description);
                    if card.base_damage > 0: st.info(f"**기본 적출액:** {card.base_damage} 억원")
                    elif card.special_effect and card.special_effect.get("type") == "draw": st.info(f"**드로우:** +{card.special_effect.get('value', 0)}")
                    if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")
                    if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"): go_to_next_stage(add_card=card)
    with t2: st.subheader("❤️ 팀 체력 회복"); st.markdown(f"현재: {st.session_state.team_hp}/{st.session_state.team_max_hp}"); heal=int(st.session_state.team_max_hp*0.3); st.button(f"팀 정비 (+{heal} 회복)", on_click=go_to_next_stage, kwargs={'heal_amount': heal}, use_container_width=True)
    with t3: st.subheader("🗑️ 덱에서 기본 카드 1장 제거"); st.markdown("덱 압축으로 좋은 카드 뽑을 확률 증가."); st.info("제거 대상: '단순 자료 대사', '기본 경비 적정성 검토', '단순 경비 처리 오류 지적'"); st.button("기본 카드 제거하러 가기", on_click=lambda: st.session_state.update(game_state="REWARD_REMOVE"), use_container_width=True)

def show_reward_remove_screen():
    st.header("🗑️ 덱 정비 (카드 제거)"); st.markdown("제거할 기본 카드 1장 선택:")
    deck = st.session_state.player_deck + st.session_state.player_discard; basics = ["단순 자료 대사", "기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]
    removable = {name: card for card in deck if card.name in basics and card.name not in locals().get('removable', {})}
    if not removable: st.warning("제거 가능한 기본 카드 없음."); st.button("맵으로 돌아가기", on_click=go_to_next_stage); return
    cols = st.columns(len(removable))
    for i, (name, card) in enumerate(removable.items()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠"); st.markdown(card.description)
                if st.button(f"제거: {card.name}", key=f"remove_{i}", use_container_width=True, type="primary"):
                    msg = ""; found = False
                    try: st.session_state.player_deck.remove(next(c for c in st.session_state.player_deck if c.name == name)); msg = "덱"; found = True
                    except (StopIteration, ValueError):
                        try: st.session_state.player_discard.remove(next(c for c in st.session_state.player_discard if c.name == name)); msg = "버린 덱"; found = True
                        except (StopIteration, ValueError): st.error("오류: 카드 제거 실패.")
                    if found: st.toast(f"{msg}에서 [{name}] 1장 제거!", icon="🗑️"); go_to_next_stage(); return
    st.markdown("---"); st.button("제거 취소 (맵으로)", on_click=go_to_next_stage, type="secondary")

def show_game_over_screen():
    st.header("... 조사 중단 ..."); st.error("팀 체력 소진.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원"); st.metric("진행 스테이지", f"📍 {st.session_state.current_stage_level + 1}")
    st.image("https://images.unsplash.com/photo-1554224155-16954a151120?...", caption="지친 조사관들...", width=400)
    st.button("다시 도전", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

def show_player_status_sidebar():
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황"); st.metric("💰 총 추징 세액", f"{st.session_state.total_collected_tax:,} 억원")
        if st.session_state.game_state != "BATTLE": st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")
        st.markdown("---")
        with st.expander("📊 팀 스탯", expanded=False): stats = st.session_state.team_stats; st.markdown(f"- 분석력: {stats['analysis']}\n- 설득력: {stats['persuasion']}\n- 증거력: {stats['evidence']}\n- 데이터: {stats['data']}")
        st.subheader("👥 팀원 (3명)")
        for m in st.session_state.player_team:
             with st.expander(f"**{m.name}** ({m.grade}급)"): st.markdown(f"HP:{m.hp}/{m.max_hp}, Focus:{m.focus}\n**{m.ability_name}**: {m.ability_desc}\n({m.description})")
        st.markdown("---")
        total = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand); st.subheader(f"📚 보유 덱 ({total}장)")
        with st.expander("덱 구성 보기"):
            deck = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand; counts = {};
            for card in deck: counts[card.name] = counts.get(card.name, 0) + 1
            for name in sorted(counts.keys()): st.write(f"- {name} x {counts[name]}")
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {name: 0 for name in counts};
                for card in st.session_state.player_discard: discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not any(v > 0 for v in discard_counts.values()): st.write("(버린 카드 없음)")
                else: [st.write(f"- {n} x {c}") for n, c in sorted(discard_counts.items()) if c > 0]
        st.markdown("---"); st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts: st.write("(없음)")
        else: [st.success(f"- {art.name}: {art.description}") for art in st.session_state.player_artifacts]
        st.markdown("---"); st.button("게임 포기 (메인 메뉴)", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), use_container_width=True)

# --- 6. 메인 실행 로직 ---
def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")
    if 'game_state' not in st.session_state: st.session_state.game_state = "MAIN_MENU"
    running = ["MAP", "BATTLE", "REWARD", "REWARD_REMOVE"]
    if st.session_state.game_state in running and 'player_team' not in st.session_state: st.toast("⚠️ 세션 만료, 메인 메뉴로."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return
    pages = { "MAIN_MENU": show_main_menu, "GAME_SETUP_DRAFT": show_setup_draft_screen, "MAP": show_map_screen, "BATTLE": show_battle_screen, "REWARD": show_reward_screen, "REWARD_REMOVE": show_reward_remove_screen, "GAME_OVER": show_game_over_screen }
    pages[st.session_state.game_state]()
    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER", "GAME_SETUP_DRAFT"] and 'player_team' in st.session_state: show_player_status_sidebar()

if __name__ == "__main__": main()
